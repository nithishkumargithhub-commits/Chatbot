"""
engines/stt/fake_engine.py — JeevanPath AI

Fake STT engine for unit tests.  Returns deterministic canned responses
so tests run fast (no GPU, no model download) and are fully reproducible.

Usage in tests:
    from engines.stt.fake_engine import FakeSTTEngine
    app.dependency_overrides[get_stt_engine] = lambda: FakeSTTEngine()
"""

from __future__ import annotations

import time

from engines.base import STTEngine, TranscriptionResult


class FakeSTTEngine(STTEngine):
    """
    Deterministic fake STT engine for tests and CI.

    By default returns a Hindi transcript.  Override `canned_result` to
    customise what the fake returns for a specific test scenario.
    """

    #: Override in tests to return a specific result.
    canned_result: TranscriptionResult = TranscriptionResult(
        language="hi",
        language_name="Hindi",
        transcript="मुझे खेती के लिए सरकारी योजना के बारे में जानकारी चाहिए।",
        confidence=0.97,
        processing_time=0.001,
        audio_duration=3.5,
    )

    def transcribe(self, audio_path: str) -> TranscriptionResult:
        """Return the canned result immediately (no file read, no GPU)."""
        # Tiny sleep to simulate async latency in integration tests
        time.sleep(0.001)
        return self.canned_result

    def is_ready(self) -> bool:
        return True
