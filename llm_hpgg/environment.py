"""Controlled HP-SPGG environment and calibration tensor helpers."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from pathlib import Path

import numpy as np

from .personas import PERSONAS


ACTIONS = np.array([0.0, 0.25, 0.5, 0.75, 1.0], dtype=float)


@dataclass(frozen=True)
class CalibrationBundle:
    reward_tensor: np.ndarray
    action_profiles: np.ndarray
    persona_keys: list[str]
    actions: np.ndarray
    n: int
    backend: str
    trap: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "reward_tensor": self.reward_tensor,
            "action_profiles": self.action_profiles,
            "persona_keys": self.persona_keys,
            "actions": self.actions,
            "n": self.n,
            "backend": self.backend,
            "trap": self.trap,
        }


def enumerate_action_profiles(n: int) -> np.ndarray:
    return np.array(list(product(ACTIONS, repeat=n)), dtype=float)


def provider_noise_scale(backend: str) -> float:
    return {
        "anthropic": 0.020,
        "openai": 0.018,
        "google": 0.024,
        "qwen3": 0.030,
        "mixed": 0.026,
    }.get(backend, 0.025)


def expected_reward(persona_index: int, player_index: int, action_profile: np.ndarray, trap: bool = False) -> float:
    persona = PERSONAS[persona_index]
    own = float(action_profile[player_index])
    others = np.delete(action_profile, player_index)
    mean_other = float(np.mean(others)) if len(others) else own
    mean_all = float(np.mean(action_profile))

    public_return = 0.72 * mean_all
    private_retention = 0.50 * (1.0 - own) * persona.self_interest_weight
    cooperation_fit = 1.0 - abs(own - persona.target_contribution)
    fairness_fit = 1.0 - abs(own - mean_other)
    reward = public_return + 0.38 * persona.cooperation_weight * cooperation_fit + 0.18 * persona.fairness_weight * fairness_fit + private_retention

    if trap:
        low_signal = 0.16 * (1.0 - abs(own - 0.25))
        high_group_bonus = 0.55 if mean_all >= 0.72 else 0.0
        reward = 0.58 * reward + low_signal + high_group_bonus * persona.cooperation_weight

    return float(np.clip(reward / 1.8, 0.0, 1.0))


def build_reward_tensor(n: int, backend: str, samples: int = 3, seed: int = 0, trap: bool = False) -> CalibrationBundle:
    rng = np.random.default_rng(seed)
    action_profiles = enumerate_action_profiles(n)
    tensor = np.zeros((n, len(PERSONAS), len(action_profiles)), dtype=float)
    noise_scale = provider_noise_scale(backend)

    for player_index in range(n):
        for persona_index in range(len(PERSONAS)):
            for profile_index, profile in enumerate(action_profiles):
                values = [expected_reward(persona_index, player_index, profile, trap=trap) for _ in range(samples)]
                if samples > 1:
                    values = [value + rng.normal(0.0, noise_scale) for value in values]
                tensor[player_index, persona_index, profile_index] = float(np.clip(np.mean(values), 0.0, 1.0))

    return CalibrationBundle(
        reward_tensor=tensor,
        action_profiles=action_profiles,
        persona_keys=[persona.key for persona in PERSONAS],
        actions=ACTIONS.copy(),
        n=n,
        backend=backend,
        trap=trap,
    )


def load_calibration(path: str | Path) -> dict[str, object]:
    data = np.load(path, allow_pickle=True)
    if hasattr(data, "files"):
        return {key: data[key] for key in data.files}
    loaded = data.item()
    if not isinstance(loaded, dict):
        raise ValueError(f"Calibration file {path} did not contain a dictionary")
    return loaded


def save_calibration(bundle: CalibrationBundle, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    np.save(path, bundle.to_dict(), allow_pickle=True)


def welfare_for_types(reward_tensor: np.ndarray, type_indices: np.ndarray, profile_index: int) -> float:
    return float(np.sum(rewards_for_types(reward_tensor, type_indices, profile_index)))


def rewards_for_types(reward_tensor: np.ndarray, type_indices: np.ndarray, profile_index: int) -> np.ndarray:
    return np.array([reward_tensor[player, type_indices[player], profile_index] for player in range(len(type_indices))], dtype=float)


def tid_min_gap(reward_tensor: np.ndarray) -> float:
    gaps: list[float] = []
    n, type_count, _ = reward_tensor.shape
    for player_index in range(n):
        for first in range(type_count):
            for second in range(first + 1, type_count):
                gaps.append(float(np.mean(np.abs(reward_tensor[player_index, first] - reward_tensor[player_index, second]))))
    return min(gaps) if gaps else 0.0
