from __future__ import annotations

import json
import random
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from ..documents import Chunk

_NS = uuid.UUID("3c0d9a64-1f7e-4c7e-b3a8-9b5d2a7c1e40")


@dataclass
class GoldenItem:
    id: str
    question: str
    answer: str = ""
    sources: list[str] = field(default_factory=list)
    answerable: bool = True
    paraphrase: str | None = None
    near_miss: str | None = None


def load_golden(path: str | Path) -> list[GoldenItem]:
    items = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            items.append(GoldenItem(**json.loads(line)))
    return items


def golden_qrels(
    items: list[GoldenItem], paraphrases: bool = True
) -> tuple[dict[str, str], dict[str, dict[str, float]]]:
    """Queries and relevance by source file; paraphrases are added as extra queries with the same answer."""
    queries: dict[str, str] = {}
    qrels: dict[str, dict[str, float]] = {}
    for item in items:
        if not (item.answerable and item.sources):
            continue
        variants = [(item.id, item.question)]
        if paraphrases and item.paraphrase:
            variants.append((f"{item.id}~p", item.paraphrase))
        for qid, text in variants:
            queries[qid] = text
            qrels[qid] = {s: 1.0 for s in item.sources}
    return queries, qrels


@dataclass
class RetrievalDataset:
    name: str
    corpus: dict[str, tuple[str, str]]
    queries: dict[str, str]
    qrels: dict[str, dict[str, float]]

    def chunks(self) -> list[Chunk]:
        return [
            Chunk(id=str(uuid.uuid5(_NS, doc_id)), source=doc_id, title=title, section="", text=text, position=0)
            for doc_id, (title, text) in self.corpus.items()
        ]


def _split(ds, *preferred: str):
    if not hasattr(ds, "keys"):
        return ds
    keys = list(ds.keys())
    return next((ds[p] for p in preferred if p in keys), ds[keys[0]])


def load_mteb(name: str, split: str = "test", max_queries: int | None = None, seed: int = 0) -> RetrievalDataset:
    """Retrieval datasets in BEIR/MTEB format from the Hugging Face Hub (e.g. mteb/scifact, mteb/RuBQRetrieval)."""
    from datasets import get_dataset_config_names, load_dataset

    configs = get_dataset_config_names(name)
    qrels_config = "qrels" if "qrels" in configs else "default"
    qrels_rows = _split(load_dataset(name, qrels_config), split)
    qrels: dict[str, dict[str, float]] = {}
    for row in qrels_rows:
        score = float(row["score"])
        if score > 0:
            qrels.setdefault(str(row["query-id"]), {})[str(row["corpus-id"])] = score

    queries_rows = _split(load_dataset(name, "queries"), "queries", split)
    queries = {str(r["_id"]): r["text"] for r in queries_rows if str(r["_id"]) in qrels}
    qrels = {q: rel for q, rel in qrels.items() if q in queries}
    if max_queries and len(queries) > max_queries:
        keep = sorted(random.Random(seed).sample(sorted(queries), max_queries))
        queries = {q: queries[q] for q in keep}
        qrels = {q: qrels[q] for q in keep}

    corpus_rows = _split(load_dataset(name, "corpus"), "corpus", split)
    corpus = {str(r["_id"]): (r.get("title") or "", r["text"]) for r in corpus_rows}
    return RetrievalDataset(name, corpus, queries, qrels)
