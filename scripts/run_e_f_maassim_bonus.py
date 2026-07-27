"""Run optional E-F: frozen beta=0.25 MaaSSim bonus ablation.

PACT and PACT+ replay the same saved MaaSSim states and hidden persona maps.
They share the posterior, expected-utility objective, and deterministic
assignment tie-breaking. PACT+ adds a pairwise type-disagreement utility bonus;
beta is frozen at 0.25 and is not tuned on MaaSSim.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from itertools import combinations, permutations
import json
import math
from pathlib import Path
import sys
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import replay_maassim_pact_persona_mechanism as mechanism
from llm_courier_dispatch.dispatch_env import ACCEPT
from llm_courier_dispatch_maassim.adapter import MaaSSimCandidateOffer, MaaSSimQueueSnapshot
from llm_courier_dispatch_maassim.hidden_rules import synthetic_action_for_type


OUT_DIR = ROOT / "analysis" / "e_f_maassim_bonus"
BETA = 0.25
SEEDS = list(range(10))


@dataclass
class BonusReplayPolicy:
    posterior_source: Any
    beta: float = BETA
    last_diagnostics: dict[str, object] = field(default_factory=dict)

    def choose_assignment(self, snapshot: MaaSSimQueueSnapshot) -> dict[int, int]:
        offers = list(snapshot.candidates)
        if not offers:
            self.last_diagnostics = {"assignment": {}, "objective": 0.0, "bonus": 0.0}
            return {}
        drivers = sorted({int(offer.driver_id) for offer in offers})
        requests = sorted({int(offer.request_id) for offer in offers})
        offer_by_pair = {(int(offer.driver_id), int(offer.request_id)): offer for offer in offers}
        match_count = min(len(drivers), len(requests))
        best_assignment: dict[int, int] = {}
        best_objective = float("-inf")
        best_base = 0.0
        best_bonus = 0.0
        evaluated = 0
        for driver_subset in combinations(range(len(drivers)), match_count):
            for request_perm in permutations(requests, match_count):
                pairs = tuple((drivers[index], request_id) for index, request_id in zip(driver_subset, request_perm, strict=True))
                if any(pair not in offer_by_pair for pair in pairs):
                    continue
                base = 0.0
                bonus = 0.0
                for driver_id, request_id in pairs:
                    offer = offer_by_pair[(driver_id, request_id)]
                    posterior = self.posterior_source.posterior_for_driver(driver_id)
                    probabilities = posterior.probs()
                    values = np.asarray(
                        [self._type_value(offer, tuple(int(value) for value in theta)) for theta in posterior.type_space],
                        dtype=float,
                    )
                    base += float(probabilities @ values)
                    difference = np.abs(values[:, None] - values[None, :])
                    bonus += float(np.sum(probabilities[:, None] * probabilities[None, :] * difference))
                objective = base + self.beta * bonus
                evaluated += 1
                assignment = {driver_id: request_id for driver_id, request_id in pairs}
                if objective > best_objective + 1e-12 or (
                    abs(objective - best_objective) <= 1e-12
                    and tuple(sorted(assignment.items())) < tuple(sorted(best_assignment.items()))
                ):
                    best_assignment = assignment
                    best_objective = objective
                    best_base = base
                    best_bonus = bonus
        self.last_diagnostics = {
            "assignment": best_assignment,
            "base_objective": best_base,
            "bonus": best_bonus,
            "objective": best_objective if evaluated else 0.0,
            "evaluated_assignments": evaluated,
        }
        return best_assignment

    @staticmethod
    def _type_value(offer: MaaSSimCandidateOffer, theta: tuple[int, int, int, int]) -> float:
        action, _ = synthetic_action_for_type(theta, offer, mechanism.SyntheticRuleConfig(
            long_trip_seconds=300.0,
            far_pickup_seconds=180.0,
            surge_fare_per_second=0.006,
            home_after_seconds=2700.0,
        ))
        if action != ACCEPT:
            return -mechanism.DRIVER_REJECT_PENALTY
        return mechanism.accepted_utility(offer)


def evaluate_bonus_seed(seed: int) -> tuple[mechanism.ReplayStats, int, int, float]:
    personas = mechanism.load_personas(seed)
    snapshots = mechanism.load_snapshots(seed)
    driver_tracker, passenger_tracker = mechanism.init_trackers(seed, personas)
    policy = BonusReplayPolicy(driver_tracker)
    stats = mechanism.ReplayStats(variant="pact_plus", seed=seed)
    changed_vs_pact = 0
    compared = 0
    total_bonus = 0.0
    for snapshot in snapshots:
        if not snapshot.candidates:
            continue
        baseline_policy = mechanism.PACTReplayPolicy(driver_tracker)
        baseline_assignment = baseline_policy.choose_assignment(snapshot)
        assignment = policy.choose_assignment(snapshot)
        if not assignment:
            continue
        compared += 1
        if assignment != baseline_assignment:
            changed_vs_pact += 1
        total_bonus += float(policy.last_diagnostics.get("bonus", 0.0))
        oracle_assignment = mechanism.wait_oracle(snapshot)
        stats.snapshots += 1
        if assignment == oracle_assignment:
            stats.exact_wait_oracle_matches += 1
        offer_by_pair = {(int(offer.driver_id), int(offer.request_id)): offer for offer in snapshot.candidates}
        oracle_wait = sum(offer_by_pair[(driver_id, request_id)].wait_time for driver_id, request_id in oracle_assignment.items())
        policy_wait = sum(offer_by_pair[(driver_id, request_id)].wait_time for driver_id, request_id in assignment.items())
        stats.extra_wait += policy_wait - oracle_wait
        for driver_id, request_id in assignment.items():
            offer = offer_by_pair[(driver_id, request_id)]
            stats.assignments += 1
            action, reason = synthetic_action_for_type(driver_tracker.type_for_driver(driver_id), offer, driver_tracker.config)
            driver_reject = action != ACCEPT
            driver_tracker._update_posterior(offer, action, reason, driver_reject, driver_reject)
            if driver_reject:
                stats.driver_rejects += 1
                stats.realized_utility -= mechanism.DRIVER_REJECT_PENALTY
                continue
            traveller = mechanism.fake_traveller(request_id, offer)
            offer_payload = mechanism.offer_dict(offer)
            passenger_reject, passenger_reason = passenger_tracker.reject_for_type(
                passenger_tracker.type_for_passenger(request_id), traveller, offer_payload
            )
            passenger_tracker._update_posterior(request_id, traveller, offer_payload, passenger_reject, passenger_reason)
            if passenger_reject:
                stats.passenger_rejects += 1
                stats.realized_utility -= mechanism.PASSENGER_REJECT_PENALTY
                continue
            stats.served += 1
            stats.total_wait += float(offer.wait_time)
            stats.total_fare += float(offer.fare)
            stats.realized_utility += mechanism.accepted_utility(offer)
    driver_summary = driver_tracker.summary()
    passenger_summary = passenger_tracker.summary()
    stats.driver_ptrue = float(driver_summary.get("mean_final_ptrue", float("nan")))
    stats.driver_rule_acc = float(driver_summary.get("mean_final_rule_acc", float("nan")))
    stats.policy_ptrue, stats.policy_rule_acc = mechanism.policy_belief_quality("pact", policy, driver_tracker)
    stats.passenger_ptrue = float(passenger_summary.get("mean_final_ptrue", float("nan")))
    stats.passenger_rule_acc = float(passenger_summary.get("mean_final_rule_acc", float("nan")))
    return stats, changed_vs_pact, compared, total_bonus / max(compared, 1)


def row_from_stats(stats: mechanism.ReplayStats, tracker: str, *, changed: int = 0, compared: int = 0, mean_bonus: float = 0.0) -> dict[str, object]:
    return {
        "seed": stats.seed,
        "tracker": tracker,
        "beta": 0.0 if tracker == "pact" else BETA,
        "utility": stats.realized_utility,
        "snapshots": stats.snapshots,
        "assignments": stats.assignments,
        "served": stats.served,
        "driver_rejects": stats.driver_rejects,
        "passenger_rejects": stats.passenger_rejects,
        "assignment_changes_vs_pact": changed,
        "compared_snapshots": compared,
        "mean_selected_bonus": mean_bonus,
    }


def mean(values: list[float]) -> float:
    return float(np.mean(values))


def sem(values: list[float]) -> float:
    data = np.asarray(values, dtype=float)
    return float(data.std(ddof=1) / math.sqrt(len(data))) if len(data) > 1 else 0.0


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    per_seed: list[dict[str, object]] = []
    for seed in SEEDS:
        pact = mechanism.evaluate_variant_seed("pact", seed)
        pact_plus, changed, compared, mean_bonus = evaluate_bonus_seed(seed)
        per_seed.append(row_from_stats(pact, "pact"))
        per_seed.append(row_from_stats(pact_plus, "pact_plus", changed=changed, compared=compared, mean_bonus=mean_bonus))
    pact = {int(row["seed"]): float(row["utility"]) for row in per_seed if row["tracker"] == "pact"}
    pact_plus = {int(row["seed"]): float(row["utility"]) for row in per_seed if row["tracker"] == "pact_plus"}
    gaps = [pact_plus[seed] - pact[seed] for seed in SEEDS]
    gap_mean = mean(gaps)
    gap_sem = sem(gaps)
    half_width = 2.262 * gap_sem
    summary = []
    for tracker in ("pact", "pact_plus"):
        group = [row for row in per_seed if row["tracker"] == tracker]
        utilities = [float(row["utility"]) for row in group]
        summary.append(
            {
                "tracker": tracker,
                "beta": 0.0 if tracker == "pact" else BETA,
                "seeds": len(group),
                "utility_mean": mean(utilities),
                "utility_sem": sem(utilities),
                "assignment_change_rate_vs_pact": sum(int(row["assignment_changes_vs_pact"]) for row in group) / max(1, sum(int(row["compared_snapshots"]) for row in group)),
                "mean_selected_bonus": mean([float(row["mean_selected_bonus"]) for row in group]),
            }
        )
    gap = {
        "seeds": len(gaps),
        "pact_plus_minus_pact_mean": gap_mean,
        "pact_plus_minus_pact_sem": gap_sem,
        "ci95_low": gap_mean - half_width,
        "ci95_high": gap_mean + half_width,
        "ci_covers_zero": gap_mean - half_width <= 0.0 <= gap_mean + half_width,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(OUT_DIR / "e_f_maassim_bonus_per_seed.csv", per_seed)
    write_csv(OUT_DIR / "e_f_maassim_bonus_summary.csv", summary)
    (OUT_DIR / "e_f_maassim_bonus_metadata.json").write_text(
        json.dumps(
            {
                "experiment": "E-F MaaSSim frozen bonus ablation",
                "status": "complete",
                "provider_calls": 0,
                "beta": BETA,
                "beta_selection": "frozen from disjoint HP-SPGG selection; no MaaSSim retuning",
                "states": "same ten saved nearest-policy Persona-v2 replay sequences",
                "bonus": "posterior-weighted pairwise absolute disagreement in one-step assignment utility",
                "tie_breaking": "lexicographic deterministic assignment order",
                "paired_gap": gap,
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# E-F MaaSSim Frozen Bonus Ablation",
        "",
        f"PACT+ minus PACT utility: {gap_mean:+.3f} +/- {gap_sem:.3f}; 95% CI [{gap['ci95_low']:+.3f}, {gap['ci95_high']:+.3f}].",
        f"Assignment change rate: {float(summary[1]['assignment_change_rate_vs_pact']):.4f}.",
        f"Mean selected disagreement bonus: {float(summary[1]['mean_selected_bonus']):.4f}.",
        "",
        "Beta was frozen at 0.25 from the disjoint HP-SPGG selection and was not tuned on MaaSSim.",
    ]
    (OUT_DIR / "e_f_maassim_bonus.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"summary": summary, "paired_gap": gap}, indent=2))


if __name__ == "__main__":
    main()
