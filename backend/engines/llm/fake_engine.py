"""
engines/llm/fake_engine.py — JeevanPath AI

Fake LLM engine for unit tests.
"""

from __future__ import annotations

import json
import time

from engines.base import LLMEngine, LLMResponse


class FakeLLMEngine(LLMEngine):
    """
    Deterministic fake LLM engine for tests.

    Returns a fixed JSON string that represents a plausible UserIntent,
    making intent-extraction tests fully deterministic without GPU.
    Override `canned_text` to customise per test.
    """

    canned_text: str = json.dumps({
        "need_type": "scheme_inquiry",
        "sector": "agriculture",
        "state": "Tamil Nadu",
        "age": 32,
        "gender": "male",
        "caste_category": "SC",
        "language": "ta",
    })

    def generate(
        self,
        system_prompt: str,
        user_message: str,
        *,
        max_new_tokens: int | None = None,
        temperature: float | None = None,
    ) -> LLMResponse:
        time.sleep(0.001)
        return LLMResponse(
            text=self.canned_text,
            input_tokens=len(system_prompt.split()) + len(user_message.split()),
            output_tokens=len(self.canned_text.split()),
            processing_time=0.001,
        )

    def is_ready(self) -> bool:
        return True
