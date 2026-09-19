"""
engines/embedding/sentence_transformer_engine.py — JeevanPath AI

Production embedding engine: sentence-transformers library.
Default model: ai4bharat/indic-sentence-bert-nli-v1 (768-dim).

Blocking CPU/GPU call — run via asyncio thread pool in callers.

Requirements:
    pip install sentence-transformers>=3.0.0
"""

from __future__ import annotations

import time

from core.config import settings
from core.logging import get_logger
from engines.base import EmbeddingEngine

logger = get_logger(__name__)


class SentenceTransformerEmbeddingEngine(EmbeddingEngine):
    """
    Sentence embedding engine backed by sentence-transformers.

    Produces L2-normalised vectors for use with pgvector cosine similarity.
    """

    def __init__(self) -> None:
        self._model = None
        self._dim: int = settings.embedding_dim
        self._load_model()

    def _load_model(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers is required. "
                "Install with: pip install sentence-transformers>=3.0.0"
            ) from exc

        model_name = settings.embedding_model_name
        logger.info("embedding_model_loading", model=model_name)

        self._model = SentenceTransformer(
            model_name,
            device=settings.device,
        )
        # Verify dimension matches config
        probe = self._model.encode(["probe"], normalize_embeddings=True)
        actual_dim = probe.shape[1]
        if actual_dim != settings.embedding_dim:
            logger.warning(
                "embedding_dim_mismatch",
                configured=settings.embedding_dim,
                actual=actual_dim,
                hint="Update EMBEDDING_DIM in .env to match the model.",
            )
            self._dim = actual_dim

        logger.info("embedding_model_ready", model=model_name, dim=self._dim)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self._model is None:
            raise RuntimeError("Embedding model is not loaded.")

        t_start = time.perf_counter()
        vectors = self._model.encode(
            texts,
            batch_size=settings.embedding_batch_size,
            normalize_embeddings=True,   # L2 normalise → cosine sim = dot product
            show_progress_bar=False,
        )
        elapsed = round(time.perf_counter() - t_start, 4)
        logger.debug(
            "embedding_complete",
            num_texts=len(texts),
            dim=self._dim,
            elapsed=elapsed,
        )
        return vectors.tolist()

    @property
    def dimension(self) -> int:
        return self._dim

    def is_ready(self) -> bool:
        return self._model is not None
