from __future__ import annotations

import re
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .cache import Cache, SemanticCache, cache_key
from .llm import LLM, Completion
from .retriever import RetrievalParams, Retriever
from .store import Hit
from .tracing import Trace

PROMPT_VERSION = "v1"
REFUSAL = "В документации нет ответа на этот вопрос."

SYSTEM_PROMPT = f"""Ты отвечаешь на вопросы по документации. Используй только фрагменты документации из сообщения пользователя.

Правила:
- После каждого утверждения ставь номер фрагмента, на котором оно основано, в квадратных скобках: [1] или [2][3].
- Если во фрагментах нет ответа, ответь ровно: «{REFUSAL}» и ничего не добавляй.
- Не используй знания, которых нет во фрагментах, и не придумывай названия функций, параметров и настроек.
- Код из фрагментов можно приводить в блоках кода.
- Отвечай кратко и по делу, на языке вопроса."""

_CITATION = re.compile(r"\[(\d+(?:\s*[,;]\s*\d+)*)\]")


def format_context(hits: list[Hit]) -> str:
    parts = []
    for i, hit in enumerate(hits, start=1):
        title, section = hit.payload.get("title", ""), hit.payload.get("section", "")
        header = f"{title} — {section}" if section else title
        parts.append(f"[{i}] {header}\n{hit.text}")
    return "\n\n".join(parts)


def build_messages(question: str, hits: list[Hit]) -> list[dict[str, str]]:
    user = f"Фрагменты документации:\n\n{format_context(hits)}\n\nВопрос: {question}"
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}]


def parse_citations(text: str, n_sources: int) -> list[int]:
    cited: list[int] = []
    for group in _CITATION.findall(text):
        for raw in re.split(r"[,;]", group):
            n = int(raw)
            if 1 <= n <= n_sources and n not in cited:
                cited.append(n)
    return cited


def is_refusal(text: str) -> bool:
    simple = re.sub(r"[«»\"'.\s]+", " ", text.lower()).strip()
    return simple.startswith(re.sub(r"[«»\"'.\s]+", " ", REFUSAL.lower()).strip()) or not simple


@dataclass
class Answer:
    question: str
    text: str
    sources: list[dict[str, Any]]
    citations: list[int] = field(default_factory=list)
    refused: bool = False
    cached: str | None = None
    trace: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    def cacheable(self) -> dict[str, Any]:
        return {k: v for k, v in self.to_dict().items() if k not in ("trace", "cached")}


