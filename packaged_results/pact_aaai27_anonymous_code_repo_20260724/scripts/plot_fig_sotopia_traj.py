"""Render the trajectory-level SOTOPIA-Hard figure from the partial-judge cache.

x-axis: turn checkpoint k in {2, 4, 6}.
y-axis: focal score (mean of agent_1 and agent_2 of the partial-judge overall),
       averaged over all four backbones and over episodes within the family.
Three panels: craigslist_bargains, revenge_plot, donate_funds.
One line per baseline (5 baselines), PACT+ bolded.

The k=6 point uses the existing source JSONs (full-episode score).
The k=2 and k=4 points use ``analysis/sotopia_partial_judge_cache.json`` produced
by ``scripts/sotopia_partial_judge.py``.

Output: arr_paper/figs/fig_sotopia_traj_v1.{pdf,png}.
"""
from __future__ import annotations

import glob
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "analysis" / "sotopia_partial_judge_cache.json"

FAMILIES = [
    ("craigslist_bargains", "Craigslist bargains", 80),
    ("revenge_plot", "Revenge plot", 20),
    ("donate_funds", "Donate funds", 20),
]

# Baseline display order + colours. PACT+ uses our signature deep navy.
# oracle_policy is shown as a dark-red upper bound (best-of-K + one-hot persona).
BASELINES = [
    ("llm_greedy", "llm_greedy", "#b8bcc2", "--", 1.0, "normal"),
    ("llm_belief", "llm_belief", "#a99c84", "--", 1.0, "normal"),
    ("econ_bne",   "ECON-BNE",   "#d68a76", "-.", 1.1, "normal"),
    ("atom_tom1",  "A-ToM-1",    "#7fbf9c", "-.", 1.1, "normal"),
    ("hpsmg_plus", "PACT$^{+}$", "#0b3a8c", "-", 2.6, "bold"),
    ("oracle_policy", "Oracle-policy (best-of-$K{=}5$)", "#b00020", (0, (4, 2)), 2.0, "bold"),
]

BACKBONES = [
    "DeepSeek_V3_2",
    "gpt_5_4_nano_20260317",
    "Kimi_K2_6",
    "Llama_4_Maverick_17B_128E_Instruct_FP8",
]

FILE_RE = re.compile(
    r"^sotopia_hard_official_(?P<bb>" + "|".join(map(re.escape, BACKBONES)) + r")_(?P<baseline>[a-z0-9_]+)_sotopia_tuned_all70\.json$"
)
# Some rerun files use dash/dot notation in the backbone token; map back.
DASH_TO_UNDERSCORE = {
    "DeepSeek-V3.2": "DeepSeek_V3_2",
    "gpt-5.4-nano-20260317": "gpt_5_4_nano_20260317",
    "Kimi-K2.6": "Kimi_K2_6",
    "Llama-4-Maverick-17B-128E-Instruct-FP8": "Llama_4_Maverick_17B_128E_Instruct_FP8",
}
FILE_DASH_RE = re.compile(
    r"^sotopia_hard_official_(?P<bb>" + "|".join(map(re.escape, DASH_TO_UNDERSCORE)) + r")_(?P<baseline>[a-z0-9_]+)_sotopia_tuned_all70\.json$"
)


def family_of(codename: str) -> str:
    parts = codename.split("_")
    while parts and parts[-1].isdigit():
        parts.pop()
    return "_".join(parts)


def load_k6() -> dict[tuple[str, str, str], list[float]]:
    """Read existing full-episode scores from analysis/sotopia_hard_official_*.json.
    Returns dict[(backbone, baseline, family)] -> list of per-episode focal scores."""
    out: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    paths = sorted(
        list((ROOT / "analysis").glob("sotopia_hard_official_*_sotopia_tuned_all70.json"))
        + list((ROOT / "analysis" / "rerun_20260518").glob("sotopia_hard_official_*_sotopia_tuned_all70.json"))
        # The oracle_policy full-episode rerun artifacts live in the archive;
        # partial-judge cache has k=1..5, so these files provide the missing k=6 endpoint.
        + list((ROOT / "_archive" / "analysis_intermediate" / "rerun_20260518").glob("sotopia_hard_official_*_oracle_policy_sotopia_tuned_all70.json"))
    )
    for path in paths:
        m = FILE_RE.match(path.name)
        if m:
            bb, baseline = m["bb"], m["baseline"]
        else:
            m = FILE_DASH_RE.match(path.name)
            if not m:
                continue
            bb, baseline = DASH_TO_UNDERSCORE[m["bb"]], m["baseline"]
        data = json.loads(path.read_text(encoding="utf-8"))
        for ep in data.get("episodes", []):
            fam = family_of(ep.get("codename", ""))
            if fam not in {f[0] for f in FAMILIES}:
                continue
            ov = ep.get("overall", {})
            a1 = ov.get("agent_1")
            a2 = ov.get("agent_2")
            if a1 is None or a2 is None:
                continue
            out[(bb, baseline, fam)].append(0.5 * (a1 + a2))
    return out


