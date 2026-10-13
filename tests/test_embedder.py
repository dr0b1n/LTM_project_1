"""Tests for validated Ollama embedding generation."""

from __future__ import annotations

import math

import pytest

from app.services import embedder
from app.services.embedder import EmbeddingError


def make_vector(value: float = 0.1) -> list[float]:
    """Return one valid embedding vector for controlled tests."""

    return [value] * embedder.EXPECTED_DIMENSION


class FakeEmbeddingClient:
    """Small Ollama client substitute used by unit tests."""

    def __init__(self, response: object) -> None:
        self.response = response
        self.last_model: str | None = None
        self.last_input: list[str] | None = None

    def embed(
        self,
        *,
        model: str,
        input: list[str],
    ) -> object:
        self.last_model = model
        self.last_input = input
        return self.response


def test_embed_texts_validates_dimension(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = FakeEmbeddingClient(
        {"embeddings": [make_vector()]}
    )

    monkeypatch.setattr(
        embedder,
        "get_ollama_client",
        lambda: client,
    )

    result = embedder.embed_texts(
        [" Vendor encryption requirement "]
    )

    assert len(result) == 1
    assert len(result[0]) == embedder.EXPECTED_DIMENSION
    assert client.last_model == embedder.EMBEDDING_MODEL
    assert client.last_input == ["Vendor encryption requirement"]


def test_embed_texts_rejects_wrong_dimension(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = FakeEmbeddingClient(
        {"embeddings": [[0.1] * 10]}
    )

    monkeypatch.setattr(
        embedder,
        "get_ollama_client",
        lambda: client,
    )

    with pytest.raises(
        EmbeddingError,
        match="unexpected embedding dimension",
    ):
        embedder.embed_texts(["Contract clause"])


def test_embed_texts_supports_object_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Response:
        embeddings = [make_vector(0.2)]

    client = FakeEmbeddingClient(Response())

    monkeypatch.setattr(
        embedder,
        "get_ollama_client",
        lambda: client,
    )

    result = embedder.embed_texts(["Contract evidence"])

    assert len(result) == 1
    assert len(result[0]) == embedder.EXPECTED_DIMENSION


@pytest.mark.parametrize(
    "texts",
    [
        [],
        [""],
        ["   "],
        ["valid", ""],
    ],
)
def test_embed_texts_rejects_empty_input(
    texts: list[str],
) -> None:
    with pytest.raises(EmbeddingError):
        embedder.embed_texts(texts)


def test_embed_texts_rejects_plain_string() -> None:
    with pytest.raises(
        EmbeddingError,
        match="not one plain string",
    ):
        embedder.embed_texts(
            "This must not be treated as individual characters."
        )


def test_embed_texts_rejects_wrong_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = FakeEmbeddingClient(
        {"embeddings": [make_vector()]}
    )

    monkeypatch.setattr(
        embedder,
        "get_ollama_client",
        lambda: client,
    )

    with pytest.raises(
        EmbeddingError,
        match="unexpected embedding count",
    ):
        embedder.embed_texts(
            ["Clause one", "Clause two"]
        )


def test_embed_texts_rejects_non_finite_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    vector = make_vector()
    vector[10] = math.nan
    client = FakeEmbeddingClient(
        {"embeddings": [vector]}
    )

    monkeypatch.setattr(
        embedder,
        "get_ollama_client",
        lambda: client,
    )

    with pytest.raises(
        EmbeddingError,
        match="non-finite",
    ):
        embedder.embed_texts(["Contract clause"])


def test_embed_texts_wraps_client_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailedClient:
        def embed(self, **kwargs: object) -> object:
            raise ConnectionError("Controlled test failure")

    monkeypatch.setattr(
        embedder,
        "get_ollama_client",
        lambda: FailedClient(),
    )

    with pytest.raises(
        EmbeddingError,
        match="could not generate embeddings",
    ):
        embedder.embed_texts(["Contract clause"])
