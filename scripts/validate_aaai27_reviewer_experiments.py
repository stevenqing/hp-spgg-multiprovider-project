"""Validate all outputs from the PACT AAAI-27 reviewer experiment spec."""

from __future__ import annotations

import csv
import math
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis" / "aaai27_review"


def rows(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def finite(row: dict[str, str], fields: tuple[str, ...]) -> bool:
    try:
        return all(math.isfinite(float(row[field])) for field in fields)
    except (KeyError, TypeError, ValueError):
        return False


def main() -> None:
    errors: list[str] = []

    er1 = rows("e_r1_noise_analytic_mixed.csv")
    er1_keys = {(r["backbone"], r["variant"], r["perturbation_type"], r["level"], r["seed"]) for r in er1}
    if len(er1) != 15_000 or len(er1_keys) != 15_000:
        errors.append(f"E-R1 expected 15000 unique rows, got rows={len(er1)} keys={len(er1_keys)}")
    if not all(finite(r, ("cumulative_regret_k20", "exact_type_mass_k20")) for r in er1):
        errors.append("E-R1 contains non-finite metrics")
    if Counter(r["seed"] for r in er1) != Counter({str(seed): 30 for seed in range(500)}):
        errors.append("E-R1 seed/grid coverage mismatch")

    loo = rows("e_r2_loo_analytic_mixed.csv")
    expansion = rows("e_r2_expansion_analytic_mixed.csv")
    if len(loo) != 80:
        errors.append(f"E-R2 LOO expected 80 rows, got {len(loo)}")
    completed_loo = [r for r in loo if r["status"].startswith("completed")]
    if len(completed_loo) != 40 or not all(
        finite(r, ("cumulative_regret_k20", "in_library_reference_regret_k20", "regret_degradation", "final_entropy"))
        for r in completed_loo
    ):
        errors.append("E-R2 completed LOO rows are incomplete/non-finite")
    if len(expansion) != 30 or not all(
        finite(r, ("cumulative_regret_k20", "exact_type_mass_k20", "final_entropy")) for r in expansion
    ):
        errors.append("E-R2 expansion expected 30 finite rows")

    er3 = rows("e_r3_menu_corruption.csv")
    er3_keys = {(r["p"], r["episode_id"]) for r in er3}
    p_counts = Counter(r["p"] for r in er3)
    if len(er3) != 480 or len(er3_keys) != 480:
        errors.append(f"E-R3 expected 480 unique rows, got rows={len(er3)} keys={len(er3_keys)}")
    if p_counts != Counter({"0.0": 120, "0.1": 120, "0.2": 120, "0.3": 120}):
        errors.append(f"E-R3 p-grid mismatch: {dict(p_counts)}")
    if not all(finite(r, ("focal_score", "corruption_updates", "corruption_events", "generation_calls", "generation_failures")) for r in er3):
        errors.append("E-R3 contains non-finite metrics")
    if sum(int(r["generation_failures"]) for r in er3) > 0:
        errors.append("E-R3 contains generation fallbacks")

    er4 = rows("e_r4_planner_concordia.csv")
    er4_keys = {(r["substrate"], r["config"], r["solver"]) for r in er4}
    if len(er4) != 54 or len(er4_keys) != 54:
        errors.append(f"E-R4 expected 54 unique rows, got rows={len(er4)} keys={len(er4_keys)}")
    if not all(finite(r, ("focal_payoff", "focal_payoff_sem", "walltime_ms", "walltime_ms_sem")) for r in er4):
        errors.append("E-R4 contains non-finite metrics")

    er0 = rows("e_r0_maassim_per_seed.csv")
    er0_keys = {(r["scenario"], r["variant"], r["seed"]) for r in er0}
    scenario_counts = Counter(r["scenario"] for r in er0)
    if len(er0) != 130 or len(er0_keys) != 130:
        errors.append(f"E-R0 expected 130 unique rows, got rows={len(er0)} keys={len(er0_keys)}")
    if scenario_counts != Counter({"normal_p2": 40, "stress_p5": 45, "conflict_p5": 45}):
        errors.append(f"E-R0 scenario grid mismatch: {dict(scenario_counts)}")
    if not all(finite(r, ("utility", "rejects", "wait", "served", "llm_calls", "cache_hits")) for r in er0):
        errors.append("E-R0 contains non-finite metrics")

    report = DATA / "PACT_AAAI27_REVIEWER_EXPERIMENTS.md"
    report_text = report.read_text(encoding="utf-8") if report.exists() else ""
    if not report_text or "missing/running" in report_text or "not completed" in report_text or "live suite running" in report_text:
        errors.append("Consolidated Markdown is missing or still reports incomplete outputs")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print(
        {
            "e_r1": len(er1),
            "e_r2_loo": len(loo),
            "e_r2_expansion": len(expansion),
            "e_r3": len(er3),
            "e_r4": len(er4),
            "e_r0": len(er0),
            "report": "complete",
        }
    )


if __name__ == "__main__":
    main()
