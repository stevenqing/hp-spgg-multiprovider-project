"""Summarize HP-SPGG external LLM baseline result archives."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("npz", help="Path to an external LLM baseline .npz result file.")
    parser.add_argument("--out", help="Optional markdown output path.")
    args = parser.parse_args()

    result_path = Path(args.npz)
    data = np.load(result_path, allow_pickle=True)
    algorithms = [str(value) for value in data["algorithms"]]
    cumulative = np.asarray(data["cumulative_regret"], dtype=float)
    regrets = np.asarray(data["regrets"], dtype=float)
    welfare = np.asarray(data["welfare"], dtype=float)

    rows = []
    for index, algorithm in enumerate(algorithms):
        final_values = cumulative[index, :, -1]
        rows.append(
            {
                "algorithm": algorithm,
                "final_mean": float(final_values.mean()),
                "final_std": float(final_values.std(ddof=0)),
                "per_round_mean": float(regrets[index].mean()),
                "welfare_mean": float(welfare[index].mean()),
            }
        )
    rows.sort(key=lambda row: row["final_mean"])

    title = f"# External LLM Baseline Summary\n\nSource: `{result_path.as_posix()}`\n"
    metadata = [
        "",
        f"- Backend: `{str(data.get('backend', 'unknown'))}`",
        f"- Model: `{str(data.get('model', ''))}`",
        f"- K: `{int(data['K'])}`",
        f"- Seeds: `{int(data['seeds'])}`",
        f"- ECON rounds: `{int(data.get('econ_rounds', 0))}`",
        "",
    ]
    table = [
        "| Rank | Algorithm | Final cumulative regret mean | Std | Mean per-round regret | Mean welfare |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(rows, start=1):
        table.append(
            f"| {rank} | `{row['algorithm']}` | {row['final_mean']:.4f} | "
            f"{row['final_std']:.4f} | {row['per_round_mean']:.4f} | {row['welfare_mean']:.4f} |"
        )

    report = "\n".join([title, *metadata, *table, ""])
    print(report)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
