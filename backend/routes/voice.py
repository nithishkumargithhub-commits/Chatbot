"""
routes/voice.py — JeevanPath AI Voice API Routes

Endpoints:
    POST /api/voice/transcribe  — Accept audio, return transcript + detected language.

Future endpoints (Phase 2+, stubs show the intended contract):
    POST /api/voice/respond     — Accept transcript, return language-matched response.
    POST /api/voice/synthesize  — Accept text + language, return TTS audio.
"""

import logging
import os
import tempfile
import io
import uuid
from pathlib import Path
from pydantic import BaseModel

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import JSONResponse, Response

from config import MAX_AUDIO_SIZE_BYTES, TEMP_AUDIO_DIR
from services.speech import SpeechService, TranscriptionResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/api/voice", tags=["voice"])

# ---------------------------------------------------------------------------
# Dependency: shared SpeechService instance
# ---------------------------------------------------------------------------
# FastAPI's dependency injection system is used so that:
#   1. The model is created once at startup (not per request).
#   2. Tests can override this dependency to inject a mock.

_speech_service: SpeechService | None = None


def get_speech_service() -> SpeechService:
    """
    Dependency that returns the shared SpeechService singleton.
    Raises HTTP 503 if the model failed to load at startup.
    """
    global _speech_service
    if _speech_service is None:
        _speech_service = SpeechService()
    if not _speech_service.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Speech recognition model is not ready. Please try again shortly.",
        )
    return _speech_service


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ensure_temp_dir() -> Path:
    """Create and return the temporary audio directory."""
    temp_dir = Path(TEMP_AUDIO_DIR)
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def _validate_audio_file(file: UploadFile) -> None:
    """
    Light-weight validation before we touch the file content.
    Raises HTTPException on invalid input.
    """
    if file.filename is None or file.filename == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No audio file provided.",
        )

    # Accept common browser-recorded and audio file types.
    # faster-whisper (via libav) handles decoding, so we validate broadly.
    allowed_content_types = {
        "audio/webm",
        "audio/ogg",
        "audio/wav",
        "audio/wave",
        "audio/x-wav",
        "audio/mp4",
        "audio/x-m4a",  # M4A — iOS Voice Memos, Windows Voice Recorder
        "audio/m4a",
        "audio/aac",
        "audio/x-aac",
        "audio/mpeg",
        "audio/mp3",
        "audio/flac",
        "audio/x-flac",
        "video/webm",   # Chrome records WebM with video MIME even for audio-only
        "video/mp4",    # Some tools report M4A/MP4 audio with video/* MIME
    }

    # Extension-based fallback: some clients (Swagger UI, certain browsers)
    # send an incorrect or generic MIME type for M4A and other formats.
    # If the extension is known-safe we allow it regardless of MIME type.
    allowed_extensions = {
        ".wav", ".mp3", ".webm", ".ogg",
        ".mp4", ".m4a", ".aac", ".flac",
    }
    filename_ext = Path(file.filename or "").suffix.lower()

    content_type = (file.content_type or "").split(";")[0].strip().lower()

    if filename_ext in allowed_extensions:
        # Extension match is enough — do not reject on MIME type alone.
        logger.debug("Accepted by extension fallback: ext=%s mime=%s", filename_ext, content_type)
    elif content_type and content_type not in allowed_content_types:
        logger.warning("Rejected: ext=%s mime=%s", filename_ext, content_type)
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported audio format: '{content_type}' (extension: '{filename_ext}'). "
                   "Please upload WAV, MP3, M4A, WebM, OGG, or MP4 audio.",
        )


# ---------------------------------------------------------------------------
# POST /api/voice/transcribe
# ---------------------------------------------------------------------------

