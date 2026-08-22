"""Plot four-model CloudGPT PACT+ beta sweep for CourierDispatch matching."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis" / "courier_dispatch_matching"
OUT_DIRS = [ROOT / "figs", ROOT / "arr_paper" / "figs"]

BETAS = [0.0, 0.025, 0.05, 0.1, 0.2, 0.4]
MODEL_ORDER = [
    "gpt-5.4-mini-20260317",
    "DeepSeek-V3.2",
    "Kimi-K2.6",
    "Llama-4-Maverick-17B-128E-Instruct-FP8",
]
MODEL_LABELS = {
    "gpt-5.4-mini-20260317": "GPT-5.4-mini",
    "DeepSeek-V3.2": "DeepSeek-V3.2",
    "Kimi-K2.6": "Kimi-K2.6",
    "Llama-4-Maverick-17B-128E-Instruct-FP8": "Llama-Maverick",
}
MODEL_COLORS = {
    "gpt-5.4-mini-20260317": "#1b3a6f",
    "DeepSeek-V3.2": "#3d6cb3",
    "Kimi-K2.6": "#c7773d",
    "Llama-4-Maverick-17B-128E-Instruct-FP8": "#7b6fb0",
}
INK = "#202020"
MUTED = "#555555"
PALE = "#cccccc"


def configure_matplotlib() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Inter", "Helvetica Neue", "Arial", "DejaVu Sans"],
            "font.size": 8.8,
            "axes.titlesize": 10.5,
            "axes.titleweight": "semibold",
            "axes.titlelocation": "left",
            "axes.titlepad": 9,
            "axes.labelsize": 8.8,
            "axes.linewidth": 0.45,
            "axes.edgecolor": PALE,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "xtick.color": "#444444",
            "ytick.color": "#444444",
            "legend.fontsize": 7.8,
            "savefig.dpi": 240,
        }
    )


def beta_tag(beta: float) -> str:
    return str(beta).replace(".", "p")


def mean(values: list[float]) -> float:
    return float(sum(values) / len(values)) if values else float("nan")


def sem(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = mean(values)
    return float(math.sqrt(sum((value - avg) ** 2 for value in values) / (len(values) - 1)) / math.sqrt(len(values)))


def load_beta(beta: float) -> dict:
    path = ANALYSIS / f"courier_matching_structured_live_expected_pact_beta_{beta_tag(beta)}_s5h8_allmodels_summary.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["setting"]["backend"] == "cloudgpt"
    assert payload["setting"]["decision_mode"] == "structured_solver_with_llm_score_calls"
    return payload


def collect_rows() -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    for beta in BETAS:
        payload = load_beta(beta)
        final_round = int(payload["setting"]["horizon"]) - 1
        by_model: dict[str, list[dict]] = {model: [] for model in MODEL_ORDER}
        for row in payload["rows"]:
            if int(row["round"]) == final_round and row["method"] == "live_pact_plus":
                by_model[str(row["model"])].append(row)
        summary_by_model = {str(row["model"]): row for row in payload["summary"] if row["method"] == "live_pact_plus"}
        for model in MODEL_ORDER:
            finals = by_model[model]
            regrets = [float(row["cumulative_regret"]) for row in finals]
            rewards = [float(row["cumulative_reward"]) for row in finals]
            summary = summary_by_model[model]
            rows.append(
                {
                    "beta": beta,
                    "model": model,
                    "model_label": MODEL_LABELS[model],
                    "regret": mean(regrets),
                    "regret_sem": sem(regrets),
                    "reward": mean(rewards),
                    "reward_sem": sem(rewards),
                    "p_true": float(summary["final_mean_true_tuple_posterior"]),
                    "rule_acc": float(summary["final_mean_rule_marginal_accuracy"]),
                    "parse": float(summary["live_score_parse_ok_rate"]),
                }
            )
    return rows


def write_rows(rows: list[dict[str, float | str]]) -> None:
    out_csv = ANALYSIS / "courier_matching_structured_live_expected_pact_beta_sweep_s5h8_allmodels_summary.csv"
    out_json = ANALYSIS / "courier_matching_structured_live_expected_pact_beta_sweep_s5h8_allmodels_summary.json"
    fields = ["beta", "model", "model_label", "regret", "regret_sem", "reward", "reward_sem", "p_true", "rule_acc", "parse"]
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    out_json.write_text(json.dumps({"backend": "cloudgpt", "betas": BETAS, "rows": rows}, indent=2), encoding="utf-8")


def style_axis(ax: plt.Axes) -> None:
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(PALE)
        ax.spines[spine].set_linewidth(0.45)
    ax.tick_params(colors=MUTED, which="both")
    ax.grid(axis="y", linestyle=":", linewidth=0.55, color="#dddddd")
    ax.set_axisbelow(True)


def plot(rows: list[dict[str, float | str]]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.45), sharex=True)
    for model in MODEL_ORDER:
        subset = [row for row in rows if row["model"] == model]
        subset.sort(key=lambda row: float(row["beta"]))
        betas = [float(row["beta"]) for row in subset]
        color = MODEL_COLORS[model]
        label = MODEL_LABELS[model]
        axes[0].errorbar(
            betas,
            [float(row["regret"]) for row in subset],
            yerr=[float(row["regret_sem"]) for row in subset],
            marker="o",
            linewidth=1.8,
            markersize=5.5,
            capsize=2.4,
            color=color,
            markerfacecolor="white",
            markeredgewidth=1.25,
            label=label,
        )
        axes[1].plot(
            betas,
            [float(row["rule_acc"]) for row in subset],
            marker="s",
            linewidth=1.8,
            markersize=5.2,
            color=color,
            markerfacecolor="white",
            markeredgewidth=1.25,
            label=label,
        )

    for ax in axes:
        ax.set_xlabel(r"PACT$^+$ exploration coefficient $\beta$")
        ax.set_xticks(BETAS)
        ax.set_xticklabels(["0", ".025", ".05", ".1", ".2", ".4"])
        style_axis(ax)
    axes[0].set_title("Regret is minimized near beta = 0.05")
    axes[0].set_ylabel("Cumulative regret at H=8")
    axes[0].set_ylim(1.25, 2.75)
    axes[1].set_title("Exploration/recovery tradeoff")
    axes[1].set_ylabel("Rule marginal accuracy")
    axes[1].set_ylim(0.70, 0.83)
    axes[0].legend(loc="upper right", ncol=1)
    fig.suptitle(
        "CloudGPT structured matching: four-model PACT+ beta sweep",
        x=0.03,
        y=1.02,
        ha="left",
        fontsize=12,
        fontweight="semibold",
        color=INK,
    )
    fig.tight_layout()
    for out_dir in OUT_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_dir / "fig_courier_matching_llm_backend_beta_sweep.png", dpi=260, bbox_inches="tight", facecolor="white")
        fig.savefig(out_dir / "fig_courier_matching_llm_backend_beta_sweep.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    configure_matplotlib()
    rows = collect_rows()
    write_rows(rows)
    plot(rows)
    print("OK: analysis/courier_dispatch_matching/courier_matching_structured_live_expected_pact_beta_sweep_s5h8_allmodels_summary.csv")
    print("OK: figs/fig_courier_matching_llm_backend_beta_sweep.png")


if __name__ == "__main__":
    main()