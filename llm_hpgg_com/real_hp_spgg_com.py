"""PACT-COM on the real HP-SPGG reward tensor and action grid."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from pathlib import Path
from time import perf_counter
from typing import Iterable

import numpy as np

from llm_hpgg.environment import ACTIONS, build_reward_tensor, load_calibration


@dataclass(frozen=True)
class RealHPSPGGComModel:
    reward_tensor: np.ndarray  # (n, type_count, profile_count)
    action_profiles: np.ndarray  # (profile_count, n)
    prior: np.ndarray  # (n, type_count)
    action_likelihood: np.ndarray  # (n, type_count, action_value_count)
    comm_cost: float
    identifiability: float
    source: str

    @property
    def n(self) -> int:
        return int(self.reward_tensor.shape[0])

    @property
    def type_count(self) -> int:
        return int(self.reward_tensor.shape[1])

    @property
    def action_values(self) -> np.ndarray:
        return np.array(sorted({float(x) for x in self.action_profiles.reshape(-1)}), dtype=float)


@dataclass(frozen=True)
class RealMessagePolicy:
    name: str
    reveal: np.ndarray  # (n, type_count), bool

    def reveals(self, agent: int, own_type: int) -> bool:
        return bool(self.reveal[agent, own_type])


def softmax(values: np.ndarray, temperature: float) -> np.ndarray:
    if temperature <= 0.0:
        out = np.zeros_like(values, dtype=float)
        out[int(np.argmax(values))] = 1.0
        return out
    scaled = values / temperature
    scaled -= float(np.max(scaled))
    exp = np.exp(scaled)
    return exp / float(exp.sum())


def action_preferences(reward_tensor: np.ndarray, action_profiles: np.ndarray, identifiability: float, temperature: float = 0.08) -> np.ndarray:
    n, type_count, _ = reward_tensor.shape
    action_values = np.array(sorted({float(x) for x in action_profiles.reshape(-1)}), dtype=float)
    uniform = np.full(len(action_values), 1.0 / len(action_values), dtype=float)
    rho = min(max(float(identifiability), 0.0), 1.0)
    out = np.zeros((n, type_count, len(action_values)), dtype=float)
    for agent in range(n):
        for theta in range(type_count):
            scores = []
            for value in action_values:
                mask = np.isclose(action_profiles[:, agent], value)
                scores.append(float(np.mean(reward_tensor[agent, theta, mask])))
            type_policy = softmax(np.asarray(scores, dtype=float), temperature)
            out[agent, theta] = (1.0 - rho) * uniform + rho * type_policy
    return out


def make_real_model(
    *,
    n: int = 2,
    calibration: str | None = None,
    comm_cost: float = 0.1,
    identifiability: float = 0.5,
    backend: str = "analytic",
    samples: int = 1,
    seed: int = 0,
    trap: bool = False,
) -> RealHPSPGGComModel:
    if calibration:
        data = load_calibration(calibration)
        reward_tensor = np.asarray(data["reward_tensor"], dtype=float)
        action_profiles = np.asarray(data["action_profiles"], dtype=float)
        source = str(calibration)
    else:
        bundle = build_reward_tensor(n=n, backend=backend, samples=samples, seed=seed, trap=trap)
        reward_tensor = np.asarray(bundle.reward_tensor, dtype=float)
        action_profiles = np.asarray(bundle.action_profiles, dtype=float)
        source = f"build_reward_tensor(n={n}, backend={backend}, samples={samples}, seed={seed}, trap={trap})"
    prior = np.full(reward_tensor.shape[:2], 1.0 / reward_tensor.shape[1], dtype=float)
    likelihood = action_preferences(reward_tensor, action_profiles, identifiability)
    return RealHPSPGGComModel(
        reward_tensor=reward_tensor,
        action_profiles=action_profiles,
        prior=prior,
        action_likelihood=likelihood,
        comm_cost=float(comm_cost),
        identifiability=float(identifiability),
        source=source,
    )


def no_comm_policy(model: RealHPSPGGComModel) -> RealMessagePolicy:
    return RealMessagePolicy("NO_COMM", np.zeros((model.n, model.type_count), dtype=bool))


def full_comm_policy(model: RealHPSPGGComModel) -> RealMessagePolicy:
    return RealMessagePolicy("FULL_COMM", np.ones((model.n, model.type_count), dtype=bool))


def verbal_heur_policy(model: RealHPSPGGComModel) -> RealMessagePolicy:
    reveal = np.zeros((model.n, model.type_count), dtype=bool)
    if model.identifiability < 0.55 and model.comm_cost < 0.18:
        reveal[:, :] = True
    return RealMessagePolicy("VERBAL_PSRL_HEUR", reveal)


def action_index(model: RealHPSPGGComModel, action_value: float) -> int:
    values = model.action_values
    matches = np.where(np.isclose(values, action_value))[0]
    if len(matches) == 0:
        raise ValueError(f"Unknown action value: {action_value}")
    return int(matches[0])


def posterior_from_action_signal(model: RealHPSPGGComModel, agent: int, signal_index: int, policy: RealMessagePolicy | None = None) -> np.ndarray:
    probs = np.zeros(model.type_count, dtype=float)
    for theta in range(model.type_count):
        if policy is not None and policy.reveals(agent, theta):
            continue
        probs[theta] = model.prior[agent, theta] * model.action_likelihood[agent, theta, signal_index]
    total = float(probs.sum())
    if total <= 0.0:
        return np.full(model.type_count, 1.0 / model.type_count, dtype=float)
    return probs / total


def expected_profile_scores(model: RealHPSPGGComModel, beliefs: tuple[np.ndarray, ...]) -> np.ndarray:
    scores = np.zeros(len(model.action_profiles), dtype=float)
    for profile_index in range(len(model.action_profiles)):
        score = 0.0
        for agent in range(model.n):
            score += float(beliefs[agent] @ model.reward_tensor[agent, :, profile_index])
        scores[profile_index] = score
    return scores


def actual_welfare(model: RealHPSPGGComModel, theta_profile: tuple[int, ...], profile_index: int) -> float:
    return float(sum(model.reward_tensor[agent, theta_profile[agent], profile_index] for agent in range(model.n)))


def agent_outcomes(model: RealHPSPGGComModel, agent: int, policy: RealMessagePolicy) -> list[tuple[float, np.ndarray, int]]:
    outcomes: list[tuple[float, np.ndarray, int]] = []
    for theta in range(model.type_count):
        if policy.reveals(agent, theta):
            belief = np.zeros(model.type_count, dtype=float)
            belief[theta] = 1.0
            outcomes.append((float(model.prior[agent, theta]), belief, 1))
    for signal in range(len(model.action_values)):
        prob = 0.0
        for theta in range(model.type_count):
            if policy.reveals(agent, theta):
                continue
            prob += float(model.prior[agent, theta] * model.action_likelihood[agent, theta, signal])
        if prob <= 0.0:
            continue
        outcomes.append((prob, posterior_from_action_signal(model, agent, signal, policy), 0))
    return outcomes


def evaluate_factorized(model: RealHPSPGGComModel, policy: RealMessagePolicy) -> float:
    total = 0.0
    per_agent = [agent_outcomes(model, agent, policy) for agent in range(model.n)]
    for outcome_profile in product(*per_agent):
        prob = 1.0
        beliefs = []
        messages = 0
        for outcome_prob, belief, message_count in outcome_profile:
            prob *= outcome_prob
            beliefs.append(belief)
            messages += message_count
        scores = expected_profile_scores(model, tuple(beliefs))
        total += prob * (float(np.max(scores)) - model.comm_cost * messages)
    return float(total)


def iter_type_profiles(model: RealHPSPGGComModel):
    return product(range(model.type_count), repeat=model.n)


def type_profile_prob(model: RealHPSPGGComModel, theta_profile: tuple[int, ...]) -> float:
    prob = 1.0
    for agent, theta in enumerate(theta_profile):
        prob *= float(model.prior[agent, theta])
    return prob


def evaluate_exact(model: RealHPSPGGComModel, policy: RealMessagePolicy) -> float:
    total = 0.0
    signal_values = range(len(model.action_values))
    for theta_profile in iter_type_profiles(model):
        p_theta = type_profile_prob(model, theta_profile)
        reveal_count = sum(1 for agent, theta in enumerate(theta_profile) if policy.reveals(agent, theta))
        signal_ranges = [signal_values if not policy.reveals(agent, theta_profile[agent]) else [None] for agent in range(model.n)]
        for signal_profile in product(*signal_ranges):
            p_signal = 1.0
            beliefs = []
            for agent, signal in enumerate(signal_profile):
                true_theta = theta_profile[agent]
                if signal is None:
                    belief = np.zeros(model.type_count, dtype=float)
                    belief[true_theta] = 1.0
                else:
                    p_signal *= float(model.action_likelihood[agent, true_theta, signal])
                    belief = posterior_from_action_signal(model, agent, int(signal), policy)
                beliefs.append(belief)
            chosen = int(np.argmax(expected_profile_scores(model, tuple(beliefs))))
            total += p_theta * p_signal * (actual_welfare(model, theta_profile, chosen) - model.comm_cost * reveal_count)
    return float(total)


def enumerate_policies(model: RealHPSPGGComModel) -> Iterable[RealMessagePolicy]:
    for bits in product([False, True], repeat=model.n * model.type_count):
        reveal = np.array(bits, dtype=bool).reshape(model.n, model.type_count)
        yield RealMessagePolicy("POLICY", reveal)


def global_optimal_policy(model: RealHPSPGGComModel) -> tuple[float, RealMessagePolicy]:
    best_value = -float("inf")
    best_policy: RealMessagePolicy | None = None
    for policy in enumerate_policies(model):
        value = evaluate_factorized(model, policy)
        if value > best_value + 1e-12:
            best_value = value
            best_policy = policy
    assert best_policy is not None
    return best_value, RealMessagePolicy("GLOBAL_OPT", best_policy.reveal.copy())


def pact_local_policy(model: RealHPSPGGComModel) -> RealMessagePolicy:
    reveal = np.zeros((model.n, model.type_count), dtype=bool)
    current = RealMessagePolicy("PACT_LOCAL", reveal.copy())
    improved = True
    while improved:
        improved = False
        base_value = evaluate_factorized(model, current)
        for agent in range(model.n):
            for theta in range(model.type_count):
                candidate_reveal = current.reveal.copy()
                candidate_reveal[agent, theta] = not candidate_reveal[agent, theta]
                candidate = RealMessagePolicy("PACT_LOCAL", candidate_reveal)
                candidate_value = evaluate_factorized(model, candidate)
                if candidate_value > base_value + 1e-12:
                    current = candidate
                    base_value = candidate_value
                    improved = True
    return current


def named_policies(model: RealHPSPGGComModel) -> dict[str, RealMessagePolicy]:
    return {
        "NO_COMM": no_comm_policy(model),
        "FULL_COMM": full_comm_policy(model),
        "VERBAL_PSRL_HEUR": verbal_heur_policy(model),
        "PACT_LOCAL": pact_local_policy(model),
    }


def runtime_pair(model: RealHPSPGGComModel, policy: RealMessagePolicy) -> dict[str, float | int | bool]:
    start = perf_counter()
    closed = evaluate_factorized(model, policy)
    closed_seconds = perf_counter() - start
    start = perf_counter()
    exact = evaluate_exact(model, policy)
    exact_seconds = perf_counter() - start
    return {
        "n": model.n,
        "type_count": model.type_count,
        "action_values": len(model.action_values),
        "closed_value": closed,
        "exact_value": exact,
        "abs_error": abs(closed - exact),
        "closed_seconds": closed_seconds,
        "exact_seconds": exact_seconds,
        "speedup": exact_seconds / max(closed_seconds, 1e-12),
    }