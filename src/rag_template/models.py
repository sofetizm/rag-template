from __future__ import annotations

import zlib
from collections import Counter
from collections.abc import Sequence
from typing import Protocol

import numpy as np

from .text import tokenize


class Embedder(Protocol):
    name: str
    dim: int

    def embed_queries(self, texts: Sequence[str]) -> np.ndarray: ...

    def embed_documents(self, texts: Sequence[str]) -> np.ndarray: ...


class Reranker(Protocol):
    name: str

    def score(self, query: str, texts: Sequence[str]) -> np.ndarray: ...


def default_prefixes(model: str) -> tuple[str, str]:
    lowered = model.lower()
    if "e5" in lowered:
        return "query: ", "passage: "
    if "bge" in lowered and "m3" not in lowered and "zh" not in lowered:
        return "Represent this sentence for searching relevant passages: ", ""
    return "", ""


class SentenceTransformerEmbedder:
    def __init__(
        self,
        model: str,
        device: str | None = None,
        query_prefix: str | None = None,
        passage_prefix: str | None = None,
        batch_size: int = 64,
    ):
        from sentence_transformers import SentenceTransformer

        self.name = model
        self.model = SentenceTransformer(model, device=device)
        get_dim = getattr(self.model, "get_embedding_dimension", None) or self.model.get_sentence_embedding_dimension
        self.dim = int(get_dim())
        qp, pp = default_prefixes(model)
        self.query_prefix = qp if query_prefix is None else query_prefix
        self.passage_prefix = pp if passage_prefix is None else passage_prefix
        self.batch_size = batch_size

    def _encode(self, texts: Sequence[str], prefix: str) -> np.ndarray:
        vectors = self.model.encode(
            [prefix + t for t in texts],
            batch_size=self.batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 5000,
        )
        return np.asarray(vectors, dtype=np.float32)

    def embed_queries(self, texts: Sequence[str]) -> np.ndarray:
        return self._encode(texts, self.query_prefix)

    def embed_documents(self, texts: Sequence[str]) -> np.ndarray:
        return self._encode(texts, self.passage_prefix)


class HashEmbedder:
    """Bag of stemmed words and character trigrams hashed into a fixed vector.

    Needs no model download; used in tests and for offline smoke runs.
    """

    def __init__(self, dim: int = 512):
        self.name = f"hash-{dim}"
        self.dim = dim

    def _vector(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dim, dtype=np.float32)
        features: list[str] = []
        for token in tokenize(text):
            features.append("w:" + token)
            padded = f"<{token}>"
            features.extend("c:" + padded[i : i + 3] for i in range(len(padded) - 2))
        for feature, count in Counter(features).items():
            h = zlib.crc32(feature.encode())
            vec[h % self.dim] += (1.0 if (h >> 16) & 1 else -1.0) * (1 + np.log(count))
        norm = np.linalg.norm(vec)
        return vec / norm if norm else vec

    def embed_queries(self, texts: Sequence[str]) -> np.ndarray:
        return np.stack([self._vector(t) for t in texts]) if texts else np.zeros((0, self.dim))

    embed_documents = embed_queries


class CrossEncoderReranker:
    def __init__(self, model: str, device: str | None = None, batch_size: int = 32, max_length: int = 512):
        from sentence_transformers import CrossEncoder

        self.name = model
        self.model = CrossEncoder(model, device=device, max_length=max_length)
        self.batch_size = batch_size

    def score(self, query: str, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.zeros(0, dtype=np.float32)
        scores = self.model.predict([(query, t) for t in texts], batch_size=self.batch_size, show_progress_bar=False)
        return np.asarray(scores, dtype=np.float32)


class BM25Encoder:
    """BM25 as sparse vectors: term-frequency saturation on the document side,
    IDF applied by Qdrant (`Modifier.IDF`), so the index stays incremental."""

    def __init__(self, k1: float = 1.2, b: float = 0.75, avgdl: float = 256.0):
        self.k1 = k1
        self.b = b
        self.avgdl = avgdl

    @staticmethod
    def term_id(term: str) -> int:
        return zlib.crc32(term.encode()) & 0x7FFFFFFF

    def _merge(self, counts: Counter) -> dict[int, float]:
        merged: dict[int, float] = {}
        for term, value in counts.items():
            idx = self.term_id(term)
            merged[idx] = merged.get(idx, 0.0) + value
        return merged

    def encode_document(self, text: str) -> tuple[list[int], list[float]]:
        tokens = tokenize(text)
        dl = len(tokens)
        norm = self.k1 * (1 - self.b + self.b * dl / self.avgdl)
        tf = self._merge(Counter(tokens))
        indices = list(tf)
        values = [tf[i] * (self.k1 + 1) / (tf[i] + norm) for i in indices]
        return indices, values

    def encode_query(self, text: str) -> tuple[list[int], list[float]]:
        tf = self._merge(Counter(set(tokenize(text))))
        indices = list(tf)
        return indices, [1.0] * len(indices)

    @staticmethod
    def doc_length(text: str) -> int:
        return len(tokenize(text))


def build_embedder(settings) -> Embedder:
    if settings.embedding_backend == "hash":
        return HashEmbedder()
    return SentenceTransformerEmbedder(
        settings.embedding_model,
        device=settings.device,
        query_prefix=settings.query_prefix,
        passage_prefix=settings.passage_prefix,
    )


def build_reranker(settings) -> Reranker | None:
    if settings.reranker_backend == "none" or not settings.rerank:
        return None
    return CrossEncoderReranker(settings.reranker_model, device=settings.device)
