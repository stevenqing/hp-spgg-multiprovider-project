"""Google Gemini backend for HP-SPGG."""

from __future__ import annotations

import time


def _call_llm(system_prompt: str, user_message: str, model: str, max_tokens: int = 256, temperature: float = 0.8) -> str:
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError("Install google-genai to use LLM_HPGG_BACKEND=google") from exc

    client = genai.Client()
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            response = client.models.generate_content(
                model=model,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                ),
            )
            return response.text or ""
        except Exception as exc:
            last_error = exc
            time.sleep(min(2**attempt, 8))
    raise RuntimeError(f"Google call failed after retries: {last_error}")
