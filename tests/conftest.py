"""
tests/conftest.py — JeevanPath AI: pytest configuration and shared fixtures

All tests use fake engine implementations so that:
  * No GPU, model download, or DB is required in CI.
  * Tests are fast (< 1 s per test).
  * Engine logic is independently testable via dependency injection.
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Force test environment before any settings are read
# ---------------------------------------------------------------------------
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("STT_ENGINE", "fake")
os.environ.setdefault("LLM_ENGINE", "fake")
os.environ.setdefault("EMBEDDING_ENGINE", "fake")
os.environ.setdefault("TTS_ENGINE", "fake")
# No real DB needed for unit tests; point at a non-existent URL
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_jeevanpath")
os.environ.setdefault("DATABASE_SYNC_URL", "postgresql+psycopg2://test:test@localhost:5432/test_jeevanpath")
os.environ.setdefault("LOG_FORMAT", "console")

# Clear pydantic-settings cache so env overrides take effect
from core.config import get_settings
get_settings.cache_clear()


@pytest.fixture(scope="session")
def app():
    """Return the FastAPI app with fake engines injected."""
    from main import app as _app
    from core.dependencies import get_stt_engine, get_llm_engine, get_embedding_engine, get_tts_engine
    from engines.stt.fake_engine import FakeSTTEngine
    from engines.llm.fake_engine import FakeLLMEngine
    from engines.embedding.fake_engine import FakeEmbeddingEngine
    from engines.tts.fake_engine import FakeTTSEngine

    _app.dependency_overrides[get_stt_engine] = lambda: FakeSTTEngine()
    _app.dependency_overrides[get_llm_engine] = lambda: FakeLLMEngine()
    _app.dependency_overrides[get_embedding_engine] = lambda: FakeEmbeddingEngine()
    _app.dependency_overrides[get_tts_engine] = lambda: FakeTTSEngine()

    yield _app

    _app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def client(app):
    """Synchronous test client (httpx under the hood)."""
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
