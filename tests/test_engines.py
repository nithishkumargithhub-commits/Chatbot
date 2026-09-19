"""
tests/test_engines.py — Unit tests for all engine ABCs and fake implementations
"""

from __future__ import annotations

import pytest

from engines.base import TranscriptionResult, LLMResponse, TTSSynthesisResult
from engines.stt.fake_engine import FakeSTTEngine
from engines.llm.fake_engine import FakeLLMEngine
from engines.embedding.fake_engine import FakeEmbeddingEngine
from engines.tts.fake_engine import FakeTTSEngine


# ---------------------------------------------------------------------------
# STT Engine
# ---------------------------------------------------------------------------

class TestFakeSTTEngine:
    def test_is_ready(self):
        engine = FakeSTTEngine()
        assert engine.is_ready() is True

    def test_transcribe_returns_result(self, tmp_path):
        """Fake engine returns canned result regardless of audio_path."""
        dummy_audio = tmp_path / "test.wav"
        dummy_audio.write_bytes(b"fake audio data")

        engine = FakeSTTEngine()
        result = engine.transcribe(str(dummy_audio))

        assert isinstance(result, TranscriptionResult)
        assert result.language == "hi"
        assert result.language_name == "Hindi"
        assert len(result.transcript) > 0
        assert 0.0 <= result.confidence <= 1.0
        assert result.processing_time >= 0.0
        assert result.audio_duration >= 0.0

    def test_transcribe_custom_canned_result(self, tmp_path):
        """Override canned_result to test Tamil scenario."""
        dummy_audio = tmp_path / "ta_audio.wav"
        dummy_audio.write_bytes(b"fake")

        custom = TranscriptionResult(
            language="ta",
            language_name="Tamil",
            transcript="நான் ஒரு விவசாயி.",
            confidence=0.95,
            processing_time=0.001,
            audio_duration=2.0,
        )
        engine = FakeSTTEngine()
        engine.canned_result = custom

        result = engine.transcribe(str(dummy_audio))
        assert result.language == "ta"
        assert result.transcript == "நான் ஒரு விவசாயி."


# ---------------------------------------------------------------------------
# LLM Engine
# ---------------------------------------------------------------------------

class TestFakeLLMEngine:
    def test_is_ready(self):
        assert FakeLLMEngine().is_ready() is True

    def test_generate_returns_response(self):
        engine = FakeLLMEngine()
        resp = engine.generate(
            system_prompt="You are JeevanPath AI.",
            user_message="Tell me about PM-AJAY scheme.",
        )
        assert isinstance(resp, LLMResponse)
        assert len(resp.text) > 0
        assert resp.input_tokens > 0
        assert resp.output_tokens > 0
        assert resp.processing_time >= 0.0

    def test_generate_returns_valid_json(self):
        import json
        engine = FakeLLMEngine()
        resp = engine.generate("sys", "user msg")
        parsed = json.loads(resp.text)
        assert "need_type" in parsed
        assert "language" in parsed


# ---------------------------------------------------------------------------
# Embedding Engine
# ---------------------------------------------------------------------------

class TestFakeEmbeddingEngine:
    def test_is_ready(self):
        assert FakeEmbeddingEngine().is_ready() is True

    def test_embed_returns_correct_shape(self):
        engine = FakeEmbeddingEngine()
        texts = ["Hello", "नमस्ते", "வணக்கம்"]
        vectors = engine.embed(texts)

        assert len(vectors) == 3
        for vec in vectors:
            assert len(vec) == engine.dimension

    def test_embed_dimension_matches_config(self):
        from core.config import settings
        engine = FakeEmbeddingEngine()
        assert engine.dimension == settings.embedding_dim


# ---------------------------------------------------------------------------
# TTS Engine
# ---------------------------------------------------------------------------

class TestFakeTTSEngine:
    def test_is_ready(self):
        assert FakeTTSEngine().is_ready() is True

    def test_supported_languages_non_empty(self):
        langs = FakeTTSEngine().supported_languages()
        assert isinstance(langs, list)
        assert "hi" in langs
        assert "ta" in langs

    def test_synthesize_returns_wav_bytes(self):
        engine = FakeTTSEngine()
        result = engine.synthesize("नमस्ते", "hi")

        assert isinstance(result, TTSSynthesisResult)
        # WAV files start with "RIFF"
        assert result.audio_bytes[:4] == b"RIFF"
        assert result.sample_rate > 0

    def test_synthesize_all_supported_languages(self):
        engine = FakeTTSEngine()
        for lang in engine.supported_languages():
            result = engine.synthesize("test", lang)
            assert result.audio_bytes[:4] == b"RIFF", f"Failed for {lang}"
