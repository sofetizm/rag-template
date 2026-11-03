import time

import fakeredis
import numpy as np
import pytest

from rag_template.cache import MemoryCache, RedisCache, SemanticCache, cache_key, normalize_question
from rag_template.documents import Document
from rag_template.pipeline import REFUSAL, build_messages, is_refusal, parse_citations
from rag_template.store import Hit
from rag_template.tracing import price

from .conftest import FakeLLM, make_components


def test_parse_citations():
    assert parse_citations("А [2]. Б [1][3]. В [1, 2]. Г [9].", 3) == [2, 1, 3]
    assert parse_citations("без ссылок", 3) == []


def test_refusal_detection():
    assert is_refusal(REFUSAL)
    assert is_refusal("«В документации нет ответа на этот вопрос»")
    assert not is_refusal("Используйте HTTPException [1].")


def test_messages_number_fragments():
    hits = [Hit("a", 1, {"title": "T", "section": "S", "text": "текст"}), Hit("b", 1, {"title": "U", "text": "x"})]
    user = build_messages("вопрос?", hits)[1]["content"]
    assert "[1] T — S\nтекст" in user and "[2] U\nx" in user and user.endswith("Вопрос: вопрос?")


def test_ask_returns_cited_sources_and_trace(small_docs):
    c = make_components(small_docs)
    answer = c.pipeline.ask("что едят кошки")
    assert answer.citations == [1] and not answer.refused
    assert answer.sources[0]["source"] == "cats.md"
    names = [s["name"] for s in answer.trace["spans"]]
    assert {"embed_query", "bm25", "dense", "fusion", "llm"} <= set(names)
    assert answer.trace["usage"]["cost_usd"] == pytest.approx(price("openai/gpt-oss-120b", 1000, 100))


def test_refusal_is_not_cited(small_docs):
    answer = make_components(small_docs).pipeline.ask("как подключить kafka")
    assert answer.refused and answer.citations == []


def test_exact_cache_and_invalidation_on_reindex(small_docs):
    llm = FakeLLM()
    c = make_components(small_docs, llm=llm)
    first = c.pipeline.ask("Что едят кошки?")
    second = c.pipeline.ask("  что   ЕДЯТ кошки ")
    assert first.cached is None and second.cached == "exact" and len(llm.calls) == 1
    assert second.text == first.text and second.trace["usage"]["cost_usd"] == 0
    c.indexer.index([Document("new.md", "# Новое\n\nНовый документ.")])
    assert c.pipeline.ask("что едят кошки").cached is None and len(llm.calls) == 2
    assert c.pipeline.ask("что едят кошки", use_cache=False).cached is None and len(llm.calls) == 3


def test_semantic_cache_respects_threshold(small_docs):
    llm = FakeLLM()
    c = make_components(small_docs, llm=llm, semantic_cache=True, semantic_cache_threshold=0.8)
    c.pipeline.ask("что едят кошки")
    close = c.pipeline.ask("что же едят кошки")
    far = c.pipeline.ask("как работает async def")
    assert close.cached == "semantic" and far.cached is None
    assert len(llm.calls) == 2


def test_no_hits_skips_llm():
    llm = FakeLLM()
    c = make_components([Document("a.md", "# A\n\nтекст")], llm=llm)
    answer = c.pipeline.ask("zzzz", params=c.retriever.params.__class__(mode="bm25", rerank=False))
    assert answer.refused and llm.calls == []


def test_stream_events(small_docs):
    events = list(make_components(small_docs).pipeline.stream("что едят кошки"))
    assert events[0]["type"] == "sources" and events[-1]["type"] == "done"
    text = "".join(e["text"] for e in events if e["type"] == "token")
    assert text.strip() == events[-1]["text"]
    llm_span = next(s for s in events[-1]["trace"]["spans"] if s["name"] == "llm")
    assert "first_token_ms" in llm_span


def test_cache_key_normalization():
    assert normalize_question(" Что  ЕДЯТ кошки?? ") == "что едят кошки"
    assert cache_key("a", "v1", "f") != cache_key("a", "v2", "f")


def test_memory_cache_ttl_and_size():
    cache = MemoryCache(max_items=2)
    cache.set("a", {"x": 1}, ttl=60)
    cache.set("b", {"x": 2}, ttl=60)
    cache.get("a")
    cache.set("c", {"x": 3}, ttl=60)
    assert cache.get("b") is None and cache.get("a") == {"x": 1}
    cache.set("d", {"x": 4}, ttl=-1)
    assert cache.get("d") is None


def test_redis_cache_roundtrip():
    cache = RedisCache(client=fakeredis.FakeRedis())
    cache.set("k", {"text": "ответ"}, ttl=10)
    assert cache.get("k") == {"text": "ответ"} and cache.get("missing") is None


def test_semantic_cache_filters_version_and_expiry():
    from qdrant_client import QdrantClient

    cache = SemanticCache(QdrantClient(":memory:"), "t", dim=3, threshold=0.9, ttl=60)
    v = np.array([1.0, 0.0, 0.0])
    cache.set(v, "q", {"text": "a"}, version="v1", fingerprint="f")
    assert cache.get(v, "v1", "f")[0] == {"text": "a"}
    assert cache.get(v, "v2", "f") is None and cache.get(v, "v1", "g") is None
    assert cache.get(np.array([0.0, 1.0, 0.0]), "v1", "f") is None
    expired = SemanticCache(QdrantClient(":memory:"), "t", dim=3, threshold=0.9, ttl=-1)
    expired.set(v, "q", {"text": "a"}, version="v1", fingerprint="f")
    time.sleep(0.01)
    assert expired.get(v, "v1", "f") is None
