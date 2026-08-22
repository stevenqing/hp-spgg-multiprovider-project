"""Diagnose whether nearest matching is close to oracle wait minimization in MaaSSim."""

from __future__ import annotations

import csv
import json
import math
from itertools import combinations, permutations
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis" / "courier_dispatch_maassim"
POLICIES = ["nearest", "random", "pact_kpi", "pact_plus_kpi", "oracle_kpi"]
LABELS = {
    "nearest": "Nearest",
    "random": "Random",
    "pact_kpi": "PACT",
    "pact_plus_kpi": "PACT+",
    "oracle_kpi": "Oracle",
}
PREFIX = "persona_v2_main"
SEEDS = list(range(10))


def mean(values: list[float]) -> float:
    return float(sum(values) / len(values)) if values else float("nan")


def sem(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = mean(values)
    return math.sqrt(sum((value - avg) ** 2 for value in values) / (len(values) - 1)) / math.sqrt(len(values))


def read_snapshots(policy: str, seed: int) -> list[dict[str, object]]:
    path = ANALYSIS / f"{policy}_{PREFIX}_s{seed}_queue_snapshots.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def normalize_assignment(raw: object) -> dict[int, int]:
    if not isinstance(raw, dict):
        return {}
    return {int(driver): int(request) for driver, request in raw.items()}


def wait_oracle(snapshot: dict[str, object]) -> tuple[dict[int, int], float, int]:
    offers = snapshot.get("candidates", [])
    if not isinstance(offers, list) or not offers:
        return {}, 0.0, 0
    drivers = sorted({int(offer["driver_id"]) for offer in offers})
    requests = sorted({int(offer["request_id"]) for offer in offers})
    offer_by_pair = {(int(offer["driver_id"]), int(offer["request_id"])): float(offer["wait_time"]) for offer in offers}
    match_count = min(len(drivers), len(requests))
    best: dict[int, int] = {}
    best_wait = float("inf")
    evaluated = 0
    for driver_subset in combinations(range(len(drivers)), match_count):
        for request_perm in permutations(requests, match_count):
            if any((drivers[driver_idx], request_id) not in offer_by_pair for driver_idx, request_id in zip(driver_subset, request_perm, strict=True)):
                continue
            total_wait = sum(offer_by_pair[(drivers[driver_idx], request_id)] for driver_idx, request_id in zip(driver_subset, request_perm, strict=True))
            evaluated += 1
            if total_wait < best_wait:
                best_wait = total_wait
                best = {drivers[driver_idx]: request_id for driver_idx, request_id in zip(driver_subset, request_perm, strict=True)}
    return best, best_wait if evaluated else 0.0, evaluated


def assignment_wait(snapshot: dict[str, object], assignment: dict[int, int]) -> float:
    offers = snapshot.get("candidates", [])
    if not isinstance(offers, list) or not assignment:
        return 0.0
    offer_by_pair = {(int(offer["driver_id"]), int(offer["request_id"])): float(offer["wait_time"]) for offer in offers}
    return float(sum(offer_by_pair.get((driver, request), 0.0) for driver, request in assignment.items()))


def diagnose_policy_seed(policy: str, seed: int) -> dict[str, object]:
    snapshots = read_snapshots(policy, seed)
    rows = []
    for snapshot in snapshots:
        oracle_assignment, oracle_wait, evaluated = wait_oracle(snapshot)
        policy_assignment = normalize_assignment(snapshot.get("shadow_assignment"))
        if not oracle_assignment and not policy_assignment:
            continue
        policy_wait = assignment_wait(snapshot, policy_assignment)
        rows.append(
            {
                "time": float(snapshot.get("time", 0.0)),
                "candidate_count": int(snapshot.get("candidate_count", 0)),
                "evaluated": evaluated,
                "oracle_wait": oracle_wait,
                "policy_wait": policy_wait,
                "extra_wait": policy_wait - oracle_wait,
                "exact_match": policy_assignment == oracle_assignment,
                "matched_count": len(policy_assignment),
            }
        )
    if not rows:
        return {"policy": policy, "seed": seed, "snapshots": 0}
    return {
        "policy": policy,
        "seed": seed,
        "snapshots": len(rows),
        "mean_candidate_count": mean([row["candidate_count"] for row in rows]),
        "mean_evaluated_assignments": mean([row["evaluated"] for row in rows]),
        "assignment_exact_match_rate": mean([float(row["exact_match"]) for row in rows]),
        "mean_oracle_wait_per_snapshot": mean([row["oracle_wait"] for row in rows]),
        "mean_policy_wait_per_snapshot": mean([row["policy_wait"] for row in rows]),
        "mean_extra_wait_per_snapshot": mean([row["extra_wait"] for row in rows]),
        "total_oracle_wait": sum(row["oracle_wait"] for row in rows),
        "total_policy_wait": sum(row["policy_wait"] for row in rows),
        "total_extra_wait": sum(row["extra_wait"] for row in rows),
    }


def aggregate(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    out = []
    for policy in POLICIES:
        group = [row for row in rows if row.get("policy") == policy and int(row.get("snapshots", 0)) > 0]
        if not group:
            continue
        summary = {"policy": policy, "seeds": len(group)}
        for key in [
            "snapshots",
            "mean_candidate_count",
            "mean_evaluated_assignments",
            "assignment_exact_match_rate",
            "mean_oracle_wait_per_snapshot",
            "mean_policy_wait_per_snapshot",
            "mean_extra_wait_per_snapshot",
            "total_oracle_wait",
            "total_policy_wait",
            "total_extra_wait",
        ]:
            values = [float(row.get(key, float("nan"))) for row in group]
            summary[key] = mean(values)
            summary[f"{key}_sem"] = sem(values)
        out.append(summary)
    return out


def write_outputs(rows: list[dict[str, object]], summary: list[dict[str, object]]) -> None:
    detail_path = ANALYSIS / "maassim_nearest_optimality_by_seed.csv"
    with detail_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    summary_path = ANALYSIS / "maassim_nearest_optimality_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        writer.writerows(summary)
    lines = [
        "# MaaSSim Nearest-Optimality Diagnostic",
        "",
        "Compares each policy's controlled assignment against an oracle that minimizes immediate pickup wait over the same candidate pairs in each snapshot.",
        "",
        "| Policy | Seeds | Exact-match rate | Extra wait / snapshot | Candidate pairs | Evaluated assignments | Total extra wait |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(
            "| {policy} | {seeds} | {match:.3f} | {extra:.2f} +/- {extrasem:.2f} | {cand:.2f} | {evals:.2f} | {total:.1f} |".format(
                policy=LABELS.get(str(row["policy"]), str(row["policy"])),
                seeds=row["seeds"],
                match=float(row["assignment_exact_match_rate"]),
                extra=float(row["mean_extra_wait_per_snapshot"]),
                extrasem=float(row["mean_extra_wait_per_snapshot_sem"]),
                cand=float(row["mean_candidate_count"]),
                evals=float(row["mean_evaluated_assignments"]),
                total=float(row["total_extra_wait"]),
            )
        )
    best = min(summary, key=lambda row: float(row["mean_extra_wait_per_snapshot"]))
    lines.extend(
        [
            "",
            f"Closest to immediate wait oracle: `{LABELS.get(str(best['policy']), str(best['policy']))}` with extra wait per snapshot `{float(best['mean_extra_wait_per_snapshot']):.2f}`.",
        ]
    )
    (ANALYSIS / "maassim_nearest_optimality_diagnostic.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = [diagnose_policy_seed(policy, seed) for policy in POLICIES for seed in SEEDS]
    summary = aggregate(rows)
    write_outputs(rows, summary)
    print(json.dumps({"rows": len(rows), "summary_rows": len(summary)}, indent=2))


if __name__ == "__main__":
    main()