"""Regenerate figures that include the llm_psrl_verbal baseline."""

from __future__ import annotations

import csv
import json
import math
import shutil
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
FIGS = ROOT / "arr_paper" / "figs"
FIGS.mkdir(parents=True, exist_ok=True)
ROOT_FIGS = ROOT / "figs"
ROOT_FIGS.mkdir(parents=True, exist_ok=True)
OVERLEAF_FIGS = ROOT / "arr_paper_overleaf" / "figs"

MODEL_ORDER = ["deepseek", "gpt5_nano", "kimi_k2", "llama_maverick"]
MODEL_LABEL = {
    "deepseek": "DeepSeek-V3.2",
    "gpt5_nano": "GPT-5.4-nano",
    "kimi_k2": "Kimi-K2.6",
    "llama_maverick": "Llama-Maverick",
}


def sync(path: Path) -> None:
    if path.parent != ROOT_FIGS:
        shutil.copy2(path, ROOT_FIGS / path.name)
    if OVERLEAF_FIGS.exists():
        shutil.copy2(path, OVERLEAF_FIGS / path.name)


def mean_sem(values: list[float]) -> tuple[float, float]:
    arr = np.asarray(values, dtype=float)
    if len(arr) <= 1:
        return float(arr.mean()) if len(arr) else float("nan"), 0.0
    return float(arr.mean()), float(arr.std(ddof=1) / np.sqrt(len(arr)))


