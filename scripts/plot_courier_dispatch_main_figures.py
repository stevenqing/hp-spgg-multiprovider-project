"""Generate the four main CourierDispatch presentation figures.

All main figures use rule-based analytic drivers. Live LLMs appear only as
platform/planner baselines, not as drivers.
"""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "analysis" / "courier_dispatch"
FIG_DIRS = [ROOT / "figs", ROOT / "arr_paper" / "figs"]

COLORS = {
    "pact": "#1b3a6f",
    "pact_plus": "#3d6cb3",
    "message": "#2c7a5e",
    "llm": "#b8723d",
    "baseline": "#6f7a86",
    "oracle": "#9aa0a6",
    "accent": "#c0463f",
}
INK = "#202020"
MUTED = "#555555"
LIGHTER = "#888888"
PALE = "#cccccc"
FAMILY_BAND = {
    "oracle": "#ffffff",
    "ours": "#f0f4fa",
    "bayesian": "#f3f6fb",
    "llm": "#fbf3ec",
    "baseline": "#f5f5f5",
}

GPT_MODEL = "gpt-5.4-mini-20260317"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def mean(values: list[float]) -> float:
    return float(sum(values) / len(values)) if values else float("nan")


def sem(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = mean(values)
    return float(math.sqrt(sum((value - avg) ** 2 for value in values) / (len(values) - 1)) / math.sqrt(len(values)))


def save_figure(fig: plt.Figure, name: str) -> None:
    for out_dir in FIG_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_dir / f"{name}.png", dpi=240, bbox_inches="tight")
        fig.savefig(out_dir / f"{name}.pdf", bbox_inches="tight")


def configure_matplotlib() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Inter", "Helvetica Neue", "Arial", "DejaVu Sans"],
            "font.size": 8.5,
            "axes.titlesize": 10,
            "axes.titleweight": "semibold",
            "axes.titlelocation": "left",
            "axes.titlepad": 10,
            "axes.labelsize": 8.8,
            "axes.labelpad": 7,
            "axes.linewidth": 0.4,
            "axes.edgecolor": PALE,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": False,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "xtick.color": "#444444",
            "ytick.color": "#444444",
            "xtick.major.size": 0,
            "ytick.major.size": 0,
            "legend.fontsize": 7.8,
            "legend.frameon": False,
            "legend.handletextpad": 0.4,
            "legend.columnspacing": 1.4,
        }
    )


def style_axis(ax: plt.Axes, *, ygrid: bool = True) -> None:
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(PALE)
        ax.spines[spine].set_linewidth(0.45)
    ax.tick_params(colors=MUTED, which="both")
    if ygrid:
        ax.grid(axis="y", linestyle=":", linewidth=0.55, color="#dddddd")
        ax.set_axisbelow(True)


def error_line(ax: plt.Axes, x, y, *, color: str, marker: str, label: str, linestyle: str = "-") -> None:
    ax.plot(
        x,
        y,
        marker=marker,
        color=color,
        linewidth=1.75,
        markersize=5.8,
        markerfacecolor="white",
        markeredgewidth=1.4,
        linestyle=linestyle,
        label=label,
        zorder=4,
    )


def plot_horizon_recovery() -> None:
    rows = read_csv(ANALYSIS_DIR / "courier_dispatch_horizon_sweep.csv")
    by_beta: dict[float, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_beta[float(row["beta"])].append(row)

    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.05), sharex=True)
    beta_styles = {
        0.0: (COLORS["pact"], "o", "PACT beta=0"),
        0.1: (COLORS["message"], "s", "PACT+ beta=0.1"),
        0.25: (COLORS["pact_plus"], "D", "PACT+ beta=0.25"),
    }
    for beta, beta_rows in sorted(by_beta.items()):
        color, marker, label = beta_styles.get(beta, ("#555555", "o", f"beta={beta:g}"))
        beta_rows = sorted(beta_rows, key=lambda row: int(row["horizon"]))
        horizons = [int(row["horizon"]) for row in beta_rows]
        p_true = [float(row["p_true"]) for row in beta_rows]
        rule_acc = [float(row["rule_acc"]) for row in beta_rows]
        error_line(axes[0], horizons, p_true, color=color, marker=marker, label=label)
        error_line(axes[1], horizons, rule_acc, color=color, marker=marker, label=label)

    axes[0].set_title("Posterior concentration")
    axes[0].set_ylabel("P(true rule tuple)")
    axes[1].set_title("Rule-marginal recovery")
    axes[1].set_ylabel("Rule accuracy")
    for ax in axes:
        ax.set_xlabel("Horizon", color=MUTED)
        ax.set_xticks([8, 16, 24, 32])
        ax.set_ylim(0.3, 1.02)
        style_axis(ax)
    axes[0].set_ylabel("P(true rule tuple)", color=MUTED)
    axes[1].set_ylabel("Rule accuracy", color=MUTED)
    axes[1].legend(loc="lower right")
    fig.tight_layout()
    save_figure(fig, "fig_courier_horizon_recovery")
    plt.close(fig)


