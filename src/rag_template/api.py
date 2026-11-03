from __future__ import annotations

import json
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import replace
from importlib import resources
from typing import Literal

from fastapi import Depends, FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field

from .config import get_settings
from .factory import Components, build
from .llm import LLMError
from .loaders import SUPPORTED, load_bytes, load_path
from .retriever import RetrievalParams
from .store import QdrantStore
from .tracing import Trace

log = logging.getLogger("rag_template")


class QueryOptions(BaseModel):
    mode: Literal["bm25", "dense", "hybrid"] | None = None
    top_k: int | None = Field(default=None, ge=1, le=20)
    rerank: bool | None = None


class AskRequest(QueryOptions):
    question: str = Field(min_length=1, max_length=2000)
    use_cache: bool = True


class SearchRequest(QueryOptions):
    query: str = Field(min_length=1, max_length=2000)


def _params(c: Components, options: QueryOptions) -> RetrievalParams:
    params = c.retriever.params
    updates = {k: v for k, v in options.model_dump(include={"mode", "top_k", "rerank"}).items() if v is not None}
    if updates.get("rerank") and c.reranker is None:
        updates["rerank"] = False
    return replace(params, **updates)


def wait_for_store(store: QdrantStore, timeout: float = 60.0) -> None:
    deadline = time.monotonic() + timeout
    while True:
        try:
            store.client.get_collections()
            return
        except Exception:
            if time.monotonic() > deadline:
                raise
            time.sleep(1)


def ingest_on_start(c: Components) -> None:
    path = c.settings.ingest_on_start
    if not path or c.store.count() > 0:
        return
    docs = load_path(path, base_url=c.settings.ingest_base_url)
    report = c.indexer.index(docs)
    log.warning("indexed %s documents, %s chunks from %s", len(docs), report.chunks, path)


def create_app(components: Components | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if getattr(app.state, "c", None) is None:
            settings = get_settings()
            store = QdrantStore.from_settings(settings)
            wait_for_store(store)
            app.state.c = build(settings, store=store)
        ingest_on_start(app.state.c)
        yield

    app = FastAPI(title="rag-template", version="0.1.0", lifespan=lifespan)
    app.state.c = components

    def comp(request: Request) -> Components:
        return request.app.state.c

    def auth(
        request: Request, x_api_key: str | None = Header(default=None), authorization: str | None = Header(default=None)
    ) -> None:
        expected = request.app.state.c.settings.api_key
        if not expected:
            return
        token = x_api_key or (authorization or "").removeprefix("Bearer ").strip()
        if token != expected:
            raise HTTPException(401, "invalid API key")

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def index() -> str:
        return resources.files("rag_template").joinpath("static/index.html").read_text(encoding="utf-8")

    @app.get("/health")
    def health(c: Components = Depends(comp)) -> dict:
        stats = c.store.stats()
        return {
            "status": "ok",
            "chunks": c.store.count(),
            "documents": stats.get("documents", 0),
            "version": stats.get("version"),
            "retrieval": c.retriever.params.label,
            "llm": c.pipeline.llm.model,
        }

    @app.post("/ask", dependencies=[Depends(auth)])
    def ask(body: AskRequest, c: Components = Depends(comp)) -> dict:
        try:
            return c.pipeline.ask(body.question, _params(c, body), use_cache=body.use_cache).to_dict()
        except LLMError as e:
            raise HTTPException(502, str(e)) from e

    @app.post("/ask/stream", dependencies=[Depends(auth)])
    def ask_stream(body: AskRequest, c: Components = Depends(comp)) -> StreamingResponse:
        def events():
            try:
                for event in c.pipeline.stream(body.question, _params(c, body), use_cache=body.use_cache):
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            except LLMError as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
        )

    @app.post("/search", dependencies=[Depends(auth)])
    def search(body: SearchRequest, c: Components = Depends(comp)) -> dict:
        trace = Trace("search")
        hits = c.retriever.retrieve(body.query, _params(c, body), trace=trace)
        trace.finish(cache="none", outcome="search")
        return {"hits": [h.to_dict() for h in hits], "trace": trace.to_dict()}

    @app.post("/ingest", dependencies=[Depends(auth)])
    def ingest(files: list[UploadFile] = File(...), c: Components = Depends(comp)) -> dict:
        docs = []
        for f in files:
            if not any(f.filename.lower().endswith(s) for s in SUPPORTED):
                raise HTTPException(415, f"unsupported file type: {f.filename}")
            docs.append(load_bytes(f.filename, f.file.read(), c.settings.ingest_base_url))
        return c.indexer.index(docs).to_dict()

    @app.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()
