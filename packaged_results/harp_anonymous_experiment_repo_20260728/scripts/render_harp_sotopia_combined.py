"""Redraw the historical SOTOPIA-Hard descriptive 2x3 figure from release data."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "arr_paper" / "figs"
FAMILIES = ["Craigslist bargains", "Revenge plot", "Donate funds"]
METHODS = ["HARP$^{+}$", "LLM-PSRL", "A-ToM-1", "ECON-BNE", "llm_belief", "llm_greedy"]
COLORS = ["#1f2d5c", "#2f7d5b", "#d8a04b", "#b64b45", "#7a8aa6", "#bdbdbd"]
ENDPOINTS = np.array([
    [3.04, 2.94, 2.98, 2.92, 2.96, 2.91],
    [2.93, 2.66, 2.76, 2.83, 2.74, 2.79],
    [3.26, 3.00, 3.24, 3.04, 3.23, 2.98],
])
# Published prefix-only trajectory values retained from the archived release plot.
TRAJECTORIES = {
    "HARP$^{+}$": np.array([[2.45, 3.10, 3.12, 3.10, 3.07, 3.04], [2.05, 2.34, 2.64, 2.68, 2.67, 2.93], [2.50, 3.25, 3.34, 3.39, 3.38, 3.26]]),
    "LLM-PSRL": np.array([[2.45, 3.08, 3.10, 3.12, 3.10, 2.94], [2.05, 2.30, 2.40, 2.52, 2.65, 2.66], [2.50, 3.20, 3.27, 3.23, 3.36, 3.00]]),
    "A-ToM-1": np.array([[2.45, 3.05, 3.08, 3.12, 3.14, 2.98], [2.05, 2.22, 2.41, 2.52, 2.65, 2.76], [2.50, 3.14, 3.22, 3.28, 3.38, 3.24]]),
    "ECON-BNE": np.array([[2.45, 3.04, 3.08, 3.12, 3.18, 2.92], [2.05, 2.45, 2.40, 2.65, 2.72, 2.83], [2.50, 3.12, 3.17, 3.42, 3.40, 3.04]]),
    "llm_belief": np.array([[2.45, 3.07, 3.10, 3.12, 3.13, 2.96], [2.05, 2.28, 2.64, 2.68, 2.70, 2.74], [2.50, 3.15, 3.20, 3.34, 3.38, 3.23]]),
    "llm_greedy": np.array([[2.45, 3.06, 3.08, 3.11, 3.00, 2.91], [2.05, 2.25, 2.62, 2.65, 2.68, 2.79], [2.50, 3.18, 3.12, 3.30, 3.34, 2.98]]),
    "Oracle-policy": np.array([[2.45, 3.06, 3.08, 3.12, 3.15, 3.42], [2.05, 2.30, 2.65, 2.70, 2.78, 3.12], [2.50, 3.20, 3.42, 3.44, 3.40, 3.55]]),
}


def main() -> None:
    plt.rcParams.update({"font.family": "serif", "font.size": 8, "pdf.fonttype": 42, "ps.fonttype": 42})
    fig, axes = plt.subplots(2, 3, figsize=(10.8, 5.1))
    for family_index, family in enumerate(FAMILIES):
        axis = axes[0, family_index]
        y = np.arange(len(METHODS))[::-1]
        values = ENDPOINTS[family_index]
        axis.barh(y, values, color=COLORS, edgecolor="black", linewidth=[1.1, .4, .4, .4, .4, .4])
        axis.set_yticks(y, METHODS if family_index == 0 else [])
        best_alt = max(values[1:])
        axis.set_title(f"{family}  ($\\Delta={values[0]-best_alt:+.2f}$)")
        axis.set_xlabel("End-of-dialogue focal score")
        axis.set_xlim(min(values) - 0.12, max(values) + 0.12)
        axis.spines[["top", "right"]].set_visible(False)
        for yi, value in zip(y, values, strict=True):
            axis.text(value + 0.01, yi, f"{value:.2f}", va="center", fontsize=6.8)

        axis = axes[1, family_index]
        turns = np.arange(1, 7)
        for method_index, method in enumerate(METHODS):
            axis.plot(turns, TRAJECTORIES[method][family_index], marker="o", markersize=2.8,
                      color=COLORS[method_index], linewidth=2.1 if method.startswith("HARP") else 1.0,
                      alpha=1.0 if method.startswith("HARP") else 0.75, label=method)
        axis.plot(turns, TRAJECTORIES["Oracle-policy"][family_index], color="#b00020", linestyle="--", linewidth=1.5, label="Oracle-policy")
        axis.set_xlabel("Turn checkpoint $k$")
        axis.set_ylabel("Prefix focal score" if family_index == 0 else "")
        axis.grid(alpha=0.22, linestyle=":")
        axis.spines[["top", "right"]].set_visible(False)
    axes[1, 0].legend(frameon=False, fontsize=6.2, ncol=2)
    fig.tight_layout()
    fig.savefig(OUT / "fig_sotopia_combined_v7.pdf", bbox_inches="tight")
    fig.savefig(OUT / "fig_sotopia_combined_v7.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    print("redrew SOTOPIA combined v7")


if __name__ == "__main__":
    main()
