"""Restore the original three-panel MaaSSim main figure from retained CSVs."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from paper_comparison_methods import METHOD_COLORS, ORACLE_COLOR, ORACLE_LINESTYLE


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis" / "courier_dispatch_maassim"
OUT = ROOT / "arr_paper" / "figs"
SCENARIOS = ["Reject-stress", "Mid-conflict", "Full-conflict"]
X_LABELS = ["Reject stress\n($\\lambda=0$)", "Mid conflict\n($\\lambda=0.5$)", "Full conflict\n($\\lambda=1$)"]
POLICIES = [
    ("llm", "HARP", METHOD_COLORS["pact_family"]),
    ("llm_belief", "LLM-belief", "#5b7f9b"),
    ("llm_psrl", "LLM-PSRL", METHOD_COLORS["llm_psrl"]),
    ("atom_tom1", "A-ToM-1", METHOD_COLORS["atom_tom1"]),
    ("econ_bne", "ECON-BNE", METHOD_COLORS["econ_bne"]),
    ("nearest", "Nearest", "#999999"),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def number(row: dict[str, str], key: str) -> float:
    return float(row[key])


def style_axis(axis: plt.Axes) -> None:
    axis.grid(axis="y", linestyle=":", linewidth=0.55, color="#d9d9d9", zorder=0)
    axis.spines[["top", "right"]].set_visible(False)
    axis.tick_params(labelsize=8.4)


def main() -> None:
    rows = read_csv(DATA / "maassim_llm_scenario_suite_detail.csv")
    mechanism = read_csv(DATA / "maassim_pact_persona_mechanism_summary.csv")
    by_scenario = {(row["scenario"], row["policy"]): row for row in rows}
    by_variant = {row["variant"]: row for row in mechanism}

    plt.rcParams.update({"font.family": "serif", "font.size": 9.4, "pdf.fonttype": 42, "ps.fonttype": 42})
    fig, axes = plt.subplots(1, 3, figsize=(11.8, 4.05), gridspec_kw={"width_ratios": [1.25, 1.0, 0.95]})
    x = np.arange(len(SCENARIOS), dtype=float)

    # (a) Original six-policy bar comparison with an oracle reference.
    axis = axes[0]
    width = 0.115
    floor = -60.0
    for index, (policy, label, color) in enumerate(POLICIES):
        offset = (index - (len(POLICIES) - 1) / 2) * width
        raw = [number(by_scenario[(scenario, policy)], "utility") for scenario in SCENARIOS]
        shown = [max(value, floor) for value in raw]
        sems = [number(by_scenario[(scenario, policy)], "utility_sem") for scenario in SCENARIOS]
        axis.bar(x + offset, shown, width=width, color=color, edgecolor="white", linewidth=0.4, label=label, zorder=3)
        axis.errorbar(x + offset, shown, yerr=sems, fmt="none", ecolor="#60656b", elinewidth=0.6, capsize=1.2, zorder=4)
        for xpos, value in zip(x + offset, raw, strict=True):
            if value < floor:
                axis.text(xpos, floor + 1.0, f"{value:.0f}", rotation=90, ha="center", va="bottom", fontsize=6.2)
    oracle = np.array([number(by_scenario[(scenario, "oracle")], "utility") for scenario in SCENARIOS])
    oracle_sem = np.array([number(by_scenario[(scenario, "oracle")], "utility_sem") for scenario in SCENARIOS])
    axis.plot(x, oracle, color=ORACLE_COLOR, linestyle=ORACLE_LINESTYLE, linewidth=1.4, label="Oracle", zorder=5)
    axis.axhline(0.0, color="#777777", linewidth=0.7)
    axis.set_xticks(x, X_LABELS)
    axis.set_ylim(floor - 5, 48)
    axis.set_ylabel("Realised dispatch utility")
    axis.set_title("(a) Utility across conflict strength", loc="left", fontsize=10.6)
    axis.legend(frameon=False, fontsize=7.1, ncol=2, loc="lower left", columnspacing=0.7, handlelength=1.4)
    style_axis(axis)

    # (b) Oracle regret for the same six policies.
    axis = axes[1]
    for policy, label, color in POLICIES:
        utility = np.array([number(by_scenario[(scenario, policy)], "utility") for scenario in SCENARIOS])
        utility_sem = np.array([number(by_scenario[(scenario, policy)], "utility_sem") for scenario in SCENARIOS])
        regret = (oracle - utility) / 5.0
        regret_sem = np.hypot(oracle_sem, utility_sem) / 5.0
        axis.errorbar(x, regret, yerr=regret_sem, marker="o", markersize=3.0, linewidth=1.15,
                      elinewidth=0.6, capsize=1.5, color=color, label=label)
    axis.axhline(0.0, color=ORACLE_COLOR, linestyle=ORACLE_LINESTYLE, linewidth=1.0)
    axis.set_xticks(x, X_LABELS)
    axis.set_ylabel("Oracle regret (reject-penalty units)")
    axis.set_title("(b) Controlled stress continuum", loc="left", fontsize=10.6)
    style_axis(axis)

    # (c) Original belief-source decomposition.
    axis = axes[2]
    variants = ["pact_prior", "pact", "oracle", "pact_shuffled"]
    values = [number(by_variant[key], "realized_utility") for key in variants]
    errors = [number(by_variant[key], "realized_utility_sem") for key in variants]
    colors = ["#9fb3d1", METHOD_COLORS["pact_family"], ORACLE_COLOR, "#a54545"]
    labels = ["Uniform\nprior", "+ Learned\nposterior", "+ True\npersona", "Shuffled\nidentity"]
    positions = np.arange(len(variants))
    axis.bar(positions, values, yerr=errors, color=colors, edgecolor="white", linewidth=0.5, capsize=2.0, zorder=3)
    axis.axhline(values[0], color="#c7776d", linestyle=":", linewidth=0.9)
    delta = values[2] - values[1]
    axis.text(2, values[2] + 1.8, f"+{delta:.1f}", ha="center", va="bottom", fontsize=8.2, color=ORACLE_COLOR)
    axis.set_xticks(positions, labels)
    axis.set_ylabel("Realised dispatch utility")
    axis.set_title("(c) Belief-source decomposition", loc="left", fontsize=10.6)
    style_axis(axis)

    fig.tight_layout(w_pad=1.1)
    fig.savefig(OUT / "fig_maassim_combined_v21.pdf", bbox_inches="tight", facecolor="white")
    fig.savefig(OUT / "fig_maassim_combined_v21.png", dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("restored original three-panel MaaSSim Figure 4")


if __name__ == "__main__":
    main()