def method_label(method: str, beta: float) -> str:
    if method == "oracle":
        return "Oracle"
    if method == "pact":
        return "PACT (ours)"
    if method == "pact_plus":
        return "PACT+ (ours)"
    if method == "pact_message":
        return "PACT-message"
    if method == "joint_psrl":
        return "Joint-PSRL"
    if method == "map_greedy":
        return "MAP-Type-Greedy"
    if method == "psrl_notype":
        return "PSRL-NoType"
    if method == "atom_tom0":
        return "A-ToM-0"
    if method == "atom_tom1":
        return "A-ToM-1"
    if method == "random":
        return "Random"
    if method == "live_llm_greedy":
        return "LLM-Greedy"
    if method == "live_llm_belief":
        return "LLM-Belief"
    if method == "live_atom_tom0":
        return "A-ToM-0"
    if method == "live_atom_tom1":
        return "A-ToM-1"
    if method == "live_atom_adaptive_hedge":
        return "A-ToM hedge"
    if method == "live_econ_bne":
        return "ECON-BNE"
    return method


def method_family(method: str) -> str:
    if method == "oracle":
        return "oracle"
    if method in {"pact", "pact_plus", "pact_message"}:
        return "ours"
    if method in {"joint_psrl", "map_greedy"}:
        return "bayesian"
    if method in {"atom_tom0", "atom_tom1", "live_llm_greedy", "live_llm_belief", "live_atom_tom0", "live_atom_tom1", "live_atom_adaptive_hedge", "live_econ_bne"}:
        return "llm"
    return "baseline"


def family_color(family: str, method: str) -> str:
    if family == "oracle":
        return COLORS["oracle"]
    if family == "ours":
        if method == "pact":
            return COLORS["pact"]
        if method == "pact_message":
            return COLORS["message"]
        return COLORS["pact_plus"]
    if family == "bayesian":
        return "#7b9fcf" if method == "map_greedy" else "#b3c5e0"
    if family == "llm":
        return COLORS["llm"] if method.startswith("live_") else "#cc8242"
    return COLORS["baseline"]


def final_stats_for_model(path: Path, model: str) -> dict[tuple[str, float], dict[str, float]]:
    rows = read_csv(path)
    model_rows = [row for row in rows if row.get("model") == model and float(row.get("couple_lambda", 0.0)) == 0.0]
    final_round = max(int(row["round"]) for row in model_rows)
    final = [row for row in model_rows if int(row["round"]) == final_round]
    grouped: dict[tuple[str, float], list[dict[str, str]]] = defaultdict(list)
    for row in final:
        grouped[(row["method"], float(row["beta"]))].append(row)
    stats: dict[tuple[str, float], dict[str, float]] = {}
    all_rows_by_key: dict[tuple[str, float], list[dict[str, str]]] = defaultdict(list)
    for row in model_rows:
        all_rows_by_key[(row["method"], float(row["beta"]))].append(row)
    for key, group in grouped.items():
        rewards = [float(row["cumulative_reward"]) for row in group]
        p_true = [float(row["mean_true_tuple_posterior"]) for row in group]
        rule_acc = [float(row["mean_rule_marginal_accuracy"]) for row in group]
        info = [float(row["cumulative_total_information_cost"]) for row in group]
        parse_rows = all_rows_by_key[key]
        parse_vals = [str(row.get("llm_parsed_ok", "True")).lower() == "true" for row in parse_rows]
        stats[key] = {
            "reward": mean(rewards),
            "reward_sem": sem(rewards),
            "p_true": mean(p_true),
            "rule_acc": mean(rule_acc),
            "info": mean(info),
            "parse": float(sum(parse_vals) / max(len(parse_vals), 1)),
        }
    return stats


