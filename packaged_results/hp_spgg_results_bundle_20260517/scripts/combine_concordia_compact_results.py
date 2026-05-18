"""Combine compact Concordia Pub Coordination result JSON files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def mean(values: list[float]) -> float:
    return float(sum(values) / max(1, len(values)))


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_method: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_method.setdefault(row["method"], []).append(row)
    summary = []
    for method, method_rows in by_method.items():
        summary.append(
            {
                "method": method,
                "episodes": len(method_rows),
                "focal_score_mean": mean([float(row["focal_score_mean"]) for row in method_rows]),
                "focal_score_min_mean": mean([float(row["focal_score_min"]) for row in method_rows]),
                "coordination_rate_mean": mean([float(row["coordination_rate"]) for row in method_rows]),
                "valid_action_rate_mean": mean([float(row["valid_action_rate"]) for row in method_rows]),
            }
        )
    summary.sort(key=lambda row: (-row["focal_score_mean"], -row["coordination_rate_mean"], row["method"]))
    return summary


def write_summary_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Compact Concordia Pub Coordination Results",
        "",
        f"Config: `{payload['config']}`",
        f"Model: `{payload['model']}`",
        f"Seeds: `{payload['seeds']}`",
        "",
        "| method | episodes | focal_score_mean | focal_score_min_mean | coordination_rate_mean | valid_action_rate_mean |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in payload["summary"]:
        lines.append(
            "| {method} | {episodes} | {focal_score_mean:.4f} | {focal_score_min_mean:.4f} | {coordination_rate_mean:.4f} | {valid_action_rate_mean:.4f} |".format(
                **row
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+")
    parser.add_argument("--out", required=True)
    parser.add_argument("--summary-out", required=True)
    args = parser.parse_args()

    episodes: list[dict[str, Any]] = []
    seeds: set[int] = set()
    methods: list[str] = []
    config = ""
    model = ""
    for input_path in args.inputs:
        payload = json.loads(Path(input_path).read_text(encoding="utf-8"))
        config = config or payload.get("config", "")
        model = model or payload.get("model", "")
        for method in payload.get("methods", []):
            if method not in methods:
                methods.append(method)
        for row in payload.get("episodes", []):
            episodes.append(row)
            seeds.add(int(row["seed"]))

    combined = {
        "config": config,
        "model": model,
        "seeds": sorted(seeds),
        "methods": methods,
        "summary": summarize(episodes),
        "episodes": episodes,
        "sources": args.inputs,
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(combined, indent=2), encoding="utf-8")
    write_summary_md(Path(args.summary_out), combined)
    print(f"saved={out_path}")
    print(f"summary={args.summary_out}")


if __name__ == "__main__":
    main()