from collections.abc import Sequence

import ollama

EMBEDDING_MODEL = "granite-embedding:30m"
EXPECTED_DIMENSION = 384


class EmbeddingError(RuntimeError):
    """Raised when local embedding generation fails validation."""


def embed_texts(
    texts: Sequence[str],
    model: str = EMBEDDING_MODEL,
) -> list[list[float]]:
    clean_texts = [text.strip() for text in texts]
    if not clean_texts or any(not text for text in clean_texts):
        raise EmbeddingError("Embedding input must contain non-empty text.")

    try:
        response = ollama.embed(model=model, input=clean_texts)
    except Exception as exc:
        raise EmbeddingError(
            f"Ollama could not generate embeddings with {model}."
        ) from exc

    embeddings = getattr(response, "embeddings", None)
    if embeddings is None and isinstance(response, dict):
        embeddings = response.get("embeddings")

    if not embeddings or len(embeddings) != len(clean_texts):
        raise EmbeddingError("Ollama returned an unexpected embedding count.")

    normalized = [list(vector) for vector in embeddings]
    dimensions = {len(vector) for vector in normalized}
    if dimensions != {EXPECTED_DIMENSION}:
        raise EmbeddingError(
            f"Expected {EXPECTED_DIMENSION}-dimensional embeddings; "
            f"received dimensions {sorted(dimensions)}."
        )

    return normalized
