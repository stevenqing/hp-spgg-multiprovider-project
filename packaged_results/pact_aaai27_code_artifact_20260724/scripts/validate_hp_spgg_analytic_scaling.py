"""Strict validator for the additive HP-SPGG analytic scaling release."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_hpgg.analytic_scaling import (  # noqa: E402
    ACTIONS,
    BASE_PARAMETERS,
    JOINT_BYTE_CAP,
    PLANNER_EVALUATION_CAP,
    RHO_THRESHOLD,
    r_squared_linear,
)


DATA = ROOT / "analysis" / "hp_spgg_analytic_scaling"
NPZ_DIR = DATA / "npz"
SUMMARY = DATA / "scaling_summary.csv"
PARITY = DATA / "scaling_parity.csv"
MANIFEST = DATA / "manifest_scaling.json"
PROBES = DATA / "dgp_probes.csv"
LIBRARIES = DATA / "type_libraries.csv"
REPORT = DATA / "scaling_run_report.md"
FIT = DATA / "scaling_burn_in_fit.json"
REGRET_FIGURE = DATA / "fig_hp_spgg_analytic_scaling_regret_v1.pdf"
BURN_FIGURE = DATA / "fig_hp_spgg_analytic_scaling_burnin_v1.pdf"
DIAGNOSTIC_JSON = DATA / "burn_in_support_diagnostic.json"
DIAGNOSTIC_MD = DATA / "burn_in_support_diagnostic.md"
K = 50
SEEDS = tuple(range(1000, 1010))
METHODS = ("oracle", "pact", "pact_plus", "joint_psrl_uniform", "psrl_notype")
SWEEPS = {
    "s1_population_m4": [(n, 4) for n in range(2, 11)],
    "s2_library_n3": [(3, m) for m in (4, 8, 16)],
    "s3_frontier_m16": [(n, 16) for n in range(2, 9)],
}
REQUIRED_NPZ_KEYS = {
    "action_indices", "beta", "burn_in_all_agents", "burn_in_per_agent", "cap_rule",
    "cumulative_regret", "feasible", "instant_regret", "joint_feasible", "K", "m",
    "method", "n", "planner_cache_hit", "planner_feasible", "planner_ms",
    "posterior_true_mass", "rho_hat", "seed", "storage_allocated_bytes",
    "storage_entries", "storage_theoretical_bytes", "sweep", "true_types",
    "update_us_per_event", "welfare",
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


def close(left: float, right: float, tolerance: float = 1e-9) -> bool:
    return abs(left - right) <= tolerance * max(1.0, abs(left), abs(right))


def npz_path(sweep: str, n: int, m: int, method: str, seed: int) -> Path:
    return NPZ_DIR / sweep / f"n{n:02d}_m{m:02d}" / f"{method}_seed{seed}.npz"


def main() -> None:
    required = (
        SUMMARY, PARITY, MANIFEST, PROBES, LIBRARIES, REPORT, FIT,
        REGRET_FIGURE, BURN_FIGURE, DIAGNOSTIC_JSON, DIAGNOSTIC_MD,
    )
    for path in required:
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(path)

    summary = read_csv(SUMMARY)
    parity = read_csv(PARITY)
    probes = read_csv(PROBES)
    libraries = read_csv(LIBRARIES)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    fit = json.loads(FIT.read_text(encoding="utf-8"))
    diagnostic = json.loads(DIAGNOSTIC_JSON.read_text(encoding="utf-8"))
    if diagnostic.get("claim_b_supported") is not False or len(diagnostic.get("causes", [])) < 9:
        raise AssertionError("burn-in support diagnostic is missing or no longer records the null")
    if any(float(row["all_agent_median"]) != 8.0 for row in diagnostic["s1"]):
        raise AssertionError("diagnostic no longer records S1 median saturation at 8")
    diagnostic_text = DIAGNOSTIC_MD.read_text(encoding="utf-8")
    for phrase in ("theory-target mismatch", "deterministic analytic observations", "informative censoring", "does not support"):
        if phrase not in diagnostic_text:
            raise AssertionError(f"burn-in diagnostic explanation missing: {phrase}")
    expected_summary_keys = [
        (sweep, n, m, method)
        for sweep, cells in SWEEPS.items()
        for n, m in cells
        for method in METHODS
    ]
    observed_summary_keys = [(row["sweep"], int(row["n"]), int(row["m"]), row["method"]) for row in summary]
    if observed_summary_keys != expected_summary_keys or len(summary) != 95:
        raise AssertionError(f"scaling summary grid changed: rows={len(summary)}")
    expected_parity_keys = [(sweep, n, m) for sweep, cells in SWEEPS.items() for n, m in cells]
    observed_parity_keys = [(row["sweep"], int(row["n"]), int(row["m"])) for row in parity]
    if observed_parity_keys != expected_parity_keys or len(parity) != 19:
        raise AssertionError(f"scaling parity grid changed: rows={len(parity)}")
    for row in parity:
        if row["joint_feasible"].lower() == "true":
            if int(row["action_mismatch_count"]) != 0 or float(row["max_abs_trajectory_gap"]) > 1e-8:
                raise AssertionError(f"feasible-cell parity failed: {row}")
            if row["ci_covers_zero"].lower() != "true":
                raise AssertionError(f"feasible-cell parity CI misses zero: {row}")

    expected_npzs = [
        npz_path(sweep, n, m, method, seed)
        for sweep, cells in SWEEPS.items()
        for n, m in cells
        for method in METHODS
        for seed in SEEDS
    ]
    if len(expected_npzs) != 950 or any(not path.is_file() for path in expected_npzs):
        missing = [path for path in expected_npzs if not path.is_file()]
        raise AssertionError(f"scaling NPZ grid incomplete: missing={len(missing)}")
    actual_npzs = sorted(NPZ_DIR.rglob("*.npz"))
    if len(actual_npzs) != 950:
        raise AssertionError(f"unexpected scaling NPZ count={len(actual_npzs)}")

    summary_lookup = {
        (row["sweep"], int(row["n"]), int(row["m"]), row["method"]): row for row in summary
    }
    oracle_max = 0.0
    no_type_min_r2 = math.inf
    for sweep, cells in SWEEPS.items():
        for n, m in cells:
            planner_count = len(ACTIONS) ** n
            planner_feasible = planner_count <= PLANNER_EVALUATION_CAP
            for method in METHODS:
                row = summary_lookup[(sweep, n, m, method)]
                payloads: list[dict[str, np.ndarray]] = []
                for seed in SEEDS:
                    path = npz_path(sweep, n, m, method, seed)
                    with np.load(path, allow_pickle=False) as payload:
                        if set(payload.files) != REQUIRED_NPZ_KEYS:
                            raise AssertionError(f"NPZ schema changed: {path}")
                        record = {key: np.array(payload[key], copy=True) for key in payload.files}
                    if int(record["n"]) != n or int(record["m"]) != m or int(record["K"]) != K:
                        raise AssertionError(f"NPZ cell attrs changed: {path}")
                    if int(record["seed"]) != seed or str(record["method"]) != method or str(record["sweep"]) != sweep:
                        raise AssertionError(f"NPZ identity attrs changed: {path}")
                    if record["cumulative_regret"].shape != (K,) or record["posterior_true_mass"].shape != (K, n):
                        raise AssertionError(f"NPZ trajectory shape changed: {path}")
                    if bool(record["feasible"]):
                        if not np.allclose(record["cumulative_regret"], np.cumsum(record["instant_regret"]), atol=1e-12, rtol=0.0):
                            raise AssertionError(f"NPZ cumulative regret mismatch: {path}")
                        if np.any(record["instant_regret"] < -1e-12):
                            raise AssertionError(f"negative regret: {path}")
                        if np.any(~np.isfinite(record["planner_ms"])) or np.any(record["planner_ms"] < 0.0):
                            raise AssertionError(f"invalid planner timing: {path}")
                        if np.any(~np.isfinite(record["update_us_per_event"])) or np.any(record["update_us_per_event"] < 0.0):
                            raise AssertionError(f"invalid update timing: {path}")
                    payloads.append(record)

                feasible = bool(payloads[0]["feasible"])
                if feasible != (row["feasible"].lower() == "true"):
                    raise AssertionError(f"summary feasibility mismatch: {(sweep,n,m,method)}")
                if bool(payloads[0]["planner_feasible"]) != planner_feasible:
                    raise AssertionError(f"planner cap mismatch: {(sweep,n,m)}")
                if method == "joint_psrl_uniform":
                    entries = m**n
                    expected_bytes = entries * 8
                elif method in {"pact", "pact_plus", "psrl_notype"}:
                    entries = n * m
                    expected_bytes = entries * 8
                else:
                    entries = expected_bytes = 0
                if int(payloads[0]["storage_entries"]) != entries or int(payloads[0]["storage_theoretical_bytes"]) != expected_bytes:
                    raise AssertionError(f"storage formula mismatch: {(sweep,n,m,method)}")
                if feasible:
                    endpoints = np.asarray([float(payload["cumulative_regret"][-1]) for payload in payloads])
                    mean = float(endpoints.mean())
                    sem = float(endpoints.std(ddof=1) / math.sqrt(len(endpoints)))
                    if not close(float(row["final_regret_mean"]), mean) or not close(float(row["final_regret_sem"]), sem):
                        raise AssertionError(f"summary regret mismatch: {(sweep,n,m,method)}")
                    if method == "oracle":
                        oracle_max = max(oracle_max, float(np.max(endpoints)))
                    if method == "psrl_notype":
                        mean_trajectory = np.mean([payload["cumulative_regret"] for payload in payloads], axis=0)
                        no_type_min_r2 = min(no_type_min_r2, r_squared_linear(mean_trajectory))

    gates = manifest["correctness_gates"]
    if not all(record["passed"] for record in gates.values()):
        raise AssertionError(f"hard correctness gate failed: {gates}")
    if gates["pathwise_identity_n3_m4"]["max_abs_regret_diff"] > 1e-8:
        raise AssertionError("pathwise parity tolerance changed")
    if oracle_max >= 1e-6 or no_type_min_r2 <= 0.9:
        raise AssertionError(f"oracle/no-type gate changed: oracle={oracle_max}, r2={no_type_min_r2}")

    # Directly recheck action/regret identity at the required cell.
    for seed in SEEDS:
        with np.load(npz_path("s1_population_m4", 3, 4, "pact", seed), allow_pickle=False) as pact, np.load(
            npz_path("s1_population_m4", 3, 4, "joint_psrl_uniform", seed), allow_pickle=False
        ) as joint:
            if not np.array_equal(pact["action_indices"], joint["action_indices"]):
                raise AssertionError(f"pathwise actions diverged at seed {seed}")
            if not np.allclose(pact["cumulative_regret"], joint["cumulative_regret"], atol=1e-8, rtol=0.0):
                raise AssertionError(f"pathwise regret diverged at seed {seed}")

    if len(probes) != 17 or any(row["all_pass"].lower() != "true" for row in probes):
        raise AssertionError(f"DGP probes changed: rows={len(probes)}")
    if len(libraries) != 28:
        raise AssertionError(f"type-library rows={len(libraries)}, expected 28")
    library_by_m: dict[int, list[dict[str, str]]] = {}
    for row in libraries:
        library_by_m.setdefault(int(row["m"]), []).append(row)
    retained = np.asarray(
        [
            [float(row["target_contribution"]), float(row["cooperation_weight"]), float(row["self_interest_weight"]), float(row["fairness_weight"])]
            for row in library_by_m[4]
        ]
    )
    if not np.array_equal(retained, BASE_PARAMETERS):
        raise AssertionError("retained four-type library changed")
    for m in (8, 16):
        records = library_by_m[m]
        rho = float(records[0]["rho_hat_min_across_cells"])
        if rho < RHO_THRESHOLD or any(row["respaced"].lower() != "true" for row in records):
            raise AssertionError(f"synthetic m={m} grid fails separation/re-spacing: rho={rho}")
        if not (float(records[0]["initial_rho_hat"]) < RHO_THRESHOLD):
            raise AssertionError(f"m={m} interpolation was not rejected before re-spacing")
        parameters = np.asarray(
            [
                [float(row["target_contribution"]), float(row["cooperation_weight"]), float(row["self_interest_weight"]), float(row["fairness_weight"])]
                for row in records
            ]
        )
        if np.any(parameters < BASE_PARAMETERS.min(axis=0) - 1e-12) or np.any(
            parameters > BASE_PARAMETERS.max(axis=0) + 1e-12
        ):
            raise AssertionError(f"synthetic m={m} parameters leave the archetype bounding box")

    frontier = manifest["joint_feasibility_frontier"]
    if frontier["largest_feasible_n"] is None or frontier["first_infeasible_n"] is None:
        raise AssertionError(f"joint frontier is incomplete: {frontier}")
    if int(frontier["first_infeasible_n"]) != int(frontier["largest_feasible_n"]) + 1:
        raise AssertionError(f"joint frontier is non-contiguous: {frontier}")
    first_bad = summary_lookup[("s3_frontier_m16", int(frontier["first_infeasible_n"]), 16, "joint_psrl_uniform")]
    if first_bad["cap_rule"] not in {"first_update_gt_1s", "joint_table_gt_4GB"}:
        raise AssertionError(f"unexpected joint frontier rule: {first_bad['cap_rule']}")
    n8_joint = summary_lookup[("s3_frontier_m16", 8, 16, "joint_psrl_uniform")]
    if int(n8_joint["storage_theoretical_bytes"]) <= JOINT_BYTE_CAP or n8_joint["cap_rule"] != "joint_table_gt_4GB":
        raise AssertionError("S3 n=8 does not expose the 16^8 byte-cap boundary")
    for cell, record in manifest["cells"].items():
        elapsed = record.get("cell_wallclock_seconds", record.get("npz_artifact_wallclock_span_seconds"))
        if elapsed is None or float(elapsed) > float(manifest["caps"]["cell_wallclock_minutes"]) * 60.0:
            raise AssertionError(f"cell runtime cap missing/exceeded: {cell}={elapsed}")

    artifact_lookup = {record["path"]: record for record in manifest["artifacts"]}
    for path in expected_npzs + [SUMMARY, PARITY, PROBES, LIBRARIES]:
        relative = path.relative_to(ROOT).as_posix()
        record = artifact_lookup.get(relative)
        if record is None or record["sha256"] != sha256(path) or int(record["bytes"]) != path.stat().st_size:
            raise AssertionError(f"manifest artifact mismatch: {relative}")
    for record in manifest.get("render_artifacts", []):
        path = ROOT / record["path"]
        if not path.is_file() or record["sha256"] != sha256(path):
            raise AssertionError(f"render artifact mismatch: {record['path']}")

    if fit["observations"] < 2 or not math.isfinite(float(fit["slope"])):
        raise AssertionError(f"invalid burn-in OLS: {fit}")
    if REGRET_FIGURE.stat().st_size < 10_000 or BURN_FIGURE.stat().st_size < 10_000:
        raise AssertionError("scaling figures are missing or unexpectedly small")
    report_text = REPORT.read_text(encoding="utf-8")
    required_report = ("Provider calls: 0", "Joint frontier for S3", "rho_hat", "Correctness gates")
    for text in required_report:
        if text not in report_text:
            raise AssertionError(f"run report missing: {text}")

    print(
        json.dumps(
            {
                "status": "ok",
                "summary_rows": len(summary),
                "parity_rows": len(parity),
                "npz_files": len(actual_npzs),
                "dgp_probe_rows": len(probes),
                "type_library_rows": len(libraries),
                "joint_frontier": frontier,
                "rho_hat_per_m": {
                    m: float(records[0]["rho_hat_min_across_cells"])
                    for m, records in library_by_m.items()
                },
                "oracle_max_regret": oracle_max,
                "psrl_notype_min_r_squared": no_type_min_r2,
                "burn_in_ols": {key: fit[key] for key in ("slope", "intercept", "r_squared", "observations")},
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
