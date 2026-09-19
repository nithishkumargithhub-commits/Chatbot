"""
engines/embedding/fake_engine.py — JeevanPath AI

Fake embedding engine for tests (returns zero vectors of the right dim).
"""

from __future__ import annotations

from core.config import settings
from engines.base import EmbeddingEngine


class FakeEmbeddingEngine(EmbeddingEngine):
    """Returns zero vectors of the correct dimension — useful for DB tests."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * settings.embedding_dim for _ in texts]

    @property
    def dimension(self) -> int:
        return settings.embedding_dim

    def is_ready(self) -> bool:
        return True
