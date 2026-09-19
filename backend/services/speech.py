"""
services/speech.py — JeevanPath AI Speech Service

Responsibilities:
  - Load the Whisper model exactly once (singleton pattern).
  - Transcribe audio files using faster-whisper on GPU.
  - Auto-detect the spoken language — no manual language selection.
  - Return a clean, typed result dict with diagnostic timing info.

Modular design: to swap the underlying ASR model in Phase 2,
only this file needs to change — no API routes or config changes required.

Key design decisions for Indian-language reliability
-----------------------------------------------------
1. language=None (always) — never force English or any specific language.
2. language_detection_threshold=0.5 — Whisper must reach ≥50 % confidence
   before it commits to a language. The old pipeline committed at 0.25 (Tamil
   recorded as "en"). This is the primary fix for the misdetection bug.
3. language_detection_segments=2 — Whisper inspects 2 audio segments (≈60 s
   of content) for language detection. Using 1 segment was insufficient for
   short clips (< 5 s) and caused Tamil/Hindi to be detected as English.
4. condition_on_previous_text=False — prevents the "I can see the sunrise ×N"
   repetition cascade that occurs when the model feeds its own hallucination
   back as a prior for the next segment.
5. temperature fallback list — if greedy decode (temp=0) produces low log-prob
   or a suspiciously repetitive output, Whisper automatically retries at higher
   temperatures before giving up.
6. compression_ratio_threshold=2.4 — detects repeated outputs (high
   compression = repeated tokens) and triggers the temperature fallback.
7. no_speech_threshold=0.6 — suppresses hallucinated text when the model
   decides the audio is mostly silence / background noise.
8. vad_filter=True with min_silence_duration_ms=300 — clips silence tightly
   so short utterances are not padded with blank audio that confuses the model.
9. Romanised-word heuristic — after transcription, if Whisper labelled the
   audio as English but the transcript contains known Indic romanised words
   (e.g. 'naan', 'mujhe'), the detected language is overridden.
"""

import logging
import os
import time
from pathlib import Path
from typing import TypedDict

from faster_whisper import WhisperModel

