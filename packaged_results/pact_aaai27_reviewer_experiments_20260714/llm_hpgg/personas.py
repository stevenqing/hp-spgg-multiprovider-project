"""Persona definitions and prompts for HP-SPGG."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Persona:
    key: str
    label: str
    description: str
    target_contribution: float
    cooperation_weight: float
    self_interest_weight: float
    fairness_weight: float


PERSONAS: tuple[Persona, ...] = (
    Persona("altruistic_builder", "Altruistic Builder", "Prioritises group welfare and consistently contributes high amounts.", 1.0, 1.2, 0.15, 0.5),
    Persona("conditional_cooperator", "Conditional Cooperator", "Contributes when others appear willing to contribute too.", 0.8, 0.95, 0.25, 0.8),
    Persona("risk_averse_balancer", "Risk-Averse Balancer", "Avoids extremes and prefers stable medium contributions.", 0.4, 0.30, 0.60, 1.0),
    Persona("free_rider", "Free Rider", "Prioritises private payoff and tends to contribute little.", 0.05, 0.1, 1.1, 0.15),
)


def persona_keys() -> list[str]:
    return [persona.key for persona in PERSONAS]


def persona_system_prompt(persona: Persona) -> str:
    return (
        f"You are playing a repeated public-goods game as {persona.label}. "
        f"Private behavioural profile: {persona.description} "
        "Choose a contribution in [0, 1]. Return only a short rationale and the numeric contribution."
    )


def render_persona_prompt(persona: Persona) -> str:
    return persona_system_prompt(persona)


def judge_system_prompt() -> str:
    return (
        "Score the player satisfaction in a public-goods-game outcome. "
        "Return only valid JSON with key score, a number from 0.0 to 1.0."
    )
