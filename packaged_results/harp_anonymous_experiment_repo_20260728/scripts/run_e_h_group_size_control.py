"""Run the preregistered E-H g=2 control against the frozen g=4 result."""

from __future__ import annotations

import json
import math
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_e_h_maassim_grouped_prior import Trace, run_seed


SOURCE_ROOT = ROOT / "analysis" / "e_e_maassim_rq2"
G4_ROOT = ROOT / "analysis" / "e_h_maassim_grouped_prior" / "k20_deterministic_crn_confirm_seed20_59"
OUT = ROOT / "analysis" / "e_h_maassim_grouped_prior" / "g2_confirm_seed20_59" / "e_h_group_size_control.json"
SEEDS = tuple(range(20, 60))
T_CRITICAL_95 = 2.02269092


def estimate(values: list[float]) -> dict[str, float | int | bool]:
    data = np.asarray(values, dtype=float)
    mean = float(data.mean())
    sem = float(data.std(ddof=1) / math.sqrt(len(data)))
    half_width = T_CRITICAL_95 * sem
    return {
        "n": len(data),
        "mean": mean,
        "sem": sem,
        "ci95_low": mean - half_width,
        "ci95_high": mean + half_width,
        "ci95_covers_zero": mean - half_width <= 0.0 <= mean + half_width,
    }


def final_regret(trace: Trace, arm: str) -> float:
    return float(trace.regret_traces[arm][-1])


def load_g4_regrets() -> dict[int, dict[str, float]]:
    path = G4_ROOT / "e_h_rho1p0_g4_n8_m2_s40.npz"
    payload = np.load(path, allow_pickle=False)
    result: dict[int, dict[str, float]] = {}
    for seed, arm, regret in zip(payload["seeds"], payload["arms"], payload["cum_regret"]):
        result.setdefault(int(seed), {})[str(arm)] = float(regret)
    if sorted(result) != list(SEEDS):
        raise AssertionError("frozen g=4 seed set does not match the preregistration")
    return result


def arm_summary(regrets: dict[str, list[float]]) -> dict[str, object]:
    harp = np.asarray(regrets["harp"], dtype=float)
    joint = np.asarray(regrets["joint"], dtype=float)
    harp_s = np.asarray(regrets["harp_s"], dtype=float)
    gap = harp - joint
    mean_harp = float(harp.mean())
    return {
        "harp_oracle_regret": estimate(harp.tolist()),
        "joint_oracle_regret": estimate(joint.tolist()),
        "harp_s_oracle_regret": estimate(harp_s.tolist()),
        "harp_minus_joint": estimate(gap.tolist()),
        "harp_s_minus_joint": estimate((harp_s - joint).tolist()),
        "relative_regret_reduction_percent": float(100.0 * gap.mean() / mean_harp),
    }


def main() -> None:
    traces = {
        rho: [
            run_seed(
                source_root=SOURCE_ROOT,
                seed=seed,
                rho=rho,
                group_size=2,
                n=8,
                m=2,
                k=20,
                strength=0.0,
                likelihood_mode="deterministic-rule",
                joint_alpha=1.0,
                common_random_numbers=True,
            )
            for seed in SEEDS
        ]
        for rho in (0.0, 1.0)
    }
    g2_regrets = {
        arm: [final_regret(trace, arm) for trace in traces[1.0]]
        for arm in ("joint", "harp", "harp_s")
    }
    g4_by_seed = load_g4_regrets()
    g4_regrets = {
        arm: [g4_by_seed[seed][arm] for seed in SEEDS]
        for arm in ("joint", "harp", "harp_s")
    }
    g2_gap = np.asarray(g2_regrets["harp"]) - np.asarray(g2_regrets["joint"])
    g4_gap = np.asarray(g4_regrets["harp"]) - np.asarray(g4_regrets["joint"])
    p3_values = (g4_gap - g2_gap).tolist()

    rho0_action_mismatches = sum(
        joint != harp
        for trace in traces[0.0]
        for joint, harp in zip(trace.actions["joint"], trace.actions["harp"])
    )
    rho1_action_mismatches = sum(
        joint != harp_s
        for trace in traces[1.0]
        for joint, harp_s in zip(trace.actions["joint"], trace.actions["harp_s"])
    )
    p3 = estimate(p3_values)
    p3["confirmed"] = bool(float(p3["mean"]) > 0.0 and float(p3["ci95_low"]) > 0.0)
    payload = {
        "config": {
            "seed_start": 20,
            "seed_end": 59,
            "seed_count": 40,
            "rho": [0.0, 1.0],
            "group_sizes": [2, 4],
            "n": 8,
            "m": 2,
            "K": 20,
            "likelihood_mode": "deterministic-rule",
            "common_random_numbers": True,
        },
        "g2": arm_summary(g2_regrets),
        "g4_frozen": arm_summary(g4_regrets),
        "p3_g4_gap_minus_g2_gap": p3,
        "hard_gates": {
            "rho0_joint_harp_action_mismatch_rounds": int(rho0_action_mismatches),
            "rho1_joint_harp_s_action_mismatch_rounds": int(rho1_action_mismatches),
            "total_rounds_per_rho": len(SEEDS) * 20,
        },
    }
    if rho0_action_mismatches or rho1_action_mismatches:
        raise AssertionError("group-size CRN action gate failed")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()