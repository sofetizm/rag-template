from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pytest
from qdrant_client import QdrantClient

from rag_template.config import Settings
from rag_template.documents import Document
from rag_template.factory import build
from rag_template.llm import Completion
from rag_template.loaders import load_path
from rag_template.models import HashEmbedder
from rag_template.pipeline import REFUSAL
from rag_template.store import QdrantStore
from rag_template.text import tokenize

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "data" / "demo" / "fastapi-ru"
GOLDEN = ROOT / "data" / "golden" / "fastapi_ru.jsonl"


class FakeLLM:
    """Answers with the first sentence of the first fragment and cites it; refuses for unknown topics."""

    model = "openai/gpt-oss-120b"

    def __init__(self, refuse_words: tuple[str, ...] = ("kafka",)):
        self.refuse_words = refuse_words
        self.calls: list[list[dict]] = []

    def _text(self, messages) -> str:
        user = messages[-1]["content"]
        question = user.rsplit("Вопрос:", 1)[-1].lower()
        if any(w in question for w in self.refuse_words):
            return REFUSAL
        first = re.search(r"\[1\][^\n]*\n(.+)", user)
        sentence = first.group(1).split(". ")[0][:200] if first else "ответ"
        return f"{sentence} [1]."

    def complete(self, messages, **kwargs) -> Completion:
        self.calls.append(messages)
        return Completion(self._text(messages), self.model, prompt_tokens=1000, completion_tokens=100)

    def stream(self, messages, **kwargs):
        self.calls.append(messages)
        text = self._text(messages)
        for word in text.split(" "):
            yield word + " "
        yield Completion(text, self.model, 1000, 100)


class LexicalReranker:
    name = "lexical"

    def score(self, query, texts):
        q = set(tokenize(query))
        return np.array([len(q & set(tokenize(t))) / (len(q) or 1) for t in texts], dtype=np.float32)


def make_settings(**kw) -> Settings:
    base = dict(embedding_backend="hash", reranker_backend="none", cache_backend="memory", _env_file=None)
    return Settings(**{**base, **kw})


def make_components(docs=None, reranker=None, llm=None, **kw):
    settings = make_settings(**kw)
    store = QdrantStore(QdrantClient(":memory:"), settings.collection)
    c = build(settings, embedder=HashEmbedder(), reranker=reranker, llm=llm or FakeLLM(), store=store)
    if reranker is not None:
        c.retriever.params.rerank = True
    if docs:
        c.indexer.index(docs)
    return c


@pytest.fixture(scope="session")
def demo_docs() -> list[Document]:
    return load_path(DEMO, base_url="https://fastapi.tiangolo.com/ru/")


@pytest.fixture(scope="session")
def demo(demo_docs):
    return make_components(demo_docs, reranker=LexicalReranker())


@pytest.fixture
def small_docs() -> list[Document]:
    return [
        Document(
            "cats.md", "# Кошки\n\nКошки любят спать на солнце и ловить мышей.\n\n## Еда\n\nКошки едят рыбу и мясо."
        ),
        Document("dogs.md", "# Собаки\n\nСобаки охраняют дом и любят долгие прогулки.\n\n## Еда\n\nСобаки едят кости."),
        Document("python.md", "# Python\n\nФункция `async def` объявляет сопрограмму. Используйте await внутри."),
    ]