@router.post(
    "/transcribe",
    summary="Transcribe speech and detect language",
    response_description="Detected language and transcript text",
)
async def transcribe_audio(
    audio: UploadFile = File(..., description="Audio file recorded from the microphone"),
    language: str | None = Form(None, description="Optional target language (e.g. 'ta', 'hi', 'te', 'auto')"),
    service: SpeechService = Depends(get_speech_service),
) -> JSONResponse:
    """
    Accept an audio file, transcribe it with Whisper, and return:

    - `language`      — ISO 639-1 code detected or guided (e.g. `"ta"`)
    - `language_name` — Human-readable name (e.g. `"Tamil"`)
    - `transcript`    — Full transcribed text
    - `confidence`    — Language detection probability (0.0 – 1.0)
    """
    # 1. Validate
    _validate_audio_file(audio)

    # 2. Read content and check size
    audio_bytes = await audio.read()
    if len(audio_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded audio file is empty.",
        )
    if len(audio_bytes) > MAX_AUDIO_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Audio file too large. Maximum size is "
                   f"{MAX_AUDIO_SIZE_BYTES // (1024 * 1024)} MB.",
        )

    # 3. Save to a unique temporary file
    temp_dir = _ensure_temp_dir()
    original_ext = Path(audio.filename or "audio").suffix or ".webm"
    temp_filename = f"{uuid.uuid4().hex}{original_ext}"
    temp_path = temp_dir / temp_filename

    try:
        temp_path.write_bytes(audio_bytes)
        logger.info(
            "Saved upload to %s (%d bytes, language hint: %s)",
            temp_path.name,
            len(audio_bytes),
            language,
        )

        # 4. Transcribe with optional language guidance
        result: TranscriptionResult = service.transcribe(temp_path, language=language)

        # 5. Query RAG Knowledge Base for relevant government schemes
        schemes = []
        advice = None
        try:
            from services.rag import RAGService
            from services.advice_generator import generate_clear_advice
            schemes = RAGService.get_instance().query(result["transcript"], top_k=3)
            if schemes:
                user_lang = language if language and language != "auto" else result.get("language", "en")
                advice = generate_clear_advice(result["transcript"], schemes[0], lang=user_lang)
        except Exception as exc:
            logger.warning("RAG retrieval/advice generation failed: %s", exc)

        # 6. Return clean JSON response with transcript, localized advice, and schemes
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "language": result["language"],
                "language_name": result["language_name"],
                "transcript": result["transcript"],
                "confidence": result["confidence"],
                "advice": advice,
                "schemes": schemes,
            },
        )

    except FileNotFoundError as exc:
        logger.error("Temp file missing during transcription: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error: audio file could not be processed.",
        ) from exc

    except RuntimeError as exc:
        logger.error("Transcription runtime error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transcription failed. Please try again with a clearer recording.",
        ) from exc

    finally:
        # 6. Always clean up the temporary file
        if temp_path.exists():
            try:
                temp_path.unlink()
                logger.debug("Cleaned up temp file: %s", temp_path.name)
            except OSError as exc:
                logger.warning("Could not delete temp file %s: %s", temp_path.name, exc)


# ---------------------------------------------------------------------------
# TTS Voice Synthesis (gTTS & Indic Audio Stream)
# ---------------------------------------------------------------------------

class SynthesizeRequest(BaseModel):
    text: str
    language: str = "en"


_GTTS_LANG_MAP = {
    "ta": "ta",
    "te": "te",
    "hi": "hi",
    "kn": "kn",
    "ml": "ml",
    "bn": "bn",
    "gu": "gu",
    "mr": "mr",
    "en": "en",
}


def _generate_tts_response(text: str, language: str) -> Response:
    lang = (language or "en").strip().lower()
    target_lang = _GTTS_LANG_MAP.get(lang, "en")

    try:
        from gtts import gTTS
        fp = io.BytesIO()
        tts = gTTS(text=text, lang=target_lang, slow=False)
        tts.write_to_fp(fp)
        fp.seek(0)
        return Response(content=fp.read(), media_type="audio/mpeg")
    except Exception as exc:
        logger.error("TTS synthesis error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech synthesis failed: {exc}",
        )


@router.get("/synthesize", summary="Synthesize speech audio via GET query")
async def synthesize_speech_get(
    text: str = Query(..., description="Text to speak"),
    language: str = Query("en", description="Language code (ta, hi, te, kn, ml, en)"),
) -> Response:
    """Synthesize text into clear MP3 audio in the beneficiary's native language."""
    return _generate_tts_response(text, language)


@router.post("/synthesize", summary="Synthesize speech audio via JSON payload")
async def synthesize_speech_post(payload: SynthesizeRequest) -> Response:
    """Synthesize text into clear MP3 audio in the beneficiary's native language."""
    return _generate_tts_response(payload.text, payload.language)


# ---------------------------------------------------------------------------
# RAG Scheme Semantic Query
# ---------------------------------------------------------------------------

class SchemeQueryRequest(BaseModel):
    query: str
    language: str = "en"
    top_k: int = 3


@router.post("/query", summary="Query government schemes by natural language query")
async def query_schemes(payload: SchemeQueryRequest) -> JSONResponse:
    """Multi-lingual semantic search across the 41 official government schemes."""
    from services.rag import RAGService
    from services.advice_generator import generate_clear_advice
    schemes = RAGService.get_instance().query(payload.query, top_k=payload.top_k)
    advice = None
    if schemes:
        advice = generate_clear_advice(payload.query, schemes[0], lang=payload.language)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "query": payload.query,
            "language": payload.language,
            "count": len(schemes),
            "advice": advice,
            "schemes": schemes,
        },
    )

