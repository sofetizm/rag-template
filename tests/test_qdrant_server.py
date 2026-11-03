"""Same flow against a real Qdrant server: RAG_TEST_QDRANT_URL=http://localhost:6333 pytest tests/test_qdrant_server.py"""

import os
import uuid

import pytest
from qdrant_client import QdrantClient

from rag_template.documents import Document
from rag_template.factory import build
from rag_template.models import HashEmbedder
from rag_template.retriever import RetrievalParams
from rag_template.store import QdrantStore

from .conftest import FakeLLM, LexicalReranker, make_settings

URL = os.environ.get("RAG_TEST_QDRANT_URL")
pytestmark = pytest.mark.skipif(not URL, reason="RAG_TEST_QDRANT_URL is not set")


@pytest.fixture
def server_components():
    name = "test_" + uuid.uuid4().hex[:8]
    settings = make_settings(collection=name, qdrant_url=URL, semantic_cache=True, semantic_cache_threshold=0.95)
    store = QdrantStore(QdrantClient(url=URL), name)
    c = build(settings, embedder=HashEmbedder(), reranker=LexicalReranker(), llm=FakeLLM(), store=store)
    c.retriever.params.rerank = True
    yield c
    store.drop()
    if store.client.collection_exists(f"{name}__cache"):
        store.client.delete_collection(f"{name}__cache")


def test_full_flow_on_server(server_components, small_docs, demo_docs):
    c = server_components
    report = c.indexer.index(demo_docs[:40] + small_docs)
    assert report.added == 43 and c.store.count() == report.chunks
    for mode in ("bm25", "dense", "hybrid"):
        hits = c.retriever.retrieve("что едят кошки", RetrievalParams(mode=mode, rerank=False))
        assert hits[0].source == "cats.md"
    answer = c.pipeline.ask("что едят кошки")
    assert answer.citations == [1] and c.pipeline.ask("что едят кошки?").cached == "exact"
    c.pipeline.cache = None
    assert c.pipeline.ask("что едят кошки").cached == "semantic"

    changed = c.indexer.index([Document("cats.md", "# Кошки\n\nКошки едят корм."), *small_docs[1:]], prune=False)
    assert changed.updated == 1
    assert c.pipeline.ask("что едят кошки").cached is None
