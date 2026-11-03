"""How often a semantic cache would serve a paraphrase (wanted) and a different question (a wrong answer)."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from ..models import Embedder
from .datasets import GoldenItem

THRESHOLDS = (0.80, 0.85, 0.88, 0.90, 0.92, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99)


def similarities(embedder: Embedder, items: Sequence[GoldenItem]) -> dict[str, list[float]]:
    pairs = [i for i in items if i.paraphrase and i.near_miss]
    q = embedder.embed_queries([i.question for i in pairs])
    p = embedder.embed_queries([i.paraphrase for i in pairs])
    n = embedder.embed_queries([i.near_miss for i in pairs])
    return {
        "ids": [i.id for i in pairs],
        "paraphrase": np.sum(q * p, axis=1).tolist(),
        "near_miss": np.sum(q * n, axis=1).tolist(),
    }


def evaluate_cache(embedder: Embedder, items: Sequence[GoldenItem], thresholds: Sequence[float] = THRESHOLDS) -> dict:
    sims = similarities(embedder, items)
    para, near = np.array(sims["paraphrase"]), np.array(sims["near_miss"])
    rows = [
        {"threshold": t, "paraphrase_hit": float((para >= t).mean()), "wrong_hit": float((near >= t).mean())}
        for t in thresholds
    ]
    safe = [r for r in rows if r["wrong_hit"] == 0]
    return {
        "pairs": len(para),
        "embedder": embedder.name,
        "paraphrase_similarity": {"mean": float(para.mean()), "min": float(para.min())},
        "near_miss_similarity": {"mean": float(near.mean()), "max": float(near.max())},
        "thresholds": rows,
        "lowest_safe_threshold": min((r["threshold"] for r in safe), default=None),
        "similarities": sims,
    }


def markdown_table(report: dict) -> str:
    lines = ["| Порог | Перефразы из кэша | Чужой ответ из кэша |", "|---|---|---|"]
    for r in report["thresholds"]:
        lines.append(f"| {r['threshold']:.2f} | {r['paraphrase_hit']:.0%} | {r['wrong_hit']:.0%} |")
    return "\n".join(lines)
