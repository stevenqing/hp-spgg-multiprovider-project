"""Plot HP-SPGG experiment results and write summary tables."""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path
import numpy as np


ALGO_DISPLAY: dict[str, str] = {
    "hpsmg_plus": r"PACT$^+$",
    "hpsmg": "PACT",
    "joint_psrl": "Joint-PSRL",
    "map_greedy": "MAP-Type-Greedy",
    "psrl_notype": "PSRL-NoType",
    "random": "Random",
    "oracle": "Oracle",
    "iql": "IQL",
}


def display_label(provider: str, algorithm: str) -> str:
    return f"{provider} / {ALGO_DISPLAY.get(algorithm, algorithm)}"


def sem(values: np.ndarray) -> float:
    if len(values) <= 1:
        return 0.0
    return float(np.std(values, ddof=1) / np.sqrt(len(values)))


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot HP-SPGG cumulative regret curves.")
    parser.add_argument("--inputs", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--summary", default="analysis/E3_summary.json")
    parser.add_argument("--table", default="tables/E3_cross_provider_regret.tex")
    args = parser.parse_args()

    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("Install matplotlib to plot results") from exc

    input_paths = expand_inputs(args.inputs)
    if not input_paths:
        raise FileNotFoundError(f"No result files matched: {args.inputs}")

    fig, axis = plt.subplots(figsize=(7.0, 4.5))
    summary: dict[str, dict[str, float]] = {}
    table_rows = ["\\begin{tabular}{llr}", r"Provider & Algorithm & Final cumulative regret \\", "\\hline"]

    for input_path in input_paths:
        data = np.load(input_path, allow_pickle=True)
        algorithms = [str(value) for value in data["algorithms"]]
        cumulative = data["cumulative_regret"]
        provider = Path(input_path).parent.name
        summary[provider] = {}
        for algo_index, algorithm in enumerate(algorithms):
            mean_curve = cumulative[algo_index].mean(axis=0)
            if algorithm in {"hpsmg_plus", "hpsmg", "random", "oracle"}:
                axis.plot(np.arange(1, len(mean_curve) + 1), mean_curve,
                          label=display_label(provider, algorithm), linewidth=1.8)
            final_values = cumulative[algo_index, :, -1]
            final_mean = float(np.mean(final_values))
            final_sem = sem(final_values)
            summary[provider][algorithm] = final_mean
            table_rows.append(f"{provider} & {algorithm} & {final_mean:.3f} $\\pm$ {final_sem:.3f} " + r"\\")

    table_rows.append("\\end{tabular}")
    axis.set_xlabel("Round")
    axis.set_ylabel("Cumulative regret")
    axis.legend(fontsize=7, ncol=2)
    axis.grid(alpha=0.25)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path)

    Path(args.summary).parent.mkdir(parents=True, exist_ok=True)
    Path(args.summary).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    Path(args.table).parent.mkdir(parents=True, exist_ok=True)
    Path(args.table).write_text("\n".join(table_rows) + "\n", encoding="utf-8")
    print(f"saved={output_path}")
    print(f"summary={args.summary}")
    print(f"table={args.table}")


def expand_inputs(patterns: list[str]) -> list[str]:
    paths: list[str] = []
    for pattern in patterns:
        matches = sorted(glob.glob(pattern))
        paths.extend(matches if matches else [pattern])
    return paths


if __name__ == "__main__":
    main()
