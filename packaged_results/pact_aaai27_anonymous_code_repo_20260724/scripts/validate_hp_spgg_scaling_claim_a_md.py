"""Strict validation for the single complete HP-SPGG scaling Claim-A Markdown."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis" / "hp_spgg_analytic_scaling"
REPORT = DATA / "claim_a_parity_feasibility_all_data.md"
NPZ_DIR = DATA / "npz"
SUMMARY = DATA / "scaling_summary.csv"
PARITY = DATA / "scaling_parity.csv"
MANIFEST = DATA / "manifest_scaling.json"
PROBES = DATA / "dgp_probes.csv"
LIBRARIES = DATA / "type_libraries.csv"
REGRET_FIGURE = DATA / "fig_hp_spgg_analytic_scaling_regret_v1.pdf"
METHODS = ("oracle", "pact", "pact_plus", "joint_psrl_uniform", "psrl_notype")
SEEDS = tuple(range(1000, 1010))
SWEEPS = {
    "s1_population_m4": [(n, 4) for n in range(2, 11)],
    "s2_library_n3": [(3, m) for m in (4, 8, 16)],
    "s3_frontier_m16": [(n, 16) for n in range(2, 9)],
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def table_rows(lines: list[str], heading: str) -> tuple[list[str], list[list[str]]]:
    try:
        index = lines.index(heading) + 1
    except ValueError as exc:
        raise AssertionError(f"Claim-A Markdown section missing: {heading}") from exc
    while index < len(lines) and not lines[index].startswith("|"):
        index += 1
    header = [cell.strip() for cell in lines[index][1:-1].split("|")]
    if index + 1 >= len(lines) or not lines[index + 1].startswith("|---"):
        raise AssertionError(f"Claim-A Markdown table missing: {heading}")
    rows: list[list[str]] = []
    for line in lines[index + 2 :]:
        if not line.startswith("|"):
            break
        rows.append([cell.strip().replace("\\|", "|") for cell in line[1:-1].split("|")])
    return header, rows


def npz_path(sweep: str, n: int, m: int, method: str, seed: int) -> Path:
    return NPZ_DIR / sweep / f"n{n:02d}_m{m:02d}" / f"{method}_seed{seed}.npz"


def same_float(left: str, right: float) -> bool:
    observed = float(left)
    return (math.isnan(observed) and math.isnan(right)) or observed == right


def main() -> None:
    import math

    if not REPORT.is_file() or REPORT.stat().st_size < 5_000_000:
        raise AssertionError("Claim-A complete Markdown is missing or unexpectedly small")
    text = REPORT.read_text(encoding="utf-8")
    lines = text.splitlines()
    private = bytes.fromhex("762d73687571696e67736869").decode("utf-8")
    if private.lower() in text.lower():
        raise AssertionError("private local identity found in Claim-A Markdown")

    expected_counts = {
        "## Aggregate factored / explicit-joint parity (all 19 sweep cells)": 19,
        "## Per-seed factored / explicit-joint parity (all 190 rows)": 190,
        "## Complete method/cell summary (all 95 rows)": 95,
        "## Storage, planner, runtime, and feasibility (all 19 sweep cells)": 19,
        "## Type-library records (all 28 rows)": 28,
        "## DGP probes (all 17 unique cells)": 17,
        "## Primary source integrity": 6,
        "## Per-NPZ integrity (all 950 files)": 950,
        "## Complete episode-level results (all 47,500 rows)": 47_500,
    }
    tables: dict[str, tuple[list[str], list[list[str]]]] = {}
    for heading, expected in expected_counts.items():
        tables[heading] = table_rows(lines, heading)
        if len(tables[heading][1]) != expected:
            raise AssertionError(f"{heading}: rows={len(tables[heading][1])}, expected={expected}")

    integrity_heading = "## Per-NPZ integrity (all 950 files)"
    integrity_header, integrity_rows = tables[integrity_heading]
    integrity_lookup = {row[0]: dict(zip(integrity_header, row, strict=True)) for row in integrity_rows}
    expected_npzs = [
        npz_path(sweep, n, m, method, seed)
        for sweep, cells in SWEEPS.items()
        for n, m in cells
        for method in METHODS
        for seed in SEEDS
    ]
    for path in expected_npzs:
        relative = path.relative_to(ROOT).as_posix()
        row = integrity_lookup.get(relative)
        if row is None or row["sha256"] != sha256(path) or row["manifest_sha256"] != row["sha256"]:
            raise AssertionError(f"Claim-A NPZ integrity mismatch: {relative}")

    long_heading = "## Complete episode-level results (all 47,500 rows)"
    long_header, long_rows = tables[long_heading]
    expected_header = [
        "sweep", "n", "m", "method", "seed", "episode", "feasible", "action_index",
        "instant_regret", "cum_regret", "planner_ms", "update_us_per_event",
    ]
    if long_header != expected_header:
        raise AssertionError(f"Claim-A long schema changed: {long_header}")
    row_index = 0
    for sweep, cells in SWEEPS.items():
        for n, m in cells:
            for method in METHODS:
                for seed in SEEDS:
                    with np.load(npz_path(sweep, n, m, method, seed), allow_pickle=False) as payload:
                        for episode in range(50):
                            row = long_rows[row_index]
                            identity = [sweep, str(n), str(m), method, str(seed), str(episode + 1)]
                            if row[:6] != identity:
                                raise AssertionError(f"Claim-A long row order mismatch at {row_index}: {row[:6]}")
                            if row[6] != str(bool(payload["feasible"])) or int(row[7]) != int(payload["action_indices"][episode]):
                                raise AssertionError(f"Claim-A feasibility/action mismatch at row {row_index}")
                            expected_values = (
                                float(payload["instant_regret"][episode]),
                                float(payload["cumulative_regret"][episode]),
                                float(payload["planner_ms"][episode]),
                                float(payload["update_us_per_event"][episode]),
                            )
                            for observed, expected in zip(row[8:], expected_values, strict=True):
                                value = float(observed)
                                if not ((math.isnan(value) and math.isnan(expected)) or value == expected):
                                    raise AssertionError(f"Claim-A numeric mismatch at row {row_index}")
                            row_index += 1
    if row_index != 47_500:
        raise AssertionError(f"Claim-A long rows checked={row_index}")

    for path in (SUMMARY, PARITY, MANIFEST, PROBES, LIBRARIES, REGRET_FIGURE):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in text or sha256(path) not in text:
            raise AssertionError(f"Claim-A source path/hash missing: {relative}")
    required_values = (
        "maximum PACT/Joint trajectory gap: 0.0",
        "action mismatches: 0",
        "feasible through n=6",
        "first infeasible at n=7",
        "first_update_gt_1s",
        "joint_table_gt_4GB",
        "Episode-level rows: 47500",
    )
    for value in required_values:
        if value not in text:
            raise AssertionError(f"Claim-A required result missing: {value}")

    print(
        json.dumps(
            {
            "status": "ok",
            "report": REPORT.relative_to(ROOT).as_posix(),
            "bytes": REPORT.stat().st_size,
            "lines": len(lines),
            "tables": expected_counts,
            "npz_hashes_checked": len(expected_npzs),
            "episode_rows_checked": row_index,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
