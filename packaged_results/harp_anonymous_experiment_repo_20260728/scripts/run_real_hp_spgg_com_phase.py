"""Run PACT-COM on the real HP-SPGG reward tensor/action grid."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_hpgg_com.real_hp_spgg_com import (  # noqa: E402
    enumerate_policies,
    evaluate_exact,
    evaluate_factorized,
    global_optimal_policy,
    make_real_model,
    named_policies,
    runtime_pair,
)


OUT_DIR = ROOT / "analysis" / "hp_spgg_com"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def expected_messages(model, policy) -> float:
    return float(np.sum(model.prior * policy.reveal))


def precompute_policy_table(model_zero_cost) -> list[dict]:
    rows = []
    for policy in enumerate_policies(model_zero_cost):
        rows.append(
            {
                "policy": policy,
                "reward_value": evaluate_factorized(model_zero_cost, policy),
                "expected_messages": expected_messages(model_zero_cost, policy),
            }
        )
    return rows


def value_from_precomputed(row: dict, cost: float) -> float:
    return float(row["reward_value"] - cost * row["expected_messages"])


def best_precomputed_policy(policy_table: list[dict], cost: float):
    best = max(policy_table, key=lambda row: value_from_precomputed(row, cost))
    return value_from_precomputed(best, cost), best["policy"], float(best["expected_messages"])


def precomputed_value_for_policy(model_zero_cost, policy, cost: float) -> tuple[float, float]:
    reward_value = evaluate_factorized(model_zero_cost, policy)
    messages = expected_messages(model_zero_cost, policy)
    return float(reward_value - cost * messages), float(messages)


def parse_float_list(raw: str) -> list[float]:
    return [float(x.strip()) for x in raw.split(",") if x.strip()]


def run(args: argparse.Namespace) -> dict:
    rows: list[dict] = []
    for rho in args.rhos:
        model_zero_cost = make_real_model(
            n=args.n,
            calibration=args.calibration,
            identifiability=rho,
            comm_cost=0.0,
            backend=args.backend,
            samples=args.samples,
            seed=args.seed,
            trap=args.trap,
        )
        policy_table = precompute_policy_table(model_zero_cost)
        for cost in args.costs:
            model = replace(model_zero_cost, comm_cost=cost)
            opt_value, opt_policy, opt_messages = best_precomputed_policy(policy_table, cost)
            rows.append(
                {
                    "rho": rho,
                    "comm_cost": cost,
                    "strategy": "GLOBAL_OPT",
                    "value": opt_value,
                    "suboptimality": 0.0,
                    "expected_messages": opt_messages,
                    "reveal_matrix": opt_policy.reveal.astype(int).tolist(),
                    "closed_exact_abs_error": None,
                }
            )
            for name, policy in named_policies(model).items():
                value, messages = precomputed_value_for_policy(model_zero_cost, policy, cost)
                rows.append(
                    {
                        "rho": rho,
                        "comm_cost": cost,
                        "strategy": name,
                        "value": value,
                        "suboptimality": opt_value - value,
                        "expected_messages": messages,
                        "reveal_matrix": policy.reveal.astype(int).tolist(),
                        "closed_exact_abs_error": None,
                    }
                )
    runtime_probe = []
    for n in args.runtime_ns:
        model = make_real_model(
            n=n,
            calibration=None,
            identifiability=0.35,
            comm_cost=0.15,
            backend=args.backend,
            samples=args.samples,
            seed=args.seed,
            trap=args.trap,
        )
        policy = named_policies(model)["PACT_LOCAL"]
        if n <= args.max_exact_runtime_n:
            runtime_probe.append(runtime_pair(model, policy))
        else:
            value = evaluate_factorized(model, policy)
            runtime_probe.append(
                {
                    "n": n,
                    "type_count": model.type_count,
                    "action_values": len(model.action_values),
                    "closed_value": value,
                    "exact_value": None,
                    "abs_error": None,
                    "closed_seconds": None,
                    "exact_seconds": None,
                    "speedup": None,
                    "exact_skipped": True,
                }
            )
    return {
        "setting": "real HP-SPGG reward tensor/action grid",
        "n": args.n,
        "calibration": args.calibration or "build_reward_tensor",
        "backend": args.backend,
        "samples": args.samples,
        "seed": args.seed,
        "trap": args.trap,
        "rho_grid": args.rhos,
        "comm_cost_grid": args.costs,
        "rows": rows,
        "runtime_probe": runtime_probe,
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    fieldnames = [
        "rho", "comm_cost", "strategy", "value", "suboptimality",
        "expected_messages", "closed_exact_abs_error", "reveal_matrix",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in fieldnames})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=2)
    parser.add_argument("--calibration", default=None)
    parser.add_argument("--backend", default="analytic")
    parser.add_argument("--samples", type=int, default=1)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--trap", action="store_true")
    parser.add_argument("--rhos", type=parse_float_list, default=parse_float_list("0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1"))
    parser.add_argument("--costs", type=parse_float_list, default=parse_float_list("0,0.05,0.1,0.15,0.2,0.25,0.3,0.35,0.4,0.45,0.5"))
    parser.add_argument("--runtime-ns", type=parse_float_list, default=parse_float_list("2,3"))
    parser.add_argument("--max-exact-runtime-n", type=int, default=3)
    parser.add_argument("--out-prefix", default="real_hp_spgg_com")
    args = parser.parse_args()
    args.runtime_ns = [int(x) for x in args.runtime_ns]
    payload = run(args)
    out_json = OUT_DIR / f"{args.out_prefix}_phase_summary.json"
    out_csv = OUT_DIR / f"{args.out_prefix}_phase_rows.csv"
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(out_csv, payload["rows"])
    print(f"OK summary: {out_json}")
    print(f"OK rows: {out_csv}")
    for rec in payload["runtime_probe"]:
        print("runtime", rec)


if __name__ == "__main__":
    main()