"""Fig 7 (SOTOPIA-Hard): report only the 3 in-scope scenario families,
each as a Fig-1-style horizontal bar chart comparing PACT$^+$ vs the four
alternative baselines, averaged across all 4 backbones.

Output: arr_paper/figs/fig_sotopia_three_exp_v1.{pdf,png}
"""
from __future__ import annotations
import json, glob, os, statistics
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

mpl.rcParams.update({"font.family": "serif", "font.size": 13, "pdf.fonttype": 42, "ps.fonttype": 42})

BASES = ["hpsmg_plus", "atom_tom1", "econ_bne", "llm_belief", "llm_greedy"]
LABELS = {
    "hpsmg_plus": "PACT$^{+}$ (ours)",
    "atom_tom1": "A-ToM-1",
    "econ_bne": "ECON-BNE",
    "llm_belief": "llm_belief",
    "llm_greedy": "llm_greedy",
}
COLORS = {
    "hpsmg_plus": "#1f2d5c",
    "atom_tom1": "#d8a04b",
    "econ_bne": "#a63a3a",
    "llm_belief": "#7a8aa6",
    "llm_greedy": "#bdbdbd",
}
ORDER = ["hpsmg_plus", "atom_tom1", "econ_bne", "llm_belief", "llm_greedy"]

SCENARIOS = [
    ("craigslist_bargains", "Craigslist bargains"),
    ("revenge_plot", "Revenge plot"),
    ("donate_funds", "Donate funds"),
]


def fam(code: str) -> str:
    parts = code.split("_")
    while parts and parts[-1].isdigit():
        parts.pop()
    return "_".join(parts) if parts else code


def load_buckets():
    # (family, baseline) -> list of episode focal scores across all backbones
    b = defaultdict(list)
    for p in sorted(glob.glob("analysis/sotopia_hard_official_*_sotopia_tuned_all70.json")):
        name = os.path.basename(p).replace("sotopia_hard_official_", "").replace("_sotopia_tuned_all70.json", "")
        bl = None
        for c in BASES:
            if name.endswith("_" + c):
                bl = c
                break
        if bl is None:
            continue
        d = json.load(open(p, encoding="utf-8"))
        for ep in d.get("episodes", []):
            code = ep.get("codename") or "?"
            ov = ep.get("overall") or {}
            vals = [v for v in ov.values() if isinstance(v, (int, float))]
            if not vals:
                continue
            b[(fam(code), bl)].append(sum(vals) / len(vals))
    return b


def plot(buckets, out_pdf):
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 3.2), sharex=False)
    for ax, (family, title) in zip(axes, SCENARIOS):
        means, stds, ns, cols, labels = [], [], [], [], []
        for m in ORDER:
            xs = buckets.get((family, m), [])
            if not xs:
                means.append(float("nan")); stds.append(0); ns.append(0)
            else:
                means.append(statistics.fmean(xs))
                stds.append(statistics.pstdev(xs) / max(1, len(xs)) ** 0.5)
                ns.append(len(xs))
            cols.append(COLORS[m])
            labels.append(LABELS[m])
        y = np.arange(len(ORDER))[::-1]
        ax.barh(y, means, xerr=stds, color=cols, edgecolor="black",
                linewidth=[1.3 if m == "hpsmg_plus" else 0.4 for m in ORDER],
                error_kw={"elinewidth": 0.8, "capsize": 2.5})
        ours = means[ORDER.index("hpsmg_plus")]
        best_alt = max(v for m, v in zip(ORDER, means) if m != "hpsmg_plus")
        for yi, v in zip(y, means):
            ax.text(v + 0.012, yi, f"{v:.2f}", va="center", fontsize=9, fontweight="bold")
        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=9)
        if ax is not axes[0]:
            ax.set_yticklabels([])
        for tick_label, m in zip(ax.get_yticklabels(), ORDER):
            if m == "hpsmg_plus":
                tick_label.set_fontweight("bold")
        ax.set_title(f"{title}  (n={ns[0]}, $\\Delta$={ours - best_alt:+.2f})", fontsize=10.5)
        xmin = min(means) - 0.10
        xmax = max([v + s for v, s in zip(means, stds)]) + 0.10
        ax.set_xlim(xmin, xmax)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.set_xlabel("Mean focal score (4 backbones)", fontsize=9.5)
    fig.subplots_adjust(left=0.13, right=0.99, top=0.90, bottom=0.18, wspace=0.18)
    fig.savefig(out_pdf)
    fig.savefig(out_pdf.replace(".pdf", ".png"), dpi=200)
    plt.close(fig)


def main():
    b = load_buckets()
    out = "arr_paper/figs/fig_sotopia_three_exp_v1.pdf"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    plot(b, out)
    for fam_name, _ in SCENARIOS:
        print(f"{fam_name}:")
        for m in ORDER:
            xs = b.get((fam_name, m), [])
            if xs:
                print(f"  {m:12s} n={len(xs):3d}  mean={statistics.fmean(xs):.3f}")
    print(f"[ok] wrote {out}")


if __name__ == "__main__":
    main()