def load_partial() -> dict[tuple[str, str, str, int], list[float]]:
    """Read partial-judge cache -> dict[(backbone, baseline, family, k)] -> list of focal scores."""
    out: dict[tuple[str, str, str, int], list[float]] = defaultdict(list)
    if not CACHE.exists():
        print("WARNING: partial cache not found")
        return out
    data = json.loads(CACHE.read_text(encoding="utf-8"))
    for key, v in data.get("entries", {}).items():
        if "overall" not in v:
            continue
        bb, baseline, combo, kk = key.split("|")
        k = int(kk[1:])
        fam = v.get("family", "?")
        ov = v["overall"]
        out[(bb, baseline, fam, k)].append(0.5 * (ov["agent_1"] + ov["agent_2"]))
    return out


def main() -> None:
    k6 = load_k6()
    partial = load_partial()

    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 13,
            "axes.labelsize": 9.5,
            "axes.titlesize": 10,
            "legend.fontsize": 7.6,
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 8.5,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.7,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "text.usetex": False,
        }
    )

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 3.2), sharey=False)
    ks = [1, 2, 3, 4, 5, 6]
    panel_lims = []  # collect (lo, hi) over k>=2 to zoom y-axis
    for ax, (fam, fam_disp, n_full) in zip(axes, FAMILIES):
        panel_lo, panel_hi = float("inf"), float("-inf")
        for bl, disp, color, ls, lw, _w in BASELINES:
            means, sems = [], []
            for k in ks:
                vals: list[float] = []
                for bb in BACKBONES:
                    if k == 6:
                        vals.extend(k6.get((bb, bl, fam), []))
                    else:
                        vals.extend(partial.get((bb, bl, fam, k), []))
                if not vals:
                    means.append(np.nan); sems.append(0.0); continue
                vals = np.array(vals, dtype=float)
                means.append(float(vals.mean()))
                sems.append(float(vals.std(ddof=1) / np.sqrt(len(vals))) if len(vals) > 1 else 0.0)
            means = np.array(means); sems = np.array(sems)
            # track tight ylim using k>=2 only
            for i, k in enumerate(ks):
                if k >= 2 and not np.isnan(means[i]):
                    panel_lo = min(panel_lo, means[i] - sems[i])
                    panel_hi = max(panel_hi, means[i] + sems[i])
            ax.plot(ks, means, marker="o", ms=3.6 if bl != "hpsmg_plus" else 7.2,
                    color=color, ls=ls, lw=lw, label=disp,
                    markeredgecolor="white" if bl == "hpsmg_plus" else color,
                    markeredgewidth=0.9 if bl == "hpsmg_plus" else 0.0,
                    zorder=6 if bl == "hpsmg_plus" else 2,
                    alpha=1.0 if bl == "hpsmg_plus" else 0.85)
            ax.fill_between(ks, means - sems, means + sems, color=color,
                            alpha=0.18 if bl == "hpsmg_plus" else 0.06, lw=0,
                            zorder=5 if bl == "hpsmg_plus" else 1)
        ax.set_xticks(ks)
        ax.set_xlabel("Turn checkpoint $k$ (utterances seen by judge)")
        ax.set_xlim(0.7, 6.3)
        # tighten y to k>=2 data range with small pad, so k=1 dip doesn't squash the gaps
        pad = 0.05 * (panel_hi - panel_lo)
        ax.set_ylim(panel_lo - pad, panel_hi + pad)
        ax.set_title(f"{fam_disp}  (n={n_full})")
        ax.grid(True, alpha=0.25, ls=":", lw=0.5)
        panel_lims.append((panel_lo, panel_hi))
    axes[0].set_ylabel("Mean focal score (partial-transcript judge)")

    # Single legend at top-right of left panel (compact).
    leg = axes[0].legend(loc="upper left", frameon=True, framealpha=0.94,
                         edgecolor="#cccccc", labelspacing=0.35, borderpad=0.4,
                         handlelength=1.6, fontsize=7.6)
    leg.get_frame().set_linewidth(0.5)
    for text in leg.get_texts():
        if "PACT" in text.get_text():
            text.set_fontweight("bold")

    fig.subplots_adjust(left=0.13, right=0.99, top=0.90, bottom=0.18, wspace=0.18)
    out_pdf = ROOT / "arr_paper" / "figs" / "fig_sotopia_traj_v1.pdf"
    out_png = ROOT / "arr_paper" / "figs" / "fig_sotopia_traj_v1.png"
    fig.savefig(out_pdf)
    fig.savefig(out_png, dpi=240)
    overleaf_dir = ROOT / "arr_paper_overleaf" / "figs"
    if overleaf_dir.exists():
        shutil.copy2(out_pdf, overleaf_dir / out_pdf.name)
        shutil.copy2(out_png, overleaf_dir / out_png.name)
    print(f"wrote {out_pdf}")
    print(f"wrote {out_png}")

    # Print numbers for caption.
    print("\nMean focal score by (family, baseline, k), averaged across 4 backbones:")
    for fam, fam_disp, _ in FAMILIES:
        print(f"  {fam_disp}:")
        for bl, disp, *_ in BASELINES:
            row = []
            for k in ks:
                vals = []
                for bb in BACKBONES:
                    if k == 6:
                        vals.extend(k6.get((bb, bl, fam), []))
                    else:
                        vals.extend(partial.get((bb, bl, fam, k), []))
                if vals:
                    row.append(f"k{k}={np.mean(vals):.3f}")
                else:
                    row.append(f"k{k}=--")
            disp_plain = re.sub(r"\\\\?[a-zA-Z]+\{?|\}\$?|\$|\\", "", disp)
            print(f"    {disp_plain:16s} " + "  ".join(row))


if __name__ == "__main__":
    main()
