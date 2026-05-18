"""Analyze and plot E1 posterior concentration rates."""

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


def backbone_from_path(path: Path) -> str:
    name = path.stem
    for prefix in ["E1_posterior_", "E1_"]:
        if name.startswith(prefix):
            return name[len(prefix):]
    return name


def expand_inputs(patterns: list[str]) -> list[str]:
    paths: list[str] = []
    for pattern in patterns:
        matches = sorted(glob.glob(pattern))
        paths.extend(matches if matches else [pattern])
    return paths


def true_mass(data: np.lib.npyio.NpzFile, algo_name: str = "hpsmg") -> np.ndarray:
    algorithms = [str(value) for value in data["algorithms"]]
    algo_index = algorithms.index(algo_name)
    posterior = data["posterior_history"][algo_index]
    true_types = data["true_types"][algo_index]
    seeds, rounds, n, _ = posterior.shape
    values = np.zeros((seeds, rounds, n), dtype=float)
    for seed_index in range(seeds):
        for player_index in range(n):
            values[seed_index, :, player_index] = posterior[seed_index, :, player_index, true_types[seed_index, player_index]]
    return values


def concentration_time(seed_values: np.ndarray, threshold: float) -> int | None:
    per_round_min = seed_values.min(axis=1)
    hits = np.where(per_round_min >= threshold)[0]
    return int(hits[0] + 1) if len(hits) else None


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze E1 posterior concentration.")
    parser.add_argument("--inputs", nargs="+", required=True)
    parser.add_argument("--out-json", default="analysis/E1_posterior_concentration_summary.json")
    parser.add_argument("--out-csv", default="tables/E1_posterior_concentration.csv")
    parser.add_argument("--fig", default="figs/E1_posterior_concentration.png")
    parser.add_argument("--threshold", type=float, default=0.9)
    args = parser.parse_args()

    import matplotlib.pyplot as plt

    summaries: list[dict[str, object]] = []
    trajectory_rows: list[dict[str, object]] = []
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
    colors = {
        "burn-in jump": "#1f4e79",
        "self-decay edge": "#5fa8d3",
        "extreme self-decay": "#8f8f8f",
    }

    for input_path_text in expand_inputs(args.inputs):
        input_path = Path(input_path_text)
        data = np.load(input_path, allow_pickle=True)
        backbone = backbone_from_path(input_path)
        values = true_mass(data)
        seeds, rounds, n = values.shape
        flat = values.transpose(0, 2, 1).reshape(seeds * n, rounds)
        mean_curve = flat.mean(axis=0)
        band = sem(flat)
        seed_times = [concentration_time(values[seed_index], args.threshold) for seed_index in range(seeds)]
        numeric_times = [rounds + 1 if item is None else item for item in seed_times]
        mean_conc = float(np.mean(numeric_times))
        if mean_conc <= 3:
            regime = "extreme self-decay"
        elif mean_conc <= 10:
            regime = "self-decay edge"
        else:
            regime = "burn-in jump"

        axes[0].plot(np.arange(1, rounds + 1), mean_curve, label=backbone, linewidth=2)
        axes[0].fill_between(np.arange(1, rounds + 1), mean_curve - band, mean_curve + band, alpha=0.16)
        summaries.append({
            "backbone": backbone,
            "input": str(input_path),
            "threshold": args.threshold,
            "seeds": seeds,
            "agents": n,
            "K": rounds,
            "seed_concentration_times": seed_times,
            "mean_concentration_time_censored": mean_conc,
            "regime": regime,
            "final_true_mass_mean": float(mean_curve[-1]),
        })
        for round_index, value in enumerate(mean_curve, start=1):
            trajectory_rows.append({"backbone": backbone, "round": round_index, "mean_true_mass": float(value), "sem": float(band[round_index - 1])})

    labels = [str(row["backbone"]) for row in summaries]
    times = [float(row["mean_concentration_time_censored"]) for row in summaries]
    regimes = [str(row["regime"]) for row in summaries]
    axes[1].bar(labels, times, color=[colors[regime] for regime in regimes])
    axes[1].axhline(args.threshold * 0 + 10, color="#444444", linestyle="--", linewidth=1)
    axes[1].set_ylabel("K conc 0.9, censored at K+1")
    axes[1].tick_params(axis="x", rotation=30)

    benefit_x = times
    benefit_y = [float(row["final_true_mass_mean"]) for row in summaries]
    axes[2].scatter(benefit_x, benefit_y, c=[colors[regime] for regime in regimes], s=70)
    for label, x, y in zip(labels, benefit_x, benefit_y):
        axes[2].annotate(label, (x, y), fontsize=8, xytext=(4, 4), textcoords="offset points")
    axes[2].set_xlabel("K conc 0.9")
    axes[2].set_ylabel("Final true-posterior mass")

    axes[0].set_xlabel("Episode k")
    axes[0].set_ylabel("Posterior mass on true type")
    axes[0].set_ylim(0, 1.02)
    axes[0].legend(fontsize=8)
    for axis in axes:
        axis.grid(alpha=0.25)
    fig.tight_layout()

    Path(args.fig).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.fig, dpi=180)
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps({"summary": summaries, "trajectories": trajectory_rows}, indent=2), encoding="utf-8")
    Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_csv, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(trajectory_rows[0].keys()))
        writer.writeheader()
        writer.writerows(trajectory_rows)
    print(f"fig={args.fig}")
    print(f"summary={args.out_json}")
    print(f"csv={args.out_csv}")


if __name__ == "__main__":
    main()