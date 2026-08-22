"""Summarize true shared-type DGP HP-SPGG experiment outputs."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np


BASE = Path("analysis/true_shared_type")


def parse_cell(path: Path) -> tuple[int, int, str]:
    stem = path.stem
    parts = stem.split("_")
    n = int(parts[2][1:])
    k_rounds = int(parts[3][1:])
    tier = "_".join(parts[4:-2])
    return n, k_rounds, tier


def main() -> None:
    by_algorithm: list[dict[str, object]] = []
    comparison: list[dict[str, object]] = []
    for path in sorted(BASE.glob("E1_truesharedtype_n*_K*_*_shared_type.npz")):
        n, k_rounds, tier = parse_cell(path)
        data = np.load(path, allow_pickle=True)
        algorithms = [str(item) for item in data["algorithms"]]
        cumulative_regret = np.asarray(data["cumulative_regret"], dtype=float)
        storage = np.asarray(data["storage"], dtype=int)
        means: dict[str, float] = {}
        sems: dict[str, float] = {}
        stores: dict[str, int] = {}
        for index, algorithm in enumerate(algorithms):
            finals = cumulative_regret[index, :, -1]
            means[algorithm] = float(np.mean(finals))
            sems[algorithm] = float(np.std(finals, ddof=1) / np.sqrt(len(finals))) if len(finals) > 1 else 0.0
            stores[algorithm] = int(storage[index])
            by_algorithm.append(
                {
                    "tier": tier,
                    "n": n,
                    "K": k_rounds,
                    "algorithm": algorithm,
                    "mean_cumulative_regret": means[algorithm],
                    "sem": sems[algorithm],
                    "storage": stores[algorithm],
                    "seeds": int(cumulative_regret.shape[1]),
                    "source": str(path),
                }
            )
        pact = means["hpsmg"]
        uniform = means["joint_psrl_uniform"]
        aware = means["joint_psrl_aware"]
        comparison.append(
            {
                "tier": tier,
                "n": n,
                "K": k_rounds,
                "PACT": pact,
                "JointPSRL_Uniform": uniform,
                "JointPSRL_Aware": aware,
                "PACT_over_Aware": pact / aware if aware > 1e-12 else "NA",
                "Uniform_over_Aware": uniform / aware if aware > 1e-12 else "NA",
                "PACT_storage": stores["hpsmg"],
                "Uniform_storage": stores["joint_psrl_uniform"],
                "Aware_storage": stores["joint_psrl_aware"],
                "Uniform_vs_PACT_storage_ratio": stores["joint_psrl_uniform"] / stores["hpsmg"],
            }
        )

    BASE.mkdir(parents=True, exist_ok=True)
    with (BASE / "summary_by_algorithm.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(by_algorithm[0].keys()))
        writer.writeheader()
        writer.writerows(by_algorithm)
    with (BASE / "summary_comparison.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(comparison[0].keys()))
        writer.writeheader()
        writer.writerows(comparison)
    (BASE / "summary.json").write_text(
        json.dumps({"by_algorithm": by_algorithm, "comparison": comparison}, indent=2),
        encoding="utf-8",
    )
    for row in comparison:
        ratio = row["PACT_over_Aware"]
        ratio_text = "NA" if ratio == "NA" else f"{float(ratio):.2f}x"
        print(
            f"{row['tier']} n={row['n']} K={row['K']}: "
            f"PACT={float(row['PACT']):.3f}, "
            f"Uniform={float(row['JointPSRL_Uniform']):.3f}, "
            f"Aware={float(row['JointPSRL_Aware']):.3f}, "
            f"PACT/Aware={ratio_text}"
        )
    print(f"wrote {BASE / 'summary_comparison.csv'}")


if __name__ == "__main__":
    main()