"""Plot the CourierDispatch matching LLM-backend headline figure.

This figure follows the earlier HP-SPGG cross-model main-figure style: one
horizontal bar panel per model, algorithms ordered by family, with shaded
family bands. The data are the CloudGPT structured-solver live run where every
method calls the LLM for driver-order score advice.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis" / "courier_dispatch_matching"
SUMMARY_DEFAULT = ANALYSIS / "courier_matching_structured_live_expected_pact_masked_type_stress_s5h8_allmodels_summary.json"
OUT_DIRS = [ROOT / "figs", ROOT / "arr_paper" / "figs"]

MODEL_ORDER = [
    "DeepSeek-V3.2",
    "gpt-5.4-mini-20260317",
    "Kimi-K2.6",
    "Llama-4-Maverick-17B-128E-Instruct-FP8",
]
MODEL_LABELS = {
    "DeepSeek-V3.2": "DeepSeek-V3.2",
    "gpt-5.4-mini-20260317": "GPT-5.4-mini",
    "Kimi-K2.6": "Kimi-K2.6",
    "Llama-4-Maverick-17B-128E-Instruct-FP8": "Llama-Maverick",
}

METHOD_ORDER = [
    "oracle",
    "live_pact_plus",
    "live_pact",
    "live_joint_psrl",
    "live_map_greedy",
    "live_llm_greedy",
    "live_llm_belief",
    "live_econ_bne",
    "live_llm_psrl_verbal",
    "live_atom_tom0",
    "live_atom_tom1",
    "live_atom_adaptive_hedge",
    "live_psrl_notype",
    "live_random",
]
METHOD_LABELS = {
    "oracle": "Oracle",
    "live_pact_plus": r"PACT$^+$",
    "live_pact": "PACT",
    "live_joint_psrl": "Joint-PSRL",
    "live_map_greedy": "MAP-Type",
    "live_llm_greedy": "LLM-Greedy",
    "live_llm_belief": "LLM-Belief",
    "live_econ_bne": "ECON-BNE",
    "live_llm_psrl_verbal": "LLM-PSRL-verbal",
    "live_atom_tom0": "A-ToM-0",
    "live_atom_tom1": "A-ToM-1",
    "live_atom_adaptive_hedge": "A-ToM hedge",
    "live_psrl_notype": "PSRL-NoType",
    "live_random": "Random",
}
FAMILY = {
    "oracle": "oracle",
    "live_pact_plus": "posterior",
    "live_pact": "posterior",
    "live_joint_psrl": "posterior",
    "live_map_greedy": "posterior",
    "live_llm_greedy": "prompt",
    "live_llm_belief": "prompt",
    "live_econ_bne": "prompt",
    "live_llm_psrl_verbal": "verbal",
    "live_atom_tom0": "prompt",
    "live_atom_tom1": "prompt",
    "live_atom_adaptive_hedge": "prompt",
    "live_psrl_notype": "no_type",
    "live_random": "no_type",
}
FAMILY_BAND = {
    "oracle": "#ffffff",
    "posterior": "#f0f4fa",
    "prompt": "#fbf3ec",
    "verbal": "#eef7f2",
    "no_type": "#f5f5f5",
}
COLORS = {
    "oracle": "#9aa0a6",
    "live_pact_plus": "#1b3a6f",
    "live_pact": "#3d6cb3",
    "live_joint_psrl": "#8faad0",
    "live_map_greedy": "#b9c8df",
    "live_llm_greedy": "#e8b06f",
    "live_llm_belief": "#e08e45",
    "live_econ_bne": "#c0463f",
    "live_llm_psrl_verbal": "#3d7b62",
    "live_atom_tom0": "#d4a04a",
    "live_atom_tom1": "#cc8242",
    "live_atom_adaptive_hedge": "#b8723d",
    "live_psrl_notype": "#3d3d3d",
    "live_random": "#8c8c8c",
}
INK = "#202020"
MUTED = "#555555"
PALE = "#cccccc"


def configure_matplotlib() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Inter", "Helvetica Neue", "Arial", "DejaVu Sans"],
            "font.size": 8.5,
            "axes.titlesize": 11,
            "axes.titleweight": "semibold",
            "axes.titlelocation": "left",
            "axes.titlepad": 8,
            "axes.labelsize": 8.8,
            "axes.linewidth": 0.45,
            "axes.edgecolor": PALE,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "xtick.color": "#444444",
            "ytick.color": "#444444",
            "xtick.major.size": 0,
            "ytick.major.size": 0,
            "savefig.dpi": 240,
        }
    )


def mean(values: list[float]) -> float:
    return float(sum(values) / len(values)) if values else float("nan")


def sem(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = mean(values)
    return float(math.sqrt(sum((value - avg) ** 2 for value in values) / (len(values) - 1)) / math.sqrt(len(values)))


def style_axis(ax: plt.Axes) -> None:
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(PALE)
        ax.spines[spine].set_linewidth(0.45)
    ax.grid(axis="x", linestyle=":", linewidth=0.55, color="#dddddd")
    ax.set_axisbelow(True)
    ax.tick_params(colors=MUTED, which="both")


def load_payload(summary_path: Path) -> dict:
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert payload["setting"]["backend"] == "cloudgpt"
    assert payload["setting"]["decision_mode"] == "structured_solver_with_llm_score_calls"
    return payload


def final_regret_stats(payload: dict) -> dict[tuple[str, str], dict[str, float]]:
    by_key_seed: dict[tuple[str, str], dict[int, float]] = defaultdict(dict)
    final_round = int(payload["setting"]["horizon"]) - 1
    for row in payload["rows"]:
        if int(row["round"]) != final_round:
            continue
        key = (str(row["model"]), str(row["method"]))
        by_key_seed[key][int(row["seed"])] = float(row["cumulative_regret"])

    stats: dict[tuple[str, str], dict[str, float]] = {}
    for key, by_seed in by_key_seed.items():
        values = list(by_seed.values())
        stats[key] = {"regret": mean(values), "sem": sem(values)}
    for model in MODEL_ORDER:
        stats[(model, "oracle")] = {"regret": 0.0, "sem": 0.0}
    return stats


def family_ranges(methods: list[str]) -> list[tuple[int, int, str]]:
    ranges: list[tuple[int, int, str]] = []
    start = 0
    for idx in range(1, len(methods) + 1):
        if idx == len(methods) or FAMILY[methods[idx]] != FAMILY[methods[start]]:
            ranges.append((start, idx - 1, FAMILY[methods[start]]))
            start = idx
    return ranges


def draw_model_panel(ax: plt.Axes, model: str, stats: dict[tuple[str, str], dict[str, float]]) -> None:
    available_methods = [method for method in METHOD_ORDER if (model, method) in stats]
    methods = sorted(available_methods, key=lambda method: stats[(model, method)]["regret"])
    y = np.arange(len(methods))
    for lo, hi, family in family_ranges(methods):
        ax.axhspan(lo - 0.45, hi + 0.45, color=FAMILY_BAND[family], alpha=0.72, zorder=0)
    values = [stats[(model, method)]["regret"] for method in methods]
    errors = [stats[(model, method)]["sem"] for method in methods]
    colors = [COLORS[method] for method in methods]
    ax.barh(
        y,
        values,
        xerr=errors,
        height=0.58,
        color=colors,
        edgecolor="white",
        linewidth=0.8,
        capsize=2.3,
        error_kw={"elinewidth": 0.75, "ecolor": "#777777"},
        zorder=3,
    )
    ax.set_yticks(y)
    ax.set_yticklabels([METHOD_LABELS[method] for method in methods])
    ax.invert_yaxis()
    ax.set_title(MODEL_LABELS[model])
    xmax = max(value + err for value, err in zip(values, errors, strict=True))
    ax.set_xlim(0.0, max(5.5, xmax * 1.16))
    style_axis(ax)
    for yi, value, err in zip(y, values, errors, strict=True):
        ax.text(value + err + 0.06, yi, f"{value:.2f}", va="center", ha="left", fontsize=7.1, color=INK)


def save(fig: plt.Figure, name: str) -> None:
    for out_dir in OUT_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        png_path = out_dir / f"{name}.png"
        fig.savefig(png_path, dpi=260, bbox_inches="tight", facecolor="white", edgecolor="none")
        Image.open(png_path).convert("RGB").save(png_path)
        fig.savefig(out_dir / f"{name}.pdf", bbox_inches="tight", facecolor="white", edgecolor="none")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, default=SUMMARY_DEFAULT)
    parser.add_argument("--out-name", default="fig_courier_matching_llm_backend_main")
    args = parser.parse_args()
    configure_matplotlib()
    summary_path = args.summary if args.summary.is_absolute() else ROOT / args.summary
    payload = load_payload(summary_path)
    stats = final_regret_stats(payload)
    fig, axes = plt.subplots(2, 2, figsize=(11.2, 7.55), sharey=False)
    fig.patch.set_facecolor("white")
    for ax, model in zip(axes.flat, MODEL_ORDER, strict=True):
        draw_model_panel(ax, model, stats)
    for ax in axes[1, :]:
        ax.set_xlabel("Cumulative regret at H=8")
    fig.suptitle(
        "CourierDispatch-Rules matching: CloudGPT backend with structured solver",
        x=0.08,
        y=0.995,
        ha="left",
        fontsize=13,
        fontweight="semibold",
        color=INK,
    )
    fig.text(
        0.08,
        0.962,
        "Structured methods use CloudGPT-backed scoring before deterministic assignment; Random is a no-type floor. Lower regret is better. Bars show mean +/- SEM over 5 seeds.",
        ha="left",
        va="top",
        fontsize=8.5,
        color=MUTED,
    )
    fig.tight_layout(rect=[0.0, 0.0, 1.0, 0.93], w_pad=2.0, h_pad=1.8)
    save(fig, args.out_name)
    plt.close(fig)
    print(f"OK: figs/{args.out_name}.png")
    print(f"OK: figs/{args.out_name}.pdf")


if __name__ == "__main__":
    main()