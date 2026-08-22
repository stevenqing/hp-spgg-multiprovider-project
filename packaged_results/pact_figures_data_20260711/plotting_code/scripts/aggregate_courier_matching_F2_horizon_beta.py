"""Aggregate unified w_LLM=0 CourierDispatch F2 horizon/beta summaries."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis" / "courier_dispatch_matching"
MODEL_LABELS = {
    "gpt-5.4-mini-20260317": "GPT-5.4-mini",
    "DeepSeek-V3.2": "DeepSeek-V3.2",
    "Kimi-K2.6": "Kimi-K2.6",
    "Llama-4-Maverick-17B-128E-Instruct-FP8": "Llama-Maverick",
}
HORIZONS = [8, 16, 24, 32]
BETAS = [0.0, 0.1, 0.25, 0.5]
TAGS = {0.0: "0p0", 0.1: "0p1", 0.25: "0p25", 0.5: "0p5"}
FIELDS = [
    "horizon",
    "beta",
    "source",
    "model",
    "model_label",
    "reward",
    "reward_sem",
    "regret",
    "regret_sem",
    "ptrue",
    "ptrue_sem",
    "rule_acc",
    "rule_acc_sem",
    "exploration_cost",
    "exploration_cost_sem",
]


def mean(values: list[float]) -> float:
    return float(sum(values) / len(values)) if values else float("nan")


def sem(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = mean(values)
    return float(math.sqrt(sum((value - avg) ** 2 for value in values) / (len(values) - 1)) / math.sqrt(len(values)))


def rows_path(horizon: int, beta: float) -> Path:
    return ANALYSIS / f"courier_matching_F2_wllm0_exact_h{horizon}_beta_{TAGS[beta]}_rows.csv"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def aggregate() -> tuple[list[dict[str, object]], list[str]]:
    rows: list[dict[str, object]] = []
    missing: list[str] = []
    for beta in BETAS:
        for horizon in HORIZONS:
            path = rows_path(horizon, beta)
            if not path.exists():
                missing.append(path.name)
                continue
            raw_rows = read_rows(path)
            final_round = horizon - 1
            final = [row for row in raw_rows if int(row["round"]) == final_round]
            if not final:
                missing.append(f"{path.name}:final_round")
                continue
            metric_values = {
                "reward": [float(row["cumulative_reward"]) for row in final],
                "regret": [float(row["cumulative_regret"]) for row in final],
                "ptrue": [float(row["mean_true_tuple_posterior"]) for row in final],
                "rule_acc": [float(row["mean_rule_marginal_accuracy"]) for row in final],
                "exploration_cost": [float(row["cumulative_exploration_cost"]) for row in final],
            }
            for model, label in MODEL_LABELS.items():
                rows.append(
                    {
                        "horizon": horizon,
                        "beta": beta,
                        "source": "exact",
                        "model": model,
                        "model_label": label,
                        "reward": mean(metric_values["reward"]),
                        "reward_sem": sem(metric_values["reward"]),
                        "regret": mean(metric_values["regret"]),
                        "regret_sem": sem(metric_values["regret"]),
                        "ptrue": mean(metric_values["ptrue"]),
                        "ptrue_sem": sem(metric_values["ptrue"]),
                        "rule_acc": mean(metric_values["rule_acc"]),
                        "rule_acc_sem": sem(metric_values["rule_acc"]),
                        "exploration_cost": mean(metric_values["exploration_cost"]),
                        "exploration_cost_sem": sem(metric_values["exploration_cost"]),
                    }
                )
    rows.sort(key=lambda row: (int(row["horizon"]), float(row["beta"]), str(row["model_label"])))
    return rows, missing


def main() -> None:
    rows, missing = aggregate()
    out_csv = ANALYSIS / "courier_matching_live_F2_horizon_beta_sweep_summary.csv"
    out_json = ANALYSIS / "courier_matching_live_F2_horizon_beta_sweep_summary.json"
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    out_json.write_text(
        json.dumps(
            {
                "backend": "cloudgpt",
                "objective": "w_LLM=0",
                "rows": rows,
                "missing": missing,
                "note": "Unified F2 aggregation: all beta/horizon rows come from the exact w_LLM=0 structured evaluator. At w_LLM=0 the LLM score term is inactive; H=8 beta=0.5 was live-verified against this evaluator.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps({"csv": str(out_csv.relative_to(ROOT)), "json": str(out_json.relative_to(ROOT)), "rows": len(rows), "missing": missing}, indent=2))


if __name__ == "__main__":
    main()