import json

import httpx
import pytest
from fastapi.testclient import TestClient

from rag_template.api import create_app
from rag_template.llm import Completion, LLMError, OpenAICompatibleLLM

from .conftest import make_components


@pytest.fixture
def client(small_docs):
    return TestClient(create_app(make_components(small_docs)))


def test_health_and_ui(client):
    health = client.get("/health").json()
    assert health["status"] == "ok" and health["documents"] == 3 and health["chunks"] > 0
    assert "<title>rag-template</title>" in client.get("/").text


def test_ask(client):
    body = client.post("/ask", json={"question": "что едят собаки", "mode": "bm25"}).json()
    assert body["sources"][0]["source"] == "dogs.md" and body["citations"] == [1]
    assert body["trace"]["total_ms"] is not None
    assert client.post("/ask", json={"question": ""}).status_code == 422
    assert client.post("/ask", json={"question": "x", "top_k": 100}).status_code == 422


def test_stream(client):
    with client.stream("POST", "/ask/stream", json={"question": "что едят кошки"}) as r:
        assert r.headers["content-type"].startswith("text/event-stream")
        events = [json.loads(line[5:]) for line in r.iter_lines() if line.startswith("data:")]
    assert [events[0]["type"], events[-1]["type"]] == ["sources", "done"]


def test_search_and_ingest(client):
    r = client.post("/ingest", files=[("files", ("birds.md", "# Птицы\n\nПтицы летают на юг осенью.".encode()))])
    assert r.json()["added"] == 1
    hits = client.post("/search", json={"query": "куда летают птицы", "mode": "bm25"}).json()["hits"]
    assert hits[0]["source"] == "birds.md"
    bad = client.post("/ingest", files=[("files", ("x.exe", b"bin"))])
    assert bad.status_code == 415


def test_metrics(client):
    client.post("/ask", json={"question": "что едят кошки"})
    text = client.get("/metrics").text
    assert "rag_stage_seconds_bucket" in text and "rag_llm_cost_usd_total" in text


def test_api_key(small_docs):
    c = make_components(small_docs, api_key="secret")
    client = TestClient(create_app(c))
    assert client.post("/ask", json={"question": "кошки"}).status_code == 401
    assert client.post("/ask", json={"question": "кошки"}, headers={"X-API-Key": "secret"}).status_code == 200
    assert (
        client.post("/search", json={"query": "кошки"}, headers={"Authorization": "Bearer secret"}).status_code == 200
    )
    assert client.get("/health").status_code == 200


def _llm(handler, **kw):
    return OpenAICompatibleLLM("https://api.test/v1", "key", "m", transport=httpx.MockTransport(handler), **kw)


def test_llm_complete_and_retry(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    calls = []

    def handler(request):
        calls.append(json.loads(request.content))
        if len(calls) == 1:
            return httpx.Response(429, headers={"retry-after": "1"})
        return httpx.Response(
            200,
            json={
                "model": "m",
                "choices": [{"message": {"content": " ответ "}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 3},
            },
        )

    out = _llm(handler, extra={"reasoning_effort": "low"}).complete([{"role": "user", "content": "q"}])
    assert out == Completion("ответ", "m", 10, 3)
    assert len(calls) == 2 and calls[1]["reasoning_effort"] == "low"


def test_llm_gives_up_on_long_rate_limit(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    with pytest.raises(LLMError, match="retry after 3600"):
        _llm(lambda r: httpx.Response(429, headers={"retry-after": "3600"})).complete([])


def test_llm_error_is_raised():
    with pytest.raises(LLMError, match="400"):
        _llm(lambda r: httpx.Response(400, text="bad")).complete([])


def test_llm_stream_reads_usage_from_groq_field():
    chunks = [
        {"model": "m", "choices": [{"delta": {"content": "При"}}]},
        {"choices": [{"delta": {"content": "вет"}}]},
        {"choices": [], "x_groq": {"usage": {"prompt_tokens": 5, "completion_tokens": 2}}},
    ]
    body = "".join(f"data: {json.dumps(c)}\n\n" for c in chunks) + "data: [DONE]\n\n"
    items = list(_llm(lambda r: httpx.Response(200, text=body)).stream([]))
    assert items[:2] == ["При", "вет"] and items[-1] == Completion("Привет", "m", 5, 2)
