"""
engines/stt/faster_whisper_engine.py — JeevanPath AI

Production STT engine: faster-whisper (CTranslate2) on GPU/CPU.

This is a refactored, ABC-compliant version of the original
``services/speech.py``.  The transcription logic and Whisper parameters
are preserved exactly — only the class structure and imports change.

Model loading is lazy and happens exactly once (double-checked locking
is handled by the dependency factory in core/dependencies.py).

Blocking GPU call — always run via asyncio thread pool:
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, stt_engine.transcribe, path)
"""

from __future__ import annotations

import time
from pathlib import Path

from faster_whisper import WhisperModel

from core.config import settings
from core.logging import get_logger
from engines.base import STTEngine, TranscriptionResult

logger = get_logger(__name__)


class FasterWhisperSTTEngine(STTEngine):
    """
    STTEngine backed by faster-whisper (CTranslate2).

    The Whisper parameters below match the original SpeechService settings
    and carry the same design rationale documented in that file.
    """

    def __init__(self) -> None:
        self._model: WhisperModel | None = None
        self._load_model()

    # ------------------------------------------------------------------ #
    # Model loading
    # ------------------------------------------------------------------ #

    def _load_model(self) -> None:
        logger.info(
            "stt_model_loading",
            model=settings.stt_model_size,
            device=settings.device,
            compute_type=settings.stt_compute_type,
        )
        try:
            self._model = WhisperModel(
                settings.stt_model_size,
                device=settings.device,
                compute_type=settings.stt_compute_type,
                cpu_threads=settings.stt_cpu_threads,
                num_workers=settings.stt_num_workers,
            )
            logger.info("stt_model_ready", model=settings.stt_model_size)
        except Exception as exc:
            logger.error("stt_model_load_failed", error=str(exc))
            raise RuntimeError(f"Whisper model load failed: {exc}") from exc

    # ------------------------------------------------------------------ #
    # STTEngine interface
    # ------------------------------------------------------------------ #

    def transcribe(self, audio_path: str, language: str | None = None) -> TranscriptionResult:
        """Transcribe audio file → language + transcript."""
        if self._model is None:
            raise RuntimeError("Whisper model is not loaded.")

        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        target_lang = None if (not language or language in ("auto", "None")) else language.strip().lower()
        logger.info("stt_transcribe_start", file=path.name, target_lang=target_lang)
        t_start = time.perf_counter()

        try:
            segments, info = self._model.transcribe(
                str(path),
                # ---- Language detection ----
                language=target_lang,
                language_detection_threshold=settings.stt_language_detection_threshold,
                language_detection_segments=1,
                # ---- Decode quality ----
                beam_size=settings.stt_beam_size,
                temperature=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
                log_prob_threshold=-1.0,
                compression_ratio_threshold=2.4,
                # ---- Hallucination / repetition prevention ----
                condition_on_previous_text=False,
                no_speech_threshold=settings.stt_no_speech_threshold,
                # ---- VAD ----
                vad_filter=True,
                vad_parameters={
                    "min_silence_duration_ms": settings.stt_vad_min_silence_ms,
                },
                # ---- Output ----
                word_timestamps=False,
            )

            detected_lang: str = info.language
            confidence: float = info.language_probability
            audio_duration: float = round(info.duration or 0.0, 2)

            transcript_parts: list[str] = [
                seg.text.strip() for seg in segments if seg.text.strip()
            ]
            transcript: str = " ".join(transcript_parts).strip()

            # Automatic Unicode script detection to prevent Indian languages being mislabeled
            if target_lang:
                detected_lang = target_lang
            elif detected_lang in ("en", "nn", "unknown"):
                for ch in transcript:
                    cp = ord(ch)
                    if 0x0B80 <= cp <= 0x0BFF:
                        detected_lang = "ta"
                        confidence = 0.99
                        break
                    elif 0x0900 <= cp <= 0x097F:
                        detected_lang = "hi"
                        confidence = 0.99
                        break
                    elif 0x0C00 <= cp <= 0x0C7F:
                        detected_lang = "te"
                        confidence = 0.99
                        break
                    elif 0x0C80 <= cp <= 0x0CFF:
                        detected_lang = "kn"
                        confidence = 0.99
                        break
                    elif 0x0D00 <= cp <= 0x0D7F:
                        detected_lang = "ml"
                        confidence = 0.99
                        break

            processing_time = round(time.perf_counter() - t_start, 3)
            language_name = settings.supported_languages.get(
                detected_lang, settings.unknown_language_name
            )

            logger.info(
                "stt_transcribe_complete",
                lang=detected_lang,
                lang_name=language_name,
                confidence=round(confidence, 4),
                audio_duration=audio_duration,
                processing_time=processing_time,
                transcript_preview=transcript[:80],
            )

            return TranscriptionResult(
                language=detected_lang,
                language_name=language_name,
                transcript=transcript,
                confidence=round(confidence, 4),
                processing_time=processing_time,
                audio_duration=audio_duration,
            )

        except Exception as exc:
            logger.error("stt_transcribe_failed", file=path.name, error=str(exc))
            raise RuntimeError(f"Transcription failed: {exc}") from exc

    def is_ready(self) -> bool:
        return self._model is not None
