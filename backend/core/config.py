"""
core/config.py — JeevanPath AI: Single Source of Truth (pydantic-settings)

ALL runtime configuration lives here.  Nothing else in the codebase reads
environment variables directly — they import from this module.

Usage:
    from core.config import settings

Environment variables are loaded from a `.env` file in the backend directory
(or from the real environment).  See `.env.example` for required variables.

Design decisions
----------------
* pydantic-settings v2 validates and coerces every value at startup — bad
  config causes a clear error, not a mysterious crash later.
* Every AI component path / name is a plain string so it can be changed in
  `.env` without touching code.
* Validators enforce sensible ranges (beam_size, thread counts, etc.).
* `model_config = SettingsConfigDict(env_file=".env", ...)` makes the class
  automatically pick up `.env`.  In production, real env vars take precedence.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal

import torch
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration for JeevanPath AI backend.

    Grouped sections:
        app           — service identity
        database      — PostgreSQL + pgvector
        stt           — Speech-to-text (Whisper)
        llm           — Local instruction-following LLM
        embedding     — Sentence embedding model
        tts           — Text-to-speech engine
        audio         — Upload limits
        concurrency   — Thread / worker pool sizes
        logging       — Log level + format
        cors          — Allowed origins
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,    # JP_STT_MODEL_SIZE == jp_stt_model_size
        extra="ignore",          # unknown env vars don't crash the app
    )

    # ------------------------------------------------------------------ #
    # App Identity
    # ------------------------------------------------------------------ #
    app_name: str = "JeevanPath AI"
    app_version: str = "0.2.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # ------------------------------------------------------------------ #
    # Database
    # ------------------------------------------------------------------ #
    # asyncpg DSN for async SQLAlchemy  (postgresql+asyncpg://...)
    database_url: str = Field(
        default="postgresql+asyncpg://jeevanpath:jeevanpath@localhost:5432/jeevanpath",
        description="Async PostgreSQL connection string (postgresql+asyncpg://...)",
    )
    # Sync DSN for Alembic migrations (alembic uses synchronous psycopg2)
    database_sync_url: str = Field(
        default="postgresql+psycopg2://jeevanpath:jeevanpath@localhost:5432/jeevanpath",
        description="Sync PostgreSQL connection string for Alembic (postgresql+psycopg2://...)",
    )
    db_pool_size: int = Field(default=5, ge=1, le=50)
    db_max_overflow: int = Field(default=10, ge=0, le=100)
    db_echo_sql: bool = False   # Set True only in development to log raw SQL

    # ------------------------------------------------------------------ #
    # Device (auto-detected; override via env if needed)
    # ------------------------------------------------------------------ #
    device: str = Field(
        default_factory=lambda: "cuda" if torch.cuda.is_available() else "cpu",
        description="PyTorch device string: 'cuda', 'cuda:0', or 'cpu'",
    )

    # ------------------------------------------------------------------ #
    # STT — Speech-to-Text (faster-whisper)
    # ------------------------------------------------------------------ #
    stt_engine: Literal["faster_whisper", "fake"] = "faster_whisper"

    stt_model_size: Literal[
        "tiny", "base", "small", "medium", "large-v2", "large-v3"
    ] = "large-v3"

    # "float16" on modern CUDA GPUs; "int8" for CPU / low-VRAM
    stt_compute_type: str = Field(
        default="",   # empty → auto-selected in validator below
        description="CTranslate2 compute type.  Leave empty for auto-selection.",
    )

    stt_beam_size: int = Field(default=5, ge=1, le=10)
    stt_language_detection_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    stt_no_speech_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    stt_cpu_threads: int = Field(default=4, ge=1, le=32)
    stt_num_workers: int = Field(default=1, ge=1, le=8)
    stt_vad_min_silence_ms: int = Field(default=300, ge=100, le=2000)

    @model_validator(mode="after")
    def _set_stt_compute_type(self) -> "Settings":
        """Auto-select compute type when not explicitly set."""
        if not self.stt_compute_type:
            self.stt_compute_type = "float16" if self.device.startswith("cuda") else "int8"
        return self

    # ------------------------------------------------------------------ #
    # LLM — Local instruction-following model
    # ------------------------------------------------------------------ #
    llm_engine: Literal["hf_local", "fake"] = "hf_local"

    # Model name as on HuggingFace Hub, or an absolute local path.
    llm_model_name: str = Field(
        default="Qwen/Qwen2.5-7B-Instruct",
        description="HuggingFace model name or absolute local path for the LLM.",
    )
    llm_max_new_tokens: int = Field(default=512, ge=64, le=4096)
    llm_temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    llm_top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    # Load in 8-bit quantization to reduce VRAM.  Requires bitsandbytes.
    llm_load_in_8bit: bool = False
    # Load in 4-bit (NF4) quantization.  Requires bitsandbytes >= 0.41.
    llm_load_in_4bit: bool = False

    # ------------------------------------------------------------------ #
    # Embedding Model
    # ------------------------------------------------------------------ #
    embedding_engine: Literal["sentence_transformer", "fake"] = "sentence_transformer"

    embedding_model_name: str = Field(
        default="ai4bharat/indic-sentence-bert-nli-v1",
        description="SentenceTransformer model name or local path.",
    )
    # Must match the model's actual output dimension.
    # ai4bharat/indic-sentence-bert → 768
    embedding_dim: int = Field(default=768, ge=64, le=4096)
    embedding_batch_size: int = Field(default=32, ge=1, le=512)

    # ------------------------------------------------------------------ #
    # TTS — Text-to-Speech
    # ------------------------------------------------------------------ #
    tts_engine: Literal["mms_tts", "fake"] = "mms_tts"

    # facebook/mms-tts-hin, facebook/mms-tts-tam, etc.
    # The engine maps ISO language codes → specific model names.
    tts_model_prefix: str = Field(
        default="facebook/mms-tts",
        description="HuggingFace model ID prefix for MMS-TTS. Language code appended per request.",
    )
    tts_sample_rate: int = Field(default=16000, ge=8000, le=48000)

    # ------------------------------------------------------------------ #
    # Audio Upload
    # ------------------------------------------------------------------ #
    audio_temp_dir: str = "temp_audio"
    audio_max_size_bytes: int = Field(
        default=25 * 1024 * 1024,
        description="Maximum audio upload size in bytes (default 25 MB).",
    )

    # ------------------------------------------------------------------ #
    # Supported Languages
    # ------------------------------------------------------------------ #
    # ISO 639-1 code → display name.  Add new languages here only.
    supported_languages: dict[str, str] = {
        "ta": "Tamil",
        "te": "Telugu",
        "hi": "Hindi",
        "en": "English",
        "kn": "Kannada",
        "ml": "Malayalam",
        "mr": "Marathi",    # Phase 2
        "gu": "Gujarati",   # Phase 2
        "bn": "Bengali",    # Phase 2
        "pa": "Punjabi",    # Phase 2
        "or": "Odia",       # Phase 2
    }
    unknown_language_name: str = "Unknown"

    # ------------------------------------------------------------------ #
    # Concurrency
    # ------------------------------------------------------------------ #
    # Number of threads in the executor that runs blocking GPU work.
    # One thread per GPU stage is usually right (GPU serialises anyway).
    threadpool_max_workers: int = Field(default=4, ge=1, le=32)

    # ------------------------------------------------------------------ #
    # Logging
    # ------------------------------------------------------------------ #
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "console"] = "json"

    # ------------------------------------------------------------------ #
    # CORS
    # ------------------------------------------------------------------ #
    cors_origins: list[str] = [
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # Alternative React dev port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # ------------------------------------------------------------------ #
    # Prometheus
    # ------------------------------------------------------------------ #
    metrics_enabled: bool = True
    metrics_path: str = "/metrics"

    # ------------------------------------------------------------------ #
    # Field validators
    # ------------------------------------------------------------------ #
    @field_validator("device", mode="before")
    @classmethod
    def _validate_device(cls, v: str) -> str:
        """Accept 'auto' as an alias for automatic CUDA detection."""
        if v == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the global Settings singleton.

    Cached so that the `.env` file is parsed only once per process.
    In tests, call `get_settings.cache_clear()` before patching env vars.
    """
    return Settings()


# Convenience alias — import `settings` directly in most modules.
settings = get_settings()
