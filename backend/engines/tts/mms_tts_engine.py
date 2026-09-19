"""
engines/tts/mms_tts_engine.py — JeevanPath AI

Production TTS engine: facebook/mms-tts-* via HuggingFace Transformers.

MMS (Massively Multilingual Speech) supports all target Indic languages:
  hi → facebook/mms-tts-hin   (Hindi)
  ta → facebook/mms-tts-tam   (Tamil)
  te → facebook/mms-tts-tel   (Telugu)
  kn → facebook/mms-tts-kan   (Kannada)
  ml → facebook/mms-tts-mal   (Malayalam)
  mr → facebook/mms-tts-mar   (Marathi)
  gu → facebook/mms-tts-guj   (Gujarati)
  bn → facebook/mms-tts-ben   (Bengali)
  pa → facebook/mms-tts-pan   (Punjabi)
  or → facebook/mms-tts-ory   (Odia)
  en → facebook/mms-tts-eng   (English)

Each language model is loaded lazily on first request for that language,
then cached in memory.  This avoids loading all 10+ models at startup.

Blocking GPU call — run via asyncio thread pool.

Requirements:
    pip install transformers>=4.40.0 accelerate scipy
"""

from __future__ import annotations

import io
import struct
import time
from typing import Any

import torch

from core.config import settings
from core.logging import get_logger
from engines.base import TTSEngine, TTSSynthesisResult

logger = get_logger(__name__)

# ISO 639-1 → MMS language code (used in the HF model name suffix)
_LANG_TO_MMS: dict[str, str] = {
    "hi": "hin",
    "ta": "tam",
    "te": "tel",
    "kn": "kan",
    "ml": "mal",
    "mr": "mar",
    "gu": "guj",
    "bn": "ben",
    "pa": "pan",
    "or": "ory",
    "en": "eng",
}


def _float32_to_wav_bytes(audio_array: Any, sample_rate: int) -> bytes:
    """
    Convert a float32 numpy/tensor array to a WAV byte string.

    We write a standard 16-bit PCM WAV without using scipy.io.wavfile
    so that the engine has zero extra dependencies beyond numpy.
    """
    import numpy as np

    # Clamp and convert to int16
    audio_np = np.array(audio_array, dtype=np.float32)
    audio_np = np.clip(audio_np, -1.0, 1.0)
    audio_int16 = (audio_np * 32767).astype(np.int16)
    raw_data = audio_int16.tobytes()

    # Build WAV header
    num_channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_chunk_size = len(raw_data)
    riff_chunk_size = 36 + data_chunk_size

    buf = io.BytesIO()
    buf.write(b"RIFF")
    buf.write(struct.pack("<I", riff_chunk_size))
    buf.write(b"WAVE")
    buf.write(b"fmt ")
    buf.write(struct.pack("<I", 16))            # PCM sub-chunk size
    buf.write(struct.pack("<H", 1))             # PCM audio format
    buf.write(struct.pack("<H", num_channels))
    buf.write(struct.pack("<I", sample_rate))
    buf.write(struct.pack("<I", byte_rate))
    buf.write(struct.pack("<H", block_align))
    buf.write(struct.pack("<H", bits_per_sample))
    buf.write(b"data")
    buf.write(struct.pack("<I", data_chunk_size))
    buf.write(raw_data)
    return buf.getvalue()


class MMSTTSEngine(TTSEngine):
    """
    TTS engine backed by facebook/mms-tts-* models.

    Each language model is loaded once and cached.
    """

    def __init__(self) -> None:
        # Cache: lang_code → (model, processor)
        self._models: dict[str, tuple[Any, Any]] = {}
        self._ready = True   # Engine itself is ready; models load on demand
        logger.info("mms_tts_engine_init", supported=list(_LANG_TO_MMS.keys()))

    def _get_model(self, language: str) -> tuple[Any, Any]:
        if language not in self._models:
            mms_code = _LANG_TO_MMS.get(language)
            if mms_code is None:
                raise ValueError(f"Language '{language}' not supported by MMS-TTS engine.")

            try:
                from transformers import VitsModel, AutoTokenizer
            except ImportError as exc:
                raise ImportError(
                    "transformers>=4.40.0 is required for MMS-TTS. "
                    "Install with: pip install transformers accelerate"
                ) from exc

            model_id = f"{settings.tts_model_prefix}-{mms_code}"
            logger.info("tts_model_loading", model=model_id, language=language)

            tokenizer = AutoTokenizer.from_pretrained(model_id)
            model = VitsModel.from_pretrained(model_id)
            model.eval()

            if settings.device.startswith("cuda"):
                model = model.to(settings.device)

            self._models[language] = (model, tokenizer)
            logger.info("tts_model_ready", model=model_id)

        return self._models[language]

    def synthesize(self, text: str, language: str) -> TTSSynthesisResult:
        model, tokenizer = self._get_model(language)

        t_start = time.perf_counter()

        inputs = tokenizer(text, return_tensors="pt")
        if settings.device.startswith("cuda"):
            inputs = {k: v.to(settings.device) for k, v in inputs.items()}

        with torch.no_grad():
            output = model(**inputs)

        # output.waveform: shape (1, T)
        waveform = output.waveform[0].cpu().float().numpy()
        sample_rate = model.config.sampling_rate

        wav_bytes = _float32_to_wav_bytes(waveform, sample_rate)
        processing_time = round(time.perf_counter() - t_start, 3)

        logger.info(
            "tts_synthesis_complete",
            language=language,
            text_len=len(text),
            audio_bytes=len(wav_bytes),
            processing_time=processing_time,
        )

        return TTSSynthesisResult(
            audio_bytes=wav_bytes,
            sample_rate=sample_rate,
            processing_time=processing_time,
        )

    def supported_languages(self) -> list[str]:
        return list(_LANG_TO_MMS.keys())

    def is_ready(self) -> bool:
        return self._ready
