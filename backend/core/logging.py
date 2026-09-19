"""
core/logging.py — JeevanPath AI: Structured JSON Logging

Sets up structlog with:
  * JSON output in production / "json" format setting
  * Human-readable colourised output in development / "console" format setting
  * request_id and turn_id automatically injected into every log record
    via Python contextvars (no need to thread them through function args).
  * Standard library `logging` bridge so that third-party libraries
    (uvicorn, SQLAlchemy, faster-whisper) emit records in the same format.

Usage
-----
    from core.logging import get_logger, bind_request_context

    logger = get_logger(__name__)

    # At the start of each request (e.g. in a FastAPI middleware):
    bind_request_context(request_id="abc-123", turn_id="t-1")

    logger.info("transcription_complete", lang="ta", duration=2.3)
    # → {"event": "transcription_complete", "lang": "ta", "duration": 2.3,
    #    "request_id": "abc-123", "turn_id": "t-1", "timestamp": "...", ...}
"""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar
from typing import Any

import structlog

from core.config import settings

# ---------------------------------------------------------------------------
# Context variables — set once per request, read by every log call
# ---------------------------------------------------------------------------

_request_id: ContextVar[str] = ContextVar("request_id", default="-")
_turn_id: ContextVar[str] = ContextVar("turn_id", default="-")


def bind_request_context(request_id: str, turn_id: str = "-") -> None:
    """
    Bind request_id and turn_id to the current async context.

    Call this at the very start of each request (e.g. in middleware) so that
    every downstream log statement automatically carries these identifiers.
    """
    _request_id.set(request_id)
    _turn_id.set(turn_id)


def _add_request_context(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """structlog processor: inject request_id and turn_id from contextvars."""
    event_dict["request_id"] = _request_id.get()
    event_dict["turn_id"] = _turn_id.get()
    return event_dict


# ---------------------------------------------------------------------------
# Shared processor chain
# ---------------------------------------------------------------------------

_SHARED_PROCESSORS: list[Any] = [
    # Inject contextvars
    _add_request_context,
    # Add log level as a string
    structlog.stdlib.add_log_level,
    # Add logger name
    structlog.stdlib.add_logger_name,
    # ISO-8601 timestamp
    structlog.processors.TimeStamper(fmt="iso"),
    # Render exception info if present
    structlog.processors.StackInfoRenderer(),
    structlog.processors.ExceptionRenderer(),
]


def _get_renderer() -> Any:
    """Return the final renderer based on log_format setting."""
    if settings.log_format == "json":
        return structlog.processors.JSONRenderer()
    # Development: pretty colourised output
    return structlog.dev.ConsoleRenderer(colors=True)


# ---------------------------------------------------------------------------
# One-time configuration
# ---------------------------------------------------------------------------

def configure_logging() -> None:
    """
    Configure structlog and the standard library logging bridge.

    Call this exactly once, at application startup (in main.py lifespan).
    Subsequent calls are safe but redundant.
    """
    structlog.configure(
        processors=_SHARED_PROCESSORS + [
            # Prepare the event for the stdlib handler
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        # This chain runs on stdlib log records that arrive via the bridge.
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            _get_renderer(),
        ],
        foreign_pre_chain=_SHARED_PROCESSORS,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.log_level)

    # Silence noisy third-party loggers in production
    if settings.environment == "production":
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Return a structlog BoundLogger for the given module name.

    Prefer this over `logging.getLogger()` in all JeevanPath modules.

    Example:
        logger = get_logger(__name__)
        logger.info("model_loaded", model="large-v3", device="cuda")
    """
    return structlog.get_logger(name)
