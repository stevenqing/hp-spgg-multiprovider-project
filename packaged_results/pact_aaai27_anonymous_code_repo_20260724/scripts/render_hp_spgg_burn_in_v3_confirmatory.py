"""Render the locked HP-SPGG Claim-B v3 confirmatory diagnostics."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis" / "hp_spgg_burn_in_v3_confirmatory"
AFFINITY = DATA / "affinity_summary.csv"
FIXED = DATA / "fixed_channel_cell_summary.csv"
PROXY = DATA / "posterior_error_proxy_checkpoints.csv"
RESULTS = DATA / "confirmatory_results.json"
OUTPUTS = (
    DATA / "fig_hp_spgg_burn_in_v3_confirmatory.pdf",
    DATA / "fig_hp_spgg_burn_in_v3_confirmatory.png",
    ROOT / "figs" / "fig_hp_spgg_burn_in_v3_confirmatory.pdf",
    ROOT / "figs" / "fig_hp_spgg_burn_in_v3_confirmatory.png",
)
COLORS = {1: "#355C9A", 2: "#2A9D8F", 4: "#E9A03B", 8: "#C84C4C"}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    affinity = rows(AFFINITY)
    fixed = rows(FIXED)
    proxy = rows(PROXY)
    results = json.loads(RESULTS.read_text(encoding="utf-8"))
    supported = bool(results["claim_b_v3_supported"])

    plt.rcParams.update(
        {
            "font.size": 8.5,
            "axes.titlesize": 9.5,
            "axes.labelsize": 8.5,
            "legend.fontsize": 7.2,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 7.5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    figure, axes = plt.subplots(2, 2, figsize=(7.1, 5.0), constrained_layout=True)

    ax = axes[0, 0]
    x = np.asarray([float(row["x_exact_information"]) for row in affinity])
    y = np.asarray([float(row["y_negative_log_empirical"]) for row in affinity])
    for gap in (1, 2, 3):
        mask = np.asarray([int(row["gap"]) == gap for row in affinity])
        ax.scatter(x[mask], y[mask], s=24, label=f"type gap {gap}", alpha=0.85)
    extent = np.linspace(0.0, max(float(x.max()), float(y.max())) * 1.04, 100)
    ax.plot(extent, extent, color="black", linewidth=1.0, linestyle="--", label="exact affinity")
    fit = results["gates"]["G1_affinity_core"]["fit"]
    ax.plot(extent, float(fit["slope"]) * extent + float(fit["intercept"]), color="#C84C4C", linewidth=1.2, label="confirmatory fit")
    ax.set_xlabel(r"Exact cumulative information $-T\log(1-\rho)$")
    ax.set_ylabel(r"$-\log\,\widehat{\mathbb{E}}\sqrt{\Lambda_T}$")
    ax.set_title("(a) Hellinger contraction core")
    ax.legend(frameon=False, ncol=2)
    ax.grid(alpha=0.18)

    ax = axes[0, 1]
    type_rows = [row for row in fixed if row["phase"] == "type_horizon"]
    for H in (1, 2, 4, 8):
        selected = sorted((row for row in type_rows if int(row["H"]) == H), key=lambda row: int(row["m"]))
        xx = np.asarray([float(row["predictor_per_agent"]) for row in selected])
        yy = np.asarray([float(row["restricted_mean_per_agent_episode"]) for row in selected])
        ax.scatter(xx, yy, s=25, color=COLORS[H], label=f"H={H}")
    fit = results["gates"]["G2_type_horizon"]["fit"]
    extent = np.linspace(
        min(float(row["predictor_per_agent"]) for row in type_rows),
        max(float(row["predictor_per_agent"]) for row in type_rows),
        200,
    )
    ax.plot(extent, float(fit["slope"]) * extent + float(fit["intercept"]), color="black", linewidth=1.2)
    ax.set_xlabel(r"$\log(m\sqrt{m})/(\rho_a H)$")
    ax.set_ylabel("Restricted mean first-passage episode")
    ax.set_title("(b) Independent type / horizon cells")
    ax.legend(frameon=False, ncol=2)
    ax.grid(alpha=0.18)

    ax = axes[1, 0]
    pop = sorted((row for row in fixed if row["phase"] == "population"), key=lambda row: int(row["n"]))
    n = np.asarray([int(row["n"]) for row in pop], dtype=float)
    y = np.asarray([float(row["restricted_mean_all_agent_episode"]) for row in pop])
    corrected_x = np.asarray([float(row["predictor_all_agent"]) for row in pop])
    original_x = np.asarray([float(row["predictor_original_linear_n"]) for row in pop])
    corrected = results["gates"]["G3_population"]["corrected_fit"]
    original = results["gates"]["G3_population"]["original_linear_n_fit"]
    ax.scatter(np.log2(n), y, s=28, color="#355C9A", zorder=3, label="independent cells")
    ax.plot(np.log2(n), float(corrected["slope"]) * corrected_x + float(corrected["intercept"]), color="#2A9D8F", linewidth=1.4, label=r"corrected $\log n$")
    ax.plot(np.log2(n), float(original["slope"]) * original_x + float(original["intercept"]), color="#C84C4C", linewidth=1.1, linestyle="--", label="retired linear n")
    ax.set_xticks(np.log2(n), [str(int(value)) for value in n])
    ax.set_xlabel("Number of agents n")
    ax.set_ylabel("Restricted mean all-agent episode")
    ax.set_title("(c) Simultaneous-agent concentration")
    ax.legend(frameon=False)
    ax.grid(alpha=0.18)

    ax = axes[1, 1]
    for m, color in ((4, "#355C9A"), (8, "#2A9D8F"), (16, "#C84C4C")):
        selected = sorted(
            (
                row
                for row in proxy
                if int(row["m"]) == m and int(row["H"]) == 1
            ),
            key=lambda row: int(row["checkpoint"]),
        )
        xx = [int(row["checkpoint"]) for row in selected]
        yy = [float(row["mean_cumulative_proxy"]) for row in selected]
        ax.plot(xx, yy, marker="o", markersize=3.5, color=color, label=f"m={m}, H=1")
    ax.set_xscale("log", base=2)
    ax.set_xlabel("Terminal episode K")
    ax.set_ylabel(r"Mean $H\sum_{k\leq K}(1-\mu_k(\theta^*))$")
    ax.set_title("(d) K-independent type-error proxy")
    ax.legend(frameon=False)
    ax.grid(alpha=0.18)

    figure.suptitle(
        "Claim B v3: " + ("all locked gates pass" if supported else "one or more locked gates fail"),
        fontsize=10.5,
        fontweight="bold",
    )
    for path in OUTPUTS:
        path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(path, dpi=240, bbox_inches="tight")
    plt.close(figure)
    print(json.dumps({"status": "ok", "supported": supported, "outputs": [path.relative_to(ROOT).as_posix() for path in OUTPUTS]}, indent=2))


if __name__ == "__main__":
    main()
