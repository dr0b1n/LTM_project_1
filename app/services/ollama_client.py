"""Shared configuration for the local Ollama API client."""

from __future__ import annotations

import os
from functools import lru_cache

from ollama import Client


DEFAULT_OLLAMA_HOST = "http://localhost:11434"


def get_ollama_host() -> str:
    """Return the configured Ollama API URL."""

    host = os.getenv(
        "OLLAMA_HOST",
        DEFAULT_OLLAMA_HOST,
    ).strip()

    if not host:
        return DEFAULT_OLLAMA_HOST

    if not host.startswith(
        ("http://", "https://")
    ):
        host = f"http://{host}"

    return host.rstrip("/")


@lru_cache(maxsize=1)
def get_ollama_client() -> Client:
    """Return a reusable Ollama client."""

    return Client(
        host=get_ollama_host(),
        timeout=300.0,
    )


def reset_ollama_client() -> None:
    """Clear the cached client for tests."""

    get_ollama_client.cache_clear()