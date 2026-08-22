"""Plot the main-text MaaSSim figure from retained scenario and mechanism CSVs."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

from maassim_rq2_parity import plot_utility_panel
from paper_comparison_methods import (
    METHOD_COLORS,
    METHOD_LABELS,
    METHOD_MARKERS,
    METHOD_ORDER,
    ORACLE_COLOR,
    ORACLE_LABEL,
    ORACLE_LINESTYLE,
)


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis" / "courier_dispatch_maassim"
OUT_DIRS = (ROOT / "figs", ROOT / "arr_paper" / "figs")

SCENARIOS = ["Reject-stress", "Mid-conflict", "Full-conflict"]
X_LABELS = ["Reject stress\n($\\lambda=0$)", "Mid conflict\n($\\lambda=0.5$)", "Full conflict\n($\\lambda=1$)"]
POLICY_METHOD_MAP = {
    "pact_family": "llm",
    "llm_psrl": "llm_psrl",
    "atom_tom1": "atom_tom1",
    "econ_bne": "econ_bne",
}
POLICY_METHOD_KEYS = {policy: method for method, policy in POLICY_METHOD_MAP.items()}
POLICIES = [POLICY_METHOD_MAP[method] for method in METHOD_ORDER]
LABELS = {
    policy: METHOD_LABELS[method]
    for method, policy in POLICY_METHOD_MAP.items()
}
LABELS["oracle"] = ORACLE_LABEL
COLORS = {
    policy: METHOD_COLORS[method]
    for method, policy in POLICY_METHOD_MAP.items()
}
COLORS.update({
    "oracle": ORACLE_COLOR,
    "pact_prior": "#9fb3d1",
    "pact": METHOD_COLORS["pact_family"],
    "pact_shuffled": "#a54545",
})
INK = "#252525"
MUTED = "#666666"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def number(row: dict[str, str], key: str) -> float:
    return float(row[key])


def style_axis(ax: plt.Axes) -> None:
    ax.grid(axis="y", linestyle=":", linewidth=0.55, color="#d9d9d9", zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=7.4)


def main() -> None:
    scenario_rows = read_rows(ANALYSIS / "maassim_llm_scenario_suite_detail.csv")
    mechanism_rows = read_rows(ANALYSIS / "maassim_pact_persona_mechanism_summary.csv")
    parity_rows = read_rows(ROOT / "analysis" / "e_e_maassim_rq2" / "e_e_maassim_tracker_parity_summary.csv")
    by_scenario = {(row["scenario"], row["policy"]): row for row in scenario_rows}
    by_variant = {row["variant"]: row for row in mechanism_rows}

    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 8,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })
    fig, axes = plt.subplots(
        2,
        2,
        figsize=(10.8, 4.75),
        gridspec_kw={"width_ratios": [1.42, 1.18], "height_ratios": [1.0, 0.92]},
    )
    x = np.arange(len(SCENARIOS), dtype=float)

    # (a) Realised utility across a controlled conflict-strength continuum.
    ax = axes[0, 0]
    width = 0.16
    floor = -65.0
    for idx, policy in enumerate(POLICIES):
        offset = (idx - (len(POLICIES) - 1) / 2) * width
        raw = [number(by_scenario[(scenario, policy)], "utility") for scenario in SCENARIOS]
        shown = [max(value, floor) for value in raw]
        sems = [number(by_scenario[(scenario, policy)], "utility_sem") for scenario in SCENARIOS]
        ax.bar(x + offset, shown, width=width, color=COLORS[policy], edgecolor="white", linewidth=0.45,
               label=LABELS[policy], zorder=3)
        ax.errorbar(x + offset, shown, yerr=sems, fmt="none", ecolor="#50565e", elinewidth=0.6,
                    capsize=1.3, alpha=0.72, zorder=4)
        for xpos, value in zip(x + offset, raw):
            if value < floor:
                ax.text(xpos, floor + 1.5, f"{value:.0f}", rotation=90, ha="center", va="bottom",
                        fontsize=5.8, color="#333333")
    oracle = [number(by_scenario[(scenario, "oracle")], "utility") for scenario in SCENARIOS]
    oracle_sem = np.array([number(by_scenario[(scenario, "oracle")], "utility_sem") for scenario in SCENARIOS])
    ax.plot(x, oracle, color=COLORS["oracle"], linestyle=ORACLE_LINESTYLE, linewidth=1.3,
            marker="_", markersize=10, label=ORACLE_LABEL, zorder=5)
    ax.axhline(0.0, color="#7f7f7f", linewidth=0.7)
    ax.set_xticks(x, X_LABELS)
    ax.set_ylim(floor, 48)
    ax.set_ylabel("Realised dispatch utility")
    ax.set_title("(a) Utility across conflict strength", loc="left", fontsize=9.2)
    comparison_handles = [
        Line2D(
            [],
            [],
            color=METHOD_COLORS[method],
            marker=METHOD_MARKERS[method],
            linestyle="-",
            linewidth=1.0,
            markersize=4.0,
            label=METHOD_LABELS[method],
        )
        for method in METHOD_ORDER
    ]
    comparison_handles.append(
        Line2D([], [], color=ORACLE_COLOR, linestyle=ORACLE_LINESTYLE, linewidth=1.2, label=ORACLE_LABEL)
    )
    ax.legend(handles=comparison_handles, ncol=3, frameon=False, fontsize=6.2, loc="lower left",
              columnspacing=0.75, handlelength=1.4, handletextpad=0.32)
    style_axis(ax)

    # (b) Oracle regret in common reject-penalty units.
    ax = axes[0, 1]
    for policy in POLICIES:
        utility = np.array([number(by_scenario[(scenario, policy)], "utility") for scenario in SCENARIOS])
        utility_sem = np.array([number(by_scenario[(scenario, policy)], "utility_sem") for scenario in SCENARIOS])
        regret = (np.array(oracle) - utility) / 5.0
        # The retained suite stores marginal seed-level SEMs rather than paired
        # oracle-minus-policy values, so propagate both terms in quadrature.
        regret_sem = np.hypot(oracle_sem, utility_sem) / 5.0
        method = POLICY_METHOD_KEYS[policy]
        ax.errorbar(x, regret, yerr=regret_sem, marker=METHOD_MARKERS[method], markersize=3.2,
                linewidth=1.15, elinewidth=0.65, capsize=1.6, alpha=0.9,
                color=COLORS[policy], label=LABELS[policy], zorder=3)
    ax.axhline(0.0, color=COLORS["oracle"], linestyle=ORACLE_LINESTYLE, linewidth=1.0)
    ax.set_xticks(x, X_LABELS)
    ax.set_ylabel("Oracle regret (reject-penalty units)")
    ax.set_title("(b) Controlled stress continuum", loc="left", fontsize=9.2)
    style_axis(ax)

    # (c) Belief-source mechanism decomposition from matched replay states.
    ax = axes[1, 0]
    variants = ["pact_prior", "pact", "oracle", "pact_shuffled"]
    values = [number(by_variant[key], "realized_utility") for key in variants]
    errors = [number(by_variant[key], "realized_utility_sem") for key in variants]
    colors = [COLORS[key] for key in variants]
    labels = ["Uniform\nprior", "+ Learned\nposterior", "+ True\npersona", "Shuffled\nidentity"]
    bx = np.arange(len(variants))
    ax.bar(bx, values, yerr=errors, color=colors, edgecolor="white", linewidth=0.6, capsize=2.0, zorder=3)
    ax.axhline(values[0], color="#c7776d", linestyle=":", linewidth=0.9)
    deltas = [None, values[1] - values[0], values[2] - values[1], values[3] - values[0]]
    for idx, delta in enumerate(deltas):
        if delta is None:
            continue
        ax.text(idx, values[idx] + (1.6 if values[idx] >= 0 else -1.6), f"{delta:+.1f}", ha="center",
                va="bottom" if values[idx] >= 0 else "top", fontsize=6.8,
                color="white" if idx in {1, 3} else "#b62d2d")
    ax.set_xticks(bx, labels)
    ax.set_ylabel("Realised dispatch utility")
    ax.set_title("(c) Belief-source decomposition", loc="left", fontsize=9.2)
    style_axis(ax)

    # (d) RQ2 realization: explicit-joint versus factored tracker parity.
    plot_utility_panel(axes[1, 1], parity_rows, compact=True)

    fig.tight_layout(w_pad=1.15, h_pad=0.55)
    for out_dir in OUT_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_dir / "fig_maassim_combined_v22.pdf", bbox_inches="tight", facecolor="white")
        fig.savefig(out_dir / "fig_maassim_combined_v22.png", dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    # Unit validation for the same 18 policy-scenario cells used in panel (b).
    fig, ax = plt.subplots(figsize=(4.8, 4.0))
    all_x: list[float] = []
    all_y: list[float] = []
    markers = ["o", "s", "^"]
    for scenario_idx, scenario in enumerate(SCENARIOS):
        oracle_row = by_scenario[(scenario, "oracle")]
        oracle_utility = number(oracle_row, "utility")
        oracle_rejects = number(oracle_row, "driver_rejects")
        for policy in POLICIES:
            row = by_scenario[(scenario, policy)]
            xval = number(row, "driver_rejects") - oracle_rejects
            yval = (oracle_utility - number(row, "utility")) / 5.0
            all_x.append(xval)
            all_y.append(yval)
            ax.scatter(xval, yval, s=34, marker=markers[scenario_idx], color=COLORS[policy],
                       edgecolor="white", linewidth=0.45,
                       label=f"{LABELS[policy]} · {X_LABELS[scenario_idx].splitlines()[0]}")
    ceiling = max(max(all_x), max(all_y)) * 1.06
    ax.plot([0, ceiling], [0, ceiling], color="#555555", linestyle="--", linewidth=1.0, label="identity")
    ax.set_xlim(-0.5, ceiling)
    ax.set_ylim(-0.5, ceiling)
    ax.set_xlabel("Excess driver rejects vs. oracle")
    ax.set_ylabel("Oracle regret (reject-penalty units)")
    ax.set_title("MaaSSim unit validation", loc="left", fontsize=10)
    style_axis(ax)
    handles, labels_ = ax.get_legend_handles_labels()
    unique: dict[str, object] = {}
    for handle, label in zip(handles, labels_):
        unique.setdefault(label, handle)
    ax.legend(unique.values(), unique.keys(), frameon=False, fontsize=5.6, ncol=2, loc="upper left")
    fig.tight_layout()
    for out_dir in OUT_DIRS:
        fig.savefig(out_dir / "fig_maassim_unit_validation_v3.pdf", bbox_inches="tight", facecolor="white")
        fig.savefig(out_dir / "fig_maassim_unit_validation_v3.png", dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote fig_maassim_combined_v22.{pdf,png}")


if __name__ == "__main__":
    main()