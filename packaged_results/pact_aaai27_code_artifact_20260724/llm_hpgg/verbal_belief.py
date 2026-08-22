"""Verbal posterior tracker for the llm_psrl_verbal baseline."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import threading
import time
from typing import Callable
import uuid

import numpy as np

from .llm_agent import call_player
from .personas import PERSONAS


CACHE_LOCK = threading.Lock()
CACHE_NEW_SINCE_SAVE = 0


INITIAL_BELIEF_TEMPLATE = (
    "At the start, all {n} agents could each be any of the following {m} personas "
    "with equal probability. No actions have been observed yet."
)

SAMPLE_PROMPT_TEMPLATE = """You are a coordinator estimating the hidden personas of {n} agents in a repeated public goods game.

CANDIDATE PERSONAS:
{persona_library}

CURRENT BELIEF:
{belief_text}

For each of the {n} agents (Agent 1 through Agent {n}), provide your single best guess of their persona based on the current belief. Output strictly as JSON in this format, with no additional text:

{json_schema}

The persona_key must be exactly one of: {persona_keys_list}."""

UPDATE_PROMPT_TEMPLATE = """You are a coordinator updating your belief about the hidden personas of {n} agents in a repeated public goods game.

CANDIDATE PERSONAS:
{persona_library}

PREVIOUS BELIEF:
{belief_text}

OBSERVATIONS FROM THE MOST RECENT EPISODE:
{observation_block}

Given these new observations, write an updated belief description that captures your refined estimate of each agent's persona. Be specific about which personas are more or less likely for each agent and briefly state why. Keep your response under 200 words. Do not output JSON; output a natural-language paragraph."""


def make_initial_belief(n: int) -> str:
    return INITIAL_BELIEF_TEMPLATE.format(n=n, m=len(PERSONAS))


def _persona_library_block() -> str:
    return "\n".join(f"- {persona.key}: {persona.description}" for persona in PERSONAS)


def _json_schema(n: int) -> str:
    payload = {f"Agent {index + 1}": "<persona_key>" for index in range(n)}
    return json.dumps(payload, indent=2)


def _build_sample_prompt(belief_text: str, n: int) -> str:
    return SAMPLE_PROMPT_TEMPLATE.format(
        n=n,
        persona_library=_persona_library_block(),
        belief_text=belief_text,
        json_schema=_json_schema(n),
        persona_keys_list=", ".join(persona.key for persona in PERSONAS),
    )


def _format_observation_block(action_values: np.ndarray, observed_rewards: np.ndarray | None = None) -> str:
    lines: list[str] = []
    for index, contribution in enumerate(np.asarray(action_values, dtype=float)):
        line = f"  - Agent {index + 1}: contributed {contribution:.2f} units"
        if observed_rewards is not None:
            line += f" and received reward {float(observed_rewards[index]):.3f}"
        lines.append(line)
    return "\n".join(lines)


def _build_update_prompt(
    belief_text: str,
    action_values: np.ndarray,
    observed_rewards: np.ndarray | None,
    n: int,
) -> str:
    return UPDATE_PROMPT_TEMPLATE.format(
        n=n,
        persona_library=_persona_library_block(),
        belief_text=belief_text,
        observation_block=_format_observation_block(action_values, observed_rewards),
    )


def _parse_persona_guess(reply: str, n: int) -> np.ndarray | None:
    key_to_index = {persona.key: index for index, persona in enumerate(PERSONAS)}
    cleaned = re.sub(r"```json\s*|```\s*", "", reply).strip()
    match = re.search(r"\{.*?\}", cleaned, re.DOTALL)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    sampled = np.zeros(n, dtype=int)
    for index in range(n):
        agent_key = f"Agent {index + 1}"
        if agent_key not in parsed:
            return None
        guess = str(parsed[agent_key]).strip()
        if guess not in key_to_index:
            guess_lower = guess.lower()
            matches = [key for key in key_to_index if key.lower() == guess_lower]
            if not matches:
                return None
            guess = matches[0]
        sampled[index] = key_to_index[guess]
    return sampled


def sample_personas_verbal(
    belief_text: str,
    n: int,
    model: str,
    rng: np.random.Generator,
    type_count: int,
    log_callback: Callable[[str], None] | None = None,
    response_cache: dict[str, str] | None = None,
    cache_path: Path | None = None,
) -> tuple[np.ndarray, bool]:
    prompt = _build_sample_prompt(belief_text, n)
    try:
        reply = cached_verbal_call(
            "sample",
            "You are a careful coordinator estimating partner personas. Return valid JSON only.",
            prompt, model, 220, response_cache, cache_path,
        )
    except Exception as exc:
        if os.getenv("LLM_PSRL_STRICT", "0") == "1":
            raise RuntimeError(f"llm_psrl_verbal sample call failed in strict mode: {exc}") from exc
        if log_callback:
            log_callback(f"llm_psrl_verbal sample call failed: {exc}; falling back")
        return rng.integers(0, type_count, size=n), False
    parsed = _parse_persona_guess(reply, n)
    if parsed is None:
        invalidate_cached_verbal_call("sample", prompt, model, response_cache, cache_path)
        if os.getenv("LLM_PSRL_STRICT", "0") == "1":
            raise ValueError(f"llm_psrl_verbal sample parse failed in strict mode: {reply[:240]!r}")
        if log_callback:
            log_callback(f"llm_psrl_verbal sample parse failed: {reply[:240]!r}; falling back")
        return rng.integers(0, type_count, size=n), False
    return parsed, True


