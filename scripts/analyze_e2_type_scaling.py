"""Analyze and plot E2 type-space-size scaling."""

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


def type_count_from_path(path: Path, data: np.lib.npyio.NpzFile) -> int:
    if "type_count" in data.files:
        return int(data["type_count"])
    match = re.search(r"types?(\d+)|m(\d+)", path.stem)
    if match:
        return int(next(group for group in match.groups() if group))
    return int(data["posterior_history"].shape[-1]) if "posterior_history" in data.files else -1


def expand_inputs(patterns: list[str]) -> list[str]:
    paths: list[str] = []
    for pattern in patterns:
        matches = sorted(glob.glob(pattern))
        paths.extend(matches if matches else [pattern])
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze E2 type scaling.")
    parser.add_argument("--inputs", nargs="+", required=True)
    parser.add_argument("--out-json", default="analysis/E2_type_scaling_summary.json")
    parser.add_argument("--out-csv", default="tables/E2_type_scaling.csv")
    parser.add_argument("--fig", default="figs/E2_type_scaling.png")
    args = parser.parse_args()

    import matplotlib.pyplot as plt

    rows: list[dict[str, object]] = []
    for input_text in expand_inputs(args.inputs):
        path = Path(input_text)
        data = np.load(path, allow_pickle=True)
        type_count = type_count_from_path(path, data)
        algorithms = [str(value) for value in data["algorithms"]]
        cumulative = data["cumulative_regret"]
        for algo_index, algorithm in enumerate(algorithms):
            values = cumulative[algo_index, :, -1]
            rows.append({
                "type_count": type_count,
                "algorithm": algorithm,
                "mean_final_cumulative_regret": float(np.mean(values)),
                "sem": sem(values),
                "seeds": int(values.shape[0]),
                "input": str(path),
            })

    rows.sort(key=lambda row: (int(row["type_count"]), str(row["algorithm"])))
    fig, axis = plt.subplots(figsize=(6.6, 4.2))
    for algorithm in sorted({str(row["algorithm"]) for row in rows}):
        subset = [row for row in rows if row["algorithm"] == algorithm]
        xs = [int(row["type_count"]) for row in subset]
        ys = [float(row["mean_final_cumulative_regret"]) for row in subset]
        es = [float(row["sem"]) for row in subset]
        axis.errorbar(xs, ys, yerr=es, marker="o", linewidth=2, capsize=3, label=algorithm)
    axis.set_xlabel("Type-space size |Theta_i|")
    axis.set_ylabel("Final cumulative regret at K")
    axis.grid(alpha=0.25)
    axis.legend()
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