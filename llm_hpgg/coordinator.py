"""Bayesian coordinators for HP-SPGG experiments."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
import numpy as np

from .environment import rewards_for_types, welfare_for_types


@dataclass
class CoordinatorState:
    posterior: np.ndarray
    joint_type_profiles: np.ndarray
    joint_posterior: np.ndarray
    reward_tensor: np.ndarray
    action_profiles: np.ndarray
    beta: float = 1.0

    @classmethod
    def fresh(cls, n: int, type_count: int, reward_tensor: np.ndarray, action_profiles: np.ndarray, beta: float) -> "CoordinatorState":
        posterior = np.full((n, type_count), 1.0 / type_count, dtype=float)
        joint_type_profiles = np.array(list(product(range(type_count), repeat=n)), dtype=int)
        joint_posterior = np.full(len(joint_type_profiles), 1.0 / len(joint_type_profiles), dtype=float)
        return cls(
            posterior=posterior,
            joint_type_profiles=joint_type_profiles,
            joint_posterior=joint_posterior,
            reward_tensor=reward_tensor,
            action_profiles=action_profiles,
            beta=beta,
        )


def profile_count_for_storage(
    algorithm: str,
    n: int,
    type_count: int,
    action_profile_count: int | None = None,
    action_value_count: int | None = None,
) -> int:
    if algorithm == "joint_psrl":
        return int(type_count**n)
    if algorithm in {"hpsmg", "hpsmg_plus", "map_greedy"}:
        return int(n * type_count)
    if algorithm in {"iql", "joint_profile_iql"} and action_profile_count is not None:
        return int(n * action_profile_count)
    if algorithm == "iql_independent_actions" and action_value_count is not None:
        return int(n * action_value_count)
    return 0


def oracle_profile(state: CoordinatorState, true_types: np.ndarray) -> int:
    scores = [welfare_for_types(state.reward_tensor, true_types, index) for index in range(len(state.action_profiles))]
    return int(np.argmax(scores))


def dispatch(algorithm: str, state: CoordinatorState, rng: np.random.Generator, true_types: np.ndarray | None = None) -> int:
    algorithm = algorithm.lower()
    if algorithm == "oracle":
        if true_types is None:
            raise ValueError("oracle dispatch requires true_types")
        return oracle_profile(state, true_types)
    if algorithm == "random":
        return int(rng.integers(0, len(state.action_profiles)))

    if algorithm == "map_greedy":
        sampled_types = np.argmax(state.posterior, axis=1)
    elif algorithm == "joint_psrl":
        sampled_types = sample_explicit_joint_types(state, rng)
    elif algorithm == "psrl_notype":
        sampled_types = rng.integers(0, state.posterior.shape[1], size=state.posterior.shape[0])
    elif algorithm == "hpsmg":
        sampled_types = np.array([rng.choice(state.posterior.shape[1], p=state.posterior[player]) for player in range(state.posterior.shape[0])])
    elif algorithm == "hpsmg_plus":
        return int(np.argmax(posterior_expected_profile_scores(state, uncertainty_bonus=True)))
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")

    return int(np.argmax(expected_profile_scores(state, sampled_types, uncertainty_bonus=False)))


def sample_joint_types(posterior: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    n, type_count = posterior.shape
    combinations = np.array(list(product(range(type_count), repeat=n)), dtype=int)
    probabilities = np.ones(len(combinations), dtype=float)
    for combo_index, combo in enumerate(combinations):
        for player_index, type_index in enumerate(combo):
            probabilities[combo_index] *= posterior[player_index, type_index]
    probabilities /= probabilities.sum()
    return combinations[int(rng.choice(len(combinations), p=probabilities))]


def sample_explicit_joint_types(state: CoordinatorState, rng: np.random.Generator) -> np.ndarray:
    return state.joint_type_profiles[int(rng.choice(len(state.joint_type_profiles), p=state.joint_posterior))]


def expected_profile_scores(state: CoordinatorState, type_indices: np.ndarray, uncertainty_bonus: bool) -> np.ndarray:
    scores = np.zeros(len(state.action_profiles), dtype=float)
    uncertainty = 1.0 - np.max(state.posterior, axis=1)
    for profile_index in range(len(state.action_profiles)):
        score = float(np.sum(rewards_for_types(state.reward_tensor, type_indices, profile_index)))
        if uncertainty_bonus:
            signal_strength = np.var(state.reward_tensor[:, :, profile_index], axis=1)
            contribution_spread = float(np.std(state.action_profiles[profile_index]))
            score += state.beta * float(np.sum(uncertainty * signal_strength))
            score += 0.05 * state.beta * contribution_spread
        scores[profile_index] = score
    return scores


def posterior_expected_profile_scores(state: CoordinatorState, uncertainty_bonus: bool) -> np.ndarray:
    scores = np.zeros(len(state.action_profiles), dtype=float)
    uncertainty = 1.0 - np.max(state.posterior, axis=1)
    for profile_index in range(len(state.action_profiles)):
        score = 0.0
        for player_index in range(state.posterior.shape[0]):
            score += float(state.posterior[player_index] @ state.reward_tensor[player_index, :, profile_index])
        if uncertainty_bonus:
            signal_strength = np.var(state.reward_tensor[:, :, profile_index], axis=1)
            contribution_spread = float(np.std(state.action_profiles[profile_index]))
            score += state.beta * float(np.sum(uncertainty * signal_strength))
            score += 0.05 * state.beta * contribution_spread
        scores[profile_index] = score
    return scores


def update_posterior(state: CoordinatorState, profile_index: int, observed_rewards: np.ndarray, sigma: float = 0.08) -> None:
    likelihood_floor = 1e-9
    for player_index in range(state.posterior.shape[0]):
        expected = state.reward_tensor[player_index, :, profile_index]
        residual = observed_rewards[player_index] - expected
        likelihood = np.exp(-0.5 * (residual / sigma) ** 2) + likelihood_floor
        state.posterior[player_index] *= likelihood
        total = float(np.sum(state.posterior[player_index]))
        if total <= 0.0 or not np.isfinite(total):
            state.posterior[player_index] = 1.0 / state.posterior.shape[1]
        else:
            state.posterior[player_index] /= total
    update_joint_posterior(state, profile_index, observed_rewards, sigma=sigma)


def update_joint_posterior(state: CoordinatorState, profile_index: int, observed_rewards: np.ndarray, sigma: float = 0.08) -> None:
    likelihood_floor = 1e-12
    log_likelihood = np.zeros(len(state.joint_type_profiles), dtype=float)
    for combo_index, type_profile in enumerate(state.joint_type_profiles):
        residual = observed_rewards - state.reward_tensor[np.arange(state.posterior.shape[0]), type_profile, profile_index]
        log_likelihood[combo_index] = float(np.sum(-0.5 * (residual / sigma) ** 2))
    log_likelihood -= float(np.max(log_likelihood))
    likelihood = np.exp(log_likelihood) + likelihood_floor
    state.joint_posterior *= likelihood
    total = float(np.sum(state.joint_posterior))
    if total <= 0.0 or not np.isfinite(total):
        state.joint_posterior[:] = 1.0 / len(state.joint_posterior)
    else:
        state.joint_posterior /= total
