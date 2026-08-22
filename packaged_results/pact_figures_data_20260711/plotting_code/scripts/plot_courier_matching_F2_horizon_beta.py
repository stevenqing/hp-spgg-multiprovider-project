"""Plot F2: CloudGPT live horizon-by-beta sweep for CourierDispatch matching."""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "analysis" / "courier_dispatch_matching" / "courier_matching_live_F2_horizon_beta_sweep_summary.csv"
OUT_DIRS = [ROOT / "figs", ROOT / "arr_paper" / "figs"]
BETAS = [0.0, 0.1, 0.25, 0.5]
COLORS = {0.0: "#3d6cb3", 0.1: "#1b3a6f", 0.25: "#c7773d", 0.5: "#2f2f2f"}
MARKERS = {0.0: "o", 0.1: "s", 0.25: "D", 0.5: "^"}
MODELS = ["GPT-5.4-mini", "DeepSeek-V3.2", "Kimi-K2.6", "Llama-Maverick"]
INK = "#202020"
MUTED = "#555555"
PALE = "#cccccc"


def read_rows() -> list[dict[str, str]]:
    with CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def style(ax: plt.Axes) -> None:
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(PALE)
        ax.spines[spine].set_linewidth(0.45)
    ax.tick_params(colors=MUTED, which="both")
    ax.grid(axis="y", linestyle=":", linewidth=0.55, color="#dddddd")
    ax.set_axisbelow(True)


def main() -> None:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Inter", "Helvetica Neue", "Arial", "DejaVu Sans"],
        "font.size": 8.8,
        "axes.titlesize": 10.5,
        "axes.titleweight": "semibold",
        "axes.titlelocation": "left",
        "savefig.dpi": 240,
    })
    rows = read_rows()
    by_beta: dict[float, dict[str, list[dict[str, str]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        by_beta[float(row["beta"])][row["model_label"]].append(row)
    for beta in BETAS:
        for model in MODELS:
            by_beta[beta][model].sort(key=lambda row: int(row["horizon"]))

    fig, axes = plt.subplots(1, 3, figsize=(10.4, 3.15), sharex=True)
    metrics = [
        ("ptrue", "P(true tuple)", "Posterior concentration"),
        ("reward", "Cumulative reward", "Reward"),
        ("regret", "Cumulative regret", "Regret"),
    ]
    for ax, (metric, ylabel, title) in zip(axes, metrics, strict=True):
        for beta in BETAS:
            # Average over four backbones for main F2 trend; model-specific rows remain in CSV.
            horizons = [int(row["horizon"]) for row in by_beta[beta][MODELS[0]]]
            means = []
            sems = []
            for h in horizons:
                matching = [row for model in MODELS for row in by_beta[beta][model] if int(row["horizon"]) == h]
                vals = [float(row[metric]) for row in matching]
                mean = sum(vals) / len(vals)
                sem_field = f"{metric}_sem"
                seed_sems = [float(row.get(sem_field, 0.0) or 0.0) for row in matching]
                if any(value > 0.0 for value in seed_sems):
                    # Unified w_LLM=0 rows are backbone-invariant, so the plotted uncertainty is the seed SEM.
                    visual_sem = sum(seed_sems) / len(seed_sems)
                else:
                    var = sum((v - mean) ** 2 for v in vals) / max(len(vals) - 1, 1)
                    visual_sem = (var ** 0.5) / (len(vals) ** 0.5)
                means.append(mean)
                sems.append(visual_sem)
            ax.errorbar(
                horizons,
                means,
                yerr=sems,
                color=COLORS[beta],
                marker=MARKERS[beta],
                markersize=5.4,
                markerfacecolor="white",
                markeredgewidth=1.2,
                linewidth=1.8,
                capsize=2.5,
                label=f"beta={beta:g}",
            )
        ax.set_title(title)
        ax.set_xlabel("Horizon H")
        ax.set_ylabel(ylabel)
        ax.set_xticks([8, 16, 24, 32])
        style(ax)
    axes[0].legend(loc="best", frameon=False)
    fig.suptitle("F2. PACT+ horizon/beta sweep (w_LLM=0)", x=0.02, y=1.02, ha="left", fontsize=12, fontweight="semibold", color=INK)
    fig.tight_layout()
    for out_dir in OUT_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_dir / "fig_courier_matching_F2_horizon_beta.png", bbox_inches="tight", facecolor="white")
        fig.savefig(out_dir / "fig_courier_matching_F2_horizon_beta.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("OK: figs/fig_courier_matching_F2_horizon_beta.png")


if __name__ == "__main__":
    main()
