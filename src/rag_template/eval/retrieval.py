from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace

import numpy as np

from ..retriever import RetrievalParams, Retriever, rrf
from ..store import Hit
from .metrics import dedupe, paired_bootstrap, score_rankings

BASE = RetrievalParams(candidates=50, rerank_top=30, top_k=50)
CONFIGS = {
    "bm25": replace(BASE, mode="bm25", rerank=False),
    "dense": replace(BASE, mode="dense", rerank=False),
    "hybrid": replace(BASE, mode="hybrid", rerank=False),
    "bm25+rerank": replace(BASE, mode="bm25", rerank=True),
    "dense+rerank": replace(BASE, mode="dense", rerank=True),
    "hybrid+rerank": replace(BASE, mode="hybrid", rerank=True),
}
DEFAULT_METRICS = ("ndcg@10", "recall@5", "recall@10", "mrr@10", "hit@1", "hit@5")


def rank_all(
    retriever: Retriever,
    queries: Mapping[str, str],
    configs: Mapping[str, RetrievalParams],
    progress: Callable[[int, int], None] | None = None,
) -> dict[str, dict[str, list[Hit]]]:
    """Rankings for every config; candidate lists and reranker scores are shared between configs."""
    qids = list(queries)
    use_bm25 = any(c.mode in ("bm25", "hybrid") for c in configs.values())
    use_dense = any(c.mode in ("dense", "hybrid") for c in configs.values())
    depth = max(c.candidates for c in configs.values())
    vectors = retriever.embedder.embed_queries([queries[q] for q in qids]) if use_dense else None
    results: dict[str, dict[str, list[Hit]]] = {name: {} for name in configs}

    for i, qid in enumerate(qids):
        query = queries[qid]
        bm25 = retriever.search_bm25(query, depth) if use_bm25 else []
        dense = retriever.search_dense(vectors[i], depth) if use_dense else []
        rerank_scores: dict[str, float] = {}
        for name, c in configs.items():
            lists = {
                "bm25": [bm25[: c.candidates]],
                "dense": [dense[: c.candidates]],
                "hybrid": [bm25[: c.candidates], dense[: c.candidates]],
            }[c.mode]
            hits = lists[0] if len(lists) == 1 else rrf(lists, c.rrf_k)
            if c.rerank and retriever.reranker is not None:
                hits = hits[: c.rerank_top]
                missing = [h for h in hits if h.id not in rerank_scores]
                if missing:
                    scores = retriever.reranker.score(query, [h.indexed_text() for h in missing])
                    rerank_scores.update({h.id: float(s) for h, s in zip(missing, scores)})
                hits = retriever.rerank(query, hits, np.array([rerank_scores[h.id] for h in hits]))
            results[name][qid] = hits[: c.top_k]
        if progress:
            progress(i + 1, len(qids))
    return results


def doc_rankings(results: Mapping[str, Sequence[Hit]]) -> dict[str, list[str]]:
    return {qid: dedupe([h.source for h in hits]) for qid, hits in results.items()}


def evaluate(
    results: Mapping[str, Mapping[str, Sequence[Hit]]],
    qrels: Mapping[str, Mapping[str, float]],
    metrics: Sequence[str] = DEFAULT_METRICS,
    baseline: str = "bm25",
    main: str = "ndcg@10",
) -> dict:
    per_query = {name: score_rankings(doc_rankings(r), qrels, metrics) for name, r in results.items()}
    summary = {name: {m: float(np.mean(v)) for m, v in pq.items()} for name, pq in per_query.items()}
    comparisons = {}
    if baseline in per_query:
        for name in per_query:
            if name != baseline:
                comparisons[f"{name} vs {baseline}"] = paired_bootstrap(
                    per_query[baseline][main], per_query[name][main]
                )
    if "hybrid" in per_query and "hybrid+rerank" in per_query:
        comparisons["hybrid+rerank vs hybrid"] = paired_bootstrap(
            per_query["hybrid"][main], per_query["hybrid+rerank"][main]
        )
    if "dense" in per_query and "hybrid" in per_query:
        comparisons["hybrid vs dense"] = paired_bootstrap(per_query["dense"][main], per_query["hybrid"][main])
    return {
        "queries": len(qrels),
        "main_metric": main,
        "summary": summary,
        "comparisons": comparisons,
        "per_query": per_query,
    }


def markdown_table(report: dict, metrics: Sequence[str] = DEFAULT_METRICS) -> str:
    lines = ["| Конфигурация | " + " | ".join(metrics) + " |", "|---" * (len(metrics) + 1) + "|"]
    best = {m: max(s[m] for s in report["summary"].values()) for m in metrics}
    for name, s in report["summary"].items():
        cells = [f"**{s[m]:.3f}**" if np.isclose(s[m], best[m]) else f"{s[m]:.3f}" for m in metrics]
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    return "\n".join(lines)
