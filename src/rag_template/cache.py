from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from collections import OrderedDict
from typing import Any, Protocol

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client import models as qm

from .store import create_indexes


def normalize_question(question: str) -> str:
    text = re.sub(r"\s+", " ", question.lower().replace("ё", "е")).strip()
    return text.rstrip("?!. ")


def cache_key(question: str, version: str, fingerprint: str) -> str:
    raw = f"{version}|{fingerprint}|{normalize_question(question)}"
    return "rag:answer:" + hashlib.sha256(raw.encode()).hexdigest()


class Cache(Protocol):
    def get(self, key: str) -> dict[str, Any] | None: ...

    def set(self, key: str, value: dict[str, Any], ttl: int) -> None: ...


class MemoryCache:
    def __init__(self, max_items: int = 10_000):
        self.max_items = max_items
        self._data: OrderedDict[str, tuple[float, dict[str, Any]]] = OrderedDict()

    def get(self, key: str) -> dict[str, Any] | None:
        item = self._data.get(key)
        if item is None:
            return None
        expires, value = item
        if expires < time.time():
            del self._data[key]
            return None
        self._data.move_to_end(key)
        return value

    def set(self, key: str, value: dict[str, Any], ttl: int) -> None:
        self._data[key] = (time.time() + ttl, value)
        self._data.move_to_end(key)
        while len(self._data) > self.max_items:
            self._data.popitem(last=False)


class RedisCache:
    def __init__(self, url: str | None = None, client=None):
        if client is None:
            import redis

            client = redis.Redis.from_url(url)
        self.client = client

    def get(self, key: str) -> dict[str, Any] | None:
        raw = self.client.get(key)
        return json.loads(raw) if raw else None

    def set(self, key: str, value: dict[str, Any], ttl: int) -> None:
        self.client.set(key, json.dumps(value, ensure_ascii=False), ex=ttl)


class SemanticCache:
    """Answers for questions whose embedding is close to an earlier one.

    A wrong hit returns the answer to a different question, so the threshold
    has to be measured (see eval/cache), not guessed.
    """

    def __init__(self, client: QdrantClient, collection: str, dim: int, threshold: float, ttl: int):
        self.client = client
        self.collection = f"{collection}__cache"
        self.threshold = threshold
        self.ttl = ttl
        if not client.collection_exists(self.collection):
            client.create_collection(
                self.collection, vectors_config=qm.VectorParams(size=dim, distance=qm.Distance.COSINE)
            )
            create_indexes(
                client,
                self.collection,
                {
                    "version": qm.PayloadSchemaType.KEYWORD,
                    "fingerprint": qm.PayloadSchemaType.KEYWORD,
                    "expires": qm.PayloadSchemaType.FLOAT,
                },
            )

    def get(self, vector: np.ndarray, version: str, fingerprint: str) -> tuple[dict[str, Any], float] | None:
        flt = qm.Filter(
            must=[
                qm.FieldCondition(key="version", match=qm.MatchValue(value=version)),
                qm.FieldCondition(key="fingerprint", match=qm.MatchValue(value=fingerprint)),
                qm.FieldCondition(key="expires", range=qm.Range(gt=time.time())),
            ]
        )
        res = self.client.query_points(
            self.collection,
            query=vector.tolist(),
            query_filter=flt,
            limit=1,
            score_threshold=self.threshold,
            with_payload=True,
        )
        if not res.points:
            return None
        point = res.points[0]
        return json.loads(point.payload["answer"]), float(point.score)

    def set(self, vector: np.ndarray, question: str, answer: dict[str, Any], version: str, fingerprint: str) -> None:
        payload = {
            "question": question,
            "answer": json.dumps(answer, ensure_ascii=False),
            "version": version,
            "fingerprint": fingerprint,
            "expires": time.time() + self.ttl,
        }
        self.client.upsert(
            self.collection, [qm.PointStruct(id=str(uuid.uuid4()), vector=vector.tolist(), payload=payload)]
        )


def build_cache(settings) -> Cache | None:
    if settings.cache_backend == "none":
        return None
    if settings.cache_backend == "redis":
        return RedisCache(settings.redis_url)
    return MemoryCache()
