import json

import pytest

from rag_template.cli import main
from rag_template.eval.answers import parse_verdict, run_answers, summarize
from rag_template.eval.cache import evaluate_cache
from rag_template.eval.datasets import GoldenItem, golden_qrels, load_golden
from rag_template.eval.metrics import mrr_at_k, ndcg_at_k, paired_bootstrap, proportion_ci, recall_at_k
from rag_template.eval.retrieval import CONFIGS, evaluate, rank_all
from rag_template.llm import Completion
from rag_template.models import HashEmbedder

from .conftest import DEMO, GOLDEN, FakeLLM


def test_metrics_known_values():
    rel = {"a": 1, "b": 1}
    assert recall_at_k(["x", "a", "y"], rel, 2) == 0.5
    assert mrr_at_k(["x", "a"], rel, 10) == 0.5
    assert ndcg_at_k(["a", "b", "x"], rel, 10) == pytest.approx(1.0)
    assert ndcg_at_k(["x", "a"], rel, 10) == pytest.approx((1 / 1.5849625) / (1 + 1 / 1.5849625))
    lo, hi = proportion_ci(8, 10)
    assert lo < 0.8 < hi


def test_paired_bootstrap_detects_improvement():
    a = [0.0] * 50 + [1.0] * 50
    b = [1.0] * 80 + [0.0] * 20
    out = paired_bootstrap(a, b, n=2000)
    assert out["diff"] == pytest.approx(0.3) and out["ci_low"] > 0


def test_golden_set_is_consistent():
    items = load_golden(GOLDEN)
    assert len({i.id for i in items}) == len(items) >= 40
    for item in items:
        assert all((DEMO / s).exists() for s in item.sources)
        if item.answerable:
            assert item.answer and item.sources and item.paraphrase and item.near_miss
        else:
            assert not item.sources


def test_retrieval_eval_on_demo(demo):
    queries, qrels = golden_qrels(load_golden(GOLDEN))
    configs = {k: CONFIGS[k] for k in ("bm25", "dense", "hybrid", "hybrid+rerank")}
    report = evaluate(rank_all(demo.retriever, queries, configs), qrels)
    assert report["queries"] == len(qrels)
    for name in configs:
        assert 0 <= report["summary"][name]["ndcg@10"] <= 1
    assert report["summary"]["bm25"]["hit@5"] > 0.6
    assert "hybrid vs dense" in report["comparisons"]


def test_rank_all_matches_retriever(demo):
    query = "Как подключить CORS?"
    params = CONFIGS["hybrid+rerank"]
    via_eval = rank_all(demo.retriever, {"q": query}, {"x": params})["x"]["q"]
    direct = demo.retriever.retrieve(query, params)
    assert [h.id for h in via_eval] == [h.id for h in direct]


def test_cache_eval():
    report = evaluate_cache(HashEmbedder(), load_golden(GOLDEN))
    assert report["pairs"] >= 40
    rates = [r["wrong_hit"] for r in report["thresholds"]]
    assert rates == sorted(rates, reverse=True)


class FakeJudge:
    model = "judge"

    def __init__(self):
        self.calls = 0

    def complete(self, messages, **kw):
        self.calls += 1
        return Completion('Вот оценка: {"correct": true, "faithful": false, "comment": "ok"}', "judge", 100, 20)


def test_answers_eval_resumes(demo, tmp_path):
    items = [i for i in load_golden(GOLDEN) if i.id in ("q09", "q15")]
    items.append(GoldenItem(id="u", question="Как подключить Kafka?", answerable=False))
    out = tmp_path / "answers.jsonl"
    judge = FakeJudge()
    configs = {"bm25": CONFIGS["bm25"]}
    demo.pipeline.llm = FakeLLM()
    rows = run_answers(demo.pipeline, items, configs, judge, out)
    assert len(rows) == 3 and judge.calls == 2
    rows = run_answers(demo.pipeline, items, configs, judge, out)
    assert judge.calls == 2 and len(out.read_text().splitlines()) == 3
    s = summarize(rows)["bm25"]
    assert s["correct"]["rate"] == 1 and s["faithful"]["rate"] == 0 and s["correct_refusal"]["rate"] == 1
    assert s["cost_per_1000_usd"] > 0


def test_parse_verdict():
    assert parse_verdict('```json\n{"correct": false, "faithful": true}\n```')["faithful"] is True
    with pytest.raises(ValueError):
        parse_verdict("нет json")


@pytest.fixture
def cli_env(monkeypatch, tmp_path):
    monkeypatch.setenv("RAG_EMBEDDING_BACKEND", "hash")
    monkeypatch.setenv("RAG_RERANKER_BACKEND", "none")
    monkeypatch.setenv("RAG_QDRANT_PATH", str(tmp_path / "qdrant"))
    return tmp_path


def test_cli_ingest_search_eval(cli_env, capsys):
    main(["ingest", str(DEMO), "--base-url", "https://x/ru/"])
    report = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert report["added"] > 100
    main(["search", "HTTPException 404", "--mode", "bm25"])
    assert "handling-errors.md" in capsys.readouterr().out.splitlines()[0]

    gate = cli_env / "gate.yaml"
    gate.write_text("bm25:\n  hit@5: 0.0\n")
    out = cli_env / "r.json"
    main(
        [
            "eval",
            "retrieval",
            "--golden",
            str(GOLDEN),
            "--configs",
            "bm25,hybrid",
            "--out",
            str(out),
            "--gate",
            str(gate),
        ]
    )
    assert json.loads(out.read_text())["summary"]["bm25"]["hit@5"] > 0
    gate.write_text("bm25:\n  hit@5: 1.01\n")
    with pytest.raises(SystemExit, match="quality gate failed"):
        main(["eval", "retrieval", "--golden", str(GOLDEN), "--configs", "bm25", "--gate", str(gate)])
