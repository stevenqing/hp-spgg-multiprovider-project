"""Render the three-panel MaaSSim main figure at its paper-facing size."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from render_harp_maassim_main_v21 import POLICIES, SCENARIOS
from paper_comparison_methods import METHOD_COLORS, ORACLE_COLOR, ORACLE_LINESTYLE


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis" / "courier_dispatch_maassim"
OUT = ROOT / "arr_paper" / "figs"
X_LABELS = ["0", "0.5", "1"]
NAVY_D = "#1B3A6F"
NAVY_L = "#7B9FCF"
RED = ORACLE_COLOR
GRAY = "#777777"
POLICY_COLORS = {
    policy: color for policy, _, color in POLICIES
}
POLICY_MARKERS = {
    "llm": "o",
    "llm_belief": "s",
    "llm_psrl": "D",
    "atom_tom1": "^",
    "econ_bne": "v",
    "moa": "X",
    "puppeteer": "*",
    "nearest": "P",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def numeric_payload() -> dict[str, object]:
    rows = read_csv(DATA / "maassim_llm_scenario_suite_detail.csv")
    mechanism = read_csv(DATA / "maassim_pact_persona_mechanism_summary.csv")
    by_scenario = {(row["scenario"], row["policy"]): row for row in rows}
    by_variant = {row["variant"]: row for row in mechanism}

    active_policies = [
        (policy, label, color)
        for policy, label, color in POLICIES
        if all((scenario, policy) in by_scenario for scenario in SCENARIOS)
    ]
    policy_order = [policy for policy, _, _ in active_policies]
    labels = [label for _, label, _ in active_policies]
    utility = np.asarray([
        [float(by_scenario[(scenario, policy)]["utility"]) for scenario in SCENARIOS]
        for policy in policy_order
    ])
    utility_sem = np.asarray([
        [float(by_scenario[(scenario, policy)]["utility_sem"]) for scenario in SCENARIOS]
        for policy in policy_order
    ])
    oracle = np.asarray([
        float(by_scenario[(scenario, "oracle")]["utility"])
        for scenario in SCENARIOS
    ])
    oracle_sem = np.asarray([
        float(by_scenario[(scenario, "oracle")]["utility_sem"])
        for scenario in SCENARIOS
    ])
    variants = ["pact_prior", "pact", "oracle", "pact_shuffled"]
    mechanism_values = np.asarray([
        float(by_variant[variant]["realized_utility"]) for variant in variants
    ])
    mechanism_sem = np.asarray([
        float(by_variant[variant]["realized_utility_sem"]) for variant in variants
    ])
    return {
        "scenarios": list(SCENARIOS),
        "policy_order": policy_order,
        "policy_labels": labels,
        "utility": utility.tolist(),
        "utility_sem": utility_sem.tolist(),
        "oracle": oracle.tolist(),
        "oracle_sem": oracle_sem.tolist(),
        "regret": ((oracle[None, :] - utility) / 5.0).tolist(),
        "regret_sem": (np.hypot(oracle_sem[None, :], utility_sem) / 5.0).tolist(),
        "mechanism_variants": variants,
        "mechanism_values": mechanism_values.tolist(),
        "mechanism_sem": mechanism_sem.tolist(),
    }


def payload_sha256(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def style_axis(axis: plt.Axes) -> None:
    axis.grid(axis="y", linestyle=":", linewidth=0.45, color="#d9d9d9", zorder=0)
    axis.spines[["top", "right"]].set_visible(False)
    axis.tick_params(axis="both", labelsize=6.5, pad=1.2, length=2.2)
    axis.xaxis.label.set_size(7.5)
    axis.yaxis.label.set_size(7.5)


def main() -> None:
    payload = numeric_payload()
    utility = np.asarray(payload["utility"], dtype=float)
    utility_sem = np.asarray(payload["utility_sem"], dtype=float)
    oracle = np.asarray(payload["oracle"], dtype=float)
    oracle_sem = np.asarray(payload["oracle_sem"], dtype=float)
    regret = np.asarray(payload["regret"], dtype=float)
    regret_sem = np.asarray(payload["regret_sem"], dtype=float)
    mechanism_values = np.asarray(payload["mechanism_values"], dtype=float)
    mechanism_sem = np.asarray(payload["mechanism_sem"], dtype=float)

    mpl.rcParams.update({
        "font.family": "serif",
        "font.serif": ["DejaVu Serif"],
        "font.size": 6.5,
        "axes.titlesize": 8.0,
        "axes.labelsize": 7.5,
        "xtick.labelsize": 6.5,
        "ytick.labelsize": 6.5,
        "legend.fontsize": 6.5,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })
    fig, axes = plt.subplots(
        1,
        3,
        figsize=(6.5, 2.2),
        gridspec_kw={"width_ratios": [1.25, 1.0, 0.95]},
    )
    fig.subplots_adjust(left=0.075, right=0.995, bottom=0.19, top=0.87, wspace=0.22)
    x = np.arange(len(SCENARIOS), dtype=float)

    # (a) Same six-policy utility comparison and oracle reference as v21.
    axis = axes[0]
    width = 0.115
    floor = -60.0
    active_policies = list(zip(payload["policy_order"], payload["policy_labels"], strict=True))
    width = min(0.115, 0.72 / max(len(active_policies), 1))
    for index, (policy, label) in enumerate(active_policies):
        offset = (index - (len(active_policies) - 1) / 2) * width
        shown = np.maximum(utility[index], floor)
        axis.bar(
            x + offset,
            shown,
            width=width,
            color=POLICY_COLORS[policy],
            edgecolor="white",
            linewidth=0.35,
            label=label,
            zorder=3,
        )
        axis.errorbar(
            x + offset,
            shown,
            yerr=utility_sem[index],
            fmt="none",
            ecolor="#60656b",
            elinewidth=0.55,
            capsize=1.0,
            zorder=4,
        )
    axis.plot(x, oracle, color=ORACLE_COLOR, linestyle=ORACLE_LINESTYLE, linewidth=1.1, label="Oracle", zorder=5)
    axis.axhline(0.0, color=GRAY, linewidth=0.6)
    axis.set_xticks(x, X_LABELS)
    axis.set_ylim(floor - 5, 48)
    axis.set_xlabel(r"conflict strength $\lambda$")
    axis.set_ylabel("realised utility")
    axis.set_title("(a) Utility across conflict strength", loc="left", pad=2)
    style_axis(axis)

    # (b) Same reject-penalty-normalized oracle regret as v21.
    axis = axes[1]
    for index, (policy, label) in enumerate(active_policies):
        axis.errorbar(
            x,
            regret[index],
            yerr=regret_sem[index],
            marker=POLICY_MARKERS[policy],
            markersize=2.5,
            linewidth=0.9,
            elinewidth=0.55,
            capsize=1.2,
            color=POLICY_COLORS[policy],
            label=label,
        )
    axis.axhline(0.0, color=ORACLE_COLOR, linestyle=ORACLE_LINESTYLE, linewidth=0.9)
    axis.set_xticks(x, X_LABELS)
    axis.set_xlabel(r"conflict strength $\lambda$")
    axis.set_ylabel("oracle regret\n(reject-penalty units)")
    axis.set_title("(b) Controlled stress continuum", loc="left", pad=2)
    style_axis(axis)

    # (c) Same four belief-source variants as v21.
    axis = axes[2]
    colors = ["#9fb3d1", METHOD_COLORS["pact_family"], ORACLE_COLOR, "#a54545"]
    labels = ["Prior", "Learned", "Oracle", "Shuffled"]
    positions = np.arange(len(labels))
    axis.bar(
        positions,
        mechanism_values,
        yerr=mechanism_sem,
        color=colors,
        edgecolor="white",
        linewidth=0.4,
        capsize=1.5,
        zorder=3,
    )
    axis.axhline(mechanism_values[0], color="#c7776d", linestyle=":", linewidth=0.8)
    delta = mechanism_values[2] - mechanism_values[1]
    axis.annotate(
        f"+{delta:.1f}",
        xy=(2, mechanism_values[2] + 1.8),
        xytext=(4, 0),
        textcoords="offset points",
        ha="left",
        va="bottom",
        fontsize=6.0,
        color=ORACLE_COLOR,
    )
    axis.set_xticks(positions, labels)
    axis.set_ylabel("realised utility")
    axis.set_title("(c) Belief sources", loc="left", pad=2)
    style_axis(axis)

    # One compact legend for panels (a) and (b), kept inside the fixed page.
    handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        legend_labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.995),
        ncol=min(9, len(legend_labels)),
        frameon=False,
        fontsize=6.5,
        columnspacing=0.65,
        handlelength=1.0,
        handletextpad=0.25,
        borderaxespad=0.0,
    )

    pdf_path = OUT / "fig_maassim_combined_v22.pdf"
    png_path = OUT / "fig_maassim_combined_v22.png"
    fig.savefig(pdf_path, facecolor="white")
    fig.savefig(png_path, dpi=300, facecolor="white")
    plt.close(fig)

    fingerprint = {
        "schema_version": "1.0",
        "source": "v21 retained CSVs and formulas",
        "numeric_payload_sha256": payload_sha256(payload),
        "payload": payload,
    }
    fingerprint_path = OUT / "fig_maassim_combined_v22_data.json"
    fingerprint_path.write_text(json.dumps(fingerprint, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "ok",
        "pdf": str(pdf_path.relative_to(ROOT)),
        "png": str(png_path.relative_to(ROOT)),
        "numeric_payload_sha256": fingerprint["numeric_payload_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
