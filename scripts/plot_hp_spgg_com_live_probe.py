"""Plot HP-SPGG-COM live LLM probe results.

The plots mirror the analytic phase diagrams but replace the heuristic panel
with the actual CloudGPT reveal decisions collected by
run_hp_spgg_com_live_probe.py.
"""

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


STRATEGIES = ["NO_COMM", "FULL_COMM", "PACT_LOCAL", "LLM_LIVE"]
LABELS = {
    "NO_COMM": "No communication",
    "FULL_COMM": "Full reveal",
    "PACT_LOCAL": "PACT-local",
    "LLM_LIVE": "CloudGPT live",
}


def load_payload(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def aggregate(payload: dict) -> tuple[list[float], list[float], dict[str, dict[tuple[float, float], dict[str, float]]]]:
    rows = payload["rows"]
    rhos = sorted({float(row["rho"]) for row in rows})
    costs = sorted({float(row["comm_cost"]) for row in rows})
    buckets: dict[str, dict[tuple[float, float], dict[str, list[float]]]] = {
        strategy: {} for strategy in STRATEGIES
    }
    for row in rows:
        key = (float(row["rho"]), float(row["comm_cost"]))
        opt = float(row["profile_optimal_value"])
        analytic = row["analytic_expected_values"]
        for strategy, value in (
            ("NO_COMM", analytic["NO_COMM"]),
            ("FULL_COMM", analytic["FULL_COMM"]),
            ("PACT_LOCAL", float(row["pact_local_value"])),
            ("LLM_LIVE", float(row["llm_value"])),
        ):
            cell = buckets[strategy].setdefault(key, {"suboptimality": [], "messages": []})
            cell["suboptimality"].append(opt - float(value))
        for strategy, messages in (
            ("NO_COMM", 0.0),
            ("FULL_COMM", len(row["theta_profile"])),
            ("PACT_LOCAL", sum(1 for flag in row["pact_local_reveal"] if flag)),
            ("LLM_LIVE", sum(1 for flag in row["llm_reveal"] if flag)),
        ):
            buckets[strategy][key]["messages"].append(float(messages))

    aggregated: dict[str, dict[tuple[float, float], dict[str, float]]] = {strategy: {} for strategy in STRATEGIES}
    for strategy, by_cell in buckets.items():
        for key, metrics in by_cell.items():
            aggregated[strategy][key] = {
                metric: float(np.mean(values)) for metric, values in metrics.items()
            }
    return rhos, costs, aggregated


def grid_for(strategy_data: dict[tuple[float, float], dict[str, float]], metric: str, rhos: list[float], costs: list[float]) -> np.ndarray:
    arr = np.full((len(costs), len(rhos)), np.nan, dtype=float)
    for (rho, cost), metrics in strategy_data.items():
        arr[costs.index(cost), rhos.index(rho)] = float(metrics[metric])
    return arr


def plot_metric(payload: dict, metric: str, out_name: str, cmap: str, cbar_label: str) -> None:
    rhos, costs, aggregated = aggregate(payload)
    fig, axes = plt.subplots(1, len(STRATEGIES), figsize=(12.8, 3.2), sharex=True, sharey=True)
    grids = [grid_for(aggregated[strategy], metric, rhos, costs) for strategy in STRATEGIES]
    vmax = max(float(np.nanmax(grid)) for grid in grids)
    vmax = max(vmax, 1e-6)
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
    cbar.set_label(cbar_label)
    backend = payload.get("backend", "LLM")
    model = payload.get("model") or "default player model"
    fig.suptitle(f"HP-SPGG-COM live probe ({backend}, {model})", fontsize=12, fontweight="semibold")
    fig.subplots_adjust(left=0.06, right=0.88, top=0.82, bottom=0.20, wspace=0.12)
    for out_dir in OUT_DIRS:
        fig.savefig(out_dir / f"{out_name}.pdf", bbox_inches="tight")
        fig.savefig(out_dir / f"{out_name}.png", bbox_inches="tight", dpi=190)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="analysis/hp_spgg_com/hp_spgg_com_live_probe_cloudgpt_v2.json")
    parser.add_argument("--prefix", default="fig_hp_spgg_com_cloudgpt_live")
    args = parser.parse_args()
    payload = load_payload(ROOT / args.input)
    plot_metric(payload, "suboptimality", f"{args.prefix}_suboptimality_v1", "magma", "Mean suboptimality vs profile optimum")
    plot_metric(payload, "messages", f"{args.prefix}_messages_v1", "viridis", "Mean reveal messages")
    print(f"OK: {args.prefix}_suboptimality_v1")
    print(f"OK: {args.prefix}_messages_v1")


if __name__ == "__main__":
    main()