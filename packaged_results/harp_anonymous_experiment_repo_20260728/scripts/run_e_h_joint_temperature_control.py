"""Run the fixed E-H rho=0 trajectory gate and Joint temperature control."""

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
BASELINE = (
    ROOT
    / "analysis"
    / "e_h_maassim_grouped_prior"
    / "k20_deterministic_likelihood_crn"
    / "e_h_rho1p0_g4_n8_m2_s20.npz"
)
OUT = (
    ROOT
    / "analysis"
    / "e_h_maassim_grouped_prior"
    / "k20_joint_temperature_control"
    / "e_h_joint_temperature_control.json"
)
ALPHAS = (0.25, 0.50, 0.75, 1.00)
SEEDS = 20
T_CRITICAL_95 = 2.093


def run_cell(seed: int, rho: float, alpha: float) -> Trace:
    return run_seed(
        source_root=SOURCE_ROOT,
        seed=seed,
        rho=rho,
        group_size=4,
        n=8,
        m=2,
        k=20,
        strength=0.0,
        likelihood_mode="deterministic-rule",
        joint_alpha=alpha,
        common_random_numbers=True,
    )


def summary(values: list[float]) -> dict[str, float]:
    data = np.asarray(values, dtype=float)
    mean = float(data.mean())
    sem = float(data.std(ddof=1) / math.sqrt(len(data)))
    half_width = T_CRITICAL_95 * sem
    return {
        "mean": mean,
        "sem": sem,
        "ci95_low": mean - half_width,
        "ci95_high": mean + half_width,
    }


def trace_regret(trace: Trace, arm: str) -> float:
    return float(trace.regret_traces[arm][-1])


def mean_hit(trace: Trace, arm: str) -> float:
    return float(np.nanmean(np.asarray(trace.assigned_type_hit_traces[arm], dtype=float)))


def assert_alpha_one_baseline(traces: list[Trace]) -> dict[str, bool]:
    payload = np.load(BASELINE, allow_pickle=False)
    current = {
        "action_traces": [json.dumps(trace.actions) for trace in traces],
        "utility_traces": [json.dumps(trace.utility_traces) for trace in traces],
        "regret_traces": [json.dumps(trace.regret_traces) for trace in traces],
    }
    result = {}
    for name, values in current.items():
        result[name] = values == [str(value) for value in payload[name].tolist()]
        if not result[name]:
            raise AssertionError(f"alpha=1 changed deterministic baseline {name}")
    return result


def main() -> None:
    rho0_traces = [run_cell(seed, rho=0.0, alpha=1.0) for seed in range(SEEDS)]
    rho0_action_mismatches = sum(
        joint != harp
        for trace in rho0_traces
        for joint, harp in zip(trace.actions["joint"], trace.actions["harp"])
    )
    rho0_utility_mismatches = sum(
        joint != harp
        for trace in rho0_traces
        for joint, harp in zip(trace.utility_traces["joint"], trace.utility_traces["harp"])
    )
    rho0_regret_mismatches = sum(
        joint != harp
        for trace in rho0_traces
        for joint, harp in zip(trace.regret_traces["joint"], trace.regret_traces["harp"])
    )
    rho0_gaps = [trace_regret(trace, "harp") - trace_regret(trace, "joint") for trace in rho0_traces]
    if rho0_action_mismatches or rho0_utility_mismatches or rho0_regret_mismatches or any(rho0_gaps):
        raise AssertionError("rho=0 Joint/HARP trajectory gate failed")

    alpha_traces = {
        alpha: [run_cell(seed, rho=1.0, alpha=alpha) for seed in range(SEEDS)]
        for alpha in ALPHAS
    }
    baseline_checks = assert_alpha_one_baseline(alpha_traces[1.0])
    reference_harp_s = [trace.regret_traces["harp_s"] for trace in alpha_traces[1.0]]
    temperature_rows = []
    for alpha in ALPHAS:
        traces = alpha_traces[alpha]
        if [trace.regret_traces["harp_s"] for trace in traces] != reference_harp_s:
            raise AssertionError(f"alpha={alpha} changed HARP-S regret traces")
        harp_s_minus_joint = [
            trace_regret(trace, "harp_s") - trace_regret(trace, "joint")
            for trace in traces
        ]
        harp_minus_joint = [
            trace_regret(trace, "harp") - trace_regret(trace, "joint")
            for trace in traces
        ]
        temperature_rows.append(
            {
                "alpha": alpha,
                "harp_s_minus_joint": summary(harp_s_minus_joint),
                "harp_minus_joint": summary(harp_minus_joint),
                "joint_le_harp_s_seed_count": int(
                    sum(trace_regret(trace, "joint") <= trace_regret(trace, "harp_s") for trace in traces)
                ),
                "joint_harp_s_action_mismatch_rounds": int(
                    sum(
                        joint != harp_s
                        for trace in traces
                        for joint, harp_s in zip(trace.actions["joint"], trace.actions["harp_s"])
                    )
                ),
                "joint_assigned_type_hit": summary([mean_hit(trace, "joint") for trace in traces]),
                "joint_final_assigned_type_hit": summary(
                    [float(trace.assigned_type_hit_traces["joint"][-1]) for trace in traces]
                ),
            }
        )

    cold_traces = alpha_traces[0.25]
    unit_traces = alpha_traces[1.0]
    profile_difference_rounds = sum(
        cold != unit
        for cold_trace, unit_trace in zip(cold_traces, unit_traces)
        for cold, unit in zip(
            cold_trace.sampled_profile_traces["joint"],
            unit_trace.sampled_profile_traces["joint"],
        )
    )
    profile_difference_seed_count = sum(
        cold_trace.sampled_profile_traces["joint"] != unit_trace.sampled_profile_traces["joint"]
        for cold_trace, unit_trace in zip(cold_traces, unit_traces)
    )
    reverse_gate = {
        "alpha_low": 0.25,
        "alpha_reference": 1.0,
        "profile_difference_rounds": int(profile_difference_rounds),
        "profile_difference_seed_count": int(profile_difference_seed_count),
        "total_rounds": SEEDS * 20,
        "passed": profile_difference_rounds > 0,
        "alpha1_shared_support_size_min": int(
            min(min(trace.joint_shared_support_size_pre) for trace in unit_traces)
        ),
        "alpha1_shared_support_size_max": int(
            max(max(trace.joint_shared_support_size_pre) for trace in unit_traces)
        ),
        "alpha1_positive_probability_ratio_max": float(
            max(max(trace.joint_shared_positive_ratio_pre) for trace in unit_traces)
        ),
    }

    payload = {
        "config": {
            "rho0_gate": {"rho": 0.0, "g": 4, "n": 8, "m": 2, "K": 20, "seeds": SEEDS},
            "temperature": {
                "rho": 1.0,
                "g": 4,
                "n": 8,
                "m": 2,
                "K": 20,
                "seeds": SEEDS,
                "alphas": list(ALPHAS),
            },
            "likelihood_mode": "deterministic-rule",
        },
        "rho0_trajectory_gate": {
            "action_mismatch_rounds": rho0_action_mismatches,
            "utility_mismatch_transitions": rho0_utility_mismatches,
            "regret_mismatch_transitions": rho0_regret_mismatches,
            "harp_minus_joint": summary(rho0_gaps),
        },
        "alpha1_baseline_exact": baseline_checks,
        "temperature_reverse_gate": reverse_gate,
        "temperature": temperature_rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    if not reverse_gate["passed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()