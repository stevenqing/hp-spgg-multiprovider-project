"""Redraw MaaSSim appendix figures directly from retained CSV artifacts."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis" / "courier_dispatch_maassim"
OUT = ROOT / "arr_paper" / "figs"
COLORS = {"HARP": "#173b67", "HARP-prior": "#adc3df", "HARP-shuffled": "#d18a7a", "Oracle": "#3e8068", "Nearest": "#929493", "Random": "#555555"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def style_axis(axis: plt.Axes) -> None:
    axis.grid(alpha=0.25, linestyle=":")
    axis.spines[["top", "right"]].set_visible(False)


def concentration() -> None:
    grouped: dict[int, dict[str, list[float]]] = defaultdict(lambda: {"ptrue": [], "rule": []})
    for seed in range(10):
        counts: dict[int, int] = defaultdict(int)
        for row in read_csv(DATA / f"pact_kpi_persona_v2_main_s{seed}_driver_posterior.csv"):
            driver = int(row["driver_id"])
            counts[driver] += 1
            grouped[counts[driver]]["ptrue"].append(float(row["ptrue"]))
            grouped[counts[driver]]["rule"].append(float(row["rule_acc"]))
    observations = sorted(grouped)
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8))
    for axis, field, label in ((axes[0], "ptrue", "Posterior mass on true persona"), (axes[1], "rule", "Persona-rule accuracy")):
        means = np.array([np.mean(grouped[index][field]) for index in observations])
        sems = np.array([np.std(grouped[index][field], ddof=1) / np.sqrt(len(grouped[index][field])) for index in observations])
        axis.fill_between(observations, means - sems, means + sems, color="#173b67", alpha=0.16)
        axis.plot(observations, means, "o-", color="#173b67", markersize=3.2, linewidth=1.4, label="HARP tracker")
        axis.axhline(0.0625 if field == "ptrue" else 0.5, color="#888888", linestyle="--", linewidth=0.8, label="uniform prior")
        axis.set_xlabel("Within-driver observation count")
        axis.set_ylabel(label)
        style_axis(axis)
    axes[0].set_title("(a) Exact-persona concentration", loc="left")
    axes[1].set_title("(b) Rule recovery", loc="left")
    axes[0].legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / "fig_maassim_concentration_v1.pdf", bbox_inches="tight")
    fig.savefig(OUT / "fig_maassim_concentration_v1.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def wait_reject_tradeoff() -> None:
    rows = read_csv(DATA / "maassim_pact_persona_mechanism_summary.csv")
    selected = [row for row in rows if row["variant"] in {"nearest", "random", "pact_prior", "pact_shuffled", "pact", "oracle"}]
    fig, axis = plt.subplots(figsize=(4.8, 3.4))
    for row in selected:
        label = row["label"]
        x = float(row["mean_wait_served"])
        y = float(row["driver_rejects"])
        xerr = float(row["mean_wait_served_sem"])
        yerr = float(row["driver_rejects_sem"])
        utility = float(row["realized_utility"])
        axis.errorbar(x, y, xerr=xerr, yerr=yerr, fmt="o", markersize=5.5, capsize=2.0,
                      color=COLORS.get(label, "#777777"), label=f"{label} ({utility:+.1f} utility)")
        axis.annotate(label, (x, y), xytext=(4, 4), textcoords="offset points", fontsize=7)
    axis.set_xlabel("Mean pickup wait for served rides (s)")
    axis.set_ylabel("Driver rejects")
    axis.set_title("MaaSSim wait-reject trade-off", loc="left")
    style_axis(axis)
    axis.legend(frameon=False, fontsize=6.4, ncol=2)
    fig.tight_layout()
    fig.savefig(OUT / "fig_maassim_wait_reject_tradeoff_v1.pdf", bbox_inches="tight")
    fig.savefig(OUT / "fig_maassim_wait_reject_tradeoff_v1.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def conflict_dynamics() -> None:
    rows = read_csv(DATA / "maassim_llm_scenario_suite_detail.csv")
    scenarios = ["Reject-stress", "Mid-conflict", "Full-conflict"]
    policies = [("llm", "LLM-HARP", "#173b67"), ("llm_psrl", "LLM-PSRL", "#2f7d5b"), ("atom_tom1", "A-ToM-1", "#d4a04a"), ("econ_bne", "ECON-BNE", "#b64b45")]
    lookup = {(row["scenario"], row["policy"]): row for row in rows}
    x = np.arange(len(scenarios))
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 2.9))
    for policy, label, color in policies:
        utility = [float(lookup[(scenario, policy)]["utility"]) for scenario in scenarios]
        utility_sem = [float(lookup[(scenario, policy)]["utility_sem"]) for scenario in scenarios]
        rejects = [float(lookup[(scenario, policy)]["driver_rejects"]) for scenario in scenarios]
        axes[0].errorbar(x, utility, yerr=utility_sem, marker="o", linewidth=1.4, capsize=2, color=color, label=label)
        axes[1].plot(x, rejects, marker="o", linewidth=1.4, color=color, label=label)
    for axis in axes:
        axis.set_xticks(x, ["$\\lambda=0$", "$\\lambda=0.5$", "$\\lambda=1$"])
        axis.set_xlabel("Conflict strength")
        style_axis(axis)
    axes[0].set_ylabel("Realized dispatch utility")
    axes[1].set_ylabel("Driver rejects")
    axes[0].set_title("(a) Utility under conflict", loc="left")
    axes[1].set_title("(b) Rejection dynamics", loc="left")
    axes[0].legend(frameon=False, fontsize=6.8, ncol=2)
    fig.tight_layout()
    fig.savefig(OUT / "fig_maassim_conflict_dynamics_v4.pdf", bbox_inches="tight")
    fig.savefig(OUT / "fig_maassim_conflict_dynamics_v4.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    plt.rcParams.update({"font.family": "serif", "font.size": 8, "pdf.fonttype": 42, "ps.fonttype": 42})
    concentration()
    wait_reject_tradeoff()
    conflict_dynamics()
    print("redrew three MaaSSim appendix figures")


if __name__ == "__main__":
    main()
