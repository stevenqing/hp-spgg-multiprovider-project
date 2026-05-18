"""Polished version of FINAL_3_1_scatter.

Reads E2_<backbone>_<profile>[_beta<x>].npz files for the four final backbones,
averages cumulative regret at K=20 over seeds and over the eight beta values per
calibration profile, and renders a head-to-head scatter (H-PSMG+ vs PSRL-NoType)
with one marker per (backbone, calibration profile) cell.

Design choices (per request: "high-end, less in-figure text, n explained in caption,
no overlap with other v5 figures"):
  - No in-figure stats box / title / per-point annotation. All numerics go to the
    LaTeX caption.
  - Single legend lists only the four backbones with their cell counts n.
  - Reference lines (y=x, 2x, 3x, 10x better) drawn faintly, labelled outside the
    plotting region in the legend.
  - Print median ratio statistics to stdout so the caption can quote exact numbers.

Output: arr_paper/figs/fig_3_1_scatter_v4.pdf (+ .png preview).
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
OUT_PDF = ROOT / "arr_paper" / "figs" / "fig_3_1_scatter_v4.pdf"
OUT_PNG = ROOT / "arr_paper" / "figs" / "fig_3_1_scatter_v4.png"

# Backbone canonical names + display palette (matches the deep-navy / coral / teal
# / amber spirit of fig10_hp_spgg_cross_model_v3 without copying its exact codes).
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
    """Return dict[(disp_backbone, profile)] -> (psrl_x, hpsmg_y, n_betas)."""
    raw = defaultdict(list)  # (bb, cell) -> list of (x, y)
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
        bb = m["bb"]
        cell = m["cell"]
        # Restrict to the canonical bonus setting beta=0.25 (matches main results
        # and Fig. fig10_beta_sweep_v3 -- "ours" elsewhere in the paper).
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
        raw[(BACKBONES[bb][0], cell)].append((base, ours))

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

    # Stats for caption
    ratios = []
    wins = 0
    total = 0
    best = None
    for bb in ORDER:
        for x, y, cell in points[bb]:
            total += 1
            if y < x:
                wins += 1
            r = (y + 1e-9) / (x + 1e-9)
            ratios.append(r)
            if best is None or r < best[0]:
                best = (r, bb, cell, x, y)
    ratios = np.array(ratios)
    print(
        f"win-rate {wins}/{total} = {100*wins/total:.1f}%   "
        f"median ratio={np.median(ratios):.3f} ({1/np.median(ratios):.2f}x better)   "
        f"P25={np.percentile(ratios,25):.3f}   P75={np.percentile(ratios,75):.3f}   "
        f"best={best[0]:.3f} ({1/best[0]:.1f}x) at {best[1]}/{best[2]}"
    )

    # --- plot ---
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 9,
            "axes.labelsize": 10,
            "axes.titlesize": 10,
            "legend.fontsize": 8.5,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.7,
            "xtick.major.width": 0.7,
            "ytick.major.width": 0.7,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    fig, ax = plt.subplots(figsize=(3.40, 3.10))
    all_x = [x for bb in ORDER for x, _, _ in points[bb]]
    all_y = [y for bb in ORDER for _, y, _ in points[bb]]
    xmax = max(all_x) * 1.06
    ymax = max(max(all_y) * 1.18, xmax / 3.5)  # leave room above max(y), below y=x/3

    # Reference lines: y=x (tie), and a few "k-times better" guides drawn faintly.
    xs = np.linspace(0, xmax * 1.5, 400)
    ax.plot(xs, xs, color="#555555", lw=0.9, label=r"tie ($y\!=\!x$)")
    for k, ls in [(3, (0, (4, 2))), (10, (0, (1, 2)))]:
        ax.plot(xs, xs / k, color="#9aa0a6", lw=0.6, ls=ls,
                label=fr"$y\!=\!x/{k}$")

    # Shaded "ours better" half-plane (clipped to axes).
    ax.fill_between(xs, 0, xs, color="#cfe4d6", alpha=0.30, lw=0)

    for bb in ORDER:
        disp, color, marker = next(
            (d, c, m) for (d, c, m) in (
                (BACKBONES[k][0], BACKBONES[k][1], BACKBONES[k][2]) for k in BACKBONES
            ) if d == bb
        )
        xs_ = [p[0] for p in points[bb]]
        ys_ = [p[1] for p in points[bb]]
        ax.scatter(
            xs_, ys_,
            s=30, marker=marker, c=color, edgecolor="white", linewidths=0.5,
            alpha=0.9, label=fr"{disp} ($n\!=\!{counts[bb]}$)",
            zorder=3,
        )

    ax.set_xlim(0, xmax)
    ax.set_ylim(0, ymax)
    ax.set_xlabel(r"PSRL-NoType cumulative regret at $K\!=\!20$")
    ax.set_ylabel(r"H-PSMG$^{+}$ cumulative regret at $K\!=\!20$")

    # Legend inside, upper-left, two columns, compact.
    leg = ax.legend(
        loc="upper left", frameon=True, framealpha=0.92,
        edgecolor="#cccccc", handlelength=1.4, ncol=2,
        columnspacing=0.9, labelspacing=0.35, borderpad=0.45,
        fontsize=7.6,
    )
    leg.get_frame().set_linewidth(0.5)
    for h in leg.legend_handles:
        try:
            h.set_alpha(1.0)
        except Exception:
            pass

    fig.subplots_adjust(left=0.16, right=0.98, top=0.97, bottom=0.13)
    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PDF, bbox_inches="tight", pad_inches=0.10)
    fig.savefig(OUT_PNG, bbox_inches="tight", pad_inches=0.10, dpi=240)
    print(f"wrote {OUT_PDF}")
    print(f"wrote {OUT_PNG}")


if __name__ == "__main__":
    main()
