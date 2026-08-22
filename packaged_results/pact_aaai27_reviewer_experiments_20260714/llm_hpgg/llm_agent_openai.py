"""OpenAI backend for HP-SPGG."""

from __future__ import annotations

import time


def _call_llm(system_prompt: str, user_message: str, model: str, max_tokens: int = 256, temperature: float = 0.8) -> str:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install the openai package to use LLM_HPGG_BACKEND=openai") from exc

    client = OpenAI()
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            last_error = exc
            time.sleep(min(2**attempt, 8))
    raise RuntimeError(f"OpenAI call failed after retries: {last_error}")
