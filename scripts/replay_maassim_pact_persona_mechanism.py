"""Persona-mechanism replay for MaaSSim PACT.

This common-state replay keeps the exogenous MaaSSim queue states fixed and
changes only the belief source used by PACT. The ablation is designed to test
whether performance gains come from recovering driver personas rather than from
using a different assignment solver.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from dataclasses import dataclass, field
from itertools import combinations, permutations
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_courier_dispatch.dispatch_env import ACCEPT, CourierDispatchEnv, RulePosterior
from llm_courier_dispatch_maassim.adapter import MaaSSimCandidateOffer, MaaSSimQueueSnapshot
from llm_courier_dispatch_maassim.hidden_rules import (
    SyntheticRuleConfig,
    SyntheticRuleTracker,
    posterior_accept_probability,
    synthetic_action_for_type,
    synthetic_features,
)
from llm_courier_dispatch_maassim.personas import PassengerPersonaConfig, PassengerPersonaTracker
from llm_courier_dispatch_maassim.policies import MaaSSimNearestPolicy, MaaSSimRandomPolicy


ANALYSIS = ROOT / "analysis" / "courier_dispatch_maassim"
FIG_DIRS = [ROOT / "figs", ROOT / "arr_paper" / "figs"]
SEEDS = list(range(10))
SOURCE_POLICY = "nearest"
PREFIX = "persona_v2_main"

SERVE_VALUE = 3.0
WAIT_WEIGHT = 0.01
TRAVEL_WEIGHT = 0.0
FARE_WEIGHT = 0.0
DRIVER_REJECT_PENALTY = 2.0
PASSENGER_REJECT_PENALTY = 0.5

VARIANTS = ["nearest", "random", "pact_prior", "pact_shuffled", "pact", "oracle"]
LABELS = {
    "nearest": "Nearest",
    "random": "Random",
    "pact_prior": "PACT-prior",
    "pact_shuffled": "PACT-shuffled",
    "pact": "PACT",
    "oracle": "Oracle",
}
BELIEF_LABELS = {
    "nearest": "none",
    "random": "none",
    "pact_prior": "uniform prior",
    "pact_shuffled": "learned posterior, shuffled across drivers",
    "pact": "learned posterior",
    "oracle": "true hidden persona",
}
COLORS = {
    "nearest": "#8c8c8c",
    "random": "#555555",
    "pact_prior": "#b9cce8",
    "pact_shuffled": "#d18a7a",
    "pact": "#12345d",
    "oracle": "#3d7b62",
}


@dataclass
class ReplayStats:
    variant: str
    seed: int
    snapshots: int = 0
    assignments: int = 0
    served: int = 0
    driver_rejects: int = 0
    passenger_rejects: int = 0
    total_wait: float = 0.0
    total_fare: float = 0.0
    realized_utility: float = 0.0
    exact_wait_oracle_matches: int = 0
    extra_wait: float = 0.0
    driver_ptrue: float = float("nan")
    driver_rule_acc: float = float("nan")
    policy_ptrue: float = float("nan")
    policy_rule_acc: float = float("nan")
    passenger_ptrue: float = float("nan")
    passenger_rule_acc: float = float("nan")


@dataclass
class UniformBeliefSource:
    config: SyntheticRuleConfig
    env: CourierDispatchEnv = field(default_factory=lambda: CourierDispatchEnv(n_agents=1, rule_count=4, horizon=1, seed=0))

    def posterior_for_driver(self, driver_id: int) -> RulePosterior:
        return RulePosterior(self.env.type_space)

    def features_for_offer(self, offer: MaaSSimCandidateOffer) -> dict[str, float | int]:
        return synthetic_features(offer, self.config)


@dataclass
class ShuffledBeliefSource:
    tracker: SyntheticRuleTracker
    mapping: dict[int, int]

    @property
    def config(self) -> SyntheticRuleConfig:
        return self.tracker.config

    def posterior_for_driver(self, driver_id: int) -> RulePosterior:
        mapped_driver = self.mapping.get(int(driver_id), int(driver_id))
        return self.tracker.posterior_for_driver(mapped_driver)

    def features_for_offer(self, offer: MaaSSimCandidateOffer) -> dict[str, float | int]:
        return self.tracker.features_for_offer(offer)


@dataclass
class PACTReplayPolicy:
    posterior_source: Any
    oracle: bool = False
    serve_value: float = SERVE_VALUE
    wait_weight: float = WAIT_WEIGHT
    travel_weight: float = TRAVEL_WEIGHT
    fare_weight: float = FARE_WEIGHT
    reject_penalty: float = DRIVER_REJECT_PENALTY
    last_diagnostics: dict[str, object] = field(default_factory=dict)

    def choose_assignment(self, snapshot: MaaSSimQueueSnapshot) -> dict[int, int]:
        offers = list(snapshot.candidates)
        if not offers:
            self.last_diagnostics = {"assignment": {}, "objective": 0.0, "evaluated_assignments": 0}
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
                    accepted_value = (
                        self.serve_value
                        + self.fare_weight * float(offer.fare)
                        - self.wait_weight * float(offer.wait_time)
                        - self.travel_weight * float(offer.travel_time)
                    )
                    score += accept_prob * accepted_value - self.reject_penalty * (1.0 - accept_prob)
                evaluated += 1
                if score > best_score:
                    best_score = score
                    best_assignment = {drivers[driver_idx]: request_id for driver_idx, request_id in zip(driver_subset, request_perm, strict=True)}
        self.last_diagnostics = {"assignment": best_assignment, "objective": best_score, "evaluated_assignments": evaluated}
        return best_assignment

    def _accept_probability(self, offer: MaaSSimCandidateOffer) -> float:
        if self.oracle and hasattr(self.posterior_source, "type_for_driver"):
            action, _ = synthetic_action_for_type(self.posterior_source.type_for_driver(int(offer.driver_id)), offer, self.posterior_source.config)
            return 1.0 if action == ACCEPT else 0.0
        posterior = self.posterior_source.posterior_for_driver(int(offer.driver_id))
        return posterior_accept_probability(posterior, offer, self.posterior_source.config)


def mean(values: list[float]) -> float:
    return float(sum(values) / len(values)) if values else float("nan")


def sem(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = mean(values)
    return float(math.sqrt(sum((value - avg) ** 2 for value in values) / (len(values) - 1)) / math.sqrt(len(values)))


def format_optional(value: object) -> str:
    numeric = float(value)
    if math.isnan(numeric):
        return "n/a"
    return f"{numeric:.3f}"


def tuple_from_bits(bits: str) -> tuple[int, int, int, int]:
    return tuple(int(char) for char in bits)  # type: ignore[return-value]


def load_personas(seed: int) -> dict[str, object]:
    return json.loads((ANALYSIS / f"{SOURCE_POLICY}_{PREFIX}_s{seed}_personas.json").read_text(encoding="utf-8"))


def load_snapshots(seed: int) -> list[MaaSSimQueueSnapshot]:
    path = ANALYSIS / f"{SOURCE_POLICY}_{PREFIX}_s{seed}_queue_snapshots.jsonl"
    snapshots = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        snapshots.append(
            MaaSSimQueueSnapshot(
                time=float(raw.get("time", 0.0)),
                vehicle_queue=tuple(int(value) for value in raw.get("vehicle_queue", [])),
                request_queue=tuple(int(value) for value in raw.get("request_queue", [])),
                candidates=tuple(MaaSSimCandidateOffer(**candidate) for candidate in raw.get("candidates", [])),
            )
        )
    return snapshots


def init_trackers(seed: int, personas: dict[str, object]) -> tuple[SyntheticRuleTracker, PassengerPersonaTracker]:
    driver_tracker = SyntheticRuleTracker(
        ANALYSIS / f"_mechanism_driver_{seed}.csv",
        intervene=True,
        seed=seed,
        assignment_mode="random",
        config=SyntheticRuleConfig(long_trip_seconds=300.0, far_pickup_seconds=180.0, surge_fare_per_second=0.006, home_after_seconds=2700.0),
    )
    passenger_tracker = PassengerPersonaTracker(
        ANALYSIS / f"_mechanism_passenger_{seed}.csv",
        seed=seed,
        assignment_mode="random",
        config=PassengerPersonaConfig(impatient_wait_ratio=1.0, price_sensitive_fare=2.75, delay_sensitive_total_ratio=3.0),
    )
    driver_types = ((personas.get("driver_personas") or {}).get("driver_types") or {})
    passenger_types = ((personas.get("passenger_personas") or {}).get("passenger_types") or {})
    driver_tracker.true_types = {int(driver_id): tuple_from_bits(bits) for driver_id, bits in driver_types.items()}
    passenger_tracker.true_types = {int(passenger_id): tuple_from_bits(bits) for passenger_id, bits in passenger_types.items()}
    return driver_tracker, passenger_tracker


def shuffled_driver_mapping(driver_ids: list[int], seed: int) -> dict[int, int]:
    if len(driver_ids) < 2:
        return {driver_id: driver_id for driver_id in driver_ids}
    rng = np.random.default_rng(seed + 90210)
    shuffled = list(driver_ids)
    while True:
        rng.shuffle(shuffled)
        if all(source != target for source, target in zip(driver_ids, shuffled, strict=True)):
            return {source: target for source, target in zip(driver_ids, shuffled, strict=True)}


def build_policy(variant: str, seed: int, driver_tracker: SyntheticRuleTracker) -> Any:
    if variant == "nearest":
        return MaaSSimNearestPolicy()
    if variant == "random":
        return MaaSSimRandomPolicy(rng_seed=seed)
    if variant == "pact_prior":
        return PACTReplayPolicy(UniformBeliefSource(driver_tracker.config))
    if variant == "pact_shuffled":
        mapping = shuffled_driver_mapping(sorted(driver_tracker.true_types), seed)
        return PACTReplayPolicy(ShuffledBeliefSource(driver_tracker, mapping))
    if variant == "pact":
        return PACTReplayPolicy(driver_tracker)
    if variant == "oracle":
        return PACTReplayPolicy(driver_tracker, oracle=True)
    raise ValueError(variant)


def policy_belief_quality(variant: str, policy: Any, driver_tracker: SyntheticRuleTracker) -> tuple[float, float]:
    driver_ids = sorted(driver_tracker.true_types)
    if not driver_ids or variant in {"nearest", "random"}:
        return float("nan"), float("nan")
    if variant == "oracle":
        return 1.0, 1.0
    if not isinstance(policy, PACTReplayPolicy):
        return float("nan"), float("nan")
    ptrue_values = []
    rule_acc_values = []
    for driver_id in driver_ids:
        posterior = policy.posterior_source.posterior_for_driver(driver_id)
        true_type = np.asarray(driver_tracker.type_for_driver(driver_id), dtype=int)
        ptrue_values.append(float(posterior.prob_true(true_type)))
        rule_acc_values.append(float(posterior.rule_marginal_accuracy(true_type)))
    return mean(ptrue_values), mean(rule_acc_values)


def wait_oracle(snapshot: MaaSSimQueueSnapshot) -> dict[int, int]:
    offers = list(snapshot.candidates)
    if not offers:
        return {}
    drivers = sorted({offer.driver_id for offer in offers})
    requests = sorted({offer.request_id for offer in offers})
    offer_by_pair = {(offer.driver_id, offer.request_id): offer for offer in offers}
    match_count = min(len(drivers), len(requests))
    best_assignment: dict[int, int] = {}
    best_wait = float("inf")
    for driver_subset in combinations(range(len(drivers)), match_count):
        for request_perm in permutations(requests, match_count):
            if any((drivers[driver_idx], request_id) not in offer_by_pair for driver_idx, request_id in zip(driver_subset, request_perm, strict=True)):
                continue
            total_wait = sum(offer_by_pair[(drivers[driver_idx], request_id)].wait_time for driver_idx, request_id in zip(driver_subset, request_perm, strict=True))
            if total_wait < best_wait:
                best_wait = total_wait
                best_assignment = {drivers[driver_idx]: request_id for driver_idx, request_id in zip(driver_subset, request_perm, strict=True)}
    return best_assignment


def fake_traveller(passenger_id: int, offer: MaaSSimCandidateOffer) -> Any:
    return SimpleNamespace(
        id=int(passenger_id),
        request=SimpleNamespace(ttrav=float(offer.travel_time)),
        sim=SimpleNamespace(env=SimpleNamespace(now=float(offer.time or 0.0))),
    )


def offer_dict(offer: MaaSSimCandidateOffer) -> dict[str, object]:
    return {
        "req_id": offer.request_id,
        "wait_time": offer.wait_time,
        "travel_time": offer.travel_time,
        "fare": offer.fare,
        "simpaxes": [offer.request_id],
    }


def accepted_utility(offer: MaaSSimCandidateOffer) -> float:
    return SERVE_VALUE + FARE_WEIGHT * float(offer.fare) - WAIT_WEIGHT * float(offer.wait_time) - TRAVEL_WEIGHT * float(offer.travel_time)


def evaluate_variant_seed(variant: str, seed: int) -> ReplayStats:
    personas = load_personas(seed)
    snapshots = load_snapshots(seed)
    driver_tracker, passenger_tracker = init_trackers(seed, personas)
    policy = build_policy(variant, seed, driver_tracker)
    stats = ReplayStats(variant=variant, seed=seed)
    for snapshot in snapshots:
        if not snapshot.candidates:
            continue
        oracle_assignment = wait_oracle(snapshot)
        assignment = policy.choose_assignment(snapshot)
        if not assignment:
            continue
        stats.snapshots += 1
        if assignment == oracle_assignment:
            stats.exact_wait_oracle_matches += 1
        offer_by_pair = {(offer.driver_id, offer.request_id): offer for offer in snapshot.candidates}
        oracle_wait = sum(offer_by_pair[(driver_id, request_id)].wait_time for driver_id, request_id in oracle_assignment.items())
        policy_wait = sum(offer_by_pair[(driver_id, request_id)].wait_time for driver_id, request_id in assignment.items() if (driver_id, request_id) in offer_by_pair)
        stats.extra_wait += policy_wait - oracle_wait
        for driver_id, request_id in assignment.items():
            offer = offer_by_pair.get((driver_id, request_id))
            if offer is None:
                continue
            stats.assignments += 1
            action, reason = synthetic_action_for_type(driver_tracker.type_for_driver(driver_id), offer, driver_tracker.config)
            driver_reject = action != ACCEPT
            driver_tracker._update_posterior(offer, action, reason, driver_reject, driver_reject)
            if driver_reject:
                stats.driver_rejects += 1
                stats.realized_utility -= DRIVER_REJECT_PENALTY
                continue
            traveller = fake_traveller(request_id, offer)
            offer_payload = offer_dict(offer)
            passenger_reject, passenger_reason = passenger_tracker.reject_for_type(passenger_tracker.type_for_passenger(request_id), traveller, offer_payload)
            passenger_tracker._update_posterior(request_id, traveller, offer_payload, passenger_reject, passenger_reason)
            if passenger_reject:
                stats.passenger_rejects += 1
                stats.realized_utility -= PASSENGER_REJECT_PENALTY
                continue
            stats.served += 1
            stats.total_wait += float(offer.wait_time)
            stats.total_fare += float(offer.fare)
            stats.realized_utility += accepted_utility(offer)
    driver_summary = driver_tracker.summary()
    passenger_summary = passenger_tracker.summary()
    stats.driver_ptrue = float(driver_summary.get("mean_final_ptrue", float("nan")))
    stats.driver_rule_acc = float(driver_summary.get("mean_final_rule_acc", float("nan")))
    stats.policy_ptrue, stats.policy_rule_acc = policy_belief_quality(variant, policy, driver_tracker)
    stats.passenger_ptrue = float(passenger_summary.get("mean_final_ptrue", float("nan")))
    stats.passenger_rule_acc = float(passenger_summary.get("mean_final_rule_acc", float("nan")))
    return stats


def aggregate(stats: list[ReplayStats]) -> list[dict[str, object]]:
    summary = []
    for variant in VARIANTS:
        group = [stat for stat in stats if stat.variant == variant]
        row: dict[str, object] = {"variant": variant, "label": LABELS[variant], "belief_source": BELIEF_LABELS[variant], "seeds": len(group)}
        metrics = {
            "snapshots": [stat.snapshots for stat in group],
            "assignments": [stat.assignments for stat in group],
            "served": [stat.served for stat in group],
            "driver_rejects": [stat.driver_rejects for stat in group],
            "passenger_rejects": [stat.passenger_rejects for stat in group],
            "driver_accept_rate": [(stat.assignments - stat.driver_rejects) / max(stat.assignments, 1) for stat in group],
            "served_rate": [stat.served / max(stat.assignments, 1) for stat in group],
            "mean_wait_served": [stat.total_wait / max(stat.served, 1) for stat in group],
            "extra_wait_per_snapshot": [stat.extra_wait / max(stat.snapshots, 1) for stat in group],
            "oracle_match_rate": [stat.exact_wait_oracle_matches / max(stat.snapshots, 1) for stat in group],
            "realized_utility": [stat.realized_utility for stat in group],
            "driver_ptrue": [stat.driver_ptrue for stat in group],
            "driver_rule_acc": [stat.driver_rule_acc for stat in group],
            "policy_ptrue": [stat.policy_ptrue for stat in group],
            "policy_rule_acc": [stat.policy_rule_acc for stat in group],
            "passenger_ptrue": [stat.passenger_ptrue for stat in group],
            "passenger_rule_acc": [stat.passenger_rule_acc for stat in group],
        }
        for key, values in metrics.items():
            numeric = [float(value) for value in values]
            row[key] = mean(numeric)
            row[f"{key}_sem"] = sem(numeric)
        summary.append(row)
    return summary


def write_outputs(summary: list[dict[str, object]]) -> None:
    csv_path = ANALYSIS / "maassim_pact_persona_mechanism_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        writer.writerows(summary)
    lines = [
        "# MaaSSim PACT Persona-Mechanism Replay",
        "",
        "All variants use the same nearest Persona v2 queue snapshots and saved persona maps. PACT variants share one assignment objective; only the driver-persona belief source changes.",
        "",
        f"PACT utility weights: serve_value={SERVE_VALUE}, wait_weight={WAIT_WEIGHT}, driver_reject_penalty={DRIVER_REJECT_PENALTY}, passenger_reject_penalty={PASSENGER_REJECT_PENALTY}.",
        "",
        "| Variant | Belief source | Seeds | Utility | Served | Driver rejects | Driver accept | Extra wait/snapshot | Policy P(true) | Policy rule acc |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(
            "| {label} | {belief} | {seeds} | {utility:.2f} +/- {utility_sem:.2f} | {served:.1f} | {drej:.1f} | {acc_rate:.3f} | {extra:.2f} +/- {extra_sem:.2f} | {ptrue} | {rule_acc} |".format(
                label=row["label"],
                belief=row["belief_source"],
                seeds=row["seeds"],
                utility=float(row["realized_utility"]),
                utility_sem=float(row["realized_utility_sem"]),
                served=float(row["served"]),
                drej=float(row["driver_rejects"]),
                acc_rate=float(row["driver_accept_rate"]),
                extra=float(row["extra_wait_per_snapshot"]),
                extra_sem=float(row["extra_wait_per_snapshot_sem"]),
                ptrue=format_optional(row["policy_ptrue"]),
                rule_acc=format_optional(row["policy_rule_acc"]),
            )
        )
    pact_row = next(row for row in summary if row["variant"] == "pact")
    prior_row = next(row for row in summary if row["variant"] == "pact_prior")
    oracle_row = next(row for row in summary if row["variant"] == "oracle")
    lines.extend(
        [
            "",
            "Mechanism readout:",
            f"- PACT improves realized utility over PACT-prior by {float(pact_row['realized_utility']) - float(prior_row['realized_utility']):.2f}.",
            f"- PACT closes {100.0 * (float(pact_row['realized_utility']) - float(prior_row['realized_utility'])) / max(float(oracle_row['realized_utility']) - float(prior_row['realized_utility']), 1e-9):.1f}% of the prior-to-oracle utility gap.",
            "- PACT-shuffled tests whether the learned posterior must stay attached to the correct driver persona.",
        ]
    )
    (ANALYSIS / "maassim_pact_persona_mechanism_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    plot_summary(summary)


def plot_summary(summary: list[dict[str, object]]) -> None:
    labels = [str(row["label"]) for row in summary]
    colors = [COLORS[str(row["variant"])] for row in summary]
    x = np.arange(len(summary))
    fig, axes = plt.subplots(1, 4, figsize=(13.0, 3.3))
    specs = [
        ("realized_utility", "Utility"),
        ("served", "Served"),
        ("driver_rejects", "Driver rejects"),
        ("policy_rule_acc", "Policy rule acc"),
    ]
    for axis, (metric, ylabel) in zip(axes, specs, strict=True):
        values = [0.0 if math.isnan(float(row[metric])) else float(row[metric]) for row in summary]
        errors = [float(row.get(f"{metric}_sem", 0.0)) for row in summary]
        axis.bar(x, values, yerr=errors, color=colors, edgecolor="white", linewidth=0.8, capsize=2.5)
        axis.set_xticks(x)
        axis.set_xticklabels(labels, rotation=28, ha="right")
        axis.set_ylabel(ylabel)
        axis.grid(axis="y", linestyle=":", linewidth=0.55, color="#dddddd")
        for spine in ("top", "right"):
            axis.spines[spine].set_visible(False)
    fig.suptitle("MaaSSim PACT persona-mechanism replay", x=0.02, y=1.03, ha="left", fontsize=12, fontweight="semibold")
    fig.tight_layout()
    for out_dir in FIG_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_dir / "fig_maassim_pact_persona_mechanism.png", bbox_inches="tight", facecolor="white")
        fig.savefig(out_dir / "fig_maassim_pact_persona_mechanism.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    stats = [evaluate_variant_seed(variant, seed) for variant in VARIANTS for seed in SEEDS]
    summary = aggregate(stats)
    write_outputs(summary)
    print(json.dumps({"rows": len(stats), "summary_rows": len(summary)}, indent=2))


if __name__ == "__main__":
    main()