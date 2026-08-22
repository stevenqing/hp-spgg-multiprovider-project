"""Strict validation for the locked HP-SPGG Claim-B v3 confirmatory study."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis" / "hp_spgg_burn_in_v3_confirmatory"
PREREG = OUT / "preregistration.json"
PREREG_MD = OUT / "PREREGISTRATION.md"
PREREG_SUMS = OUT / "PREREGISTRATION.sha256"
PREREG_SHA = "1cbaf2a8eaf215f241e9274e4296c7be9137bdff8ad8f84eefb053e81f84fb44"
PREREG_MD_SHA = "4acdb89a5dd39b8a13ef73f160a56ca17f4faee2dda862a02b0969e43ddf11fd"
FILES = {
    "affinity_batches": OUT / "affinity_batches.csv",
    "affinity_summary": OUT / "affinity_summary.csv",
    "fixed_raw": OUT / "fixed_channel_agent_results.csv",
    "fixed_summary": OUT / "fixed_channel_cell_summary.csv",
    "proxy": OUT / "posterior_error_proxy_checkpoints.csv",
    "adaptive_raw": OUT / "adaptive_seed_results.csv",
    "adaptive_summary": OUT / "adaptive_cell_summary.csv",
    "results": OUT / "confirmatory_results.json",
    "report": OUT / "claim_b_v3_confirmatory_results.md",
    "figure_pdf": OUT / "fig_hp_spgg_burn_in_v3_confirmatory.pdf",
    "figure_png": OUT / "fig_hp_spgg_burn_in_v3_confirmatory.png",
}
EXPECTED_ROWS = {
    "affinity_batches": 3000,
    "affinity_summary": 15,
    "fixed_raw": 105000,
    "fixed_summary": 34,
    "proxy": 84,
    "adaptive_raw": 1200,
    "adaptive_summary": 6,
}
TYPE_M = (2, 3, 4, 6, 8, 12, 16)
TYPE_H = (1, 2, 4, 8)
POP_N = (2, 4, 8, 16, 32, 64)
BOOTSTRAP_REPS = 2000
BOOTSTRAP_SEED = 91073


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def ols(x: list[float], y: list[float]) -> dict[str, float | int]:
    x_array = np.asarray(x, dtype=float)
    y_array = np.asarray(y, dtype=float)
    slope, intercept = np.polyfit(x_array, y_array, 1)
    predicted = slope * x_array + intercept
    denominator = float(np.sum((y_array - np.mean(y_array)) ** 2))
    r_squared = 1.0 - float(np.sum((y_array - predicted) ** 2)) / denominator if denominator > 0.0 else 1.0
    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "r_squared": float(r_squared),
        "observations": len(x),
    }


def assert_close(observed: float, expected: float, *, atol: float = 1e-12) -> None:
    if not math.isclose(observed, expected, rel_tol=0.0, abs_tol=atol):
        raise AssertionError(f"numeric mismatch: observed={observed}, expected={expected}")


def validate_affinity(rows: list[dict[str, str]], results: dict[str, object]) -> None:
    x = [float(row["x_exact_information"]) for row in rows]
    y = [float(row["y_negative_log_empirical"]) for row in rows]
    fit = ols(x, y)
    stored = results["gates"]["G1_affinity_core"]["fit"]
    for key in ("slope", "intercept", "r_squared"):
        assert_close(float(fit[key]), float(stored[key]))
    max_standardized = max(abs(float(row["standardized_error"])) for row in rows)
    assert_close(max_standardized, float(results["gates"]["G1_affinity_core"]["max_abs_standardized_cell_error"]))
    gates = {
        "r_squared": float(fit["r_squared"]) >= 0.995,
        "point_slope": 0.98 <= float(fit["slope"]) <= 1.02,
        "bootstrap_ci_covers_one": (
            float(results["gates"]["G1_affinity_core"]["slope_ci95"][0]) <= 1.0
            <= float(results["gates"]["G1_affinity_core"]["slope_ci95"][1])
        ),
        "absolute_intercept": abs(float(fit["intercept"])) <= 0.03,
        "maximum_standardized_cell_error": max_standardized <= 4.5,
    }
    if gates != results["gates"]["G1_affinity_core"]["gates"]:
        raise AssertionError("G1 gate reconstruction mismatch")


def bootstrap_slopes(
    cells: list[tuple[tuple[int, int, int], float, np.ndarray]],
    *,
    seed_offset: int,
) -> list[float]:
    rng = np.random.default_rng(BOOTSTRAP_SEED + seed_offset)
    x = [cell[1] for cell in cells]
    slopes = np.empty(BOOTSTRAP_REPS, dtype=float)
    for replicate in range(BOOTSTRAP_REPS):
        y = []
        for _, _, values in cells:
            indices = rng.integers(0, len(values), size=len(values))
            y.append(float(np.mean(values[indices])))
        slopes[replicate] = float(ols(x, y)["slope"])
    return [float(np.quantile(slopes, 0.025)), float(np.quantile(slopes, 0.975))]


def validate_fixed(
    raw: list[dict[str, str]],
    summaries: list[dict[str, str]],
    results: dict[str, object],
) -> None:
    by_cell_seed: dict[tuple[str, int, int, int], dict[int, list[float]]] = {}
    events: dict[tuple[str, int, int, int], list[bool]] = {}
    for row in raw:
        key = (row["phase"], int(row["n"]), int(row["m"]), int(row["H"]))
        by_cell_seed.setdefault(key, {}).setdefault(int(row["seed"]), []).append(float(row["restricted_first_episode"]))
        events.setdefault(key, []).append(row["event"] == "True")
    if any(len(seed_rows) != 500 for seed_rows in by_cell_seed.values()):
        raise AssertionError("fixed cell does not contain exactly 500 seed clusters")

    summary_by_key = {
        (row["phase"], int(row["n"]), int(row["m"]), int(row["H"])): row
        for row in summaries
    }
    expected_type = {("type_horizon", 3, m, H) for m in TYPE_M for H in TYPE_H}
    expected_population = {("population", n, 8, 4) for n in POP_N}
    if set(summary_by_key) != expected_type | expected_population:
        raise AssertionError("fixed summary grid mismatch")

    type_cells: list[tuple[tuple[int, int, int], float, np.ndarray]] = []
    population_cells: list[tuple[tuple[int, int, int], float, np.ndarray]] = []
    original_cells: list[tuple[tuple[int, int, int], float, np.ndarray]] = []
    type_censor = []
    pop_censor = []
    turn_equivalents: dict[int, list[float]] = {m: [] for m in TYPE_M}
    for key, row in summary_by_key.items():
        phase, n, m, H = key
        seed_map = by_cell_seed[key]
        seed_agent_means = np.asarray([np.mean(seed_map[seed]) for seed in sorted(seed_map)], dtype=float)
        seed_all = np.asarray([np.max(seed_map[seed]) for seed in sorted(seed_map)], dtype=float)
        if phase == "type_horizon":
            x = float(row["predictor_per_agent"])
            type_cells.append(((n, m, H), x, seed_agent_means))
            type_censor.append(1.0 - float(np.mean(events[key])))
            turn_equivalents[m].append(H * float(np.mean(seed_agent_means)))
            assert_close(float(row["restricted_mean_per_agent_episode"]), float(np.mean(seed_agent_means)))
        else:
            x = float(row["predictor_all_agent"])
            original_x = float(row["predictor_original_linear_n"])
            population_cells.append(((n, m, H), x, seed_all))
            original_cells.append(((n, m, H), original_x, seed_all))
            pop_censor.append(float(row["censoring_fraction_seeds"]))
            assert_close(float(row["restricted_mean_all_agent_episode"]), float(np.mean(seed_all)))

    type_cells.sort(key=lambda item: item[0])
    population_cells.sort(key=lambda item: item[0])
    original_cells.sort(key=lambda item: item[0])
    type_fit = ols([item[1] for item in type_cells], [float(np.mean(item[2])) for item in type_cells])
    population_fit = ols([item[1] for item in population_cells], [float(np.mean(item[2])) for item in population_cells])
    original_fit = ols([item[1] for item in original_cells], [float(np.mean(item[2])) for item in original_cells])
    for observed, stored in (
        (type_fit, results["gates"]["G2_type_horizon"]["fit"]),
        (population_fit, results["gates"]["G3_population"]["corrected_fit"]),
        (original_fit, results["gates"]["G3_population"]["original_linear_n_fit"]),
    ):
        for name in ("slope", "intercept", "r_squared"):
            assert_close(float(observed[name]), float(stored[name]))

    type_ci = bootstrap_slopes(type_cells, seed_offset=10)
    pop_ci = bootstrap_slopes(population_cells, seed_offset=20)
    for observed, stored in (
        (type_ci, results["gates"]["G2_type_horizon"]["slope_ci95"]),
        (pop_ci, results["gates"]["G3_population"]["corrected_slope_ci95"]),
    ):
        assert_close(observed[0], float(stored[0]))
        assert_close(observed[1], float(stored[1]))

    max_ratio = max(max(values) / min(values) for values in turn_equivalents.values())
    g2 = {
        "r_squared": float(type_fit["r_squared"]) >= 0.9,
        "bootstrap_slope_ci_low_positive": type_ci[0] > 0.0,
        "censoring": max(type_censor) <= 0.01,
        "turn_equivalent_ratio": max_ratio <= 1.35,
    }
    advantage = float(population_fit["r_squared"]) - float(original_fit["r_squared"])
    g3 = {
        "r_squared": float(population_fit["r_squared"]) >= 0.9,
        "bootstrap_slope_ci_low_positive": pop_ci[0] > 0.0,
        "censoring": max(pop_censor) <= 0.01,
        "corrected_advantage": advantage >= 0.1,
    }
    if g2 != results["gates"]["G2_type_horizon"]["gates"]:
        raise AssertionError("G2 gate reconstruction mismatch")
    if g3 != results["gates"]["G3_population"]["gates"]:
        raise AssertionError("G3 gate reconstruction mismatch")


def validate_proxy(rows: list[dict[str, str]], results: dict[str, object]) -> None:
    if not all(row["upper95_below_bound"] == "True" for row in rows):
        reconstructed_bound = False
    else:
        reconstructed_bound = True
    by_cell: dict[tuple[int, int], dict[int, float]] = {}
    for row in rows:
        if row["phase"] != "type_horizon":
            raise AssertionError("proxy table unexpectedly contains a non-type-horizon row")
        key = (int(row["m"]), int(row["H"]))
        by_cell.setdefault(key, {})[int(row["checkpoint"])] = float(row["mean_cumulative_proxy"])
        if float(row["upper95_cumulative_proxy"]) > float(row["finite_hellinger_bound"]):
            reconstructed_bound = False
    increments = [
        (values[2048] - values[1024]) / max(values[2048], 1e-15)
        for values in by_cell.values()
    ]
    max_increment = max(increments)
    assert_close(max_increment, float(results["gates"]["G4_K_independent_proxy"]["max_relative_increment_1024_to_2048"]))
    gates = {
        "all_upper95_below_bound": reconstructed_bound,
        "relative_increment": max_increment <= 0.02,
    }
    if gates != results["gates"]["G4_K_independent_proxy"]["gates"]:
        raise AssertionError("G4 gate reconstruction mismatch")


def validate_adaptive(rows: list[dict[str, str]], results: dict[str, object]) -> None:
    grid = {(int(row["m"]), int(row["H"])) for row in rows}
    if grid != {(m, H) for m in (4, 8, 16) for H in (1, 4)}:
        raise AssertionError("adaptive grid mismatch")
    max_censor = max(float(row["censoring_fraction_agents"]) for row in rows)
    all_bounds = all(float(row["upper95_error_final_preupdate"]) <= float(row["global_rho_error_bound"]) for row in rows)
    max_increment = max(float(row["relative_proxy_increment"]) for row in rows)
    gates = {
        "censoring": max_censor <= 0.05,
        "all_upper95_errors_below_global_bound": all_bounds,
        "relative_proxy_increment": max_increment <= 0.05,
    }
    if gates != results["gates"]["G5_adaptive_robustness"]["gates"]:
        raise AssertionError("G5 gate reconstruction mismatch")


def main() -> None:
    if sha256(PREREG) != PREREG_SHA or sha256(PREREG_MD) != PREREG_MD_SHA:
        raise AssertionError("preregistration hash mismatch")
    expected_sums = (
        f"{PREREG_SHA}  preregistration.json\n"
        f"{PREREG_MD_SHA}  PREREGISTRATION.md\n"
    )
    if PREREG_SUMS.read_text(encoding="utf-8") != expected_sums:
        raise AssertionError("preregistration checksum sidecar mismatch")
    for path in FILES.values():
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(path)
    tables = {name: read_csv(FILES[name]) for name in EXPECTED_ROWS}
    counts = {name: len(rows) for name, rows in tables.items()}
    if counts != EXPECTED_ROWS:
        raise AssertionError(f"row-count mismatch: {counts}")
    results = json.loads(FILES["results"].read_text(encoding="utf-8"))
    if results["preregistration_sha256"] != PREREG_SHA:
        raise AssertionError("results reference the wrong preregistration")
    if results["provider_calls"] != 0:
        raise AssertionError("confirmatory study must make zero provider calls")
    if results["row_counts"] != {
        "affinity_batches": 3000,
        "affinity_summary": 15,
        "fixed_agent_results": 105000,
        "fixed_cell_summary": 34,
        "proxy_checkpoints": 84,
        "adaptive_seed_results": 1200,
        "adaptive_cell_summary": 6,
    }:
        raise AssertionError("stored row counts mismatch")

    validate_affinity(tables["affinity_summary"], results)
    validate_fixed(tables["fixed_raw"], tables["fixed_summary"], results)
    validate_proxy(tables["proxy"], results)
    validate_adaptive(tables["adaptive_summary"], results)
    reconstructed = all(bool(results["gates"][name]["passed"]) for name in (
        "G1_affinity_core",
        "G2_type_horizon",
        "G3_population",
        "G4_K_independent_proxy",
        "G5_adaptive_robustness",
    ))
    if bool(results["claim_b_v3_supported"]) != reconstructed:
        raise AssertionError("overall decision does not equal the locked conjunction")
    if results["original_linear_n_formula_supported"] is not False:
        raise AssertionError("retired linear-n formula must not be relabeled as supported")
    report = FILES["report"].read_text(encoding="utf-8")
    expected_word = "SUPPORTED" if reconstructed else "UNSUPPORTED"
    if f"Overall locked decision: **{expected_word}**" not in report:
        raise AssertionError("Markdown decision differs from machine-readable decision")
    private = bytes.fromhex("762d73687571696e67736869")
    for path in FILES.values():
        if private in path.read_bytes().lower():
            raise AssertionError(f"private identity found in {path.name}")

    output = {
        "status": "ok",
        "claim_b_v3_supported": reconstructed,
        "row_counts": counts,
        "preregistration_sha256": PREREG_SHA,
        "output_sha256": {name: sha256(path) for name, path in FILES.items()},
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