def plot_hp_spgg() -> None:
    old_data = {
        "deepseek": [
            ("oracle", 0.000, 0.000), ("hpsmg_plus", 0.400, 0.800), ("hpsmg", 0.828, 0.541),
            ("map_greedy", 0.712, 0.466), ("joint_psrl", 0.832, 0.080), ("llm_belief", 3.074, 2.231),
            ("econ_bne", 3.990, 3.414), ("atom_tom0", 6.000, 7.457), ("atom_adaptive_hedge", 4.790, 4.509),
            ("psrl_notype", 13.912, 7.374), ("random", 28.266, 5.124), ("iql", 28.342, 16.914),
        ],
        "gpt5_nano": [
            ("oracle", 0.000, 0.000), ("hpsmg_plus", 0.912, 0.292), ("hpsmg", 0.644, 0.631),
            ("map_greedy", 0.854, 0.421), ("joint_psrl", 1.492, 0.342), ("llm_belief", 7.197, 3.475),
            ("econ_bne", 14.880, 2.753), ("atom_tom0", 4.080, 4.941), ("atom_adaptive_hedge", 7.653, 4.958),
            ("psrl_notype", 17.720, 1.677), ("random", 26.458, 1.814), ("iql", 24.792, 11.728),
        ],
        "kimi_k2": [
            ("oracle", 0.000, 0.000), ("hpsmg_plus", 0.704, 0.435), ("hpsmg", 0.632, 0.609),
            ("map_greedy", 0.762, 0.391), ("joint_psrl", 1.650, 0.404), ("llm_belief", 11.784, 3.334),
            ("econ_bne", 10.488, 6.032), ("atom_tom0", 10.672, 6.356), ("atom_adaptive_hedge", 7.484, 4.096),
            ("psrl_notype", 19.506, 2.610), ("random", 26.540, 4.514), ("iql", 20.118, 18.527),
        ],
        "llama_maverick": [
            ("oracle", 0.000, 0.000), ("hpsmg_plus", 0.312, 0.624), ("hpsmg", 0.732, 0.609),
            ("map_greedy", 0.974, 0.439), ("joint_psrl", 1.194, 0.347), ("llm_belief", 10.356, 3.819),
            ("econ_bne", 3.382, 4.534), ("atom_tom0", 7.240, 7.789), ("atom_adaptive_hedge", 7.006, 4.583),
            ("psrl_notype", 10.654, 4.357), ("random", 24.342, 4.323), ("iql", 27.526, 16.339),
        ],
    }
    rows = list(csv.DictReader(open(ROOT / "analysis" / "llm_psrl_verbal" / "summary.csv", encoding="utf-8")))
    verbal = {(r["tier"], int(r["n"])): r for r in rows if r["algorithm"] == "llm_psrl_verbal"}
    data = {}
    for tier, entries in old_data.items():
        v = verbal[(tier, 3)]
        data[tier] = entries[:5] + [("llm_psrl_verbal", float(v["mean_cumulative_regret"]), float(v["sem"]))] + entries[5:]

    palette = {
        "oracle": "#9aa0a6", "hpsmg_plus": "#1b3a6f", "hpsmg": "#3d6cb3", "map_greedy": "#7b9fcf", "joint_psrl": "#b3c5e0",
        "llm_psrl_verbal": "#2e7d32", "llm_belief": "#e08e45", "econ_bne": "#c0463f", "atom_tom0": "#d4a04a",
        "atom_adaptive_hedge": "#b8723d", "psrl_notype": "#3d3d3d", "random": "#6e6e6e", "iql": "#a8a8a8",
    }
    label = {
        "oracle": "Oracle", "hpsmg_plus": r"PACT$^+$", "hpsmg": "PACT", "map_greedy": "MAP-Type", "joint_psrl": "Joint-PSRL",
        "llm_psrl_verbal": "LLM-PSRL-verbal", "llm_belief": "LLM-Belief", "econ_bne": "ECON-BNE", "atom_tom0": "A-ToM-0",
        "atom_adaptive_hedge": "A-ToM hedge", "psrl_notype": "PSRL-NoType", "random": "Random", "iql": "IQL",
    }
    family = {
        "oracle": "#ffffff", "hpsmg_plus": "#f0f4fa", "hpsmg": "#f0f4fa", "map_greedy": "#f0f4fa", "joint_psrl": "#f0f4fa",
        "llm_psrl_verbal": "#edf7ed", "llm_belief": "#fbf3ec", "econ_bne": "#fbf3ec", "atom_tom0": "#fbf3ec", "atom_adaptive_hedge": "#fbf3ec",
        "psrl_notype": "#f5f5f5", "random": "#f5f5f5", "iql": "#f5f5f5",
    }
    fig, axes = plt.subplots(2, 2, figsize=(10.4, 7.4))
    for ax, tier in zip(axes.flatten(), MODEL_ORDER):
        entries = data[tier]
        y = np.arange(len(entries))
        means = np.array([e[1] for e in entries])
        sems = np.array([e[2] for e in entries])
        start = 0
        fams = [family[e[0]] for e in entries]
        for i in range(1, len(fams) + 1):
            if i == len(fams) or fams[i] != fams[i - 1]:
                if fams[start] != "#ffffff":
                    ax.axhspan(start - 0.5, i - 0.5, color=fams[start], zorder=0)
                start = i
        for i, (alg, mean, sem) in enumerate(entries):
            ax.barh(y[i], mean, color=palette[alg], height=0.6, edgecolor="none", zorder=2)
            if sem > 0:
                ax.plot([max(0, mean - sem), mean + sem], [y[i], y[i]], color="#777777", lw=0.7, zorder=3)
            ax.text(mean + 0.55, y[i], f"{mean:.2f}", va="center", ha="left", fontsize=7.2)
        ax.set_yticks(y)
        ax.set_yticklabels([label[e[0]] for e in entries], fontsize=7.8)
        ax.invert_yaxis()
        ax.set_title(MODEL_LABEL[tier], loc="left", fontsize=11, fontweight="semibold")
        ax.grid(axis="x", ls=":", lw=0.5, color="#dddddd")
        ax.set_xlim(0, max(means + sems) * 1.18 + 0.1)
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    fig.text(0.5, 0.01, "Cumulative Bayesian regret at K=20", ha="center", fontsize=9)
    plt.tight_layout(rect=(0, 0.03, 1, 1))
    for suffix in ("pdf", "png"):
        path = FIGS / f"fig10_hp_spgg_cross_model_v3.{suffix}"
        fig.savefig(path, dpi=220 if suffix == "png" else None, bbox_inches="tight")
        sync(path)
    plt.close(fig)


