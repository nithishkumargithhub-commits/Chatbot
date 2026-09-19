"""
engines/tts/fake_engine.py — JeevanPath AI

Fake TTS engine for tests — returns minimal valid WAV bytes.
"""

from __future__ import annotations

import struct
import time

from engines.base import TTSEngine, TTSSynthesisResult

# Minimal valid 16-bit PCM WAV with 1 frame of silence
_SILENCE_WAV = (
    b"RIFF\x28\x00\x00\x00WAVE"
    b"fmt \x10\x00\x00\x00\x01\x00\x01\x00"
    b"\x80\x3e\x00\x00\x00\x7d\x00\x00\x02\x00\x10\x00"
    b"data\x02\x00\x00\x00\x00\x00"
)


class FakeTTSEngine(TTSEngine):
    """Returns a tiny silence WAV for any text/language — no GPU needed."""

    def synthesize(self, text: str, language: str) -> TTSSynthesisResult:
        time.sleep(0.001)
        return TTSSynthesisResult(
            audio_bytes=_SILENCE_WAV,
            sample_rate=16000,
            processing_time=0.001,
        )

    def supported_languages(self) -> list[str]:
        return ["hi", "ta", "te", "kn", "ml", "mr", "gu", "bn", "pa", "or", "en"]

    def is_ready(self) -> bool:
        return True
