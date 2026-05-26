"""Verbal posterior tracker for the llm_psrl_verbal baseline."""

from __future__ import annotations

import json
import re
from typing import Callable

import numpy as np

from .llm_agent import call_player
from .personas import PERSONAS


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
) -> tuple[np.ndarray, bool]:
    prompt = _build_sample_prompt(belief_text, n)
    try:
        reply = call_player(
            "You are a careful coordinator estimating partner personas. Return valid JSON only.",
            prompt,
            model=model,
            max_tokens=220,
            temperature=0.0,
        )
    except Exception as exc:
        if log_callback:
            log_callback(f"llm_psrl_verbal sample call failed: {exc}; falling back")
        return rng.integers(0, type_count, size=n), False
    parsed = _parse_persona_guess(reply, n)
    if parsed is None:
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
) -> tuple[str, bool]:
    prompt = _build_update_prompt(belief_text, action_values, observed_rewards, n)
    try:
        reply = call_player(
            "You are a careful coordinator maintaining beliefs about partner personas.",
            prompt,
            model=model,
            max_tokens=420,
            temperature=0.0,
        )
    except Exception as exc:
        if log_callback:
            log_callback(f"llm_psrl_verbal update call failed: {exc}; keeping belief")
        return belief_text, False
    updated = reply.strip()
    if not updated:
        if log_callback:
            log_callback("llm_psrl_verbal update returned empty text; keeping belief")
        return belief_text, False
    return updated[:2000], True