"""Pure trace analysis for the exploratory E-H K=20 mechanism finding."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "analysis" / "e_h_maassim_grouped_prior" / "k20"
ARMS = ("oracle", "joint", "harp", "harp_s")
T95 = 2.093
PRIOR_TRUE_MASS = 1.0 / 16.0


def estimate(values: list[float]) -> dict[str, float | int]:
    data = np.asarray(values, dtype=float)
    mean = float(data.mean())
    sem = float(data.std(ddof=1) / math.sqrt(len(data))) if len(data) > 1 else 0.0
    return {
        "n": len(data),
        "mean": mean,
        "sem": sem,
        "ci95_low": mean - T95 * sem,
        "ci95_high": mean + T95 * sem,
    }


def increments(values: list[float]) -> list[float]:
    data = np.asarray(values, dtype=float)
    return np.diff(np.concatenate(([0.0], data))).tolist()


def load_json_traces(payload: np.lib.npyio.NpzFile, name: str) -> list[dict]:
    return [json.loads(str(value)) for value in payload[name].tolist()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    payload = np.load(root / "e_h_rho1p0_g4_n8_m2_s20.npz", allow_pickle=False)
    action_traces = load_json_traces(payload, "action_traces")
    regret_traces = load_json_traces(payload, "regret_traces")
    marginal_traces = load_json_traces(payload, "marginal_true_mass_traces")
    round_count = int(payload["K"])
    seed_count = len(action_traces)

    output: dict[str, object] = {
        "experiment": "E-H K=20 exploratory mechanism diagnostics",
        "source": "existing rho=1,g=4,n=8,m=2,K=20 NPZ traces",
        "methodological_status": "exploratory; seeds 0-19 were used during design iteration",
        "seeds": seed_count,
        "K": round_count,
        "coverage": {},
        "joint_belief_reversal": {},
        "regret_curves": {},
        "seed_decomposition": {},
    }
    csv_rows: list[dict[str, object]] = []

    # 1. Distinct drivers assigned at least once over K rounds.
    for arm in ARMS:
        coverage = []
        per_seed = []
        for seed, trace in enumerate(action_traces):
            drivers = {
                int(pair[0])
                for assignment in trace[arm]
                for pair in assignment
            }
            coverage.append(float(len(drivers)))
            per_seed.append({"seed": seed, "distinct_drivers": len(drivers)})
        summary = estimate(coverage)
        summary["min"] = int(min(coverage))
        summary["median"] = float(np.median(coverage))
        summary["max"] = int(max(coverage))
        summary["per_seed"] = per_seed
        output["coverage"][arm] = summary
        csv_rows.append({"section": "coverage", "arm": arm, "round": "all", **{key: value for key, value in summary.items() if key != "per_seed"}})

    # 2. Joint marginal true-persona mass and below-prior events.
    joint_values = np.asarray(
        [[float(value) for value in trace["joint"]] for trace in marginal_traces],
        dtype=float,
    )
    by_round = {}
    for round_index in range(round_count):
        values = joint_values[:, round_index].tolist()
        item = estimate(values)
        item["seeds_below_prior"] = int(np.sum(joint_values[:, round_index] < PRIOR_TRUE_MASS - 1e-15))
        item["seeds_at_or_below_prior"] = int(np.sum(joint_values[:, round_index] <= PRIOR_TRUE_MASS + 1e-15))
        by_round[str(round_index + 1)] = item
        csv_rows.append({"section": "joint_belief", "arm": "joint", "round": round_index + 1, **item})
    ever_below = np.any(joint_values < PRIOR_TRUE_MASS - 1e-15, axis=1)
    first_below = [
        int(np.where(joint_values[seed] < PRIOR_TRUE_MASS - 1e-15)[0][0] + 1)
        if ever_below[seed] else None
        for seed in range(seed_count)
    ]
    output["joint_belief_reversal"] = {
        "uniform_prior": PRIOR_TRUE_MASS,
        "seeds_ever_below_prior": int(ever_below.sum()),
        "fraction_ever_below_prior": float(ever_below.mean()),
        "first_below_round_by_seed": first_below,
        "minimum_by_seed": joint_values.min(axis=1).tolist(),
        "rounds": by_round,
    }

    # 3. Cumulative and incremental regret curves plus paired gaps.
    for arm in ARMS:
        matrix = np.asarray(
            [[float(value) for value in trace[arm]] for trace in regret_traces],
            dtype=float,
        )
        cumulative = {}
        incremental = {}
        increment_matrix = np.asarray([increments(row.tolist()) for row in matrix], dtype=float)
        for round_index in range(round_count):
            cumulative[str(round_index + 1)] = estimate(matrix[:, round_index].tolist())
            incremental[str(round_index + 1)] = estimate(increment_matrix[:, round_index].tolist())
            csv_rows.append({"section": "cumulative_regret", "arm": arm, "round": round_index + 1, **cumulative[str(round_index + 1)]})
            csv_rows.append({"section": "regret_increment", "arm": arm, "round": round_index + 1, **incremental[str(round_index + 1)]})
        output["regret_curves"][arm] = {"cumulative": cumulative, "incremental": incremental}

    for target in ("harp", "harp_s"):
        paired = {}
        for round_index in range(round_count):
            values = [
                float(regret_traces[seed][target][round_index])
                - float(regret_traces[seed]["joint"][round_index])
                for seed in range(seed_count)
            ]
            paired[str(round_index + 1)] = estimate(values)
        output["regret_curves"][f"{target}_minus_joint"] = paired

    # 4. Final per-seed HARP-S minus Joint decomposition.
    gaps = np.asarray(
        [
            float(regret_traces[seed]["harp_s"][-1])
            - float(regret_traces[seed]["joint"][-1])
            for seed in range(seed_count)
        ],
        dtype=float,
    )
    ordered = np.argsort(gaps)
    advantage = np.maximum(-gaps, 0.0)
    total_advantage = float(advantage.sum())
    top3 = np.argsort(advantage)[-3:][::-1]
    output["seed_decomposition"] = {
        "estimate": estimate(gaps.tolist()),
        "median": float(np.median(gaps)),
        "std": float(gaps.std(ddof=1)),
        "min": float(gaps.min()),
        "max": float(gaps.max()),
        "quantiles": {
            "q10": float(np.quantile(gaps, 0.10)),
            "q25": float(np.quantile(gaps, 0.25)),
            "q50": float(np.quantile(gaps, 0.50)),
            "q75": float(np.quantile(gaps, 0.75)),
            "q90": float(np.quantile(gaps, 0.90)),
        },
        "counts": {
            "harp_s_better_negative": int(np.sum(gaps < -1e-12)),
            "tie": int(np.sum(np.abs(gaps) <= 1e-12)),
            "harp_s_worse_positive": int(np.sum(gaps > 1e-12)),
        },
        "per_seed": [{"seed": int(seed), "harp_s_minus_joint": float(gaps[seed])} for seed in range(seed_count)],
        "sorted_seeds": [int(seed) for seed in ordered],
        "top3_advantage_seeds": [int(seed) for seed in top3],
        "top3_share_of_total_harp_s_advantage": float(advantage[top3].sum() / total_advantage) if total_advantage > 0 else 0.0,
        "leave_one_out_mean_min": float(min(np.delete(gaps, seed).mean() for seed in range(seed_count))),
        "leave_one_out_mean_max": float(max(np.delete(gaps, seed).mean() for seed in range(seed_count))),
    }

    json_path = root / "e_h_mechanism_diagnostics.json"
    json_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    csv_path = root / "e_h_mechanism_diagnostics.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=sorted({key for row in csv_rows for key in row}))
        writer.writeheader()
        writer.writerows(csv_rows)
    md_path = root / "e_h_mechanism_diagnostics.md"
    md_path.write_text(
        "# E-H K=20 exploratory mechanism diagnostics\n\n"
        "Computed only from existing NPZ traces; no arm was rerun.\n",
        encoding="utf-8",
    )
    manifest_path = root / "e_h_mechanism_diagnostics_sha256.json"
    artifacts = [
        {"path": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in (json_path, csv_path, md_path)
    ]
    manifest_path.write_text(json.dumps({"schema_version": "1.0", "artifacts": artifacts}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "json": str(json_path), "csv": str(csv_path)}, indent=2))


if __name__ == "__main__":
    main()
