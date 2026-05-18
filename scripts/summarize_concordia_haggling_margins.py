from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

PROPOSED = "hpsmg_plus_joint_proxy"
ORACLE = "oracle_joint"


def fmt(value: float) -> str:
    return f"{value:.4f}"


def score_key(row: dict[str, Any]) -> tuple[float, float, float]:
    return (
        float(row.get("nash_product_mean", 0.0)),
        float(row.get("focal_score_min_mean", 0.0)),
        float(row.get("focal_score_mean", 0.0)),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize Concordia compact haggling margins.")
    parser.add_argument("inputs", nargs="*", type=Path)
    parser.add_argument("--out", type=Path, default=Path("analysis/concordia_haggling_margin_summary.md"))
    args = parser.parse_args()

    inputs = args.inputs or sorted(Path("analysis").glob("concordia_haggling*_compact_*_s30.json"))
    rows: list[dict[str, Any]] = []
    for path in inputs:
        if "smoke" in path.name:
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        summary = {row["method"]: row for row in payload.get("summary", [])}
        if PROPOSED not in summary:
            continue
        comparable = [
            row for method, row in summary.items()
            if method not in {PROPOSED, ORACLE} and not method.startswith("hpsmg_plus")
        ]
        if not comparable:
            continue
        proposed = summary[PROPOSED]
        best_baseline = max(comparable, key=score_key)
        oracle = summary.get(ORACLE)
        proposed_nash = float(proposed.get("nash_product_mean", 0.0))
        baseline_nash = float(best_baseline.get("nash_product_mean", 0.0))
        proposed_min = float(proposed.get("focal_score_min_mean", 0.0))
        baseline_min = float(best_baseline.get("focal_score_min_mean", 0.0))
        proposed_focal = float(proposed.get("focal_score_mean", 0.0))
        baseline_focal = float(best_baseline.get("focal_score_mean", 0.0))
        rows.append(
            {
                "domain": payload.get("domain", ""),
                "config": payload.get("config", ""),
                "episodes": int(proposed["episodes"]),
                "proposed_nash": proposed_nash,
                "best_baseline": best_baseline["method"],
                "baseline_nash": baseline_nash,
                "nash_margin": proposed_nash - baseline_nash,
                "proposed_min": proposed_min,
                "baseline_min": baseline_min,
                "min_margin": proposed_min - baseline_min,
                "proposed_focal": proposed_focal,
                "baseline_focal": baseline_focal,
                "focal_margin": proposed_focal - baseline_focal,
                "oracle_focal": float(oracle.get("focal_score_mean", 0.0)) if oracle else float("nan"),
                "source": path.as_posix(),
            }
        )
    rows.sort(key=lambda row: (-row["nash_margin"], -row["min_margin"], row["domain"], row["config"]))

    lines = [
        "# Concordia Compact Haggling Margin Summary",
        "",
        f"Proposed method: `{PROPOSED}`",
        "Best baseline excludes oracle and proposed/HPSMG ablations. Primary ordering uses Nash product margin, then focal-min margin.",
        "",
        "| domain | config | episodes | proposed_nash | best_baseline | baseline_nash | nash_margin | proposed_min | baseline_min | min_margin | proposed_focal | baseline_focal | focal_margin | source |",
        "|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {domain} | {config} | {episodes} | {proposed_nash} | {best_baseline} | {baseline_nash} | {nash_margin} | {proposed_min} | {baseline_min} | {min_margin} | {proposed_focal} | {baseline_focal} | {focal_margin} | {source} |".format(
                domain=row["domain"],
                config=row["config"],
                episodes=row["episodes"],
                proposed_nash=fmt(row["proposed_nash"]),
                best_baseline=row["best_baseline"],
                baseline_nash=fmt(row["baseline_nash"]),
                nash_margin=fmt(row["nash_margin"]),
                proposed_min=fmt(row["proposed_min"]),
                baseline_min=fmt(row["baseline_min"]),
                min_margin=fmt(row["min_margin"]),
                proposed_focal=fmt(row["proposed_focal"]),
                baseline_focal=fmt(row["baseline_focal"]),
                focal_margin=fmt(row["focal_margin"]),
                source=row["source"],
            )
        )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.out.as_posix())


if __name__ == "__main__":
    main()