from config import (
    COMPUTE_TYPE,
    DEVICE,
    SUPPORTED_LANGUAGES,
    UNKNOWN_LANGUAGE_NAME,
    WHISPER_MODEL_SIZE,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

class TranscriptionResult(TypedDict):
    """Typed dictionary returned by SpeechService.transcribe()."""
    language: str           # ISO 639-1 code detected by Whisper, e.g. "ta"
    language_name: str      # Human-readable name, e.g. "Tamil"
    transcript: str         # Full transcribed text, including code-switched words
    confidence: float       # Language detection probability (0.0 – 1.0)
    processing_time: float  # Wall-clock seconds from call start to return
    audio_duration: float   # Duration of the audio clip in seconds (from Whisper info)


# ---------------------------------------------------------------------------
# SpeechService
# ---------------------------------------------------------------------------

class SpeechService:
    """
    Singleton-style service that holds the Whisper model in memory.

    Usage (in routes):
        speech_service = SpeechService()          # instantiate once at startup
        result = speech_service.transcribe(path)  # call per request
    """

    def __init__(self) -> None:
        self._model: WhisperModel | None = None
        self._load_model()

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def _load_model(self) -> None:
        """
        Load the Whisper model into memory.
        Uses GPU (float16) when CUDA is available; falls back to CPU (int8).
        The model is downloaded to HuggingFace cache on first run (~1.5 GB for
        large-v3), then loaded from disk on subsequent starts in seconds.
        """
        logger.info(
            "Loading Whisper model '%s' on device='%s' with compute_type='%s'",
            WHISPER_MODEL_SIZE,
            DEVICE,
            COMPUTE_TYPE,
        )

        try:
            self._model = WhisperModel(
                WHISPER_MODEL_SIZE,
                device=DEVICE,
                compute_type=COMPUTE_TYPE,
                # cpu_threads silences a CTranslate2 warning on GPU paths.
                cpu_threads=4,
                # num_workers: number of parallel audio loaders (1 is fine for
                # a real-time voice assistant; raise for bulk batch processing).
                num_workers=1,
            )
            logger.info("Whisper model loaded successfully.")
        except Exception as exc:
            logger.error("Failed to load Whisper model: %s", exc)
            # Re-raise so the application fails fast at startup,
            # rather than silently serving broken responses.
            raise RuntimeError(f"Whisper model load failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Transcription
    # ------------------------------------------------------------------

    def transcribe(self, audio_path: str | Path, language: str | None = None) -> TranscriptionResult:
        """
        Transcribe audio and detect the spoken language automatically.

        Args:
            audio_path: Path to the audio file (WAV, MP3, M4A, WebM, OGG …).
            language: Optional ISO 639-1 code (e.g. 'ta', 'hi') to guide transcription.
                      If None or 'auto', Whisper auto-detects.
        """
        if self._model is None:
            raise RuntimeError("Whisper model is not loaded.")

        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        target_lang = None if (not language or language in ("auto", "None")) else language.strip().lower()
        logger.info("Transcribing audio file: %s (target_lang=%s)", audio_path.name, target_lang)

        t_start = time.perf_counter()

        try:
            segments, info = self._model.transcribe(
                str(audio_path),

                # --- Language detection ---
                language=target_lang,
                language_detection_threshold=0.5,
                # Number of audio segments used for the initial language-detect
                # pass. 1 segment (~30 s max) was too little for short clips
                # (< 5 s) causing Tamil/Hindi to be misdetected as English.
                # 2 segments provides sufficient signal without adding latency.
                language_detection_segments=2,

                # --- Decode quality ---
                beam_size=5,
                # Temperature fallback: greedy (0.0) first; if output quality
                # is poor (log-prob < threshold or compression ratio > threshold)
                # Whisper retries at progressively higher temperatures.
                temperature=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
                # Triggers temperature retry when average log-prob is too low.
                log_prob_threshold=-1.0,
                # Triggers temperature retry when output is suspiciously
                # repetitive (compression ratio > 2.4 = repeated tokens).
                compression_ratio_threshold=2.4,

                # --- Hallucination / repetition prevention ---
                # Do NOT feed previous segment text as a prior for the next
                # segment. This is the key guard against the cascade:
                # "I can see the sunrise. I can see the sunrise. ..."
                condition_on_previous_text=False,
                # Suppress transcript when the model itself thinks the audio
                # is non-speech (no_speech_prob > 0.6 → skip segment).
                no_speech_threshold=0.6,

                # --- VAD (Voice Activity Detection) ---
                # Remove leading/trailing silence so Whisper sees clean speech.
                vad_filter=True,
                vad_parameters={
                    # 300 ms is tighter than the old 500 ms — avoids clipping
                    # the last syllable of short utterances.
                    "min_silence_duration_ms": 300,
                },

                # --- Output format ---
                # No word-level timestamps needed for Phase 1.
                word_timestamps=False,
            )

            # info.language and info.language_probability are determined
            # during the first-pass language detection and are available
            # immediately, before any segment is consumed.
            detected_lang: str = info.language           # e.g. "ta"
            confidence: float = info.language_probability  # 0.0 – 1.0
            audio_duration: float = round(info.duration or 0.0, 2)

            # Consume the lazy segment generator to build the full transcript.
            transcript_parts: list[str] = []
            for segment in segments:
                text = segment.text.strip()
                if text:
                    transcript_parts.append(text)

            transcript: str = " ".join(transcript_parts).strip()

            # Post-transcription language correction (two-layer fallback)
            if target_lang:
                # If the caller forced a language, honour it regardless of detection.
                detected_lang = target_lang
            elif detected_lang in ("en", "nn", "unknown"):
                # Layer 1 — Unicode script detection (most reliable):
                # If the transcript contains native-script characters, use them.
                script_override: str | None = None
                for ch in transcript:
                    cp = ord(ch)
                    if 0x0B80 <= cp <= 0x0BFF:
                        script_override = "ta"; break
                    elif 0x0900 <= cp <= 0x097F:
                        script_override = "hi"; break
                    elif 0x0C00 <= cp <= 0x0C7F:
                        script_override = "te"; break
                    elif 0x0C80 <= cp <= 0x0CFF:
                        script_override = "kn"; break
                    elif 0x0D00 <= cp <= 0x0D7F:
                        script_override = "ml"; break
                    elif 0x0980 <= cp <= 0x09FF:
                        script_override = "bn"; break

                if script_override:
                    detected_lang = script_override
                    confidence = 0.99
                else:
                    # Layer 2 — Romanised word heuristic:
                    # Whisper sometimes writes Indic speech in English letters.
                    # Check for common native words in their romanised form.
                    _ROMANISED: dict[str, list[str]] = {
                        "ta": ["naan", "neenga", "enna", "enga", "enakku", "ungal", "romba", "sollu"],
                        "hi": ["mujhe", "aapka", "aapki", "kaise", "chahiye", "milega", "batao", "karein", "hain"],
                        "te": ["nenu", "meeru", "enti", "ela", "cheppandi", "kavali"],
                        "kn": ["naanu", "neevu", "yenu", "heli", "maadbeku"],
                        "ml": ["njan", "ningal", "enthu", "evide", "cheyyuka"],
                    }
                    t_lower = transcript.lower()
                    for lang_code, words in _ROMANISED.items():
                        if any(f" {w} " in f" {t_lower} " for w in words):
                            detected_lang = lang_code
                            confidence = 0.85  # lower confidence — heuristic only
                            logger.info(
                                "Romanised-word heuristic overrode 'en' → '%s' | transcript='%s'",
                                lang_code, transcript[:60],
                            )
                            break

            t_end = time.perf_counter()
            processing_time: float = round(t_end - t_start, 3)

            # Resolve language code → display name.
            language_name: str = SUPPORTED_LANGUAGES.get(
                detected_lang, UNKNOWN_LANGUAGE_NAME
            )

            logger.info(
                "Transcription complete | lang=%s (%s) | conf=%.3f | "
                "duration=%.1fs | proc=%.2fs | text='%s'",
                detected_lang,
                language_name,
                confidence,
                audio_duration,
                processing_time,
                transcript[:80],  # log only first 80 chars
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
            logger.error("Transcription failed for %s: %s", audio_path.name, exc)
            raise RuntimeError(f"Transcription failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Health check helper
    # ------------------------------------------------------------------

    def is_ready(self) -> bool:
        """Returns True if the model is loaded and ready."""
        return self._model is not None
