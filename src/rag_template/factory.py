from __future__ import annotations

from dataclasses import dataclass

from .cache import SemanticCache, build_cache
from .config import Settings
from .documents import Chunker
from .llm import LLM, OpenAICompatibleLLM
from .models import BM25Encoder, Embedder, Reranker, build_embedder, build_reranker
from .pipeline import RAGPipeline
from .retriever import RetrievalParams, Retriever
from .store import Indexer, QdrantStore


@dataclass
class Components:
    settings: Settings
    store: QdrantStore
    embedder: Embedder
    encoder: BM25Encoder
    reranker: Reranker | None
    retriever: Retriever
    indexer: Indexer
    pipeline: RAGPipeline


def build(
    settings: Settings,
    embedder: Embedder | None = None,
    reranker: Reranker | None = None,
    llm: LLM | None = None,
    store: QdrantStore | None = None,
) -> Components:
    store = store or QdrantStore.from_settings(settings)
    embedder = embedder or build_embedder(settings)
    if reranker is None:
        reranker = build_reranker(settings)
    encoder = BM25Encoder()
    stats = store.stats()
    if stats.get("avgdl"):
        encoder.avgdl = float(stats["avgdl"])
    params = RetrievalParams.from_settings(settings)
    if reranker is None:
        params.rerank = False
    retriever = Retriever(store, embedder, encoder, reranker, params)
    indexer = Indexer(store, embedder, encoder, Chunker(settings.chunk_size, settings.chunk_overlap))
    semantic = None
    if settings.semantic_cache:
        semantic = SemanticCache(
            store.client, settings.collection, embedder.dim, settings.semantic_cache_threshold, settings.cache_ttl
        )
    pipeline = RAGPipeline(
        retriever,
        llm or OpenAICompatibleLLM.from_settings(settings),
        cache=build_cache(settings),
        semantic_cache=semantic,
        cache_ttl=settings.cache_ttl,
        min_rerank_score=settings.min_rerank_score,
        trace_log=settings.trace_log,
        price_override=settings.price_override(),
    )
    return Components(settings, store, embedder, encoder, reranker, retriever, indexer, pipeline)
