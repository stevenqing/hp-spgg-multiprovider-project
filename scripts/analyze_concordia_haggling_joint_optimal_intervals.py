"""Enumerate focal-score ranges inside Haggling joint-optimal action sets.

The compact Haggling oracle_joint maximizes buyer_score + seller_score. In a
transfer-price bargain, that total surplus is flat over many feasible prices,
so the stored oracle_joint row depends on tie-breaking. This script computes
the focal-score interval induced by all joint-optimal choices for the four
Pareto-selected Haggling configurations.
"""
from __future__ import annotations

import csv
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from llm_hpgg_concordia import run_haggling_compact as haggling


ANALYSIS = ROOT / "analysis"
GIT_SNAPSHOT = "9e7f12b"

CONFIGS = [
    {
        "config_key": "fruitville_gullible_single",
        "config_label": "Fruitville: gullible buyer",
        "domain": "haggling",
        "config_name": "fruitville_gullible",
        "source_json": "analysis/concordia_haggling_compact_fruitville_gullible_s30.json",
    },
    {
        "config_key": "vegbrooke_stubborn_single",
        "config_label": "Vegbrooke: stubborn seller",
        "domain": "haggling",
        "config_name": "vegbrooke_stubborn",
        "source_json": "analysis/concordia_haggling_compact_vegbrooke_stubborn_s30.json",
    },
    {
        "config_key": "cumulative_score_multi",
        "config_label": "Multi-item: cumulative",
        "domain": "haggling_multi_item",
        "config_name": "cumulative_score",
        "source_json": "analysis/concordia_haggling_multi_item_compact_cumulative_score_s30.json",
    },
    {
        "config_key": "fruitville_gullible_multi",
        "config_label": "Multi-item: gullible",
        "domain": "haggling_multi_item",
        "config_name": "fruitville_gullible",
        "source_json": "analysis/concordia_haggling_multi_item_compact_fruitville_gullible_s30.json",
    },
]


def git_json(path: str) -> dict[str, Any]:
    raw = subprocess.check_output(["git", "show", f"{GIT_SNAPSHOT}:{path}"], cwd=ROOT)
    return json.loads(raw)


def deal_options(case: dict[str, Any], deal: dict[str, Any]) -> list[tuple[float, float, dict[str, str]]]:
    options: list[tuple[float, float, dict[str, str]]] = []
    if case["domain"] == "haggling":
        prices = [haggling.price_value(option) for option in case["price_options"]]
        for price in prices:
            for accept in (False, True):
                buyer_score, seller_score = haggling.single_scores(
                    float(deal["buyer_reward"]),
                    float(deal["seller_cost"]),
                    price,
                    accept,
                )
                options.append((buyer_score, seller_score, haggling.make_single_action(deal, price, accept)))
        return options

    prices = [float(price) for price in case["prices"]]
    for item in case["items"]:
        for price in prices:
            for accept in (False, True):
                buyer_score, seller_score = haggling.single_scores(
                    float(deal["buyer_rewards"][item]),
                    float(deal["seller_costs"][item]),
                    price,
                    accept,
                )
                options.append((buyer_score, seller_score, haggling.make_multi_action(deal, item, price, accept)))
    return options


def focal_value_for_deal(case: dict[str, Any], deal: dict[str, Any], buyer_score: float, seller_score: float) -> float:
    focal_players = set(case["focal_players"])
    focal_value = 0.0
    if deal["buyer"] in focal_players:
        focal_value += buyer_score
    if deal["seller"] in focal_players:
        focal_value += seller_score
    return focal_value


def episode_interval(case: dict[str, Any]) -> dict[str, float]:
    min_focal_sum = 0.0
    max_focal_sum = 0.0
    tiebreak_focal_sum = 0.0
    tie_counts: list[int] = []
    for deal in case["deals"]:
        options = deal_options(case, deal)
        max_joint = max(buyer_score + seller_score for buyer_score, seller_score, _ in options)
        tied_options = [
            (buyer_score, seller_score, action)
            for buyer_score, seller_score, action in options
            if math.isclose(buyer_score + seller_score, max_joint, rel_tol=0.0, abs_tol=1e-12)
        ]
        focal_values = [
            focal_value_for_deal(case, deal, buyer_score, seller_score)
            for buyer_score, seller_score, _ in tied_options
        ]
        min_focal_sum += min(focal_values)
        max_focal_sum += max(focal_values)
        tie_counts.append(len(tied_options))

        tiebreak_action, _ = haggling.choose_action(case, deal, "oracle_joint")
        tiebreak_scores = haggling.score_deal(case, deal, tiebreak_action)
        tiebreak_focal_sum += sum(float(tiebreak_scores.get(player, 0.0)) for player in case["focal_players"])

    focal_count = max(1, len(case["focal_players"]))
    return {
        "joint_opt_focal_min": min_focal_sum / focal_count,
        "joint_opt_focal_max": max_focal_sum / focal_count,
        "oracle_joint_tiebreak_focal": tiebreak_focal_sum / focal_count,
        "tie_count_min": float(min(tie_counts)),
        "tie_count_max": float(max(tie_counts)),
        "tie_count_mean": sum(tie_counts) / len(tie_counts),
    }


