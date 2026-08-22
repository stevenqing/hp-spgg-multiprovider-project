"""Plot real HP-SPGG-COM phase diagrams."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUT_DIRS = [ROOT / "figs", ROOT / "arr_paper" / "figs"]
for out_dir in OUT_DIRS:
    out_dir.mkdir(parents=True, exist_ok=True)

STRATEGIES = ["NO_COMM", "FULL_COMM", "VERBAL_PSRL_HEUR", "PACT_LOCAL"]
LABELS = {
    "NO_COMM": "No communication",
    "FULL_COMM": "Full reveal",
    "VERBAL_PSRL_HEUR": "Verbal heuristic",
    "PACT_LOCAL": "PACT-local",
}


def grid_for(rows: list[dict], strategy: str, metric: str, rhos: list[float], costs: list[float]) -> np.ndarray:
    arr = np.full((len(costs), len(rhos)), np.nan, dtype=float)
    for row in rows:
        if row["strategy"] != strategy:
            continue
        arr[costs.index(row["comm_cost"]), rhos.index(row["rho"])] = float(row[metric])
    return arr


def plot_metric(payload: dict, metric: str, filename: str, cmap: str, label: str) -> None:
    rows = payload["rows"]
    rhos = payload["rho_grid"]
    costs = payload["comm_cost_grid"]
    grids = [grid_for(rows, strategy, metric, rhos, costs) for strategy in STRATEGIES]
    vmax = max(max(float(np.nanmax(grid)) for grid in grids), 1e-9)
    fig, axes = plt.subplots(1, len(STRATEGIES), figsize=(12.8, 3.2), sharex=True, sharey=True)
    for ax, strategy, grid in zip(axes, STRATEGIES, grids, strict=True):
        im = ax.imshow(
            grid,
            origin="lower",
            aspect="auto",
            cmap=cmap,
            vmin=0.0,
            vmax=vmax,
            extent=[min(rhos), max(rhos), min(costs), max(costs)],
        )
        ax.set_title(LABELS[strategy], fontsize=10)
        ax.set_xlabel(r"Identifiability $\rho$")
        ax.grid(color="white", alpha=0.2, linewidth=0.5)
    axes[0].set_ylabel(r"Communication cost $c_\sigma$")
    cax = fig.add_axes([0.91, 0.20, 0.012, 0.62])
    cbar = fig.colorbar(im, cax=cax)
    cbar.set_label(label)
    fig.suptitle("Real HP-SPGG-COM phase diagram", fontsize=12, fontweight="semibold")
    fig.subplots_adjust(left=0.06, right=0.88, top=0.82, bottom=0.20, wspace=0.12)
    for out_dir in OUT_DIRS:
        fig.savefig(out_dir / f"{filename}.pdf", bbox_inches="tight")
        fig.savefig(out_dir / f"{filename}.png", bbox_inches="tight", dpi=190)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="analysis/hp_spgg_com/real_hp_spgg_com_phase_summary.json")
    parser.add_argument("--prefix", default="fig_real_hp_spgg_com")
    args = parser.parse_args()
    payload = json.loads((ROOT / args.input).read_text(encoding="utf-8"))
    plot_metric(payload, "suboptimality", f"{args.prefix}_suboptimality_v1", "magma", "Suboptimality vs global optimum")
    plot_metric(payload, "expected_messages", f"{args.prefix}_messages_v1", "viridis", "Expected reveal messages")
    print(f"OK: {args.prefix}_suboptimality_v1")
    print(f"OK: {args.prefix}_messages_v1")


if __name__ == "__main__":
    main()