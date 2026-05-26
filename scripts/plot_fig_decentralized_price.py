"""Fig 12: price of decentralisation on Concordia london_mini (bars + lines).

Four-panel layout:
  (a) focal payoff (mean of focal_score_mean) -- grouped bars per backbone
  (b) coordination rate -- grouped bars per backbone
  (c) social welfare W = sum_{i=1..5} score_i -- grouped bars per backbone
  (d) cumulative focal regret over K=5 episode seeds -- one line per method,
      mean +/- SE across the 4 backbones

Source: analysis/concordia_pub_coordination_compact_L3_{slug}_s5.json
"""
from __future__ import annotations
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

mpl.rcParams.update({
    "font.family": "serif", "font.size": 9,
    "pdf.fonttype": 42, "ps.fonttype": 42,
    "figure.facecolor": "white", "axes.facecolor": "white",
})

ROOT = Path(__file__).resolve().parents[1]
FIGS = ROOT / "figs"
ANALYSIS = ROOT / "analysis"

BACKBONES = [
    ("gpt_5_4_nano_20260317",                  "GPT-5.4-nano"),
    ("DeepSeek_V3_2",                          "DeepSeek-V3.2"),
    ("Kimi_K2_6",                              "Kimi-K2.6"),
    ("Llama_4_Maverick_17B_128E_Instruct_FP8", "Llama-4-Mav."),
]

# (key, display, color) -- bars in this order, oracle is reference line only
METHOD_TIERS = [
    ("centralized_planner_llm", "Centralized planner LLM",      "#1f4e79"),
    ("chat_agent_llm",          "Per-agent type-guess LLM",     "#5a8fc5"),
    ("llm_belief",              "Decentralized LLM (ToM)",      "#d98a5a"),
    ("llm_greedy",              "Decentralized LLM (greedy)",   "#c44536"),
]
ORACLE_KEY = "oracle_joint"
ORACLE_COLOR = "#2f2f2f"


def load_backbone(slug: str) -> dict[str, dict]:
    f = ANALYSIS / f"concordia_pub_coordination_compact_L3_{slug}_s5.json"
    d = json.load(open(f, encoding="utf-8"))
    per_method: dict[str, dict] = {}
    for ep in d["episodes"]:
        b = per_method.setdefault(ep["method"], {
            "focal": [], "coord": [], "welfare": [],
            "seeds": [], "focal_by_seed": {},
        })
        b["focal"].append(float(ep["focal_score_mean"]))
        b["coord"].append(float(ep["coordination_rate"]))
        b["welfare"].append(float(sum(ep["scores"].values())))
        b["seeds"].append(int(ep["seed"]))
        b["focal_by_seed"][int(ep["seed"])] = float(ep["focal_score_mean"])
    return per_method


def mean_se(xs: list[float]) -> tuple[float, float]:
    arr = np.asarray(xs, dtype=float)
    if arr.size == 0:
        return 0.0, 0.0
    return float(arr.mean()), float(arr.std(ddof=1) / np.sqrt(arr.size)) if arr.size > 1 else 0.0


def grouped_bars(ax, all_data: list[dict], field: str, ylabel: str, title: str,
                 oracle_each_backbone: list[float] | None = None,
                 show_legend: bool = False):
    n_bb = len(BACKBONES)
    n_m = len(METHOD_TIERS)
    width = 0.8 / n_m
    x = np.arange(n_bb)
    for i, (key, disp, color) in enumerate(METHOD_TIERS):
        means, ses = [], []
        for bb in all_data:
            xs = bb.get(key, {}).get(field, [])
            m, s = mean_se(xs)
            means.append(m); ses.append(s)
        offs = (i - (n_m - 1) / 2) * width
        ax.bar(x + offs, means, width=width * 0.95, yerr=ses,
               color=color, label=disp, capsize=2.5,
               error_kw={"elinewidth": 0.8, "ecolor": "#404040"})
    if oracle_each_backbone is not None:
        for j, val in enumerate(oracle_each_backbone):
            ax.hlines(val, x[j] - 0.42, x[j] + 0.42,
                      colors=ORACLE_COLOR, linestyles=(0, (3, 2)),
                      linewidth=1.3, zorder=4,
                      label="Oracle (privileged)" if j == 0 else None)
    ax.set_xticks(x)
    ax.set_xticklabels([d for _, d in BACKBONES], rotation=12, fontsize=8)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.set_title(title, fontsize=10.5)
    ax.grid(axis="y", alpha=0.3, linestyle=":")
    ax.set_axisbelow(True)


