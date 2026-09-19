"""
tests/test_config.py — Tests for the Settings class (core/config.py)
"""

from __future__ import annotations

import os
import pytest


class TestSettings:
    def test_settings_loads_without_env_file(self):
        """Settings must work even if .env file is absent."""
        from core.config import get_settings
        get_settings.cache_clear()
        s = get_settings()
        assert s.app_name == "JeevanPath AI"

    def test_device_auto_detection(self):
        from core.config import settings
        assert settings.device in ("cuda", "cpu", "cuda:0")

    def test_stt_compute_type_set_automatically(self):
        from core.config import settings
        # compute_type must be non-empty (auto-set by model validator)
        assert settings.stt_compute_type in ("float16", "int8")

    def test_supported_languages_includes_required(self):
        from core.config import settings
        required = {"hi", "ta", "te", "kn", "ml", "en"}
        assert required.issubset(settings.supported_languages.keys())

    def test_embedding_dim_positive(self):
        from core.config import settings
        assert settings.embedding_dim > 0

    def test_audio_max_size_is_25mb(self):
        from core.config import settings
        assert settings.audio_max_size_bytes == 25 * 1024 * 1024

    def test_env_override_via_os_environ(self, monkeypatch):
        """Changing an env var and clearing cache should return new value."""
        from core.config import get_settings
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        get_settings.cache_clear()
        s = get_settings()
        assert s.log_level == "DEBUG"
        # Restore
        get_settings.cache_clear()
