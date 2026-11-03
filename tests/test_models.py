"""Model wrappers on a tiny randomly initialised BERT saved locally, so no download is needed."""

import numpy as np
import pytest

pytest.importorskip("sentence_transformers")

from rag_template.models import CrossEncoderReranker, SentenceTransformerEmbedder, default_prefixes  # noqa: E402


@pytest.fixture(scope="module")
def tiny(tmp_path_factory):
    from transformers import BertConfig, BertForSequenceClassification, BertModel, BertTokenizerFast

    root = tmp_path_factory.mktemp("tiny")
    vocab = [
        "[PAD]",
        "[UNK]",
        "[CLS]",
        "[SEP]",
        "[MASK]",
        *"абвгдежзийклмнопрстуфхцчшщъыьэюяabcdefghijklmnopqrstuvwxyz",
    ]
    (root / "vocab.txt").write_text("\n".join(vocab))
    tokenizer = BertTokenizerFast(vocab_file=str(root / "vocab.txt"))
    config = BertConfig(
        vocab_size=len(vocab),
        hidden_size=32,
        num_hidden_layers=1,
        num_attention_heads=2,
        intermediate_size=64,
        max_position_embeddings=128,
    )
    BertModel(config).save_pretrained(root / "encoder")
    tokenizer.save_pretrained(root / "encoder")
    config.num_labels = 1
    BertForSequenceClassification(config).save_pretrained(root / "cross")
    tokenizer.save_pretrained(root / "cross")
    return root


def test_embedder_returns_normalized_vectors(tiny):
    embedder = SentenceTransformerEmbedder(str(tiny / "encoder"))
    vectors = embedder.embed_documents(["кошка", "собака ест"])
    assert vectors.shape == (2, embedder.dim) and np.allclose((vectors**2).sum(1), 1, atol=1e-5)
    assert embedder.embed_queries(["кошка"]).dtype == np.float32


def test_cross_encoder_scores_each_pair(tiny):
    scores = CrossEncoderReranker(str(tiny / "cross"), max_length=64).score("кошка", ["кошка ест", "собака"])
    assert scores.shape == (2,)
    assert CrossEncoderReranker(str(tiny / "cross")).score("q", []).shape == (0,)


def test_prefixes():
    assert default_prefixes("intfloat/multilingual-e5-small") == ("query: ", "passage: ")
    assert default_prefixes("BAAI/bge-m3") == ("", "")