def plot_gpt_all_methods() -> None:
    stats = final_stats_for_model(ANALYSIS_DIR / "courier_dispatch_live_llm_s5h8_allmodels_allbaselines_rows.csv", GPT_MODEL)
    ordered_keys = [
        ("oracle", 0.0),
        ("pact_plus", 0.1),
        ("pact", 0.0),
        ("joint_psrl", 0.0),
        ("map_greedy", 0.0),
        ("live_llm_greedy", 0.0),
        ("live_llm_belief", 0.0),
        ("live_econ_bne", 0.0),
        ("live_llm_greedy", 0.0),
        ("live_econ_bne", 0.0),
        ("live_atom_tom0", 0.0),
        ("live_atom_tom1", 0.0),
        ("live_atom_adaptive_hedge", 0.0),
        ("psrl_notype", 0.0),
        ("random", 0.0),
    ]
    # Preserve order while removing accidental duplicates.
    ordered_keys = list(dict.fromkeys(ordered_keys))
    rows = []
    for key in ordered_keys:
        if key not in stats:
            continue
        method, beta = key
        family = method_family(method)
        rows.append(
            {
                "label": method_label(method, beta),
                "method": method,
                "beta": beta,
                "family": family,
                "color": family_color(family, method),
                **stats[key],
            }
        )

    fig, ax = plt.subplots(figsize=(7.8, 4.9))
    y = np.arange(len(rows))
    family_ranges = []
    start = 0
    for idx in range(1, len(rows) + 1):
        if idx == len(rows) or rows[idx]["family"] != rows[start]["family"]:
            family_ranges.append((start, idx - 1, str(rows[start]["family"])))
            start = idx
    for lo, hi, family in family_ranges:
        if family != "oracle":
            ax.axhspan(lo - 0.45, hi + 0.45, color=FAMILY_BAND[family], alpha=0.55, zorder=0)
    ax.barh(
        y,
        [float(row["reward"]) for row in rows],
        xerr=[float(row["reward_sem"]) for row in rows],
        height=0.58,
        color=[str(row["color"]) for row in rows],
        edgecolor="white",
        linewidth=0.8,
        capsize=2.5,
        zorder=3,
    )
    ax.set_yticks(y)
    ax.set_yticklabels([str(row["label"]) for row in rows])
    ax.invert_yaxis()
    ax.set_xlabel("Cumulative reward at H=8", color=MUTED)
    ax.set_title("CourierDispatch planner comparison", loc="left")
    ax.set_xlim(0.0, 7.8)
    style_axis(ax, ygrid=False)
    ax.grid(axis="x", linestyle=":", linewidth=0.55, color="#dddddd")
    ax.set_axisbelow(True)
    for idx, row in enumerate(rows):
        value = float(row["reward"])
        ax.text(value + float(row["reward_sem"]) + 0.08, idx, f"{value:.2f}", va="center", ha="left", fontsize=7.2, color=INK)
        if str(row["method"]).startswith("live_") and float(row["parse"]) < 0.9:
            ax.text(0.08, idx + 0.24, f"parse {float(row['parse']):.2f}", va="center", ha="left", fontsize=6.7, color=COLORS["accent"])
    fig.tight_layout()
    save_figure(fig, "fig_courier_gpt_all_methods")
    plt.close(fig)