class RAGPipeline:
    def __init__(
        self,
        retriever: Retriever,
        llm: LLM,
        cache: Cache | None = None,
        semantic_cache: SemanticCache | None = None,
        cache_ttl: int = 86400,
        min_rerank_score: float | None = None,
        trace_log: str | None = None,
        price_override: tuple[float, float] | None = None,
    ):
        self.retriever = retriever
        self.llm = llm
        self.cache = cache
        self.semantic_cache = semantic_cache
        self.cache_ttl = cache_ttl
        self.min_rerank_score = min_rerank_score
        self.trace_log = trace_log
        self.price_override = price_override

    def version(self) -> str:
        return str(self.retriever.store.stats().get("version", "empty"))

    def fingerprint(self, params: RetrievalParams) -> str:
        return f"{PROMPT_VERSION}|{self.llm.model}|{params.label}|{params.top_k}|{params.candidates}"

    @staticmethod
    def _sources(hits: list[Hit]) -> list[dict[str, Any]]:
        return [{"n": i, **hit.to_dict()} for i, hit in enumerate(hits, start=1)]

    def _prepare(self, question: str, params: RetrievalParams, trace: Trace, use_cache: bool):
        version = self.version()
        fingerprint = self.fingerprint(params)
        key = cache_key(question, version, fingerprint)
        if use_cache and self.cache is not None:
            with trace.span("cache_lookup", kind="exact"):
                cached = self.cache.get(key)
            if cached:
                return {"cached": ("exact", cached, None)}
        vector: np.ndarray | None = None
        if self.semantic_cache is not None or params.mode != "bm25":
            with trace.span("embed_query"):
                vector = self.retriever.embed_query(question)
        if use_cache and self.semantic_cache is not None and vector is not None:
            with trace.span("cache_lookup", kind="semantic") as span:
                found = self.semantic_cache.get(vector, version, fingerprint)
                span["hit"] = found is not None
            if found:
                answer, score = found
                trace.attrs["semantic_similarity"] = round(score, 4)
                return {"cached": ("semantic", answer, None)}
        hits = self.retriever.retrieve(question, params, query_vector=vector, trace=trace)
        low = (
            self.min_rerank_score is not None
            and hits
            and "rerank" in hits[0].scores
            and hits[0].scores["rerank"] < self.min_rerank_score
        )
        return {
            "hits": hits,
            "key": key,
            "vector": vector,
            "version": version,
            "fingerprint": fingerprint,
            "skip_llm": not hits or low,
        }

    def _store(self, answer: Answer, state: dict[str, Any]) -> None:
        if self.cache is not None:
            self.cache.set(state["key"], answer.cacheable(), self.cache_ttl)
        if self.semantic_cache is not None and state["vector"] is not None:
            self.semantic_cache.set(
                state["vector"], answer.question, answer.cacheable(), state["version"], state["fingerprint"]
            )

    def _from_cache(self, question: str, kind: str, cached: dict[str, Any], trace: Trace) -> Answer:
        trace.finish(cache=kind, outcome="refused" if cached.get("refused") else "answered")
        return Answer(**{**cached, "question": question, "cached": kind, "trace": trace.to_dict()})

    def ask(self, question: str, params: RetrievalParams | None = None, use_cache: bool = True) -> Answer:
        params = params or self.retriever.params
        trace = Trace("ask", self.trace_log)
        state = self._prepare(question, params, trace, use_cache)
        if "cached" in state:
            return self._from_cache(question, *state["cached"][:2], trace)
        hits = state["hits"]
        if state["skip_llm"]:
            answer = Answer(question, REFUSAL, self._sources(hits), refused=True)
        else:
            with trace.span("llm", model=self.llm.model) as span:
                completion = self.llm.complete(build_messages(question, hits))
                span.update(prompt_tokens=completion.prompt_tokens, completion_tokens=completion.completion_tokens)
            trace.add_usage(
                completion.model, completion.prompt_tokens, completion.completion_tokens, self.price_override
            )
            refused = is_refusal(completion.text)
            answer = Answer(
                question,
                completion.text,
                self._sources(hits),
                [] if refused else parse_citations(completion.text, len(hits)),
                refused,
            )
        self._store(answer, state)
        trace.finish(cache="miss", outcome="refused" if answer.refused else "answered")
        answer.trace = trace.to_dict()
        return answer

    def stream(
        self, question: str, params: RetrievalParams | None = None, use_cache: bool = True
    ) -> Iterator[dict[str, Any]]:
        params = params or self.retriever.params
        trace = Trace("ask_stream", self.trace_log)
        state = self._prepare(question, params, trace, use_cache)
        if "cached" in state:
            answer = self._from_cache(question, *state["cached"][:2], trace)
            yield {"type": "sources", "sources": answer.sources}
            yield {"type": "token", "text": answer.text}
            yield {"type": "done", **answer.to_dict()}
            return
        hits = state["hits"]
        sources = self._sources(hits)
        yield {"type": "sources", "sources": sources}
        if state["skip_llm"]:
            answer = Answer(question, REFUSAL, sources, refused=True)
            yield {"type": "token", "text": REFUSAL}
        else:
            completion: Completion | None = None
            with trace.span("llm", model=self.llm.model) as span:
                t0 = time.perf_counter()
                for item in self.llm.stream(build_messages(question, hits)):
                    if isinstance(item, Completion):
                        completion = item
                    else:
                        span.setdefault("first_token_ms", round((time.perf_counter() - t0) * 1000, 1))
                        yield {"type": "token", "text": item}
            if completion is None:
                raise RuntimeError("LLM stream ended without a final message")
            trace.add_usage(
                completion.model, completion.prompt_tokens, completion.completion_tokens, self.price_override
            )
            refused = is_refusal(completion.text)
            answer = Answer(
                question,
                completion.text,
                sources,
                [] if refused else parse_citations(completion.text, len(hits)),
                refused,
            )
        self._store(answer, state)
        trace.finish(cache="miss", outcome="refused" if answer.refused else "answered")
        answer.trace = trace.to_dict()
        yield {"type": "done", **answer.to_dict()}
