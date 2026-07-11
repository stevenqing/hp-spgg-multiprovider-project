"""
Combined HP-SPGG scaling figure.

This prototype merges the type-space sweep and the n-agent sweep onto a common
hidden-profile complexity axis, |Theta_i|^n. The lower panel shows the storage
ratio between the joint profile table and the factored PACT representation.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


ROOT = Path(__file__).resolve().parents[1]
OUT_DIRS = [ROOT / "figs", ROOT / "arr_paper" / "figs"]
for out_dir in OUT_DIRS:
    out_dir.mkdir(parents=True, exist_ok=True)


plt.rcParams.update({
    "font.family": "Inter",
    "font.sans-serif": ["Inter", "Helvetica Neue", "Arial", "DejaVu Sans"],
    "font.size": 9,
    "axes.titlesize": 11,
    "axes.titleweight": "semibold",
    "axes.labelsize": 9,
    "axes.linewidth": 0.5,
    "axes.edgecolor": "#cfcfcf",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "xtick.color": "#444444",
    "ytick.color": "#444444",
    "xtick.major.size": 0,
    "ytick.major.size": 0,
    "savefig.dpi": 220,
    "savefig.bbox": "tight",
})


INK = "#202020"
MUTED = "#565656"
LIGHT = "#e8edf4"
C_PACT = "#3d6cb3"
C_PACT_PLUS = "#102f63"
C_JOINT = "#9ab3d7"
C_STORAGE = "#9b4d2f"


def complexity(theta: np.ndarray, n_agents: np.ndarray) -> np.ndarray:
    return theta.astype(float) ** n_agents.astype(float)


def storage_ratio(theta: np.ndarray, n_agents: np.ndarray) -> np.ndarray:
    return complexity(theta, n_agents) / (theta.astype(float) * n_agents.astype(float))


theta_sweep = {
    "theta": np.array([2, 3, 4, 5, 6]),
    "n": np.array([3, 3, 3, 3, 3]),
    "pact_mean": np.array([0.198, 0.632, 0.232, 0.910, 1.280]),
    "pact_sem": np.array([0.135, 0.494, 0.142, 0.110, 0.272]),
    "pact_plus_mean": np.array([0.062, 0.000, 0.000, 0.772, 0.200]),
    "pact_plus_sem": np.array([0.062, 0.000, 0.000, 0.322, 0.082]),
}

n_sweep = {
    "theta": np.array([4, 4, 4, 4]),
    "n": np.array([2, 3, 4, 5]),
    "pact_mean": np.array([0.070, 0.232, 0.108, 0.870]),
    "pact_sem": np.array([0.037, 0.142, 0.108, 0.588]),
    "pact_plus_mean": np.array([2.962, 0.000, 0.000, 0.278]),
    "pact_plus_sem": np.array([0.545, 0.000, 0.000, 0.278]),
    "joint_mean": np.array([0.275, 0.348, 0.216, 1.252]),
    "joint_sem": np.array([0.140, 0.232, 0.216, 0.648]),
}


def add_curve(ax, x, mean, sem, *, color, marker, label, offset=1.0, linestyle="-"):
    ax.errorbar(
        x * offset,
        mean,
        yerr=sem,
        color=color,
        marker=marker,
        linestyle=linestyle,
        linewidth=2.0 if color != C_JOINT else 1.6,
        markersize=6.5,
        markerfacecolor="white",
        markeredgewidth=1.6,
        capsize=3,
        capthick=0.7,
        elinewidth=0.7,
        label=label,
        zorder=4 if color != C_JOINT else 3,
    )


def annotate_points(ax, x, y, labels, *, dy, color):
    for x_i, y_i, label in zip(x, y, labels):
        ax.annotate(
            label,
            xy=(x_i, y_i),
            xytext=(0, dy),
            textcoords="offset points",
            ha="center",
            va="bottom" if dy > 0 else "top",
            fontsize=7,
            color=color,
            alpha=0.95,
        )


def main() -> None:
    theta_x = complexity(theta_sweep["theta"], theta_sweep["n"])
    n_x = complexity(n_sweep["theta"], n_sweep["n"])
    theta_ratio = storage_ratio(theta_sweep["theta"], theta_sweep["n"])
    n_ratio = storage_ratio(n_sweep["theta"], n_sweep["n"])

    fig = plt.figure(figsize=(7.6, 5.2))
    grid = fig.add_gridspec(2, 1, height_ratios=[3.2, 1.05], hspace=0.10)
    ax = fig.add_subplot(grid[0, 0])
    ax_storage = fig.add_subplot(grid[1, 0], sharex=ax)

    # Separate the duplicated (theta=4, n=3) point just enough to reveal both sweeps.
    theta_offset = 0.965
    n_offset = 1.035

    # Highlight the high joint-profile regime where factorization matters most.
    ax.axvspan(180, 1150, color=LIGHT, alpha=0.65, zorder=0)
    ax.text(
        360,
        3.38,
        "large hidden-profile space",
        ha="center",
        va="top",
        fontsize=7.6,
        color="#60708a",
        fontweight="semibold",
    )

    add_curve(
        ax,
        theta_x,
        theta_sweep["pact_mean"],
        theta_sweep["pact_sem"],
        color=C_PACT,
        marker="o",
        label="PACT, vary |Theta_i|",
        offset=theta_offset,
    )
    add_curve(
        ax,
        theta_x,
        theta_sweep["pact_plus_mean"],
        theta_sweep["pact_plus_sem"],
        color=C_PACT_PLUS,
        marker="D",
        label="PACT+, vary |Theta_i|",
        offset=theta_offset,
    )
    add_curve(
        ax,
        n_x,
        n_sweep["joint_mean"],
        n_sweep["joint_sem"],
        color=C_JOINT,
        marker="s",
        label="Joint-PSRL, vary n",
        offset=n_offset,
        linestyle="--",
    )
    add_curve(
        ax,
        n_x,
        n_sweep["pact_mean"],
        n_sweep["pact_sem"],
        color=C_PACT,
        marker="s",
        label="PACT, vary n",
        offset=n_offset,
    )
    add_curve(
        ax,
        n_x,
        n_sweep["pact_plus_mean"],
        n_sweep["pact_plus_sem"],
        color=C_PACT_PLUS,
        marker="^",
        label="PACT+, vary n",
        offset=n_offset,
    )

    theta_labels = [fr"$\Theta$={value}" for value in theta_sweep["theta"]]
    n_labels = [fr"$n$={value}" for value in n_sweep["n"]]
    annotate_points(
        ax,
        theta_x * theta_offset,
        theta_sweep["pact_mean"],
        theta_labels,
        dy=9,
        color=C_PACT,
    )
    annotate_points(
        ax,
        n_x * n_offset,
        n_sweep["joint_mean"],
        n_labels,
        dy=-10,
        color="#6c82a6",
    )

    ax.set_xscale("log")
    ax.set_xlim(7, 1200)
    ax.set_ylim(-0.18, 3.60)
    ax.set_ylabel(r"Cumulative regret at $K=20$", color=MUTED)
    ax.set_title(
        "Scaling with hidden-profile complexity",
        loc="left",
        color=INK,
        fontsize=12,
        fontweight="semibold",
    )
    ax.text(
        7.2,
        3.35,
        r"Two sweeps share the same x-axis: joint profiles $|\Theta_i|^n$.",
        color=MUTED,
        fontsize=8,
        ha="left",
        va="top",
    )
    ax.annotate(
        "boundary case",
        xy=(n_x[0] * n_offset, n_sweep["pact_plus_mean"][0]),
        xytext=(18, -18),
        textcoords="offset points",
        arrowprops={"arrowstyle": "-", "color": MUTED, "lw": 0.7},
        fontsize=7.3,
        color=MUTED,
        ha="left",
        va="top",
    )
    ax.annotate(
        "PACT+ remains low\nwhere joint profiles explode",
        xy=(n_x[-1] * n_offset, n_sweep["pact_plus_mean"][-1]),
        xytext=(-86, 24),
        textcoords="offset points",
        arrowprops={"arrowstyle": "-", "color": C_PACT_PLUS, "lw": 0.8},
        fontsize=7.5,
        color=C_PACT_PLUS,
        ha="right",
        va="bottom",
    )
    ax.grid(axis="y", linestyle=":", linewidth=0.5, color="#d7d7d7")
    ax.grid(axis="x", linestyle=":", linewidth=0.45, color="#e5e5e5", which="major")
    ax.set_axisbelow(True)

    method_handles = [
        Line2D([0], [0], color=C_PACT_PLUS, marker="D", markerfacecolor="white",
               markeredgewidth=1.5, linewidth=2.2, label="PACT+"),
        Line2D([0], [0], color=C_PACT, marker="o", markerfacecolor="white",
               markeredgewidth=1.5, linewidth=2.0, label="PACT"),
        Line2D([0], [0], color=C_JOINT, marker="s", markerfacecolor="white",
               markeredgewidth=1.4, linewidth=1.6, linestyle="--", label="Joint-PSRL"),
    ]
    sweep_handles = [
        Line2D([0], [0], color="#777777", marker="o", linestyle="", markerfacecolor="white",
               markeredgewidth=1.4, label=r"vary $|\Theta_i|$, fixed $n=3$"),
        Line2D([0], [0], color="#777777", marker="s", linestyle="", markerfacecolor="white",
               markeredgewidth=1.4, label=r"vary $n$, fixed $|\Theta_i|=4$"),
    ]
    leg1 = ax.legend(handles=method_handles, loc="upper center", bbox_to_anchor=(0.52, 1.01),
                     ncol=3, frameon=False, fontsize=8, handlelength=2.2, columnspacing=1.4)
    ax.add_artist(leg1)
    ax.legend(handles=sweep_handles, loc="upper left", bbox_to_anchor=(0.01, 0.78),
              frameon=False, fontsize=7.4, handletextpad=0.6)

    storage_x = np.concatenate([theta_x * theta_offset, n_x * n_offset])
    storage_y = np.concatenate([theta_ratio, n_ratio])
    storage_labels = theta_labels + n_labels
    order = np.argsort(storage_x)
    ax_storage.plot(
        storage_x[order],
        storage_y[order],
        color=C_STORAGE,
        linewidth=1.5,
        marker="o",
        markersize=4.5,
        markerfacecolor="white",
        markeredgewidth=1.1,
        zorder=3,
    )
    for x_i, y_i, label in zip(storage_x, storage_y, storage_labels):
        if label in {r"$\Theta$=2", r"$\Theta$=6", r"$n$=4", r"$n$=5"}:
            ax_storage.annotate(
                label,
                xy=(x_i, y_i),
                xytext=(0, 5),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=6.8,
                color=C_STORAGE if y_i >= 10 else MUTED,
            )
    ax_storage.set_xscale("log")
    ax_storage.set_yscale("log")
    ax_storage.set_ylim(1.0, 70)
    ax_storage.set_ylabel("storage\nratio", color=MUTED, linespacing=0.9)
    ax_storage.set_xlabel(r"Joint hidden profiles $|\Theta_i|^n$ (log scale)", color=MUTED)
    ax_storage.grid(axis="both", linestyle=":", linewidth=0.45, color="#e0e0e0")
    ax_storage.text(
        8,
        42,
        r"$|\Theta_i|^n / (n|\Theta_i|)$",
        ha="left",
        va="center",
        fontsize=8,
        color=C_STORAGE,
        fontweight="semibold",
    )

    xticks = [8, 27, 64, 125, 256, 1024]
    ax_storage.set_xticks(xticks)
    ax_storage.set_xticklabels([str(tick) for tick in xticks])
    plt.setp(ax.get_xticklabels(), visible=False)

    for axis in (ax, ax_storage):
        for spine in ("left", "bottom"):
            axis.spines[spine].set_color("#cfcfcf")

    for out_dir in OUT_DIRS:
        fig.savefig(out_dir / "fig_scaling_hidden_complexity_v2.pdf", bbox_inches="tight")
        fig.savefig(out_dir / "fig_scaling_hidden_complexity_v2.png", bbox_inches="tight", dpi=220)
    plt.close(fig)
    print("OK: fig_scaling_hidden_complexity_v2")

    make_paper_compact()


def add_scaling_panel(ax, x, data, *, title, xlabel, tick_labels, show_joint=False):
    ax.errorbar(
        x,
        data["pact_mean"],
        yerr=data["pact_sem"],
        color=C_PACT,
        marker="o",
        markersize=6.5,
        markerfacecolor="white",
        markeredgewidth=1.5,
        linewidth=2.0,
        capsize=3,
        capthick=0.7,
        elinewidth=0.7,
        label="PACT",
        zorder=4,
    )
    ax.errorbar(
        x,
        data["pact_plus_mean"],
        yerr=data["pact_plus_sem"],
        color=C_PACT_PLUS,
        marker="D",
        markersize=6.5,
        markerfacecolor="white",
        markeredgewidth=1.5,
        linewidth=2.3,
        capsize=3,
        capthick=0.7,
        elinewidth=0.7,
            label=r"PACT+ ($\beta=0.25$)",
        zorder=5,
    )
    if show_joint:
        ax.errorbar(
            x,
            data["joint_mean"],
            yerr=data["joint_sem"],
            color=C_JOINT,
            marker="s",
            markersize=6.2,
            markerfacecolor="white",
            markeredgewidth=1.4,
            linewidth=1.7,
            linestyle="--",
            capsize=3,
            capthick=0.7,
            elinewidth=0.7,
            label="Joint-PSRL",
            zorder=3,
        )
    ax.set_title(title, loc="left", color=INK, fontsize=10.5, fontweight="semibold")
    ax.set_xlabel(xlabel, color=MUTED, labelpad=30)
    ax.set_xticks(x)
    ax.set_xticklabels(tick_labels)
    ax.grid(axis="y", linestyle=":", linewidth=0.5, color="#d9d9d9")
    ax.set_axisbelow(True)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("#cfcfcf")


def make_paper_compact() -> None:
    theta_labels = [str(theta) for theta in theta_sweep["theta"]]
    n_labels = [str(n) for n in n_sweep["n"]]

    fig, axes = plt.subplots(1, 2, figsize=(7.6, 4.25), sharey=True)
    add_scaling_panel(
        axes[0],
        np.arange(len(theta_sweep["theta"])),
        theta_sweep,
        title=r"Vary type-space size, fixed $n=3$",
        xlabel=r"Type-space size $|\Theta_i|$",
        tick_labels=theta_labels,
        show_joint=False,
    )
    add_scaling_panel(
        axes[1],
        np.arange(len(n_sweep["n"])),
        n_sweep,
        title=r"Vary number of agents, fixed $|\Theta_i|=4$",
        xlabel=r"Number of agents $n$",
        tick_labels=n_labels,
        show_joint=False,
    )

    axes[0].set_ylabel(r"Cumulative regret at $K=20$", color=MUTED)
    axes[0].set_ylim(-0.16, 3.35)

    handles = [
        Line2D([0], [0], color=C_PACT_PLUS, marker="D", markerfacecolor="white",
               markeredgewidth=1.5, linewidth=2.2, label=r"PACT+ ($\beta=0.25$)"),
        Line2D([0], [0], color=C_PACT, marker="o", markerfacecolor="white",
               markeredgewidth=1.5, linewidth=2.0, label="PACT"),
    ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.55, 0.985),
               ncol=2, frameon=False, fontsize=8.5, handlelength=2.4, columnspacing=1.6)
    fig.subplots_adjust(left=0.08, right=0.985, top=0.82, bottom=0.16, wspace=0.12)

    for out_dir in OUT_DIRS:
        fig.savefig(out_dir / "fig_scaling_hidden_complexity_v3.pdf", bbox_inches="tight")
        fig.savefig(out_dir / "fig_scaling_hidden_complexity_v3.png", bbox_inches="tight", dpi=220)
        fig.savefig(out_dir / "fig_scaling_hidden_complexity_v4.pdf", bbox_inches="tight")
        fig.savefig(out_dir / "fig_scaling_hidden_complexity_v4.png", bbox_inches="tight", dpi=220)
        fig.savefig(out_dir / "fig_scaling_hidden_complexity_v5.pdf", bbox_inches="tight")
        fig.savefig(out_dir / "fig_scaling_hidden_complexity_v5.png", bbox_inches="tight", dpi=220)
    plt.close(fig)
    print("OK: fig_scaling_hidden_complexity_v3")
    print("OK: fig_scaling_hidden_complexity_v4")
    print("OK: fig_scaling_hidden_complexity_v5")


if __name__ == "__main__":
    main()