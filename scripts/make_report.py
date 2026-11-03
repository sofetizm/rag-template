"""Builds results/RESULTS.md and charts from the JSON files written by `rag eval ...`."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from rag_template.eval import answers, cache, retrieval  # noqa: E402

RESULTS = Path("results")
SURFACE, TEXT, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e0"
BLUE, ORANGE, GRAY = "#2a78d6", "#eb6834", "#b9b8b2"
ORDER = ["bm25", "dense", "hybrid", "bm25+rerank", "dense+rerank", "hybrid+rerank"]
BENCHES = [
    ("bench_rubq.json", "RuBQ (рус., 56 тыс. абзацев)"),
    ("bench_scifact.json", "SciFact (англ., 5 тыс. статей)"),
    ("golden_retrieval.json", "Документация FastAPI (рус., 42 вопроса)"),
]


def load(name: str) -> dict | None:
    path = RESULTS / name
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def style(ax) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, length=0)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def retrieval_chart(reports: list[tuple[str, dict]]) -> None:
    fig, axes = plt.subplots(1, len(reports), figsize=(4.2 * len(reports), 3.4), sharey=True, facecolor=SURFACE)
    axes = [axes] if len(reports) == 1 else axes
    for ax, (title, rep) in zip(axes, reports):
        names = [n for n in ORDER if n in rep["summary"]]
        values = [rep["summary"][n]["ndcg@10"] for n in names]
        best = max(values)
        colors = [BLUE if v == best else GRAY for v in values]
        bars = ax.barh(names, values, color=colors, height=0.62)
        for bar, v in zip(bars, values):
            ax.text(
                v + 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{v:.3f}".replace(".", ","),
                va="center",
                fontsize=9,
                color=TEXT,
            )
        ax.set_xlim(0, min(1.0, best * 1.25))
        ax.invert_yaxis()
        ax.set_title(title, fontsize=10, color=TEXT, loc="left")
        style(ax)
    fig.suptitle("nDCG@10, больше — лучше", x=0.01, ha="left", fontsize=12, color=TEXT)
    fig.tight_layout()
    fig.savefig(RESULTS / "retrieval.png", dpi=160)


def cache_chart(rep: dict) -> None:
    rows = rep["thresholds"]
    t = [r["threshold"] for r in rows]
    fig, ax = plt.subplots(figsize=(7, 3.6), facecolor=SURFACE)
    for key, color, label in (
        ("paraphrase_hit", BLUE, "перефраз получил ответ из кэша"),
        ("wrong_hit", ORANGE, "другой вопрос получил чужой ответ"),
    ):
        y = [r[key] * 100 for r in rows]
        ax.plot(t, y, color=color, linewidth=2, marker="o", markersize=5, label=label)
    ax.legend(frameon=False, fontsize=9, labelcolor=TEXT, loc="best")
    ax.set_xlim(t[0] - 0.01, t[-1] + 0.01)
    ax.set_ylim(-3, 105)
    ax.set_xlabel("порог косинусного сходства", color=MUTED)
    ax.set_ylabel("% пар", color=MUTED)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    style(ax)
    ax.grid(axis="x", visible=False)
    ax.spines["left"].set_visible(False)
    ax.set_title(
        f"Семантический кэш: перефразы против похожих вопросов ({rep['pairs']} пар)",
        fontsize=11,
        color=TEXT,
        loc="left",
    )
    fig.tight_layout()
    fig.savefig(RESULTS / "cache.png", dpi=160)


def main() -> None:
    parts = ["# Результаты\n"]
    reports = []
    for name, title in BENCHES:
        rep = load(name)
        if rep:
            reports.append((title, rep))
            parts.append(
                f"## {title}\n\nЭмбеддинги: `{rep.get('embedder')}`, реранкер: `{rep.get('reranker')}`, "
                f"запросов: {rep['queries']}.\n\n{retrieval.markdown_table(rep)}\n"
            )
            rows = [
                f"| {k} | {v['diff']:+.3f} | [{v['ci_low']:+.3f}; {v['ci_high']:+.3f}] |"
                for k, v in rep["comparisons"].items()
            ]
            parts.append(
                "Разница nDCG@10 (парный бутстреп по запросам, 95% ДИ):\n\n| Сравнение | Δ | 95% ДИ |\n"
                "|---|---|---|\n" + "\n".join(rows) + "\n"
            )
    if reports:
        retrieval_chart(reports)
        parts.append("![nDCG@10](retrieval.png)\n")
    rep = load("cache.json")
    if rep:
        cache_chart(rep)
        parts.append(
            f"## Семантический кэш\n\nЭмбеддинги: `{rep['embedder']}`.\n\n{cache.markdown_table(rep)}\n\n"
            f"Минимальный порог без чужих ответов: {rep['lowest_safe_threshold']}.\n\n![Кэш](cache.png)\n"
        )
    summary = load("answers_summary.json")
    if summary:
        parts.append(f"## Ответы целиком (LLM-судья)\n\n{answers.markdown_table(summary)}\n")
    (RESULTS / "RESULTS.md").write_text("\n".join(parts), encoding="utf-8")
    print("results/RESULTS.md")


if __name__ == "__main__":
    main()