def update_belief_verbal(
    belief_text: str,
    action_values: np.ndarray,
    observed_rewards: np.ndarray,
    n: int,
    model: str,
    log_callback: Callable[[str], None] | None = None,
    response_cache: dict[str, str] | None = None,
    cache_path: Path | None = None,
) -> tuple[str, bool]:
    prompt = _build_update_prompt(belief_text, action_values, observed_rewards, n)
    try:
        reply = cached_verbal_call(
            "update",
            "You are a careful coordinator maintaining beliefs about partner personas.",
            prompt, model, 256, response_cache, cache_path,
        )
    except Exception as exc:
        if os.getenv("LLM_PSRL_STRICT", "0") == "1":
            raise RuntimeError(f"llm_psrl_verbal update call failed in strict mode: {exc}") from exc
        if log_callback:
            log_callback(f"llm_psrl_verbal update call failed: {exc}; keeping belief")
        return belief_text, False
    updated = reply.strip()
    if not updated:
        invalidate_cached_verbal_call("update", prompt, model, response_cache, cache_path)
        if os.getenv("LLM_PSRL_STRICT", "0") == "1":
            raise ValueError("llm_psrl_verbal update returned empty text in strict mode")
        if log_callback:
            log_callback("llm_psrl_verbal update returned empty text; keeping belief")
        return belief_text, False
    return updated[:2000], True


def cached_verbal_call(
    kind: str,
    system_prompt: str,
    prompt: str,
    model: str,
    max_tokens: int,
    response_cache: dict[str, str] | None,
    cache_path: Path | None,
) -> str:
    global CACHE_NEW_SINCE_SAVE
    if response_cache is None:
        return call_player(system_prompt, prompt, model=model, max_tokens=max_tokens, temperature=0.0)
    key = hashlib.sha256(f"{kind}\n{model}\n{prompt}".encode("utf-8")).hexdigest()
    with CACHE_LOCK:
        cached = response_cache.get(key)
    if cached is None:
        if os.getenv("VERBAL_CACHE_ONLY", "0") == "1":
            raise KeyError(f"Verbal response cache miss for {kind}: {key}")
        retries = max(1, int(os.getenv("VERBAL_LLM_CALL_RETRIES", "8")))
        base_delay = float(os.getenv("VERBAL_LLM_RETRY_BASE_SECONDS", "5"))
        last_error: Exception | None = None
        for attempt in range(retries):
            try:
                reply = call_player(system_prompt, prompt, model=model, max_tokens=max_tokens, temperature=0.0)
                break
            except Exception as exc:
                last_error = exc
                if "401" in str(exc) or "Unauthorized" in str(exc):
                    raise RuntimeError("CloudGPT access token expired or is invalid") from exc
                if attempt + 1 >= retries:
                    raise
                time.sleep(min(base_delay * (2**attempt), 120.0))
        else:
            raise RuntimeError(f"Verbal LLM call failed after {retries} retries: {last_error}")
        with CACHE_LOCK:
            if key not in response_cache:
                response_cache[key] = reply
                CACHE_NEW_SINCE_SAVE += 1
            if cache_path is not None and CACHE_NEW_SINCE_SAVE >= 10:
                save_response_cache(cache_path, response_cache)
                CACHE_NEW_SINCE_SAVE = 0
    with CACHE_LOCK:
        return response_cache[key]


def invalidate_cached_verbal_call(
    kind: str,
    prompt: str,
    model: str,
    response_cache: dict[str, str] | None,
    cache_path: Path | None,
) -> None:
    if response_cache is None:
        return
    key = hashlib.sha256(f"{kind}\n{model}\n{prompt}".encode("utf-8")).hexdigest()
    with CACHE_LOCK:
        response_cache.pop(key, None)
        if cache_path is not None:
            save_response_cache(cache_path, response_cache)


def load_response_cache(path: Path | None) -> dict[str, str]:
    if path is None or not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Verbal response cache {path} must contain a JSON object")
    return {str(key): str(value) for key, value in payload.items()}


def save_response_cache(path: Path, response_cache: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(json.dumps(response_cache, indent=2), encoding="utf-8")
    last_error: PermissionError | None = None
    for _ in range(20):
        try:
            temporary.replace(path)
            return
        except PermissionError as exc:
            last_error = exc
            time.sleep(0.1)
    temporary.unlink(missing_ok=True)
    if last_error is not None:
        raise last_error