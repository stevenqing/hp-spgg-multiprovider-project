"""Fig 7: HP-SPGG headline bar chart comparing Native (PACT/PACT+ and Bayesian
baselines), Prompted LLM, and External LLM families on the DeepSeek c19 K=20 s=5
cell. Data hardcoded from analysis/E2_native_vs_llm_baselines_stats.md (preserved
from 2026-05-17 archive bundle).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "arr_paper" / "figs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# (family, algorithm-id, display-label, mean, sem-from-ci-half-width)
# Means + bootstrap 95% CIs from analysis/E2_native_vs_llm_baselines_stats.md.
ROWS = [
    ("Native",       "oracle",              "Oracle",                 0.0000, 0.0000),
    ("Native",       "hpsmg_plus",          r"PACT$^+$ (ours)",       0.4000, 0.4000),
    ("Native",       "map_greedy",          "MAP-Type-Greedy",        0.7120, 0.2331),
    ("Native",       "hpsmg",               "PACT (ours)",            0.8280, 0.2707),
    ("Native",       "joint_psrl",          "Joint-PSRL",             0.8320, 0.0398),
    ("Prompted LLM", "llm_belief",          "LLM-Belief",             3.0740, 1.1154),
    ("External LLM", "econ_bne",            "ECON-BNE",               3.9900, 1.7068),
    ("External LLM", "atom_adaptive_hedge", "A-ToM Adaptive-Hedge",   4.7900, 2.2544),
    ("External LLM", "atom_tom0",           "A-ToM-0",                6.0000, 3.7283),
    ("External LLM", "atom_tom2",           "A-ToM-2",                13.4020, 5.1600),
    ("Native",       "psrl_notype",         "PSRL-NoType",            13.9120, 3.6868),
    ("Prompted LLM", "llm_greedy",          "LLM-Greedy",             14.0200, 7.3321),
    ("External LLM", "atom_adaptive_ftl",   "A-ToM Adaptive-FTL",     14.9440, 0.7156),
    ("External LLM", "atom_tom1",           "A-ToM-1",                16.6760, 4.1002),
    ("Native",       "random",              "Random",                 28.2660, 2.5621),
    ("Native",       "iql",                 "IQL",                    28.3420, 8.4568),
]

FAMILY_COLOR = {
    "Native":       "#1b3a6f",
    "Prompted LLM": "#8b6dc1",
    "External LLM": "#d68a3d",
}
# Highlight our methods with a distinct hue
OURS_COLOR = "#c44e52"
OURS_ALGOS = {"hpsmg_plus", "hpsmg"}

plt.rcParams.update({
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "legend.fontsize": 8,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "savefig.bbox": "tight",
    "savefig.dpi": 200,
})


def main() -> None:
    families = [r[0] for r in ROWS]
    algos = [r[1] for r in ROWS]
    labels = [r[2] for r in ROWS]
    means = np.array([r[3] for r in ROWS])
    sems = np.array([r[4] for r in ROWS])

    y = np.arange(len(ROWS))
    colors = [OURS_COLOR if a in OURS_ALGOS else FAMILY_COLOR[f]
              for f, a in zip(families, algos)]

    fig, ax = plt.subplots(figsize=(8.4, 5.6))
    bars = ax.barh(y, means, xerr=sems, color=colors,
                   edgecolor="black", linewidth=0.6,
                   error_kw={"elinewidth": 0.9, "capsize": 2.5, "ecolor": "#444"})

    # Annotate bars with mean
    for yi, m in zip(y, means):
        ax.text(m + 0.4, yi, f"{m:.2f}", va="center", fontsize=7.5, color="#222")

    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()  # best (oracle) at top
    ax.set_xlabel(r"Cumulative regret at $K=20$ (mean $\pm$ SEM, $5$ seeds)")
    ax.set_title("HP-SPGG headline: Native (Bayesian) vs Prompted LLM vs External LLM baselines\n"
                 "DeepSeek-V3.2, cell c19, $\\beta=0.25$")
    ax.grid(axis="x", alpha=0.25, linewidth=0.5)
    ax.set_xlim(0, max(means + sems) * 1.12)

    # Legend (family colors + ours)
    import matplotlib.patches as mpatches
    handles = [
        mpatches.Patch(color=OURS_COLOR, label="Ours (PACT family)"),
        mpatches.Patch(color=FAMILY_COLOR["Native"], label="Native (Bayesian baselines)"),
        mpatches.Patch(color=FAMILY_COLOR["Prompted LLM"], label="Prompted LLM"),
        mpatches.Patch(color=FAMILY_COLOR["External LLM"], label="External LLM (A-ToM, ECON-BNE)"),
    ]
    ax.legend(handles=handles, loc="lower right", frameon=True, framealpha=0.9)

    plt.tight_layout()
    out_pdf = OUT_DIR / "E2_native_vs_llm_baselines_main.pdf"
    out_png = OUT_DIR / "E2_native_vs_llm_baselines_main.png"
    fig.savefig(out_pdf)
    fig.savefig(out_png, dpi=180)
    plt.close(fig)
    print(f"OK: {out_pdf.name}")


if __name__ == "__main__":
    main()
