"""HP-SPGG-COM: a small cooperative communication layer for PACT.

This module instantiates the PACT-COM idea inside a controlled HP-SPGG-style
type model. Agents know their own hidden type, receive noisy action-derived
signals about partners' types, may reveal their own type at a cost, and then
choose type-conditioned coordination actions. The factorized evaluator computes
the expected value from per-agent type marginals; the exact evaluator enumerates
joint types and all pairwise signals for validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from time import perf_counter
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class HPSPGGComModel:
    """Tiny cooperative type-communication model.

    Attributes:
        n: number of agents.
        type_count: number of hidden types per agent.
        prior: shape ``(n, type_count)`` type prior, factorized across agents.
        type_weights: reward value for correctly coordinating with each type.
        identifiability: rho in [0, 1]; action-derived signal accuracy is
            ``1/type_count + rho * (1 - 1/type_count)``.
        coupling: kappa, scale of type-dependent coordination reward.
        comm_cost: cost paid by the team for each explicit reveal message.
    """

    n: int
    type_count: int
    prior: np.ndarray
    type_weights: np.ndarray
    identifiability: float
    coupling: float
    comm_cost: float

    @property
    def signal_accuracy(self) -> float:
        base = 1.0 / self.type_count
        return base + self.identifiability * (1.0 - base)

    @property
    def pair_count(self) -> int:
        return self.n * max(self.n - 1, 1)


@dataclass(frozen=True)
class MessagePolicy:
    """Deterministic reveal policy indexed by agent and own type."""

    name: str
    reveal: np.ndarray  # shape (n, type_count), bool

    def reveals(self, agent: int, own_type: int) -> bool:
        return bool(self.reveal[agent, own_type])


def make_model(
    *,
    n: int = 2,
    type_count: int = 2,
    identifiability: float = 0.5,
    comm_cost: float = 0.1,
    coupling: float = 1.0,
    type_weights: Iterable[float] | None = None,
) -> HPSPGGComModel:
    """Build a factorized HP-SPGG-COM model.

    The default binary weights make high-value types worth revealing at larger
    communication costs than low-value types, which yields a nontrivial middle
    region where locally optimal communication reveals selectively.
    """

    if not 0.0 <= identifiability <= 1.0:
        raise ValueError("identifiability must be in [0, 1]")
    if comm_cost < 0.0:
        raise ValueError("comm_cost must be nonnegative")
    if coupling < 0.0:
        raise ValueError("coupling must be nonnegative")
    prior = np.full((n, type_count), 1.0 / type_count, dtype=float)
    if type_weights is None:
        if type_count == 2:
            weights = np.array([0.75, 1.25], dtype=float)
        else:
            weights = np.linspace(0.75, 1.25, type_count, dtype=float)
    else:
        weights = np.asarray(list(type_weights), dtype=float)
    if weights.shape != (type_count,):
        raise ValueError("type_weights must have length type_count")
    return HPSPGGComModel(
        n=n,
        type_count=type_count,
        prior=prior,
        type_weights=weights,
        identifiability=float(identifiability),
        coupling=float(coupling),
        comm_cost=float(comm_cost),
    )


def no_comm_policy(model: HPSPGGComModel) -> MessagePolicy:
    return MessagePolicy("NO_COMM", np.zeros((model.n, model.type_count), dtype=bool))


def full_comm_policy(model: HPSPGGComModel) -> MessagePolicy:
    return MessagePolicy("FULL_COMM", np.ones((model.n, model.type_count), dtype=bool))


def heuristic_verbal_policy(model: HPSPGGComModel) -> MessagePolicy:
    """A deliberately simple prompt-style heuristic baseline.

    It communicates only when action-derived identifiability is low and message
    cost is below a fixed moderate threshold. This is not meant as a theorem;
    it is a brittle threshold policy for phase-diagram comparison.
    """

    reveal = np.zeros((model.n, model.type_count), dtype=bool)
    if model.identifiability < 0.55 and model.comm_cost < 0.18 * max(model.coupling, 1e-9):
        reveal[:, :] = True
    return MessagePolicy("VERBAL_PSRL_HEUR", reveal)


def pact_local_policy(model: HPSPGGComModel) -> MessagePolicy:
    """Closed-form local value-of-information reveal policy.

    Agent i reveals type theta_i iff the expected team-value gain from allowing
    every teammate to coordinate against the known type is at least the message
    cost. Because the cooperative reward is pairwise additive, this criterion is
    globally optimal for the restricted reveal-policy class in this model.
    """

    reveal = np.zeros((model.n, model.type_count), dtype=bool)
    for agent in range(model.n):
        for own_type in range(model.type_count):
            gain_per_observer = model.type_weights[own_type] - expected_no_reveal_value(model, agent, own_type)
            team_gain = model.coupling * (model.n - 1) * gain_per_observer / model.pair_count
            reveal[agent, own_type] = team_gain >= model.comm_cost - 1e-12
    return MessagePolicy("PACT_LOCAL", reveal)


def signal_likelihood(model: HPSPGGComModel, signal: int, true_type: int) -> float:
    if signal == true_type:
        return model.signal_accuracy
    return (1.0 - model.signal_accuracy) / max(model.type_count - 1, 1)


def posterior_from_signal(model: HPSPGGComModel, target_agent: int, signal: int) -> np.ndarray:
    probs = np.zeros(model.type_count, dtype=float)
    for theta in range(model.type_count):
        probs[theta] = model.prior[target_agent, theta] * signal_likelihood(model, signal, theta)
    total = float(probs.sum())
    if total <= 0.0:
        return np.full(model.type_count, 1.0 / model.type_count, dtype=float)
    return probs / total


def best_target_estimate(model: HPSPGGComModel, target_agent: int, belief: np.ndarray) -> int:
    scores = belief * model.type_weights
    return int(np.argmax(scores))


def expected_no_reveal_value(model: HPSPGGComModel, target_agent: int, true_type: int) -> float:
    """Expected weighted correct-match value for one observer without reveal."""

    value = 0.0
    for signal in range(model.type_count):
        belief = posterior_from_signal(model, target_agent, signal)
        guess = best_target_estimate(model, target_agent, belief)
        correct_value = model.type_weights[true_type] if guess == true_type else 0.0
        value += signal_likelihood(model, signal, true_type) * correct_value
    return float(value)


def expected_reveals(model: HPSPGGComModel, policy: MessagePolicy) -> float:
    total = 0.0
    for agent in range(model.n):
        for theta in range(model.type_count):
            if policy.reveals(agent, theta):
                total += model.prior[agent, theta]
    return float(total)


def _pair_normalizer(model: HPSPGGComModel, normalize_pairs: bool) -> float:
    return float(model.pair_count) if normalize_pairs else 1.0


def evaluate_closed_form(model: HPSPGGComModel, policy: MessagePolicy, *, normalize_pairs: bool = True) -> float:
    """Evaluate expected cooperative value using factorized type marginals."""

    pair_value = 0.0
    for observer in range(model.n):
        for target in range(model.n):
            if observer == target:
                continue
            for theta in range(model.type_count):
                p_theta = model.prior[target, theta]
                if policy.reveals(target, theta):
                    value = model.type_weights[theta]
                else:
                    value = expected_no_reveal_value(model, target, theta)
                pair_value += p_theta * value
    reward = model.coupling * pair_value / _pair_normalizer(model, normalize_pairs)
    cost = model.comm_cost * expected_reveals(model, policy)
    return float(reward - cost)


def iter_type_profiles(model: HPSPGGComModel):
    return product(range(model.type_count), repeat=model.n)


def type_profile_prob(model: HPSPGGComModel, theta_profile: tuple[int, ...]) -> float:
    p = 1.0
    for agent, theta in enumerate(theta_profile):
        p *= float(model.prior[agent, theta])
    return p


def iter_signal_profiles(model: HPSPGGComModel):
    pairs = [(observer, target) for observer in range(model.n) for target in range(model.n) if observer != target]
    for raw in product(range(model.type_count), repeat=len(pairs)):
        yield dict(zip(pairs, raw, strict=True))


def signal_profile_prob(model: HPSPGGComModel, theta_profile: tuple[int, ...], signals: dict[tuple[int, int], int]) -> float:
    p = 1.0
    for (_, target), signal in signals.items():
        p *= signal_likelihood(model, signal, theta_profile[target])
    return p


def evaluate_exact_enumeration(model: HPSPGGComModel, policy: MessagePolicy, *, normalize_pairs: bool = True) -> float:
    """Evaluate by enumerating joint types and all pairwise signal histories."""

    total = 0.0
    for theta_profile in iter_type_profiles(model):
        p_theta = type_profile_prob(model, theta_profile)
        if p_theta <= 0.0:
            continue
        reveal_count = sum(1 for agent, theta in enumerate(theta_profile) if policy.reveals(agent, theta))
        for signals in iter_signal_profiles(model):
            p_signal = signal_profile_prob(model, theta_profile, signals)
            pair_value = 0.0
            for observer in range(model.n):
                for target in range(model.n):
                    if observer == target:
                        continue
                    true_type = theta_profile[target]
                    if policy.reveals(target, true_type):
                        guess = true_type
                    else:
                        belief = posterior_from_signal(model, target, signals[(observer, target)])
                        guess = best_target_estimate(model, target, belief)
                    if guess == true_type:
                        pair_value += model.type_weights[true_type]
                reward = model.coupling * pair_value / _pair_normalizer(model, normalize_pairs)
            total += p_theta * p_signal * (reward - model.comm_cost * reveal_count)
    return float(total)


def enumerate_message_policies(model: HPSPGGComModel) -> Iterable[MessagePolicy]:
    cells = model.n * model.type_count
    for bits in product([False, True], repeat=cells):
        reveal = np.array(bits, dtype=bool).reshape(model.n, model.type_count)
        yield MessagePolicy("POLICY", reveal)


def global_optimal_policy(model: HPSPGGComModel) -> tuple[float, MessagePolicy]:
    best_value = -float("inf")
    best_policy: MessagePolicy | None = None
    for policy in enumerate_message_policies(model):
        value = evaluate_closed_form(model, policy)
        if value > best_value + 1e-12:
            best_value = value
            best_policy = policy
    assert best_policy is not None
    return float(best_value), MessagePolicy("GLOBAL_OPT", best_policy.reveal.copy())


def named_policies(model: HPSPGGComModel) -> dict[str, MessagePolicy]:
    return {
        "NO_COMM": no_comm_policy(model),
        "FULL_COMM": full_comm_policy(model),
        "VERBAL_PSRL_HEUR": heuristic_verbal_policy(model),
        "PACT_LOCAL": pact_local_policy(model),
    }


def validate_closed_form(model: HPSPGGComModel, policy: MessagePolicy, *, normalize_pairs: bool = True) -> float:
    return abs(
        evaluate_closed_form(model, policy, normalize_pairs=normalize_pairs)
        - evaluate_exact_enumeration(model, policy, normalize_pairs=normalize_pairs)
    )


def runtime_pair(model: HPSPGGComModel, policy: MessagePolicy, *, normalize_pairs: bool = True) -> dict[str, float]:
    start = perf_counter()
    closed_value = evaluate_closed_form(model, policy, normalize_pairs=normalize_pairs)
    closed_seconds = perf_counter() - start
    start = perf_counter()
    exact_value = evaluate_exact_enumeration(model, policy, normalize_pairs=normalize_pairs)
    exact_seconds = perf_counter() - start
    return {
        "n": model.n,
        "type_count": model.type_count,
        "closed_value": closed_value,
        "exact_value": exact_value,
        "abs_error": abs(closed_value - exact_value),
        "closed_seconds": closed_seconds,
        "exact_seconds": exact_seconds,
        "speedup": exact_seconds / max(closed_seconds, 1e-12),
        "normalize_pairs": normalize_pairs,
    }


def mode2_binary_myopic_voi(prob_type1: float, reward_gap: float) -> float:
    """Mode-2 T=1 value of a perfect action-space type cue.

    In the binary symmetric case, knowing the type before choosing the matched
    coordination response improves value by min(p, 1-p) times the action's
    type-separation gap.
    """

    p = min(max(float(prob_type1), 0.0), 1.0)
    return min(p, 1.0 - p) * abs(float(reward_gap))


def pact_plus_binary_disagreement_bonus(prob_type1: float, reward_gap: float) -> float:
    """PACT+ pairwise type-disagreement bonus in the same binary case.

    For reward signatures that differ by ``reward_gap`` across two candidate
    personas, E_{theta,theta' iid mu}|r(theta)-r(theta')| equals
    2 p (1-p) |reward_gap|.
    """

    p = min(max(float(prob_type1), 0.0), 1.0)
    return 2.0 * p * (1.0 - p) * abs(float(reward_gap))


def pact_plus_mode2_scale(prob_type1: float) -> float:
    """Scale factor connecting PACT+ disagreement to Mode-2 myopic VoI.

    For binary types and fixed current posterior,
    PACT+_bonus(a) = 2 max(p,1-p) * Mode2_VoI(a). The factor is constant
    across candidate actions, so both criteria rank actions identically. It is
    exactly 1 at the uniform prior p=0.5.
    """

    p = min(max(float(prob_type1), 0.0), 1.0)
    return 2.0 * max(p, 1.0 - p)


def value_for_realized_policy(
    model: HPSPGGComModel,
    theta_profile: tuple[int, ...],
    reveal: tuple[bool, ...],
    *,
    normalize_pairs: bool = True,
) -> float:
    """Realized one-shot team value for a type profile and reveal decisions.

    This is used by the live LLM probe. If a target agent reveals, every partner
    coordinates against the true type. Otherwise the partner uses the same noisy
    action-derived signal model as the analytic layer, in expectation.
    """

    if len(theta_profile) != model.n or len(reveal) != model.n:
        raise ValueError("theta_profile and reveal must have length model.n")
    pair_value = 0.0
    for observer in range(model.n):
        for target in range(model.n):
            if observer == target:
                continue
            true_type = int(theta_profile[target])
            if reveal[target]:
                pair_value += model.type_weights[true_type]
            else:
                pair_value += expected_no_reveal_value(model, target, true_type)
    reward = model.coupling * pair_value / _pair_normalizer(model, normalize_pairs)
    cost = model.comm_cost * sum(1 for flag in reveal if flag)
    return float(reward - cost)


def optimal_reveal_for_profile(model: HPSPGGComModel, theta_profile: tuple[int, ...]) -> tuple[bool, ...]:
    """Best realized reveal decision for a known type profile."""

    best_value = -float("inf")
    best_reveal: tuple[bool, ...] | None = None
    for reveal in product([False, True], repeat=model.n):
        value = value_for_realized_policy(model, theta_profile, reveal)
        if value > best_value + 1e-12:
            best_value = value
            best_reveal = tuple(bool(x) for x in reveal)
    assert best_reveal is not None
    return best_reveal