from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

PROPOSED = "hpsmg_plus_joint_proxy"
ORACLE = "oracle_joint"


def fmt(value: float) -> str:
    return f"{value:.4f}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize Concordia compact margins across result JSON files.")
    parser.add_argument("inputs", nargs="*", type=Path)
    parser.add_argument("--out", type=Path, default=Path("analysis/concordia_compact_margin_summary.md"))
    args = parser.parse_args()

    inputs = args.inputs or sorted(Path("analysis").glob("concordia_pub_coordination_compact_*mechanistic_joint_s*.json"))
    rows: list[dict[str, Any]] = []
    for path in inputs:
        payload = json.loads(path.read_text(encoding="utf-8"))
        summary = {row["method"]: row for row in payload.get("summary", [])}
        if PROPOSED not in summary:
            continue
        proposed = summary[PROPOSED]
        comparable = [
            row for method, row in summary.items()
            if method not in {PROPOSED, ORACLE} and not method.startswith("hpsmg_plus")
        ]
        if not comparable:
            continue
        best_baseline = max(comparable, key=lambda row: float(row["focal_score_mean"]))
        oracle = summary.get(ORACLE)
        proposed_mean = float(proposed["focal_score_mean"])
        baseline_mean = float(best_baseline["focal_score_mean"])
        oracle_mean = float(oracle["focal_score_mean"]) if oracle else float("nan")
        rows.append(
            {
                "config": payload.get("config", ""),
                "episodes": int(proposed["episodes"]),
                "proposed_mean": proposed_mean,
                "best_baseline": best_baseline["method"],
                "best_baseline_mean": baseline_mean,
                "margin": proposed_mean - baseline_mean,
                "oracle_mean": oracle_mean,
                "oracle_gap": oracle_mean - proposed_mean,
                "coordination": float(proposed["coordination_rate_mean"]),
                "source": path.as_posix(),
            }
        )
    rows.sort(key=lambda row: (-row["margin"], row["config"]))

    lines = [
        "# Concordia Compact Margin Summary",
        "",
        f"Proposed method: `{PROPOSED}`",
        "Best baseline excludes oracle and proposed/HPSMG ablations.",
        "",
        "| config | episodes | proposed_mean | best_baseline | best_baseline_mean | margin | oracle_mean | oracle_gap | proposed_coordination | source |",
        "|---|---:|---:|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {config} | {episodes} | {proposed_mean} | {best_baseline} | {best_baseline_mean} | {margin} | {oracle_mean} | {oracle_gap} | {coordination} | {source} |".format(
                config=row["config"],
                episodes=row["episodes"],
                proposed_mean=fmt(row["proposed_mean"]),
                best_baseline=row["best_baseline"],
                best_baseline_mean=fmt(row["best_baseline_mean"]),
                margin=fmt(row["margin"]),
                oracle_mean=fmt(row["oracle_mean"]),
                oracle_gap=fmt(row["oracle_gap"]),
                coordination=fmt(row["coordination"]),
                source=row["source"],
            )
        )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.out.as_posix())


if __name__ == "__main__":
    main()
