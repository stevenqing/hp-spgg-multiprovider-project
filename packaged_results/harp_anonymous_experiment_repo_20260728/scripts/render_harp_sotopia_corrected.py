"""Redraw corrected SOTOPIA HARP figures from retained summary CSVs."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis" / "e_c_sotopia_corrected"
OUT = ROOT / "arr_paper" / "figs"
FAMILIES = ["craigslist_bargains", "donate_funds", "revenge_plot"]
COLORS = dict(zip(FAMILIES, ["#12345d", "#2f7d5b", "#b64b45"], strict=True))


def rows(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main_figure() -> None:
    posterior = rows("e_c_posterior_proxy_summary.csv")
    corruption = rows("e_c_menu_corruption_summary.csv")
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.35))
    for family in FAMILIES:
        selected = [row for row in posterior if row["family"] == family]
        axes[0].errorbar([int(row["turn"]) for row in selected], [float(row["proxy_mass_mean"]) for row in selected],
                         yerr=[float(row["proxy_mass_sem"]) for row in selected], marker="o", capsize=2,
                         linewidth=1.3, color=COLORS[family], label=family.replace("_", " "))
        selected = [row for row in corruption if row["family"] == family]
        axes[1].errorbar([float(row["p"]) for row in selected], [float(row["focal_score_mean"]) for row in selected],
                         yerr=[float(row["focal_score_sem"]) for row in selected], marker="o", capsize=2,
                         linewidth=1.3, color=COLORS[family], label=family.replace("_", " "))
    axes[0].axhline(0.25, color="#888888", linestyle="--", linewidth=0.9)
    axes[0].set_xlabel("Dialogue turn")
    axes[0].set_ylabel("Mass on profile-derived proxy type")
    axes[0].set_title("(a) Corrected recurrent tracker", loc="left")
    axes[1].set_xlabel("Menu-corruption probability")
    axes[1].set_ylabel("Focal score")
    axes[1].set_title("(b) Intent-menu sensitivity", loc="left")
    for axis in axes:
        axis.grid(axis="y", linestyle=":", linewidth=0.6, color="#d7d7d7")
        axis.spines[["top", "right"]].set_visible(False)
    axes[0].legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / "fig_e_c_sotopia_corrected.pdf", bbox_inches="tight", facecolor="white")
    fig.savefig(OUT / "fig_e_c_sotopia_corrected.png", dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def component_figure() -> None:
    data = rows("e_c_component_summary.csv")
    variants = ["surrogate-only corrected", "naive-belief corrected", "PACT+ corrected"]
    display = {"surrogate-only corrected": "surrogate-only", "naive-belief corrected": "naive belief", "PACT+ corrected": "HARP+"}
    colors = ["#9a9a9a", "#b64b45", "#12345d"]
    x = np.arange(len(FAMILIES), dtype=float)
    width = 0.24
    fig, axis = plt.subplots(figsize=(6.8, 3.4))
    for index, (variant, color) in enumerate(zip(variants, colors, strict=True)):
        selected = {row["family"]: row for row in data if row["variant"] == variant}
        axis.bar(x + (index - 1) * width, [float(selected[family]["focal_score_mean"]) for family in FAMILIES], width,
                 yerr=[float(selected[family]["focal_score_sem"]) for family in FAMILIES], capsize=2,
                 color=color, label=display[variant])
    axis.set_xticks(x, [family.replace("_", "\n") for family in FAMILIES])
    axis.set_ylabel("Focal score")
    axis.set_title("Corrected SOTOPIA tracker variants", loc="left")
    axis.grid(axis="y", linestyle=":", linewidth=0.6, color="#d7d7d7")
    axis.spines[["top", "right"]].set_visible(False)
    axis.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fig_e_c_sotopia_component_corrected.pdf", bbox_inches="tight", facecolor="white")
    fig.savefig(OUT / "fig_e_c_sotopia_component_corrected.png", dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    plt.rcParams.update({"font.family": "serif", "font.size": 8, "pdf.fonttype": 42, "ps.fonttype": 42})
    main_figure()
    component_figure()
    print("redrew corrected SOTOPIA figures")


if __name__ == "__main__":
    main()
