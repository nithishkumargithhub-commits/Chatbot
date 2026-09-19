"""
main.py — JeevanPath AI FastAPI Application Entry Point (v0.2.0)

Startup sequence
----------------
  1. Configure structured logging (structlog JSON / dev-console).
  2. Pre-load the STT engine (model warm on first request).
  3. Configure CORS from settings.
  4. Mount all API routers.
  5. Expose health-check and Prometheus /metrics endpoints.

Backward compatibility
----------------------
  * The Phase 1 endpoint POST /api/voice/transcribe is preserved as-is
    under routes/voice.py (the original file, unchanged).
  * The new engine-based router will live at api/v1/ in Phase 2/3.
    Nothing is broken or removed.

Run with:
    cd backend
    uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Core
from core.config import settings
from core.logging import configure_logging, get_logger
from core.dependencies import get_stt_engine

# Logging must be configured before any other import that logs at module level
configure_logging()
logger = get_logger(__name__)

# Prometheus (conditional)
if settings.metrics_enabled:
    from prometheus_client import make_asgi_app as _make_metrics_app


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI lifespan context manager.

    Startup:
      - Eagerly load the STT engine so the first request is not slow.
      - Future: pre-warm LLM, embedding, TTS (deferred to Phase 2 — those
        models are not yet wired in service logic).

    Shutdown:
      - Placeholder for future GPU memory release / connection pool close.
    """
    logger.info(
        "jeevanpath_startup",
        version=settings.app_version,
        environment=settings.environment,
        stt_model=settings.stt_model_size,
        device=settings.device,
        compute_type=settings.stt_compute_type,
        llm_model=settings.llm_model_name,
        embedding_model=settings.embedding_model_name,
    )

    # Pre-load STT engine (10–30 s on first run while the model downloads)
    try:
        stt = await asyncio.get_event_loop().run_in_executor(None, get_stt_engine)
        logger.info("stt_engine_ready", engine=settings.stt_engine)
    except Exception as exc:
        # Non-fatal: server starts, /health shows degraded, /transcribe → 503
        logger.error(
            "stt_engine_load_failed",
            error=str(exc),
            hint="The /api/voice/transcribe endpoint will return 503.",
        )

    logger.info(
        "jeevanpath_ready",
        docs_url="http://localhost:8000/docs",
        health_url="http://localhost:8000/health",
    )

    yield   # ← server is live and serving requests

    # Shutdown
    logger.info("jeevanpath_shutdown")


# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.app_name,
    description=(
        "AI-Driven Voice Assistant for Livelihood Mapping and NSQF-Aligned "
        "Skilling Recommendations.\n\n"
        "**Phase 1** (live): Speech-to-text with automatic Indian language detection "
        "using locally running Whisper (faster-whisper on GPU).\n\n"
        "**Phase 2** (in progress): Full pipeline — intent → knowledge search → "
        "guidance generation → Indic TTS."
    ),
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

# Request ID injection middleware — binds request_id to the logging context
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from core.logging import bind_request_context


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Inject a unique request_id into every request's log context."""

    async def dispatch(self, request: Request, call_next: any) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        bind_request_context(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


app.add_middleware(RequestContextMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Prometheus metrics endpoint
# ---------------------------------------------------------------------------

if settings.metrics_enabled:
    metrics_app = _make_metrics_app()
    app.mount(settings.metrics_path, metrics_app)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

# Phase 1 voice router (preserved, backward-compatible)
from routes.voice import router as voice_router_v1
app.include_router(voice_router_v1)

# Phase 2 routers go here as they are implemented, e.g.:
# from api.v1.voice import router as voice_router_v2
# app.include_router(voice_router_v2, prefix="/api/v1")

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["system"], summary="Backend health check")
async def health_check() -> dict:
    """
    Returns the service status, model configuration, and engine readiness.

    The ``stt_ready`` flag indicates whether the Whisper model is loaded.
    A ``false`` value means the model is still initialising or failed to load.
    """
    from core.dependencies import _stt_instance
    stt_ready = _stt_instance is not None and _stt_instance.is_ready()

    return {
        "status": "ok" if stt_ready else "degraded",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "stt": {
            "engine": settings.stt_engine,
            "model": settings.stt_model_size,
            "device": settings.device,
            "compute_type": settings.stt_compute_type,
            "ready": stt_ready,
        },
        "llm": {
            "engine": settings.llm_engine,
            "model": settings.llm_model_name,
        },
        "embedding": {
            "engine": settings.embedding_engine,
            "model": settings.embedding_model_name,
            "dim": settings.embedding_dim,
        },
        "tts": {
            "engine": settings.tts_engine,
        },
    }