def mean(values: list[float]) -> float:
    return sum(values) / max(1, len(values))


def build_rows() -> list[dict[str, Any]]:
    haggling.ensure_concordia_examples_on_path()
    rows: list[dict[str, Any]] = []
    for config in CONFIGS:
        module = haggling.load_config(config["domain"], config["config_name"])
        episode_rows = [episode_interval(haggling.build_case(config["domain"], module, seed)) for seed in range(30)]
        summary = {row["method"]: row for row in git_json(config["source_json"])["summary"]}
        tiebreak_values = [row["oracle_joint_tiebreak_focal"] for row in episode_rows]
        min_values = [row["joint_opt_focal_min"] for row in episode_rows]
        max_values = [row["joint_opt_focal_max"] for row in episode_rows]
        rows.append(
            {
                **config,
                "episodes": 30,
                "source_snapshot": GIT_SNAPSHOT,
                "joint_opt_focal_min_mean": mean(min_values),
                "joint_opt_focal_max_mean": mean(max_values),
                "oracle_joint_tiebreak_focal_mean": mean(tiebreak_values),
                "oracle_joint_source_focal_mean": float(summary["oracle_joint"]["focal_score_mean"]),
                "pact_plus_joint_proxy_focal_mean": float(summary["hpsmg_plus_joint_proxy"]["focal_score_mean"]),
                "oracle_joint_deal_score_mean": float(summary["oracle_joint"]["deal_score_mean"]),
                "pact_plus_joint_proxy_deal_score_mean": float(summary["hpsmg_plus_joint_proxy"]["deal_score_mean"]),
                "oracle_joint_deal_min_score_mean": float(summary["oracle_joint"]["deal_min_score_mean"]),
                "pact_plus_joint_proxy_deal_min_score_mean": float(summary["hpsmg_plus_joint_proxy"]["deal_min_score_mean"]),
                "oracle_joint_nash_product_mean": float(summary["oracle_joint"]["nash_product_mean"]),
                "pact_plus_joint_proxy_nash_product_mean": float(summary["hpsmg_plus_joint_proxy"]["nash_product_mean"]),
                "tie_count_min": min(row["tie_count_min"] for row in episode_rows),
                "tie_count_max": max(row["tie_count_max"] for row in episode_rows),
                "tie_count_mean": mean([row["tie_count_mean"] for row in episode_rows]),
                "tiebreak_episode_at_interval_min_count": sum(
                    math.isclose(tiebreak, min_value, rel_tol=0.0, abs_tol=1e-12)
                    for tiebreak, min_value in zip(tiebreak_values, min_values)
                ),
                "tiebreak_episode_at_interval_max_count": sum(
                    math.isclose(tiebreak, max_value, rel_tol=0.0, abs_tol=1e-12)
                    for tiebreak, max_value in zip(tiebreak_values, max_values)
                ),
            }
        )
    return rows


def write_outputs(rows: list[dict[str, Any]]) -> None:
    csv_path = ANALYSIS / "concordia_haggling_joint_optimal_focal_intervals.csv"
    md_path = ANALYSIS / "concordia_haggling_joint_optimal_focal_intervals.md"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# Concordia Haggling Joint-Optimal Focal Intervals",
        "",
        "The compact Haggling `oracle_joint` maximizes total buyer+seller payoff. Because price is a transfer, many accepted prices have identical total surplus but different focal-player payoffs. The stored `oracle_joint` focal score is therefore a tie-break point, not the focal-best value within the joint-optimal set.",
        "",
        "`oracle_joint` itself is pure total surplus in `run_haggling_compact.py`. The `hpsmg_plus_blend_a0` implementation is not pure total surplus: at alpha=0 it uses `buyer_score + seller_score + 0.35 * min(buyer_score, seller_score) + 0.15 * nash`.",
        "",
        "| Config | joint-opt focal interval | stored oracle_joint focal | PACT+ focal | joint surplus oracle / PACT+ | min surplus oracle / PACT+ | Nash oracle / PACT+ |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {config_label} | [{joint_opt_focal_min_mean:.3f}, {joint_opt_focal_max_mean:.3f}] | {oracle_joint_tiebreak_focal_mean:.3f} | {pact_plus_joint_proxy_focal_mean:.3f} | {oracle_joint_deal_score_mean:.3f} / {pact_plus_joint_proxy_deal_score_mean:.3f} | {oracle_joint_deal_min_score_mean:.3f} / {pact_plus_joint_proxy_deal_min_score_mean:.3f} | {oracle_joint_nash_product_mean:.3f} / {pact_plus_joint_proxy_nash_product_mean:.3f} |".format(**row)
        )
    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            "- The Haggling `oracle_joint` focal value can look worse because it is an arbitrary tie-break inside a flat total-surplus optimum set.",
            "- On all four selected configs, PACT+ matches the `oracle_joint` mean joint surplus while choosing a more balanced/focal-favorable split than the stored tie-break.",
            "- PACT+ is not claimed to reach the upper end of the joint-optimal focal interval; the interval is a diagnostic for transfer-allocation indeterminacy, not a new strict ceiling.",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {csv_path}")
    print(f"wrote {md_path}")


def main() -> None:
    write_outputs(build_rows())


if __name__ == "__main__":
    main()