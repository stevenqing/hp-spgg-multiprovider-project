"""Render E-H grouped-prior paired regret gaps against posterior correlation TV."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "analysis" / "e_h_maassim_grouped_prior" / "e_h_maassim_grouped_prior.csv"
DEFAULT_OUTPUT = ROOT / "analysis" / "e_h_maassim_grouped_prior" / "e_h_maassim_grouped_prior.pdf"


def mean_sem(values: list[float]) -> tuple[float, float]:
    data = np.asarray(values, dtype=float)
    return float(data.mean()), float(data.std(ddof=1) / np.sqrt(len(data))) if len(data) > 1 else 0.0


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    with args.input.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    group_sizes = sorted({int(row["g"]) for row in rows})
    fig, axes = plt.subplots(1, len(group_sizes), figsize=(3.4 * len(group_sizes), 2.5), squeeze=False)
    colors = {"harp": "#12345D", "harp_s": "#2F7D5B"}
    labels = {"harp": "HARP $-$ Joint", "harp_s": "HARP-S $-$ Joint"}
    for axis, group_size in zip(axes.ravel(), group_sizes):
        subset = [row for row in rows if int(row["g"]) == group_size]
        rhos = sorted({float(row["rho"]) for row in subset})
        for arm in ("harp", "harp_s"):
            xs, ys, errors = [], [], []
            for rho in rhos:
                cell = [row for row in subset if float(row["rho"]) == rho]
                joint = {int(row["seed"]): float(row["cum_regret"]) for row in cell if row["arm"] == "joint"}
                target = {int(row["seed"]): float(row["cum_regret"]) for row in cell if row["arm"] == arm}
                seeds = sorted(set(joint) & set(target))
                gaps = [target[seed] - joint[seed] for seed in seeds]
                x = float(np.mean([float(row["corr_tv"]) for row in cell if row["arm"] == "joint"]))
                y, error = mean_sem(gaps)
                xs.append(x); ys.append(y); errors.append(error)
            axis.errorbar(xs, ys, yerr=errors, marker="o", capsize=2.2, color=colors[arm], label=labels[arm])
        axis.axhline(0.0, color="#303030", linestyle="--", linewidth=0.8, label="zero")
        axis.set_xlabel("joint posterior vs marginal-product TV")
        axis.set_ylabel("paired oracle-regret gap")
        axis.set_title(f"group size $g={group_size}$")
        axis.grid(linestyle=":", linewidth=0.5, color="#dddddd")
        axis.legend(frameon=False, fontsize=7)
    fig.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, bbox_inches="tight")
    fig.savefig(args.output.with_suffix(".png"), dpi=220, bbox_inches="tight")
    print(args.output)


if __name__ == "__main__":
    main()