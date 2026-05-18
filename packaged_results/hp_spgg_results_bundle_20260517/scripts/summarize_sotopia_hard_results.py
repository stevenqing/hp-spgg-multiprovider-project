from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path


ANALYSIS = Path("analysis")
OUT = ANALYSIS / "sotopia_hard_official_DeepSeek_V3_2_summary.md"
BASELINES = ["hpsmg_plus", "llm_belief", "llm_greedy", "atom_tom1", "econ_bne"]
DIMENSIONS = [
    "believability",
    "relationship",
    "knowledge",
    "secret",
    "social_rules",
    "financial_and_material_benefits",
    "goal",
]


def fmt(value: float) -> str:
    return f"{value:.4f}"


def table(headers: list[str], rows: list[list[object]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def load_result(baseline: str) -> tuple[Path, dict[str, object]] | None:
    path = ANALYSIS / f"sotopia_hard_official_DeepSeek_V3_2_{baseline}_all70.json"
    if not path.exists():
        return None
    return path, json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    summary_rows: list[list[object]] = []
    dimension_rows: list[list[object]] = []

    for baseline in BASELINES:
        loaded = load_result(baseline)
        if loaded is None:
            continue
        path, payload = loaded
        summary = payload.get("summary", {})
        agent_1 = summary.get("agent_1", {})
        agent_2 = summary.get("agent_2", {})
        case_count = payload.get("case_count", len(payload.get("episodes", [])))
        target_count = payload.get("target_case_count", 70)

        summary_rows.append(
            [
                baseline,
                case_count,
                target_count,
                payload.get("complete", False),
                fmt(float(summary.get("mean_overall", 0.0))),
                fmt(float(agent_1.get("overall_score", 0.0))),
                fmt(float(agent_2.get("overall_score", 0.0))),
                path.as_posix(),
            ]
        )
        for dimension in DIMENSIONS:
            agent_1_score = float(agent_1.get(dimension, 0.0))
            agent_2_score = float(agent_2.get(dimension, 0.0))
            dimension_rows.append(
                [
                    baseline,
                    dimension,
                    fmt(agent_1_score),
                    fmt(agent_2_score),
                    fmt((agent_1_score + agent_2_score) / 2.0),
                ]
            )

    summary_rows.sort(key=lambda row: float(row[4]), reverse=True)

    lines = [
        "# SOTOPIA-Hard Official Reconstruction Summary",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "Metric: SOTOPIA 7-dimension evaluator score; higher is better. Each baseline uses the same 70 reconstructed official SOTOPIA-Hard combinations, DeepSeek-V3.2 player calls, DeepSeek-V3.2 evaluator calls, and six-turn cap.",
        "",
        "## Overall",
        "",
        table(
            ["baseline", "cases", "target_cases", "complete", "mean_overall", "agent_1_overall", "agent_2_overall", "source"],
            summary_rows,
        ),
        "",
        "## Dimension Means",
        "",
        table(["baseline", "dimension", "agent_1", "agent_2", "mean_agents"], dimension_rows),
        "",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT.as_posix())


if __name__ == "__main__":
    main()