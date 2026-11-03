from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from .models import BM25Encoder, Embedder, Reranker
from .store import Hit, QdrantStore
from .tracing import NULL_TRACE, Trace

Mode = Literal["bm25", "dense", "hybrid"]


def rrf(rankings: list[list[Hit]], k: int = 60) -> list[Hit]:
    fused: dict[str, Hit] = {}
    for ranking in rankings:
        for rank, hit in enumerate(ranking, start=1):
            if hit.id not in fused:
                fused[hit.id] = Hit(hit.id, 0.0, hit.payload, {})
            target = fused[hit.id]
            target.score += 1.0 / (k + rank)
            target.scores.update(hit.scores)
    ordered = sorted(fused.values(), key=lambda h: h.score, reverse=True)
    for hit in ordered:
        hit.scores["rrf"] = hit.score
    return ordered


@dataclass
class RetrievalParams:
    mode: Mode = "hybrid"
    candidates: int = 40
    rerank: bool = True
    rerank_top: int = 30
    top_k: int = 5
    rrf_k: int = 60

    @classmethod
    def from_settings(cls, s) -> RetrievalParams:
        return cls(s.retrieval_mode, s.candidates, s.rerank, s.rerank_top, s.top_k, s.rrf_k)

    @property
    def label(self) -> str:
        return self.mode + ("+rerank" if self.rerank else "")


class Retriever:
    def __init__(
        self,
        store: QdrantStore,
        embedder: Embedder,
        encoder: BM25Encoder,
        reranker: Reranker | None = None,
        params: RetrievalParams | None = None,
    ):
        self.store = store
        self.embedder = embedder
        self.encoder = encoder
        self.reranker = reranker
        self.params = params or RetrievalParams()

    def embed_query(self, query: str) -> np.ndarray:
        return self.embedder.embed_queries([query])[0]

    def search_bm25(self, query: str, limit: int) -> list[Hit]:
        return self.store.search_sparse(*self.encoder.encode_query(query), limit=limit)

    def search_dense(self, vector: np.ndarray, limit: int) -> list[Hit]:
        return self.store.search_dense(vector, limit=limit)

    def rerank(self, query: str, hits: list[Hit], scores: np.ndarray | None = None) -> list[Hit]:
        if scores is None:
            scores = self.reranker.score(query, [h.indexed_text() for h in hits])
        reranked = [Hit(h.id, float(s), h.payload, {**h.scores, "rerank": float(s)}) for h, s in zip(hits, scores)]
        return sorted(reranked, key=lambda h: h.score, reverse=True)

    def retrieve(
        self,
        query: str,
        params: RetrievalParams | None = None,
        query_vector: np.ndarray | None = None,
        trace: Trace = NULL_TRACE,
    ) -> list[Hit]:
        p = params or self.params
        rankings: list[list[Hit]] = []
        if p.mode in ("bm25", "hybrid"):
            with trace.span("bm25") as span:
                rankings.append(self.search_bm25(query, p.candidates))
                span["hits"] = len(rankings[-1])
        if p.mode in ("dense", "hybrid"):
            if query_vector is None:
                with trace.span("embed_query"):
                    query_vector = self.embed_query(query)
            with trace.span("dense") as span:
                rankings.append(self.search_dense(query_vector, p.candidates))
                span["hits"] = len(rankings[-1])
        if len(rankings) == 1:
            hits = rankings[0]
        else:
            with trace.span("fusion"):
                hits = rrf(rankings, p.rrf_k)
        if p.rerank and self.reranker is not None and hits:
            with trace.span("rerank") as span:
                hits = self.rerank(query, hits[: p.rerank_top])
                span["pairs"] = min(len(hits), p.rerank_top)
        return hits[: p.top_k]
