from __future__ import annotations

import json
import time
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, Protocol

import httpx


@dataclass
class Completion:
    text: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0


class LLM(Protocol):
    model: str

    def complete(self, messages: list[dict[str, str]], **kwargs: Any) -> Completion: ...

    def stream(self, messages: list[dict[str, str]], **kwargs: Any) -> Iterator[str | Completion]: ...


class LLMError(RuntimeError):
    pass


class OpenAICompatibleLLM:
    """Chat Completions API: Groq, OpenAI, vLLM, Ollama, LM Studio, OpenRouter."""

    def __init__(
        self,
        base_url: str,
        api_key: str | None,
        model: str,
        temperature: float = 0.1,
        max_tokens: int = 1024,
        extra: dict[str, Any] | None = None,
        timeout: float = 60.0,
        retries: int = 5,
        max_wait: float = 120.0,
        transport: httpx.BaseTransport | None = None,
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.extra = extra or {}
        self.retries = retries
        self.max_wait = max_wait
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self.client = httpx.Client(base_url=base_url.rstrip("/"), headers=headers, timeout=timeout, transport=transport)

    @classmethod
    def from_settings(cls, s) -> OpenAICompatibleLLM:
        return cls(
            s.llm_base_url, s.llm_api_key, s.llm_model, s.llm_temperature, s.llm_max_tokens, s.llm_extra, s.llm_timeout
        )

    def _body(self, messages, stream: bool, **kwargs: Any) -> dict[str, Any]:
        body = {
            "model": kwargs.pop("model", self.model),
            "messages": messages,
            "temperature": kwargs.pop("temperature", self.temperature),
            "max_tokens": kwargs.pop("max_tokens", self.max_tokens),
            **self.extra,
            **kwargs,
        }
        if stream:
            body["stream"] = True
            body["stream_options"] = {"include_usage": True}
        return body

    def _wait(self, response: httpx.Response | None, attempt: int) -> None:
        delay = float(min(2**attempt, 60))
        if response is not None:
            try:
                delay = max(delay, float(response.headers.get("retry-after", 0)))
            except ValueError:
                pass
            if delay > self.max_wait:
                raise LLMError(f"rate limit: retry after {delay:.0f} s ({response.text[:300]})")
        time.sleep(delay)

    def _post(self, body: dict[str, Any]) -> httpx.Response:
        for attempt in range(self.retries + 1):
            try:
                response = self.client.post("/chat/completions", json=body)
            except httpx.TransportError:
                if attempt == self.retries:
                    raise
                self._wait(None, attempt)
                continue
            if response.status_code in (429, 500, 502, 503, 504) and attempt < self.retries:
                self._wait(response, attempt)
                continue
            if response.status_code >= 400:
                raise LLMError(f"LLM API error {response.status_code}: {response.text[:500]}")
            return response
        raise LLMError("unreachable")

    def complete(self, messages: list[dict[str, str]], **kwargs: Any) -> Completion:
        data = self._post(self._body(messages, False, **kwargs)).json()
        usage = data.get("usage") or {}
        return Completion(
            text=(data["choices"][0]["message"].get("content") or "").strip(),
            model=data.get("model", self.model),
            prompt_tokens=int(usage.get("prompt_tokens", 0)),
            completion_tokens=int(usage.get("completion_tokens", 0)),
        )

    def stream(self, messages: list[dict[str, str]], **kwargs: Any) -> Iterator[str | Completion]:
        body = self._body(messages, True, **kwargs)
        parts: list[str] = []
        usage: dict[str, Any] = {}
        model = body["model"]
        with self.client.stream("POST", "/chat/completions", json=body) as response:
            if response.status_code >= 400:
                response.read()
                raise LLMError(f"LLM API error {response.status_code}: {response.text[:500]}")
            for line in response.iter_lines():
                if not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if payload == "[DONE]":
                    break
                chunk = json.loads(payload)
                model = chunk.get("model", model)
                usage = chunk.get("usage") or (chunk.get("x_groq") or {}).get("usage") or usage
                for choice in chunk.get("choices") or []:
                    delta = (choice.get("delta") or {}).get("content")
                    if delta:
                        parts.append(delta)
                        yield delta
        yield Completion(
            "".join(parts).strip(), model, int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0))
        )