def plot_sotopia_three_exp() -> None:
    bases = ["hpsmg_plus", "llm_psrl_verbal", "atom_tom1", "econ_bne", "llm_belief", "llm_greedy"]
    labels = {"hpsmg_plus": r"PACT$^+$", "llm_psrl_verbal": "LLM-PSRL-verbal", "atom_tom1": "A-ToM-1", "econ_bne": "ECON-BNE", "llm_belief": "llm_belief", "llm_greedy": "llm_greedy"}
    colors = {"hpsmg_plus": "#1f2d5c", "llm_psrl_verbal": "#2e7d32", "atom_tom1": "#d8a04b", "econ_bne": "#a63a3a", "llm_belief": "#7a8aa6", "llm_greedy": "#bdbdbd"}
    scenarios = [("craigslist_bargains", "Craigslist bargains"), ("revenge_plot", "Revenge plot"), ("donate_funds", "Donate funds")]
    buckets: dict[tuple[str, str], list[float]] = defaultdict(list)
    for path in sorted((ROOT / "analysis").glob("sotopia_hard_official_*_sotopia_tuned_all70.json")):
        name = path.name.replace("sotopia_hard_official_", "").replace("_sotopia_tuned_all70.json", "")
        baseline = next((b for b in bases if name.endswith("_" + b)), None)
        if baseline is None:
            continue
        data = json.load(open(path, encoding="utf-8"))
        for episode in data.get("episodes", []):
            fam = family_of(episode.get("codename", ""))
            vals = [v for v in (episode.get("overall") or {}).values() if isinstance(v, (int, float))]
            if vals:
                buckets[(fam, baseline)].append(sum(vals) / len(vals))
    for path in sorted((ROOT / "analysis" / "llm_psrl_verbal").glob("sotopia_hard_*_llm_psrl_verbal_all70.json")):
        data = json.load(open(path, encoding="utf-8"))
        for episode in data.get("episodes", []):
            fam = family_of(episode.get("codename", ""))
            vals = [v for v in (episode.get("overall") or {}).values() if isinstance(v, (int, float))]
            if vals:
                buckets[(fam, "llm_psrl_verbal")].append(sum(vals) / len(vals))
    fig, axes = plt.subplots(1, 3, figsize=(14.8, 3.5))
    for ax, (fam, title) in zip(axes, scenarios):
        means, sems = [], []
        for base in bases:
            mean, sem = mean_sem(buckets.get((fam, base), []))
            means.append(mean); sems.append(sem)
        means_arr = np.asarray(means, dtype=float)
        sems_arr = np.asarray(sems, dtype=float)
        finite = np.isfinite(means_arr)
        x_min = max(0.0, math.floor((float(np.nanmin(means_arr[finite] - sems_arr[finite])) - 0.02) * 100) / 100)
        x_max = math.ceil((float(np.nanmax(means_arr[finite] + sems_arr[finite])) + 0.04) * 100) / 100
        y = np.arange(len(bases))[::-1]
        best_alt = max(v for b, v in zip(bases, means) if b != "hpsmg_plus")
        ax.barh(y, means, xerr=sems, color=[colors[b] for b in bases], edgecolor="black", linewidth=[1.2 if b == "hpsmg_plus" else 0.4 for b in bases])
        for yi, value in zip(y, means):
            ax.text(value + 0.012, yi, f"{value:.2f}", va="center", fontsize=8.5, clip_on=False)
        ax.set_yticks(y); ax.set_yticklabels([labels[b] for b in bases], fontsize=8.5)
        if ax is not axes[0]: ax.set_yticklabels([])
        ax.set_title(f"{title}  ($\\Delta$={means[0] - best_alt:+.2f})", fontsize=10)
        ax.set_xlabel("Mean focal score (truncated x-axis)")
        ax.set_xlim(x_min, x_max)
        ticks = np.linspace(x_min, x_max, 4)
        ax.set_xticks(ticks)
        ax.set_xticklabels([f"{tick:.2f}" for tick in ticks])
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    plt.tight_layout()
    for suffix in ("pdf", "png"):
        path = FIGS / f"fig_sotopia_three_exp_v1.{suffix}"
        fig.savefig(path, dpi=220 if suffix == "png" else None, bbox_inches="tight")
        sync(path)
    plt.close(fig)


def family_of(code: str) -> str:
    parts = code.split("_")
    while parts and parts[-1].isdigit():
        parts.pop()
    return "_".join(parts) if parts else code


