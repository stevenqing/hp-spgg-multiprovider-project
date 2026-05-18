"""Provider dispatcher for player and judge LLM calls."""

from __future__ import annotations

import os


DEFAULT_MODELS = {
    "anthropic": {"player": "claude-haiku-4-5-20251001", "judge": "claude-sonnet-4-6-20251101"},
    "openai": {"player": "gpt-5.4-mini", "judge": "gpt-5.4"},
    "cloudgpt": {"player": "gpt-5.4-mini-20260317", "judge": "gpt-5.4-mini-20260317"},
    "google": {"player": "gemini-2.5-flash", "judge": "gemini-2.5-pro"},
    "qwen3": {"player": "Qwen/Qwen3-32B", "judge": "Qwen/Qwen3-235B-A22B"},
    "deepseek": {"player": "deepseek-ai/DeepSeek-V3.2", "judge": "deepseek-ai/DeepSeek-V3.2"},
}


def backend_name(role: str | None = None) -> str:
    backend = os.getenv("LLM_HPGG_BACKEND", "anthropic").strip().lower()
    if backend != "mixed" or role is None:
        return backend
    env_name = "LLM_HPGG_PLAYER_BACKEND" if role == "player" else "LLM_HPGG_JUDGE_BACKEND"
    return os.getenv(env_name, "anthropic").strip().lower()


def model_for(role: str, backend: str, override: str | None = None) -> str:
    if override:
        return override
    env_name = "LLM_HPGG_PLAYER_MODEL" if role == "player" else "LLM_HPGG_JUDGE_MODEL"
    if os.getenv(env_name):
        return os.environ[env_name]
    if backend not in DEFAULT_MODELS:
        raise ValueError(f"Unsupported backend: {backend}")
    return DEFAULT_MODELS[backend][role]


def call_player(system_prompt: str, user_message: str, model: str | None = None, max_tokens: int = 256, temperature: float = 0.8) -> str:
    backend = backend_name("player")
    return _backend_call(backend, system_prompt, user_message, model_for("player", backend, model), max_tokens, temperature)


def call_judge(system_prompt: str, user_message: str, model: str | None = None, max_tokens: int = 128, temperature: float = 0.0) -> str:
    backend = backend_name("judge")
    return _backend_call(backend, system_prompt, user_message, model_for("judge", backend, model), max_tokens, temperature)


def _backend_call(backend: str, system_prompt: str, user_message: str, model: str, max_tokens: int, temperature: float) -> str:
    if os.getenv("LLM_HPGG_OFFLINE", "0") == "1":
        return '{"score": 0.75}' if "score" in system_prompt.lower() else "contribution=0.75; reason=offline smoke test"
    if backend == "anthropic":
        from .llm_agent_anthropic import _call_llm
    elif backend == "openai":
        from .llm_agent_openai import _call_llm
    elif backend == "cloudgpt":
        from .llm_agent_cloudgpt import _call_llm
    elif backend == "google":
        from .llm_agent_google import _call_llm
    elif backend in {"qwen3", "deepseek"}:
        from .llm_agent_deepinfra import _call_llm
    else:
        raise ValueError(f"Unsupported LLM_HPGG_BACKEND: {backend}")
    return _call_llm(system_prompt, user_message, model=model, max_tokens=max_tokens, temperature=temperature)
