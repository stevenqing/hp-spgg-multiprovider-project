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

EXTERNAL_ALGORITHMS = [
    "atom_tom0",
    "atom_tom1",
    "atom_tom2",
    "atom_adaptive_ftl",
    "atom_adaptive_hedge",
    "econ_bne",
]


def load_rows(path: Path, group: str) -> list[dict[str, object]]:
    data = np.load(path, allow_pickle=True)
    algorithms = [str(value) for value in data["algorithms"]]
    cumulative = np.asarray(data["cumulative_regret"], dtype=float)
    welfare = np.asarray(data["welfare"], dtype=float)
    rows = []
    for index, algorithm in enumerate(algorithms):
        final = cumulative[index, :, -1]
        rows.append(
            {
                "group": group,
                "algorithm": algorithm,
                "mean": float(final.mean()),
                "std": float(final.std(ddof=0)),
                "welfare": float(welfare[index].mean()),
                "source": path.as_posix(),
            }
        )
    return rows


def main() -> None:
    all_rows: list[dict[str, object]] = []
    violations: list[dict[str, object]] = []

    for model, slug in MODELS.items():
        native_path = ROOT / f"E2_{slug}_c19_beta0p25.npz"
        if not native_path.exists():
            continue
        native_rows = load_rows(native_path, "native")
        proposed = next(row for row in native_rows if row["algorithm"] == "hpsmg_plus")
        candidate_rows = [row for row in native_rows if row["algorithm"] != "oracle"]

        prompted_path = ROOT / f"E2_llm_baselines_{slug}_c19_K20_s5.npz"
        if prompted_path.exists():
            candidate_rows.extend(load_rows(prompted_path, "prompted"))

        merged_external = ROOT / f"E2_external_llm_baselines_{slug}_c19_K20_s5.npz"
        if merged_external.exists():
            candidate_rows.extend(load_rows(merged_external, "external"))
        else:
            for algorithm in EXTERNAL_ALGORITHMS:
                shard_path = ROOT / "shards" / f"E2_external_{slug}_c19_K20_s5_{algorithm}.npz"
                if shard_path.exists():
                    rows = load_rows(shard_path, "external_shard")
                    candidate_rows.extend(row for row in rows if row["algorithm"] == algorithm)

        best_baseline = min(
            (row for row in candidate_rows if row["algorithm"] != "hpsmg_plus"),
            key=lambda row: float(row["mean"]),
        )
        margin = float(best_baseline["mean"]) - float(proposed["mean"])
        status = "PASS" if margin > 0 else "VIOLATION"
        if status != "PASS":
            violations.append({"model": model, "proposed": proposed, "best_baseline": best_baseline, "margin": margin})
        all_rows.append(
            {
                "model": model,
                "proposed_mean": proposed["mean"],
                "proposed_std": proposed["std"],
                "best_baseline_group": best_baseline["group"],
                "best_baseline_algorithm": best_baseline["algorithm"],
                "best_baseline_mean": best_baseline["mean"],
                "best_baseline_std": best_baseline["std"],
                "margin": margin,
                "status": status,
            }
        )

    print("model\tproposed_hpsmg_plus\tproposed_std\tbest_baseline_group\tbest_baseline\tbest_baseline_mean\tbest_baseline_std\tmargin\tstatus")
    for row in all_rows:
        print(
            f"{row['model']}\t{row['proposed_mean']:.4f}\t{row['proposed_std']:.4f}\t"
            f"{row['best_baseline_group']}\t{row['best_baseline_algorithm']}\t"
            f"{row['best_baseline_mean']:.4f}\t{row['best_baseline_std']:.4f}\t"
            f"{row['margin']:.4f}\t{row['status']}"
        )

    if violations:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
