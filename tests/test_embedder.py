import pytest

from app.services import embedder


def test_embed_texts_validates_dimension(monkeypatch) -> None:
    monkeypatch.setattr(
        embedder.ollama,
        "embed",
        lambda **kwargs: {"embeddings": [[0.1] * 384]},
    )
    vectors = embedder.embed_texts(["contract clause"] )
    assert len(vectors) == 1
    assert len(vectors[0]) == 384


def test_embed_texts_rejects_wrong_dimension(monkeypatch) -> None:
    monkeypatch.setattr(
        embedder.ollama,
        "embed",
        lambda **kwargs: {"embeddings": [[0.1] * 10]},
    )
    with pytest.raises(embedder.EmbeddingError, match="384-dimensional"):
        embedder.embed_texts(["contract clause"] )
