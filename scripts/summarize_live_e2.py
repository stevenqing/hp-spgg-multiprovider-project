"""Summarize live calibration audit and E2 sanity outputs."""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_hpgg.environment import load_calibration, tid_min_gap


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize live HP-SPGG calibration and E2 results.")
    parser.add_argument("--calibration", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--audit", required=True)
    parser.add_argument("--results", nargs="+", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args()

    calibration = load_calibration(args.calibration)
    reward_tensor = np.asarray(calibration["reward_tensor"], dtype=float)
    report = load_json(Path(args.report))
    audit_text = read_text(Path(args.audit))
    result_paths = expand_paths(args.results)
    result_summaries = [summarize_npz(path) for path in result_paths]
    best_result = choose_best_result(result_summaries)

    summary = {
        "calibration": args.calibration,
        "report": args.report,
        "audit": args.audit,
        "tid_min_gap": float(tid_min_gap(reward_tensor)),
        "new_live_cells": report.get("new_live_cells"),
        "cached_cells_loaded": report.get("cached_cells_loaded"),
        "skipped_cached_cells": report.get("skipped_cached_cells"),
        "parse_failure_count": report.get("parse_failure_count"),
        "results": result_summaries,
        "best_result": best_result,
    }

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(render_markdown(summary, audit_text), encoding="utf-8")
    print(f"summary_json={out_json}")
    print(f"summary_md={out_md}")
    if best_result:
        print(
            "best="
            f"{best_result['path']} beta={best_result['beta']} "
            f"hpsmg_plus={best_result['final_regret'].get('hpsmg_plus')} "
            f"hpsmg={best_result['final_regret'].get('hpsmg')}"
        )


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def expand_paths(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            paths.extend(Path(match) for match in matches)
        else:
            paths.append(Path(pattern))
    return sorted(path for path in paths if path.exists())


def summarize_npz(path: Path) -> dict[str, object]:
    data = np.load(path, allow_pickle=True)
    algorithms = [str(value) for value in data["algorithms"]]
    cumulative_regret = np.asarray(data["cumulative_regret"], dtype=float)
    final_means = cumulative_regret[:, :, -1].mean(axis=1)
    final_regret = {algorithm: round(float(value), 6) for algorithm, value in zip(algorithms, final_means)}
    return {
        "path": str(path),
        "beta": float(data["beta"]),
        "K": int(data["K"]),
        "seeds": int(data["seeds"]),
        "final_regret": final_regret,
    }


def choose_best_result(results: list[dict[str, object]]) -> dict[str, object] | None:
    candidates = [result for result in results if "hpsmg_plus" in result["final_regret"]]
    if not candidates:
        return None
    return min(candidates, key=lambda result: result["final_regret"]["hpsmg_plus"])


def render_markdown(summary: dict[str, object], audit_text: str) -> str:
    lines = ["# Live Calibration Overnight Summary", ""]
    lines.append(f"calibration: `{summary['calibration']}`")
    lines.append(f"tid_min_gap: `{summary['tid_min_gap']:.4f}`")
    lines.append(f"new_live_cells: `{summary.get('new_live_cells')}`")
    lines.append(f"parse_failure_count: `{summary.get('parse_failure_count')}`")
    lines.append("")
    lines.append("## E2 beta sweep")
    lines.append("")
    algorithms = sorted({algorithm for result in summary["results"] for algorithm in result["final_regret"].keys()})
    preferred_order = [
        "oracle",
        "hpsmg_plus",
        "hpsmg",
        "joint_psrl",
        "map_greedy",
        "psrl_notype",
        "iql_independent_actions",
        "iql",
        "joint_profile_iql",
        "random",
    ]
    algorithms = [algorithm for algorithm in preferred_order if algorithm in algorithms] + [
        algorithm for algorithm in algorithms if algorithm not in preferred_order
    ]
    lines.append("| beta | " + " | ".join(algorithms) + " | file |")
    lines.append("| ---: | " + " | ".join(["---:"] * len(algorithms)) + " | --- |")
    for result in summary["results"]:
        final = result["final_regret"]
        values = " | ".join(str(final.get(algorithm, "")) for algorithm in algorithms)
        lines.append(f"| {result['beta']} | {values} | `{result['path']}` |")
    best = summary.get("best_result")
    if best:
        lines.extend(["", "## Best hpsmg_plus", ""])
        lines.append(f"file: `{best['path']}`")
        lines.append(f"beta: `{best['beta']}`")
        lines.append(f"final_regret: `{best['final_regret']}`")
    if audit_text:
        lines.extend(["", "## Audit", "", "```text", audit_text.rstrip(), "```"])
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()