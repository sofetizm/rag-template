"""End-to-end evaluation: answers judged by an LLM against reference answers and retrieved context."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

import numpy as np

from ..llm import LLM
from ..pipeline import RAGPipeline
from ..retriever import RetrievalParams
from .datasets import GoldenItem
from .metrics import proportion_ci

JUDGE_PROMPT = """Ты проверяешь ответ системы, которая отвечает на вопросы по документации.

Вопрос: {question}

Эталонный ответ: {reference}

Фрагменты документации, которые получила система:
{context}

Ответ системы:
{answer}

Оцени два свойства.
1. correct: ответ передаёт суть эталона — содержит его ключевые факты и не противоречит ему. Дополнительные верные подробности допустимы. Если система отказалась отвечать, correct = false.
2. faithful: каждое утверждение ответа подтверждается фрагментами. Пересказ своими словами допустим; факты, названия функций, параметров и настроек, которых нет во фрагментах, — нарушение.

Верни только JSON без пояснений вокруг: {{"correct": true или false, "faithful": true или false, "comment": "одно предложение"}}"""


def parse_verdict(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError(f"judge returned no JSON: {text[:200]}")
    data = json.loads(match.group(0))
    return {
        "correct": bool(data.get("correct")),
        "faithful": bool(data.get("faithful")),
        "comment": str(data.get("comment", "")),
    }


def judge_answer(judge: LLM, item: GoldenItem, answer_text: str, sources: Sequence[dict]) -> dict:
    context = "\n\n".join(f"[{s['n']}] {s.get('title', '')} — {s.get('section') or ''}\n{s['text']}" for s in sources)
    prompt = JUDGE_PROMPT.format(question=item.question, reference=item.answer, context=context, answer=answer_text)
    for attempt in range(3):
        completion = judge.complete([{"role": "user", "content": prompt}], temperature=0.0)
        try:
            return {
                **parse_verdict(completion.text),
                "judge_tokens": completion.prompt_tokens + completion.completion_tokens,
            }
        except (ValueError, json.JSONDecodeError):
            if attempt == 2:
                raise
    raise RuntimeError("unreachable")


def _load(path: Path) -> dict[tuple[str, str], dict]:
    if not path.exists():
        return {}
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {(r["config"], r["id"]): r for r in rows}


def run_answers(
    pipeline: RAGPipeline,
    items: Sequence[GoldenItem],
    configs: Mapping[str, RetrievalParams],
    judge: LLM,
    out_path: str | Path,
    progress: Callable[[str, int, int], None] | None = None,
) -> list[dict]:
    """Resumable: finished rows are kept in out_path, so a run stopped by a rate limit continues later."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = _load(out_path)
    for name, params in configs.items():
        for n, item in enumerate(items, start=1):
            if (name, item.id) in done:
                continue
            answer = pipeline.ask(item.question, params, use_cache=False)
            cited = sorted({answer.sources[c - 1]["source"] for c in answer.citations})
            row = {
                "config": name,
                "id": item.id,
                "question": item.question,
                "answerable": item.answerable,
                "gold_sources": item.sources,
                "answer": answer.text,
                "refused": answer.refused,
                "citations": answer.citations,
                "cited_sources": cited,
                "retrieved_sources": [s["source"] for s in answer.sources],
                "total_ms": answer.trace.get("total_ms"),
                "spans": answer.trace.get("spans"),
                "usage": answer.trace.get("usage"),
            }
            if item.answerable and not answer.refused:
                row.update(judge_answer(judge, item, answer.text, answer.sources))
            elif item.answerable:
                row.update(correct=False, faithful=None, comment="refused")
            with out_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            done[(name, item.id)] = row
            if progress:
                progress(name, n, len(items))
    return [done[(name, i.id)] for name in configs for i in items if (name, i.id) in done]


def _rate(values: Sequence[bool]) -> dict:
    n, k = len(values), int(sum(values))
    lo, hi = proportion_ci(k, n)
    return {"rate": k / n if n else 0.0, "n": n, "ci_low": lo, "ci_high": hi}


def summarize(rows: Sequence[dict]) -> dict:
    out = {}
    for name in dict.fromkeys(r["config"] for r in rows):
        rs = [r for r in rows if r["config"] == name]
        ans = [r for r in rs if r["answerable"]]
        answered = [r for r in ans if not r["refused"]]
        unans = [r for r in rs if not r["answerable"]]
        stage_ms: dict[str, list[float]] = {}
        for r in rs:
            for span in r.get("spans") or []:
                stage_ms.setdefault(span["name"], []).append(span["ms"])
        totals = [r["total_ms"] for r in rs if r.get("total_ms") is not None]
        usage = [r.get("usage") or {} for r in rs]
        out[name] = {
            "correct": _rate([bool(r.get("correct")) for r in ans]),
            "faithful": _rate([bool(r.get("faithful")) for r in answered]),
            "false_refusal": _rate([r["refused"] for r in ans]),
            "citation_hit": _rate([bool(set(r["cited_sources"]) & set(r["gold_sources"])) for r in answered]),
            "uncited": _rate([not r["citations"] for r in answered]),
            "correct_refusal": _rate([r["refused"] for r in unans]),
            "latency_ms": {"p50": float(np.percentile(totals, 50)), "p95": float(np.percentile(totals, 95))}
            if totals
            else {},
            "stage_ms_p50": {k: float(np.percentile(v, 50)) for k, v in stage_ms.items()},
            "prompt_tokens_mean": float(np.mean([u.get("prompt_tokens", 0) for u in usage])),
            "completion_tokens_mean": float(np.mean([u.get("completion_tokens", 0) for u in usage])),
            "cost_per_1000_usd": float(np.mean([u.get("cost_usd", 0.0) for u in usage]) * 1000),
        }
    return out


def markdown_table(summary: dict) -> str:
    def pct(x: dict) -> str:
        return f"{x['rate']:.0%} ({x['ci_low']:.0%}–{x['ci_high']:.0%})" if x["n"] else "—"

    lines = [
        "| Конфигурация | Верных ответов | Без выдумок | Отказ, где ответ есть | Отказ, где ответа нет | "
        "Цитата из нужного документа | p50, мс | $ за 1000 ответов |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name, s in summary.items():
        lines.append(
            f"| {name} | {pct(s['correct'])} | {pct(s['faithful'])} | {pct(s['false_refusal'])} | "
            f"{pct(s['correct_refusal'])} | {pct(s['citation_hit'])} | {s['latency_ms'].get('p50', 0):.0f} | "
            f"{s['cost_per_1000_usd']:.2f} |"
        )
    return "\n".join(lines)