def cum_regret_lines(ax, all_data: list[dict]):
    """One line per method: cumulative regret vs oracle_joint across K=5 seeds,
       mean +/- SE across the 4 backbones."""
    K = 5
    ks = np.arange(1, K + 1)
    for (key, disp, color) in METHOD_TIERS:
        per_bb_curves = []
        for bb in all_data:
            if key not in bb or ORACLE_KEY not in bb:
                continue
            oracle = bb[ORACLE_KEY]["focal_by_seed"]
            cand = bb[key]["focal_by_seed"]
            seeds = sorted(oracle)[:K]
            per_ep = [max(0.0, oracle[s] - cand.get(s, 0.0)) for s in seeds]
            per_bb_curves.append(np.cumsum(per_ep))
        if not per_bb_curves:
            continue
        arr = np.vstack(per_bb_curves)
        mu = arr.mean(axis=0)
        se = arr.std(axis=0, ddof=1) / np.sqrt(arr.shape[0]) if arr.shape[0] > 1 else np.zeros_like(mu)
        ax.plot(ks, mu, "-o", color=color, label=disp, linewidth=1.6, markersize=4)
        ax.fill_between(ks, mu - se, mu + se, color=color, alpha=0.18, linewidth=0)
    ax.axhline(0.0, color=ORACLE_COLOR, linestyle=(0, (3, 2)),
               linewidth=1.2, label="Oracle (privileged)")
    ax.set_xticks(ks)
    ax.set_xlabel("Episode index $k$", fontsize=9)
    ax.set_ylabel(r"Cumulative focal regret $\sum_{j\leq k}\Delta_j$", fontsize=9)
    ax.set_title("(d) Cumulative focal regret", fontsize=10.5)
    ax.grid(alpha=0.3, linestyle=":")
    ax.set_axisbelow(True)


def main() -> None:
    all_data = [load_backbone(slug) for slug, _ in BACKBONES]

    # Per-backbone oracle reference values
    oracle_focal   = [float(np.mean(bb[ORACLE_KEY]["focal"]))   for bb in all_data]
    oracle_coord   = [float(np.mean(bb[ORACLE_KEY]["coord"]))   for bb in all_data]
    oracle_welfare = [float(np.mean(bb[ORACLE_KEY]["welfare"])) for bb in all_data]

    fig, axes = plt.subplots(1, 4, figsize=(14.2, 3.1))
    grouped_bars(axes[0], all_data, "focal",
                 r"Focal payoff (mean)", "(a) Focal-player payoff",
                 oracle_each_backbone=oracle_focal)
    grouped_bars(axes[1], all_data, "coord",
                 r"Coordination rate", "(b) Coordination rate",
                 oracle_each_backbone=oracle_coord)
    grouped_bars(axes[2], all_data, "welfare",
                 r"Social welfare  $\sum_{i=1}^{5}\mathrm{score}_i$",
                 "(c) Social welfare",
                 oracle_each_backbone=oracle_welfare)
    cum_regret_lines(axes[3], all_data)

    # Shared legend across panels (use the 4 methods + oracle, once)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=5,
               bbox_to_anchor=(0.5, -0.06), fontsize=8.5, frameon=False,
               columnspacing=1.5, handletextpad=0.6)

    fig.tight_layout(rect=(0, 0.03, 1, 1))
    out_pdf = FIGS / "fig12_decentralized_price.pdf"
    out_png = FIGS / "fig12_decentralized_price.png"
    FIGS.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_pdf, bbox_inches="tight")
    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    print(f"saved {out_pdf}")
    print(f"saved {out_png}")


if __name__ == "__main__":
    main()
