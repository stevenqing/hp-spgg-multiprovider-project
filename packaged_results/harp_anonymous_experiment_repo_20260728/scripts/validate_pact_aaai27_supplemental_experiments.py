"""Validate row counts, uniqueness, provenance, and artifacts for E-A..E-G."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]


def stored_path(raw: object) -> Path:
    """Resolve repository-relative metadata paths on Windows and POSIX."""
    path = Path(str(raw).replace("\\", "/"))
    return path if path.is_absolute() else ROOT / path


def rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def unique(records: list[dict[str, str]], fields: tuple[str, ...], name: str) -> None:
    keys = [tuple(record[field] for field in fields) for record in records]
    if len(keys) != len(set(keys)):
        raise AssertionError(f"{name}: duplicate keys for {fields}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-components", action="store_true")
    parser.add_argument("--require-matched-e-a", action="store_true")
    args = parser.parse_args()

    # E-A: 4 models * (5 native PACT+ + 6 external algorithms * 5 seeds).
    ea = rows(ROOT / "analysis" / "e_a_matched_likelihood" / "e_a_historical_per_seed_provenance.csv")
    if len(ea) != 140:
        raise AssertionError(f"E-A provenance rows={len(ea)}, expected 140")
    unique(ea, ("model", "algorithm", "seed_index"), "E-A")
    historical_root = ROOT / "analysis" / "e_a_matched_likelihood" / "source_snapshot"
    if not historical_root.exists():
        legacy_roots = sorted((ROOT / "analysis" / "e_a_matched_likelihood").glob("source_git_*"))
        if len(legacy_roots) != 1:
            raise FileNotFoundError("expected one historical E-A source snapshot")
        historical_root = legacy_roots[0]
    source_npz = sorted(historical_root.glob("*.npz"))
    if len(source_npz) != 8:
        raise AssertionError(f"E-A source NPZ count={len(source_npz)}, expected 8")
    for path in source_npz:
        with np.load(path, allow_pickle=True) as payload:
            if np.asarray(payload["regrets"]).shape[-2:] != (5, 20):
                raise AssertionError(f"unexpected E-A shape in {path}")

    matched_root = ROOT / "analysis" / "e_a_matched_likelihood" / "matched_s10"
    matched_path = matched_root / "e_a_matched_per_seed.csv"
    if args.require_matched_e_a and not matched_path.exists():
        raise FileNotFoundError(matched_path)
    matched_ea: list[dict[str, str]] = []
    if matched_path.exists():
        matched_ea = rows(matched_path)
        if len(matched_ea) != 400:
            raise AssertionError(f"E-A matched rows={len(matched_ea)}, expected 400")
        unique(matched_ea, ("model", "algorithm", "seed_index"), "E-A matched")
        for model in sorted({record["model"] for record in matched_ea}):
            model_rows = [record for record in matched_ea if record["model"] == model]
            for seed_index in range(10):
                seed_rows = [record for record in model_rows if int(record["seed_index"]) == seed_index]
                if len(seed_rows) != 10:
                    raise AssertionError(f"E-A {model} seed {seed_index} has {len(seed_rows)} algorithms")
                if len({record["rng_seed"] for record in seed_rows}) != 1:
                    raise AssertionError(f"E-A {model} seed {seed_index} RNG mismatch")
                if len({record["true_types"] for record in seed_rows}) != 1:
                    raise AssertionError(f"E-A {model} seed {seed_index} type-profile mismatch")
                if len({record["initial_state_id"] for record in seed_rows}) != 1:
                    raise AssertionError(f"E-A {model} seed {seed_index} initial-state mismatch")
                if any(record["matched_seed"].lower() != "true" for record in seed_rows):
                    raise AssertionError(f"E-A {model} seed {seed_index} is not marked matched")
        calibration_dir = matched_root / "calibration"
        reports = sorted(calibration_dir.glob("e_a_c19_fullgrid_*.report.json"))
        if len(reports) != 4:
            raise AssertionError(f"E-A matched calibration reports={len(reports)}, expected 4")
        for report_path in reports:
            report = json.loads(report_path.read_text(encoding="utf-8"))
            if report["live_profile_count"] != 125 or report["incomplete_required_cells"] != 0:
                raise AssertionError(f"Incomplete E-A calibration: {report_path}")
            if report["parse_failure_count"] != 0:
                raise AssertionError(f"E-A calibration parse failures: {report_path}")
            tensor_path = stored_path(report["out"])
            digest = hashlib.sha256(tensor_path.read_bytes()).hexdigest()
            if digest != report["tensor_sha256"]:
                raise AssertionError(f"E-A calibration hash mismatch: {tensor_path}")
            calibration = np.load(tensor_path, allow_pickle=True).item()
            reward_tensor = np.asarray(calibration["reward_tensor"], dtype=float)
            if reward_tensor.shape != (3, 4, 125):
                raise AssertionError(f"E-A calibration tensor shape={reward_tensor.shape}: {tensor_path}")
            if not np.all(np.isfinite(reward_tensor)) or np.any(reward_tensor < 0.0) or np.any(reward_tensor > 1.0):
                raise AssertionError(f"E-A calibration rewards leave [0,1]: {tensor_path}")
            cache_path = stored_path(report["cache"])
            cache_entries = [json.loads(line) for line in cache_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            cache_keys = [entry["key"] for entry in cache_entries]
            if len(cache_entries) != 1500 or len(set(cache_keys)) != 1500:
                raise AssertionError(f"E-A calibration cache is not complete: {cache_path}")
            if any(len(entry.get("scores", [])) != int(report["samples"]) for entry in cache_entries):
                raise AssertionError(f"E-A calibration cache contains incomplete score cells: {cache_path}")
        matched_meta = json.loads((matched_root / "e_a_matched_metadata.json").read_text(encoding="utf-8"))
        if matched_meta.get("status") != "complete" or not matched_meta.get("matched_seed"):
            raise AssertionError("E-A matched metadata is not complete")
        if "unavailable" not in str(matched_meta.get("provider_sampling_seed", "")):
            raise AssertionError("E-A provider sampling-seed limitation is not disclosed")
        if "Kimi-K2.6" not in matched_meta.get("provider_temperature_constraints", {}):
            raise AssertionError("E-A Kimi temperature constraint is not disclosed")
        if int(matched_meta.get("accepted_response_cache_entries", 0)) <= 6000:
            raise AssertionError("E-A accepted response-cache accounting is incomplete")
        if int(matched_meta.get("external_parse_repairs", -1)) < 0:
            raise AssertionError("E-A external parse-repair accounting is missing")
        if set(matched_meta.get("calibration_judge_cache_cells", {}).values()) != {1500}:
            raise AssertionError("E-A per-backbone calibration cache accounting is incomplete")
        per_seed_npz = sorted((matched_root / "per_seed").glob("*/*.npz"))
        if len(per_seed_npz) != 400:
            raise AssertionError(f"E-A per-seed NPZ count={len(per_seed_npz)}, expected 400")
        for path in per_seed_npz:
            with np.load(path, allow_pickle=True) as payload:
                if np.asarray(payload["regrets"]).shape != (20,):
                    raise AssertionError(f"E-A per-seed regret shape is not K=20: {path}")
                if np.asarray(payload["true_types"]).shape != (3,):
                    raise AssertionError(f"E-A per-seed type profile shape is not n=3: {path}")
                if not bool(payload["matched_seed"]):
                    raise AssertionError(f"E-A per-seed file is not marked matched: {path}")
                if int(payload["rng_seed"]) != int(payload["expected_rng_seed"]):
                    raise AssertionError(f"E-A per-seed RNG provenance mismatch: {path}")

    # E-B: 6 configs * 8 methods * 5 seeds * 20 episodes.
    eb = rows(ROOT / "analysis" / "e_b_iterated_concordia" / "e_b_iterated_concordia_per_seed.csv")
    if len(eb) != 4800:
        raise AssertionError(f"E-B rows={len(eb)}, expected 4800")
    unique(eb, ("config_id", "method", "seed", "episode"), "E-B")
    eb_meta = json.loads((ROOT / "analysis" / "e_b_iterated_concordia" / "e_b_iterated_concordia_metadata.json").read_text(encoding="utf-8"))
    if eb_meta["selection_seeds"] != "0..4" or eb_meta["report_seed_range"] != "1000..1004":
        raise AssertionError("E-B selection/report seeds are not the disjoint planned sets")
    eb_figure = rows(ROOT / "analysis" / "e_b_iterated_concordia" / "e_b_iterated_concordia_figure_v2_long.csv")
    if len(eb_figure) != 4800 or list(eb_figure[0]) != ["method", "config", "seed", "episode", "cum_regret"]:
        raise AssertionError("E-B v2 normalized long table is incomplete or has the wrong schema")
    unique(eb_figure, ("method", "config", "seed", "episode"), "E-B v2 figure")
    eb_figure_stats = json.loads((ROOT / "analysis" / "e_b_iterated_concordia" / "e_b_iterated_concordia_figure_v2_stats.json").read_text(encoding="utf-8"))
    if not eb_figure_stats["panel_a"].get("all_episodes_cover_zero"):
        raise AssertionError("E-B v2 panel-a Student-t intervals do not all cover zero")
    if int(eb_figure_stats["panel_b"].get("mean_crossover_episode", -1)) != 6:
        raise AssertionError("E-B v2 update-value crossover changed")
    eb_all_data = ROOT / "analysis" / "e_b_iterated_concordia" / "e_b_iterated_concordia_rq2_rq3_all_data.md"
    if not eb_all_data.is_file() or eb_all_data.stat().st_size < 300_000:
        raise AssertionError("E-B v2 complete-data Markdown is missing or unexpectedly small")
    eb_all_data_text = eb_all_data.read_text(encoding="utf-8")
    if "## Complete normalized long table (all 4,800 rows)" not in eb_all_data_text:
        raise AssertionError("E-B v2 complete-data Markdown does not declare the full long table")

    # E-C: 6 p levels * 120 episode rows.
    ec = rows(ROOT / "analysis" / "aaai27_review" / "e_r3_menu_corruption.csv")
    if len(ec) != 720:
        raise AssertionError(f"E-C corruption rows={len(ec)}, expected 720")
    unique(ec, ("p", "episode_id"), "E-C corruption")
    levels = sorted({float(record["p"]) for record in ec})
    if levels != [0.0, 0.1, 0.2, 0.25, 0.3, 0.5]:
        raise AssertionError(f"E-C levels={levels}")
    if any(int(record["generation_failures"]) != 0 for record in ec):
        raise AssertionError("E-C accepted grid contains provider generation fallbacks")

    for baseline in ("surrogate_only", "naive_belief"):
        path = ROOT / "analysis" / "aaai27_review" / f"e_c_component_{baseline}.csv"
        if args.require_components and not path.exists():
            raise FileNotFoundError(path)
        if path.exists():
            component = rows(path)
            if args.require_components and len(component) != 120:
                raise AssertionError(f"E-C {baseline} rows={len(component)}, expected 120")
            unique(component, ("episode_id",), f"E-C {baseline}")
            if any(int(record["generation_failures"]) != 0 for record in component):
                raise AssertionError(f"E-C {baseline} contains accepted generation fallbacks")

    # E-D: 2 tiers * 6 alpha * 3 methods * 10 seeds * 100 episodes.
    ed = rows(ROOT / "analysis" / "e_d_reward_locality_violation_combined" / "e_d_reward_locality_violation_per_seed.csv")
    if len(ed) != 36000:
        raise AssertionError(f"E-D rows={len(ed)}, expected 36000")
    unique(ed, ("model", "alpha", "algorithm", "seed", "episode"), "E-D")
    ed_summary = rows(ROOT / "analysis" / "e_d_reward_locality_violation_combined" / "e_d_reward_locality_violation_summary.csv")
    for model in ("analytic-mixed", "DeepSeek-V3.2-live"):
        anchor = next(
            row
            for row in ed_summary
            if row["model"] == model
            and row["algorithm"] == "pact_factored"
            and float(row["alpha"]) == 0.0
        )
        if abs(float(anchor["regret_gap_vs_joint"])) > 1e-12:
            raise AssertionError(f"E-D alpha=0 is not pathwise matched for {model}")
        if float(anchor["posterior_marginal_tv_vs_joint_mean"]) > 1e-10:
            raise AssertionError(f"E-D alpha=0 posterior does not decouple for {model}")
    ed_meta = json.loads((ROOT / "analysis" / "e_d_reward_locality_violation_combined" / "e_d_reward_locality_violation_metadata.json").read_text(encoding="utf-8"))
    if not ed_meta.get("reward_range_preserved"):
        raise AssertionError("E-D did not record bounded-reward preservation")
    live_dir = ROOT / "analysis" / "e_d_reward_locality_violation"
    live_report = json.loads((live_dir / "deepseek_live_3action_report.json").read_text(encoding="utf-8"))
    if live_report["live_profile_count"] != 27 or live_report["parse_failure_count"] != 0:
        raise AssertionError(f"unexpected E-D live calibration report: {live_report}")
    cache_rows = [
        json.loads(line)
        for line in (live_dir / "deepseek_live_3action_cache.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len({row["key"] for row in cache_rows}) != 324:
        raise AssertionError("E-D live calibration does not contain 324 unique complete cells")

    # E-E: 9 required joint/factored cells * 10 seeds plus 6 factored-only cells * 10 seeds.
    ee_root = ROOT / "analysis" / "e_e_maassim_rq2"
    ee = rows(ee_root / "e_e_maassim_tracker_parity.csv")
    if len(ee) != 240:
        raise AssertionError(f"E-E rows={len(ee)}, expected 240")
    unique(ee, ("seed", "n", "lambda", "tracker"), "E-E")
    ee_gaps = rows(ee_root / "e_e_maassim_tracker_parity_gaps.csv")
    if len(ee_gaps) != 9:
        raise AssertionError(f"E-E paired-gap rows={len(ee_gaps)}, expected 9")
    ee_max_tv = max(float(row["max_tv"]) for row in ee_gaps)
    if ee_max_tv >= 1e-10:
        raise AssertionError(f"E-E max marginal TV={ee_max_tv} exceeds 1e-10")
    ee_meta = json.loads((ee_root / "e_e_maassim_tracker_parity_metadata.json").read_text(encoding="utf-8"))
    if ee_meta.get("status") != "complete" or ee_meta.get("provider_calls") != 0:
        raise AssertionError("E-E metadata is not a complete zero-provider run")
    if ee_meta.get("source_scheme") != "scheme i: closed-loop regeneration by fleet size":
        raise AssertionError("E-E did not use the preferred self-consistent sub-fleet scheme")

    # E-F: 2 trackers * 10 saved-state environment indices.
    ef_root = ROOT / "analysis" / "e_f_maassim_bonus"
    ef = rows(ef_root / "e_f_maassim_bonus_per_seed.csv")
    if len(ef) != 20:
        raise AssertionError(f"E-F rows={len(ef)}, expected 20")
    unique(ef, ("seed", "tracker"), "E-F")
    ef_meta = json.loads((ef_root / "e_f_maassim_bonus_metadata.json").read_text(encoding="utf-8"))
    if ef_meta.get("status") != "complete" or ef_meta.get("provider_calls") != 0 or ef_meta.get("beta") != 0.25:
        raise AssertionError("E-F metadata is not a complete zero-provider frozen-beta run")
    ef_changed = sum(int(row["assignment_changes_vs_pact"]) for row in ef if row["tracker"] == "pact_plus")
    if ef_changed != 4:
        raise AssertionError(f"E-F assignment changes={ef_changed}, expected 4")
    ef_gap = ef_meta["paired_gap"]
    if not (float(ef_gap["ci95_low"]) <= 0.0 <= float(ef_gap["ci95_high"])):
        raise AssertionError("E-F paired utility gap is unexpectedly resolved")

    # E-G: 5 component variants * 10 common environments * 20 episodes.
    eg_root = ROOT / "analysis" / "e_g_hp_spgg_component_ladder"
    eg = rows(eg_root / "e_g_hp_spgg_component_ladder_long.csv")
    if len(eg) != 1000:
        raise AssertionError(f"E-G rows={len(eg)}, expected 1000")
    unique(eg, ("variant", "seed", "episode"), "E-G")
    if {row["variant"] for row in eg} != {"full", "minus_bonus", "minus_update", "minus_identity", "minus_dispatch"}:
        raise AssertionError("E-G component grid changed")
    if {int(row["seed"]) for row in eg} != set(range(10)) or {int(row["episode"]) for row in eg} != set(range(1, 21)):
        raise AssertionError("E-G seed/episode grid changed")
    eg_summary = rows(eg_root / "e_g_hp_spgg_component_ladder_summary.csv")
    if len(eg_summary) != 5:
        raise AssertionError(f"E-G summary rows={len(eg_summary)}, expected 5")
    eg_means = {row["variant"]: float(row["cumulative_regret_mean"]) for row in eg_summary}
    expected_eg_means = {
        "full": 0.014803811559212865,
        "minus_bonus": 0.015594443719659812,
        "minus_update": 0.6752610309174041,
        "minus_identity": 0.7000513484402628,
        "minus_dispatch": 6.3236933621419436,
    }
    if any(abs(eg_means[key] - value) > 1e-10 for key, value in expected_eg_means.items()):
        raise AssertionError(f"E-G canonical means changed: {eg_means}")
    eg_meta = json.loads((eg_root / "e_g_hp_spgg_component_ladder_metadata.json").read_text(encoding="utf-8"))
    if eg_meta.get("status") != "complete" or eg_meta.get("provider_calls") != 0:
        raise AssertionError("E-G metadata is not a complete zero-provider run")

    required = [
        ROOT / "arr_paper" / "figs" / "fig_e_a_hp_spgg_matched.pdf",
        ROOT / "arr_paper" / "figs" / "fig_e_b_iterated_concordia_v2.pdf",
        ROOT / "arr_paper" / "figs" / "fig_e_c_sotopia_corrected.pdf",
        ROOT / "arr_paper" / "figs" / "fig_e_d_reward_locality_violation.pdf",
        ROOT / "arr_paper" / "figs" / "fig_maassim_rq2_parity.pdf",
        ROOT / "arr_paper" / "figs" / "fig_maassim_combined_v22.pdf",
        ROOT / "arr_paper" / "figs" / "fig_e_g_hp_spgg_component_ladder.pdf",
        ROOT / "arr_paper" / "figs" / "fig_e_g_hp_spgg_component_trajectories.pdf",
        ROOT / "arr_paper" / "main.pdf",
    ]
    for path in required:
        if not path.exists() or path.stat().st_size <= 0:
            raise AssertionError(f"missing/empty artifact: {path}")

    print(
        json.dumps(
            {
                "E-A_rows": len(ea),
                "E-A_matched_rows": len(matched_ea),
                "E-B_rows": len(eb),
                "E-B_figure_rows": len(eb_figure),
                "E-C_rows": len(ec),
                "E-C_levels": levels,
                "E-D_rows": len(ed),
                "E-E_rows": len(ee),
                "E-E_gap_rows": len(ee_gaps),
                "E-E_max_marginal_tv": ee_max_tv,
                "E-F_rows": len(ef),
                "E-F_assignment_changes": ef_changed,
                "E-G_rows": len(eg),
                "E-G_summary_rows": len(eg_summary),
                "E-G_means": eg_means,
                "components_required": args.require_components,
                "status": "ok",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
