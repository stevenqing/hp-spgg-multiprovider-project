"""Synthetic hidden driver rules for MaaSSim shadow experiments."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from llm_courier_dispatch.dispatch_env import ACCEPT, DECLINE_B, DECLINE_C, DECLINE_D, REPOSITION, CourierDispatchEnv, RulePosterior, state_from_dict
from llm_courier_dispatch_maassim.adapter import MaaSSimCandidateOffer, MaaSSimFeatureConfig, offer_to_rule_features


DEFAULT_DRIVER_TYPES = {
    1: (1, 0, 0, 1),
    2: (0, 1, 1, 0),
    3: (1, 1, 0, 0),
    4: (0, 0, 1, 1),
    5: (1, 0, 1, 0),
}


@dataclass(frozen=True)
class SyntheticRuleConfig:
    long_trip_seconds: float = 180.0
    far_pickup_seconds: float = 90.0
    surge_fare_per_second: float = 0.008
    home_after_seconds: float = 1800.0


def offer_from_maassim(veh: Any, offer: dict[str, Any]) -> MaaSSimCandidateOffer:
    request = offer["request"]
    travel_time_raw = offer.get("travel_time", getattr(request, "ttrav", 0.0))
    travel_time = float(travel_time_raw.total_seconds() if hasattr(travel_time_raw, "total_seconds") else travel_time_raw)
    distance = float(getattr(request, "dist", 0.0)) if hasattr(request, "dist") else None
    return MaaSSimCandidateOffer(
        driver_id=int(offer["veh_id"]),
        request_id=int(offer["req_id"]),
        driver_position=veh.veh.pos,
        origin=getattr(request, "origin", None),
        destination=getattr(request, "destination", None),
        wait_time=float(offer.get("wait_time", 0.0)),
        travel_time=travel_time,
        fare=float(offer.get("fare", 0.0)),
        distance=distance,
        time=float(veh.sim.env.now),
    )


def synthetic_features(offer: MaaSSimCandidateOffer, config: SyntheticRuleConfig) -> dict[str, float | int]:
    fare_per_second = offer.fare / max(float(offer.travel_time), 1.0)
    base = offer_to_rule_features(
        offer,
        MaaSSimFeatureConfig(
            long_trip_seconds=config.long_trip_seconds,
            surge_fare_per_second=config.surge_fare_per_second,
        ),
    )
    base["leaves_zone"] = int(float(offer.wait_time) >= config.far_pickup_seconds)
    base["surge"] = int(fare_per_second >= config.surge_fare_per_second)
    base["after_deadline"] = int(float(offer.time or 0.0) >= config.home_after_seconds)
    base["home_ward"] = int(str(offer.destination) == str(offer.driver_position))
    return base


def synthetic_action_for_type(theta: tuple[int, int, int, int], offer: MaaSSimCandidateOffer, config: SyntheticRuleConfig) -> tuple[int, str]:
    features = synthetic_features(offer, config)
    avoid_long, zone_loyal, home_pull, surge_only = theta
    if avoid_long and int(features["long_trip"]):
        return DECLINE_B, "avoid_long"
    if zone_loyal and int(features["leaves_zone"]):
        return DECLINE_C, "zone_loyal"
    if surge_only and not int(features["surge"]):
        return DECLINE_D, "surge_only"
    if home_pull and int(features["after_deadline"]) and not int(features["home_ward"]):
        return REPOSITION, "home_pull"
    return ACCEPT, "accept"


def posterior_accept_probability(posterior: RulePosterior, offer: MaaSSimCandidateOffer, config: SyntheticRuleConfig) -> float:
    accept_prob = 0.0
    for type_prob, theta in zip(posterior.probs(), posterior.type_space, strict=True):
        action, _ = synthetic_action_for_type(tuple(int(value) for value in theta), offer, config)
        if action == ACCEPT:
            accept_prob += float(type_prob)
    return float(accept_prob)


@dataclass
class SyntheticRuleTracker:
    out_path: Path
    intervene: bool = False
    seed: int = 0
    assignment_mode: str = "cycle"
    config: SyntheticRuleConfig = field(default_factory=SyntheticRuleConfig)
    env: CourierDispatchEnv = field(default_factory=lambda: CourierDispatchEnv(n_agents=1, rule_count=4, horizon=1, seed=0))
    true_types: dict[int, tuple[int, int, int, int]] = field(default_factory=dict)
    posteriors: dict[int, RulePosterior] = field(default_factory=dict)
    rows: list[dict[str, object]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.out_path.parent.mkdir(parents=True, exist_ok=True)

    def type_for_driver(self, driver_id: int) -> tuple[int, int, int, int]:
        if driver_id not in self.true_types:
            if self.assignment_mode == "random":
                rng = np.random.default_rng(self.seed + 1009 * int(driver_id))
                self.true_types[driver_id] = tuple(int(v) for v in self.env.type_space[int(rng.integers(0, len(self.env.type_space)))])
            else:
                self.true_types[driver_id] = DEFAULT_DRIVER_TYPES.get(driver_id, tuple(int(v) for v in self.env.type_space[driver_id % len(self.env.type_space)]))
        return self.true_types[driver_id]

    def posterior_for_driver(self, driver_id: int) -> RulePosterior:
        if driver_id not in self.posteriors:
            self.posteriors[driver_id] = RulePosterior(self.env.type_space)
        return self.posteriors[driver_id]

    def features_for_offer(self, offer: MaaSSimCandidateOffer) -> dict[str, float | int]:
        return synthetic_features(offer, self.config)

    def decline_function(self, *args: Any, **kwargs: Any) -> bool:
        veh = kwargs.get("veh")
        if veh is None:
            return False
        my_offer = self._current_offer(veh)
        if my_offer is None:
            return False
        candidate = offer_from_maassim(veh, my_offer)
        action, reason = self._synthetic_action(candidate)
        synthetic_declined = action != ACCEPT
        if self.intervene:
            actual_declined = synthetic_declined
        else:
            from MaaSSim.decisions import f_decline as default_decline  # type: ignore

            actual_declined = bool(default_decline(veh=veh))
        self._update_posterior(candidate, action, reason, synthetic_declined, actual_declined)
        return actual_declined

    def _current_offer(self, veh: Any) -> dict[str, Any] | None:
        for offer in veh.platform.offers.values():
            if offer.get("status") == 0 and offer.get("veh_id") == veh.id:
                return offer
        return None

    def _synthetic_action(self, offer: MaaSSimCandidateOffer) -> tuple[int, str]:
        return synthetic_action_for_type(self.type_for_driver(offer.driver_id), offer, self.config)

    def _update_posterior(self, offer: MaaSSimCandidateOffer, action: int, reason: str, synthetic_declined: bool, actual_declined: bool) -> None:
        features = self.features_for_offer(offer)
        state = state_from_dict(features)
        posterior = self.posterior_for_driver(offer.driver_id)
        posterior.update(self.env, state, action)
        true_type = np.asarray(self.type_for_driver(offer.driver_id), dtype=int)
        self.rows.append(
            {
                "time": offer.time,
                "driver_id": offer.driver_id,
                "request_id": offer.request_id,
                "action_code": int(action),
                "synthetic_declined": bool(synthetic_declined),
                "actual_declined": bool(actual_declined),
                "intervened": bool(self.intervene),
                "reason": reason,
                "true_type": "".join(str(v) for v in true_type.tolist()),
                "ptrue": posterior.prob_true(true_type),
                "rule_acc": posterior.rule_marginal_accuracy(true_type),
                "long_trip": features["long_trip"],
                "leaves_zone": features["leaves_zone"],
                "home_ward": features["home_ward"],
                "surge": features["surge"],
                "pay": features["pay"],
                "wait_time": offer.wait_time,
                "travel_time": offer.travel_time,
                "fare": offer.fare,
            }
        )

    def write_csv(self) -> None:
        if not self.rows:
            self.out_path.write_text("", encoding="utf-8")
            return
        with self.out_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(self.rows[0].keys()))
            writer.writeheader()
            writer.writerows(self.rows)

    def summary(self) -> dict[str, object]:
        if not self.rows:
            return {"events": 0}
        final_by_driver = {}
        for row in self.rows:
            final_by_driver[int(row["driver_id"])] = row
        return {
            "events": len(self.rows),
            "drivers": len(final_by_driver),
            "mean_final_ptrue": float(np.mean([float(row["ptrue"]) for row in final_by_driver.values()])),
            "mean_final_rule_acc": float(np.mean([float(row["rule_acc"]) for row in final_by_driver.values()])),
            "synthetic_decline_rate": float(np.mean([float(row["synthetic_declined"]) for row in self.rows])),
            "actual_decline_rate": float(np.mean([float(row["actual_declined"]) for row in self.rows])),
            "intervened": bool(self.intervene),
        }

    def persona_payload(self) -> dict[str, object]:
        return {
            "assignment_mode": self.assignment_mode,
            "seed": self.seed,
            "driver_types": {str(driver_id): "".join(str(v) for v in type_tuple) for driver_id, type_tuple in sorted(self.true_types.items())},
        }
