from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import replace
from pathlib import Path

import yaml

from .config import Settings


def _components(settings: Settings, need_llm: bool = False):
    from .factory import build

    llm = None if need_llm else _NoLLM()
    return build(settings, llm=llm)


class _NoLLM:
    model = "none"

    def complete(self, *args, **kwargs):
        raise RuntimeError("LLM is not configured for this command")

    stream = complete


def _params(c, args):
    p = c.retriever.params
    updates = {}
    if getattr(args, "mode", None):
        updates["mode"] = args.mode
    if getattr(args, "top_k", None):
        updates["top_k"] = args.top_k
    if getattr(args, "no_rerank", False) or c.reranker is None:
        updates["rerank"] = False
    return replace(p, **updates)


def _write_json(path: str | None, data: dict) -> None:
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"saved {path}")


def cmd_ingest(args, settings: Settings) -> None:
    from .loaders import load_path

    c = _components(settings)
    if args.rebuild:
        c.store.drop()
    docs = load_path(args.path, base_url=args.base_url or settings.ingest_base_url)
    t0 = time.perf_counter()
    report = c.indexer.index(docs, prune=args.prune)
    print(
        json.dumps(
            {**report.to_dict(), "documents": len(docs), "seconds": round(time.perf_counter() - t0, 1)},
            ensure_ascii=False,
        )
    )


def cmd_search(args, settings: Settings) -> None:
    c = _components(settings)
    for i, hit in enumerate(c.retriever.retrieve(args.query, _params(c, args)), start=1):
        scores = ", ".join(f"{k}={v:.3f}" for k, v in hit.scores.items())
        print(f"{i}. {hit.source} — {hit.payload.get('section') or hit.payload.get('title')}  ({scores})")


def cmd_ask(args, settings: Settings) -> None:
    c = _components(settings, need_llm=True)
    answer = c.pipeline.ask(args.question, _params(c, args), use_cache=False)
    if args.json:
        print(json.dumps(answer.to_dict(), ensure_ascii=False, indent=2))
        return
    print(answer.text, "\n")
    for s in answer.sources:
        mark = "*" if s["n"] in answer.citations else " "
        print(f"{mark}[{s['n']}] {s['source']} — {s['section'] or s['title']}")
    u = answer.trace["usage"]
    print(
        f"\n{answer.trace['total_ms']} мс, токены {u['prompt_tokens']}+{u['completion_tokens']}, ${u['cost_usd']:.5f}"
    )


def cmd_serve(args, settings: Settings) -> None:
    import uvicorn

    uvicorn.run("rag_template.api:app", host=args.host, port=args.port, workers=args.workers)


def _gate(report: dict, path: str) -> list[str]:
    thresholds = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    failures = []
    for config, metrics in thresholds.items():
        for metric, minimum in metrics.items():
            value = report["summary"][config][metric]
            status = "ok" if value >= minimum else "FAIL"
            print(f"{status:4} {config:15} {metric:10} {value:.3f} (min {minimum})")
            if value < minimum:
                failures.append(f"{config} {metric}")
    return failures


def cmd_eval_retrieval(args, settings: Settings) -> None:
    from .eval.datasets import golden_qrels, load_golden
    from .eval.retrieval import CONFIGS, evaluate, markdown_table, rank_all

    c = _components(settings)
    queries, qrels = golden_qrels(load_golden(args.golden))
    configs = {k: v for k, v in CONFIGS.items() if not args.configs or k in args.configs.split(",")}
    if c.reranker is None:
        configs = {k: v for k, v in configs.items() if not v.rerank}
    report = evaluate(rank_all(c.retriever, queries, configs), qrels)
    print(markdown_table(report))
    _write_json(
        args.out,
        {"dataset": args.golden, "embedder": c.embedder.name, "reranker": getattr(c.reranker, "name", None), **report},
    )
    if args.gate and (failures := _gate(report, args.gate)):
        sys.exit(f"quality gate failed: {', '.join(failures)}")


def cmd_eval_cache(args, settings: Settings) -> None:
    from .eval.cache import evaluate_cache, markdown_table
    from .eval.datasets import load_golden
    from .models import build_embedder

    report = evaluate_cache(build_embedder(settings), load_golden(args.golden))
    print(markdown_table(report))
    print("lowest threshold without wrong answers:", report["lowest_safe_threshold"])
    _write_json(args.out, report)


def cmd_eval_answers(args, settings: Settings) -> None:
    from .eval.answers import markdown_table, run_answers, summarize
    from .eval.datasets import load_golden
    from .eval.retrieval import CONFIGS
    from .llm import OpenAICompatibleLLM

    c = _components(settings, need_llm=True)
    items = load_golden(args.golden)[: args.limit]
    base = c.retriever.params
    configs = {}
    for name in args.configs.split(","):
        cfg = CONFIGS[name]
        configs[name] = replace(base, mode=cfg.mode, rerank=cfg.rerank and c.reranker is not None)
    judge = OpenAICompatibleLLM(
        settings.llm_base_url,
        settings.llm_api_key,
        args.judge_model,
        temperature=0.0,
        max_tokens=1024,
        extra=settings.llm_extra,
    )
    rows = run_answers(
        c.pipeline,
        items,
        configs,
        judge,
        args.out,
        progress=lambda name, n, total: print(f"\r{name}: {n}/{total}", end="", flush=True),
    )
    print()
    summary = summarize(rows)
    print(markdown_table(summary))
    _write_json(args.summary, summary)


