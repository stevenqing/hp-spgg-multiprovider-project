"""Build HP-SPGG calibration tensors for E2 type-count and E3 n-agent scaling."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from itertools import product
from pathlib import Path

import numpy as np


ACTIONS = np.array([0.0, 0.25, 0.5, 0.75, 1.0], dtype=float)


@dataclass(frozen=True)
class ScalingPersona:
    key: str
    target_contribution: float
    cooperation_weight: float
    self_interest_weight: float
    fairness_weight: float
    punishment_weight: float = 0.0


PERSONA_LIBRARY: tuple[ScalingPersona, ...] = (
    ScalingPersona("selfish", 0.15, 0.15, 1.05, 0.15),
    ScalingPersona("cooperative", 0.85, 0.95, 0.25, 0.55),
    ScalingPersona("conditional_cooperator", 0.70, 0.75, 0.35, 0.95),
    ScalingPersona("altruistic", 1.00, 1.20, 0.10, 0.45),
    ScalingPersona("free_rider", 0.00, 0.05, 1.25, 0.10),
    ScalingPersona("punisher", 0.65, 0.70, 0.35, 1.10, 0.40),
)


def provider_noise_scale(backend: str) -> float:
    return {
        "DeepSeek-V3.2": 0.020,
        "gpt-5.4-nano-20260317": 0.018,
        "Kimi-K2.6": 0.022,
        "Llama-4-Maverick-17B-128E-Instruct-FP8": 0.028,
        "cloudgpt": 0.024,
        "offline": 0.0,
    }.get(backend, 0.025)


def enumerate_action_profiles(n: int) -> np.ndarray:
    return np.array(list(product(ACTIONS, repeat=n)), dtype=float)


def expected_reward(persona: ScalingPersona, player_index: int, action_profile: np.ndarray, trap: bool) -> float:
    own = float(action_profile[player_index])
    others = np.delete(action_profile, player_index)
    mean_other = float(np.mean(others)) if len(others) else own
    mean_all = float(np.mean(action_profile))
    low_others = float(np.mean(others < 0.35)) if len(others) else 0.0

    public_return = 0.72 * mean_all
    private_retention = 0.50 * (1.0 - own) * persona.self_interest_weight
    cooperation_fit = 1.0 - abs(own - persona.target_contribution)
    fairness_fit = 1.0 - abs(own - mean_other)
    punishment_fit = persona.punishment_weight * low_others * (1.0 - own)
    reward = public_return + 0.36 * persona.cooperation_weight * cooperation_fit + 0.18 * persona.fairness_weight * fairness_fit + private_retention + 0.16 * punishment_fit

    if trap:
        low_signal = 0.16 * (1.0 - abs(own - 0.25))
        high_group_bonus = 0.55 if mean_all >= 0.72 else 0.0
        reward = 0.58 * reward + low_signal + high_group_bonus * persona.cooperation_weight

    return float(np.clip(reward / 1.8, 0.0, 1.0))


def build_tensor(n: int, type_count: int, backend: str, samples: int, seed: int, trap: bool) -> dict[str, object]:
    if not 2 <= type_count <= len(PERSONA_LIBRARY):
        raise ValueError(f"type_count must be in [2, {len(PERSONA_LIBRARY)}]")
    rng = np.random.default_rng(seed)
    personas = PERSONA_LIBRARY[:type_count]
    action_profiles = enumerate_action_profiles(n)
    reward_tensor = np.zeros((n, type_count, len(action_profiles)), dtype=float)
    noise_scale = provider_noise_scale(backend)

    for player_index in range(n):
        for type_index, persona in enumerate(personas):
            for profile_index, profile in enumerate(action_profiles):
                values = [expected_reward(persona, player_index, profile, trap=trap) for _ in range(samples)]
                if samples > 1 and noise_scale > 0.0:
                    values = [value + rng.normal(0.0, noise_scale) for value in values]
                reward_tensor[player_index, type_index, profile_index] = float(np.clip(np.mean(values), 0.0, 1.0))

    return {
        "reward_tensor": reward_tensor,
        "action_profiles": action_profiles,
        "persona_keys": np.array([persona.key for persona in personas]),
        "actions": ACTIONS.copy(),
        "n": n,
        "backend": backend,
        "trap": trap,
        "type_count": type_count,
        "scaling_persona_library": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build E2/E3 HP-SPGG scaling calibration.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--n", type=int, default=3)
    parser.add_argument("--type-count", type=int, default=4)
    parser.add_argument("--backend", default="Llama-4-Maverick-17B-128E-Instruct-FP8")
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--trap", action="store_true")
    args = parser.parse_args()

    bundle = build_tensor(args.n, args.type_count, args.backend, args.samples, args.seed, args.trap)
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(output_path, **bundle)
    print(f"saved={output_path}")
    print(f"backend={args.backend} n={args.n} type_count={args.type_count} profiles={bundle['action_profiles'].shape[0]} trap={args.trap}")


if __name__ == "__main__":
    main()