def plot_beta_tradeoff() -> None:
    rows = read_csv(ANALYSIS_DIR / "courier_dispatch_horizon_sweep.csv")
    horizons = [24, 32]
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.05), sharex=True)
    markers = {24: "o", 32: "s"}
    colors = {24: COLORS["pact"], 32: COLORS["pact_plus"]}

    for horizon in horizons:
        subset = sorted([row for row in rows if int(row["horizon"]) == horizon], key=lambda row: float(row["beta"]))
        betas = [float(row["beta"]) for row in subset]
        reward = [float(row["reward_per_round"]) for row in subset]
        p_true = [float(row["p_true"]) for row in subset]
        error_line(axes[0], betas, reward, marker=markers[horizon], color=colors[horizon], label=f"H={horizon}")
        error_line(axes[1], betas, p_true, marker=markers[horizon], color=colors[horizon], label=f"H={horizon}")

    axes[0].set_title("Reward cost")
    axes[0].set_ylabel("Reward / round")
    axes[1].set_title("Inference gain")
    axes[1].set_ylabel("P(true rule tuple)")
    for ax in axes:
        ax.set_xlabel("PACT+ beta", color=MUTED)
        ax.set_xticks([0.0, 0.1, 0.25])
        style_axis(ax)
    axes[0].set_ylabel("Reward / round", color=MUTED)
    axes[1].set_ylabel("P(true rule tuple)", color=MUTED)
    axes[0].set_ylim(0.70, 0.77)
    axes[1].set_ylim(0.74, 0.97)
    axes[0].legend(loc="lower left")
    fig.tight_layout()
    save_figure(fig, "fig_courier_beta_tradeoff")
    plt.close(fig)


def live_best_by_model() -> list[dict[str, object]]:
    rows = read_csv(ANALYSIS_DIR / "courier_dispatch_live_llm_s5h24_allmodels_allbaselines_liveonly_rows.csv")
    final = [row for row in rows if int(row["round"]) == 23]
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in final:
        grouped[(row["model"], row["method"])].append(row)

    best_rows = []
    by_model: dict[str, list[tuple[str, list[dict[str, str]]]]] = defaultdict(list)
    for (model, method), group in grouped.items():
        by_model[model].append((method, group))
    label_map = {
        "gpt-5.4-mini-20260317": "GPT-5.4-mini",
        "DeepSeek-V3.2": "DeepSeek-V3.2",
        "Kimi-K2.6": "Kimi-K2.6",
        "Llama-4-Maverick-17B-128E-Instruct-FP8": "Llama-4-Maverick",
    }
    for model, candidates in by_model.items():
        best_method = None
        best_reward = -1e9
        best_values: list[float] = []
        best_parse = 0.0
        best_info = 0.0
        for method, group in candidates:
            rewards = [float(row["cumulative_reward"]) / 24.0 for row in group]
            reward_mean = mean(rewards)
            if reward_mean > best_reward:
                best_reward = reward_mean
                best_method = method
                best_values = rewards
                parse_rows = [row for row in rows if row["model"] == model and row["method"] == method]
                parses = [str(row["llm_parsed_ok"]).lower() == "true" for row in parse_rows]
                best_parse = float(sum(parses) / max(len(parses), 1))
                best_info = mean([float(row["cumulative_total_information_cost"]) for row in group])
        best_rows.append(
            {
                "model": label_map.get(model, model),
                "method": str(best_method),
                "reward": best_reward,
                "sem": sem(best_values),
                "parse": best_parse,
                "info": best_info,
            }
        )
    order = ["GPT-5.4-mini", "DeepSeek-V3.2", "Kimi-K2.6", "Llama-4-Maverick"]
    return sorted(best_rows, key=lambda row: order.index(str(row["model"])))


