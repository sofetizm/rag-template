import math
from collections import Counter

import pytest

from rag_template.documents import Chunk, Document
from rag_template.models import BM25Encoder, HashEmbedder
from rag_template.retriever import RetrievalParams, rrf
from rag_template.store import Hit
from rag_template.text import tokenize

from .conftest import LexicalReranker, make_components


def test_bm25_scores_match_reference_formula():
    texts = [
        "кошка сидит на окне",
        "кошка и собака",
        "собака лает на кошку и кошку",
        "рыба плавает",
        "окно открыто",
        "кошки спят",
    ]
    c = make_components()
    chunks = [
        Chunk(id=f"00000000-0000-0000-0000-00000000000{i}", source=str(i), title="", section="", text=t, position=0)
        for i, t in enumerate(texts)
    ]
    c.indexer.index_chunks(chunks)
    enc = c.encoder
    docs = [tokenize(t) for t in texts]
    avgdl = sum(map(len, docs)) / len(docs)
    assert enc.avgdl == pytest.approx(avgdl)

    query = "кошка на окне"
    expected = {}
    for i, d in enumerate(docs):
        tf = Counter(d)
        score = 0.0
        for term in set(tokenize(query)):
            n = sum(term in x for x in docs)
            if not tf[term]:
                continue
            idf = math.log((len(docs) - n + 0.5) / (n + 0.5) + 1)
            score += idf * tf[term] * (enc.k1 + 1) / (tf[term] + enc.k1 * (1 - enc.b + enc.b * len(d) / avgdl))
        if score:
            expected[str(i)] = score
    hits = c.retriever.search_bm25(query, 10)
    assert {h.source: pytest.approx(h.score, rel=1e-4) for h in hits} == expected


def test_rrf_rewards_documents_found_by_both():
    a = [Hit("x", 1, {}), Hit("y", 1, {}), Hit("z", 1, {})]
    b = [Hit("y", 1, {}), Hit("w", 1, {})]
    fused = rrf([a, b], k=60)
    assert [h.id for h in fused][:2] == ["y", "x"]
    assert fused[0].score == pytest.approx(1 / 62 + 1 / 61)


def test_modes_and_rerank(small_docs):
    c = make_components(small_docs, reranker=LexicalReranker())
    for mode in ("bm25", "dense", "hybrid"):
        hits = c.retriever.retrieve("чем питаются кошки", RetrievalParams(mode=mode, rerank=False, top_k=2))
        assert hits[0].source == "cats.md", mode
    hits = c.retriever.retrieve("кошки едят", RetrievalParams(mode="hybrid", rerank=True, top_k=3))
    assert "rerank" in hits[0].scores and hits[0].source == "cats.md"
    assert [h.score for h in hits] == sorted([h.score for h in hits], reverse=True)


def test_incremental_indexing(small_docs):
    c = make_components()
    first = c.indexer.index(small_docs)
    assert (first.added, first.chunks) == (3, c.store.count())
    again = c.indexer.index(small_docs)
    assert (again.added, again.updated, again.unchanged, again.chunks) == (0, 0, 3, 0)
    assert again.version == first.version

    changed = [Document("cats.md", "# Кошки\n\nКошки теперь едят только корм."), *small_docs[1:]]
    report = c.indexer.index(changed)
    assert report.updated == 1 and report.version != first.version
    texts = [h.text for h in c.retriever.retrieve("кошки", RetrievalParams(mode="bm25", rerank=False))]
    assert any("корм" in t for t in texts) and not any("мышей" in t for t in texts)

    pruned = c.indexer.index(small_docs[1:], prune=True)
    assert pruned.removed == 1
    assert "cats.md" not in c.store.documents()
    assert all(h.source != "cats.md" for h in c.retriever.retrieve("кошки", RetrievalParams(mode="bm25", rerank=False)))


def test_collection_built_with_other_embedder_is_rejected(small_docs):
    c = make_components(small_docs)
    c.indexer.embedder = HashEmbedder(dim=64)
    with pytest.raises(ValueError, match="rebuild"):
        c.indexer.index(small_docs)


def test_demo_corpus_finds_the_right_page(demo):
    hits = demo.retriever.retrieve("Как вернуть клиенту ошибку 404 через HTTPException?")
    assert hits[0].source == "tutorial/handling-errors.md"
    assert hits[0].payload["url"].startswith("https://fastapi.tiangolo.com/ru/tutorial/handling-errors/")


def test_bm25_encoder_merges_hash_collisions():
    enc = BM25Encoder()
    indices, values = enc.encode_document("слово слово другое")
    assert len(indices) == len(set(indices)) == 2
