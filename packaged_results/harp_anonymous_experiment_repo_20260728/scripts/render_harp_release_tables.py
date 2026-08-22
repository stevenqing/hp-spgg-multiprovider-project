"""Redraw HARP release figures whose raw NPZs were retired but tables remain."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "analysis" / "wave1_experiment_additions_summary.md"
OUT = ROOT / "arr_paper" / "figs"

COLORS = {
    "HARP+": "#1b3a6f",
    "HARP": "#3d6cb3",
    "Joint-PSRL": "#c44e52",
    "MAP-greedy": "#8172b2",
    "PSRL (no type)": "#937860",
    "IQL (joint)": "#da8b41",
    "IQL (indep)": "#dd8452",
    "Random": "#999999",
    "Oracle": "#3c8c5a",
}
MARKERS = {
    "HARP+": "D", "HARP": "o", "Joint-PSRL": "s", "MAP-greedy": "^",
    "PSRL (no type)": "v", "IQL (joint)": "x", "IQL (indep)": "+",
    "Random": "P", "Oracle": "*",
}


def table_after(text: str, heading: str) -> tuple[list[str], list[list[str]]]:
    lines = text.splitlines()
    index = next(index for index, line in enumerate(lines) if heading in line) + 1
    while index < len(lines) and not lines[index].startswith("|"):
        index += 1
    header = [cell.strip() for cell in lines[index].strip("|").split("|")]
    rows = []
    for line in lines[index + 2 :]:
        if not line.startswith("|"):
            break
        rows.append([cell.strip() for cell in line.strip("|").split("|")])
    return header, rows


def style() -> None:
    plt.rcParams.update({
        "font.family": "serif", "font.size": 8.2, "pdf.fonttype": 42,
        "ps.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False,
    })


def display_method(value: str) -> str:
    return {"PACT+": "HARP+", "PACT": "HARP"}.get(value, value)


def plot_scaling(text: str) -> None:
    header, rows = table_after(text, "## E-1.1 n-scaling (Wave-2, 9-baseline analytic tier)")
    records = [dict(zip(header, row, strict=True)) for row in rows]
    for record in records:
        record["algorithm"] = display_method(record["algorithm"])
    methods = ["HARP+", "HARP", "Joint-PSRL", "MAP-greedy", "PSRL (no type)", "IQL (joint)", "IQL (indep)", "Random", "Oracle"]
    ns = [3, 4, 5, 6]
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    for method in methods:
        selected = [row for row in records if row["algorithm"] == method]
        selected.sort(key=lambda row: int(row["n"]))
        ax.errorbar(
            [int(row["n"]) for row in selected],
            [float(row["final cum-regret mean"]) for row in selected],
            yerr=[float(row["sem"]) for row in selected],
            color=COLORS[method], marker=MARKERS[method], linewidth=2.0 if method.startswith("HARP") else 1.25,
            linestyle="-" if method in {"HARP+", "HARP", "Joint-PSRL", "Oracle"} else "--",
            capsize=2.2, markersize=5.2, label=method,
        )
    ax.set_yscale("symlog", linthresh=1.0)
    ax.set_xticks(ns)
    ax.set_xlabel("Number of agents $n$")
    ax.set_ylabel("Final cumulative regret ($K=20$, symlog)")
    ax.set_title("Analytic HP-SPGG population scaling", loc="left")
    ax.grid(alpha=0.25, linestyle=":")
    ax.legend(fontsize=6.7, ncol=2, loc="center right")
    fig.tight_layout()
    fig.savefig(OUT / "fig_e1_1_n_scaling.pdf", bbox_inches="tight")
    fig.savefig(OUT / "fig_e1_1_n_scaling.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_llm_scaling(text: str) -> None:
    header, rows = table_after(text, "## E-1.1 LLM-tier n-scaling (DeepSeek + Llama-Maverick, live judge, 9-baseline)")
    records = [dict(zip(header, row, strict=True)) for row in rows]
    for record in records:
        record["algorithm"] = display_method(record["algorithm"])
    methods = ["HARP+", "HARP", "Joint-PSRL", "MAP-greedy", "PSRL (no type)", "IQL (joint)", "IQL (indep)", "Random", "Oracle"]
    backbones = [("deepseek", "DeepSeek-V3.2"), ("llama_maverick", "Llama-4-Maverick")]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), sharey=True)
    for ax, (key, label) in zip(axes, backbones, strict=True):
        for method in methods:
            selected = [row for row in records if row["backbone"] == key and row["algorithm"] == method]
            selected.sort(key=lambda row: int(row["n"]))
            ax.errorbar(
                [int(row["n"]) for row in selected], [float(row["mean"]) for row in selected],
                yerr=[float(row["sem"]) for row in selected], color=COLORS[method], marker=MARKERS[method],
                linewidth=2.0 if method.startswith("HARP") else 1.2,
                linestyle="-" if method in {"HARP+", "HARP", "Joint-PSRL", "Oracle"} else "--",
                capsize=2.0, markersize=4.8, label=method,
            )
        ax.set_yscale("symlog", linthresh=1.0)
        ax.set_xticks([3, 4, 5, 6])
        ax.set_xlabel("Number of agents $n$")
        ax.set_title(label, loc="left")
        ax.grid(alpha=0.25, linestyle=":")
    axes[0].set_ylabel("Final cumulative regret ($K=20$, symlog)")
    axes[0].legend(fontsize=6.2, ncol=2, loc="upper left")
    fig.tight_layout()
    fig.savefig(OUT / "fig_e1_1_n_scaling_llm.pdf", bbox_inches="tight")
    fig.savefig(OUT / "fig_e1_1_n_scaling_llm.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_pf_isolation(text: str) -> None:
    header, rows = table_after(text, "E-1.3a (symmetric Dirichlet")
    normalized_header = [display_method(value) for value in header]
    records = [dict(zip(normalized_header, row, strict=True)) for row in rows]
    shared_header, shared_rows = table_after(text, "E-1.3b (shared-type structured prior")
    shared = dict(zip([display_method(value) for value in shared_header], shared_rows[0], strict=True))
    methods = [name for name in normalized_header[1:] if name in COLORS and name != "Oracle"]
    x = np.arange(len(records))
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.8), gridspec_kw={"width_ratios": [1.7, 1.0]})
    for method in methods:
        axes[0].plot(x, [float(row[method]) for row in records], marker=MARKERS[method], color=COLORS[method],
                     linewidth=2.0 if method.startswith("HARP") else 1.25, label=method)
    axes[0].set_yscale("symlog", linthresh=1.0)
    axes[0].set_xticks(x, [row[normalized_header[0]].replace("dirichlet alpha=", "") for row in records])
    axes[0].set_xlabel("Dirichlet concentration $\\alpha$ ($\\infty$ = uniform)")
    axes[0].set_ylabel("Final cumulative regret ($K=20$, symlog)")
    axes[0].set_title("(a) Symmetric joint prior", loc="left")
    axes[0].grid(alpha=0.25, linestyle=":")
    axes[0].legend(fontsize=6.3, ncol=2)
    values = [float(shared[method]) for method in methods]
    y = np.arange(len(methods))
    axes[1].barh(y, values, color=[COLORS[m] for m in methods], edgecolor="black", linewidth=0.4)
    axes[1].set_yticks(y, methods)
    axes[1].invert_yaxis()
    axes[1].set_xscale("symlog", linthresh=1.0)
    axes[1].set_xlabel("Final cumulative regret")
    axes[1].set_title("(b) Shared-type prior", loc="left")
    axes[1].grid(axis="x", alpha=0.25, linestyle=":")
    fig.tight_layout()
    fig.savefig(OUT / "fig_e1_3_pf_isolation.pdf", bbox_inches="tight")
    fig.savefig(OUT / "fig_e1_3_pf_isolation.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    style()
    text = SOURCE.read_text(encoding="utf-8")
    plot_scaling(text)
    plot_llm_scaling(text)
    plot_pf_isolation(text)
    print("redrew three HARP release-table figures")


if __name__ == "__main__":
    main()
