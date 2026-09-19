"""
core/dependencies.py — JeevanPath AI: FastAPI Dependency Factories

All engine singletons are accessed via FastAPI Depends() so that:
  1. Each engine is created exactly once per process (lazy singleton).
  2. Tests can override any dependency with a fake implementation:
        app.dependency_overrides[get_stt_engine] = lambda: FakeSTTEngine()
  3. No business logic imports engines directly — they always receive them
     injected, keeping services testable in isolation.

Usage (in a router):
    from core.dependencies import get_stt_engine, STTEngineDep
    from typing import Annotated
    from fastapi import Depends

    async def my_endpoint(stt: STTEngineDep) -> ...:
        result = await stt.transcribe(audio_path)

The `*Dep` type aliases use `Annotated[..., Depends(...)]` (FastAPI 0.95+
style) so endpoints are cleanly typed without repeating the Depends call.
"""

from __future__ import annotations

import threading
from typing import Annotated

from fastapi import Depends

from engines.base import EmbeddingEngine, LLMEngine, STTEngine, TTSEngine


# ---------------------------------------------------------------------------
# Thread-safe lazy singletons
# ---------------------------------------------------------------------------
# Each lock ensures that the heavy model is loaded only once even if
# multiple async workers race to the first request.

_stt_lock = threading.Lock()
_stt_instance: STTEngine | None = None

_llm_lock = threading.Lock()
_llm_instance: LLMEngine | None = None

_emb_lock = threading.Lock()
_emb_instance: EmbeddingEngine | None = None

_tts_lock = threading.Lock()
_tts_instance: TTSEngine | None = None


# ---------------------------------------------------------------------------
# Factory functions
# ---------------------------------------------------------------------------

def get_stt_engine() -> STTEngine:
    """
    Return the global STT engine singleton.

    The concrete implementation is chosen by ``settings.stt_engine``:
    * ``"faster_whisper"`` → FasterWhisperSTTEngine (GPU/CPU)
    * ``"fake"``           → FakeSTTEngine (deterministic, for tests)
    """
    global _stt_instance
    if _stt_instance is None:
        with _stt_lock:
            if _stt_instance is None:
                _stt_instance = _build_stt_engine()
    return _stt_instance


def get_llm_engine() -> LLMEngine:
    """Return the global LLM engine singleton."""
    global _llm_instance
    if _llm_instance is None:
        with _llm_lock:
            if _llm_instance is None:
                _llm_instance = _build_llm_engine()
    return _llm_instance


def get_embedding_engine() -> EmbeddingEngine:
    """Return the global Embedding engine singleton."""
    global _emb_instance
    if _emb_instance is None:
        with _emb_lock:
            if _emb_instance is None:
                _emb_instance = _build_embedding_engine()
    return _emb_instance


def get_tts_engine() -> TTSEngine:
    """Return the global TTS engine singleton."""
    global _tts_instance
    if _tts_instance is None:
        with _tts_lock:
            if _tts_instance is None:
                _tts_instance = _build_tts_engine()
    return _tts_instance


# ---------------------------------------------------------------------------
# FastAPI Annotated type aliases  (use these in endpoint signatures)
# ---------------------------------------------------------------------------
STTEngineDep = Annotated[STTEngine, Depends(get_stt_engine)]
LLMEngineDep = Annotated[LLMEngine, Depends(get_llm_engine)]
EmbeddingEngineDep = Annotated[EmbeddingEngine, Depends(get_embedding_engine)]
TTSEngineDep = Annotated[TTSEngine, Depends(get_tts_engine)]


# ---------------------------------------------------------------------------
# Internal builders — config-driven factory pattern
# ---------------------------------------------------------------------------

def _build_stt_engine() -> STTEngine:
    from core.config import settings
    if settings.stt_engine == "faster_whisper":
        from engines.stt.faster_whisper_engine import FasterWhisperSTTEngine
        return FasterWhisperSTTEngine()
    if settings.stt_engine == "fake":
        from engines.stt.fake_engine import FakeSTTEngine
        return FakeSTTEngine()
    raise ValueError(f"Unknown stt_engine: {settings.stt_engine!r}")


def _build_llm_engine() -> LLMEngine:
    from core.config import settings
    if settings.llm_engine == "hf_local":
        from engines.llm.hf_local_engine import HFLocalLLMEngine
        return HFLocalLLMEngine()
    if settings.llm_engine == "fake":
        from engines.llm.fake_engine import FakeLLMEngine
        return FakeLLMEngine()
    raise ValueError(f"Unknown llm_engine: {settings.llm_engine!r}")


def _build_embedding_engine() -> EmbeddingEngine:
    from core.config import settings
    if settings.embedding_engine == "sentence_transformer":
        from engines.embedding.sentence_transformer_engine import SentenceTransformerEmbeddingEngine
        return SentenceTransformerEmbeddingEngine()
    if settings.embedding_engine == "fake":
        from engines.embedding.fake_engine import FakeEmbeddingEngine
        return FakeEmbeddingEngine()
    raise ValueError(f"Unknown embedding_engine: {settings.embedding_engine!r}")


def _build_tts_engine() -> TTSEngine:
    from core.config import settings
    if settings.tts_engine == "mms_tts":
        from engines.tts.mms_tts_engine import MMSTTSEngine
        return MMSTTSEngine()
    if settings.tts_engine == "fake":
        from engines.tts.fake_engine import FakeTTSEngine
        return FakeTTSEngine()
    raise ValueError(f"Unknown tts_engine: {settings.tts_engine!r}")
