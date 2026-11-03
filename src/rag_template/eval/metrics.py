from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import numpy as np


def dedupe(ids: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    out = []
    for i in ids:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def recall_at_k(ranked: Sequence[str], relevant: Mapping[str, float], k: int) -> float:
    rel = {d for d, g in relevant.items() if g > 0}
    if not rel:
        return 0.0
    return len(rel.intersection(ranked[:k])) / len(rel)


def hit_at_k(ranked: Sequence[str], relevant: Mapping[str, float], k: int) -> float:
    return float(any(relevant.get(d, 0) > 0 for d in ranked[:k]))


def mrr_at_k(ranked: Sequence[str], relevant: Mapping[str, float], k: int) -> float:
    for rank, d in enumerate(ranked[:k], start=1):
        if relevant.get(d, 0) > 0:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(ranked: Sequence[str], relevant: Mapping[str, float], k: int) -> float:
    dcg = sum(relevant.get(d, 0) / math.log2(i + 2) for i, d in enumerate(ranked[:k]))
    ideal = sorted((g for g in relevant.values() if g > 0), reverse=True)[:k]
    idcg = sum(g / math.log2(i + 2) for i, g in enumerate(ideal))
    return dcg / idcg if idcg else 0.0


METRICS = {"ndcg": ndcg_at_k, "recall": recall_at_k, "mrr": mrr_at_k, "hit": hit_at_k}


def score_rankings(
    rankings: Mapping[str, Sequence[str]], qrels: Mapping[str, Mapping[str, float]], names: Sequence[str]
) -> dict[str, list[float]]:
    """names like 'ndcg@10', 'recall@5'; returns per-query values in qrels order."""
    out: dict[str, list[float]] = {n: [] for n in names}
    for qid, relevant in qrels.items():
        ranked = rankings.get(qid, [])
        for name in names:
            metric, k = name.split("@")
            out[name].append(METRICS[metric](ranked, relevant, int(k)))
    return out


def paired_bootstrap(a: Sequence[float], b: Sequence[float], n: int = 10_000, seed: int = 0) -> dict[str, float]:
    """Mean of b - a with a percentile 95% CI over resampled queries."""
    diff = np.asarray(b, dtype=float) - np.asarray(a, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(diff), size=(n, len(diff)))
    means = diff[idx].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return {
        "diff": float(diff.mean()),
        "ci_low": float(lo),
        "ci_high": float(hi),
        "p_worse": float((means <= 0).mean()),
    }


def proportion_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson interval."""
    if n == 0:
        return 0.0, 0.0
    p = successes / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return max(0.0, center - half), min(1.0, center + half)
