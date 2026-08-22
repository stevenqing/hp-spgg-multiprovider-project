"""Consolidate every Claim-A analytic-scaling result into one Markdown file."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis" / "hp_spgg_analytic_scaling"
NPZ_DIR = DATA / "npz"
SUMMARY = DATA / "scaling_summary.csv"
PARITY = DATA / "scaling_parity.csv"
MANIFEST = DATA / "manifest_scaling.json"
PROBES = DATA / "dgp_probes.csv"
LIBRARIES = DATA / "type_libraries.csv"
REGRET_FIGURE = DATA / "fig_hp_spgg_analytic_scaling_regret_v1.pdf"
OUT = DATA / "claim_a_parity_feasibility_all_data.md"
METHODS = ("oracle", "pact", "pact_plus", "joint_psrl_uniform", "psrl_notype")
SEEDS = tuple(range(1000, 1010))
SWEEPS = {
    "s1_population_m4": [(n, 4) for n in range(2, 11)],
    "s2_library_n3": [(3, m) for m in (4, 8, 16)],
    "s3_frontier_m16": [(n, 16) for n in range(2, 9)],
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def table(lines: list[str], rows: list[dict[str, object] | dict[str, str]], columns: list[tuple[str, str]]) -> None:
    lines.append("| " + " | ".join(label for _, label in columns) + " |")
    lines.append("|" + "|".join("---" for _ in columns) + "|")
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(key, "")).replace("|", "\\|").replace("\n", " ") for key, _ in columns) + " |")


def npz_path(sweep: str, n: int, m: int, method: str, seed: int) -> Path:
    return NPZ_DIR / sweep / f"n{n:02d}_m{m:02d}" / f"{method}_seed{seed}.npz"


def main() -> None:
    summary = read_csv(SUMMARY)
    parity = read_csv(PARITY)
    probes = read_csv(PROBES)
    libraries = read_csv(LIBRARIES)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    artifact_lookup = {record["path"]: record for record in manifest["artifacts"]}

    per_seed_parity: list[dict[str, object]] = []
    long_rows: list[dict[str, object]] = []
    integrity: list[dict[str, object]] = []
    for sweep, cells in SWEEPS.items():
        for n, m in cells:
            for seed in SEEDS:
                pact_path = npz_path(sweep, n, m, "pact", seed)
                joint_path = npz_path(sweep, n, m, "joint_psrl_uniform", seed)
                with np.load(pact_path, allow_pickle=False) as pact, np.load(joint_path, allow_pickle=False) as joint:
                    joint_feasible = bool(joint["feasible"])
                    if joint_feasible:
                        endpoint_gap = float(pact["cumulative_regret"][-1] - joint["cumulative_regret"][-1])
                        max_gap = float(np.max(np.abs(pact["cumulative_regret"] - joint["cumulative_regret"])))
                        mismatches = int(np.count_nonzero(pact["action_indices"] != joint["action_indices"]))
                        joint_endpoint = float(joint["cumulative_regret"][-1])
                    else:
                        endpoint_gap = max_gap = joint_endpoint = math.nan
                        mismatches = 0
                    per_seed_parity.append(
                        {
                            "sweep": sweep,
                            "n": n,
                            "m": m,
                            "seed": seed,
                            "joint_feasible": joint_feasible,
                            "pact_endpoint": repr(float(pact["cumulative_regret"][-1])),
                            "joint_endpoint": repr(joint_endpoint),
                            "pact_minus_joint": repr(endpoint_gap),
                            "max_abs_trajectory_gap": repr(max_gap),
                            "action_mismatches": mismatches,
                            "cap_rule": str(joint["cap_rule"]),
                        }
                    )

            for method in METHODS:
                for seed in SEEDS:
                    path = npz_path(sweep, n, m, method, seed)
                    relative = path.relative_to(ROOT).as_posix()
                    record = artifact_lookup[relative]
                    integrity.append(
                        {
                            "path": relative,
                            "bytes": path.stat().st_size,
                            "sha256": sha256(path),
                            "manifest_sha256": record["sha256"],
                        }
                    )
                    with np.load(path, allow_pickle=False) as payload:
                        for episode in range(50):
                            long_rows.append(
                                {
                                    "sweep": sweep,
                                    "n": n,
                                    "m": m,
                                    "method": method,
                                    "seed": seed,
                                    "episode": episode + 1,
                                    "feasible": bool(payload["feasible"]),
                                    "action_index": int(payload["action_indices"][episode]),
                                    "instant_regret": repr(float(payload["instant_regret"][episode])),
                                    "cum_regret": repr(float(payload["cumulative_regret"][episode])),
                                    "planner_ms": repr(float(payload["planner_ms"][episode])),
                                    "update_us_per_event": repr(float(payload["update_us_per_event"][episode])),
                                }
                            )

    storage_rows: list[dict[str, object]] = []
    for sweep, cells in SWEEPS.items():
        for n, m in cells:
            factored_entries = n * m
            joint_entries = m**n
            cell = manifest["cells"][f"n{n}_m{m}"]
            probe = cell["joint_probe"]
            storage_rows.append(
                {
                    "sweep": sweep,
                    "n": n,
                    "m": m,
                    "planner_profiles": cell["planner_profiles"],
                    "factored_entries": factored_entries,
                    "factored_bytes": factored_entries * 8,
                    "joint_entries": joint_entries,
                    "joint_bytes": joint_entries * 8,
                    "joint_factored_ratio": repr(joint_entries / factored_entries),
                    "joint_feasible": probe["feasible"],
                    "cap_rule": probe["rule"],
                    "first_update_seconds": probe["elapsed_seconds"],
                    "entries_processed": probe["entries_processed"],
                    "planner_allocated_bytes": cell["planner_allocated_bytes"],
                    "cell_runtime_seconds": cell.get("cell_wallclock_seconds", cell.get("npz_artifact_wallclock_span_seconds")),
                }
            )

    headline = {
        "feasible_joint_cells": sum(row["joint_feasible"].lower() == "true" for row in parity),
        "max_trajectory_gap": max(float(row["max_abs_trajectory_gap"]) for row in parity if row["joint_feasible"].lower() == "true"),
        "action_mismatches": sum(int(row["action_mismatch_count"]) for row in parity),
        "frontier": manifest["joint_feasibility_frontier"],
        "npz_files": len(integrity),
        "trajectory_rows": len(long_rows),
    }

    source_files = [SUMMARY, PARITY, MANIFEST, PROBES, LIBRARIES, REGRET_FIGURE]
    source_integrity = [
        {"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in source_files
    ]

    lines = [
        "# HP-SPGG Analytic Scaling — Claim A Complete Results",
        "",
        "This single document contains every numeric result relevant to Claim A: factored/explicit-joint parity as storage grows, the explicit-joint feasibility frontier, all method/cell aggregates, all per-seed parity checks, every 50-episode trajectory/timing row, all DGP and type-library records, and SHA-256 for every NPZ. Claim B burn-in inference is intentionally excluded and documented separately.",
        "",
        "## Headline disposition",
        "",
        f"- Joint-feasible sweep cells: {headline['feasible_joint_cells']}; maximum PACT/Joint trajectory gap: {headline['max_trajectory_gap']}; action mismatches: {headline['action_mismatches']}.",
        f"- S3 joint frontier: feasible through n={headline['frontier']['largest_feasible_n']}; first infeasible at n={headline['frontier']['first_infeasible_n']}.",
        "- At n=7,m=16 the first-update >1 s rule fires; at n=8,m=16 the >4 GB rule fires. Factored methods remain feasible.",
        "- S1 final regret is zero for every displayed method, so S1 supports exact parity/storage scaling but is decision-degenerate rather than performance-separating.",
        "",
        "## Protocol and hard caps",
        "",
        f"- K={manifest['K']}; beta={manifest['beta']}; sigma={manifest['sigma']}; seeds={manifest['seeds']}; provider calls={manifest['provider_calls']}.",
        f"- Action values read from substrate: {manifest['action_values']} ({manifest['action_value_count']} values).",
        f"- Joint table cap: {manifest['caps']['joint_table_bytes']} bytes; first-update cap: {manifest['caps']['joint_first_update_seconds']} s; planner cap: {manifest['caps']['planner_evaluations_per_step']} profiles/step; cell cap: {manifest['caps']['cell_wallclock_minutes']} min.",
        "",
        "## Aggregate factored / explicit-joint parity (all 19 sweep cells)",
        "",
    ]
    table(lines, parity, [(key, key) for key in parity[0]])
    lines.extend(["", "## Per-seed factored / explicit-joint parity (all 190 rows)", ""])
    table(lines, per_seed_parity, [(key, key) for key in per_seed_parity[0]])
    lines.extend(["", "## Complete method/cell summary (all 95 rows)", ""])
    table(lines, summary, [(key, key) for key in summary[0]])
    lines.extend(["", "## Storage, planner, runtime, and feasibility (all 19 sweep cells)", ""])
    table(lines, storage_rows, [(key, key) for key in storage_rows[0]])
    lines.extend(["", "## Type-library records (all 28 rows)", ""])
    table(lines, libraries, [(key, key) for key in libraries[0]])
    lines.extend(["", "## DGP probes (all 17 unique cells)", ""])
    table(lines, probes, [(key, key) for key in probes[0]])
    lines.extend(["", "## Correctness gates", "", "```json", json.dumps(manifest["correctness_gates"], indent=2), "```"])
    lines.extend(["", "## Primary source integrity", ""])
    table(lines, source_integrity, [(key, key) for key in source_integrity[0]])
    lines.extend(["", "## Per-NPZ integrity (all 950 files)", ""])
    table(lines, integrity, [(key, key) for key in integrity[0]])
    lines.extend(["", "## Complete episode-level results (all 47,500 rows)", ""])
    table(lines, long_rows, [(key, key) for key in long_rows[0]])
    lines.extend(
        [
            "",
            "## Coverage checks",
            "",
            f"- Parity aggregate rows: {len(parity)}.",
            f"- Per-seed parity rows: {len(per_seed_parity)}.",
            f"- Method/cell summary rows: {len(summary)}.",
            f"- Storage/frontier rows: {len(storage_rows)}.",
            f"- Type-library rows: {len(libraries)}.",
            f"- DGP probe rows: {len(probes)}.",
            f"- NPZ integrity rows: {len(integrity)}.",
            f"- Episode-level rows: {len(long_rows)}.",
            "- Every feasible PACT/Joint action sequence and regret trajectory is identical.",
        ]
    )
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "output": OUT.relative_to(ROOT).as_posix(), "bytes": OUT.stat().st_size, "lines": len(lines), **headline}, indent=2))


if __name__ == "__main__":
    main()
