"""Plot E-1.1 analytic-tier n-scaling for all 9 baselines."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "analysis" / "e1_1_n_scaling" / "summary.json"
FIG_DIR = ROOT / "arr_paper" / "figs"

ALGO_STYLE = {
    "hpsmg_plus":              ("PACT+",                 "#1b3a6f", "D", "-",  2.0),
    "hpsmg":                   ("PACT",                  "#3d6cb3", "o", "-",  1.6),
    "joint_psrl":              ("Joint-PSRL",            "#c44e52", "s", "-",  1.6),
    "map_greedy":              ("MAP-greedy",            "#8172b2", "^", "--", 1.4),
    "psrl_notype":             ("PSRL (no type)",        "#937860", "v", "--", 1.4),
    "iql":                     ("IQL (joint)",           "#da8b41", "x", ":",  1.4),
    "iql_independent_actions": ("IQL (indep)",           "#dd8452", "+", ":",  1.4),
    "random":                  ("Random",                "#999999", "P", ":",  1.2),
    "oracle":                  ("Oracle (known types)",  "#4c956c", "*", "-",  1.4),
}


def main() -> None:
    rows = json.loads(SUMMARY.read_text(encoding="utf-8"))["rows"]
    ns = sorted({r["n"] for r in rows})

    fig, ax = plt.subplots(figsize=(8.0, 5.0))
    for algo, (label, color, marker, ls, lw) in ALGO_STYLE.items():
        xs, ys, es = [], [], []
        for n in ns:
            r = next((x for x in rows if x["n"] == n and x["algorithm"] == algo), None)
            if r is None:
                continue
            xs.append(n)
            ys.append(r["final_cumulative_regret_mean"])
            es.append(r["final_cumulative_regret_sem"])
        if not xs:
            continue
        ax.errorbar(xs, ys, yerr=es, label=label, color=color, marker=marker,
                    linestyle=ls, markersize=6.5, linewidth=lw, capsize=2.5)

    ax.set_yscale("symlog", linthresh=1.0)
    ax.set_xlabel("Number of agents n")
    ax.set_ylabel("Final cumulative regret (K=20, symlog)")
    ax.set_title(r"E-1.1 n-scaling on HP-SPGG (|$\Theta$|=4, |A|=5)")
    ax.set_xticks(ns)
    ax.grid(alpha=0.25, linestyle=":")
    ax.legend(loc="center right", fontsize=8, ncol=1)
    fig.tight_layout()

    out = FIG_DIR / "fig_e1_1_n_scaling.pdf"
    fig.savefig(out)
    fig.savefig(out.with_suffix(".png"), dpi=180)
    plt.close(fig)
    print(f"OK figure: {out}")


if __name__ == "__main__":
    main()
