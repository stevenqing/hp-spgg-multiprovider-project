"""Plot HP-SPGG-COM phase diagrams."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "analysis" / "hp_spgg_com" / "hp_spgg_com_phase_summary.json"
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
        x = rhos.index(row["rho"])
        y = costs.index(row["comm_cost"])
        arr[y, x] = float(row[metric])
    return arr


def plot_metric(payload: dict, metric: str, filename: str, cmap: str, label: str) -> None:
    rows = payload["rows"]
    rhos = payload["rho_grid"]
    costs = payload["comm_cost_grid"]
    fig, axes = plt.subplots(1, len(STRATEGIES), figsize=(12.8, 3.2), sharex=True, sharey=True)
    values = [grid_for(rows, strategy, metric, rhos, costs) for strategy in STRATEGIES]
    vmax = float(np.nanmax(values)) if values else 1.0
    if metric == "suboptimality":
        vmax = max(vmax, 1e-6)
        vmin = 0.0
    else:
        vmin = 0.0
    for ax, strategy, arr in zip(axes, STRATEGIES, values, strict=True):
        im = ax.imshow(
            arr,
            origin="lower",
            aspect="auto",
            cmap=cmap,
            vmin=vmin,
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
    fig.suptitle("HP-SPGG-COM communication phase diagram", fontsize=12, fontweight="semibold")
    fig.subplots_adjust(left=0.06, right=0.88, top=0.82, bottom=0.20, wspace=0.12)
    for out_dir in OUT_DIRS:
        fig.savefig(out_dir / f"{filename}.pdf", bbox_inches="tight")
        fig.savefig(out_dir / f"{filename}.png", bbox_inches="tight", dpi=190)
    plt.close(fig)


def main() -> None:
    payload = json.loads(SUMMARY.read_text(encoding="utf-8"))
    plot_metric(payload, "suboptimality", "fig_hp_spgg_com_suboptimality_v1", "magma", "Suboptimality vs global optimum")
    plot_metric(payload, "expected_messages", "fig_hp_spgg_com_messages_v1", "viridis", "Expected reveal messages")
    print("OK: fig_hp_spgg_com_suboptimality_v1")
    print("OK: fig_hp_spgg_com_messages_v1")


if __name__ == "__main__":
    main()