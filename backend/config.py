"""
config.py — JeevanPath AI Backend Configuration

Single source of truth for all backend settings.
Change model size, device preference, or add languages here — nowhere else.
"""

import os
import torch

# ---------------------------------------------------------------------------
# Whisper Model Configuration
# ---------------------------------------------------------------------------

# Model size: "tiny" | "base" | "small" | "medium" | "large-v2" | "large-v3"
# Automatically uses "large-v3" when CUDA GPU is available (local PC).
# Falls back to "base" on CPU (cloud hosting like Render to fit 512MB RAM).
WHISPER_MODEL_SIZE: str = os.getenv(
    "WHISPER_MODEL_SIZE",
    "large-v3" if torch.cuda.is_available() else "base"
)

# ---------------------------------------------------------------------------
# Device Configuration
# ---------------------------------------------------------------------------

# Automatically use CUDA if available; fall back to CPU gracefully.
DEVICE: str = "cuda" if torch.cuda.is_available() else "cpu"

# Compute type controls inference precision:
#   "float16" — fast and memory-efficient on modern NVIDIA GPUs
#   "int8"    — quantized, good for CPU / low VRAM situations
COMPUTE_TYPE: str = "float16" if DEVICE == "cuda" else "int8"

# ---------------------------------------------------------------------------
# Language Map
# ---------------------------------------------------------------------------
# Maps Whisper's ISO 639-1 language codes to human-readable names.
# Add new Indian languages here without touching any other file.
# Key   = ISO 639-1 code that Whisper returns
# Value = Display name shown to the user

SUPPORTED_LANGUAGES: dict[str, str] = {
    "ta": "Tamil",
    "te": "Telugu",
    "hi": "Hindi",
    "en": "English",
    "kn": "Kannada",
    "ml": "Malayalam",
    "mr": "Marathi",    # Reserved for Phase 2
    "gu": "Gujarati",   # Reserved for Phase 2
    "bn": "Bengali",    # Reserved for Phase 2
    "pa": "Punjabi",    # Reserved for Phase 2
    "or": "Odia",       # Reserved for Phase 2
}

# Fallback display name when Whisper detects a language outside our map.
UNKNOWN_LANGUAGE_NAME: str = "Unknown"

# ---------------------------------------------------------------------------
# Audio Processing
# ---------------------------------------------------------------------------

# Temporary directory for uploaded audio files (relative to backend/).
TEMP_AUDIO_DIR: str = "temp_audio"

# Maximum audio file size accepted by the API (in bytes). 25 MB.
MAX_AUDIO_SIZE_BYTES: int = 25 * 1024 * 1024
