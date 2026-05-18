"""Analyze and plot E4 prior recovery."""

from __future__ import annotations

import argparse
import csv
import glob
import json
from pathlib import Path

import numpy as np


def sem(values: np.ndarray) -> np.ndarray:
    if values.shape[0] <= 1:
        return np.zeros(values.shape[1], dtype=float)
    return np.std(values, axis=0, ddof=1) / np.sqrt(values.shape[0])


def prior_from_path(path: Path, data: np.lib.npyio.NpzFile) -> str:
    if "prior_mode" in data.files:
        return str(data["prior_mode"])
    for mode in ["uniform", "correct", "adversarial"]:
        if mode in path.stem:
            return mode
    return path.stem


def expand_inputs(patterns: list[str]) -> list[str]:
    paths: list[str] = []
    for pattern in patterns:
        matches = sorted(glob.glob(pattern))
        paths.extend(matches if matches else [pattern])
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze E4 prior recovery.")
    parser.add_argument("--inputs", nargs="+", required=True)
    parser.add_argument("--out-json", default="analysis/E4_prior_recovery_summary.json")
    parser.add_argument("--out-csv", default="tables/E4_prior_recovery.csv")
    parser.add_argument("--fig", default="figs/E4_prior_recovery.png")
    args = parser.parse_args()

    import matplotlib.pyplot as plt

    rows: list[dict[str, object]] = []
    fig, axis = plt.subplots(figsize=(7.2, 4.5))
    for input_text in expand_inputs(args.inputs):
        path = Path(input_text)
        data = np.load(path, allow_pickle=True)
        prior = prior_from_path(path, data)
        algorithms = [str(value) for value in data["algorithms"]]
        cumulative = data["cumulative_regret"]
        for algo_index, algorithm in enumerate(algorithms):
            curves = cumulative[algo_index]
            mean_curve = curves.mean(axis=0)
            band = sem(curves)
            label = f"{prior}/{algorithm}"
            axis.plot(np.arange(1, curves.shape[1] + 1), mean_curve, linewidth=2, label=label)
            axis.fill_between(np.arange(1, curves.shape[1] + 1), mean_curve - band, mean_curve + band, alpha=0.12)
            rows.append({
                "prior_mode": prior,
                "algorithm": algorithm,
                "mean_final_cumulative_regret": float(mean_curve[-1]),
                "sem_final": float(band[-1]),
                "seeds": int(curves.shape[0]),
                "K": int(curves.shape[1]),
                "input": str(path),
            })
    axis.set_xlabel("Episode k")
    axis.set_ylabel("Cumulative regret")
    axis.grid(alpha=0.25)
    axis.legend(fontsize=8, ncol=2)
    fig.tight_layout()

    Path(args.fig).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.fig, dpi=180)
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps({"rows": rows}, indent=2), encoding="utf-8")
    Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_csv, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"fig={args.fig}")
    print(f"summary={args.out_json}")
    print(f"csv={args.out_csv}")


if __name__ == "__main__":
    main()