"""Anthropic backend."""

from __future__ import annotations

import time



def _call_llm(system_prompt: str, user_message: str, model: str, max_tokens: int = 256, temperature: float = 0.8) -> str:
    try:
        from anthropic import Anthropic
    except ImportError as exc:
        raise RuntimeError("Install the anthropic package to use LLM_HPGG_BACKEND=anthropic") from exc

    client = Anthropic()
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            response = client.messages.create(
                model=model,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
        except Exception as exc:
            last_error = exc
            time.sleep(min(2**attempt, 8))
    raise RuntimeError(f"Anthropic call failed after retries: {last_error}")
