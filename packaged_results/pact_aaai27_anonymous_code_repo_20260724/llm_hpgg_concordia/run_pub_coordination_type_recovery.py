"""Pub-Coordination type-recovery benchmark.

Evaluates how well each method recovers each player's hidden favourite venue
(``person_preferences[player]``) from social context. Reuses the compact
Pub-Coordination sampler and method registry; replaces the planning-style
scoring (focal_score / coordination_rate) with type-recovery metrics
(top-1 accuracy, NLL, Brier).
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from .run_pub_coordination_compact import (
    build_case,
    ensure_concordia_examples_on_path,
    information_scope_for_method,
    load_config,
    run_method,
    type_recovery_metrics,
    venue_posterior_from_method,
)


DEFAULT_METHODS = [
    "llm_greedy",
    "llm_belief",
    "atom_tom1_mech",
    "econ_bne_mech",
    "hpsmg_plus_proxy",
    "hpsmg_plus_joint_proxy",
    "oracle_joint",
    "centralized_planner_llm",
    "chat_agent_llm",
]


def mean(values: Any) -> float:
    values = list(values)
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
                "top1_accuracy_mean": mean(r["top1_accuracy"] for r in method_rows),
                "nll_mean": mean(r["nll"] for r in method_rows),
                "brier_mean": mean(r["brier"] for r in method_rows),
                "uniform_baseline_nll": method_rows[0]["uniform_baseline_nll"],
            }
        )
    summary.sort(key=lambda r: (-r["top1_accuracy_mean"], r["nll_mean"], r["method"]))
    return summary


def write_summary_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Pub-Coordination Type Recovery",
        "",
        f"Config: `{payload['config']}`",
        f"Model: `{payload['model']}`",
        f"Seeds: `{payload['seeds']}`",
        "",
        "Hidden type per player = favourite venue in `person_preferences`.",
        "",
        "| method | episodes | top1_accuracy | NLL | Brier | uniform_NLL |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in payload["summary"]:
        lines.append(
            "| {method} | {episodes} | {top1_accuracy_mean:.4f} | {nll_mean:.4f} | {brier_mean:.4f} | {uniform_baseline_nll:.4f} |".format(
                **row
            )
        )
    if payload.get("information_audit"):
        lines.extend(
            [
                "",
                "## Information Fairness Audit",
                "",
                "| method | mode | all_preferences | full_relationship_matrix | known_payoff_model | privileged_oracle | comparable |",
                "|---|---|---|---|---|---|---|",
            ]
        )
        for method, scope in payload["information_audit"].items():
            lines.append(
                "| {method} | {mode} | {prefs} | {matrix} | {payoff} | {oracle} | {comparable} |".format(
                    method=method,
                    mode=scope["mode"],
                    prefs=str(scope["sees_all_person_preferences"]).lower(),
                    matrix=str(scope["sees_full_relationship_matrix"]).lower(),
                    payoff=str(scope["uses_known_payoff_model"]).lower(),
                    oracle=str(scope["uses_privileged_oracle_objective"]).lower(),
                    comparable=str(scope["comparable_as_baseline"]).lower(),
                )
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="london_mini")
    parser.add_argument("--model")
    parser.add_argument("--methods", nargs="+", default=DEFAULT_METHODS)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--seed-offset", type=int, default=0)
    parser.add_argument("--out", default="analysis/pub_coordination_type_recovery.json")
    parser.add_argument("--summary-out", default="analysis/pub_coordination_type_recovery.md")
    args = parser.parse_args()

    ensure_concordia_examples_on_path()
    config = load_config(args.config)
    seeds = [args.seed_offset + index for index in range(args.seeds)]

    rows: list[dict[str, Any]] = []
    t0 = time.time()
    total_jobs = len(seeds) * len(args.methods)
    job = 0
    for seed in seeds:
        case = build_case(config, seed)
        for method in args.methods:
            job += 1
            t_start = time.time()
            result = run_method(case, method, args.model)
            venue_post = venue_posterior_from_method(
                case, method, result["joint_action"], result.get("info", {})
            )
            metrics = type_recovery_metrics(case, venue_post)
            elapsed = time.time() - t_start
            row = {
                "method": method,
                "seed": seed,
                **metrics,
                "venue_posterior": venue_post,
                "true_preferences": dict(case["person_preferences"]),
                "joint_action": result["joint_action"],
                "elapsed_sec": elapsed,
            }
            rows.append(row)
            print(
                f"[{job}/{total_jobs}] seed={seed} method={method} "
                f"top1={metrics['top1_accuracy']:.2f} nll={metrics['nll']:.3f} "
                f"brier={metrics['brier']:.3f} elapsed={elapsed:.1f}s",
                flush=True,
            )

    payload = {
        "config": args.config,
        "model": args.model or "",
        "seeds": seeds,
        "methods": args.methods,
        "information_audit": {m: information_scope_for_method(m) for m in args.methods},
        "summary": summarize(rows),
        "episodes": rows,
        "total_elapsed_sec": time.time() - t0,
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if args.summary_out:
        write_summary_md(Path(args.summary_out), payload)
    print(f"wrote {out_path}")
    if args.summary_out:
        print(f"wrote {args.summary_out}")
    print(f"all {total_jobs} jobs done in {payload['total_elapsed_sec']:.1f}s")
    print()
    print("=== summary ===")
    for row in payload["summary"]:
        print(
            f"  {row['method']:<28s} top1={row['top1_accuracy_mean']:.3f}  "
            f"nll={row['nll_mean']:.3f}  brier={row['brier_mean']:.3f}"
        )


if __name__ == "__main__":
    main()