def cmd_eval_benchmark(args, settings: Settings) -> None:
    from .eval.datasets import load_mteb
    from .eval.retrieval import CONFIGS, evaluate, markdown_table, rank_all
    from .factory import build
    from .store import QdrantStore

    t0 = time.perf_counter()
    data = load_mteb(args.dataset, max_queries=args.max_queries)
    print(f"{args.dataset}: {len(data.corpus)} documents, {len(data.queries)} queries")
    collection = "bench_" + args.dataset.split("/")[-1].lower()
    bench = settings.model_copy(update={"collection": collection})
    c = build(bench, llm=_NoLLM(), store=QdrantStore.from_settings(bench))
    if not c.store.count() or args.rebuild:
        c.store.drop()
        c.indexer.index_chunks(data.chunks())
    index_s = time.perf_counter() - t0
    configs = {k: v for k, v in CONFIGS.items() if not args.configs or k in args.configs.split(",")}
    t1 = time.perf_counter()
    results = rank_all(
        c.retriever,
        data.queries,
        configs,
        progress=lambda n, total: print(f"\r{n}/{total}", end="", flush=True) if n % 50 == 0 else None,
    )
    print()
    report = evaluate(results, data.qrels)
    print(markdown_table(report))
    _write_json(
        args.out,
        {
            "dataset": args.dataset,
            "documents": len(data.corpus),
            "embedder": c.embedder.name,
            "reranker": getattr(c.reranker, "name", None),
            "index_seconds": round(index_s, 1),
            "search_seconds": round(time.perf_counter() - t1, 1),
            **report,
        },
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="rag", description="RAG template: ingest, ask, serve, evaluate")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ingest", help="index a file or a folder")
    p.add_argument("path")
    p.add_argument("--base-url", help="URL prefix for links to sources")
    p.add_argument("--prune", action="store_true", help="remove documents that are no longer in the folder")
    p.add_argument("--rebuild", action="store_true", help="drop the collection first")
    p.set_defaults(func=cmd_ingest)

    for name, func, arg in (("search", cmd_search, "query"), ("ask", cmd_ask, "question")):
        p = sub.add_parser(name)
        p.add_argument(arg)
        p.add_argument("--mode", choices=["bm25", "dense", "hybrid"])
        p.add_argument("--top-k", type=int)
        p.add_argument("--no-rerank", action="store_true")
        if name == "ask":
            p.add_argument("--json", action="store_true")
        p.set_defaults(func=func)

    p = sub.add_parser("serve", help="run the HTTP API and the web UI")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--workers", type=int, default=1)
    p.set_defaults(func=cmd_serve)

    ev = sub.add_parser("eval", help="evaluation").add_subparsers(dest="eval_command", required=True)
    p = ev.add_parser("retrieval", help="retrieval metrics on a golden set (index it first)")
    p.add_argument("--golden", default="data/golden/fastapi_ru.jsonl")
    p.add_argument("--configs")
    p.add_argument("--out")
    p.add_argument("--gate", help="YAML with minimal metric values; exit code 1 if any is lower")
    p.set_defaults(func=cmd_eval_retrieval)

    p = ev.add_parser("cache", help="semantic cache: paraphrases vs different questions")
    p.add_argument("--golden", default="data/golden/fastapi_ru.jsonl")
    p.add_argument("--out")
    p.set_defaults(func=cmd_eval_cache)

    p = ev.add_parser("answers", help="end-to-end answers judged by an LLM")
    p.add_argument("--golden", default="data/golden/fastapi_ru.jsonl")
    p.add_argument("--configs", default="bm25,hybrid+rerank")
    p.add_argument("--judge-model", default="openai/gpt-oss-120b")
    p.add_argument("--limit", type=int)
    p.add_argument("--out", default="results/answers.jsonl")
    p.add_argument("--summary", default="results/answers_summary.json")
    p.set_defaults(func=cmd_eval_answers)

    p = ev.add_parser("benchmark", help="retrieval on a public BEIR/MTEB dataset")
    p.add_argument("--dataset", default="mteb/scifact")
    p.add_argument("--max-queries", type=int)
    p.add_argument("--configs")
    p.add_argument("--rebuild", action="store_true")
    p.add_argument("--out")
    p.set_defaults(func=cmd_eval_benchmark)

    args = parser.parse_args(argv)
    args.func(args, Settings())


if __name__ == "__main__":
    main()
