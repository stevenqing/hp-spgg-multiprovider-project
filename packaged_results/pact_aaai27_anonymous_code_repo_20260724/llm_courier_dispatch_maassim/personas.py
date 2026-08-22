"""Passenger personas for MaaSSim integration experiments."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from itertools import product
from pathlib import Path
from typing import Any

import numpy as np


PASSENGER_RULES = ("impatient", "price_sensitive", "delay_sensitive", "pooling_averse")
DEFAULT_PASSENGER_TYPES = [
    (1, 0, 1, 0),
    (0, 1, 1, 0),
    (1, 1, 0, 1),
    (0, 0, 1, 1),
    (1, 0, 0, 0),
    (0, 1, 0, 1),
]


@dataclass(frozen=True)
class PassengerPersonaConfig:
    impatient_wait_ratio: float = 0.85
    price_sensitive_fare: float = 2.25
    delay_sensitive_total_ratio: float = 2.25
    mismatch_likelihood: float = 0.08


def passenger_type_space() -> np.ndarray:
    return np.asarray(list(product([0, 1], repeat=len(PASSENGER_RULES))), dtype=int)


class BinaryTypePosterior:
    def __init__(self, type_space: np.ndarray):
        self.type_space = np.asarray(type_space, dtype=int)
        self.log_probs = np.full(len(self.type_space), -np.log(len(self.type_space)), dtype=float)

    def probs(self) -> np.ndarray:
        shifted = self.log_probs - float(np.max(self.log_probs))
        probs = np.exp(shifted)
        total = float(probs.sum())
        if total <= 0.0:
            return np.full(len(self.type_space), 1.0 / len(self.type_space), dtype=float)
        return probs / total

    def update(self, likelihoods: np.ndarray) -> None:
        self.log_probs += np.log(np.maximum(np.asarray(likelihoods, dtype=float), 1e-12))
        self.log_probs -= float(np.max(self.log_probs))

    def prob_true(self, true_type: tuple[int, ...]) -> float:
        target = np.asarray(true_type, dtype=int)
        matches = np.where(np.all(self.type_space == target, axis=1))[0]
        if len(matches) == 0:
            return 0.0
        return float(self.probs()[int(matches[0])])

    def rule_accuracy(self, true_type: tuple[int, ...]) -> float:
        target = np.asarray(true_type, dtype=int)
        marginals = self.probs() @ self.type_space
        return float(1.0 - np.mean(np.abs(marginals - target)))


@dataclass
class PassengerPersonaTracker:
    out_path: Path
    config: PassengerPersonaConfig = field(default_factory=PassengerPersonaConfig)
    seed: int = 0
    assignment_mode: str = "cycle"
    type_space: np.ndarray = field(default_factory=passenger_type_space)
    true_types: dict[int, tuple[int, int, int, int]] = field(default_factory=dict)
    posteriors: dict[int, BinaryTypePosterior] = field(default_factory=dict)
    rows: list[dict[str, object]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.out_path.parent.mkdir(parents=True, exist_ok=True)

    def type_for_passenger(self, passenger_id: int) -> tuple[int, int, int, int]:
        if passenger_id not in self.true_types:
            if self.assignment_mode == "random":
                rng = np.random.default_rng(self.seed + 2003 * int(passenger_id))
                self.true_types[passenger_id] = tuple(int(v) for v in self.type_space[int(rng.integers(0, len(self.type_space)))])
            else:
                self.true_types[passenger_id] = DEFAULT_PASSENGER_TYPES[int(passenger_id) % len(DEFAULT_PASSENGER_TYPES)]
        return self.true_types[passenger_id]

    def posterior_for_passenger(self, passenger_id: int) -> BinaryTypePosterior:
        if passenger_id not in self.posteriors:
            self.posteriors[passenger_id] = BinaryTypePosterior(self.type_space)
        return self.posteriors[passenger_id]

    def mode_choice_function(self, *args: Any, **kwargs: Any) -> bool:
        traveller = kwargs.get("traveller") or kwargs.get("pax")
        if traveller is None:
            return False
        offer = self._active_offer(traveller)
        if offer is None:
            return False
        passenger_id = int(traveller.id)
        true_type = self.type_for_passenger(passenger_id)
        reject, reason = self.reject_for_type(true_type, traveller, offer)
        self._update_posterior(passenger_id, traveller, offer, reject, reason)
        return reject

    def _active_offer(self, traveller: Any) -> dict[str, Any] | None:
        for offer in traveller.offers.values():
            if offer.get("status") == 0:
                return offer
        return None

    def reject_for_type(self, type_tuple: tuple[int, int, int, int], traveller: Any, offer: dict[str, Any]) -> tuple[bool, str]:
        impatient, price_sensitive, delay_sensitive, pooling_averse = type_tuple
        direct_time = self._direct_time_seconds(traveller)
        wait_time = float(offer.get("wait_time", 0.0))
        travel_time = float(offer.get("travel_time", direct_time))
        fare = float(offer.get("fare", 0.0))
        simpaxes = offer.get("simpaxes", [])
        if impatient and wait_time > self.config.impatient_wait_ratio * max(direct_time, 1.0):
            return True, "impatient"
        if price_sensitive and fare > self.config.price_sensitive_fare:
            return True, "price_sensitive"
        if delay_sensitive and (wait_time + travel_time) / max(direct_time, 1.0) > self.config.delay_sensitive_total_ratio:
            return True, "delay_sensitive"
        if pooling_averse and len(simpaxes) > 1:
            return True, "pooling_averse"
        return False, "accept"

    def _direct_time_seconds(self, traveller: Any) -> float:
        raw = getattr(traveller.request, "ttrav", 1.0)
        if hasattr(raw, "total_seconds"):
            return float(raw.total_seconds())
        return float(raw)

    def _update_posterior(self, passenger_id: int, traveller: Any, offer: dict[str, Any], rejected: bool, reason: str) -> None:
        posterior = self.posterior_for_passenger(passenger_id)
        likelihoods = []
        for theta in self.type_space:
            predicted_reject, _ = self.reject_for_type(tuple(int(value) for value in theta), traveller, offer)
            likelihoods.append(1.0 - self.config.mismatch_likelihood if predicted_reject == rejected else self.config.mismatch_likelihood)
        posterior.update(np.asarray(likelihoods, dtype=float))
        true_type = self.type_for_passenger(passenger_id)
        self.rows.append(
            {
                "time": float(traveller.sim.env.now),
                "passenger_id": passenger_id,
                "request_id": int(offer.get("req_id", passenger_id)),
                "rejected": bool(rejected),
                "reason": reason,
                "true_type": "".join(str(v) for v in true_type),
                "ptrue": posterior.prob_true(true_type),
                "rule_acc": posterior.rule_accuracy(true_type),
                "wait_time": float(offer.get("wait_time", 0.0)),
                "travel_time": float(offer.get("travel_time", 0.0)),
                "fare": float(offer.get("fare", 0.0)),
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
        final_by_passenger = {}
        for row in self.rows:
            final_by_passenger[int(row["passenger_id"])] = row
        return {
            "events": len(self.rows),
            "passengers": len(final_by_passenger),
            "mean_final_ptrue": float(np.mean([float(row["ptrue"]) for row in final_by_passenger.values()])),
            "mean_final_rule_acc": float(np.mean([float(row["rule_acc"]) for row in final_by_passenger.values()])),
            "rejection_rate": float(np.mean([float(row["rejected"]) for row in self.rows])),
        }

    def persona_payload(self) -> dict[str, object]:
        return {
            "assignment_mode": self.assignment_mode,
            "seed": self.seed,
            "passenger_types": {str(passenger_id): "".join(str(v) for v in type_tuple) for passenger_id, type_tuple in sorted(self.true_types.items())},
        }
