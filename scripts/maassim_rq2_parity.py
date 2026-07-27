"""Render E-E MaaSSim factored-versus-explicit-joint parity figures."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis" / "e_e_maassim_rq2"
OUT_DIRS = (ROOT / "figs", ROOT / "arr_paper" / "figs")
N_VALUES = [2, 3, 4, 6, 8]
LAMBDAS = [0.0, 0.5, 1.0]
COLORS = {0.0: "#557a95", 0.5: "#6f8f68", 1.0: "#b64b45"}
TRACKER_COLORS = {"factored": "#12345d", "joint": "#b64b45"}
INK = "#252525"
MUTED = "#686868"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def style_axis(ax: plt.Axes) -> None:
    ax.grid(axis="y", linestyle=":", linewidth=0.55, color="#d9d9d9", zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=7.4)


def storage_tick(n: int) -> str:
    factored = 16 * n
    joint = 16**n
    if joint >= 1_000_000_000:
        joint_text = f"{joint / 1_000_000_000:.1f}B"
    elif joint >= 1_000_000:
        joint_text = f"{joint / 1_000_000:.1f}M"
    elif joint >= 1_000:
        joint_text = f"{joint:,}"
    else:
        joint_text = str(joint)
    return f"{n}\n{factored}/{joint_text}"


def lookup_summary(summary: list[dict[str, str]]) -> dict[tuple[int, float, str], dict[str, str]]:
    return {(int(row["n"]), float(row["lambda"]), row["tracker"]): row for row in summary}


def plot_utility_panel(ax: plt.Axes, summary: list[dict[str, str]], *, compact: bool = False) -> None:
    lookup = lookup_summary(summary)
    x = np.arange(len(N_VALUES), dtype=float)
    for strength in LAMBDAS:
        factored = [lookup[(n, strength, "factored")] for n in N_VALUES]
        ax.errorbar(
            x,
            [float(row["utility_mean"]) for row in factored],
            yerr=[float(row["utility_sem"]) for row in factored],
            marker="o",
            markersize=3.5,
            linewidth=1.25,
            elinewidth=0.65,
            capsize=1.5,
            color=COLORS[strength],
            label=rf"Factored, $\lambda={strength:g}$",
            zorder=4,
        )
        joint_n = [2, 3, 4]
        joint_rows = [lookup[(n, strength, "joint")] for n in joint_n]
        ax.errorbar(
            x[:3],
            [float(row["utility_mean"]) for row in joint_rows],
            yerr=[float(row["utility_sem"]) for row in joint_rows],
            marker="s",
            markerfacecolor="white",
            markersize=3.4,
            linestyle="--",
            linewidth=1.05,
            elinewidth=0.6,
            capsize=1.4,
            color=COLORS[strength],
            label=rf"Joint, $\lambda={strength:g}$",
            zorder=5,
        )
    ax.axvspan(3.65, 4.35, color="#ececec", alpha=0.9, zorder=1)
    ax.text(4.0, 0.97, "joint infeasible", transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=6.1, color=MUTED)
    ax.text(3.0, 0.90, "joint optional\n(not run)", transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=5.8, color=MUTED)
    ax.set_xticks(x, [storage_tick(n) for n in N_VALUES])
    ax.set_xlabel("Drivers $n$\n(factored / joint entries)", fontsize=7.5)
    ax.set_ylabel("Replay utility")
    ax.set_title("(d) RQ2: tracker parity and storage" if compact else "(a) Replay utility on common environments", loc="left", fontsize=9.0)
    ax.legend(frameon=False, fontsize=5.8 if compact else 6.5, ncol=2, loc="lower right", columnspacing=0.7, handlelength=1.7)
    style_axis(ax)


def main() -> None:
    summary = rows(ANALYSIS / "e_e_maassim_tracker_parity_summary.csv")
    gaps = rows(ANALYSIS / "e_e_maassim_tracker_parity_gaps.csv")
    lookup = lookup_summary(summary)

    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 8,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })
    fig, axes = plt.subplots(1, 3, figsize=(10.6, 3.35), gridspec_kw={"width_ratios": [1.55, 1.0, 1.05]})
    plot_utility_panel(axes[0], summary)

    # Belief-update time: average the two payoff geometries because lambda does
    # not enter the evidence channel or update equation.
    ax = axes[1]
    for tracker, marker, linestyle in (("factored", "o", "-"), ("joint", "s", "--")):
        available_n = N_VALUES if tracker == "factored" else [2, 3, 4]
        values = [
            np.mean([float(lookup[(n, strength, tracker)]["mean_update_us"]) for strength in LAMBDAS])
            for n in available_n
        ]
        ax.plot(
            available_n,
            values,
            marker=marker,
            markerfacecolor="white" if tracker == "joint" else TRACKER_COLORS[tracker],
            color=TRACKER_COLORS[tracker],
            linestyle=linestyle,
            linewidth=1.2,
            markersize=4.0,
            label=tracker.capitalize(),
            zorder=3,
        )
    ax.set_yscale("log")
    ax.set_xticks(N_VALUES)
    ax.set_xlabel("Drivers $n$")
    ax.set_ylabel(r"Mean update time ($\mu$s/event)")
    ax.set_title("(b) Belief-update work", loc="left", fontsize=9.0)
    ax.legend(frameon=False, fontsize=6.5)
    style_axis(ax)

    ax = axes[2]
    factored_bytes = np.asarray([16 * n * 8 for n in N_VALUES], dtype=float)
    joint_bytes = np.asarray([16**n * 8 for n in N_VALUES], dtype=float)
    ax.plot(N_VALUES, factored_bytes / 1024.0, color=TRACKER_COLORS["factored"], marker="o", linewidth=1.25, label="Factored")
    ax.plot(N_VALUES[:4], joint_bytes[:4] / 1024.0, color=TRACKER_COLORS["joint"], marker="s", markerfacecolor="white", linestyle="--", linewidth=1.1, label="Joint (n=6 theoretical)")
    ax.scatter([8], [joint_bytes[-1] / 1024.0], marker="x", s=28, color=TRACKER_COLORS["joint"], zorder=4)
    ax.text(8, joint_bytes[-1] / 1024.0 / 1.9, "34.4 GB\nnot run", ha="center", va="top", fontsize=6.0, color=MUTED)
    ax.set_yscale("log")
    ax.set_xticks(N_VALUES)
    ax.set_xlabel("Drivers $n$")
    ax.set_ylabel("Float64 belief memory (KiB)")
    ax.set_title("(c) Persistent belief storage", loc="left", fontsize=9.0)
    ax.legend(frameon=False, fontsize=6.2, loc="upper left")
    style_axis(ax)

    max_tv = max(float(row["max_tv"]) for row in gaps)
    noncovering = sum(row["ci_covers_zero"].lower() != "true" for row in gaps)
    fig.text(
        0.01,
        0.005,
        f"Explicit-joint marginals match the factored tracker (max TV={max_tv:.1e}); "
        f"{len(gaps)-noncovering}/{len(gaps)} nominal utility CIs include zero. "
        "Timing excludes the TV diagnostic.",
        fontsize=6.5,
        color=MUTED,
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1), w_pad=1.1)
    for out_dir in OUT_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_dir / "fig_maassim_rq2_parity.pdf", bbox_inches="tight", facecolor="white")
        fig.savefig(out_dir / "fig_maassim_rq2_parity.png", dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote fig_maassim_rq2_parity.{pdf,png}")


if __name__ == "__main__":
    main()
