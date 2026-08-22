"""Common-state replay evaluation for MaaSSim Persona v2 policies.

The replay fixes a sequence of MaaSSim queue snapshots and persona maps, then
lets each policy choose assignments on the same candidate sets. Outcomes are
generated from the synthetic driver and passenger personas without advancing the
MaaSSim simulator. This isolates one-step policy quality from closed-loop state
distribution shifts.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from dataclasses import dataclass
from itertools import combinations, permutations
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_courier_dispatch.dispatch_env import ACCEPT
from llm_courier_dispatch_maassim.adapter import MaaSSimCandidateOffer, MaaSSimQueueSnapshot
from llm_courier_dispatch_maassim.hidden_rules import SyntheticRuleConfig, SyntheticRuleTracker, synthetic_action_for_type
from llm_courier_dispatch_maassim.personas import PassengerPersonaConfig, PassengerPersonaTracker
from llm_courier_dispatch_maassim.policies import MaaSSimKpiPolicy, MaaSSimNearestPolicy, MaaSSimRandomPolicy


ANALYSIS = ROOT / "analysis" / "courier_dispatch_maassim"
FIGS = [ROOT / "figs", ROOT / "arr_paper" / "figs"]
SEEDS = list(range(10))
SOURCE_POLICY = "nearest"
PREFIX = "persona_v2_main"
POLICIES = ["wait_oracle", "nearest", "random", "pact_kpi", "pact_plus_kpi", "oracle_kpi"]
LABELS = {
    "wait_oracle": "Wait-oracle",
    "nearest": "Nearest",
    "random": "Random",
    "pact_kpi": "PACT",
    "pact_plus_kpi": "PACT+",
    "oracle_kpi": "Oracle",
}
COLORS = {
    "wait_oracle": "#c7773d",
    "nearest": "#8c8c8c",
    "random": "#555555",
    "pact_kpi": "#82a6d9",
    "pact_plus_kpi": "#12345d",
    "oracle_kpi": "#3d7b62",
}


@dataclass
class ReplayStats:
    policy: str
    seed: int
    snapshots: int = 0
    assignments: int = 0
    served: int = 0
    driver_rejects: int = 0
    passenger_rejects: int = 0
    total_wait: float = 0.0
    total_fare: float = 0.0
    exact_wait_oracle_matches: int = 0
    extra_wait: float = 0.0
    driver_ptrue: float = float("nan")
    driver_rule_acc: float = float("nan")
    passenger_ptrue: float = float("nan")
    passenger_rule_acc: float = float("nan")


def mean(values: list[float]) -> float:
    return float(sum(values) / len(values)) if values else float("nan")


def sem(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = mean(values)
    return float(math.sqrt(sum((value - avg) ** 2 for value in values) / (len(values) - 1)) / math.sqrt(len(values)))


def tuple_from_bits(bits: str) -> tuple[int, int, int, int]:
    return tuple(int(char) for char in bits)  # type: ignore[return-value]


def load_personas(seed: int) -> dict[str, object]:
    path = ANALYSIS / f"{SOURCE_POLICY}_{PREFIX}_s{seed}_personas.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_snapshots(seed: int) -> list[MaaSSimQueueSnapshot]:
    path = ANALYSIS / f"{SOURCE_POLICY}_{PREFIX}_s{seed}_queue_snapshots.jsonl"
    snapshots = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        candidates = tuple(MaaSSimCandidateOffer(**candidate) for candidate in raw.get("candidates", []))
        snapshots.append(
            MaaSSimQueueSnapshot(
                time=float(raw.get("time", 0.0)),
                vehicle_queue=tuple(int(value) for value in raw.get("vehicle_queue", [])),
                request_queue=tuple(int(value) for value in raw.get("request_queue", [])),
                candidates=candidates,
            )
        )
    return snapshots


def init_trackers(seed: int, personas: dict[str, object]) -> tuple[SyntheticRuleTracker, PassengerPersonaTracker]:
    driver_tracker = SyntheticRuleTracker(
        ANALYSIS / f"_replay_driver_{seed}.csv",
        intervene=True,
        seed=seed,
        assignment_mode="random",
        config=SyntheticRuleConfig(long_trip_seconds=300.0, far_pickup_seconds=180.0, surge_fare_per_second=0.006, home_after_seconds=2700.0),
    )
    passenger_tracker = PassengerPersonaTracker(
        ANALYSIS / f"_replay_passenger_{seed}.csv",
        seed=seed,
        assignment_mode="random",
        config=PassengerPersonaConfig(impatient_wait_ratio=1.0, price_sensitive_fare=2.75, delay_sensitive_total_ratio=3.0),
    )
    driver_types = ((personas.get("driver_personas") or {}).get("driver_types") or {})
    passenger_types = ((personas.get("passenger_personas") or {}).get("passenger_types") or {})
    driver_tracker.true_types = {int(driver): tuple_from_bits(bits) for driver, bits in driver_types.items()}
    passenger_tracker.true_types = {int(passenger): tuple_from_bits(bits) for passenger, bits in passenger_types.items()}
    return driver_tracker, passenger_tracker


def build_policy(policy: str, seed: int, driver_tracker: SyntheticRuleTracker) -> Any:
    if policy == "nearest":
        return MaaSSimNearestPolicy()
    if policy == "random":
        return MaaSSimRandomPolicy(rng_seed=seed)
    if policy == "pact_kpi":
        return MaaSSimKpiPolicy(posterior_source=driver_tracker, wait_weight=0.12, fare_weight=0.0, reject_penalty=0.0)
    if policy == "pact_plus_kpi":
        return MaaSSimKpiPolicy(posterior_source=driver_tracker, wait_weight=0.12, fare_weight=0.0, reject_penalty=0.25)
    if policy == "oracle_kpi":
        return MaaSSimKpiPolicy(posterior_source=driver_tracker, oracle=True, wait_weight=0.12, fare_weight=0.0, reject_penalty=0.0)
    raise ValueError(policy)


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


def evaluate_policy_seed(policy_name: str, seed: int) -> ReplayStats:
    personas = load_personas(seed)
    snapshots = load_snapshots(seed)
    driver_tracker, passenger_tracker = init_trackers(seed, personas)
    policy = None if policy_name == "wait_oracle" else build_policy(policy_name, seed, driver_tracker)
    stats = ReplayStats(policy=policy_name, seed=seed)
    for snapshot in snapshots:
        if not snapshot.candidates:
            continue
        oracle_assignment = wait_oracle(snapshot)
        assignment = oracle_assignment if policy_name == "wait_oracle" else policy.choose_assignment(snapshot)
        if not assignment:
            continue
        stats.snapshots += 1
        if assignment == oracle_assignment:
            stats.exact_wait_oracle_matches += 1
        offer_by_pair = {(offer.driver_id, offer.request_id): offer for offer in snapshot.candidates}
        oracle_wait = sum(offer_by_pair[(driver, request)].wait_time for driver, request in oracle_assignment.items())
        policy_wait = sum(offer_by_pair[(driver, request)].wait_time for driver, request in assignment.items() if (driver, request) in offer_by_pair)
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
                continue
            traveller = fake_traveller(request_id, offer)
            offer_payload = offer_dict(offer)
            passenger_reject, passenger_reason = passenger_tracker.reject_for_type(passenger_tracker.type_for_passenger(request_id), traveller, offer_payload)
            passenger_tracker._update_posterior(request_id, traveller, offer_payload, passenger_reject, passenger_reason)
            if passenger_reject:
                stats.passenger_rejects += 1
                continue
            stats.served += 1
            stats.total_wait += float(offer.wait_time)
            stats.total_fare += float(offer.fare)
    driver_summary = driver_tracker.summary()
    passenger_summary = passenger_tracker.summary()
    stats.driver_ptrue = float(driver_summary.get("mean_final_ptrue", float("nan")))
    stats.driver_rule_acc = float(driver_summary.get("mean_final_rule_acc", float("nan")))
    stats.passenger_ptrue = float(passenger_summary.get("mean_final_ptrue", float("nan")))
    stats.passenger_rule_acc = float(passenger_summary.get("mean_final_rule_acc", float("nan")))
    return stats


def aggregate(stats: list[ReplayStats]) -> list[dict[str, object]]:
    rows = []
    for policy in POLICIES:
        group = [stat for stat in stats if stat.policy == policy]
        if not group:
            continue
        row: dict[str, object] = {"policy": policy, "label": LABELS[policy], "seeds": len(group)}
        metrics = {
            "snapshots": [stat.snapshots for stat in group],
            "assignments": [stat.assignments for stat in group],
            "served": [stat.served for stat in group],
            "driver_rejects": [stat.driver_rejects for stat in group],
            "passenger_rejects": [stat.passenger_rejects for stat in group],
            "mean_wait_served": [stat.total_wait / max(stat.served, 1) for stat in group],
            "extra_wait_per_snapshot": [stat.extra_wait / max(stat.snapshots, 1) for stat in group],
            "oracle_match_rate": [stat.exact_wait_oracle_matches / max(stat.snapshots, 1) for stat in group],
            "driver_ptrue": [stat.driver_ptrue for stat in group],
            "driver_rule_acc": [stat.driver_rule_acc for stat in group],
            "passenger_ptrue": [stat.passenger_ptrue for stat in group],
            "passenger_rule_acc": [stat.passenger_rule_acc for stat in group],
        }
        for key, values in metrics.items():
            row[key] = mean([float(value) for value in values])
            row[f"{key}_sem"] = sem([float(value) for value in values])
        rows.append(row)
    return rows


def write_outputs(summary: list[dict[str, object]]) -> None:
    csv_path = ANALYSIS / "maassim_common_state_replay_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        writer.writerows(summary)
    lines = [
        "# MaaSSim Common-State Replay Evaluation",
        "",
        "All policies are evaluated on the same exogenous queue snapshots from the nearest Persona v2 main trajectory and the same saved persona maps.",
        "",
        "| Policy | Seeds | Oracle-match | Extra wait/snapshot | Served | Driver rejects | Passenger rejects | Driver rule acc |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(
            "| {label} | {seeds} | {match:.3f} | {extra:.2f} +/- {extrasem:.2f} | {served:.1f} | {drej:.1f} | {prej:.1f} | {acc:.3f} |".format(
                label=row["label"],
                seeds=row["seeds"],
                match=float(row["oracle_match_rate"]),
                extra=float(row["extra_wait_per_snapshot"]),
                extrasem=float(row["extra_wait_per_snapshot_sem"]),
                served=float(row["served"]),
                drej=float(row["driver_rejects"]),
                prej=float(row["passenger_rejects"]),
                acc=float(row["driver_rule_acc"]),
            )
        )
    best_wait = min(summary, key=lambda row: float(row["extra_wait_per_snapshot"]))
    lines.extend(["", f"Closest to wait oracle on common states: `{best_wait['label']}`."])
    (ANALYSIS / "maassim_common_state_replay_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    plot_summary(summary)


def plot_summary(summary: list[dict[str, object]]) -> None:
    labels = [str(row["label"]) for row in summary]
    colors = [COLORS[str(row["policy"])] for row in summary]
    x = np.arange(len(summary))
    fig, axes = plt.subplots(1, 3, figsize=(10.8, 3.2))
    specs = [
        ("oracle_match_rate", "Oracle-match"),
        ("extra_wait_per_snapshot", "Extra wait/snapshot"),
        ("served", "Served offers"),
    ]
    for ax, (metric, ylabel) in zip(axes, specs, strict=True):
        vals = [float(row[metric]) for row in summary]
        errs = [float(row.get(f"{metric}_sem", 0.0)) for row in summary]
        ax.bar(x, vals, yerr=errs, color=colors, edgecolor="white", linewidth=0.8, capsize=2.5)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=25, ha="right")
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", linestyle=":", linewidth=0.55, color="#dddddd")
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
    fig.suptitle("MaaSSim common-state replay", x=0.02, y=1.02, ha="left", fontsize=12, fontweight="semibold")
    fig.tight_layout()
    for out_dir in FIGS:
        out_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_dir / "fig_maassim_common_state_replay.png", bbox_inches="tight", facecolor="white")
        fig.savefig(out_dir / "fig_maassim_common_state_replay.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    stats = [evaluate_policy_seed(policy, seed) for policy in POLICIES for seed in SEEDS]
    summary = aggregate(stats)
    write_outputs(summary)
    print(json.dumps({"rows": len(stats), "summary_rows": len(summary)}, indent=2))


if __name__ == "__main__":
    main()