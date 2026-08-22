"""Build the epsilon-sensitivity panel for the Fig5 supplement.

For each epsilon, load the aggregate.json and compute per (model, method) the
max_nll and final_nll. Plot:
  - 2 rows (max_nll, final_nll)
  - 4 columns (one per model)
  - x-axis = epsilon, y-axis = NLL
  - lines = methods (map_greedy, hpsmg_plus, joint_psrl, llm_belief, oracle)

Saves PDF + PNG to figs/.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt


METHOD_ORDER = ["random", "map_greedy", "atom_tom1", "atom_tom2", "econ_bne", "llm_belief", "hpsmg_plus"]
METHOD_LABEL = {
    "oracle": "Oracle",
    "hpsmg": "H-PSMG",
    "hpsmg_plus": "H-PSMG / H-PSMG$^+$ (ours)",
    "joint_psrl": "Joint-PSRL",
    "llm_belief": "LLM-Belief",
    "map_greedy": "MAP-Type-Greedy",
    "random": "Random",
    "atom_tom1": "A-ToM-1",
    "atom_tom2": "A-ToM-2",
    "econ_bne": "ECON-BNE",
}
METHOD_COLOR = {
    "oracle": "#7f7f7f",
    "hpsmg": "#1f77b4",
    "hpsmg_plus": "#d62728",
    "joint_psrl": "#1f77b4",
    "map_greedy": "#9467bd",
    "llm_belief": "#ff7f0e",
    "atom_tom1": "#ffbb78",
    "atom_tom2": "#e377c2",
    "econ_bne": "#bcbd22",
    "random": "#999999",
}
METHOD_MARKER = {
    "oracle": "s",
    "hpsmg": "o",
    "hpsmg_plus": "*",
    "joint_psrl": "^",
    "map_greedy": "v",
    "llm_belief": "D",
    "atom_tom1": "P",
    "atom_tom2": "X",
    "econ_bne": "<",
    "random": ".",
}
METHOD_LW = {"hpsmg_plus": 3.2}
METHOD_MS = {"hpsmg_plus": 12}


def load_eps(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def metrics(conv):
    nlls = [pt["nll"] for pt in conv]
    return {"final_nll": nlls[-1], "max_nll": max(nlls), "mean_nll": sum(nlls) / len(nlls)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inputs", nargs="+", required=True,
                    help="space-separated eps:aggregate.json pairs, e.g. 0.1:path 0.2:path")
    ap.add_argument("--out", default="figs/pub_coord_type_recovery_v2_eps_sensitivity")
    args = ap.parse_args()

    runs = {}
    models = None
    methods = None
    for spec in args.inputs:
        eps_str, path = spec.split(":", 1)
        eps = float(eps_str)
        agg = load_eps(Path(path))
        if models is None:
            models = agg["models"]
        if methods is None:
            methods = [m for m in METHOD_ORDER if m in agg["methods"]]
        per_mm = {}
        for model in models:
            conv_all = agg["by_model"][model]["summary"]["convergence"]
            for method in methods:
                if method in conv_all and conv_all[method]:
                    per_mm[(model, method)] = metrics(conv_all[method])
        runs[eps] = per_mm

    eps_sorted = sorted(runs.keys())
    nrows, ncols = 2, len(models)
    fig, axes = plt.subplots(nrows, ncols, figsize=(3.6 * ncols, 3.1 * nrows),
                             sharex=True)

    for col, model in enumerate(models):
        for row, metric in enumerate(["max_nll", "final_nll"]):
            ax = axes[row, col]
            for method in methods:
                ys = [runs[e].get((model, method), {}).get(metric, float("nan"))
                      for e in eps_sorted]
                ax.plot(eps_sorted, ys, marker=METHOD_MARKER[method],
                        color=METHOD_COLOR[method],
                        lw=METHOD_LW.get(method, 1.8),
                        ms=METHOD_MS.get(method, 7),
                        label=METHOD_LABEL[method])
            if row == 0:
                ax.set_title(model, fontsize=14, fontweight="bold")
            if col == 0:
                ylab = "Max NLL over rounds" if metric == "max_nll" else "Final-round NLL"
                ax.set_ylabel(ylab, fontsize=13)
            if row == nrows - 1:
                ax.set_xlabel(r"masking $\epsilon$", fontsize=13)
            ax.grid(alpha=0.3)
            ax.tick_params(labelsize=11)

    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center",
               ncol=len(methods), fontsize=13, frameon=False,
               bbox_to_anchor=(0.5, -0.02))

    fig.suptitle(
        "Robustness to observation masking on london_mini "
        "(5 seeds, 4 rounds, K=2; oracle$\\equiv$0 omitted)",
        fontsize=14, y=1.0,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.97))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    pdf = out.with_suffix(".pdf")
    png = out.with_suffix(".png")
    fig.savefig(pdf, bbox_inches="tight")
    fig.savefig(png, dpi=150, bbox_inches="tight")
    print(f"wrote {pdf}")
    print(f"wrote {png}")


if __name__ == "__main__":
    main()
