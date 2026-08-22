"""Grid-search placeholder CourierDispatch coefficients.

The goal is not to fit real-world dispatch data. It is to pick analytic-tier
defaults where hidden rules are identifiable inside the episode budget but not
so trivial that the verbal-belief surrogate saturates.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_courier_dispatch.demo_dispatch import run_episode, summarize  # noqa: E402


ANALYSIS_DIR = ROOT / "analysis" / "courier_dispatch"


def parse_float_list(raw: str) -> list[float]:
    return [float(item.strip()) for item in raw.split(",") if item.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--penalty-scales", type=parse_float_list, default=parse_float_list("1.0,1.25,1.5,1.75,2.0"))
    parser.add_argument("--taus", type=parse_float_list, default=parse_float_list("0.35,0.5,0.7,0.9"))
    parser.add_argument("--seeds", type=int, default=2)
    parser.add_argument("--horizon", type=int, default=30)
    parser.add_argument("--candidates", type=int, default=3)
    args = parser.parse_args()

    rows = []
    for penalty in args.penalty_scales:
        for tau in args.taus:
            sim_rows = []
            for seed in range(args.seeds):
                for method, beta in [("pact", 0.0), ("pact_plus", 0.25), ("atom_tom1", 0.0), ("atom_tom0", 0.0)]:
                    sim_rows.extend(
                        run_episode(
                            method,
                            beta,
                            seed=seed,
                            n_agents=3,
                            rule_count=4,
                            horizon=args.horizon,
                            tau=tau,
                            penalty_scale=penalty,
                            home_scale=1.2,
                            menu_friction=0.2,
                            candidate_count=args.candidates,
                            couple_lambda=0.0,
                        )
                    )
            summary = summarize(sim_rows)
            by_method = {(row["method"], row["beta"]): row for row in summary}
            pact = by_method[("pact", 0.0)]
            plus = by_method[("pact_plus", 0.25)]
            belief = by_method[("atom_tom1", 0.0)]
            greedy = by_method[("atom_tom0", 0.0)]
            row = {
                "penalty_scale": penalty,
                "tau": tau,
                "pact_ptrue": pact["final_mean_true_tuple_posterior"],
                "pact_rule_acc": pact["final_mean_rule_marginal_accuracy"],
                "pact_reward": pact["final_mean_cumulative_reward"],
                "pact_plus_ptrue": plus["final_mean_true_tuple_posterior"],
                "pact_plus_rule_acc": plus["final_mean_rule_marginal_accuracy"],
                "pact_plus_reward": plus["final_mean_cumulative_reward"],
                "atom_tom1_rule_acc": belief["final_mean_rule_marginal_accuracy"],
                "atom_tom1_reward": belief["final_mean_cumulative_reward"],
                "atom_tom0_reward": greedy["final_mean_cumulative_reward"],
            }
            row["pact_minus_atom_tom1_acc"] = row["pact_rule_acc"] - row["atom_tom1_rule_acc"]
            row["pact_reward_margin_vs_atom_tom1"] = row["pact_reward"] - row["atom_tom1_reward"]
            row["not_trivial"] = bool(0.75 <= row["pact_rule_acc"] <= 0.995)
            row["clear_pact_advantage"] = bool(row["pact_minus_atom_tom1_acc"] >= 0.20)
            rows.append(row)

    def score(row: dict[str, float | bool]) -> float:
        target_acc = 0.92
        return (
            3.0 * float(row["clear_pact_advantage"])
            + 2.0 * float(row["not_trivial"])
            - abs(float(row["pact_rule_acc"]) - target_acc)
            + 0.1 * float(row["pact_reward_margin_vs_atom_tom1"])
        )

    best = max(rows, key=score)
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = ANALYSIS_DIR / "courier_dispatch_calibration_sweep.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    payload = {
        "purpose": "Choose placeholder analytic coefficients where PACT learns hidden rule tuples but A-ToM-1 remains below PACT.",
        "grid": {"penalty_scales": args.penalty_scales, "taus": args.taus, "seeds": args.seeds, "horizon": args.horizon},
        "best": best,
        "rows": rows,
    }
    json_path = ANALYSIS_DIR / "courier_dispatch_calibration_sweep.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"json": str(json_path.relative_to(ROOT)), "csv": str(csv_path.relative_to(ROOT)), "best": best}, indent=2))


if __name__ == "__main__":
    main()