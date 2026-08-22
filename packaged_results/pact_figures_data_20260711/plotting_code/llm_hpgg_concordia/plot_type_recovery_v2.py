"""Plot the type-recovery v2 multi-model figure.

Produces two figures from ``analysis/pub_coord_type_recovery_v2_paper/``:

1. ``figs/pub_coord_type_recovery_v2_paper_curves.pdf`` (and .png)
   Convergence curves: NLL vs round, one subplot per model.
2. ``figs/pub_coord_type_recovery_v2_paper_finalbar.pdf`` (and .png)
   Final-round NLL bar chart, methods grouped, models as colors.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


METHOD_ORDER = [
    "random", "hpsmg", "hpsmg_plus", "joint_psrl",
    "atom_tom1", "atom_tom2", "econ_bne", "llm_belief", "oracle",
]
METHOD_LABEL = {
    "random": "Random",
    "map_greedy": "MAP-Greedy",
    "hpsmg": "H-PSMG",
    "hpsmg_plus": "H-PSMG+",
    "joint_psrl": "Joint-PSRL",
    "atom_tom1": "A-ToM-1",
    "atom_tom2": "A-ToM-2",
    "econ_bne": "Econ-BNE",
    "llm_belief": "LLM-Belief",
    "oracle": "Oracle",
}
# Visual grouping
METHOD_COLOR = {
    "random": "#999999",
    "map_greedy": "#444444",
    "hpsmg": "#1f77b4",
    "hpsmg_plus": "#1f77b4",
    "joint_psrl": "#2ca02c",
    "atom_tom1": "#ff7f0e",
    "atom_tom2": "#d62728",
    "econ_bne": "#9467bd",
    "llm_belief": "#17becf",
    "oracle": "#000000",
}
METHOD_LINESTYLE = {
    "random": ":",
    "map_greedy": "--",
    "hpsmg": "-",
    "hpsmg_plus": (0, (3, 1, 1, 1)),
    "joint_psrl": "-",
    "atom_tom1": "-",
    "atom_tom2": "-",
    "econ_bne": "-",
    "llm_belief": "-",
    "oracle": ":",
}
MODEL_COLOR = {
    "gpt-5.4-nano": "#1f77b4",
    "DeepSeek-V3.2": "#ff7f0e",
    "Kimi-K2.6": "#2ca02c",
    "Llama-4-Maverick": "#d62728",
}


def plot_curves(agg: dict, out_path: Path) -> None:
    models = agg["models"]
    rounds = agg["rounds"]
    rounds_axis = list(range(1, rounds + 1))
    methods = [m for m in METHOD_ORDER if m in agg["methods"]]

    n = len(models)
    cols = 2 if n > 1 else 1
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(6.5 * cols, 4.0 * rows),
                             sharex=True, sharey=True)
    axes = np.atleast_1d(axes).flatten()

    for ax, model in zip(axes, models):
        conv = agg["by_model"][model]["summary"]["convergence"]
        for method in methods:
            series = conv.get(method, [])
            if not series:
                continue
            ys = [pt["nll"] for pt in series]
            xs = [pt["round"] for pt in series]
            ax.plot(
                xs, ys,
                label=METHOD_LABEL[method],
                color=METHOD_COLOR[method],
                linestyle=METHOD_LINESTYLE[method],
                linewidth=1.8 if method in {"hpsmg_plus", "joint_psrl"} else 1.3,
                marker="o" if method in {"hpsmg_plus", "joint_psrl", "llm_belief"} else None,
                markersize=3,
            )
        ax.set_title(model)
        ax.set_xlabel("round")
        ax.set_ylabel("NLL (lower = better)")
        ax.set_xticks(rounds_axis)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=-0.05)

    for ax in axes[len(models):]:
        ax.set_visible(False)

    # Single legend
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=min(len(labels), 5),
               bbox_to_anchor=(0.5, -0.02), frameon=False)
    fig.suptitle(
        f"Pub Coordination type recovery (config={agg['config']}, "
        f"seeds={len(agg['seeds'])}, eps={agg['epsilon']})",
        y=1.0,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.98))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    fig.savefig(out_path.with_suffix(".png"), bbox_inches="tight", dpi=180)
    plt.close(fig)
    print(f"wrote {out_path}\nwrote {out_path.with_suffix('.png')}")


def plot_final_bar(agg: dict, out_path: Path) -> None:
    models = agg["models"]
    methods = [m for m in METHOD_ORDER if m in agg["methods"]]
    x = np.arange(len(methods))
    width = 0.8 / len(models)

    fig, (ax_top1, ax_nll) = plt.subplots(2, 1, figsize=(11, 7), sharex=True)

    for j, model in enumerate(models):
        finals = {row["method"]: row for row in
                  agg["by_model"][model]["summary"]["final"]}
        top1 = [finals.get(m, {}).get("top1_accuracy_mean", np.nan) for m in methods]
        nll = [finals.get(m, {}).get("nll_mean", np.nan) for m in methods]
        offset = (j - (len(models) - 1) / 2) * width
        ax_top1.bar(x + offset, top1, width=width, label=model,
                    color=MODEL_COLOR.get(model))
        ax_nll.bar(x + offset, nll, width=width, label=model,
                   color=MODEL_COLOR.get(model))

    ax_top1.set_ylabel("Final-round top-1 accuracy (higher = better)")
    ax_top1.set_ylim(0, 1.05)
    ax_top1.grid(True, axis="y", alpha=0.3)
    ax_top1.legend(loc="lower right", ncol=len(models), frameon=False)

    ax_nll.set_ylabel("Final-round NLL (lower = better)")
    ax_nll.grid(True, axis="y", alpha=0.3)
    ax_nll.set_xticks(x)
    ax_nll.set_xticklabels([METHOD_LABEL[m] for m in methods], rotation=30,
                           ha="right")

    fig.suptitle(
        f"Pub Coordination type recovery (final round, config={agg['config']}, "
        f"seeds={len(agg['seeds'])}, rounds={agg['rounds']}, eps={agg['epsilon']})"
    )
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    fig.savefig(out_path.with_suffix(".png"), bbox_inches="tight", dpi=180)
    plt.close(fig)
    print(f"wrote {out_path}\nwrote {out_path.with_suffix('.png')}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--aggregate",
        default="analysis/pub_coord_type_recovery_v2_paper/aggregate.json",
    )
    parser.add_argument(
        "--curves-out",
        default="figs/pub_coord_type_recovery_v2_paper_curves.pdf",
    )
    parser.add_argument(
        "--bar-out",
        default="figs/pub_coord_type_recovery_v2_paper_finalbar.pdf",
    )
    args = parser.parse_args()

    with Path(args.aggregate).open(encoding="utf-8") as fh:
        agg = json.load(fh)

    plot_curves(agg, Path(args.curves_out))
    plot_final_bar(agg, Path(args.bar_out))


if __name__ == "__main__":
    main()
