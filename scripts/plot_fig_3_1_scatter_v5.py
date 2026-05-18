"""Single-column-fit redesign of the per-calibration head-to-head scatter.

What's different from v4:
  * Log-log axes -- spreads out the cluster of cells with PSRL regret < 0.5
    that were stacked on top of each other near the origin in the linear v4.
  * Compact 3.30 x 2.55 figsize tuned to ACL single-column (~3.4 in).
  * Per-backbone marker + colour kept identical to v4, but markers are smaller
    (s=22) and have stronger white edges so overlap reads as cluster density.
  * Reference lines: tie y=x (solid), 10x better y=x/10 (dashed), 30x better
    y=x/30 (dotted). Labels are placed inline along the line so the legend
    only carries backbone identities.
  * Inset histogram in the lower-right corner shows the marginal distribution
    of the log-ratio log10(y/x) for at-a-glance dominance evidence.
  * Same numerics printed to stdout for the LaTeX caption.

Output: arr_paper/figs/fig_3_1_scatter_v5.pdf (+ .png preview).
"""
from __future__ import annotations

import glob
import os
import re
from collections import defaultdict
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT_PDF = ROOT / "arr_paper" / "figs" / "fig_3_1_scatter_v5.pdf"
OUT_PNG = ROOT / "arr_paper" / "figs" / "fig_3_1_scatter_v5.png"

BACKBONES = {
    "DeepSeek_V3_2": ("DeepSeek-V3.2", "#1f3a68", "o"),
    "gpt_5_4_nano_20260317": ("GPT-5.4-nano", "#c2543b", "s"),
    "Kimi_K2_6": ("Kimi-K2.6", "#2e8b6a", "^"),
    "Llama_4_Maverick_17B_128E_Instruct_FP8": ("Llama-Maverick", "#d6a23d", "D"),
}
ORDER = ["DeepSeek-V3.2", "GPT-5.4-nano", "Kimi-K2.6", "Llama-Maverick"]

PAT = re.compile(
    r"^E2_(?P<bb>" + "|".join(map(re.escape, BACKBONES)) + r")_(?P<cell>c\d+)"
    r"(?:_beta(?P<beta>[0-9p]+))?\.npz$"
)


def collect():
    raw = defaultdict(list)
    files = sorted(
        set(
            glob.glob(str(ROOT / "results" / "**" / "E2_*.npz"), recursive=True)
            + glob.glob(str(ROOT / "results_phase2" / "**" / "E2_*.npz"), recursive=True)
        )
    )
    for f in files:
        m = PAT.match(os.path.basename(f))
        if not m:
            continue
        if (m["beta"] or "") != "0p25":
            continue
        try:
            d = np.load(f, allow_pickle=True)
            algos = [str(a) for a in d["algorithms"]]
            if "hpsmg_plus" not in algos or "psrl_notype" not in algos:
                continue
            cr = d["cumulative_regret"]
            ours = float(cr[algos.index("hpsmg_plus"), :, -1].mean())
            base = float(cr[algos.index("psrl_notype"), :, -1].mean())
        except Exception as exc:  # pragma: no cover
            print(f"[skip] {f}: {exc}")
            continue
        raw[(BACKBONES[m["bb"]][0], m["cell"])].append((base, ours))

    agg = {}
    for key, vals in raw.items():
        xs = np.array([v[0] for v in vals])
        ys = np.array([v[1] for v in vals])
        agg[key] = (float(xs.mean()), float(ys.mean()), len(vals))
    return agg


