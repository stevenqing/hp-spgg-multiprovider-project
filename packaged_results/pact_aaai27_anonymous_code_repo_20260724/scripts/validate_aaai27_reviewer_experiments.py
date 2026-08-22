"""Validate all outputs from the PACT AAAI-27 reviewer experiment spec."""

from __future__ import annotations

import csv
import hashlib
import json
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def family_of(codename: str) -> str:
    parts = codename.split("_")
    while parts and parts[-1].isdigit():
        parts.pop()
    return "_".join(parts)


def canonical_er3_row(episode: dict[str, object], p: str, replicate: int) -> dict[str, object]:
    overall = episode.get("overall", {}) or {}
    scores = [
        float(value)
        for value in (overall.get("agent_1"), overall.get("agent_2"))
        if isinstance(value, (int, float))
    ] if isinstance(overall, dict) else []
    menu = episode.get("menu_corruption", {}) or {}
    generation = episode.get("generation_audit", {}) or {}
    codename = str(episode.get("codename", ""))
    return {
        "family": family_of(codename),
        "p": p,
        "episode_id": str(episode.get("episode_id", f"{episode.get('combo_pk', '')}_r{replicate}")),
        "focal_score": sum(scores) / len(scores) if scores else float("nan"),
        "combo_pk": str(episode.get("combo_pk", "")),
        "codename": codename,
        "replicate": replicate,
        "turns_completed": int(episode.get("turns_completed", 0) or 0),
        "corruption_updates": sum(
            int(item.get("updates", 0) or 0) for item in menu.values() if isinstance(item, dict)
        ) if isinstance(menu, dict) else 0,
        "corruption_events": sum(
            int(item.get("events", 0) or 0) for item in menu.values() if isinstance(item, dict)
        ) if isinstance(menu, dict) else 0,
        "generation_calls": sum(
            int(item.get("calls", 0) or 0) for item in generation.values() if isinstance(item, dict)
        ) if isinstance(generation, dict) else 0,
        "generation_failures": sum(
            int(item.get("failures", 0) or 0) for item in generation.values() if isinstance(item, dict)
        ) if isinstance(generation, dict) else 0,
    }


