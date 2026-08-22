"""Fig 6 / Fig E5: per-episode cumulative-regret trajectories across 4 LLM backbones.

Reads the aggregated summary CSV at tables/E5_cross_model_cumulative_regret_summary.csv
(mean + SEM per (model, family, algorithm, episode_k); produced from the K=20 s=5
HP-SPGG cell c19, beta=0.25) and renders a 1x4 panel with PACT-branded display labels.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "tables" / "E5_cross_model_cumulative_regret_summary.csv"
OUT_DIR = ROOT / "arr_paper" / "figs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODELS = ["DeepSeek-V3.2", "gpt-5.4-nano", "Kimi-K2.6", "Llama-4-Maverick"]
MODEL_DISPLAY = {
    "DeepSeek-V3.2": "DeepSeek-V3.2",
    "gpt-5.4-nano": "GPT-5.4-nano",
    "Kimi-K2.6": "Kimi-K2.6",
    "Llama-4-Maverick": "Llama-4-Maverick",
}

# (family, algorithm) -> display label, color, linestyle, linewidth, zorder
CURVES = [
    (("Native", "hpsmg_plus"),  r"PACT$^+$ (ours)",        "#1b3a6f", "-",  2.4, 6),
    (("Native", "hpsmg"),       r"PACT (ours)",            "#3d6cb3", "-",  2.0, 5),
    (("Native", "joint_psrl"),  "Joint-PSRL",              "#7aa7d9", "--", 1.6, 4),
    (("Native", "psrl_notype"), "PSRL-NoType",             "#c44e52", "-",  1.8, 3),
    (("Prompted LLM", "llm_belief"), "LLM-Belief",         "#8b6dc1", "-.", 1.6, 2),
    (("External LLM", "econ_bne"),   "ECON-BNE",           "#d68a3d", ":",  1.6, 2),
]

plt.rcParams.update({
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "legend.fontsize": 7.5,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "savefig.bbox": "tight",
    "savefig.dpi": 200,
})


def load_curves():
    """Return dict[(model, family, algo)] -> (ks, means, sems)."""
    rows = defaultdict(list)
    with CSV_PATH.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            key = (row["model"], row["family"], row["algorithm"])
            rows[key].append(
                (int(row["episode_k"]),
                 float(row["cumulative_regret_mean"]),
                 float(row["cumulative_regret_sem"]))
            )
    out = {}
    for key, pts in rows.items():
        pts.sort()
        ks = np.array([p[0] for p in pts])
        means = np.array([p[1] for p in pts])
        sems = np.array([p[2] for p in pts])
        out[key] = (ks, means, sems)
    return out


def main() -> None:
    data = load_curves()
    fig, axes = plt.subplots(1, 4, figsize=(13.5, 3.4), sharey=False)

    legend_handles = []
    legend_labels = []
    seen_labels = set()

    for ax, model in zip(axes, MODELS):
        ax.set_title(MODEL_DISPLAY[model])
        for (family, algo), label, color, ls, lw, z in CURVES:
            key = (model, family, algo)
            if key not in data:
                continue
            ks, means, sems = data[key]
            line, = ax.plot(ks, means, color=color, linestyle=ls, linewidth=lw,
                            zorder=z, label=label)
            ax.fill_between(ks, means - sems, means + sems,
                            color=color, alpha=0.15, linewidth=0, zorder=z - 0.5)
            if label not in seen_labels:
                legend_handles.append(line)
                legend_labels.append(label)
                seen_labels.add(label)
        ax.set_xlabel(r"Episode $k$")
        ax.set_xlim(1, 20)
        ax.grid(alpha=0.25, linewidth=0.5)
        ax.set_ylim(bottom=-0.5)

    axes[0].set_ylabel("Cumulative regret")

    fig.legend(legend_handles, legend_labels, loc="lower center",
               ncol=len(legend_handles), bbox_to_anchor=(0.5, -0.04),
               frameon=False, columnspacing=1.4, handlelength=2.2)

    plt.tight_layout(rect=[0, 0.04, 1, 1])
    out_pdf = OUT_DIR / "fig_e5_cumulative_regret_trajectories_v3.pdf"
    out_png = OUT_DIR / "fig_e5_cumulative_regret_trajectories_v3.png"
    fig.savefig(out_pdf)
    fig.savefig(out_png, dpi=180)
    plt.close(fig)
    print(f"OK: {out_pdf.name}")


if __name__ == "__main__":
    main()
