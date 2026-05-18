from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROMPT_ONLY_METHODS = ["llm_greedy", "llm_belief", "atom_tom1", "econ_bne"]


def joint_signature(row: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((str(player), str(choice)) for player, choice in row["joint_action"].items()))


def compact_action(row: dict[str, Any]) -> str:
    return "; ".join(
        f"{player.split()[0]}={choice}" for player, choice in row["joint_action"].items()
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnose action collapse in compact Concordia result JSON.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path, default=Path("analysis/concordia_compact_action_diagnostics.md"))
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    episodes = payload["episodes"]
    seeds = payload["seeds"]
    methods = payload["methods"]

    lines = [
        "# Concordia Compact Action Diagnostics",
        "",
        f"Source: `{args.input.as_posix()}`",
        f"Config: `{payload.get('config', '')}`",
        f"Model: `{payload.get('model', '')}`",
        f"Seeds: `{seeds}`",
        "",
        "## Prompt-Only Baseline Collapse",
        "",
        "This diagnostic checks whether the prompt-only baselines produced identical joint actions per seed. Identical actions necessarily produce identical payoff scores.",
        "",
        "| seed | prompt_only_unique_joint_actions | collapsed |",
        "|---:|---:|---|",
    ]

    collapsed_count = 0
    for seed in seeds:
        rows = [row for row in episodes if row["seed"] == seed and row["method"] in PROMPT_ONLY_METHODS]
        unique_count = len({joint_signature(row) for row in rows})
        collapsed = unique_count == 1
        collapsed_count += int(collapsed)
        lines.append(f"| {seed} | {unique_count} | {'yes' if collapsed else 'no'} |")

    lines.extend(
        [
            "",
            f"Collapsed seeds: `{collapsed_count}/{len(seeds)}`",
            "",
            "## Per-Seed Actions",
            "",
            "| seed | method | focal_score_mean | coordination_rate | joint_action |",
            "|---:|---|---:|---:|---|",
        ]
    )

    for seed in seeds:
        for method in methods:
            row = next(row for row in episodes if row["seed"] == seed and row["method"] == method)
            lines.append(
                "| {seed} | {method} | {focal_score_mean:.4f} | {coordination_rate:.4f} | {joint_action} |".format(
                    seed=seed,
                    method=method,
                    focal_score_mean=float(row["focal_score_mean"]),
                    coordination_rate=float(row["coordination_rate"]),
                    joint_action=compact_action(row),
                )
            )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.out.as_posix())


if __name__ == "__main__":
    main()