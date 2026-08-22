"""Plot E-1.3 PF-isolation: regret vs Dirichlet alpha for all 9 algos."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "analysis" / "e1_3_pf_isolation" / "summary.json"
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
    "oracle":                  ("Oracle",                "#4c956c", "*", "-",  1.4),
}


def main() -> None:
    payload = json.loads(SUMMARY.read_text(encoding="utf-8"))
    rows = payload["rows"]
    # Two-panel: left = Dirichlet sweep, right = single shared_type bar group
    dir_rows = [r for r in rows if r["setting"].startswith("dirichlet_")]
    sh_rows = [r for r in rows if r["setting"] == "shared_type"]
    dir_alphas = sorted({r["alpha"] for r in dir_rows}, key=lambda a: 10.0 if a == "inf" else float(a))

    def xval(a: str) -> float:
        return 10.0 if a == "inf" else float(a)

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.0), gridspec_kw={"width_ratios": [2.2, 1.0]})
    ax = axes[0]
    for algo, (label, color, marker, ls, lw) in ALGO_STYLE.items():
        xs, ys, es = [], [], []
        for a in dir_alphas:
            r = next((x for x in dir_rows if x["alpha"] == a and x["algorithm"] == algo), None)
            if r is None:
                continue
            xs.append(xval(a))
            ys.append(r["mean"])
            es.append(r["sem"])
        if not xs:
            continue
        ax.errorbar(xs, ys, yerr=es, label=label, color=color, marker=marker,
                    linestyle=ls, markersize=6.5, linewidth=lw, capsize=2.5)
    ax.set_xscale("log")
    ax.set_yscale("symlog", linthresh=1.0)
    ax.set_xlabel(r"Dirichlet concentration $\alpha$ on joint type prior ($\infty$ = uniform)")
    ax.set_ylabel("Final cumulative regret (K=20, symlog)")
    ax.set_title(r"E-1.3a: symmetric Dirichlet joint prior on $|\Theta|^n=64$ profiles (n=3)")
    ax.set_xticks([xval(a) for a in dir_alphas])
    ax.set_xticklabels(dir_alphas)
    ax.grid(alpha=0.25, linestyle=":")
    ax.legend(loc="center right", fontsize=7)

    ax2 = axes[1]
    if sh_rows:
        order = list(ALGO_STYLE.keys())
        means = []
        sems = []
        labels = []
        colors = []
        for algo in order:
            r = next((x for x in sh_rows if x["algorithm"] == algo), None)
            if r is None:
                continue
            label, color, *_ = ALGO_STYLE[algo]
            means.append(r["mean"])
            sems.append(r["sem"])
            labels.append(label)
            colors.append(color)
        idx = list(range(len(means)))
        ax2.barh(idx, means, xerr=sems, color=colors, edgecolor="black", linewidth=0.4)
        ax2.set_yticks(idx)
        ax2.set_yticklabels(labels, fontsize=8)
        ax2.set_xscale("symlog", linthresh=1.0)
        ax2.invert_yaxis()
        ax2.set_xlabel("Final cum regret (K=20)")
        ax2.set_title("E-1.3b: shared-type structured prior")
        ax2.grid(axis="x", alpha=0.25, linestyle=":")

    fig.tight_layout()
    out = FIG_DIR / "fig_e1_3_pf_isolation.pdf"
    fig.savefig(out)
    fig.savefig(out.with_suffix(".png"), dpi=180)
    plt.close(fig)
    print(f"OK figure: {out}")


if __name__ == "__main__":
    main()
