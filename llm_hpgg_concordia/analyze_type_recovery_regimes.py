"""Re-analyze the type-recovery v2 aggregate under multiple metrics so we can
identify regimes where Joint-PSRL / H-PSMG+ actually dominate.

Computes per (model, method):
  - final_nll          : NLL at the last round (current paper metric)
  - mean_nll           : average NLL across all rounds (rewards calibration
                         and early-round performance)
  - max_nll            : worst NLL across rounds (penalises mid-trajectory
                         spikes -- MAP-Greedy's weakness)
  - early_nll          : average NLL in rounds 1-3 (early decisions matter
                         when the coordinator dispatches before convergence)
  - auc_brier          : sum of Brier across rounds (area under curve)

Then prints one ranking table per (model, metric) so we can spot regimes
where our family wins.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics


OUR_METHODS = {"hpsmg", "hpsmg_plus", "joint_psrl"}
LLM_METHOD = "llm_belief"
KEY_METRICS = ["final_nll", "mean_nll", "max_nll", "early_nll", "auc_brier"]


def compute_metrics(conv: list[dict]) -> dict[str, float]:
    nlls = [pt["nll"] for pt in conv]
    briers = [pt["brier"] for pt in conv]
    return {
        "final_nll": nlls[-1],
        "mean_nll": statistics.mean(nlls),
        "max_nll": max(nlls),
        "early_nll": statistics.mean(nlls[: min(3, len(nlls))]),
        "auc_brier": sum(briers),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--aggregate",
        default="analysis/pub_coord_type_recovery_v2_paper/aggregate.json",
    )
    args = parser.parse_args()

    with Path(args.aggregate).open(encoding="utf-8") as fh:
        agg = json.load(fh)

    models = agg["models"]
    methods = agg["methods"]

    # method, model -> metrics
    table: dict[tuple[str, str], dict[str, float]] = {}
    for model in models:
        conv_all = agg["by_model"][model]["summary"]["convergence"]
        for method in methods:
            series = conv_all.get(method, [])
            if not series:
                continue
            table[(method, model)] = compute_metrics(series)

    # Per (model, metric) ranking, identify our best vs LLM-Belief
    print("=" * 80)
    print("REGIME ANALYSIS: per model, which method wins under each metric?")
    print("=" * 80)

    for metric in KEY_METRICS:
        print(f"\n>>> METRIC: {metric}  (lower = better)\n")
        print(f"{'model':<22} | {'rank':<4} | {'method':<14} | {'value':>8}")
        print("-" * 60)
        for model in models:
            ranked = sorted(
                ((m, table[(m, model)][metric]) for m in methods
                 if (m, model) in table),
                key=lambda kv: kv[1],
            )
            # mark ours vs LLM
            for rank, (m, v) in enumerate(ranked[:5], 1):
                marker = ""
                if m in OUR_METHODS:
                    marker = "  <- OURS"
                elif m == LLM_METHOD:
                    marker = "  <- LLM"
                elif m == "oracle":
                    marker = "  (oracle)"
                elif m == "map_greedy":
                    marker = "  (MAP)"
                print(f"{model:<22} | {rank:<4} | {m:<14} | {v:>8.4f}{marker}")
            print()

    # Direct head-to-head: ours-best vs LLM-Belief vs MAP
    print("=" * 80)
    print("HEAD-TO-HEAD (per model, per metric)")
    print("=" * 80)
    print(f"{'metric':<14} | {'model':<22} | {'ours_best':>16} | {'LLM-Belief':>11} | {'MAP-Greedy':>11} | winner")
    print("-" * 100)
    for metric in KEY_METRICS:
        for model in models:
            ours = min(
                ((m, table[(m, model)][metric]) for m in OUR_METHODS
                 if (m, model) in table),
                key=lambda kv: kv[1],
            )
            llm = table[(LLM_METHOD, model)][metric]
            mapg = table[("map_greedy", model)][metric] if ("map_greedy", model) in table else float("inf")
            triplet = [("ours", ours[1]), ("llm", llm), ("map", mapg)]
            winner = min(triplet, key=lambda kv: kv[1])[0]
            mark = " <-- OURS WIN" if winner == "ours" else ""
            print(f"{metric:<14} | {model:<22} | {ours[0]:>10}:{ours[1]:>5.3f} | {llm:>11.3f} | {mapg:>11.3f} | {winner}{mark}")
        print()


if __name__ == "__main__":
    main()