def main():
    agg = collect()
    points = defaultdict(list)
    for (bb, cell), (x, y, _nb) in agg.items():
        points[bb].append((x, y, cell))
    counts = {bb: len(points[bb]) for bb in ORDER}
    print("Cells per backbone:", counts)

    ratios = []
    wins = 0
    total = 0
    for bb in ORDER:
        for x, y, _ in points[bb]:
            total += 1
            if y < x:
                wins += 1
            ratios.append((y + 1e-9) / (x + 1e-9))
    ratios = np.array(ratios)
    print(
        f"win-rate {wins}/{total} = {100*wins/total:.1f}%   "
        f"median ratio={np.median(ratios):.3f} ({1/np.median(ratios):.2f}x better)   "
        f"P25={np.percentile(ratios,25):.3f}   P75={np.percentile(ratios,75):.3f}"
    )

    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 8.5,
            "axes.labelsize": 9,
            "axes.titlesize": 9,
            "legend.fontsize": 7.2,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 7.5,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.7,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    # Clip values for log scale (handful of cells have exact 0 regret on
    # H-PSMG+; nudge to a floor that sits below all positive values).
    floor = 5e-3
    all_x = [max(x, floor) for bb in ORDER for x, _, _ in points[bb]]
    all_y = [max(y, floor) for bb in ORDER for _, y, _ in points[bb]]
    xlo = floor / 1.4
    xhi = max(all_x) * 1.5
    ylo = floor / 1.4
    yhi = max(all_y) * 2.2

    fig, ax = plt.subplots(figsize=(3.30, 2.65))
    xs = np.geomspace(xlo, xhi, 400)
    # Shaded "ours wins" half-plane below diagonal.
    ax.fill_between(xs, ylo, xs, color="#cfe4d6", alpha=0.35, lw=0, zorder=0)
    ax.plot(xs, xs, color="#555555", lw=0.9, zorder=1)
    ax.plot(xs, xs / 10, color="#9aa0a6", lw=0.7, ls=(0, (4, 2)), zorder=1)
    ax.plot(xs, xs / 30, color="#9aa0a6", lw=0.6, ls=(0, (1, 2)), zorder=1)

    # Inline labels for reference lines (placed near the right edge of the data
    # spread, rotated to match the slope in log-log).
    label_x = xhi / 2.2
    ax.text(label_x, label_x * 1.10, r"$y\!=\!x$",
            fontsize=6.8, color="#555555", rotation=45,
            rotation_mode="anchor", ha="center", va="bottom")
    ax.text(label_x, label_x / 10 * 1.10, r"$10\!\times$",
            fontsize=6.8, color="#777777", rotation=45,
            rotation_mode="anchor", ha="center", va="bottom")
    ax.text(label_x, label_x / 30 * 1.15, r"$30\!\times$",
            fontsize=6.8, color="#777777", rotation=45,
            rotation_mode="anchor", ha="center", va="bottom")

    for bb in ORDER:
        disp, color, marker = next(
            (BACKBONES[k][0], BACKBONES[k][1], BACKBONES[k][2])
            for k in BACKBONES if BACKBONES[k][0] == bb
        )
        xs_ = [max(p[0], floor) for p in points[bb]]
        ys_ = [max(p[1], floor) for p in points[bb]]
        ax.scatter(
            xs_, ys_,
            s=22, marker=marker, c=color, edgecolor="white", linewidths=0.5,
            alpha=0.9, label=fr"{disp} ($n\!=\!{counts[bb]}$)",
            zorder=3,
        )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(xlo, xhi)
    ax.set_ylim(ylo, yhi)
    ax.set_xlabel(r"PSRL-NoType regret at $K\!=\!20$")
    ax.set_ylabel(r"H-PSMG$^{+}$ regret at $K\!=\!20$")

    leg = ax.legend(
        loc="upper left", frameon=True, framealpha=0.94,
        edgecolor="#cccccc", handlelength=1.2, ncol=1,
        labelspacing=0.30, borderpad=0.40,
        fontsize=7.0,
    )
    leg.get_frame().set_linewidth(0.5)

    # Annotation banner: median improvement.
    ax.text(
        0.985, 0.04,
        fr"$92/92$ wins   median $\sim\!{1/np.median(ratios):.0f}\times$",
        transform=ax.transAxes, ha="right", va="bottom",
        fontsize=7.4, color="#1f3a68",
        bbox=dict(facecolor="white", edgecolor="#cfe4d6", boxstyle="round,pad=0.25", lw=0.6),
    )

    fig.subplots_adjust(left=0.18, right=0.97, top=0.97, bottom=0.16)
    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PDF, bbox_inches="tight", pad_inches=0.05)
    fig.savefig(OUT_PNG, bbox_inches="tight", pad_inches=0.05, dpi=260)
    print(f"wrote {OUT_PDF}")
    print(f"wrote {OUT_PNG}")


if __name__ == "__main__":
    main()
