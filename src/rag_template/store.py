from __future__ import annotations

import hashlib
import uuid
import warnings
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client import models as qm

from .documents import Chunk, Chunker, Document
from .models import BM25Encoder, Embedder

DENSE = "dense"
SPARSE = "bm25"
_META_NS = uuid.UUID("0b8b6d0a-3a4c-4c5e-8f6c-6a1f6f0e7d21")
_STATS_ID = str(uuid.uuid5(_META_NS, "stats"))


def create_indexes(client: QdrantClient, collection: str, fields: dict[str, qm.PayloadSchemaType]) -> None:
    """Payload indexes speed up filters on a Qdrant server; local mode ignores them."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for name, schema in fields.items():
            client.create_payload_index(collection, name, schema)


@dataclass
class Hit:
    id: str
    score: float
    payload: dict[str, Any]
    scores: dict[str, float] = field(default_factory=dict)

    @property
    def text(self) -> str:
        return self.payload.get("text", "")

    @property
    def source(self) -> str:
        return self.payload.get("source", "")

    def indexed_text(self) -> str:
        title, section = self.payload.get("title", ""), self.payload.get("section", "")
        header = f"{title} — {section}" if section else title
        return f"{header}\n\n{self.text}" if header else self.text

    def to_dict(self) -> dict[str, Any]:
        keys = ("source", "title", "section", "url", "text")
        return {"id": self.id, "score": self.score, "scores": self.scores, **{k: self.payload.get(k) for k in keys}}


class QdrantStore:
    def __init__(self, client: QdrantClient, collection: str = "docs"):
        self.client = client
        self.collection = collection
        self.meta = f"{collection}__meta"

    @classmethod
    def from_settings(cls, settings) -> QdrantStore:
        return cls(QdrantClient(**settings.location()), settings.collection)

    def exists(self) -> bool:
        return self.client.collection_exists(self.collection)

    def ensure(self, dim: int, embedder: str) -> None:
        if self.exists():
            stats = self.stats()
            if stats.get("dim") not in (None, dim) or stats.get("embedder") not in (None, embedder):
                raise ValueError(
                    f"collection '{self.collection}' was built with {stats.get('embedder')} "
                    f"(dim {stats.get('dim')}); rebuild it with `rag ingest --rebuild`"
                )
            return
        self.client.create_collection(
            self.collection,
            vectors_config={DENSE: qm.VectorParams(size=dim, distance=qm.Distance.COSINE)},
            sparse_vectors_config={SPARSE: qm.SparseVectorParams(modifier=qm.Modifier.IDF)},
        )
        create_indexes(self.client, self.collection, {"source": qm.PayloadSchemaType.KEYWORD})
        if not self.client.collection_exists(self.meta):
            self.client.create_collection(self.meta, vectors_config={})
            create_indexes(self.client, self.meta, {"kind": qm.PayloadSchemaType.KEYWORD})
        self.save_stats({"dim": dim, "embedder": embedder})

    def drop(self) -> None:
        for name in (self.collection, self.meta):
            if self.client.collection_exists(name):
                self.client.delete_collection(name)

    def stats(self) -> dict[str, Any]:
        if not self.client.collection_exists(self.meta):
            return {}
        found = self.client.retrieve(self.meta, [_STATS_ID])
        return dict(found[0].payload or {}) if found else {}

    def save_stats(self, update: dict[str, Any]) -> None:
        stats = {**self.stats(), **update, "kind": "stats"}
        self.client.upsert(self.meta, [qm.PointStruct(id=_STATS_ID, vector={}, payload=stats)])

    def documents(self) -> dict[str, dict[str, Any]]:
        if not self.client.collection_exists(self.meta):
            return {}
        docs: dict[str, dict[str, Any]] = {}
        offset = None
        flt = qm.Filter(must=[qm.FieldCondition(key="kind", match=qm.MatchValue(value="doc"))])
        while True:
            points, offset = self.client.scroll(self.meta, scroll_filter=flt, limit=1000, offset=offset)
            for p in points:
                docs[p.payload["source"]] = dict(p.payload)
            if offset is None:
                return docs

    def count(self) -> int:
        return self.client.count(self.collection).count if self.exists() else 0

    def delete_source(self, source: str) -> None:
        flt = qm.Filter(must=[qm.FieldCondition(key="source", match=qm.MatchValue(value=source))])
        self.client.delete(self.collection, points_selector=qm.FilterSelector(filter=flt))
        self.client.delete(self.meta, points_selector=[str(uuid.uuid5(_META_NS, "doc:" + source))])

    def upsert(
        self, chunks: Sequence[Chunk], dense: np.ndarray, sparse: Sequence[tuple[list[int], list[float]]]
    ) -> None:
        points = [
            qm.PointStruct(
                id=chunk.id,
                vector={DENSE: dense[i].tolist(), SPARSE: qm.SparseVector(indices=sparse[i][0], values=sparse[i][1])},
                payload=chunk.payload(),
            )
            for i, chunk in enumerate(chunks)
        ]
        self.client.upsert(self.collection, points)

    def record_document(self, doc: Document, n_chunks: int) -> None:
        payload = {
            "kind": "doc",
            "source": doc.source,
            "title": doc.title,
            "hash": doc.hash,
            "chunks": n_chunks,
            "url": doc.url,
        }
        point = qm.PointStruct(id=str(uuid.uuid5(_META_NS, "doc:" + doc.source)), vector={}, payload=payload)
        self.client.upsert(self.meta, [point])

    def _hits(self, points, stage: str) -> list[Hit]:
        return [Hit(str(p.id), float(p.score), dict(p.payload or {}), {stage: float(p.score)}) for p in points]

    def search_dense(self, vector: np.ndarray, limit: int) -> list[Hit]:
        res = self.client.query_points(
            self.collection, query=vector.tolist(), using=DENSE, limit=limit, with_payload=True
        )
        return self._hits(res.points, "dense")

    def search_sparse(self, indices: list[int], values: list[float], limit: int) -> list[Hit]:
        if not indices:
            return []
        res = self.client.query_points(
            self.collection,
            query=qm.SparseVector(indices=indices, values=values),
            using=SPARSE,
            limit=limit,
            with_payload=True,
        )
        return self._hits(res.points, "bm25")


@dataclass
class IndexReport:
    added: int = 0
    updated: int = 0
    unchanged: int = 0
    removed: int = 0
    chunks: int = 0
    version: str = ""

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


class Indexer:
    def __init__(self, store: QdrantStore, embedder: Embedder, encoder: BM25Encoder, chunker: Chunker):
        self.store = store
        self.embedder = embedder
        self.encoder = encoder
        self.chunker = chunker

    def _fit_avgdl(self, chunks: Sequence[Chunk]) -> None:
        stats = self.store.stats()
        if stats.get("avgdl"):
            self.encoder.avgdl = float(stats["avgdl"])
            return
        lengths = [self.encoder.doc_length(c.indexed_text()) for c in chunks]
        if lengths:
            self.encoder.avgdl = float(np.mean(lengths))
            self.store.save_stats({"avgdl": self.encoder.avgdl, "k1": self.encoder.k1, "b": self.encoder.b})

    def _write(self, chunks: Sequence[Chunk], batch_size: int) -> None:
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            texts = [c.indexed_text() for c in batch]
            dense = self.embedder.embed_documents(texts)
            sparse = [self.encoder.encode_document(t) for t in texts]
            self.store.upsert(batch, dense, sparse)

    def index_chunks(self, chunks: Sequence[Chunk], batch_size: int = 256) -> None:
        """Index chunks as they are, without splitting or document bookkeeping (benchmarks)."""
        self.store.ensure(self.embedder.dim, self.embedder.name)
        self._fit_avgdl(chunks)
        self._write(chunks, batch_size)

    def index(self, docs: Sequence[Document], prune: bool = False, batch_size: int = 256) -> IndexReport:
        self.store.ensure(self.embedder.dim, self.embedder.name)
        existing = self.store.documents()
        report = IndexReport()

        changed = [d for d in docs if existing.get(d.source, {}).get("hash") != d.hash]
        report.unchanged = len(docs) - len(changed)
        split = [(d, self.chunker.split(d)) for d in changed]
        self._fit_avgdl([c for _, cs in split for c in cs])

        for doc, chunks in split:
            if doc.source in existing:
                self.store.delete_source(doc.source)
                report.updated += 1
            else:
                report.added += 1
            self._write(chunks, batch_size)
            self.store.record_document(doc, len(chunks))
            report.chunks += len(chunks)

        if prune:
            keep = {d.source for d in docs}
            for source in existing:
                if source not in keep:
                    self.store.delete_source(source)
                    report.removed += 1

        current = self.store.documents()
        digest = hashlib.sha1("".join(sorted(f"{s}:{d['hash']}" for s, d in current.items())).encode())
        report.version = digest.hexdigest()[:12]
        self.store.save_stats({"version": report.version, "documents": len(current), "chunks": self.store.count()})
        return report
