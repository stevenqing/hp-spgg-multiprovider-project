"""Concordia LanguageModel adapter backed by the project LLM provider layer."""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
import json
import re
from typing import Any

from concordia.language_model import language_model

from llm_hpgg.llm_agent import call_player


class HPGGConcordiaLanguageModel(language_model.LanguageModel):
    """Minimal Concordia model wrapper around `llm_hpgg.llm_agent.call_player`."""

    def __init__(self, model: str | None = None, system_prompt: str | None = None) -> None:
        self.model = model
        self.system_prompt = system_prompt or (
            "You are controlling a careful generative social-simulation agent. "
            "Follow the prompt exactly and keep responses concise."
        )

    def sample_text(
        self,
        prompt: str,
        *,
        max_tokens: int = language_model.DEFAULT_MAX_TOKENS,
        terminators: Collection[str] = language_model.DEFAULT_TERMINATORS,
        temperature: float = language_model.DEFAULT_TEMPERATURE,
        top_p: float = language_model.DEFAULT_TOP_P,
        top_k: int = language_model.DEFAULT_TOP_K,
        timeout: float = language_model.DEFAULT_TIMEOUT_SECONDS,
        seed: int | None = None,
    ) -> str:
        del terminators, top_p, top_k, timeout, seed
        return call_player(
            self.system_prompt,
            prompt,
            model=self.model,
            max_tokens=min(max_tokens, 4000),
            temperature=temperature,
        )

    def sample_choice(
        self,
        prompt: str,
        responses: Sequence[str],
        *,
        seed: int | None = None,
    ) -> tuple[int, str, Mapping[str, Any]]:
        if not responses:
            return 0, "", {"empty_responses": True}

        choice_prompt = json.dumps(
            {
                "task": "Choose exactly one response option for a Concordia simulation.",
                "prompt": prompt,
                "options": [
                    {"index": index, "response": response}
                    for index, response in enumerate(responses)
                ],
                "response_schema": {"index": "integer option index", "reason": "brief reason"},
                "instruction": "Return only JSON. Do not include markdown.",
            },
            indent=2,
        )
        reply = call_player(
            "You choose one option from a finite list. Return valid JSON only.",
            choice_prompt,
            model=self.model,
            max_tokens=160,
            temperature=0.0,
        )
        index = _parse_choice_index(reply, len(responses))
        if index is None:
            index = 0 if seed is None else seed % len(responses)
        return index, responses[index], {"reply": reply[:1000]}


def _parse_choice_index(reply: str, option_count: int) -> int | None:
    try:
        parsed = json.loads(_extract_json(reply))
        value = int(parsed.get("index"))
    except Exception:
        match = re.search(r"\b(\d+)\b", reply)
        if not match:
            return None
        value = int(match.group(1))
    if 0 <= value < option_count:
        return value
    return None


def _extract_json(text: str) -> str:
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON object found")
    return match.group(0)
