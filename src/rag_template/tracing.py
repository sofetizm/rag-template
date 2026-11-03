from __future__ import annotations

import json
import threading
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from prometheus_client import Counter, Histogram

PRICES_PER_MILLION = {
    "openai/gpt-oss-120b": (0.15, 0.60),
    "openai/gpt-oss-20b": (0.075, 0.30),
}

STAGE_SECONDS = Histogram(
    "rag_stage_seconds",
    "Duration of pipeline stages",
    ["stage"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30),
)
REQUESTS = Counter("rag_requests_total", "Answered questions", ["cache", "outcome"])
TOKENS = Counter("rag_llm_tokens_total", "LLM tokens", ["model", "kind"])
COST = Counter("rag_llm_cost_usd_total", "LLM cost in USD", ["model"])

_log_lock = threading.Lock()


def price(model: str, prompt_tokens: int, completion_tokens: int, override: tuple[float, float] | None = None) -> float:
    per_in, per_out = override or PRICES_PER_MILLION.get(model, (0.0, 0.0))
    return (prompt_tokens * per_in + completion_tokens * per_out) / 1_000_000


class Trace:
    def __init__(self, name: str = "ask", log_path: str | None = None):
        self.id = uuid.uuid4().hex[:16]
        self.name = name
        self.log_path = log_path
        self.spans: list[dict[str, Any]] = []
        self.attrs: dict[str, Any] = {}
        self.usage = {"prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0}
        self._start = time.perf_counter()
        self.total_ms: float | None = None

    @contextmanager
    def span(self, name: str, **attrs: Any) -> Iterator[dict[str, Any]]:
        record: dict[str, Any] = {"name": name, **attrs}
        t0 = time.perf_counter()
        try:
            yield record
        finally:
            elapsed = time.perf_counter() - t0
            record["ms"] = round(elapsed * 1000, 1)
            self.spans.append(record)
            STAGE_SECONDS.labels(name).observe(elapsed)

    def add_usage(
        self, model: str, prompt_tokens: int, completion_tokens: int, override: tuple[float, float] | None = None
    ) -> None:
        cost = price(model, prompt_tokens, completion_tokens, override)
        self.usage["prompt_tokens"] += prompt_tokens
        self.usage["completion_tokens"] += completion_tokens
        self.usage["cost_usd"] += cost
        self.usage["model"] = model
        TOKENS.labels(model, "prompt").inc(prompt_tokens)
        TOKENS.labels(model, "completion").inc(completion_tokens)
        COST.labels(model).inc(cost)

    def finish(self, cache: str = "miss", outcome: str = "answered") -> None:
        self.total_ms = round((time.perf_counter() - self._start) * 1000, 1)
        self.attrs.update(cache=cache, outcome=outcome)
        REQUESTS.labels(cache, outcome).inc()
        STAGE_SECONDS.labels("total").observe(self.total_ms / 1000)
        if self.log_path:
            line = json.dumps({"ts": time.time(), **self.to_dict()}, ensure_ascii=False)
            with _log_lock:
                path = Path(self.log_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("a", encoding="utf-8") as f:
                    f.write(line + "\n")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "total_ms": self.total_ms,
            "spans": self.spans,
            "usage": {**self.usage, "cost_usd": round(self.usage["cost_usd"], 6)},
            **self.attrs,
        }


class _NullTrace(Trace):
    @contextmanager
    def span(self, name: str, **attrs: Any) -> Iterator[dict[str, Any]]:
        yield {}

    def add_usage(self, *args: Any, **kwargs: Any) -> None:
        pass

    def finish(self, *args: Any, **kwargs: Any) -> None:
        pass


NULL_TRACE = _NullTrace("null")
