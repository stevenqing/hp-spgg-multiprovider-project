"""Decentralized HP-SPGG variant (信念分散 + 目标分散).

Each agent i:
  - maintains its own marginal posterior over OWN type (row [i]);
    beliefs about OTHER players' types stay at the uniform prior
    (no access to others' observations);
  - selects its OWN action value v_i to maximise E[r_i | own belief,
    others' actions assumed uniform marginally];
  - never optimises joint welfare.

Joint profile is composed from (v_1, ..., v_n) after every agent acts.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np


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
    def fresh(
        cls,
        player_index: int,
        n: int,
        type_count: int,
        reward_tensor: np.ndarray,
        action_profiles: np.ndarray,
        action_values: np.ndarray,
        beta: float,
    ) -> "DecentralizedAgentState":
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


def _decent_own_action_scores(
    algorithm: str,
    agent: DecentralizedAgentState,
    rng: np.random.Generator,
) -> np.ndarray:
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


def decentralized_dispatch(
    algorithm: str,
    agents: list[DecentralizedAgentState],
    rng: np.random.Generator,
    action_lookup: dict,
    true_types: np.ndarray | None = None,
) -> int:
    """Choose per-agent actions independently, return joint profile index."""
    algorithm = algorithm.lower()
    n = len(agents)
    action_values = agents[0].action_values
    chosen_values = np.zeros(n, dtype=float)
    if algorithm == "decent_random":
        for i in range(n):
            chosen_values[i] = float(action_values[int(rng.integers(0, len(action_values)))])
    elif algorithm == "decent_oracle":
        if true_types is None:
            raise ValueError("decent_oracle dispatch requires true_types")
        # Each agent knows OWN true type, optimises own reward over its own action
        # assuming others' actions are uniform.
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


def update_decentralized(
    agent: DecentralizedAgentState,
    profile_index: int,
    own_observed_reward: float,
    sigma: float = 0.08,
) -> None:
    """Each agent updates ONLY its own marginal posterior row from OWN observed reward."""
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
