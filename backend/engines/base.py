"""
engines/base.py — JeevanPath AI: Abstract Engine Interfaces

Four Abstract Base Classes, one per AI component in the pipeline.
Every concrete implementation (production or fake) must subclass the
appropriate ABC and implement ALL abstract methods.

Design rules
------------
* ABCs define the contract; they contain NO business logic.
* All heavy I/O (model loading, GPU inference, disk reads) is synchronous
  in the engine itself.  The caller is responsible for running it in a
  thread pool (``asyncio.get_event_loop().run_in_executor``).
* Return types use only stdlib / Pydantic dataclasses — no framework-specific
  types leak through the interface boundary.
* Config is read from ``core.config.settings`` inside __init__; the ABC
  does not accept settings as a constructor argument (keeps the Depends()
  factory simple).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Shared return types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TranscriptionResult:
    """Output of STTEngine.transcribe()."""
    language: str           # ISO 639-1 code, e.g. "ta"
    language_name: str      # Display name, e.g. "Tamil"
    transcript: str         # Full transcribed text
    confidence: float       # Language detection probability [0, 1]
    processing_time: float  # Wall-clock seconds for this call
    audio_duration: float   # Duration of the audio clip in seconds


@dataclass(frozen=True)
class LLMResponse:
    """Output of LLMEngine.generate()."""
    text: str               # Generated text (stripped)
    input_tokens: int       # Prompt token count (for monitoring)
    output_tokens: int      # Generated token count
    processing_time: float


@dataclass(frozen=True)
class TTSSynthesisResult:
    """Output of TTSEngine.synthesize()."""
    audio_bytes: bytes      # Raw PCM / WAV bytes
    sample_rate: int        # e.g. 16000
    processing_time: float


# ---------------------------------------------------------------------------
# Abstract Base Classes
# ---------------------------------------------------------------------------

class STTEngine(ABC):
    """
    Speech-to-Text engine.

    Implementations: FasterWhisperSTTEngine, FakeSTTEngine.
    """

    @abstractmethod
    def transcribe(self, audio_path: str) -> TranscriptionResult:
        """
        Transcribe the audio file at ``audio_path``.

        Parameters
        ----------
        audio_path : str
            Absolute path to an audio file (WAV, WebM, MP3, M4A, …).
            The file must exist on the local filesystem.

        Returns
        -------
        TranscriptionResult
            Detected language, full transcript, confidence, timings.

        Raises
        ------
        FileNotFoundError
            If ``audio_path`` does not exist.
        RuntimeError
            On model or decoding failure.
        """
        ...

    @abstractmethod
    def is_ready(self) -> bool:
        """Return True if the model is loaded and ready to transcribe."""
        ...


class LLMEngine(ABC):
    """
    Instruction-following LLM engine for intent extraction and guidance
    generation.

    Implementations: HFLocalLLMEngine, FakeLLMEngine.
    """

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_message: str,
        *,
        max_new_tokens: int | None = None,
        temperature: float | None = None,
    ) -> LLMResponse:
        """
        Run a chat-style completion.

        Parameters
        ----------
        system_prompt : str
            The system / instruction context shown before the user message.
        user_message : str
            The user's message (transcript or intermediate prompt).
        max_new_tokens : int | None
            Override ``settings.llm_max_new_tokens`` for this call.
        temperature : float | None
            Override ``settings.llm_temperature`` for this call.

        Returns
        -------
        LLMResponse
            Generated text plus token counts and timing.
        """
        ...

    @abstractmethod
    def is_ready(self) -> bool:
        """Return True if the model is loaded."""
        ...


class EmbeddingEngine(ABC):
    """
    Sentence embedding engine for semantic similarity search.

    Implementations: SentenceTransformerEmbeddingEngine, FakeEmbeddingEngine.
    """

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Return L2-normalised embeddings for a list of texts.

        Parameters
        ----------
        texts : list[str]
            One or more sentences / paragraphs to embed.

        Returns
        -------
        list[list[float]]
            One float vector per input text.  All vectors have the same
            dimension (``settings.embedding_dim``).
        """
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding vector dimension (e.g. 768 for indic-sentence-bert)."""
        ...

    @abstractmethod
    def is_ready(self) -> bool:
        """Return True if the model is loaded."""
        ...


class TTSEngine(ABC):
    """
    Text-to-Speech engine for Indic language voice output.

    Implementations: MMSTTSEngine, FakeTTSEngine.
    """

    @abstractmethod
    def synthesize(self, text: str, language: str) -> TTSSynthesisResult:
        """
        Synthesize speech for the given text in the given language.

        Parameters
        ----------
        text : str
            The guidance text to speak aloud.
        language : str
            ISO 639-1 language code (e.g. ``"ta"`` for Tamil).

        Returns
        -------
        TTSSynthesisResult
            Raw audio bytes, sample rate, and timing.

        Raises
        ------
        ValueError
            If ``language`` is not supported by this engine.
        RuntimeError
            On synthesis failure.
        """
        ...

    @abstractmethod
    def supported_languages(self) -> list[str]:
        """Return ISO 639-1 codes this engine can synthesize."""
        ...

    @abstractmethod
    def is_ready(self) -> bool:
        """Return True if the engine/model is loaded."""
        ...
