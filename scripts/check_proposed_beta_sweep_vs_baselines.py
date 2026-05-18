from __future__ import annotations

from pathlib import Path

import numpy as np

ROOT = Path("results/cloudgpt")
MODELS = {
    "DeepSeek-V3.2": "DeepSeek_V3_2",
    "gpt-5.4-nano": "gpt_5_4_nano_20260317",
    "Kimi-K2.6": "Kimi_K2_6",
    "Llama-4-Maverick": "Llama_4_Maverick_17B_128E_Instruct_FP8",
}
BETAS = ["beta0", "beta0p05", "beta0p1", "beta0p25", "beta0p5", "beta0p75", "beta1", "beta1p5"]
EXTERNAL_ALGORITHMS = ["atom_tom0", "atom_tom1", "atom_tom2", "atom_adaptive_ftl", "atom_adaptive_hedge", "econ_bne"]


def rows(path: Path, group: str):
    data = np.load(path, allow_pickle=True)
    algorithms = [str(value) for value in data["algorithms"]]
    cumulative = np.asarray(data["cumulative_regret"], dtype=float)
    out = []
    for index, algorithm in enumerate(algorithms):
        final = cumulative[index, :, -1]
        out.append({"group": group, "algorithm": algorithm, "mean": float(final.mean()), "std": float(final.std(ddof=0)), "path": path})
    return out


def main() -> None:
    print("model\tbest_hpsmg_plus_beta\tbest_hpsmg_plus\tbest_hpsmg_plus_std\tbest_baseline_group\tbest_baseline\tbest_baseline_mean\tmargin\tstatus")
    for model, slug in MODELS.items():
        proposed_candidates = []
        baseline_candidates = []
        for beta in BETAS:
            path = ROOT / f"E2_{slug}_c19_{beta}.npz"
            if not path.exists():
                continue
            for row in rows(path, "native"):
                if row["algorithm"] == "hpsmg_plus":
                    proposed_candidates.append(row | {"beta": beta})
                elif row["algorithm"] != "oracle":
                    baseline_candidates.append(row | {"beta": beta})

        prompted_path = ROOT / f"E2_llm_baselines_{slug}_c19_K20_s5.npz"
        if prompted_path.exists():
            baseline_candidates.extend(rows(prompted_path, "prompted"))

        merged_external = ROOT / f"E2_external_llm_baselines_{slug}_c19_K20_s5.npz"
        if merged_external.exists():
            baseline_candidates.extend(rows(merged_external, "external"))
        else:
            for algorithm in EXTERNAL_ALGORITHMS:
                shard = ROOT / "shards" / f"E2_external_{slug}_c19_K20_s5_{algorithm}.npz"
                if shard.exists():
                    baseline_candidates.extend(row for row in rows(shard, "external_shard") if row["algorithm"] == algorithm)

        proposed = min(proposed_candidates, key=lambda row: row["mean"])
        baseline = min(baseline_candidates, key=lambda row: row["mean"])
        margin = baseline["mean"] - proposed["mean"]
        print(
            f"{model}\t{proposed['beta']}\t{proposed['mean']:.4f}\t{proposed['std']:.4f}\t"
            f"{baseline['group']}\t{baseline['algorithm']}\t{baseline['mean']:.4f}\t{margin:.4f}\t"
            f"{'PASS' if margin > 0 else 'VIOLATION'}"
        )


if __name__ == "__main__":
    main()
