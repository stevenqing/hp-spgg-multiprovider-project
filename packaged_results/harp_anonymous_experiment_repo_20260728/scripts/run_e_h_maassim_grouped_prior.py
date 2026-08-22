"""Run E-H: MaaSSim grouped coupling over the full driver persona.

The runner reuses E-E queue snapshots, likelihood, assignment objective, and
utility. Only the driver persona map changes with (rho, group_size, seed).
No provider calls are made: driver responses are deterministic hidden rules.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_courier_dispatch.dispatch_env import ACCEPT, DECLINE_B, CourierDispatchEnv
from llm_courier_dispatch_maassim.adapter import MaaSSimCandidateOffer, MaaSSimQueueSnapshot
from llm_courier_dispatch_maassim.hidden_rules import grouped_driver_types, synthetic_action_for_type
from scripts.run_e_e_maassim_tracker_parity import (
    FactoredTracker,
    RULE_CONFIG,
    UtilityStats,
    cell_paths,
    choose_assignment,
    conflict_transform,
    evaluate_assignment,
    legal_assignments,
    likelihood_vector,
    load_cell,
)


DEFAULT_SOURCE_ROOT = ROOT / "analysis" / "e_e_maassim_rq2"
DEFAULT_OUT = ROOT / "analysis" / "e_h_maassim_grouped_prior"
ARMS = ("oracle", "joint", "harp", "harp_s")
BETA = 0.25
PREREGISTERED_PREDICTIONS = {
    "P1": "At rho=0, HARP-Joint covers zero and HARP-S is trajectory-identical to HARP.",
    "P2": "The paired gap rises monotonically with rho and measured posterior correlation.",
    "P3": "The paired gap rises with group size g.",
    "P4": "HARP-S restores a zero-covering paired gap at unchanged HARP storage.",
}


def logsumexp(values: np.ndarray) -> float:
    maximum = float(np.max(values))
    return maximum + math.log(float(np.exp(values - maximum).sum()))


def tempered_probabilities(probabilities: np.ndarray, alpha: float) -> np.ndarray:
    if not 0.0 < alpha <= 1.0:
        raise ValueError(f"joint alpha must be in (0, 1], got {alpha}")
    values = np.asarray(probabilities, dtype=float)
    if alpha == 1.0:
        return values
    positive = values > 0.0
    log_weights = np.full(values.shape, -np.inf, dtype=float)
    log_weights[positive] = alpha * np.log(values[positive])
    weights = np.exp(log_weights - float(np.max(log_weights)))
    return weights / float(weights.sum())


def categorical_from_uniform(probabilities: np.ndarray, uniform: float) -> int:
    cumulative = np.cumsum(np.asarray(probabilities, dtype=float))
    return min(int(np.searchsorted(cumulative, uniform, side="right")), len(cumulative) - 1)


class GroupedJointTracker:
    """Exact shared-group/factored two-component posterior over full personas."""

    def __init__(self, driver_ids: list[int], type_space: np.ndarray, rho: float, group_size: int):
        self.driver_ids = list(sorted(driver_ids))
        self.driver_index = {driver_id: index for index, driver_id in enumerate(self.driver_ids)}
        self.type_space = np.asarray(type_space, dtype=int)
        self.groups = [self.driver_ids[start:start + group_size] for start in range(0, len(self.driver_ids), group_size)]
        self.group_for_driver = {
            driver_id: group_index
            for group_index, group in enumerate(self.groups)
            for driver_id in group
        }
        type_count = len(self.type_space)
        shared_shape = (type_count,) * len(self.groups)
        self.shared_states = np.asarray(
            np.unravel_index(np.arange(type_count ** len(self.groups)), shared_shape),
            dtype=int,
        ).T
        self.shared_probs = np.full(len(self.shared_states), 1.0 / len(self.shared_states), dtype=float)
        self.independent_probs = np.full((len(self.driver_ids), type_count), 1.0 / type_count, dtype=float)
        self.shared_weight = float(rho)
        self.prior_rho = float(rho)

    @property
    def belief_bytes(self) -> int:
        return int(self.shared_probs.nbytes + self.independent_probs.nbytes + 8)

    def update(self, driver_id: int, log_likelihood: np.ndarray) -> None:
        driver_index = self.driver_index[int(driver_id)]
        likelihood = np.exp(np.asarray(log_likelihood, dtype=float))
        group_index = self.group_for_driver[int(driver_id)]
        shared_weighted = self.shared_probs * likelihood[self.shared_states[:, group_index]]
        shared_evidence = max(float(shared_weighted.sum()), 1e-300)
        self.shared_probs = shared_weighted / shared_evidence
        independent_weighted = self.independent_probs[driver_index] * likelihood
        independent_evidence = max(float(independent_weighted.sum()), 1e-300)
        self.independent_probs[driver_index] = independent_weighted / independent_evidence
        numerator = self.shared_weight * shared_evidence
        denominator = numerator + (1.0 - self.shared_weight) * independent_evidence
        self.shared_weight = float(numerator / max(denominator, 1e-300))

    def shared_marginals(self) -> np.ndarray:
        group_marginals = np.empty((len(self.groups), len(self.type_space)), dtype=float)
        for group_index in range(len(self.groups)):
            group_marginals[group_index] = np.bincount(
                self.shared_states[:, group_index],
                weights=self.shared_probs,
                minlength=len(self.type_space),
            )
        return np.asarray(
            [group_marginals[self.group_for_driver[driver_id]] for driver_id in self.driver_ids],
            dtype=float,
        )

    def marginals(self) -> np.ndarray:
        return self.shared_weight * self.shared_marginals() + (1.0 - self.shared_weight) * self.independent_probs

    def sample_profile(self, rng: np.random.Generator, alpha: float = 1.0) -> np.ndarray:
        result = np.empty((len(self.driver_ids), self.type_space.shape[1]), dtype=int)
        if self.shared_weight <= 0.0:
            for driver_index in range(len(self.driver_ids)):
                weights = tempered_probabilities(self.independent_probs[driver_index], alpha)
                type_index = int(rng.choice(len(self.type_space), p=weights))
                result[driver_index] = self.type_space[type_index]
        elif float(rng.random()) < self.shared_weight:
            weights = tempered_probabilities(self.shared_probs, alpha)
            state_index = int(rng.choice(len(self.shared_probs), p=weights))
            group_types = self.shared_states[state_index]
            for group_index, group in enumerate(self.groups):
                for driver_id in group:
                    result[self.driver_index[driver_id]] = self.type_space[group_types[group_index]]
        else:
            for driver_index in range(len(self.driver_ids)):
                weights = tempered_probabilities(self.independent_probs[driver_index], alpha)
                type_index = int(rng.choice(len(self.type_space), p=weights))
                result[driver_index] = self.type_space[type_index]
        return result

    def sample_profile_from_uniforms(self, uniforms: np.ndarray, alpha: float = 1.0) -> np.ndarray:
        values = np.asarray(uniforms, dtype=float)
        result = np.empty((len(self.driver_ids), self.type_space.shape[1]), dtype=int)
        if self.shared_weight <= 0.0:
            for driver_index in range(len(self.driver_ids)):
                weights = tempered_probabilities(self.independent_probs[driver_index], alpha)
                type_index = categorical_from_uniform(weights, float(values[driver_index]))
                result[driver_index] = self.type_space[type_index]
            return result
        if self.shared_weight < 1.0:
            raise ValueError("common-random-number sampling is defined only at rho endpoints")
        weights = tempered_probabilities(self.shared_probs, alpha)
        for group_index, group in enumerate(self.groups):
            group_weights = np.bincount(
                self.shared_states[:, group_index],
                weights=weights,
                minlength=len(self.type_space),
            )
            group_weights /= float(group_weights.sum())
            uniform_index = self.driver_index[group[0]]
            type_index = categorical_from_uniform(group_weights, float(values[uniform_index]))
            for driver_id in group:
                result[self.driver_index[driver_id]] = self.type_space[type_index]
        return result

    def true_profile_mass(self, true_profile: np.ndarray) -> float:
        profile = np.asarray(true_profile, dtype=int)
        type_indices = []
        for row in profile:
            matches = np.where(np.all(self.type_space == row, axis=1))[0]
            if len(matches) != 1:
                return 0.0
            type_indices.append(int(matches[0]))
        independent_mass = float(
            np.prod(
                self.independent_probs[
                    np.arange(len(self.driver_ids)), np.asarray(type_indices, dtype=int)
                ]
            )
        )
        group_types = []
        for group in self.groups:
            values = {type_indices[self.driver_index[driver_id]] for driver_id in group}
            if len(values) != 1:
                shared_mass = 0.0
                break
            group_types.append(values.pop())
        else:
            matches = np.where(np.all(self.shared_states == np.asarray(group_types, dtype=int), axis=1))[0]
            shared_mass = float(self.shared_probs[int(matches[0])]) if len(matches) == 1 else 0.0
        return float(self.shared_weight * shared_mass + (1.0 - self.shared_weight) * independent_mass)

    def corr_tv(self) -> float:
        if self.shared_weight <= 1e-12:
            return 0.0
        marginals = self.marginals()
        if self.shared_weight >= 1.0 - 1e-12:
            product_on_support = np.ones(len(self.shared_states), dtype=float)
            for group_index, group in enumerate(self.groups):
                for driver_id in group:
                    product_on_support *= marginals[
                        self.driver_index[driver_id], self.shared_states[:, group_index]
                    ]
            return float(
                0.5
                * (
                    np.abs(self.shared_probs - product_on_support).sum()
                    + 1.0
                    - product_on_support.sum()
                )
            )
        return self._estimated_corr_tv(marginals)

    def _estimated_corr_tv(self, marginals: np.ndarray, samples: int = 32768) -> float:
        rng = np.random.default_rng(97_531)

        def independent_probability(profile_indices: np.ndarray) -> float:
            return float(
                np.prod(
                    self.independent_probs[np.arange(len(self.driver_ids)), profile_indices]
                )
            )

        def marginal_product(profile_indices: np.ndarray) -> float:
            return float(np.prod(marginals[np.arange(len(self.driver_ids)), profile_indices]))

        shared_lookup = {tuple(state.tolist()): float(probability) for state, probability in zip(self.shared_states, self.shared_probs)}

        def shared_probability(profile_indices: np.ndarray) -> float:
            group_types = []
            for group in self.groups:
                values = {int(profile_indices[self.driver_index[driver_id]]) for driver_id in group}
                if len(values) != 1:
                    return 0.0
                group_types.append(values.pop())
            return shared_lookup.get(tuple(group_types), 0.0)

        total = 0.0
        for index in range(samples):
            if index % 2 == 0:
                profile = np.asarray(
                    [int(rng.choice(len(self.type_space), p=marginals[driver])) for driver in range(len(self.driver_ids))],
                    dtype=int,
                )
            elif float(rng.random()) < self.shared_weight:
                state = self.shared_states[int(rng.choice(len(self.shared_probs), p=self.shared_probs))]
                profile = np.asarray(
                    [int(state[self.group_for_driver[driver_id]]) for driver_id in self.driver_ids],
                    dtype=int,
                )
            else:
                profile = np.asarray(
                    [int(rng.choice(len(self.type_space), p=self.independent_probs[driver])) for driver in range(len(self.driver_ids))],
                    dtype=int,
                )
            p_value = self.shared_weight * shared_probability(profile) + (1.0 - self.shared_weight) * independent_probability(profile)
            q_value = marginal_product(profile)
            total += abs(p_value - q_value) / max(p_value + q_value, 1e-300)
        return float(total / samples)


@dataclass(frozen=True)
class Trace:
    rows: list[dict[str, object]]
    actions: dict[str, tuple[tuple[tuple[int, int], ...], ...]]
    sampled_profile_traces: dict[str, tuple[tuple[tuple[int, ...], ...], ...]]
    utility_traces: dict[str, tuple[float, ...]]
    regret_traces: dict[str, tuple[float, ...]]
    assigned_type_hit_traces: dict[str, tuple[float, ...]]
    marginal_true_mass_traces: dict[str, tuple[float, ...]]
    true_profile_mass_traces: dict[str, tuple[float, ...]]
    joint_shared_weight_pre: tuple[float, ...]
    joint_shared_weight_post: tuple[float, ...]
    joint_shared_support_size_pre: tuple[int, ...]
    joint_shared_positive_ratio_pre: tuple[float, ...]
    request_sequence: tuple[tuple[int, ...], ...]
    final_factored_marginals: np.ndarray
    final_joint_marginals: np.ndarray


def restricted_snapshot(snapshot: MaaSSimQueueSnapshot, m: int) -> MaaSSimQueueSnapshot:
    available = {int(offer.request_id) for offer in snapshot.candidates}
    ordered = [int(request_id) for request_id in snapshot.request_queue if int(request_id) in available]
    ordered.extend(sorted(available - set(ordered)))
    selected = set(ordered[:m])
    candidates = tuple(offer for offer in snapshot.candidates if int(offer.request_id) in selected)
    return MaaSSimQueueSnapshot(snapshot.time, snapshot.vehicle_queue, tuple(ordered[:m]), candidates)


def selected_rounds(snapshots: list[tuple[MaaSSimQueueSnapshot, list[tuple[int, int]]]], k: int, m: int) -> list[MaaSSimQueueSnapshot]:
    result = []
    for snapshot, _ in snapshots:
        restricted = restricted_snapshot(snapshot, m)
        if legal_assignments(restricted):
            result.append(restricted)
        if len(result) == k:
            break
    if len(result) != k:
        raise AssertionError(f"only {len(result)} usable snapshots for K={k}, m={m}")
    return result


def harp_s_profile(
    tracker: FactoredTracker,
    rng: np.random.Generator,
    driver_ids: list[int],
    groups: list[list[int]],
    rho: float,
) -> np.ndarray:
    if rho == 0.0:
        return tracker.sample_profile(rng)
    driver_index = {driver_id: index for index, driver_id in enumerate(driver_ids)}
    probabilities = tracker.marginals()
    log_probabilities = np.log(np.clip(probabilities, 1e-12, 1.0))
    profile = np.empty((len(driver_ids), tracker.type_space.shape[1]), dtype=int)
    for group in groups:
        indices = [driver_index[driver_id] for driver_id in group]
        group_log_probabilities = log_probabilities[indices].sum(axis=0)
        shared_type_index = None
        if rho == 1.0:
            shared_weights = np.exp(group_log_probabilities - float(np.max(group_log_probabilities)))
            shared_weights /= float(shared_weights.sum())
            shared_type_index = int(rng.choice(len(tracker.type_space), p=shared_weights))
        for driver_id in group:
            index = driver_index[driver_id]
            if shared_type_index is not None:
                type_index = shared_type_index
            else:
                weighted = log_probabilities[index] + rho * (
                    group_log_probabilities - log_probabilities[index]
                )
                weights = np.exp(weighted - float(np.max(weighted)))
                weights /= float(weights.sum())
                type_index = int(rng.choice(len(tracker.type_space), p=weights))
            profile[index] = tracker.type_space[type_index]
    return profile


def factored_profile_from_uniforms(tracker: FactoredTracker, uniforms: np.ndarray) -> np.ndarray:
    probabilities = tracker.marginals()
    indices = [
        categorical_from_uniform(probabilities[index], float(uniforms[index]))
        for index in range(len(probabilities))
    ]
    return tracker.type_space[np.asarray(indices, dtype=int)]


def harp_s_profile_from_uniforms(
    tracker: FactoredTracker,
    uniforms: np.ndarray,
    driver_ids: list[int],
    groups: list[list[int]],
    rho: float,
) -> np.ndarray:
    if rho == 0.0:
        return factored_profile_from_uniforms(tracker, uniforms)
    if rho != 1.0:
        raise ValueError("common-random-number HARP-S sampling is defined only at rho endpoints")
    driver_index = {driver_id: index for index, driver_id in enumerate(driver_ids)}
    probabilities = tracker.marginals()
    log_probabilities = np.log(np.clip(probabilities, 1e-12, 1.0))
    profile = np.empty((len(driver_ids), tracker.type_space.shape[1]), dtype=int)
    for group in groups:
        indices = [driver_index[driver_id] for driver_id in group]
        group_log_probabilities = log_probabilities[indices].sum(axis=0)
        weights = np.exp(group_log_probabilities - float(np.max(group_log_probabilities)))
        weights /= float(weights.sum())
        uniform_index = indices[0]
        type_index = categorical_from_uniform(weights, float(uniforms[uniform_index]))
        for index in indices:
            profile[index] = tracker.type_space[type_index]
    return profile


def request_signature(snapshot: MaaSSimQueueSnapshot) -> tuple[int, ...]:
    return tuple(int(request_id) for request_id in snapshot.request_queue)


def observation_log_likelihood(
    env: CourierDispatchEnv,
    offer: MaaSSimCandidateOffer,
    features: dict[str, float | int],
    action: int,
    mode: str,
) -> np.ndarray:
    if mode == "softmax":
        return likelihood_vector(env, features, action)
    if mode != "deterministic-rule":
        raise ValueError(f"unknown likelihood mode: {mode}")
    matches = np.asarray(
        [
            synthetic_action_for_type(
                tuple(int(value) for value in theta), offer, RULE_CONFIG
            )[0]
            == int(action)
            for theta in env.type_space
        ],
        dtype=bool,
    )
    if not np.any(matches):
        raise AssertionError("deterministic likelihood has empty support")
    return np.where(matches, 0.0, -np.inf)


def realized_rule_correlation(true_types: dict[int, tuple[int, int, int, int]], groups: list[list[int]]) -> float:
    pairs = []
    for group in groups:
        for left in range(len(group)):
            for right in range(left + 1, len(group)):
                pairs.append(float(true_types[group[left]][0] == true_types[group[right]][0]))
    return float(np.mean(pairs)) if pairs else 1.0


def true_type_indices(type_space: np.ndarray, true_profile: np.ndarray) -> np.ndarray:
    indices = []
    for row in np.asarray(true_profile, dtype=int):
        matches = np.where(np.all(type_space == row, axis=1))[0]
        if len(matches) != 1:
            raise AssertionError(f"true type is outside type space: {row}")
        indices.append(int(matches[0]))
    return np.asarray(indices, dtype=int)


def marginal_true_mass(marginals: np.ndarray, true_indices: np.ndarray) -> float:
    return float(np.mean(marginals[np.arange(len(true_indices)), true_indices]))


def factored_profile_mass(marginals: np.ndarray, true_indices: np.ndarray) -> float:
    return float(np.prod(marginals[np.arange(len(true_indices)), true_indices]))


def assigned_type_hit(
    assignment: tuple[tuple[int, int], ...],
    sampled_profile: np.ndarray,
    true_profile: np.ndarray,
    driver_index: dict[int, int],
) -> float:
    if not assignment:
        return float("nan")
    return float(
        np.mean(
            [
                np.array_equal(
                    sampled_profile[driver_index[driver_id]],
                    true_profile[driver_index[driver_id]],
                )
                for driver_id, _ in assignment
            ]
        )
    )


def run_seed(
    *,
    source_root: Path,
    seed: int,
    rho: float,
    group_size: int,
    n: int,
    m: int,
    k: int,
    strength: float,
    likelihood_mode: str,
    joint_alpha: float = 1.0,
    common_random_numbers: bool = True,
) -> Trace:
    paths = cell_paths(source_root, n, seed)
    snapshots, true_driver_source, passenger_source, _ = load_cell(paths, seed, n)
    driver_ids = sorted(true_driver_source.true_types)
    type_env = CourierDispatchEnv(n_agents=1, rule_count=4, horizon=1, seed=seed)
    legacy_types = {driver_id: true_driver_source.type_for_driver(driver_id) for driver_id in driver_ids}
    true_types = grouped_driver_types(
        driver_ids,
        seed=seed,
        rho=rho,
        group_size=group_size,
        type_space=type_env.type_space,
    )
    if rho == 0.0 and true_types != legacy_types:
        raise AssertionError(f"rho=0 persona mismatch: n={n} seed={seed}")
    true_driver_source.true_types = true_types
    groups = [driver_ids[start:start + group_size] for start in range(0, len(driver_ids), group_size)]
    rounds = [conflict_transform(snapshot, strength) for snapshot in selected_rounds(snapshots, k, m)]
    factored = FactoredTracker(driver_ids, type_env.type_space)
    joint = GroupedJointTracker(driver_ids, type_env.type_space, rho, group_size)
    driver_index = {driver_id: index for index, driver_id in enumerate(driver_ids)}
    true_profile = np.asarray([true_types[driver_id] for driver_id in driver_ids], dtype=int)
    rng_seed = 810_000 + seed + 10_000 * group_size + int(round(1000 * rho))
    harp_rng = np.random.default_rng(rng_seed)
    harp_s_rng = np.random.default_rng(rng_seed)
    joint_rng = np.random.default_rng(rng_seed if rho == 0.0 else rng_seed + 100_000)
    common_rng = np.random.default_rng(rng_seed)
    stats = {arm: UtilityStats() for arm in ARMS}
    cumulative_regret = {arm: 0.0 for arm in ARMS}
    action_rows: dict[str, list[tuple[tuple[int, int], ...]]] = {arm: [] for arm in ARMS}
    sampled_profile_rows: dict[str, list[tuple[tuple[int, ...], ...]]] = {arm: [] for arm in ARMS}
    utility_traces: dict[str, list[float]] = {arm: [] for arm in ARMS}
    regret_traces: dict[str, list[float]] = {arm: [] for arm in ARMS}
    assigned_hit_traces: dict[str, list[float]] = {arm: [] for arm in ARMS}
    marginal_mass_traces: dict[str, list[float]] = {arm: [] for arm in ARMS}
    profile_mass_traces: dict[str, list[float]] = {arm: [] for arm in ARMS}
    joint_weight_pre: list[float] = []
    joint_weight_post: list[float] = []
    joint_support_size_pre: list[int] = []
    joint_positive_ratio_pre: list[float] = []
    observed: set[int] = set()
    tv_values = []
    unelicited_values = []
    request_sequences = {arm: [] for arm in ARMS}
    true_indices = true_type_indices(type_env.type_space, true_profile)

    for round_index, snapshot in enumerate(rounds):
        factored_marginals = factored.marginals()
        joint_marginals = joint.marginals()
        if rho == 0.0 and not np.allclose(joint_marginals, factored_marginals, atol=1e-15, rtol=0.0):
            raise AssertionError(f"rho=0 Joint/HARP posterior mismatch: seed={seed} round={round_index}")
        joint_weight_pre.append(float(joint.shared_weight))
        positive_shared = joint.shared_probs[joint.shared_probs > 0.0]
        joint_support_size_pre.append(int(len(positive_shared)))
        joint_positive_ratio_pre.append(
            float(positive_shared.max() / positive_shared.min()) if len(positive_shared) else 1.0
        )
        current_marginal_mass = {
            "oracle": 1.0,
            "joint": marginal_true_mass(joint_marginals, true_indices),
            "harp": marginal_true_mass(factored_marginals, true_indices),
            "harp_s": marginal_true_mass(factored_marginals, true_indices),
        }
        current_profile_mass = {
            "oracle": 1.0,
            "joint": joint.true_profile_mass(true_profile),
            "harp": factored_profile_mass(factored_marginals, true_indices),
            "harp_s": factored_profile_mass(factored_marginals, true_indices),
        }
        if common_random_numbers:
            uniforms = common_rng.random(len(driver_ids))
            profiles = {
                "joint": joint.sample_profile_from_uniforms(uniforms, alpha=joint_alpha),
                "harp": factored_profile_from_uniforms(factored, uniforms),
                "harp_s": harp_s_profile_from_uniforms(factored, uniforms, driver_ids, groups, rho),
                "oracle": true_profile,
            }
        else:
            profiles = {
                "joint": joint.sample_profile(joint_rng, alpha=joint_alpha),
                "harp": factored.sample_profile(harp_rng),
                "harp_s": harp_s_profile(factored, harp_s_rng, driver_ids, groups, rho),
                "oracle": true_profile,
            }
        if rho == 0.0 and not np.array_equal(profiles["joint"], profiles["harp"]):
            raise AssertionError(f"rho=0 Joint/HARP sampled-profile mismatch: seed={seed} round={round_index}")
        assignments = {
            arm: choose_assignment(snapshot, profiles[arm], driver_index)
            for arm in ARMS
        }
        if rho == 0.0 and assignments["joint"] != assignments["harp"]:
            raise AssertionError(f"rho=0 Joint/HARP assignment mismatch: seed={seed} round={round_index}")
        signature = request_signature(snapshot)
        for arm in ARMS:
            request_sequences[arm].append(signature)
            action_rows[arm].append(assignments[arm])
            sampled_profile_rows[arm].append(
                tuple(tuple(int(value) for value in row) for row in profiles[arm])
            )
            evaluate_assignment(assignments[arm], snapshot, true_driver_source, passenger_source, stats[arm])
            assigned_hit_traces[arm].append(
                assigned_type_hit(assignments[arm], profiles[arm], true_profile, driver_index)
            )
            marginal_mass_traces[arm].append(current_marginal_mass[arm])
            profile_mass_traces[arm].append(current_profile_mass[arm])
        if any(tuple(request_sequences[arm]) != tuple(request_sequences["oracle"]) for arm in ARMS):
            raise AssertionError(f"request sequence mismatch at seed={seed} round={round_index}")

        oracle_total = stats["oracle"].utility
        for arm in ARMS:
            cumulative_regret[arm] = oracle_total - stats[arm].utility
            utility_traces[arm].append(float(stats[arm].utility))
            regret_traces[arm].append(float(cumulative_regret[arm]))

        elicitation = legal_assignments(snapshot)[0]
        offer_by_pair = {(int(offer.driver_id), int(offer.request_id)): offer for offer in snapshot.candidates}
        for driver_id, request_id in elicitation:
            offer = offer_by_pair[(driver_id, request_id)]
            action, _ = synthetic_action_for_type(true_types[driver_id], offer, RULE_CONFIG)
            features = true_driver_source.features_for_offer(offer)
            log_likelihood = observation_log_likelihood(
                type_env, offer, features, action, likelihood_mode
            )
            factored.update(driver_id, log_likelihood)
            joint.update(driver_id, log_likelihood)
            observed.add(driver_id)
        joint_weight_post.append(float(joint.shared_weight))
        tv_values.append(joint.corr_tv())
        unelicited_values.append(1.0 - len(observed) / len(driver_ids))

    if rho == 0.0 and tuple(action_rows["harp"]) != tuple(action_rows["harp_s"]):
        raise AssertionError(f"rho=0 HARP/HARP-S action mismatch: seed={seed}")
    if rho == 0.0 and common_random_numbers:
        if tuple(sampled_profile_rows["joint"]) != tuple(sampled_profile_rows["harp"]):
            raise AssertionError(f"rho=0 Joint/HARP sampled-profile trajectory mismatch: seed={seed}")
        if tuple(action_rows["joint"]) != tuple(action_rows["harp"]):
            raise AssertionError(f"rho=0 Joint/HARP action trajectory mismatch: seed={seed}")
        if tuple(utility_traces["joint"]) != tuple(utility_traces["harp"]):
            raise AssertionError(f"rho=0 Joint/HARP utility trajectory mismatch: seed={seed}")
        if tuple(regret_traces["joint"]) != tuple(regret_traces["harp"]):
            raise AssertionError(f"rho=0 Joint/HARP regret trajectory mismatch: seed={seed}")
    exact_shared_control = (
        rho == 1.0
        and common_random_numbers
        and joint_alpha == 1.0
    )
    if exact_shared_control:
        if tuple(sampled_profile_rows["joint"]) != tuple(sampled_profile_rows["harp_s"]):
            raise AssertionError(f"rho=1 Joint/HARP-S sampled-profile trajectory mismatch: seed={seed}")
        if tuple(action_rows["joint"]) != tuple(action_rows["harp_s"]):
            raise AssertionError(f"rho=1 Joint/HARP-S action trajectory mismatch: seed={seed}")
        if tuple(utility_traces["joint"]) != tuple(utility_traces["harp_s"]):
            raise AssertionError(f"rho=1 Joint/HARP-S utility trajectory mismatch: seed={seed}")
        if tuple(regret_traces["joint"]) != tuple(regret_traces["harp_s"]):
            raise AssertionError(f"rho=1 Joint/HARP-S regret trajectory mismatch: seed={seed}")
    if abs(cumulative_regret["oracle"]) > 1e-12:
        raise AssertionError(f"oracle regret is not zero: {cumulative_regret['oracle']}")
    for arm in ARMS:
        if not regret_traces[arm] or abs(cumulative_regret[arm] - regret_traces[arm][-1]) > 1e-12:
            raise AssertionError(f"{arm} cumulative regret is not sourced from its own regret trace")

    corr_tv = float(np.mean(tv_values))
    unelicited = float(np.mean(unelicited_values))
    realized_corr = realized_rule_correlation(true_types, groups)
    rows = []
    for arm in ARMS:
        rows.append(
            {
                "rho": rho,
                "g": group_size,
                "n": n,
                "m": m,
                "K": k,
                "lambda": strength,
                "seed": seed,
                "arm": arm,
                "cum_regret": cumulative_regret[arm],
                "corr_tv": corr_tv,
                "unelicited_frac": unelicited,
                "realized_rule_corr": realized_corr,
                "n_llm_calls": 0,
                "belief_entries": n * 16 if arm in {"harp", "harp_s"} else joint.belief_bytes // 8,
                "belief_bytes": n * 16 * 8 if arm in {"harp", "harp_s"} else joint.belief_bytes,
                "beta": BETA,
                "joint_prior": "global two-component pi_rho=(1-rho)*pi_independent+rho*pi_group_shared over full 16-type personas",
                "regret_source": f"oracle_utility_trace - {arm}_utility_trace",
            }
        )
    action_mismatches = sum(
        left != right
        for left, right in zip(action_rows["harp"], action_rows["harp_s"])
    )
    regret_trace_equal = tuple(regret_traces["harp"]) == tuple(regret_traces["harp_s"])
    if action_mismatches > 0 and regret_trace_equal:
        # This is legal when different assignments realize the same utility, but it must be explicit.
        for row in rows:
            row["harp_harp_s_action_mismatches"] = action_mismatches
            row["harp_harp_s_equal_regret_trace_despite_action_mismatch"] = True
    else:
        for row in rows:
            row["harp_harp_s_action_mismatches"] = action_mismatches
            row["harp_harp_s_equal_regret_trace_despite_action_mismatch"] = False
    if likelihood_mode == "deterministic-rule" and rho == 1.0:
        masses = list(profile_mass_traces["joint"])
        masses.append(joint.true_profile_mass(true_profile))
        decreases = [
            right - left
            for left, right in zip(masses, masses[1:])
            if right < left - 1e-15
        ]
        if decreases:
            raise AssertionError(
                f"deterministic Joint true-profile mass decreased: seed={seed}, "
                f"count={len(decreases)}, largest={min(decreases)}"
            )
        for row in rows:
            row["joint_true_profile_monotonic"] = True
    else:
        for row in rows:
            row["joint_true_profile_monotonic"] = None
    for row in rows:
        row["likelihood_mode"] = likelihood_mode
        row["joint_alpha"] = joint_alpha
        row["common_random_numbers"] = common_random_numbers
    return Trace(
        rows=rows,
        actions={arm: tuple(action_rows[arm]) for arm in ARMS},
        sampled_profile_traces={arm: tuple(values) for arm, values in sampled_profile_rows.items()},
        utility_traces={arm: tuple(values) for arm, values in utility_traces.items()},
        regret_traces={arm: tuple(values) for arm, values in regret_traces.items()},
        assigned_type_hit_traces={arm: tuple(values) for arm, values in assigned_hit_traces.items()},
        marginal_true_mass_traces={arm: tuple(values) for arm, values in marginal_mass_traces.items()},
        true_profile_mass_traces={arm: tuple(values) for arm, values in profile_mass_traces.items()},
        joint_shared_weight_pre=tuple(joint_weight_pre),
        joint_shared_weight_post=tuple(joint_weight_post),
        joint_shared_support_size_pre=tuple(joint_support_size_pre),
        joint_shared_positive_ratio_pre=tuple(joint_positive_ratio_pre),
        request_sequence=tuple(request_sequences["oracle"]),
        final_factored_marginals=factored.marginals(),
        final_joint_marginals=joint.marginals(),
    )


def decision_relevance(
    source_root: Path,
    *,
    n: int,
    m: int,
    k: int,
    seeds: int,
    threshold: float,
    group_size: int,
    strength: float,
) -> dict[str, object]:
    per_round = []
    for seed in range(seeds):
        snapshots, true_driver_source, _, _ = load_cell(cell_paths(source_root, n, seed), seed, n)
        driver_ids = sorted(true_driver_source.true_types)
        driver_index = {driver_id: index for index, driver_id in enumerate(driver_ids)}
        groups = [driver_ids[start:start + group_size] for start in range(0, len(driver_ids), group_size)]
        group_count = len(groups)
        for round_index, base_snapshot in enumerate(selected_rounds(snapshots, k, m)):
            snapshot = conflict_transform(base_snapshot, strength)
            counts: dict[tuple[tuple[int, int], ...], int] = {}
            profile_count = len(true_driver_source.env.type_space) ** group_count
            for encoded in range(profile_count):
                group_types = np.asarray(
                    np.unravel_index(encoded, (len(true_driver_source.env.type_space),) * group_count),
                    dtype=int,
                )
                profile = np.empty((n, 4), dtype=int)
                for group_index, group in enumerate(groups):
                    for driver_id in group:
                        profile[driver_index[driver_id]] = true_driver_source.env.type_space[group_types[group_index]]
                assignment = choose_assignment(snapshot, profile, driver_index)
                counts[assignment] = counts.get(assignment, 0) + 1
            modal = max(counts.values())
            per_round.append(
                {
                    "seed": seed,
                    "round": round_index,
                    "distinct_oracle_assignments": len(counts),
                    "profile_change_fraction": 1.0 - modal / float(profile_count),
                }
            )
    mean_change = float(np.mean([row["profile_change_fraction"] for row in per_round]))
    sensitive_fraction = float(np.mean([row["distinct_oracle_assignments"] > 1 for row in per_round]))
    result = {
        "definition": "enumerate all 16^(n/g) group-shared full-persona profiles; compare oracle assignments to the modal assignment",
        "lambda": strength,
        "group_size": group_size,
        "profile_count_per_round": 16 ** math.ceil(n / group_size),
        "threshold": threshold,
        "mean_profile_change_fraction": mean_change,
        "sensitive_round_fraction": sensitive_fraction,
        "rounds": len(per_round),
        "passed": mean_change >= threshold,
        "per_round": per_round,
    }
    return result


def hard_gates(
    source_root: Path,
    *,
    decision_threshold: float = 0.10,
    likelihood_mode: str = "softmax",
) -> dict[str, object]:
    gate_rows = []
    for n in (2, 3, 4):
        trace = run_seed(source_root=source_root, seed=0, rho=0.0, group_size=2, n=n, m=1, k=5, strength=0.0, likelihood_mode=likelihood_mode)
        tv = float(np.max(0.5 * np.abs(trace.final_factored_marginals - trace.final_joint_marginals).sum(axis=1)))
        if tv > 1e-12:
            raise AssertionError(f"rho=0 parity gate failed: n={n} TV={tv}")
        gate_rows.append({"n": n, "max_marginal_tv": tv})
    first = run_seed(source_root=source_root, seed=0, rho=1.0, group_size=4, n=8, m=2, k=20, strength=0.0, likelihood_mode=likelihood_mode)
    second = run_seed(source_root=source_root, seed=0, rho=1.0, group_size=4, n=8, m=2, k=20, strength=0.0, likelihood_mode=likelihood_mode)
    if first.rows != second.rows or first.actions != second.actions or first.request_sequence != second.request_sequence:
        raise AssertionError("determinism gate failed for repeated E-H cell")
    type_space = CourierDispatchEnv(n_agents=1, rule_count=4, horizon=1, seed=0).type_space
    rho0_tracker = GroupedJointTracker(list(range(8)), type_space, rho=0.0, group_size=4)
    rho1_tracker = GroupedJointTracker(list(range(8)), type_space, rho=1.0, group_size=4)
    if rho0_tracker.shared_weight != 0.0 or not np.allclose(rho0_tracker.independent_probs, 1.0 / 16.0, atol=1e-15):
        raise AssertionError("Joint rho=0 prior is not the independent full-persona prior")
    if rho1_tracker.shared_weight != 1.0 or len(rho1_tracker.shared_probs) != 16 ** 2 or not np.allclose(rho1_tracker.shared_probs, 1.0 / (16 ** 2), atol=1e-15):
        raise AssertionError("Joint rho=1 prior is not the 16^(n/g) group-shared full-persona prior")
    native_relevance = decision_relevance(
        source_root, n=8, m=2, k=20, seeds=20, threshold=decision_threshold,
        group_size=4, strength=0.0,
    )
    conflict_relevance = None
    if not bool(native_relevance["passed"]):
        conflict_relevance = decision_relevance(
            source_root, n=8, m=2, k=20, seeds=20, threshold=decision_threshold,
            group_size=4, strength=1.0,
        )
    selected_relevance = native_relevance if native_relevance["passed"] else conflict_relevance
    selected_lambda = float(selected_relevance["lambda"]) if selected_relevance and selected_relevance["passed"] else None
    return {
        "rho0_parity": gate_rows,
        "repeat_determinism": True,
        "oracle_regret_zero": True,
        "decision_relevance": {
            "native_lambda0": native_relevance,
            "conflict_lambda1": conflict_relevance,
            "selected_lambda": selected_lambda,
            "passed": selected_lambda is not None,
        },
        "joint_prior_verified": {
            "formula": "global pi_rho=(1-rho)*pi_independent+rho*pi_group_shared over full personas",
            "rho0_independent_full_persona_prior": True,
            "rho1_shared_state_count": 16 ** 2,
        },
        "arm_regret_write_paths_verified": True,
        "likelihood_mode": likelihood_mode,
    }


def write_failed_gate_report(out: Path, gates: dict[str, object]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    relevance = gates["decision_relevance"]
    final_attempt = relevance["conflict_lambda1"] or relevance["native_lambda0"]
    payload = {
        "experiment": "E-H MaaSSim grouped coupling prior",
        "status": "halted_before_repaired_minimal_rerun",
        "reason": "decision relevance gate failed",
        "decision_relevance": relevance,
        "gates": gates,
        "action": "No repaired minimal cell or wider grid was run.",
        "superseded_outputs": "The earlier minimal outputs in this directory predate the corrected HARP-S log-odds mechanism and must not be used as results.",
    }
    path = out / "e_h_repair_gate_failure.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    marker = out / "INVALIDATED_PRE_REPAIR_MINIMAL_RESULTS.md"
    marker.write_text(
        "# Invalidated E-H pre-repair minimal results\n\n"
        "The existing minimal CSV/NPZ/figure in this directory were produced before the corrected "
        "HARP-S group log-odds mechanism and must not be used as experimental results.\n\n"
        f"The repaired pre-run decision-relevance gate failed: mean profile-change fraction "
        f"{float(final_attempt['mean_profile_change_fraction']):.4f} < threshold {float(final_attempt['threshold']):.4f}. "
        "No repaired minimal cell or broader grid was run.\n",
        encoding="utf-8",
    )


def slug(value: float) -> str:
    return str(value).replace(".", "p")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_existing_behavior(out: Path, rho: float, group_size: int, n: int, m: int, seeds: int) -> dict[str, list[str]] | None:
    path = out / f"e_h_rho{slug(rho)}_g{group_size}_n{n}_m{m}_s{seeds}.npz"
    if not path.is_file():
        return None
    payload = np.load(path, allow_pickle=False)
    required = ("action_traces", "request_sequences", "utility_traces", "regret_traces")
    if not all(name in payload for name in required):
        return None
    return {name: [str(value) for value in payload[name].tolist()] for name in required}


def assert_behavior_unchanged(existing: dict[str, list[str]] | None, traces: list[Trace], *, rho: float) -> None:
    if existing is None:
        return
    current = {
        "action_traces": [json.dumps(trace.actions) for trace in traces],
        "request_sequences": [json.dumps(trace.request_sequence) for trace in traces],
        "utility_traces": [json.dumps(trace.utility_traces) for trace in traces],
        "regret_traces": [json.dumps(trace.regret_traces) for trace in traces],
    }
    for name, expected in existing.items():
        if current[name] != expected:
            raise AssertionError(f"diagnostics-only rerun changed {name} at rho={rho}")


def t_critical_95(sample_count: int) -> float:
    critical_values = {19: 2.093024054, 39: 2.02269092}
    degrees_of_freedom = sample_count - 1
    if degrees_of_freedom not in critical_values:
        raise ValueError(f"no preregistered 95% t critical value for n={sample_count}")
    return critical_values[degrees_of_freedom]


def paired_summary(rows: list[dict[str, object]], rho: float, arm: str) -> dict[str, object]:
    cell = [row for row in rows if float(row["rho"]) == rho]
    joint = {int(row["seed"]): float(row["cum_regret"]) for row in cell if row["arm"] == "joint"}
    target = {int(row["seed"]): float(row["cum_regret"]) for row in cell if row["arm"] == arm}
    seeds = sorted(set(joint) & set(target))
    values = np.asarray([target[seed] - joint[seed] for seed in seeds], dtype=float)
    standard_error = float(values.std(ddof=1) / math.sqrt(len(values)))
    half_width = t_critical_95(len(values)) * standard_error
    mean_value = float(values.mean())
    return {
        "arm": arm,
        "rho": rho,
        "seeds": len(seeds),
        "mean": mean_value,
        "sem": standard_error,
        "ci95_low": mean_value - half_width,
        "ci95_high": mean_value + half_width,
        "ci95_covers_zero": mean_value - half_width <= 0.0 <= mean_value + half_width,
    }


def paired_arm_difference(
    rows: list[dict[str, object]], rho: float, left_arm: str, right_arm: str
) -> dict[str, object]:
    cell = [row for row in rows if float(row["rho"]) == rho]
    left = {int(row["seed"]): float(row["cum_regret"]) for row in cell if row["arm"] == left_arm}
    right = {int(row["seed"]): float(row["cum_regret"]) for row in cell if row["arm"] == right_arm}
    seeds = sorted(set(left) & set(right))
    values = np.asarray([left[seed] - right[seed] for seed in seeds], dtype=float)
    standard_error = float(values.std(ddof=1) / math.sqrt(len(values)))
    half_width = t_critical_95(len(values)) * standard_error
    mean_value = float(values.mean())
    return {
        "left_arm": left_arm,
        "right_arm": right_arm,
        "rho": rho,
        "seeds": len(seeds),
        "mean": mean_value,
        "sem": standard_error,
        "ci95_low": mean_value - half_width,
        "ci95_high": mean_value + half_width,
        "ci95_covers_zero": mean_value - half_width <= 0.0 <= mean_value + half_width,
    }


def evaluate_minimal(rows: list[dict[str, object]], traces: dict[tuple[float, int, int, int], list[Trace]]) -> dict[str, object]:
    summaries = {
        f"rho{rho:g}_{arm}": paired_summary(rows, rho, arm)
        for rho in (0.0, 1.0)
        for arm in ("harp", "harp_s")
    }
    diagnostics = {}
    for rho in (0.0, 1.0):
        cell = [row for row in rows if float(row["rho"]) == rho]
        diagnostics[f"rho{rho:g}"] = {
            "corr_tv_mean": float(np.mean([float(row["corr_tv"]) for row in cell])),
            "unelicited_frac_mean": float(np.mean([float(row["unelicited_frac"]) for row in cell])),
            "realized_rule_corr_mean": float(np.mean([float(row["realized_rule_corr"]) for row in cell])),
            "oracle_max_abs_regret": max(abs(float(row["cum_regret"])) for row in cell if row["arm"] == "oracle"),
        }
    rho0_traces = traces[(0.0, 4, 8, 2)]
    rho1_traces = traces[(1.0, 4, 8, 2)]
    seed_count = len(rho1_traces)
    prior_true_mass = 1.0 / 16.0
    belief_threshold = 2.0 * prior_true_mass
    final_marginal_mass = {}
    for arm in ("joint", "harp", "harp_s"):
        values = np.asarray(
            [trace.marginal_true_mass_traces[arm][-1] for trace in rho1_traces],
            dtype=float,
        )
        final_marginal_mass[arm] = {
            "mean": float(values.mean()),
            "sem": float(values.std(ddof=1) / math.sqrt(len(values))),
            "ratio_to_uniform_prior": float(values.mean() / prior_true_mass),
        }
    belief_gate_passed = any(
        item["mean"] >= belief_threshold for item in final_marginal_mass.values()
    )
    belief_movement_gate = {
        "definition": f"rho=1 final-round pre-decision mean marginal probability assigned to each driver's true full persona, averaged over n=8 drivers and {seed_count} seeds",
        "uniform_prior": prior_true_mass,
        "threshold": belief_threshold,
        "threshold_multiple": 2.0,
        "arms": final_marginal_mass,
        "passed": belief_gate_passed,
    }
    rho0_mismatches = sum(
        left != right
        for trace in rho0_traces
        for left, right in zip(trace.actions["harp"], trace.actions["harp_s"])
    )
    rho1_mismatches = sum(
        left != right
        for trace in rho1_traces
        for left, right in zip(trace.actions["harp"], trace.actions["harp_s"])
    )
    p1 = bool(summaries["rho0_harp"]["ci95_covers_zero"] and rho0_mismatches == 0)
    p4 = bool(summaries["rho1_harp_s"]["ci95_covers_zero"] and float(summaries["rho1_harp_s"]["mean"]) < float(summaries["rho1_harp"]["mean"]))
    rho1_harp_positive = float(summaries["rho1_harp"]["ci95_low"]) > 0.0
    direct_harp_s = paired_arm_difference(rows, 1.0, "harp_s", "harp")
    if not belief_gate_passed:
        stop_reason = (
            "The K=20 belief-movement gate failed: no non-oracle arm reached twice the uniform-prior "
            "true-persona marginal mass. Regret values are retained but marked non-comparable."
        )
    elif not rho1_harp_positive:
        stop_reason = (
            "The full-persona decision-relevance gate passed and posterior correlation reached its maximum, "
            "but Joint showed no measurable oracle-regret advantage over HARP. This is the preregistered "
            "positive null result; the wider parameter grid was halted without tuning."
        )
    elif not p4:
        stop_reason = "Joint advantage appeared, but HARP-S did not recover parity; the wider grid was halted without tuning."
    else:
        stop_reason = None
    return {
        "paired_gaps": summaries,
        "direct_harp_s_minus_harp": direct_harp_s,
        "belief_movement_gate": belief_movement_gate,
        "diagnostics": diagnostics,
        "action_mismatches": {"rho0_harp_vs_harp_s": rho0_mismatches, "rho1_harp_vs_harp_s": rho1_mismatches},
        "prediction_status": {
            "P1": p1,
            "P2": "not supported by rho={0,1} endpoints; rho=0.5 not run after minimal stop",
            "P3": "not tested after minimal stop",
            "P4": p4,
        },
        "rho1_harp_significantly_positive": rho1_harp_positive,
        "regret_comparable": belief_gate_passed,
        "continue_full_grid": bool(belief_gate_passed and rho1_harp_positive and p4),
        "stop_reason": stop_reason,
    }


def write_outputs(out: Path, traces: dict[tuple[float, int, int, int], list[Trace]], gates: dict[str, object]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for stale in ("e_h_repair_gate_failure.json", "INVALIDATED_PRE_REPAIR_MINIMAL_RESULTS.md"):
        path = out / stale
        if path.exists():
            path.unlink()
    long_rows = [row for values in traces.values() for trace in values for row in trace.rows]
    csv_path = out / "e_h_maassim_grouped_prior.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(long_rows[0].keys()))
        writer.writeheader()
        writer.writerows(long_rows)
    minimal_evaluation = evaluate_minimal(long_rows, traces)
    likelihood_mode = str(long_rows[0]["likelihood_mode"])
    seed_indices = sorted({int(row["seed"]) for row in long_rows})

    artifacts = []
    for (rho, group_size, n, m), values in sorted(traces.items()):
        rows = [row for trace in values for row in trace.rows]
        path = out / f"e_h_rho{slug(rho)}_g{group_size}_n{n}_m{m}_s{len(values)}.npz"
        np.savez_compressed(
            path,
            rho=np.asarray(rho),
            g=np.asarray(group_size),
            n=np.asarray(n),
            m=np.asarray(m),
            K=np.asarray(int(rows[0]["K"])),
            strength=np.asarray(float(rows[0]["lambda"])),
            seeds=np.asarray([int(row["seed"]) for row in rows]),
            arms=np.asarray([str(row["arm"]) for row in rows]),
            cum_regret=np.asarray([float(row["cum_regret"]) for row in rows]),
            corr_tv=np.asarray([float(row["corr_tv"]) for row in rows]),
            unelicited_frac=np.asarray([float(row["unelicited_frac"]) for row in rows]),
            n_llm_calls=np.asarray([int(row["n_llm_calls"]) for row in rows]),
            request_sequences=np.asarray([json.dumps(trace.request_sequence) for trace in values]),
            action_traces=np.asarray([json.dumps(trace.actions) for trace in values]),
            utility_traces=np.asarray([json.dumps(trace.utility_traces) for trace in values]),
            regret_traces=np.asarray([json.dumps(trace.regret_traces) for trace in values]),
            assigned_type_hit_traces=np.asarray([json.dumps(trace.assigned_type_hit_traces) for trace in values]),
            marginal_true_mass_traces=np.asarray([json.dumps(trace.marginal_true_mass_traces) for trace in values]),
            true_profile_mass_traces=np.asarray([json.dumps(trace.true_profile_mass_traces) for trace in values]),
            joint_shared_weight_pre=np.asarray([json.dumps(trace.joint_shared_weight_pre) for trace in values]),
            joint_shared_weight_post=np.asarray([json.dumps(trace.joint_shared_weight_post) for trace in values]),
        )
        artifacts.append({"path": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)})

    metadata = {
        "experiment": "E-H MaaSSim grouped coupling prior",
        "status": (
            "minimal_complete_belief_gate_failed"
            if not minimal_evaluation["belief_movement_gate"]["passed"]
            else (
                "minimal_complete_positive_null"
                if not minimal_evaluation["rho1_harp_significantly_positive"]
                else "minimal_complete"
            )
        ),
        "backbone": "gpt-5.4-mini-20260317 (pinned but unused; deterministic rule replay)",
        "n_llm_calls": 0,
        "m_definition": "maximum requests/elicited drivers per replay round",
        "beta": BETA,
        "preregistered_predictions": PREREGISTERED_PREDICTIONS,
        "likelihood_mode": likelihood_mode,
        "likelihood": (
            "correctly specified 0/1 indicator from synthetic_action_for_type"
            if likelihood_mode == "deterministic-rule"
            else "CourierDispatchEnv softmax behavioral likelihood"
        ),
        "queue_snapshots": "unchanged E-E saved MaaSSim snapshots",
        "seed_indices": seed_indices,
        "seed_start": seed_indices[0],
        "seed_end": seed_indices[-1],
        "seed_count": len(seed_indices),
        "joint_prior": "global pi_rho=(1-rho)*pi_independent+rho*pi_group_shared over full 16-type personas; exact two-component evidence updates",
        "harp_s_sampling": "weighted group categorical log probabilities: log(mu_i)+rho*sum_{j!=i}log(mu_j); rho=1 samples one shared full persona per group",
        "gates": gates,
        "minimal_evaluation": minimal_evaluation,
        "artifacts": artifacts,
    }
    metadata_path = out / "e_h_maassim_grouped_prior_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": "1.0",
        "artifacts": [
            {"path": csv_path.name, "bytes": csv_path.stat().st_size, "sha256": sha256(csv_path)},
            {"path": metadata_path.name, "bytes": metadata_path.stat().st_size, "sha256": sha256(metadata_path)},
            *artifacts,
        ],
    }
    (out / "e_h_maassim_grouped_prior_sha256.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    report = [
        "# E-H MaaSSim Grouped Coupling Prior — Minimal Unit",
        "",
        f"The preregistered minimal unit is rho in {{0,1}}, g=4, n=8, m=2, K={int(long_rows[0]['K'])}, seeds {seed_indices[0]}--{seed_indices[-1]} (n={len(seed_indices)}).",
        "Driver decisions are deterministic hidden rules; provider/LLM calls are zero.",
        f"Likelihood mode: {likelihood_mode}.",
        "",
        "| rho | arm - Joint | mean | SEM | 95% CI | covers zero |",
        "|---:|---|---:|---:|---:|:---:|",
    ]
    for rho in (0.0, 1.0):
        for arm in ("harp", "harp_s"):
            item = minimal_evaluation["paired_gaps"][f"rho{rho:g}_{arm}"]
            report.append(
                f"| {rho:g} | {arm} | {item['mean']:+.3f} | {item['sem']:.3f} | "
                f"[{item['ci95_low']:+.3f}, {item['ci95_high']:+.3f}] | {item['ci95_covers_zero']} |"
            )
    report.extend(
        [
            "",
            f"Mean corr TV: rho=0 {minimal_evaluation['diagnostics']['rho0']['corr_tv_mean']:.3e}; rho=1 {minimal_evaluation['diagnostics']['rho1']['corr_tv_mean']:.3f}.",
            f"Mean unelicited fraction: rho=0 {minimal_evaluation['diagnostics']['rho0']['unelicited_frac_mean']:.3f}; rho=1 {minimal_evaluation['diagnostics']['rho1']['unelicited_frac_mean']:.3f}.",
            f"Belief movement gate: {minimal_evaluation['belief_movement_gate']}.",
            f"Prediction status: {minimal_evaluation['prediction_status']}.",
            f"Direct HARP-S minus HARP at rho=1: {minimal_evaluation['direct_harp_s_minus_harp']['mean']:+.3f} +/- {minimal_evaluation['direct_harp_s_minus_harp']['sem']:.3f}, 95% CI [{minimal_evaluation['direct_harp_s_minus_harp']['ci95_low']:+.3f}, {minimal_evaluation['direct_harp_s_minus_harp']['ci95_high']:+.3f}].",
            f"Decision: {minimal_evaluation['stop_reason']}",
        ]
    )
    report_path = out / "e_h_maassim_grouped_prior_minimal.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest["artifacts"].append({"path": report_path.name, "bytes": report_path.stat().st_size, "sha256": sha256(report_path)})
    (out / "e_h_maassim_grouped_prior_sha256.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def parse_floats(raw: str) -> list[float]:
    return [float(value) for value in raw.split(",") if value.strip()]


def parse_ints(raw: str) -> list[int]:
    return [int(value) for value in raw.split(",") if value.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("gates", "minimal", "grid"), default="minimal")
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--rhos", default="0,1")
    parser.add_argument("--group-sizes", default="4")
    parser.add_argument("--n", type=int, default=8)
    parser.add_argument("--m-values", default="2")
    parser.add_argument("--K", type=int, default=20)
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--decision-relevance-threshold", type=float, default=0.10)
    parser.add_argument("--likelihood-mode", choices=("softmax", "deterministic-rule"), default="softmax")
    args = parser.parse_args()
    if args.seed_start < 0:
        raise ValueError("seed start must be nonnegative")
    source_root = args.source_root.resolve()
    out = args.out.resolve()
    gates = hard_gates(
        source_root,
        decision_threshold=args.decision_relevance_threshold,
        likelihood_mode=args.likelihood_mode,
    )
    if not bool(gates["decision_relevance"]["passed"]):
        write_failed_gate_report(out, gates)
        print(json.dumps({"status": "halted", "reason": "decision relevance gate failed", "gates": gates}, indent=2))
        raise SystemExit(2)
    if args.stage == "gates":
        print(json.dumps({"status": "gates_ok", **gates}, indent=2))
        return
    rhos = parse_floats(args.rhos)
    groups = parse_ints(args.group_sizes)
    m_values = parse_ints(args.m_values)
    if args.stage == "minimal" and (
        rhos != [0.0, 1.0]
        or groups not in ([4], [2, 4])
        or m_values != [2]
        or args.K != 20
    ):
        raise ValueError("minimal stage is fixed to rho={0,1}, g in {4,2,4}, m=2, K=20")
    traces: dict[tuple[float, int, int, int], list[Trace]] = {}
    existing_behavior: dict[tuple[float, int, int, int], dict[str, list[str]] | None] = {}
    selected_strength = float(gates["decision_relevance"]["selected_lambda"])
    for rho in rhos:
        for group_size in groups:
            for m in m_values:
                key = (rho, group_size, args.n, m)
                existing_behavior[key] = load_existing_behavior(
                    out, rho, group_size, args.n, m, args.seeds
                )
                traces[key] = []
                for seed in range(args.seed_start, args.seed_start + args.seeds):
                    print(f"E-H rho={rho:g} g={group_size} n={args.n} m={m} seed={seed}", flush=True)
                    traces[key].append(
                        run_seed(
                            source_root=source_root,
                            seed=seed,
                            rho=rho,
                            group_size=group_size,
                            n=args.n,
                            m=m,
                            k=args.K,
                            strength=selected_strength,
                            likelihood_mode=args.likelihood_mode,
                        )
                    )
                assert_behavior_unchanged(existing_behavior[key], traces[key], rho=rho)
    write_outputs(out, traces, gates)
    print(json.dumps({"status": "minimal_complete", "cells": len(traces), "seed_start": args.seed_start, "seeds": args.seeds, "rows": sum(len(trace.rows) for values in traces.values() for trace in values)}, indent=2))


if __name__ == "__main__":
    main()