def main() -> None:
    errors: list[str] = []

    er1 = rows("e_r1_noise_analytic_mixed.csv")
    er1_keys = {(r["backbone"], r["variant"], r["perturbation_type"], r["level"], r["seed"]) for r in er1}
    perturbations = {
        "additive_log_noise": ("0.0", "0.1", "0.25", "0.5", "1.0", "2.0"),
        "temperature": ("0.5", "0.7", "1.0", "1.5", "2.0"),
        "top_k": ("1", "3", "5", "full"),
    }
    expected_er1 = {
        ("analytic_mixed", variant, perturbation, level, str(seed))
        for variant in ("pact", "pact_plus")
        for perturbation, levels in perturbations.items()
        for level in levels
        for seed in range(500)
    }
    if len(er1) != 15_000 or er1_keys != expected_er1:
        errors.append(f"E-R1 expected 15000 unique rows, got rows={len(er1)} keys={len(er1_keys)}")
    if not all(finite(r, ("cumulative_regret_k20", "exact_type_mass_k20")) for r in er1):
        errors.append("E-R1 contains non-finite metrics")
    if Counter(r["seed"] for r in er1) != Counter({str(seed): 30 for seed in range(500)}):
        errors.append("E-R1 seed/grid coverage mismatch")

    loo = rows("e_r2_loo_analytic_mixed.csv")
    expansion = rows("e_r2_expansion_analytic_mixed.csv")
    personas = ("altruistic_builder", "conditional_cooperator", "free_rider", "risk_averse_balancer")
    loo_keys = {(r["backbone"], r["excluded_persona"], r["variant"], r["seed"], r["status"]) for r in loo}
    expected_loo = {
        (
            "analytic_mixed" if variant in {"pact", "pact_plus"} else "gpt-5.4-nano-20260317",
            persona,
            variant,
            str(seed),
            "completed_offline_outcome_likelihood"
            if variant in {"pact", "pact_plus"}
            else "not_run_no_cached_trajectory_and_no_shared_discrete_library",
        )
        for persona in personas
        for variant in ("pact", "pact_plus", "llm_belief", "atom_tom1")
        for seed in range(5)
    }
    if len(loo) != 80 or loo_keys != expected_loo:
        errors.append(f"E-R2 LOO expected 80 rows, got {len(loo)}")
    completed_loo = [r for r in loo if r["status"].startswith("completed")]
    if len(completed_loo) != 40 or not all(
        finite(r, ("cumulative_regret_k20", "in_library_reference_regret_k20", "regret_degradation", "final_entropy"))
        for r in completed_loo
    ):
        errors.append("E-R2 completed LOO rows are incomplete/non-finite")
    expansion_keys = {(r["backbone"], r["distractor_count"], r["variant"], r["seed"]) for r in expansion}
    expected_expansion = {
        ("analytic_mixed", str(count), variant, str(seed))
        for count in (0, 2, 4)
        for variant in ("pact", "pact_plus")
        for seed in range(5)
    }
    if len(expansion) != 30 or expansion_keys != expected_expansion or not all(
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
        errors.append("E-R3 contains caught provider-call generation fallbacks")
    if any(int(r["corruption_events"]) > int(r["corruption_updates"]) for r in er3):
        errors.append("E-R3 corruption events exceed eligible updates")
    event_counts = Counter()
    for row in er3:
        event_counts[row["p"]] += int(row["corruption_events"])
    if event_counts["0.0"] != 0 or any(event_counts[p] <= 0 for p in ("0.1", "0.2", "0.3")):
        errors.append(f"E-R3 corruption-event grid is invalid: {dict(event_counts)}")
    raw_paths = sorted((DATA / "e_r3_raw").glob("p*_r*.json"))
    raw_keys: set[tuple[str, str]] = set()
    raw_cells: set[tuple[str, int]] = set()
    raw_rows_by_key: dict[tuple[str, str], dict[str, object]] = {}
    sotopia_data = ROOT / "external" / "sotopia_data_probe"
    manifest_path = ROOT / "config" / "aaai27_sotopia_input_manifest.csv"
    with manifest_path.open(newline="", encoding="utf-8") as handle:
        input_manifest = list(csv.DictReader(handle))
    input_hashes = {row["name"]: row["sha256"] for row in input_manifest}
    expected_input_names = {
        "benchmark_agents.json", "sotopia_episodes_v1_hf.jsonl", "sotopia_hard_cases_cache.json"
    }
    if set(input_hashes) != expected_input_names or len(input_manifest) != len(expected_input_names):
        errors.append("SOTOPIA input manifest has an invalid file grid")
    for item in input_manifest:
        path = ROOT / item["relative_path"]
        if path.exists() and (path.stat().st_size != int(item["bytes"]) or sha256(path) != item["sha256"]):
            errors.append(f"SOTOPIA input does not match manifest: {item['relative_path']}")
    hard_cases = json.loads((sotopia_data / "sotopia_hard_cases_cache.json").read_text(encoding="utf-8"))
    target_combo_ids = sorted(
        str(case["combo_pk"])
        for case in hard_cases
        if family_of(str(case["codename"])) in {"craigslist_bargains", "donate_funds", "revenge_plot"}
    )
    if len(raw_paths) != 16:
        errors.append(f"E-R3 expected 16 raw cells, got {len(raw_paths)}")
    for path in raw_paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            p = f"{float(payload['p']):.1f}"
            replicate = int(payload["replicate"])
            episodes = payload.get("episodes", [])
            failures = payload.get("failures", [])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"E-R3 invalid raw checkpoint {path.name}: {exc}")
            continue
        raw_cells.add((p, replicate))
        expected_signature = {
            "schema_version": 2,
            "baseline": "hpsmg_plus",
            "p": float(p),
            "replicate": replicate,
            "model": "gpt-5.4-nano-20260317",
            "evaluator_model": "gpt-5.4-nano-20260317",
            "turns": 6,
            "menu_corruption_seed": 2701 + replicate,
            "strategy_profile": "sotopia_tuned",
            "target_combo_ids": target_combo_ids,
            "input_sha256": input_hashes,
        }
        if payload.get("checkpoint_schema_version") != 2 or payload.get("run_signature") != expected_signature:
            errors.append(f"E-R3 raw cell {path.name} has a stale/mismatched run signature")
        if not isinstance(payload.get("attempt_history", []), list):
            errors.append(f"E-R3 raw cell {path.name} has invalid attempt history")
        combo_ids = [str(episode.get("combo_pk", "")) for episode in episodes]
        if len(episodes) != 30 or len(set(combo_ids)) != 30:
            errors.append(
                f"E-R3 raw cell {path.name} expected 30 unique episodes, "
                f"got rows={len(episodes)} combos={len(set(combo_ids))}"
            )
        if not payload.get("complete") or failures:
            errors.append(f"E-R3 raw cell {path.name} is incomplete or contains outer failures")
        for episode in episodes:
            audit = episode.get("generation_audit", {})
            menu = episode.get("menu_corruption", {})
            generation_failures = sum(
                int(item.get("failures", 0) or 0) for item in audit.values() if isinstance(item, dict)
            ) if isinstance(audit, dict) else 1
            generation_calls = sum(
                int(item.get("calls", 0) or 0) for item in audit.values() if isinstance(item, dict)
            ) if isinstance(audit, dict) else 0
            updates = sum(
                int(item.get("updates", 0) or 0) for item in menu.values() if isinstance(item, dict)
            ) if isinstance(menu, dict) else 0
            if not isinstance(audit, dict) or len(audit) != 2 or generation_failures or generation_calls <= 0 or updates <= 0:
                errors.append(
                    f"E-R3 raw episode {episode.get('episode_id', '')} has invalid "
                    f"generation/update audit ({generation_calls=}, {generation_failures=}, {updates=})"
                )
            canonical = canonical_er3_row(episode, p, replicate)
            key = (p, str(canonical["episode_id"]))
            raw_keys.add(key)
            raw_rows_by_key[key] = canonical
    expected_cells = {(p, replicate) for p in ("0.0", "0.1", "0.2", "0.3") for replicate in range(4)}
    if raw_cells != expected_cells:
        errors.append(f"E-R3 raw cell grid mismatch: {sorted(raw_cells)}")
    if raw_keys != er3_keys:
        errors.append(
            f"E-R3 raw/CSV key mismatch: raw_only={len(raw_keys - er3_keys)} "
            f"csv_only={len(er3_keys - raw_keys)}"
        )
    integer_fields = (
        "replicate",
        "turns_completed",
        "corruption_updates",
        "corruption_events",
        "generation_calls",
        "generation_failures",
    )
    string_fields = ("family", "p", "episode_id", "combo_pk", "codename")
    for row in er3:
        key = (row["p"], row["episode_id"])
        expected = raw_rows_by_key.get(key)
        if expected is None:
            continue
        if any(row[field] != str(expected[field]) for field in string_fields):
            errors.append(f"E-R3 raw/CSV string-field mismatch for {key}")
            continue
        try:
            if any(int(row[field]) != int(expected[field]) for field in integer_fields):
                errors.append(f"E-R3 raw/CSV audit-field mismatch for {key}")
            if not math.isclose(float(row["focal_score"]), float(expected["focal_score"]), rel_tol=0.0, abs_tol=1e-12):
                errors.append(f"E-R3 raw/CSV focal-score mismatch for {key}")
        except (TypeError, ValueError):
            errors.append(f"E-R3 raw/CSV parse failure for {key}")

    er4 = rows("e_r4_planner_concordia.csv")
    er4_keys = {(r["substrate"], r["config"], r["solver"]) for r in er4}
    expected_configs = {
        "pub_coordination": {
            "capetown_s100", "capetown_s30", "edinburgh_closures_s30", "edinburgh_s30",
            "edinburgh_tough_friendship_s30", "london_closures_s30", "london_mini_s30",
            "london_mini_s5", "london_s30",
        },
        "haggling": {
            "haggling_fruitville_gullible_s30", "haggling_fruitville_s30", "haggling_vegbrooke_s30",
            "haggling_vegbrooke_strange_game_s30", "haggling_vegbrooke_stubborn_s30",
        },
        "haggling_multi_item": {
            "haggling_multi_item_cumulative_score_s30", "haggling_multi_item_fruitville_gullible_s30",
            "haggling_multi_item_fruitville_multi_s30", "haggling_multi_item_vegbrooke_s30",
        },
    }
    expected_er4 = {
        (substrate, config, solver)
        for substrate, configs in expected_configs.items()
        for config in configs
        for solver in ("exact_enumeration", "greedy_br_1pass", "iterated_br_3pass")
    }
    if len(er4) != 54 or er4_keys != expected_er4:
        errors.append(f"E-R4 expected 54 unique rows, got rows={len(er4)} keys={len(er4_keys)}")
    if not all(finite(r, ("focal_payoff", "focal_payoff_sem", "walltime_ms", "walltime_ms_sem")) for r in er4):
        errors.append("E-R4 contains non-finite metrics")

    er0 = rows("e_r0_maassim_per_seed.csv")
    er0_keys = {(r["scenario"], r["variant"], r["seed"]) for r in er0}
    scenario_counts = Counter(r["scenario"] for r in er0)
    er0_policies = {
        "normal_p2": {"nearest", "random", "llm", "llm_belief", "llm_psrl", "atom_tom1", "econ_bne", "oracle"},
        "stress_p5": {"nearest", "random", "llm", "llm_belief", "llm_psrl", "atom_tom0", "atom_tom1", "econ_bne", "oracle"},
        "conflict_p5": {"nearest", "random", "llm", "llm_belief", "llm_psrl", "atom_tom0", "atom_tom1", "econ_bne", "oracle"},
    }
    expected_er0 = {
        (scenario, variant, str(seed))
        for scenario, variants in er0_policies.items()
        for variant in variants
        for seed in range(5)
    }
    if len(er0) != 130 or er0_keys != expected_er0:
        errors.append(f"E-R0 expected 130 unique rows, got rows={len(er0)} keys={len(er0_keys)}")
    if scenario_counts != Counter({"normal_p2": 40, "stress_p5": 45, "conflict_p5": 45}):
        errors.append(f"E-R0 scenario grid mismatch: {dict(scenario_counts)}")
    if not all(finite(r, ("utility", "rejects", "wait", "served", "llm_calls", "cache_hits")) for r in er0):
        errors.append("E-R0 contains non-finite metrics")

    report = DATA / "PACT_AAAI27_REVIEWER_EXPERIMENTS.md"
    report_text = report.read_text(encoding="utf-8") if report.exists() else ""
    if not report_text or "missing/running" in report_text or "not completed" in report_text or "live suite running" in report_text:
        errors.append("Consolidated Markdown is missing or still reports incomplete outputs")
    if "**Status:** 480/480 episode rows checkpointed (complete grid)." not in report_text:
        errors.append("Consolidated Markdown has a stale E-R3 completion count")
    delivery_rows = {
        "e_r1_noise_analytic_mixed.csv": len(er1),
        "e_r2_loo_analytic_mixed.csv": len(loo),
        "e_r2_expansion_analytic_mixed.csv": len(expansion),
        "e_r3_menu_corruption.csv": len(er3),
        "e_r4_planner_concordia.csv": len(er4),
        "e_r0_maassim_per_seed.csv": len(er0),
    }
    for filename, row_count in delivery_rows.items():
        path = DATA / filename
        expected_line = (
            f"| `analysis/aaai27_review/{filename}` | {row_count} rows | `{sha256(path)}` |"
        )
        if expected_line not in report_text:
            errors.append(f"Consolidated Markdown has stale rows/hash for {filename}")
    raw_hash_manifest = "\n".join(
        f"{path.relative_to(ROOT).as_posix()} {sha256(path)}" for path in raw_paths
    )
    raw_set_hash = hashlib.sha256(raw_hash_manifest.encode("utf-8")).hexdigest()
    expected_raw_fragment = (
        f"| `analysis/aaai27_review/e_r3_raw/*.json` | 480 checkpointed episodes in 16 files | "
        f"raw-set manifest `{raw_set_hash}`;"
    )
    if expected_raw_fragment not in report_text:
        errors.append("Consolidated Markdown has a stale E-R3 raw-set digest")

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
