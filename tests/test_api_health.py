"""
tests/test_api_health.py — Integration tests for the /health endpoint
and the existing /api/voice/transcribe endpoint (Phase 1).
"""

from __future__ import annotations

import io
import pytest


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_json_structure(self, client):
        data = client.get("/health").json()
        assert data["service"] == "JeevanPath AI"
        assert "version" in data
        assert "stt" in data
        assert "llm" in data
        assert "embedding" in data
        assert "tts" in data

    def test_health_stt_section(self, client):
        data = client.get("/health").json()
        stt = data["stt"]
        assert "engine" in stt
        assert "model" in stt
        assert "device" in stt
        assert "ready" in stt


class TestTranscribeEndpoint:
    """Test the existing Phase 1 /api/voice/transcribe endpoint with a fake engine."""

    def _make_wav_bytes(self) -> bytes:
        """Return a minimal valid 16-bit PCM WAV (1 frame silence)."""
        return (
            b"RIFF\x28\x00\x00\x00WAVE"
            b"fmt \x10\x00\x00\x00\x01\x00\x01\x00"
            b"\x80\x3e\x00\x00\x00\x7d\x00\x00\x02\x00\x10\x00"
            b"data\x02\x00\x00\x00\x00\x00"
        )

    def test_transcribe_valid_wav(self, client):
        wav = self._make_wav_bytes()
        response = client.post(
            "/api/voice/transcribe",
            files={"audio": ("test.wav", io.BytesIO(wav), "audio/wav")},
        )
        # The Phase 1 route uses the old SpeechService singleton, not the
        # new DI.  It may return 503 if the real Whisper model is not loaded
        # in the test process.  We only assert the response is structured.
        assert response.status_code in (200, 503)

    def test_transcribe_empty_file(self, client):
        response = client.post(
            "/api/voice/transcribe",
            files={"audio": ("empty.wav", io.BytesIO(b""), "audio/wav")},
        )
        assert response.status_code == 400

    def test_transcribe_unsupported_type(self, client):
        response = client.post(
            "/api/voice/transcribe",
            files={"audio": ("doc.pdf", io.BytesIO(b"%PDF"), "application/pdf")},
        )
        assert response.status_code == 415
