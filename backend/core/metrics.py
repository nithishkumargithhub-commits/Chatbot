"""
core/metrics.py — JeevanPath AI: Prometheus Instrumentation

Every major pipeline stage has a dedicated Histogram so Grafana dashboards
can show P50/P95/P99 latency per stage.

Counter for error types allows alerting on transcription / LLM failures.

Usage
-----
    from core.metrics import METRICS

    with METRICS.stt_latency.time():   # context manager records duration
        result = stt_engine.transcribe(...)

    # OR manual:
    start = time.perf_counter()
    ...
    METRICS.stt_latency.observe(time.perf_counter() - start)

FastAPI mounts /metrics automatically (see main.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from prometheus_client import Counter, Histogram, Info

# ---------------------------------------------------------------------------
# Latency buckets — tuned for voice assistant real-time feel
# (values in seconds)
# ---------------------------------------------------------------------------
_LATENCY_BUCKETS = (
    0.05, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0,
    1.5, 2.0, 3.0, 5.0, 8.0, 12.0, 20.0,
)


@dataclass(frozen=True)
class _Metrics:
    """Prometheus metric objects — instantiated once, never mutated."""

    # ------------------------------------------------------------------ #
    # Stage latencies
    # ------------------------------------------------------------------ #
    stt_latency: Histogram = field(
        default_factory=lambda: Histogram(
            "jeevanpath_stt_latency_seconds",
            "Time to transcribe audio (faster-whisper)",
            buckets=_LATENCY_BUCKETS,
        )
    )
    intent_latency: Histogram = field(
        default_factory=lambda: Histogram(
            "jeevanpath_intent_latency_seconds",
            "Time to extract user intent (LLM)",
            buckets=_LATENCY_BUCKETS,
        )
    )
    embedding_latency: Histogram = field(
        default_factory=lambda: Histogram(
            "jeevanpath_embedding_latency_seconds",
            "Time to compute query embedding",
            buckets=_LATENCY_BUCKETS,
        )
    )
    search_latency: Histogram = field(
        default_factory=lambda: Histogram(
            "jeevanpath_knowledge_search_latency_seconds",
            "Time for pgvector similarity + BM25 search",
            buckets=_LATENCY_BUCKETS,
        )
    )
    ranking_latency: Histogram = field(
        default_factory=lambda: Histogram(
            "jeevanpath_ranking_latency_seconds",
            "Time to re-rank knowledge results",
            buckets=_LATENCY_BUCKETS,
        )
    )
    guidance_latency: Histogram = field(
        default_factory=lambda: Histogram(
            "jeevanpath_guidance_latency_seconds",
            "Time to generate guidance text (LLM)",
            buckets=_LATENCY_BUCKETS,
        )
    )
    tts_latency: Histogram = field(
        default_factory=lambda: Histogram(
            "jeevanpath_tts_latency_seconds",
            "Time to synthesize speech (MMS-TTS)",
            buckets=_LATENCY_BUCKETS,
        )
    )
    pipeline_latency: Histogram = field(
        default_factory=lambda: Histogram(
            "jeevanpath_pipeline_total_latency_seconds",
            "End-to-end pipeline latency (voice-in to voice-out)",
            buckets=_LATENCY_BUCKETS,
        )
    )

    # ------------------------------------------------------------------ #
    # Request / error counters
    # ------------------------------------------------------------------ #
    requests_total: Counter = field(
        default_factory=lambda: Counter(
            "jeevanpath_requests_total",
            "Total pipeline requests",
            ["language", "status"],     # labels: e.g. ("ta", "success")
        )
    )
    stt_errors_total: Counter = field(
        default_factory=lambda: Counter(
            "jeevanpath_stt_errors_total",
            "Total STT transcription errors",
        )
    )
    llm_errors_total: Counter = field(
        default_factory=lambda: Counter(
            "jeevanpath_llm_errors_total",
            "Total LLM inference errors",
        )
    )
    tts_errors_total: Counter = field(
        default_factory=lambda: Counter(
            "jeevanpath_tts_errors_total",
            "Total TTS synthesis errors",
        )
    )

    # ------------------------------------------------------------------ #
    # Service info (visible in Grafana as a label set)
    # ------------------------------------------------------------------ #
    service_info: Info = field(
        default_factory=lambda: Info(
            "jeevanpath_service",
            "JeevanPath AI service metadata",
        )
    )


# ---------------------------------------------------------------------------
# Singleton — import this in all services / endpoints
# ---------------------------------------------------------------------------
METRICS = _Metrics()

# Populate service info once at module import time.
# (Importing core.config here is safe — it's already cached.)
def _init_service_info() -> None:
    from core.config import settings  # local import avoids circular deps at module load
    METRICS.service_info.info({
        "version": settings.app_version,
        "environment": settings.environment,
        "stt_model": settings.stt_model_size,
        "llm_model": settings.llm_model_name,
        "embedding_model": settings.embedding_model_name,
    })

_init_service_info()
