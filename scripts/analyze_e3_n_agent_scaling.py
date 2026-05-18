"""Analyze and plot E3 n-agent storage/performance scaling."""

from __future__ import annotations

import argparse
import csv
import glob
import json
import re
from pathlib import Path

import numpy as np


def sem(values: np.ndarray) -> float:
    return 0.0 if len(values) <= 1 else float(np.std(values, ddof=1) / np.sqrt(len(values)))


def n_from_path(path: Path, data: np.lib.npyio.NpzFile) -> int:
    match = re.search(r"n(\d+)", path.stem)
    if match:
        return int(match.group(1))
    if "true_types" in data.files:
        return int(data["true_types"].shape[-1])
    return -1


def expand_inputs(patterns: list[str]) -> list[str]:
    paths: list[str] = []
    for pattern in patterns:
        matches = sorted(glob.glob(pattern))
        paths.extend(matches if matches else [pattern])
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze E3 n-agent scaling.")
    parser.add_argument("--inputs", nargs="+", required=True)
    parser.add_argument("--out-json", default="analysis/E3_n_agent_scaling_summary.json")
    parser.add_argument("--out-csv", default="tables/E3_n_agent_scaling.csv")
    parser.add_argument("--fig", default="figs/E3_n_agent_scaling.png")
    args = parser.parse_args()

    import matplotlib.pyplot as plt

    rows: list[dict[str, object]] = []
    for input_text in expand_inputs(args.inputs):
        path = Path(input_text)
        data = np.load(path, allow_pickle=True)
        n = n_from_path(path, data)
        algorithms = [str(value) for value in data["algorithms"]]
        cumulative = data["cumulative_regret"]
        storage = data["storage"]
        for algo_index, algorithm in enumerate(algorithms):
            values = cumulative[algo_index, :, -1]
            rows.append({
                "n": n,
                "algorithm": algorithm,
                "storage_entries": int(storage[algo_index]),
                "mean_final_cumulative_regret": float(np.mean(values)),
                "sem": sem(values),
                "seeds": int(values.shape[0]),
                "input": str(path),
            })

    rows.sort(key=lambda row: (int(row["n"]), str(row["algorithm"])))
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    for algorithm in sorted({str(row["algorithm"]) for row in rows}):
        subset = [row for row in rows if row["algorithm"] == algorithm]
        xs = [int(row["n"]) for row in subset]
        ys = [float(row["mean_final_cumulative_regret"]) for row in subset]
        es = [float(row["sem"]) for row in subset]
        storage = [int(row["storage_entries"]) for row in subset]
        axes[0].errorbar(xs, ys, yerr=es, marker="o", linewidth=2, capsize=3, label=algorithm)
        axes[1].plot(xs, storage, marker="o", linewidth=2, label=algorithm)
    axes[0].set_xlabel("Number of agents n")
    axes[0].set_ylabel("Final cumulative regret at K")
    axes[1].set_xlabel("Number of agents n")
    axes[1].set_ylabel("Posterior/storage entries")
    axes[1].set_yscale("log")
    for axis in axes:
        axis.grid(alpha=0.25)
        axis.legend(fontsize=8)
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