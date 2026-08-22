"""Audit E-A source artifacts and export per-seed provenance.

The recovered historical external-baseline runs already consumed rewards from
the same c19 calibration tensor in their public history, but their runner used
algorithm-specific RNG seeds.  They are therefore an analytic-outcome control,
not the requested matched-seed control.  This script makes that distinction
machine-readable and refuses to label the historical comparison as E-A.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np


MODEL_FILES = {
    "DeepSeek-V3.2": (
        "E2_DeepSeek_V3_2_c19_beta0p25.npz",
        "E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz",
    ),
    "GPT-5.4-nano": (
        "E2_gpt_5_4_nano_20260317_c19_beta0p25.npz",
        "E2_external_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5.npz",
    ),
    "Kimi-K2.6": (
        "E2_Kimi_K2_6_c19_beta0p25.npz",
        "E2_external_llm_baselines_Kimi_K2_6_c19_K20_s5.npz",
    ),
    "Llama-4-Maverick": (
        "E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p25.npz",
        "E2_external_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5.npz",
    ),
}
EXTERNAL_CANONICAL = (
    "atom_tom0",
    "atom_tom1",
    "atom_tom2",
    "atom_adaptive_ftl",
    "atom_adaptive_hedge",
    "econ_bne",
)


def true_types_for_seed(seed: int) -> str:
    values = np.random.default_rng(seed).integers(0, 4, size=3)
    return "|".join(str(int(value)) for value in values)


def mean_sem(values: list[float]) -> tuple[float, float]:
    array = np.asarray(values, dtype=float)
    return float(array.mean()), float(array.std(ddof=1) / math.sqrt(len(array))) if len(array) > 1 else 0.0


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--git-commit", default="historical_snapshot")
    args = parser.parse_args()

    rows: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []
    for model, (native_name, external_name) in MODEL_FILES.items():
        native = np.load(args.source_dir / native_name, allow_pickle=True)
        external = np.load(args.source_dir / external_name, allow_pickle=True)
        native_algorithms = [str(value) for value in native["algorithms"]]
        external_algorithms = [str(value) for value in external["algorithms"]]
        pact_index = native_algorithms.index("hpsmg_plus")
        pact_final = np.asarray(native["cumulative_regret"], dtype=float)[pact_index, :, -1]
        native_final = np.asarray(native["cumulative_regret"], dtype=float)[:, :, -1]
        family_means = {
            algorithm: float(native_final[native_algorithms.index(algorithm)].mean())
            for algorithm in ("hpsmg", "hpsmg_plus")
        }
        best_family_method = min(family_means, key=family_means.get)
        best_family_values = native_final[native_algorithms.index(best_family_method)]
        external_final = np.asarray(external["cumulative_regret"], dtype=float)[:, :, -1]

        for seed_index, value in enumerate(pact_final):
            rows.append(
                {
                    "model": model,
                    "family": "PACT-family",
                    "algorithm": "hpsmg_plus",
                    "seed_index": seed_index,
                    "actual_rng_seed": seed_index,
                    "true_types": true_types_for_seed(seed_index),
                    "final_cumulative_regret": float(value),
                    "analytic_outcome_history": True,
                    "matched_to_pact_seed": True,
                    "source_file": native_name,
                }
            )
        for algorithm_index, algorithm in enumerate(external_algorithms):
            canonical_index = EXTERNAL_CANONICAL.index(algorithm)
            for seed_position, seed_index in enumerate(np.asarray(external["seed_indices"], dtype=int)):
                actual_seed = 120_000 + 10_000 * canonical_index + int(seed_index)
                rows.append(
                    {
                        "model": model,
                        "family": "LLM-coordination",
                        "algorithm": algorithm,
                        "seed_index": int(seed_index),
                        "actual_rng_seed": actual_seed,
                        "true_types": true_types_for_seed(actual_seed),
                        "final_cumulative_regret": float(external_final[algorithm_index, seed_position]),
                        "analytic_outcome_history": True,
                        "matched_to_pact_seed": False,
                        "source_file": external_name,
                    }
                )

        external_means = {algorithm: float(external_final[index].mean()) for index, algorithm in enumerate(external_algorithms)}
        best_algorithm = min(external_means, key=external_means.get)
        pact_mean, pact_sem = mean_sem(pact_final.tolist())
        best_values = external_final[external_algorithms.index(best_algorithm)].tolist()
        best_mean, best_sem = mean_sem(best_values)
        family_mean, family_sem = mean_sem(best_family_values.tolist())
        summaries.append(
            {
                "model": model,
                "status": "historical analytic-outcome comparison; NOT matched-seed E-A",
                "pact_plus_regret_mean": pact_mean,
                "pact_plus_regret_sem": pact_sem,
                "best_pact_family_method": best_family_method,
                "best_pact_family_regret_mean": family_mean,
                "best_pact_family_regret_sem": family_sem,
                "best_baseline": best_algorithm,
                "best_baseline_regret_mean": best_mean,
                "best_baseline_regret_sem": best_sem,
                "historical_ratio": best_mean / pact_mean if pact_mean > 0.0 else float("inf"),
                "historical_best_family_ratio": best_mean / family_mean if family_mean > 0.0 else float("inf"),
                "same_analytic_reward_history_interface": True,
                "matched_type_and_initial_state": False,
                "condition_b_live_pact_available": False,
            }
        )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.out_dir / "e_a_historical_per_seed_provenance.csv", rows)
    write_csv(args.out_dir / "e_a_historical_summary.csv", summaries)
    metadata = {
        "experiment": "E-A source audit",
        "git_commit": args.git_commit,
        "source_dir": str(args.source_dir),
        "result": "blocked",
        "reason": (
            "Historical external baselines consumed analytic c19 rewards in their prompt history, "
            "but used algorithm-specific true-type RNG seeds. The retained c19 calibration tensors "
            "and baseline caches are absent, so histories cannot be rerun counterfactually without new LLM calls."
        ),
        "condition_a_complete": False,
        "condition_b_complete": False,
        "condition_a_interface_decision": (
            "Use the existing recent_public_history/history rewards field rather than a bypass; "
            "the historical runners already inject analytic realized outcomes through this interface."
        ),
        "paper_action": "retain evaluation-asymmetry caveat; do not claim a matched-likelihood result",
    }
    (args.out_dir / "e_a_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# E-A Matched-Likelihood Audit",
        "",
        "**Status: blocked; no matched-likelihood result is claimed.**",
        "",
        "The recovered historical external baselines already received analytic c19 rewards in `recent_public_history`, "
        "but their runner used algorithm-specific RNG seeds. Thus they do not share PACT's type profiles or initial states. "
        "The raw c19 calibration tensors and LLM response caches were not retained, so a valid matched rerun requires fresh model calls.",
        "",
        "| model | PACT+ | best PACT-family | best historical baseline | family ratio | matched? |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in summaries:
        lines.append(
            f"| {row['model']} | {float(row['pact_plus_regret_mean']):.3f} $\\pm$ {float(row['pact_plus_regret_sem']):.3f} | "
            f"{row['best_pact_family_method']} {float(row['best_pact_family_regret_mean']):.3f} $\\pm$ {float(row['best_pact_family_regret_sem']):.3f} | "
            f"{row['best_baseline']} {float(row['best_baseline_regret_mean']):.3f} $\\pm$ {float(row['best_baseline_regret_sem']):.3f} | "
            f"{float(row['historical_best_family_ratio']):.2f}$\\times$ | no |"
        )
    lines.extend(
        [
            "",
            "No appendix matched-control table should be added from these rows. They are retained only to expose provenance and to prevent the old aggregate from being mislabeled as E-A.",
        ]
    )
    (args.out_dir / "e_a_matched_likelihood_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))
    for row in summaries:
        print(
            f"{row['model']}: PACT+={float(row['pact_plus_regret_mean']):.3f}, "
            f"best-family={row['best_pact_family_method']} {float(row['best_pact_family_regret_mean']):.3f}, "
            f"best={row['best_baseline']} {float(row['best_baseline_regret_mean']):.3f}, "
            f"family-ratio={float(row['historical_best_family_ratio']):.2f}x, matched=false"
        )


if __name__ == "__main__":
    main()
