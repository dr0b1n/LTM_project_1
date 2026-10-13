"""Generate and validate local text embeddings through Ollama."""

from __future__ import annotations

import math
import os
from collections.abc import Sequence

from app.services.ollama_client import get_ollama_client


DEFAULT_EMBEDDING_MODEL = "granite-embedding:30m"

EMBEDDING_MODEL = (
    os.getenv(
        "OLLAMA_EMBEDDING_MODEL",
        DEFAULT_EMBEDDING_MODEL,
    ).strip()
    or DEFAULT_EMBEDDING_MODEL
)

EXPECTED_DIMENSION = 384


class EmbeddingError(RuntimeError):
    """Raised when local embedding generation fails validation."""


def _validate_input(
    texts: Sequence[str],
) -> list[str]:
    """Normalize and validate embedding input."""

    if isinstance(texts, (str, bytes)):
        raise EmbeddingError(
            "Embedding input must be a sequence of strings, "
            "not one plain string."
        )

    if not texts:
        raise EmbeddingError(
            "Embedding input must contain at least one text."
        )

    clean_texts: list[str] = []

    for index, text in enumerate(texts):
        if not isinstance(text, str):
            raise EmbeddingError(
                f"Embedding input item {index} must be a string."
            )

        clean_text = text.strip()

        if not clean_text:
            raise EmbeddingError(
                f"Embedding input item {index} must not be empty."
            )

        clean_texts.append(clean_text)

    return clean_texts


def _extract_embeddings(response: object) -> object:
    """Extract embeddings from object-style or dictionary responses."""

    embeddings = getattr(response, "embeddings", None)

    if embeddings is None and isinstance(response, dict):
        embeddings = response.get("embeddings")

    return embeddings


def _normalize_embeddings(
    embeddings: object,
    expected_count: int,
) -> list[list[float]]:
    """Validate embedding count, numeric values, and dimensions."""

    if not isinstance(embeddings, (list, tuple)):
        raise EmbeddingError(
            "Ollama returned no usable embeddings."
        )

    if len(embeddings) != expected_count:
        raise EmbeddingError(
            "Ollama returned an unexpected embedding count. "
            f"Expected {expected_count}; received {len(embeddings)}."
        )

    normalized: list[list[float]] = []

    for embedding_index, vector in enumerate(embeddings):
        if isinstance(vector, (str, bytes)):
            raise EmbeddingError(
                "Ollama returned an invalid embedding vector "
                f"at index {embedding_index}."
            )

        try:
            normalized_vector = [float(value) for value in vector]
        except (TypeError, ValueError) as exc:
            raise EmbeddingError(
                "Ollama returned a non-numeric embedding "
                f"at index {embedding_index}."
            ) from exc

        if len(normalized_vector) != EXPECTED_DIMENSION:
            raise EmbeddingError(
                "Ollama returned an unexpected embedding dimension "
                f"at index {embedding_index}. "
                f"Expected {EXPECTED_DIMENSION}; "
                f"received {len(normalized_vector)}."
            )

        if not all(math.isfinite(value) for value in normalized_vector):
            raise EmbeddingError(
                "Ollama returned a non-finite embedding value "
                f"at index {embedding_index}."
            )

        normalized.append(normalized_vector)

    return normalized


def embed_texts(
    texts: Sequence[str],
    model: str = EMBEDDING_MODEL,
) -> list[list[float]]:
    """Generate validated embeddings for non-empty text inputs."""

    clean_texts = _validate_input(texts)

    if not isinstance(model, str):
        raise EmbeddingError(
            "The embedding model name must be a string."
        )

    clean_model = model.strip()

    if not clean_model:
        raise EmbeddingError(
            "The embedding model name must not be empty."
        )

    try:
        client = get_ollama_client()
        response = client.embed(
            model=clean_model,
            input=clean_texts,
        )
    except Exception as exc:
        raise EmbeddingError(
            "Ollama could not generate embeddings with "
            f"{clean_model}. Verify that Ollama is reachable "
            "and that the embedding model is installed."
        ) from exc

    embeddings = _extract_embeddings(response)

    return _normalize_embeddings(
        embeddings,
        expected_count=len(clean_texts),
    )
