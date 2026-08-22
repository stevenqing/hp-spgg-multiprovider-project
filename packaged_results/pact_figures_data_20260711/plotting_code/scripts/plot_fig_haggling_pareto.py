"""Fig 11: Haggling blend beta-sweep, mirroring Figure 2's beta-sweep style.

Per-config 2x2 panel. Each panel:
- x-axis: blend dial beta in [0, 1]
- left y-axis (solid blue, circles): focal payoff F  (more = more greedy)
- right y-axis (dashed red, squares): min surplus M  (more = more fair)
- vertical guide lines at beta=0 (Oracle_joint) and beta=1 (Oracle_focal)
- thin horizontal dotted reference: A-ToM-2 baseline on F (if available)

The visual story: as beta increases, focal payoff F monotonically rises
and fairness M monotonically falls; both endpoints coincide with the
respective oracles.
"""
from __future__ import annotations
import json
from pathlib import Path
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

mpl.rcParams.update({
    "font.family": "serif", "font.size": 8,
    "pdf.fonttype": 42, "ps.fonttype": 42,
    "figure.facecolor": "white", "axes.facecolor": "white",
})

ROOT = Path(__file__).resolve().parents[1]
FIGS = ROOT / "figs"
ANA = ROOT / "analysis"

CONFIGS = [
    ("Fruitville: gullible buyer",
     "concordia_haggling_blend_fruitville_gullible_s30.json",
     "concordia_haggling_compact_fruitville_gullible_s30_v3.json"),
    ("Vegbrooke: stubborn seller",
     "concordia_haggling_blend_vegbrooke_stubborn_s30.json",
     "concordia_haggling_compact_vegbrooke_stubborn_s30_v3.json"),
    ("Multi-item: cumulative",
     "concordia_haggling_blend_multi_cumulative_score_s30.json",
     "concordia_haggling_multi_item_compact_cumulative_score_s30_v3.json"),
    ("Multi-item: gullible",
     "concordia_haggling_blend_multi_fruitville_gullible_s30.json",
     "concordia_haggling_multi_item_compact_fruitville_gullible_s30_v3.json"),
]
BETAS = [0, 10, 20, 30, 40, 60, 80, 100]
F_COLOR = "#1f4e79"   # focal payoff (left axis)
M_COLOR = "#c44536"   # min surplus  (right axis)


def load_points(path: Path):
    if not path.exists(): return {}
    d = json.load(open(path, encoding="utf-8"))
    return {r["method"]: (r["focal_score_mean"], r["deal_min_score_mean"])
            for r in d["summary"]}


def main() -> None:
    fig, axes = plt.subplots(
        2, 2, figsize=(3.3, 3.3),
        gridspec_kw=dict(hspace=0.55, wspace=1.05, left=0.15,
                         right=0.82, top=0.93, bottom=0.20),
    )
    for ax_idx, (ax, (title, blend_name, v3_name)) in enumerate(
            zip(axes.flat, CONFIGS)):
        b = load_points(ANA / blend_name)
        v = load_points(ANA / v3_name)
        merged = {**v, **b}

        # Collect blend trajectory keyed by beta
        beta_x, fs, ms = [], [], []
        for a in BETAS:
            key = f"hpsmg_plus_blend_a{a}"
            if key not in merged: continue
            beta_x.append(a / 100.0)
            fs.append(merged[key][0]); ms.append(merged[key][1])

        # Left y-axis: F
        ax.plot(beta_x, fs, "-o", color=F_COLOR, lw=1.5, ms=4,
                mec="white", mew=0.6, zorder=4)
        ax.set_ylabel(r"$F$", color=F_COLOR, fontsize=8, labelpad=2)
        ax.tick_params(axis="y", labelcolor=F_COLOR, labelsize=6.5, pad=1.5)
        ax.tick_params(axis="x", labelsize=6.5, pad=1.5)
        ax.set_xticks([0.0, 0.5, 1.0])
        ax.set_xlim(-0.05, 1.05)
        ax.grid(True, alpha=0.22, lw=0.5)

        # Vertical guide lines at endpoints
        ax.axvline(0.0, color="#bbbbbb", lw=0.6, ls=":", zorder=1)
        ax.axvline(1.0, color="#bbbbbb", lw=0.6, ls=":", zorder=1)

        # Right y-axis: M
        ax2 = ax.twinx()
        ax2.plot(beta_x, ms, "--s", color=M_COLOR, lw=1.3, ms=3.5,
                 mec="white", mew=0.5, zorder=4)
        ax2.set_ylabel(r"$M$", color=M_COLOR, fontsize=8, labelpad=2)
        ax2.tick_params(axis="y", labelcolor=M_COLOR, labelsize=6.5, pad=1.5)

        # Endpoint annotations: J at beta=0, F at beta=1; place above the dot
        if beta_x:
            ax.annotate("J", (0.0, fs[0]), xytext=(2, 8),
                        textcoords="offset points", fontsize=7.5,
                        color="#222222", ha="left", va="bottom",
                        fontweight="bold")
            ax.annotate("F", (1.0, fs[-1]), xytext=(-2, -10),
                        textcoords="offset points", fontsize=7.5,
                        color="#222222", ha="right", va="top",
                        fontweight="bold")

        ax.set_title(title, fontsize=7.5, pad=3)

    # Shared x-axis label
    fig.text(0.49, 0.105, r"blend dial $\beta$  "
             r"($\beta{=}0$: Oracle$_{\mathrm{joint}}$, $\beta{=}1$: Oracle$_{\mathrm{focal}}$)",
             ha="center", fontsize=7.5)

    # Bottom legend
    handles = [
        Line2D([0], [0], color=F_COLOR, lw=1.5, marker="o", ms=4, mec="white",
               label=r"focal payoff $F$ (greedy $\uparrow$)"),
        Line2D([0], [0], color=M_COLOR, lw=1.3, ls="--", marker="s", ms=3.5,
               mec="white", label=r"min surplus $M$ (fair $\uparrow$)"),
    ]
    fig.legend(handles=handles, loc="lower center",
               bbox_to_anchor=(0.49, 0.005),
               ncol=2, fontsize=7, frameon=False,
               handlelength=1.8, handletextpad=0.4, columnspacing=1.4)

    fig.savefig(FIGS / "fig11_haggling_pareto.pdf", bbox_inches="tight")
    fig.savefig(FIGS / "fig11_haggling_pareto.png", bbox_inches="tight", dpi=200)
    print("wrote", FIGS / "fig11_haggling_pareto.pdf")


if __name__ == "__main__":
    main()
