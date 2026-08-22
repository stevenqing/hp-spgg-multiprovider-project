"""Plot the main E-G component ladder and its appendix trajectory diagnostic."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis" / "e_g_hp_spgg_component_ladder"
SUMMARY = DATA / "e_g_hp_spgg_component_ladder_summary.csv"
LONG = DATA / "e_g_hp_spgg_component_ladder_long.csv"
METADATA = DATA / "e_g_hp_spgg_component_ladder_metadata.json"
OUT_DIRS = (ROOT / "figs", ROOT / "arr_paper" / "figs")
VARIANTS = ("full", "minus_bonus", "minus_update", "minus_identity", "minus_dispatch")
LABELS = {
    "full": "Full\nHARP$^+$",
    "minus_bonus": "$-$ bonus",
    "minus_update": "$-$ update",
    "minus_identity": "$-$ identity",
    "minus_dispatch": "$-$ dispatch",
}
BASE_COLORS = {
    "full": "#12345D",
    "minus_bonus": "#365F8D",
    "minus_update": "#6488AD",
    "minus_identity": "#86A3C0",
    "minus_dispatch": "#AEC0D2",
}
AMBER = "#D4A04A"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def mean_sem(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return values.mean(axis=0), values.std(axis=0, ddof=1) / math.sqrt(values.shape[0])


def main() -> None:
    summary_rows = read_csv(SUMMARY)
    long_rows = read_csv(LONG)
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    summary = {row["variant"]: row for row in summary_rows}
    identity_is_worse = bool(metadata["identity_minus_no_update"]["significantly_worse"])
    colors = dict(BASE_COLORS)
    if identity_is_worse:
        colors["minus_identity"] = AMBER

    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["DejaVu Serif"],
            "font.size": 7.2,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    # Main-paper single-column component ladder.
    means = np.asarray([float(summary[variant]["cumulative_regret_mean"]) for variant in VARIANTS])
    sems = np.asarray([float(summary[variant]["cumulative_regret_sem"]) for variant in VARIANTS])
    x = np.arange(len(VARIANTS), dtype=float)
    fig, ax = plt.subplots(figsize=(3.35, 2.05))
    ax.bar(
        x,
        means,
        yerr=sems,
        width=0.68,
        color=[colors[variant] for variant in VARIANTS],
        edgecolor="#171717",
        linewidth=0.65,
        capsize=2.2,
        error_kw={"elinewidth": 0.75, "capthick": 0.75, "ecolor": "#303030"},
        zorder=3,
    )
    ax.axhline(0.0, color="#111111", linewidth=0.8, zorder=2)
    ax.set_xticks(x, [LABELS[variant] for variant in VARIANTS])
    ax.set_ylabel("Cumulative Bayesian regret ($K=20$)", fontsize=7.0)
    ax.set_title("RQ3: analytic component knock-out", loc="left", fontsize=8.0, pad=2.0)
    ax.grid(axis="y", color="#d8d8d8", linestyle=":", linewidth=0.5, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=6.5, length=2.4, width=0.55)
    ax.set_ylim(0.0, float(np.max(means + sems)) * 1.12)
    fig.tight_layout(pad=0.35)
    for out_dir in OUT_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_dir / "fig_e_g_hp_spgg_component_ladder.pdf", bbox_inches="tight", pad_inches=0.02, facecolor="white")
        fig.savefig(out_dir / "fig_e_g_hp_spgg_component_ladder.png", dpi=280, bbox_inches="tight", pad_inches=0.02, facecolor="white")
    plt.close(fig)

    # Appendix trajectory view from the same complete long table.
    lookup: dict[str, np.ndarray] = {}
    for variant in VARIANTS:
        array = np.empty((10, 20), dtype=float)
        for row in long_rows:
            if row["variant"] == variant:
                array[int(row["seed"]), int(row["episode"]) - 1] = float(row["cum_regret"])
        lookup[variant] = array
    episodes = np.arange(1, 21, dtype=float)
    fig, ax = plt.subplots(figsize=(4.8, 2.9))
    for variant in VARIANTS:
        mean, sem = mean_sem(lookup[variant])
        ax.fill_between(episodes, np.maximum(0.0, mean - sem), mean + sem, color=colors[variant], alpha=0.12, linewidth=0)
        ax.plot(episodes, mean, color=colors[variant], linewidth=1.3 if variant == "full" else 1.05,
                label=LABELS[variant].replace("\n", " "))
    ax.axhline(0.0, color="#111111", linewidth=0.75)
    ax.set_xlim(1, 20)
    ax.set_xticks([1, 5, 10, 15, 20])
    ax.set_xlabel("Episode $k$")
    ax.set_ylabel("Cumulative Bayesian regret")
    ax.set_title("E-G trajectory diagnostic", loc="left", fontsize=8.5)
    ax.grid(axis="y", color="#d8d8d8", linestyle=":", linewidth=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False, fontsize=6.4, ncol=2, loc="upper left")
    fig.tight_layout(pad=0.45)
    for out_dir in OUT_DIRS:
        fig.savefig(out_dir / "fig_e_g_hp_spgg_component_trajectories.pdf", bbox_inches="tight", pad_inches=0.02, facecolor="white")
        fig.savefig(out_dir / "fig_e_g_hp_spgg_component_trajectories.png", dpi=240, bbox_inches="tight", pad_inches=0.02, facecolor="white")
    plt.close(fig)

    # Refresh the single complete Markdown after both figure artifacts exist so
    # its source-integrity table covers the final plots as well as all data.
    from run_e_g_hp_spgg_component_ladder import write_report

    write_report(summary_rows, long_rows, metadata)

    print(
        json.dumps(
            {
                "status": "ok",
                "main_figure": "arr_paper/figs/fig_e_g_hp_spgg_component_ladder.pdf",
                "trajectory_figure": "arr_paper/figs/fig_e_g_hp_spgg_component_trajectories.pdf",
                "identity_amber": identity_is_worse,
                "means": {variant: float(summary[variant]["cumulative_regret_mean"]) for variant in VARIANTS},
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