def plot_live_llm_comparison() -> None:
    best_live = live_best_by_model()
    rows = [
        {"label": "PACT", "reward": 0.758, "sem": 0.0, "family": "ours", "color": COLORS["pact"], "note": "ours"},
        {"label": "PACT+ beta=0.1", "reward": 0.757, "sem": 0.0, "family": "ours", "color": COLORS["pact_plus"], "note": "ours"},
    ]
    for row in best_live:
        rows.append(
            {
                "label": str(row["model"]),
                "reward": float(row["reward"]),
                "sem": float(row["sem"]),
                "family": "llm",
                "color": COLORS["llm"],
                "note": str(row["method"]).replace("live_", ""),
                "parse": float(row["parse"]),
            }
        )

    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    y = np.arange(len(rows))
    for idx, row in enumerate(rows):
        band = FAMILY_BAND[str(row["family"])]
        ax.axhspan(idx - 0.45, idx + 0.45, color=band, alpha=0.72, zorder=0)
    ax.barh(
        y,
        [float(row["reward"]) for row in rows],
        xerr=[float(row["sem"]) for row in rows],
        color=[str(row["color"]) for row in rows],
        edgecolor="white",
        linewidth=0.8,
        capsize=2.5,
        zorder=3,
    )
    ax.set_yticks(y)
    ax.set_yticklabels([str(row["label"]) for row in rows])
    ax.invert_yaxis()
    ax.set_xlabel("Reward / round", color=MUTED)
    ax.set_title("Live LLM planners vs PACT", loc="left")
    ax.set_xlim(0.0, 0.86)
    style_axis(ax, ygrid=False)
    ax.grid(axis="x", linestyle=":", linewidth=0.55, color="#dddddd")
    ax.set_axisbelow(True)
    for idx, row in enumerate(rows):
        value = float(row["reward"])
        ax.text(value + float(row["sem"]) + 0.012, idx, f"{value:.3f}", va="center", ha="left", fontsize=7.4, color=INK)
        note = str(row["note"])
        if row["family"] == "llm":
            ax.text(0.012, idx + 0.24, note, va="center", ha="left", fontsize=6.8, color=LIGHTER)
            if float(row.get("parse", 1.0)) < 0.9:
                ax.text(0.40, idx + 0.24, f"parse {float(row['parse']):.2f}", va="center", ha="left", fontsize=6.8, color=COLORS["accent"])
    fig.tight_layout()
    save_figure(fig, "fig_courier_live_llm_planner_comparison")
    plt.close(fig)


def plot_masking_rl_stress() -> None:
    rows = read_csv(ANALYSIS_DIR / "courier_dispatch_masking_rl_stress.csv")
    lambdas = np.asarray([float(row["couple_lambda"]) for row in rows], dtype=float)
    p_true = np.asarray([float(row["p_true"]) for row in rows], dtype=float)
    p_sem = np.asarray([float(row["p_true_sem"]) for row in rows], dtype=float)
    rule_acc = np.asarray([float(row["rule_acc"]) for row in rows], dtype=float)
    rule_sem = np.asarray([float(row["rule_acc_sem"]) for row in rows], dtype=float)
    nll = np.asarray([float(row["nll_true"]) for row in rows], dtype=float)
    nll_sem = np.asarray([float(row["nll_true_sem"]) for row in rows], dtype=float)

    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.05), sharex=True)
    axes[0].errorbar(lambdas, p_true, yerr=p_sem, marker="o", linewidth=1.75, color=COLORS["pact"], capsize=3, capthick=0.7, elinewidth=0.7, markerfacecolor="white", markeredgewidth=1.35, label="P(true)")
    axes[0].errorbar(lambdas, rule_acc, yerr=rule_sem, marker="s", linewidth=1.75, color=COLORS["message"], capsize=3, capthick=0.7, elinewidth=0.7, markerfacecolor="white", markeredgewidth=1.35, label="Rule acc")
    axes[1].errorbar(lambdas, nll, yerr=nll_sem, marker="D", linewidth=1.75, color=COLORS["accent"], capsize=3, capthick=0.7, elinewidth=0.7, markerfacecolor="white", markeredgewidth=1.35, label="NLL(true)")

    axes[0].set_title("Posterior degrades")
    axes[0].set_ylabel("Recovery metric", color=MUTED)
    axes[0].set_ylim(0.30, 1.02)
    axes[0].legend(loc="upper right")
    axes[1].set_title("True-type NLL rises")
    axes[1].set_ylabel("NLL(true)", color=MUTED)
    axes[1].set_ylim(0.0, 3.25)
    for ax in axes:
        ax.set_xlabel("couple_lambda", color=MUTED)
        ax.set_xticks(lambdas)
        style_axis(ax)
    fig.tight_layout()
    save_figure(fig, "fig_courier_masking_rl_stress")
    plt.close(fig)


def main() -> None:
    configure_matplotlib()
    plot_gpt_all_methods()
    plot_horizon_recovery()
    plot_beta_tradeoff()
    plot_live_llm_comparison()
    plot_masking_rl_stress()
    for name in [
        "fig_courier_gpt_all_methods",
        "fig_courier_horizon_recovery",
        "fig_courier_beta_tradeoff",
        "fig_courier_live_llm_planner_comparison",
        "fig_courier_masking_rl_stress",
    ]:
        print(f"wrote figs/{name}.png and .pdf")


if __name__ == "__main__":
    main()