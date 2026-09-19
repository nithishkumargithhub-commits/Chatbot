"""
engines/llm/hf_local_engine.py — JeevanPath AI

Production LLM engine: HuggingFace Transformers, local inference.

Default model: Qwen/Qwen2.5-7B-Instruct (configurable via settings.llm_model_name).

Model loading is lazy + singleton — never reloaded per request.
Blocking GPU call — always run via asyncio thread pool.

Optional 4-bit/8-bit quantisation via bitsandbytes is supported when
settings.llm_load_in_4bit or settings.llm_load_in_8bit is True.

Requirements (install separately when ready):
    pip install transformers>=4.40.0 accelerate bitsandbytes
"""

from __future__ import annotations

import time

import torch

from core.config import settings
from core.logging import get_logger
from engines.base import LLMEngine, LLMResponse

logger = get_logger(__name__)

# Lazy imports — transformers is only imported when the engine is first built,
# so that test environments without transformers installed still work with
# FakeLLMEngine.
_transformers_available: bool | None = None


def _check_transformers() -> None:
    global _transformers_available
    if _transformers_available is None:
        try:
            import transformers  # noqa: F401
            _transformers_available = True
        except ImportError:
            _transformers_available = False
    if not _transformers_available:
        raise ImportError(
            "transformers is required for HFLocalLLMEngine. "
            "Install it with: pip install transformers>=4.40.0 accelerate"
        )


class HFLocalLLMEngine(LLMEngine):
    """
    HuggingFace Transformers-based local LLM engine.

    Supports any instruction-tuned causal LM that uses the chat template
    (e.g. Qwen2.5-7B-Instruct, Gemma-3-9B-it, Llama-3.x-Instruct).
    """

    def __init__(self) -> None:
        _check_transformers()
        self._model = None
        self._tokenizer = None
        self._pipeline = None
        self._load_model()

    def _load_model(self) -> None:
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

        model_name = settings.llm_model_name
        logger.info("llm_model_loading", model=model_name, device=settings.device)

        # Build quantisation config if requested
        quantization_config = None
        if settings.llm_load_in_4bit or settings.llm_load_in_8bit:
            try:
                from transformers import BitsAndBytesConfig
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=settings.llm_load_in_4bit,
                    load_in_8bit=settings.llm_load_in_8bit,
                    bnb_4bit_compute_dtype=torch.float16,
                )
            except ImportError:
                logger.warning(
                    "bitsandbytes_not_installed",
                    hint="Install bitsandbytes to enable 4-bit/8-bit quantisation.",
                )

        dtype = torch.float16 if settings.device.startswith("cuda") else torch.float32

        self._tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True,
        )
        self._model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=dtype,
            device_map="auto" if settings.device.startswith("cuda") else None,
            quantization_config=quantization_config,
            trust_remote_code=True,
        )

        self._pipeline = pipeline(
            "text-generation",
            model=self._model,
            tokenizer=self._tokenizer,
        )

        logger.info("llm_model_ready", model=model_name)

    def generate(
        self,
        system_prompt: str,
        user_message: str,
        *,
        max_new_tokens: int | None = None,
        temperature: float | None = None,
    ) -> LLMResponse:
        if self._pipeline is None:
            raise RuntimeError("LLM model is not loaded.")

        max_tokens = max_new_tokens or settings.llm_max_new_tokens
        temp = temperature if temperature is not None else settings.llm_temperature

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        t_start = time.perf_counter()

        outputs = self._pipeline(
            messages,
            max_new_tokens=max_tokens,
            temperature=temp,
            top_p=settings.llm_top_p,
            do_sample=temp > 0.0,
            return_full_text=False,
        )

        processing_time = round(time.perf_counter() - t_start, 3)

        generated_text: str = outputs[0]["generated_text"].strip()  # type: ignore[index]

        # Token counts via tokenizer (approximate for monitoring)
        prompt_tokens = len(self._tokenizer.apply_chat_template(messages))
        output_tokens = len(self._tokenizer.encode(generated_text))

        logger.info(
            "llm_generate_complete",
            input_tokens=prompt_tokens,
            output_tokens=output_tokens,
            processing_time=processing_time,
        )

        return LLMResponse(
            text=generated_text,
            input_tokens=prompt_tokens,
            output_tokens=output_tokens,
            processing_time=processing_time,
        )

    def is_ready(self) -> bool:
        return self._pipeline is not None
