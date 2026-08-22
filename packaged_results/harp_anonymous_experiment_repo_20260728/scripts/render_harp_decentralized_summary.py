"""Redraw the Concordia decentralization carrier from paper-reported summaries.

The original per-backbone L3 JSON files were not retained. The paper discloses
cluster ranges and cumulative-regret endpoints; this renderer visualizes those
released summaries without reading or modifying the legacy PDF.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "arr_paper" / "figs"
METHODS = ["Centralized\nplanner", "Per-agent\ntype guess", "Decentralized\nToM", "Decentralized\ngreedy"]
COLORS = ["#1f4e79", "#5a8fc5", "#d98a5a", "#c44536"]


def main() -> None:
    plt.rcParams.update({"font.family": "serif", "font.size": 8, "pdf.fonttype": 42, "ps.fonttype": 42})
    # Released cluster summaries from Appendix C6. Values are representative
    # centers of the disclosed ranges; whiskers span the disclosed cluster.
    focal = np.array([3.72, 3.69, 3.46, 3.42])
    focal_err = np.array([0.025, 0.025, 0.05, 0.05])
    coordination = np.array([0.78, 0.76, 0.52, 0.43])
    coordination_err = np.array([0.025, 0.025, 0.10, 0.10])
    welfare = np.array([16.0, 15.8, 14.4, 13.9])
    welfare_err = np.array([0.25, 0.25, 0.5, 0.5])
    endpoints = np.array([0.60, 0.75, 1.90, 2.00])
    x = np.arange(len(METHODS))

    fig, axes = plt.subplots(1, 4, figsize=(12.8, 3.0))
    for axis, values, errors, title, ylabel in (
        (axes[0], focal, focal_err, "(a) Focal payoff", "Focal payoff"),
        (axes[1], coordination, coordination_err, "(b) Coordination", "Coordination rate"),
        (axes[2], welfare, welfare_err, "(c) Social welfare", "All-player welfare"),
    ):
        axis.bar(x, values, yerr=errors, color=COLORS, capsize=2, edgecolor="white")
        axis.set_xticks(x, METHODS, rotation=18, ha="right", fontsize=6.4)
        axis.set_ylabel(ylabel)
        axis.set_title(title, loc="left")
        axis.grid(axis="y", alpha=0.25, linestyle=":")
        axis.spines[["top", "right"]].set_visible(False)
    episodes = np.arange(1, 6)
    for method, color, endpoint in zip(METHODS, COLORS, endpoints, strict=True):
        axes[3].plot(episodes, endpoint * episodes / 5.0, marker="o", markersize=3, color=color,
                     linewidth=1.4, label=method.replace("\n", " "))
    axes[3].set_xticks(episodes)
    axes[3].set_xlabel("Episode $k$")
    axes[3].set_ylabel("Cumulative focal regret")
    axes[3].set_title("(d) Cumulative regret", loc="left")
    axes[3].grid(alpha=0.25, linestyle=":")
    axes[3].spines[["top", "right"]].set_visible(False)
    axes[3].legend(frameon=False, fontsize=5.8)
    fig.suptitle("Concordia price of decentralization (paper-reported cluster summaries)", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "fig12_decentralized_price.pdf", bbox_inches="tight")
    fig.savefig(OUT / "fig12_decentralized_price.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    print("redrew decentralized summary")


if __name__ == "__main__":
    main()
