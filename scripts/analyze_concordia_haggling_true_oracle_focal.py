"""Compute the true focal oracle for compact Concordia Haggling.

The reported Haggling metric is focal_score_mean, so the proper upper
reference is oracle_focal: full-information enumeration that directly
maximizes the focal player's payoff on each deal. This differs from
oracle_joint, which maximizes total buyer+seller surplus and is tie-break
dependent in transfer-price bargains.
"""
from __future__ import annotations

import csv
import json
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
    ("fruitville", "fruitville (single)", "haggling", "fruitville", "analysis/concordia_haggling_compact_fruitville_s30.json"),
    ("fruitville_gullible", "fruitville gullible (single)", "haggling", "fruitville_gullible", "analysis/concordia_haggling_compact_fruitville_gullible_s30.json"),
    ("vegbrooke", "vegbrooke (single)", "haggling", "vegbrooke", "analysis/concordia_haggling_compact_vegbrooke_s30.json"),
    ("vegbrooke_stubborn", "vegbrooke stubborn", "haggling", "vegbrooke_stubborn", "analysis/concordia_haggling_compact_vegbrooke_stubborn_s30.json"),
    ("vegbrooke_strange_game", "vegbrooke strange", "haggling", "vegbrooke_strange_game", "analysis/concordia_haggling_compact_vegbrooke_strange_game_s30.json"),
    ("fruitville_multi", "fruitville multi", "haggling_multi_item", "fruitville_multi", "analysis/concordia_haggling_multi_item_compact_fruitville_multi_s30.json"),
    ("fruitville_gullible", "fruitville gullible (multi)", "haggling_multi_item", "fruitville_gullible", "analysis/concordia_haggling_multi_item_compact_fruitville_gullible_s30.json"),
    ("vegbrooke", "vegbrooke (multi)", "haggling_multi_item", "vegbrooke", "analysis/concordia_haggling_multi_item_compact_vegbrooke_s30.json"),
    ("cumulative_score", "cumulative score (multi)", "haggling_multi_item", "cumulative_score", "analysis/concordia_haggling_multi_item_compact_cumulative_score_s30.json"),
]


def git_json(path: str) -> dict[str, Any]:
    raw = subprocess.check_output(["git", "show", f"{GIT_SNAPSHOT}:{path}"], cwd=ROOT)
    return json.loads(raw)


def mean(values: list[float]) -> float:
    return sum(values) / max(1, len(values))


def oracle_focal_summary(domain: str, config_name: str, seeds: int = 30) -> dict[str, float]:
    module = haggling.load_config(domain, config_name)
    rows = [haggling.run_method(haggling.build_case(domain, module, seed), "oracle_focal") for seed in range(seeds)]
    return {
        "oracle_focal_focal_score_mean": mean([float(row["focal_score_mean"]) for row in rows]),
        "oracle_focal_focal_score_min_mean": mean([float(row["focal_score_min"]) for row in rows]),
        "oracle_focal_deal_score_mean": mean([float(row["deal_score_mean"]) for row in rows]),
        "oracle_focal_deal_min_score_mean": mean([float(row["deal_min_score_mean"]) for row in rows]),
        "oracle_focal_nash_product_mean": mean([float(row["nash_product_mean"]) for row in rows]),
        "oracle_focal_agreement_rate_mean": mean([float(row["agreement_rate"]) for row in rows]),
        "oracle_focal_valid_action_rate_mean": mean([float(row["valid_action_rate"]) for row in rows]),
    }


def build_rows() -> list[dict[str, Any]]:
    haggling.ensure_concordia_examples_on_path()
    rows: list[dict[str, Any]] = []
    for config_key, label, domain, config_name, source_json in CONFIGS:
        historical = git_json(source_json)
        summary = {row["method"]: row for row in historical["summary"]}
        true_oracle = oracle_focal_summary(domain, config_name)
        non_oracle_rows = [row for row in historical["summary"] if not row["method"].startswith("oracle")]
        best_non_oracle = max(non_oracle_rows, key=lambda row: float(row["focal_score_mean"]))
        pact = summary["hpsmg_plus_joint_proxy"]
        joint = summary["oracle_joint"]
        rows.append(
            {
                "config_key": config_key,
                "axis_label": label,
                "domain": domain,
                "config_name": config_name,
                "episodes": 30,
                "source_snapshot": GIT_SNAPSHOT,
                "source_json": source_json,
                **true_oracle,
                "best_non_oracle_method": best_non_oracle["method"],
                "best_non_oracle_focal_score_mean": float(best_non_oracle["focal_score_mean"]),
                "pact_plus_joint_proxy_focal_score_mean": float(pact["focal_score_mean"]),
                "pact_plus_joint_proxy_deal_score_mean": float(pact["deal_score_mean"]),
                "oracle_joint_focal_score_mean": float(joint["focal_score_mean"]),
                "oracle_joint_deal_score_mean": float(joint["deal_score_mean"]),
                "gap_oracle_focal_minus_pact_plus": true_oracle["oracle_focal_focal_score_mean"] - float(pact["focal_score_mean"]),
                "gap_oracle_focal_minus_best_non_oracle": true_oracle["oracle_focal_focal_score_mean"] - float(best_non_oracle["focal_score_mean"]),
            }
        )
    return rows


def write_outputs(rows: list[dict[str, Any]]) -> None:
    csv_path = ANALYSIS / "concordia_haggling_true_oracle_focal.csv"
    md_path = ANALYSIS / "concordia_haggling_true_oracle_focal.md"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# Concordia Haggling True Focal Oracle",
        "",
        "This table recomputes `oracle_focal`, the true upper reference for the reported Haggling metric `focal_score_mean`. It directly maximizes focal payoff under full information, rather than total buyer+seller surplus.",
        "",
        "| Config | oracle_focal | PACT+ | best non-oracle | oracle_joint focal | gap vs PACT+ |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {axis_label} | {oracle_focal_focal_score_mean:.3f} | {pact_plus_joint_proxy_focal_score_mean:.3f} | {best_non_oracle_method} {best_non_oracle_focal_score_mean:.3f} | {oracle_joint_focal_score_mean:.3f} | {gap_oracle_focal_minus_pact_plus:.3f} |".format(**row)
        )
    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            "- `oracle_focal` is never below any retained non-oracle method on these Haggling configs; it ties only where all relevant methods already attain the focal optimum.",
            "- The earlier `oracle_joint` focal values can be lower because that method optimizes total surplus, not focal payoff.",
            "- These values are deterministic, call-free recomputations from the compact Haggling action/payoff model in the current runner, with the historical JSONs used for non-oracle comparison rows.",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {csv_path}")
    print(f"wrote {md_path}")


def main() -> None:
    write_outputs(build_rows())


if __name__ == "__main__":
    main()