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
    belief_text: str | None = None

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
    if algorithm == "joint_psrl_aware":
        return int(type_count)
    if algorithm in {"joint_psrl", "joint_psrl_uniform"}:
        return int(type_count**n)
    if algorithm in {"hpsmg", "hpsmg_plus", "map_greedy"}:
        return int(n * type_count)
    if algorithm == "llm_psrl_verbal":
        return 0
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
    elif algorithm in {"joint_psrl", "joint_psrl_uniform", "joint_psrl_aware"}:
        sampled_types = sample_explicit_joint_types(state, rng)
    elif algorithm == "psrl_notype":
        sampled_types = rng.integers(0, state.posterior.shape[1], size=state.posterior.shape[0])
    elif algorithm == "hpsmg":
        sampled_types = np.array([rng.choice(state.posterior.shape[1], p=state.posterior[player]) for player in range(state.posterior.shape[0])])
    elif algorithm == "llm_psrl_verbal":
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


# ============================================================
# Decentralized HP-SPGG variant (???? + ????)
# ============================================================
# Each agent i:
#   - maintains its own marginal posterior over OWN type (row [i]);
#     beliefs about OTHER players' types stay at the uniform prior
#     (no access to others' observations);
#   - selects its OWN action value v_i to maximise E[r_i | own belief,
#     others' actions assumed uniform marginally];
#   - never optimises joint welfare.
# Joint profile is composed from (v_1, ..., v_n) after every agent acts.

@dataclass
class DecentralizedAgentState:
    player_index: int
    posterior: np.ndarray            # (n, type_count); only row [player_index] is updated
    reward_tensor: np.ndarray        # (n, type_count, num_profiles)
    action_profiles: np.ndarray      # (num_profiles, n) action values
    action_values: np.ndarray        # sorted unique action values
    profiles_by_own_action: dict     # av_idx -> 1d np.ndarray of profile indices where profile[i] == action_values[av_idx]
    beta: float = 1.0

    @classmethod
    def fresh(cls, player_index: int, n: int, type_count: int, reward_tensor: np.ndarray, action_profiles: np.ndarray, action_values: np.ndarray, beta: float) -> "DecentralizedAgentState":
        posterior = np.full((n, type_count), 1.0 / type_count, dtype=float)
        profiles_by_own_action: dict[int, np.ndarray] = {}
        for av_idx, value in enumerate(action_values):
            matching = np.where(np.isclose(action_profiles[:, player_index], value))[0]
            profiles_by_own_action[av_idx] = matching
        return cls(
            player_index=player_index,
            posterior=posterior,
            reward_tensor=reward_tensor,
            action_profiles=action_profiles,
            action_values=action_values,
            profiles_by_own_action=profiles_by_own_action,
            beta=beta,
        )


def _decent_own_action_scores(algorithm: str, agent: DecentralizedAgentState, rng: np.random.Generator) -> np.ndarray:
    """Per-own-action score for agent. Marginalises over others' actions uniformly."""
    i = agent.player_index
    posterior = agent.posterior
    type_count = posterior.shape[1]

    if algorithm == "decent_map_greedy":
        own_type = int(np.argmax(posterior[i]))
        own_row = agent.reward_tensor[i, own_type, :]
    elif algorithm == "decent_hpsmg":
        own_type = int(rng.choice(type_count, p=posterior[i]))
        own_row = agent.reward_tensor[i, own_type, :]
    elif algorithm == "decent_hpsmg_plus":
        own_row = posterior[i] @ agent.reward_tensor[i, :, :]  # (num_profiles,)
    else:
        raise ValueError(f"Unknown decentralized algorithm: {algorithm}")

    scores = np.zeros(len(agent.action_values), dtype=float)
    for av_idx, profile_indices in agent.profiles_by_own_action.items():
        if len(profile_indices) == 0:
            scores[av_idx] = -np.inf
            continue
        score = float(np.mean(own_row[profile_indices]))
        if algorithm == "decent_hpsmg_plus":
            own_uncertainty = 1.0 - float(np.max(posterior[i]))
            signal_strength = float(np.mean(np.var(agent.reward_tensor[i, :, profile_indices], axis=1)))
            score += agent.beta * own_uncertainty * signal_strength
        scores[av_idx] = score
    return scores


def decentralized_dispatch(algorithm: str, agents: list[DecentralizedAgentState], rng: np.random.Generator, action_lookup: dict, true_types: np.ndarray | None = None) -> int:
    """Choose per-agent actions independently, return joint profile index."""
    algorithm = algorithm.lower()
    n = len(agents)
    action_values = agents[0].action_values
    chosen_values = np.zeros(n, dtype=float)
    if algorithm == "decent_random":
        for i, agent in enumerate(agents):
            chosen_values[i] = float(action_values[int(rng.integers(0, len(action_values)))])
    elif algorithm == "decent_oracle":
        if true_types is None:
            raise ValueError("decent_oracle dispatch requires true_types")
        # Each agent knows OWN true type, optimises own reward over its own action assuming others' actions uniform.
        for i, agent in enumerate(agents):
            own_row = agent.reward_tensor[i, int(true_types[i]), :]
            scores = np.full(len(action_values), -np.inf)
            for av_idx, profile_indices in agent.profiles_by_own_action.items():
                if len(profile_indices) > 0:
                    scores[av_idx] = float(np.mean(own_row[profile_indices]))
            chosen_values[i] = float(action_values[int(np.argmax(scores))])
    else:
        for i, agent in enumerate(agents):
            scores = _decent_own_action_scores(algorithm, agent, rng)
            chosen_values[i] = float(action_values[int(np.argmax(scores))])
    key = tuple(float(v) for v in chosen_values)
    return int(action_lookup[key])


def update_decentralized(agent: DecentralizedAgentState, profile_index: int, own_observed_reward: float, sigma: float = 0.08) -> None:
    """Each agent updates ONLY its own marginal posterior row using OWN observed reward."""
    likelihood_floor = 1e-9
    i = agent.player_index
    expected = agent.reward_tensor[i, :, profile_index]
    residual = own_observed_reward - expected
    likelihood = np.exp(-0.5 * (residual / sigma) ** 2) + likelihood_floor
    agent.posterior[i] *= likelihood
    total = float(np.sum(agent.posterior[i]))
    if total <= 0.0 or not np.isfinite(total):
        agent.posterior[i] = 1.0 / agent.posterior.shape[1]
    else:
        agent.posterior[i] /= total


DECENTRALIZED_ALGORITHMS = {
    "decent_random",
    "decent_oracle",
    "decent_map_greedy",
    "decent_hpsmg",
    "decent_hpsmg_plus",
}