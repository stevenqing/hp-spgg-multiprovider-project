"""Summarize E-A through E-G and write a provenance manifest."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "analysis" / "aaai27_supplemental_experiments"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def main() -> None:
    ea_dir = ROOT / "analysis" / "e_a_matched_likelihood"
    ea_matched_dir = ea_dir / "matched_s10"
    eb_dir = ROOT / "analysis" / "e_b_iterated_concordia"
    ec_dir = ROOT / "analysis" / "e_c_sotopia_corrected"
    ed_dir = ROOT / "analysis" / "e_d_reward_locality_violation_combined"
    ee_dir = ROOT / "analysis" / "e_e_maassim_rq2"
    ef_dir = ROOT / "analysis" / "e_f_maassim_bonus"
    eg_dir = ROOT / "analysis" / "e_g_hp_spgg_component_ladder"

    ea_meta = read_json(ea_dir / "e_a_metadata.json")
    ea = read_csv(ea_dir / "e_a_historical_summary.csv")
    ea_matched_meta = read_json(ea_matched_dir / "e_a_matched_metadata.json")
    ea_matched = read_csv(ea_matched_dir / "e_a_matched_summary.csv")
    ea_status = "complete" if ea_matched_meta.get("status") == "complete" else ea_meta.get("result", "missing")
    eb = read_csv(eb_dir / "e_b_iterated_concordia_aggregate.csv")
    ec_meta = read_json(ec_dir / "e_c_metadata.json")
    ec_branch = read_csv(ec_dir / "e_c_branch_decision.csv")
    ec_corruption = read_csv(ec_dir / "e_c_menu_corruption_summary.csv")
    ec_component = read_csv(ec_dir / "e_c_component_summary.csv")
    ed = read_csv(ed_dir / "e_d_reward_locality_violation_summary.csv")
    ee = read_csv(ee_dir / "e_e_maassim_tracker_parity_summary.csv")
    ee_gaps = read_csv(ee_dir / "e_e_maassim_tracker_parity_gaps.csv")
    ef = read_csv(ef_dir / "e_f_maassim_bonus_summary.csv")
    ef_meta = read_json(ef_dir / "e_f_maassim_bonus_metadata.json")
    eg = read_csv(eg_dir / "e_g_hp_spgg_component_ladder_summary.csv")

    lines = [
        "# PACT AAAI-27 Supplemental Experiments",
        "",
        "## Status",
        "",
        "| Experiment | Status | Claim-safe disposition |",
        "|---|---|---|",
        f"| E-A matched likelihood | {ea_status} | Four-backbone, ten-common-environment-seed control shares each pinned tensor, type profile, uniform prior, no additional board state, and oracle; each method generates its own trajectory. |",
        "| E-B iterated Concordia | complete | Constructed exact-payoff diagnostic: plateau-vs-linear result; not native Concordia or backbone evidence. |",
        f"| E-C corrected SOTOPIA | {ec_meta.get('branch', 'missing')} | Corrected tracker updates; no score lead, so clean-boundary branch. |",
        "| E-D RL violation | complete | Posterior TV grows with coupling, but paired regret gaps remain null on this geometry. |",
        "| E-E MaaSSim tracker parity | complete | Joint marginals match factored tracking to numerical precision through n=4; independent sampling leaves one of nine nominal utility CIs non-covering. |",
        "| E-F MaaSSim frozen bonus | complete | Beta 0.25 changes 4/406 assignments; paired utility gap remains unresolved. |",
        "| E-G HP-SPGG component ladder | complete | One analytic substrate/metric: update and dispatch paired effects resolve; bonus and identity do not. |",
        "",
        "## E-A environment-matched control",
        "",
        "| model | PACT+ | PACT | Joint-PSRL | LLM-PSRL | best baseline | family ratio |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in ea_matched:
        lines.append(
            f"| {row['model']} | {float(row['pact_plus_regret_mean']):.3f} $\\pm$ {float(row['pact_plus_regret_sem']):.3f} | "
            f"{float(row['pact_regret_mean']):.3f} $\\pm$ {float(row['pact_regret_sem']):.3f} | "
            f"{float(row['joint_psrl_regret_mean']):.3f} $\\pm$ {float(row['joint_psrl_regret_sem']):.3f} | "
            f"{float(row['llm_psrl_regret_mean']):.3f} $\\pm$ {float(row['llm_psrl_regret_sem']):.3f} | "
            f"{row['best_llm_coordination_baseline']} {float(row['best_baseline_regret_mean']):.3f} | "
            f"{float(row['best_family_ratio']):.2f}x |"
        )
    if not ea_matched:
        lines.extend(["", "Matched rerun artifacts are not yet complete."])
    else:
        lines.extend(
            [
                "",
                "Environment seeds and type profiles are matched. Provider sampling seeds are unavailable, so accepted raw responses are content-hash cache-pinned rather than claimed to be pathwise provider-RNG matched.",
                f"Accepted response-cache entries: {int(ea_matched_meta.get('accepted_response_cache_entries', 0)):,}; strict external format repairs: {int(ea_matched_meta.get('external_parse_repairs', 0)):,}.",
            ]
        )

    lines.extend(["", "### Historical source audit (unmatched; retained for provenance)", "", "| model | PACT+ | best PACT family | best baseline | historical family ratio |", "|---|---:|---:|---:|---:|"])
    for row in ea:
        lines.append(
            f"| {row['model']} | {float(row['pact_plus_regret_mean']):.3f} | "
            f"{row['best_pact_family_method']} {float(row['best_pact_family_regret_mean']):.3f} | "
            f"{row['best_baseline']} {float(row['best_baseline_regret_mean']):.3f} | "
            f"{float(row['historical_best_family_ratio']):.2f}x |"
        )

    lines.extend(
        [
            "",
            "## E-B aggregate",
            "",
            "| scope | method | regret K=20 | late regret | paired gap vs PACT+ |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for row in eb:
        if row["method"] not in {"pact", "pact_plus", "joint_psrl_uniform", "psrl_notype"}:
            continue
        lines.append(
            f"| {row['scope']} | {row['method']} | {float(row['cumulative_regret_mean']):.3f} $\\pm$ {float(row['cumulative_regret_sem']):.3f} | "
            f"{float(row['late_instant_regret_mean']):.4f} | {float(row['paired_gap_vs_pact_plus_mean']):+.3f} $\\pm$ {float(row['paired_gap_vs_pact_plus_sem']):.3f} |"
        )

    lines.extend(
        [
            "",
            "## E-G HP-SPGG analytic component ladder",
            "",
            "| variant | cumulative regret | paired minus full | 95% CI | ratio vs full |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in eg:
        lines.append(
            f"| {row['variant']} | {float(row['cumulative_regret_mean']):.3f} $\\pm$ {float(row['cumulative_regret_sem']):.3f} | "
            f"{float(row['paired_minus_full_mean']):+.3f} | "
            f"[{float(row['ci95_low']):+.3f}, {float(row['ci95_high']):+.3f}] | "
            f"{float(row['ratio_vs_full']):.2f}x |"
        )

    lines.extend(["", "## E-C branch", "", "| family | corrected p=0 | delta vs retained best | branch |", "|---|---:|---:|---|"])
    for row in ec_branch:
        lines.append(
            f"| {row['family']} | {float(row['corrected_p0_mean']):.3f} $\\pm$ {float(row['corrected_p0_sem']):.3f} | "
            f"{float(row['delta_vs_historical_best']):+.3f} | {row['branch']} |"
        )
    lines.extend(["", f"Completed corruption levels: {sorted({float(row['p']) for row in ec_corruption})}."])
    if ec_component:
        lines.extend(["", "### Corrected component variants", "", "| family | variant | n | score | paired PACT-minus-variant |", "|---|---|---:|---:|---:|"])
        for row in ec_component:
            lines.append(
                f"| {row['family']} | {row['variant']} | {row['episodes']} | "
                f"{float(row['focal_score_mean']):.3f} $\\pm$ {float(row['focal_score_sem']):.3f} | "
                f"{float(row['pact_minus_variant_paired_mean']):+.3f} $\\pm$ {float(row['pact_minus_variant_paired_sem']):.3f} |"
            )

    lines.extend(["", "## E-D posterior coupling and regret", "", "| tier | alpha | PACT | Joint | paired gap | marginal TV |", "|---|---:|---:|---:|---:|---:|"])
    ed_lookup = {(row["model"], float(row["alpha"]), row["algorithm"]): row for row in ed}
    for model in ("analytic-mixed", "DeepSeek-V3.2-live"):
        for alpha in (0.0, 1.0, 2.0, 4.0):
            pact = ed_lookup[(model, alpha, "pact_factored")]
            joint = ed_lookup[(model, alpha, "joint_psrl_coupled")]
            lines.append(
                f"| {model} | {alpha:g} | {float(pact['cumulative_regret_mean']):.3f} $\\pm$ {float(pact['cumulative_regret_sem']):.3f} | "
                f"{float(joint['cumulative_regret_mean']):.3f} $\\pm$ {float(joint['cumulative_regret_sem']):.3f} | "
                f"{float(pact['regret_gap_vs_joint']):+.3f} $\\pm$ {float(pact['regret_gap_vs_joint_sem']):.3f} | "
                f"{float(pact['posterior_marginal_tv_vs_joint_mean']):.4f} $\\pm$ {float(pact['posterior_marginal_tv_vs_joint_sem']):.4f} |"
            )

    lines.extend(["", "## E-E MaaSSim tracker parity", "", "| n | lambda | factored utility | joint utility | joint - factored 95% CI | max TV | storage ratio |", "|---:|---:|---:|---:|---:|---:|---:|"])
    ee_lookup = {(int(row["n"]), float(row["lambda"]), row["tracker"]): row for row in ee}
    for gap in ee_gaps:
        n = int(gap["n"])
        strength = float(gap["lambda"])
        factored = ee_lookup[(n, strength, "factored")]
        joint = ee_lookup[(n, strength, "joint")]
        lines.append(
            f"| {n} | {strength:g} | {float(factored['utility_mean']):.3f} $\\pm$ {float(factored['utility_sem']):.3f} | "
            f"{float(joint['utility_mean']):.3f} $\\pm$ {float(joint['utility_sem']):.3f} | "
            f"{float(gap['joint_minus_factored_mean']):+.3f} [{float(gap['ci95_low']):+.3f}, {float(gap['ci95_high']):+.3f}] | "
            f"{float(gap['max_tv']):.2e} | {float(gap['storage_ratio']):,.1f}x |"
        )

    ef_lookup = {row["tracker"]: row for row in ef}
    ef_gap = ef_meta.get("paired_gap", {})
    lines.extend(
        [
            "",
            "## E-F MaaSSim frozen bonus",
            "",
            f"PACT utility: {float(ef_lookup['pact']['utility_mean']):.3f} $\\pm$ {float(ef_lookup['pact']['utility_sem']):.3f}; "
            f"PACT+ utility: {float(ef_lookup['pact_plus']['utility_mean']):.3f} $\\pm$ {float(ef_lookup['pact_plus']['utility_sem']):.3f}. "
            f"Paired PACT+ minus PACT: {float(ef_gap['pact_plus_minus_pact_mean']):+.3f} "
            f"[{float(ef_gap['ci95_low']):+.3f}, {float(ef_gap['ci95_high']):+.3f}] (95% CI); 4/406 assignments change.",
        ]
    )

    artifact_paths = [
        ea_dir / "e_a_metadata.json",
        ea_dir / "e_a_historical_per_seed_provenance.csv",
        ea_dir / "e_a_historical_summary.csv",
        eb_dir / "e_b_iterated_concordia_metadata.json",
        eb_dir / "e_b_iterated_concordia_per_seed.csv",
        eb_dir / "e_b_iterated_concordia_aggregate.csv",
        eb_dir / "e_b_iterated_concordia_figure_v2_long.csv",
        eb_dir / "e_b_iterated_concordia_figure_v2_stats.json",
        eb_dir / "e_b_iterated_concordia_rq2_rq3_all_data.md",
        ec_dir / "e_c_metadata.json",
        ec_dir / "e_c_posterior_proxy_per_turn.csv",
        ec_dir / "e_c_menu_corruption_summary.csv",
        ec_dir / "e_c_branch_decision.csv",
        ed_dir / "e_d_reward_locality_violation_metadata.json",
        ed_dir / "e_d_reward_locality_violation_per_seed.csv",
        ed_dir / "e_d_reward_locality_violation_summary.csv",
        ROOT / "analysis" / "e_d_reward_locality_violation" / "deepseek_live_3action_full.npy",
        ROOT / "analysis" / "e_d_reward_locality_violation" / "deepseek_live_3action_report.json",
        ROOT / "analysis" / "e_d_reward_locality_violation" / "deepseek_live_3action_cache.jsonl",
        ROOT / "arr_paper" / "figs" / "fig_e_b_iterated_concordia_v2.pdf",
        ROOT / "arr_paper" / "figs" / "fig_e_a_hp_spgg_matched.pdf",
        ROOT / "arr_paper" / "figs" / "fig_e_c_sotopia_corrected.pdf",
        ROOT / "arr_paper" / "figs" / "fig_e_d_reward_locality_violation.pdf",
        ROOT / "arr_paper" / "figs" / "fig_maassim_rq2_parity.pdf",
        ROOT / "arr_paper" / "figs" / "fig_maassim_combined_v22.pdf",
        ROOT / "arr_paper" / "figs" / "fig_e_g_hp_spgg_component_ladder.pdf",
        ROOT / "arr_paper" / "figs" / "fig_e_g_hp_spgg_component_trajectories.pdf",
        ROOT / "analysis" / "maassim_rq2_rq3_all_data.md",
        ROOT / "arr_paper" / "main.pdf",
        ROOT / "arr_paper" / "HARP_AAAI27.pdf",
    ]
    if (ec_dir / "e_c_component_summary.csv").exists():
        artifact_paths.append(ec_dir / "e_c_component_summary.csv")
    if (ROOT / "arr_paper" / "figs" / "fig_e_c_sotopia_component_corrected.pdf").exists():
        artifact_paths.append(ROOT / "arr_paper" / "figs" / "fig_e_c_sotopia_component_corrected.pdf")
    historical_root = ea_dir / "source_snapshot"
    if not historical_root.exists():
        legacy_roots = sorted(ea_dir.glob("source_git_*"))
        if len(legacy_roots) != 1:
            raise FileNotFoundError("expected one historical E-A source snapshot")
        historical_root = legacy_roots[0]
    artifact_paths.extend(sorted(historical_root.glob("*.npz")))
    artifact_paths.extend(
        sorted(
            path
            for path in ea_matched_dir.rglob("*")
            if path.is_file() and ".tmp" not in path.name
        )
    )
    artifact_paths.extend(sorted(path for path in ee_dir.rglob("*") if path.is_file()))
    artifact_paths.extend(sorted(path for path in ef_dir.rglob("*") if path.is_file()))
    artifact_paths.extend(sorted(path for path in eg_dir.rglob("*") if path.is_file()))
    artifact_paths.extend(
        sorted(
            path
            for path in (ROOT / "analysis" / "aaai27_review" / "e_r3_raw").glob("*.json")
            if "p0p25_" in path.name or "p0p5_" in path.name or path.name.startswith("component_")
        )
    )
    manifest = {
        "schema_version": "1.0",
        "experiment_status": {
            "E-A": ea_status,
            "E-B": "complete",
            "E-C": ec_meta.get("branch", "missing"),
            "E-D": "complete",
            "E-E": "complete",
            "E-F": "complete",
            "E-G": "complete",
        },
        "artifacts": [
            {"path": relative(path), "bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in artifact_paths
            if path.exists()
        ],
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "PACT_AAAI27_SUPPLEMENTAL_EXPERIMENTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["experiment_status"], "artifacts": len(manifest["artifacts"])}, indent=2))


if __name__ == "__main__":
    main()
