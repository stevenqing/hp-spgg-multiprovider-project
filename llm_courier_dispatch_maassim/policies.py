"""Shadow dispatch policies for MaaSSim integration experiments."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations, permutations
from typing import Any

import numpy as np

from llm_courier_dispatch.dispatch_env import CourierDispatchEnv, RulePosterior, state_from_dict
from llm_courier_dispatch.matching_dispatch import (
    assignment_disagreement_bonus,
    expected_assignment_under_factored_posteriors,
    pact_plus_exploration_scale,
)
from llm_courier_dispatch_maassim.adapter import MaaSSimQueueSnapshot, offer_to_rule_features
from llm_courier_dispatch_maassim.hidden_rules import posterior_accept_probability, synthetic_action_for_type


@dataclass
class MaaSSimNearestPolicy:
    """Greedy nearest-driver baseline using MaaSSim candidate wait times."""

    last_diagnostics: dict[str, object] = field(default_factory=dict)

    def choose_assignment(self, snapshot: MaaSSimQueueSnapshot) -> dict[int, int]:
        assignment: dict[int, int] = {}
        used_drivers: set[int] = set()
        used_requests: set[int] = set()
        for offer in sorted(snapshot.candidates, key=lambda item: (item.wait_time, item.driver_id, item.request_id)):
            if offer.driver_id in used_drivers or offer.request_id in used_requests:
                continue
            assignment[offer.driver_id] = offer.request_id
            used_drivers.add(offer.driver_id)
            used_requests.add(offer.request_id)
        self.last_diagnostics = {
            "assignment": assignment,
            "evaluated_assignments": len(snapshot.candidates),
            "candidate_count": len(snapshot.candidates),
            "objective": 0.0,
            "policy": "nearest",
        }
        return assignment


@dataclass
class MaaSSimRandomPolicy:
    """Uniform random legal assignment baseline."""

    rng_seed: int = 0
    call_count: int = 0
    last_diagnostics: dict[str, object] = field(default_factory=dict)

    def choose_assignment(self, snapshot: MaaSSimQueueSnapshot) -> dict[int, int]:
        rng = np.random.default_rng(self.rng_seed + self.call_count)
        self.call_count += 1
        offers = list(snapshot.candidates)
        if not offers:
            self.last_diagnostics = {"assignment": {}, "evaluated_assignments": 0, "candidate_count": 0, "objective": 0.0, "policy": "random"}
            return {}
        order = rng.permutation(len(offers))
        assignment: dict[int, int] = {}
        used_drivers: set[int] = set()
        used_requests: set[int] = set()
        for index in order:
            offer = offers[int(index)]
            if offer.driver_id in used_drivers or offer.request_id in used_requests:
                continue
            assignment[offer.driver_id] = offer.request_id
            used_drivers.add(offer.driver_id)
            used_requests.add(offer.request_id)
        self.last_diagnostics = {
            "assignment": assignment,
            "evaluated_assignments": len(offers),
            "candidate_count": len(offers),
            "objective": 0.0,
            "policy": "random",
        }
        return assignment


@dataclass
class MaaSSimKpiPolicy:
    """KPI-oriented policy using accept probability, fare, and pickup wait."""

    posterior_source: Any | None = None
    oracle: bool = False
    wait_weight: float = 0.01
    travel_weight: float = 0.0
    fare_weight: float = 1.0
    reject_penalty: float = 2.0
    last_diagnostics: dict[str, object] = field(default_factory=dict)

    def choose_assignment(self, snapshot: MaaSSimQueueSnapshot) -> dict[int, int]:
        offers = list(snapshot.candidates)
        if not offers:
            self.last_diagnostics = {"assignment": {}, "objective": 0.0, "evaluated_assignments": 0, "candidate_count": 0, "policy": "kpi"}
            return {}
        drivers = sorted({offer.driver_id for offer in offers})
        requests = sorted({offer.request_id for offer in offers})
        offer_by_pair = {(offer.driver_id, offer.request_id): offer for offer in offers}
        match_count = min(len(drivers), len(requests))
        best_assignment: dict[int, int] = {}
        best_score = float("-inf")
        evaluated = 0
        for driver_subset in combinations(range(len(drivers)), match_count):
            for request_perm in permutations(requests, match_count):
                if any((drivers[driver_idx], request_id) not in offer_by_pair for driver_idx, request_id in zip(driver_subset, request_perm, strict=True)):
                    continue
                score = 0.0
                for driver_idx, request_id in zip(driver_subset, request_perm, strict=True):
                    offer = offer_by_pair[(drivers[driver_idx], request_id)]
                    accept_prob = self._accept_probability(offer)
                    score += (
                        self.fare_weight * float(offer.fare) * accept_prob
                        - self.wait_weight * float(offer.wait_time)
                        - self.travel_weight * float(offer.travel_time)
                        - self.reject_penalty * (1.0 - accept_prob)
                    )
                evaluated += 1
                if score > best_score:
                    best_score = score
                    best_assignment = {drivers[driver_idx]: request_id for driver_idx, request_id in zip(driver_subset, request_perm, strict=True)}
        self.last_diagnostics = {
            "assignment": best_assignment,
            "objective": best_score if evaluated else 0.0,
            "evaluated_assignments": evaluated,
            "candidate_count": len(offers),
            "policy": "oracle_kpi" if self.oracle else "pact_kpi",
        }
        return best_assignment

    def _accept_probability(self, offer) -> float:
        if self.posterior_source is None or not hasattr(self.posterior_source, "config"):
            return 1.0
        if self.oracle and hasattr(self.posterior_source, "type_for_driver"):
            action, _ = synthetic_action_for_type(self.posterior_source.type_for_driver(int(offer.driver_id)), offer, self.posterior_source.config)
            return 1.0 if action == 0 else 0.0
        if hasattr(self.posterior_source, "posterior_for_driver"):
            return posterior_accept_probability(self.posterior_source.posterior_for_driver(int(offer.driver_id)), offer, self.posterior_source.config)
        return 1.0


@dataclass
class MaaSSimPactShadowPolicy:
    """PACT+ assignment scorer for MaaSSim queue snapshots.

    This policy is intentionally shadow-only. It uses a uniform factored
    posterior because the first smoke does not yet inject hidden driver rules or
    update beliefs from MaaSSim driver events.
    """

    beta: float = 0.25
    rule_count: int = 4
    rng_seed: int = 0
    max_exact_profiles: int = 10000
    posterior_source: Any | None = None
    last_diagnostics: dict[str, object] = field(default_factory=dict)

    def choose_assignment(self, snapshot: MaaSSimQueueSnapshot) -> dict[int, int]:
        offer_by_pair = {(offer.driver_id, offer.request_id): offer for offer in snapshot.candidates}
        drivers = [driver_id for driver_id in snapshot.vehicle_queue if any(offer.driver_id == driver_id for offer in snapshot.candidates)]
        requests = [request_id for request_id in snapshot.request_queue if any(offer.request_id == request_id for offer in snapshot.candidates)]
        if not drivers or not requests or not offer_by_pair:
            self.last_diagnostics = {"assignment": {}, "objective": 0.0, "reason": "empty_queue"}
            return {}

        match_count = min(len(drivers), len(requests))
        rng = np.random.default_rng(self.rng_seed)

        best_assignment: dict[int, int] = {}
        best_value = float("-inf")
        best_reward = 0.0
        best_bonus = 0.0
        evaluated = 0

        for driver_subset in combinations(range(len(drivers)), match_count):
            env = CourierDispatchEnv(n_agents=match_count, rule_count=self.rule_count, horizon=1, seed=self.rng_seed)
            selected_drivers = [drivers[driver_idx] for driver_idx in driver_subset]
            posteriors = [self._posterior_for_driver(env, driver_id) for driver_id in selected_drivers]
            scale = pact_plus_exploration_scale(posteriors, round_index=0, horizon=1)
            for request_perm in permutations(requests, match_count):
                if any((drivers[driver_idx], request_id) not in offer_by_pair for driver_idx, request_id in zip(driver_subset, request_perm, strict=True)):
                    continue
                pair_offers = [offer_by_pair[(drivers[driver_idx], request_id)] for driver_idx, request_id in zip(driver_subset, request_perm, strict=True)]
                orders = [state_from_dict(self._features_for_offer(offer)) for offer in pair_offers]
                assignment_tuple = tuple(range(match_count))
                reward = expected_assignment_under_factored_posteriors(
                    env,
                    orders,
                    assignment_tuple,
                    posteriors,
                    rng,
                    samples=4,
                    max_exact_profiles=self.max_exact_profiles,
                )
                bonus = scale * assignment_disagreement_bonus(env, orders, assignment_tuple, posteriors)
                objective = reward + self.beta * bonus
                evaluated += 1
                if objective > best_value:
                    best_value = objective
                    best_reward = reward
                    best_bonus = bonus
                    best_assignment = {drivers[driver_idx]: request_id for driver_idx, request_id in zip(driver_subset, request_perm, strict=True)}

        self.last_diagnostics = {
            "assignment": best_assignment,
            "objective": best_value if evaluated else 0.0,
            "expected_reward": best_reward,
            "bonus": best_bonus,
            "evaluated_assignments": evaluated,
            "match_count": match_count,
            "candidate_count": len(snapshot.candidates),
        }
        return best_assignment

    def _posterior_for_driver(self, env: CourierDispatchEnv, driver_id: int) -> RulePosterior:
        if self.posterior_source is not None and hasattr(self.posterior_source, "posterior_for_driver"):
            return self.posterior_source.posterior_for_driver(int(driver_id))
        return RulePosterior(env.type_space)

    def _features_for_offer(self, offer) -> dict[str, float | int]:
        if self.posterior_source is not None and hasattr(self.posterior_source, "features_for_offer"):
            return self.posterior_source.features_for_offer(offer)
        return offer_to_rule_features(offer)
