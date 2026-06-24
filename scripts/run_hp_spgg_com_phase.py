"""Run the minimal HP-SPGG-COM layer-A phase diagram.

This script evaluates fixed communication policies on a cooperative HP-SPGG-style
type model. It writes a JSON summary and a flat CSV under analysis/hp_spgg_com.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from time import perf_counter

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_hpgg_com import (
    evaluate_closed_form,
    global_optimal_policy,
    make_model,
    named_policies,
    runtime_pair,
    validate_closed_form,
)


OUT_DIR = ROOT / "analysis" / "hp_spgg_com"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def policy_record(model, name, policy, opt_value: float) -> dict:
    value = evaluate_closed_form(model, policy)
    return {
        "strategy": name,
        "value": value,
        "suboptimality": opt_value - value,
        "expected_messages": float(np.sum(model.prior * policy.reveal)),
        "reveal_matrix": policy.reveal.astype(int).tolist(),
        "closed_exact_abs_error": validate_closed_form(model, policy),
    }


def run_phase() -> dict:
    rho_grid = [round(x, 2) for x in np.linspace(0.0, 1.0, 11)]
    cost_grid = [round(x, 2) for x in np.linspace(0.0, 0.5, 11)]
    rows: list[dict] = []
    for rho in rho_grid:
        for cost in cost_grid:
            model = make_model(n=2, type_count=2, identifiability=rho, comm_cost=cost, coupling=1.0)
            opt_value, opt_policy = global_optimal_policy(model)
            rows.append({
                "rho": rho,
                "comm_cost": cost,
                "strategy": "GLOBAL_OPT",
                "value": opt_value,
                "suboptimality": 0.0,
                "expected_messages": float(np.sum(model.prior * opt_policy.reveal)),
                "reveal_matrix": opt_policy.reveal.astype(int).tolist(),
                "closed_exact_abs_error": validate_closed_form(model, opt_policy),
            })
            for name, policy in named_policies(model).items():
                rec = policy_record(model, name, policy, opt_value)
                rec.update({"rho": rho, "comm_cost": cost})
                rows.append(rec)
    return {
        "setting": "HP-SPGG-COM minimal cooperative type communication benchmark",
        "rho_grid": rho_grid,
        "comm_cost_grid": cost_grid,
        "rows": rows,
    }


def run_runtime_probe() -> list[dict]:
    out: list[dict] = []
    for n in [2, 3, 4, 5, 6]:
        model = make_model(n=n, type_count=2, identifiability=0.35, comm_cost=0.15, coupling=1.0)
        policy = named_policies(model)["PACT_LOCAL"]
        for normalize_pairs in [True, False]:
            if n <= 4:
                rec = runtime_pair(model, policy, normalize_pairs=normalize_pairs)
                rec["exact_skipped"] = False
            else:
                start = perf_counter()
                value = evaluate_closed_form(model, policy, normalize_pairs=normalize_pairs)
                closed_seconds = perf_counter() - start
                rec = {
                    "n": n,
                    "type_count": model.type_count,
                    "closed_value": value,
                    "exact_value": None,
                    "abs_error": None,
                    "closed_seconds": closed_seconds,
                    "exact_seconds": None,
                    "speedup": None,
                    "exact_skipped": True,
                    "normalize_pairs": normalize_pairs,
                    "joint_type_states": int(model.type_count ** model.n),
                    "joint_type_signal_histories": int(model.type_count ** (model.n + model.n * (model.n - 1))),
                }
            out.append(rec)
    return out


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
    phase = run_phase()
    runtime = run_runtime_probe()
    phase["runtime_probe"] = runtime
    out_json = OUT_DIR / "hp_spgg_com_phase_summary.json"
    out_csv = OUT_DIR / "hp_spgg_com_phase_rows.csv"
    out_json.write_text(json.dumps(phase, indent=2), encoding="utf-8")
    write_csv(out_csv, phase["rows"])
    print(f"OK summary: {out_json}")
    print(f"OK rows: {out_csv}")
    for rec in runtime:
        print("runtime", rec)


if __name__ == "__main__":
    main()