def plot_sotopia_appendix() -> None:
    baselines = ["hpsmg_plus", "llm_psrl_verbal", "atom_tom1", "econ_bne", "llm_belief", "llm_greedy"]
    labels = {"hpsmg_plus": r"PACT$^+$", "llm_psrl_verbal": "LLM-PSRL-verbal", "atom_tom1": "A-ToM-1", "econ_bne": "ECON-BNE", "llm_belief": "llm_belief", "llm_greedy": "llm_greedy"}
    colors = {"hpsmg_plus": "#1f2d5c", "llm_psrl_verbal": "#2e7d32", "atom_tom1": "#d8a04b", "econ_bne": "#a63a3a", "llm_belief": "#7a8aa6", "llm_greedy": "#bdbdbd"}
    aggregate: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    model_map = {"DeepSeek_V3_2": "deepseek", "gpt_5_4_nano_20260317": "gpt5_nano", "Kimi_K2_6": "kimi_k2", "Llama_4_Maverick_17B_128E_Instruct_FP8": "llama_maverick"}
    for path in sorted((ROOT / "analysis").glob("sotopia_hard_official_*_sotopia_tuned_all70.json")):
        name = path.name.replace("sotopia_hard_official_", "").replace("_sotopia_tuned_all70.json", "")
        baseline = next((b for b in baselines if name.endswith("_" + b)), None)
        if baseline is None: continue
        model_raw = name[: -(len(baseline) + 1)]
        model_key = model_map.get(model_raw, model_raw)
        data = json.load(open(path, encoding="utf-8"))
        for episode in data.get("episodes", []):
            vals = [v for v in (episode.get("overall") or {}).values() if isinstance(v, (int, float))]
            if vals: aggregate[model_key][baseline].append(sum(vals) / len(vals))
    for path in sorted((ROOT / "analysis" / "llm_psrl_verbal").glob("sotopia_hard_*_llm_psrl_verbal_all70.json")):
        model_key = path.name.split("sotopia_hard_")[1].split("_llm_psrl")[0]
        data = json.load(open(path, encoding="utf-8"))
        for episode in data.get("episodes", []):
            vals = [v for v in (episode.get("overall") or {}).values() if isinstance(v, (int, float))]
            if vals: aggregate[model_key]["llm_psrl_verbal"].append(sum(vals) / len(vals))
    x = np.arange(len(MODEL_ORDER)); width = 0.13
    fig, ax = plt.subplots(figsize=(8.8, 3.8))
    offsets = (np.arange(len(baselines)) - (len(baselines)-1)/2) * width
    for i, baseline in enumerate(baselines):
        means = [mean_sem(aggregate[tier].get(baseline, []))[0] for tier in MODEL_ORDER]
        ax.bar(x + offsets[i], means, width, color=colors[baseline], label=labels[baseline], edgecolor="black" if baseline == "hpsmg_plus" else "none", linewidth=0.9)
    ax.set_xticks(x); ax.set_xticklabels([MODEL_LABEL[t] for t in MODEL_ORDER])
    ax.set_ylabel("Mean focal score (70 episodes)")
    ax.legend(ncol=3, fontsize=8, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.22))
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    plt.tight_layout()
    for suffix in ("pdf", "png"):
        path = FIGS / f"fig_sotopia_hard_appendix_v2.{suffix}"
        fig.savefig(path, dpi=220 if suffix == "png" else None, bbox_inches="tight")
        sync(path)
    plt.close(fig)


def plot_concordia_verbal_summary() -> None:
    rows = list(csv.DictReader(open(ROOT / "analysis" / "llm_psrl_verbal" / "concordia_summary.csv", encoding="utf-8")))
    selected = [r for r in rows if r["method"] in {"llm_psrl_verbal", "hpsmg_plus_joint_proxy", "oracle_joint", "oracle_focal"}]
    substrates = ["concordia_pub_london_mini", "concordia_haggling_fruitville"]
    methods_by_substrate = {
        "concordia_pub_london_mini": ["oracle_joint", "hpsmg_plus_joint_proxy", "llm_psrl_verbal"],
        "concordia_haggling_fruitville": ["oracle_focal", "oracle_joint", "hpsmg_plus_joint_proxy", "llm_psrl_verbal"],
    }
    labels = {"oracle_focal": "Oracle focal", "oracle_joint": "Oracle joint", "hpsmg_plus_joint_proxy": r"PACT$^+$", "llm_psrl_verbal": "LLM-PSRL-verbal"}
    colors = {"oracle_focal": "#2f2f2f", "oracle_joint": "#9aa0a6", "hpsmg_plus_joint_proxy": "#1f4e79", "llm_psrl_verbal": "#2e7d32"}
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.6))
    for ax, substrate in zip(axes, substrates):
        sub = [r for r in selected if r["substrate"] == substrate]
        methods = methods_by_substrate[substrate]
        # Average across four backbones for this compact summary.
        vals = []
        for method in methods:
            xs = [float(r["focal_score_mean"]) for r in sub if r["method"] == method and r.get("focal_score_mean")]
            vals.append(mean_sem(xs)[0] if xs else np.nan)
        y = np.arange(len(methods))[::-1]
        ax.barh(y, vals, color=[colors[m] for m in methods], edgecolor="black", linewidth=0.4)
        ax.set_yticks(y); ax.set_yticklabels([labels[m] for m in methods], fontsize=9)
        for yi, value in zip(y, vals):
            if value == value: ax.text(value + 0.03, yi, f"{value:.2f}", va="center", fontsize=9)
        ax.set_title("Pub Coordination" if substrate.endswith("london_mini") else "Haggling")
        ax.set_xlabel("Mean focal score")
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    plt.tight_layout()
    for suffix in ("pdf", "png"):
        path = FIGS / f"fig_concordia_llm_psrl_verbal_summary.{suffix}"
        fig.savefig(path, dpi=220 if suffix == "png" else None, bbox_inches="tight")
        sync(path)
    plt.close(fig)


def main() -> None:
    plot_hp_spgg()
    plot_sotopia_three_exp()
    plot_sotopia_appendix()
    plot_concordia_verbal_summary()
    print("wrote llm_psrl_verbal figure updates")


if __name__ == "__main__":
    main()