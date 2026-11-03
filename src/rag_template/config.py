from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RAG_", env_file=".env", extra="ignore", populate_by_name=True)

    qdrant_url: str | None = None
    qdrant_path: str | None = None
    collection: str = "docs"

    embedding_backend: Literal["sentence-transformers", "hash"] = "sentence-transformers"
    embedding_model: str = "intfloat/multilingual-e5-small"
    query_prefix: str | None = None
    passage_prefix: str | None = None
    reranker_backend: Literal["cross-encoder", "none"] = "cross-encoder"
    reranker_model: str = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
    device: str | None = None

    chunk_size: int = 1000
    chunk_overlap: int = 150

    retrieval_mode: Literal["bm25", "dense", "hybrid"] = "hybrid"
    candidates: int = 40
    rerank: bool = True
    rerank_top: int = 30
    top_k: int = 5
    rrf_k: int = 60
    min_rerank_score: float | None = None

    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_api_key: str | None = Field(
        default=None, validation_alias=AliasChoices("RAG_LLM_API_KEY", "GROQ_API_KEY", "OPENAI_API_KEY", "llm_api_key")
    )
    llm_model: str = "openai/gpt-oss-20b"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 1024
    llm_extra: dict[str, Any] = Field(default_factory=lambda: {"reasoning_effort": "low"})
    llm_timeout: float = 60.0
    llm_price_input: float | None = None
    llm_price_output: float | None = None

    cache_backend: Literal["memory", "redis", "none"] = "memory"
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 86400
    semantic_cache: bool = False
    semantic_cache_threshold: float = 0.97

    api_key: str | None = None
    trace_log: str | None = None
    ingest_on_start: str | None = None
    ingest_base_url: str | None = None

    def price_override(self) -> tuple[float, float] | None:
        if self.llm_price_input is None and self.llm_price_output is None:
            return None
        return self.llm_price_input or 0.0, self.llm_price_output or 0.0

    def location(self) -> dict[str, Any]:
        if self.qdrant_url:
            return {"url": self.qdrant_url}
        if self.qdrant_path:
            return {"path": self.qdrant_path}
        return {"location": ":memory:"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
