"""Run the locked HP-SPGG Claim-B v3 stochastic-channel confirmatory study."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Iterable

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_hpgg.analytic_scaling import (  # noqa: E402
    ACTIONS,
    SIGMA,
    AnalyticPlanner,
    local_reward_lookup,
    rho_hat_from_lookup,
    sample_marginals,
    squared_hellinger_gaussians,
    synthesize_type_library,
)


OUT_DIR = ROOT / "analysis" / "hp_spgg_burn_in_v3_confirmatory"
PREREG = OUT_DIR / "preregistration.json"
PREREG_MD = OUT_DIR / "PREREGISTRATION.md"
PREREG_SHA256 = "1cbaf2a8eaf215f241e9274e4296c7be9137bdff8ad8f84eefb053e81f84fb44"
PREREG_MD_SHA256 = "4acdb89a5dd39b8a13ef73f160a56ca17f4faee2dda862a02b0969e43ddf11fd"
AFFINITY_BATCH_OUT = OUT_DIR / "affinity_batches.csv"
AFFINITY_SUMMARY_OUT = OUT_DIR / "affinity_summary.csv"
FIXED_RAW_OUT = OUT_DIR / "fixed_channel_agent_results.csv"
FIXED_SUMMARY_OUT = OUT_DIR / "fixed_channel_cell_summary.csv"
PROXY_OUT = OUT_DIR / "posterior_error_proxy_checkpoints.csv"
ADAPTIVE_RAW_OUT = OUT_DIR / "adaptive_seed_results.csv"
ADAPTIVE_SUMMARY_OUT = OUT_DIR / "adaptive_cell_summary.csv"
RESULTS_OUT = OUT_DIR / "confirmatory_results.json"
REPORT_OUT = OUT_DIR / "claim_b_v3_confirmatory_results.md"

CONFIRMATORY_SEEDS = tuple(range(30_000, 30_500))
ADAPTIVE_SEEDS = tuple(range(50_000, 50_200))
TYPE_M = (2, 3, 4, 6, 8, 12, 16)
TYPE_H = (1, 2, 4, 8)
POP_N = (2, 4, 8, 16, 32, 64)
TYPE_N = 3
POP_M = 8
POP_H = 4
FIXED_MAX_EPISODES = 2048
PROXY_CHECKPOINTS = (512, 1024, 2048)
ADAPTIVE_M = (4, 8, 16)
ADAPTIVE_H = (1, 4)
ADAPTIVE_N = 3
ADAPTIVE_MAX_EPISODES = 4096
THRESHOLD = 0.9
BOOTSTRAP_REPS = 2000
BOOTSTRAP_SEED = 91073
AFFINITY_REPS = 200_000
AFFINITY_BATCHES = 200
AFFINITY_GAPS = (1, 2, 3)
AFFINITY_TARGETS = (0.25, 0.5, 1.0, 1.5, 2.0)

RESULT_FILES = (
    AFFINITY_BATCH_OUT,
    AFFINITY_SUMMARY_OUT,
    FIXED_RAW_OUT,
    FIXED_SUMMARY_OUT,
    PROXY_OUT,
    ADAPTIVE_RAW_OUT,
    ADAPTIVE_SUMMARY_OUT,
    RESULTS_OUT,
    REPORT_OUT,
)


@dataclass
class FixedCell:
    phase: str
    n: int
    m: int
    H: int
    rho_action: float
    rho_global: float
    first_episode: np.ndarray
    event: np.ndarray
    true_types: np.ndarray
    final_mass: np.ndarray
    proxy_values: dict[int, np.ndarray]

    @property
    def restricted(self) -> np.ndarray:
        return np.where(self.event, self.first_episode, FIXED_MAX_EPISODES + 1.0)

    @property
    def seed_agent_means(self) -> np.ndarray:
        return np.mean(self.restricted, axis=1)

    @property
    def all_agent_restricted(self) -> np.ndarray:
        return np.max(self.restricted, axis=1)


@dataclass
class OLSFit:
    slope: float
    intercept: float
    r_squared: float
    observations: int

    def as_dict(self) -> dict[str, float | int]:
        return {
            "slope": self.slope,
            "intercept": self.intercept,
            "r_squared": self.r_squared,
            "observations": self.observations,
        }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    if not rows:
        raise AssertionError(f"refusing to write empty CSV: {path}")
    fields = fieldnames or list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def ols(x: Iterable[float], y: Iterable[float]) -> OLSFit:
    x_array = np.asarray(tuple(x), dtype=float)
    y_array = np.asarray(tuple(y), dtype=float)
    if len(x_array) < 2 or len(x_array) != len(y_array):
        raise ValueError("OLS requires equal vectors with at least two observations")
    slope, intercept = np.polyfit(x_array, y_array, 1)
    predicted = slope * x_array + intercept
    denominator = float(np.sum((y_array - np.mean(y_array)) ** 2))
    r_squared = 1.0 - float(np.sum((y_array - predicted) ** 2)) / denominator if denominator > 0.0 else 1.0
    return OLSFit(float(slope), float(intercept), float(r_squared), len(x_array))


def percentile_interval(values: np.ndarray) -> list[float]:
    return [float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))]


def nested_parameters(m: int) -> np.ndarray:
    if m not in TYPE_M:
        raise ValueError(f"m={m} is outside the locked nested family")
    return synthesize_type_library(16).parameters[:m].copy()


def channel(n: int, m: int) -> tuple[np.ndarray, np.ndarray, float, float]:
    parameters = nested_parameters(m)
    lookup = local_reward_lookup(n, parameters)
    means = lookup[:, len(ACTIONS) - 1, 4 * n]
    distances = squared_hellinger_gaussians(means[:, None], means[None, :])
    distances[np.tril_indices(m)] = np.inf
    rho_action = float(np.min(distances))
    rho_global, _ = rho_hat_from_lookup(lookup)
    return parameters, means, rho_action, float(rho_global)


def rng_for(seed: int, phase_code: int, n: int, m: int, H: int) -> np.random.Generator:
    return np.random.default_rng(np.random.SeedSequence([seed, phase_code, n, m, H]))


def stable_posterior(log_posterior: np.ndarray) -> np.ndarray:
    shifted = log_posterior - np.max(log_posterior, axis=-1, keepdims=True)
    posterior = np.exp(shifted)
    posterior /= np.sum(posterior, axis=-1, keepdims=True)
    return posterior


def true_mass(posterior: np.ndarray, true_types: np.ndarray) -> np.ndarray:
    return np.take_along_axis(posterior, true_types[..., None], axis=-1)[..., 0]


def finite_proxy_bound(m: int, H: int, rho: float, K: int) -> float:
    indices = np.arange(K, dtype=float)
    terms = np.minimum(1.0, (m - 1) * math.sqrt(m) * np.exp(-rho * H * indices))
    return float(H * np.sum(terms))


def error_bound(m: int, H: int, rho: float, episode: int) -> float:
    return float(min(1.0, (m - 1) * math.sqrt(m) * math.exp(-rho * H * (episode - 1))))


def simulate_fixed_cell(phase: str, n: int, m: int, H: int) -> FixedCell:
    _, means, rho_action, rho_global = channel(n, m)
    seed_count = len(CONFIRMATORY_SEEDS)
    true_types = np.empty((seed_count, n), dtype=np.int16)
    noises = np.empty((FIXED_MAX_EPISODES, seed_count, n), dtype=np.float32)
    phase_code = 101 if phase == "type_horizon" else 202
    for seed_index, seed in enumerate(CONFIRMATORY_SEEDS):
        rng = rng_for(seed, phase_code, n, m, H)
        true_types[seed_index] = rng.integers(0, m, size=n)
        noises[:, seed_index, :] = rng.standard_normal((FIXED_MAX_EPISODES, n), dtype=np.float32)

    log_posterior = np.full((seed_count, n, m), -math.log(m), dtype=float)
    first_episode = np.full((seed_count, n), FIXED_MAX_EPISODES + 1.0, dtype=float)
    event = np.zeros((seed_count, n), dtype=bool)
    cumulative_proxy = np.zeros((seed_count, n), dtype=float)
    proxy_values: dict[int, np.ndarray] = {}
    final_mass = np.full((seed_count, n), 1.0 / m, dtype=float)
    true_means = means[true_types]

    for episode in range(1, FIXED_MAX_EPISODES + 1):
        posterior = stable_posterior(log_posterior)
        mass_before = true_mass(posterior, true_types)
        cumulative_proxy += H * (1.0 - mass_before)
        observations = true_means + (SIGMA / math.sqrt(H)) * noises[episode - 1]
        residual = observations[..., None] - means.reshape(1, 1, m)
        log_posterior += -0.5 * H * (residual / SIGMA) ** 2
        posterior_after = stable_posterior(log_posterior)
        mass_after = true_mass(posterior_after, true_types)
        newly = (~event) & (mass_after > THRESHOLD)
        first_episode[newly] = episode
        event[newly] = True
        final_mass = mass_after
        if episode in PROXY_CHECKPOINTS:
            proxy_values[episode] = cumulative_proxy.copy()

    return FixedCell(
        phase=phase,
        n=n,
        m=m,
        H=H,
        rho_action=rho_action,
        rho_global=rho_global,
        first_episode=first_episode,
        event=event,
        true_types=true_types,
        final_mass=final_mass,
        proxy_values=proxy_values,
    )


def run_affinity_core() -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    _, means, _, _ = channel(TYPE_N, 16)
    batch_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    cell_batches: list[np.ndarray] = []
    x_values: list[float] = []
    for gap in AFFINITY_GAPS:
        true_mean = float(means[0])
        wrong_mean = float(means[gap])
        rho = float(squared_hellinger_gaussians(true_mean, wrong_mean))
        log_affinity = math.log1p(-rho)
        information_per_turn = -log_affinity
        for target_index, target in enumerate(AFFINITY_TARGETS):
            turns = max(1, int(round(target / information_per_turn)))
            rng = rng_for(70_000 + 100 * gap + target_index, 303, TYPE_N, 16, turns)
            sample_mean = rng.normal(true_mean, SIGMA / math.sqrt(turns), size=AFFINITY_REPS)
            log_lr = -turns * ((sample_mean - wrong_mean) ** 2 - (sample_mean - true_mean) ** 2) / (2.0 * SIGMA**2)
            root_lr = np.exp(0.5 * log_lr)
            batches = root_lr.reshape(AFFINITY_BATCHES, AFFINITY_REPS // AFFINITY_BATCHES).mean(axis=1)
            empirical = float(np.mean(root_lr))
            standard_error = float(np.std(root_lr, ddof=1) / math.sqrt(AFFINITY_REPS))
            theoretical = float(math.exp(turns * log_affinity))
            x_value = float(turns * information_per_turn)
            y_value = float(-math.log(empirical))
            standardized = (empirical - theoretical) / standard_error
            cell_index = len(summary_rows)
            cell_batches.append(batches)
            x_values.append(x_value)
            summary_rows.append(
                {
                    "cell": cell_index,
                    "gap": gap,
                    "target_information": repr(target),
                    "turns": turns,
                    "rho_pair": repr(rho),
                    "x_exact_information": repr(x_value),
                    "empirical_mean_root_lr": repr(empirical),
                    "theoretical_affinity_product": repr(theoretical),
                    "standard_error": repr(standard_error),
                    "standardized_error": repr(standardized),
                    "y_negative_log_empirical": repr(y_value),
                }
            )
            for batch_index, value in enumerate(batches):
                batch_rows.append(
                    {
                        "cell": cell_index,
                        "gap": gap,
                        "target_information": repr(target),
                        "turns": turns,
                        "batch": batch_index,
                        "mean_root_lr": repr(float(value)),
                    }
                )

    y_values = [-math.log(float(row["empirical_mean_root_lr"])) for row in summary_rows]
    point_fit = ols(x_values, y_values)
    bootstrap_rng = np.random.default_rng(BOOTSTRAP_SEED + 1)
    slopes = np.empty(BOOTSTRAP_REPS, dtype=float)
    intercepts = np.empty(BOOTSTRAP_REPS, dtype=float)
    for replicate in range(BOOTSTRAP_REPS):
        bootstrap_y = []
        for batches in cell_batches:
            indices = bootstrap_rng.integers(0, len(batches), size=len(batches))
            bootstrap_y.append(-math.log(float(np.mean(batches[indices]))))
        fit = ols(x_values, bootstrap_y)
        slopes[replicate] = fit.slope
        intercepts[replicate] = fit.intercept
    max_standardized = max(abs(float(row["standardized_error"])) for row in summary_rows)
    slope_ci = percentile_interval(slopes)
    intercept_ci = percentile_interval(intercepts)
    gates = {
        "r_squared": point_fit.r_squared >= 0.995,
        "point_slope": 0.98 <= point_fit.slope <= 1.02,
        "bootstrap_ci_covers_one": slope_ci[0] <= 1.0 <= slope_ci[1],
        "absolute_intercept": abs(point_fit.intercept) <= 0.03,
        "maximum_standardized_cell_error": max_standardized <= 4.5,
    }
    result = {
        "fit": point_fit.as_dict(),
        "slope_ci95": slope_ci,
        "intercept_ci95": intercept_ci,
        "max_abs_standardized_cell_error": max_standardized,
        "gates": gates,
        "passed": all(gates.values()),
    }
    return batch_rows, summary_rows, result


def fixed_cell_summary(cell: FixedCell) -> dict[str, object]:
    restricted = cell.restricted
    all_agent = cell.all_agent_restricted
    log_c = math.log(cell.m * math.sqrt(cell.m))
    censor_agents = int(np.size(cell.event) - np.count_nonzero(cell.event))
    seed_event = np.all(cell.event, axis=1)
    censor_seeds = int(len(seed_event) - np.count_nonzero(seed_event))
    return {
        "phase": cell.phase,
        "n": cell.n,
        "m": cell.m,
        "H": cell.H,
        "rho_action": repr(cell.rho_action),
        "rho_global": repr(cell.rho_global),
        "predictor_per_agent": repr(log_c / (cell.rho_action * cell.H)),
        "predictor_all_agent": repr((log_c + math.log(cell.n)) / (cell.rho_action * cell.H)),
        "predictor_original_linear_n": repr((cell.n + 1) * math.log(cell.m) / (cell.rho_action * cell.H)),
        "restricted_mean_per_agent_episode": repr(float(np.mean(restricted))),
        "restricted_mean_all_agent_episode": repr(float(np.mean(all_agent))),
        "median_per_agent_episode": repr(float(np.median(restricted))),
        "median_all_agent_episode": repr(float(np.median(all_agent))),
        "censored_agents": censor_agents,
        "censoring_fraction_agents": repr(censor_agents / np.size(cell.event)),
        "censored_seeds": censor_seeds,
        "censoring_fraction_seeds": repr(censor_seeds / len(seed_event)),
        "mean_final_true_mass": repr(float(np.mean(cell.final_mass))),
    }


def bootstrap_cell_fit(cells: list[FixedCell], predictor: str) -> tuple[OLSFit, list[float]]:
    if predictor == "type":
        x = [math.log(cell.m * math.sqrt(cell.m)) / (cell.rho_action * cell.H) for cell in cells]
        seed_values = [cell.seed_agent_means for cell in cells]
    elif predictor == "population":
        x = [
            (math.log(cell.m * math.sqrt(cell.m)) + math.log(cell.n)) / (cell.rho_action * cell.H)
            for cell in cells
        ]
        seed_values = [cell.all_agent_restricted for cell in cells]
    elif predictor == "original":
        x = [(cell.n + 1) * math.log(cell.m) / (cell.rho_action * cell.H) for cell in cells]
        seed_values = [cell.all_agent_restricted for cell in cells]
    else:
        raise ValueError(predictor)
    y = [float(np.mean(values)) for values in seed_values]
    point = ols(x, y)
    bootstrap_rng = np.random.default_rng(BOOTSTRAP_SEED + {"type": 10, "population": 20, "original": 30}[predictor])
    slopes = np.empty(BOOTSTRAP_REPS, dtype=float)
    for replicate in range(BOOTSTRAP_REPS):
        sampled_y = []
        for values in seed_values:
            indices = bootstrap_rng.integers(0, len(values), size=len(values))
            sampled_y.append(float(np.mean(values[indices])))
        slopes[replicate] = ols(x, sampled_y).slope
    return point, percentile_interval(slopes)


def proxy_rows(cells: list[FixedCell]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for cell in cells:
        for checkpoint in PROXY_CHECKPOINTS:
            values = cell.proxy_values[checkpoint].reshape(-1)
            mean = float(np.mean(values))
            sem = float(np.std(values, ddof=1) / math.sqrt(len(values)))
            bound = finite_proxy_bound(cell.m, cell.H, cell.rho_action, checkpoint)
            rows.append(
                {
                    "phase": cell.phase,
                    "n": cell.n,
                    "m": cell.m,
                    "H": cell.H,
                    "checkpoint": checkpoint,
                    "rho_action": repr(cell.rho_action),
                    "mean_cumulative_proxy": repr(mean),
                    "sem_cumulative_proxy": repr(sem),
                    "upper95_cumulative_proxy": repr(mean + 1.96 * sem),
                    "finite_hellinger_bound": repr(bound),
                    "upper95_below_bound": bool(mean + 1.96 * sem <= bound),
                    "observations": len(values),
                }
            )
    return rows


def run_fixed_phases() -> tuple[list[FixedCell], list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    cells: list[FixedCell] = []
    for m in TYPE_M:
        for H in TYPE_H:
            cells.append(simulate_fixed_cell("type_horizon", TYPE_N, m, H))
    for n in POP_N:
        cells.append(simulate_fixed_cell("population", n, POP_M, POP_H))

    raw_rows: list[dict[str, object]] = []
    summary_rows = [fixed_cell_summary(cell) for cell in cells]
    for cell in cells:
        restricted = cell.restricted
        for seed_index, seed in enumerate(CONFIRMATORY_SEEDS):
            for agent in range(cell.n):
                raw_rows.append(
                    {
                        "phase": cell.phase,
                        "n": cell.n,
                        "m": cell.m,
                        "H": cell.H,
                        "seed": seed,
                        "agent": agent,
                        "true_type": int(cell.true_types[seed_index, agent]),
                        "first_episode": repr(float(cell.first_episode[seed_index, agent])),
                        "event": bool(cell.event[seed_index, agent]),
                        "restricted_first_episode": repr(float(restricted[seed_index, agent])),
                        "final_true_mass": repr(float(cell.final_mass[seed_index, agent])),
                        "proxy_512": repr(float(cell.proxy_values[512][seed_index, agent])),
                        "proxy_1024": repr(float(cell.proxy_values[1024][seed_index, agent])),
                        "proxy_2048": repr(float(cell.proxy_values[2048][seed_index, agent])),
                        "rho_action": repr(cell.rho_action),
                        "rho_global": repr(cell.rho_global),
                    }
                )

    type_cells = [cell for cell in cells if cell.phase == "type_horizon"]
    population_cells = [cell for cell in cells if cell.phase == "population"]
    type_fit, type_slope_ci = bootstrap_cell_fit(type_cells, "type")
    population_fit, population_slope_ci = bootstrap_cell_fit(population_cells, "population")
    original_fit, original_slope_ci = bootstrap_cell_fit(population_cells, "original")

    turn_ratios: dict[str, float] = {}
    for m in TYPE_M:
        equivalents = [
            cell.H * float(np.mean(cell.restricted))
            for cell in type_cells
            if cell.m == m
        ]
        turn_ratios[str(m)] = float(max(equivalents) / min(equivalents))

    max_type_censor = max(1.0 - float(np.mean(cell.event)) for cell in type_cells)
    max_population_censor = max(1.0 - float(np.mean(np.all(cell.event, axis=1))) for cell in population_cells)
    proxy = proxy_rows(type_cells)
    proxy_bound_pass = all(bool(row["upper95_below_bound"]) for row in proxy)
    increments: dict[str, float] = {}
    for cell in type_cells:
        mean_1024 = float(np.mean(cell.proxy_values[1024]))
        mean_2048 = float(np.mean(cell.proxy_values[2048]))
        increment = (mean_2048 - mean_1024) / max(mean_2048, 1e-15)
        increments[f"m{cell.m}_H{cell.H}"] = float(increment)
    max_increment = max(increments.values())

    type_gates = {
        "r_squared": type_fit.r_squared >= 0.9,
        "bootstrap_slope_ci_low_positive": type_slope_ci[0] > 0.0,
        "censoring": max_type_censor <= 0.01,
        "turn_equivalent_ratio": max(turn_ratios.values()) <= 1.35,
    }
    population_gates = {
        "r_squared": population_fit.r_squared >= 0.9,
        "bootstrap_slope_ci_low_positive": population_slope_ci[0] > 0.0,
        "censoring": max_population_censor <= 0.01,
        "corrected_advantage": population_fit.r_squared - original_fit.r_squared >= 0.1,
    }
    proxy_gates = {
        "all_upper95_below_bound": proxy_bound_pass,
        "relative_increment": max_increment <= 0.02,
    }
    results = {
        "type_horizon": {
            "fit": type_fit.as_dict(),
            "slope_ci95": type_slope_ci,
            "max_censoring_fraction": max_type_censor,
            "turn_equivalent_ratios": turn_ratios,
            "gates": type_gates,
            "passed": all(type_gates.values()),
        },
        "population": {
            "corrected_fit": population_fit.as_dict(),
            "corrected_slope_ci95": population_slope_ci,
            "original_linear_n_fit": original_fit.as_dict(),
            "original_linear_n_slope_ci95": original_slope_ci,
            "r_squared_advantage": population_fit.r_squared - original_fit.r_squared,
            "max_censoring_fraction": max_population_censor,
            "gates": population_gates,
            "passed": all(population_gates.values()),
        },
        "K_independent_proxy": {
            "max_relative_increment_1024_to_2048": max_increment,
            "relative_increments": increments,
            "gates": proxy_gates,
            "passed": all(proxy_gates.values()),
        },
    }
    return cells, raw_rows, summary_rows, {"proxy_rows": proxy, "results": results}


def run_adaptive() -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    raw_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    for m in ADAPTIVE_M:
        parameters = nested_parameters(m)
        for H in ADAPTIVE_H:
            planner = AnalyticPlanner(ADAPTIVE_N, parameters, beta=0.25)
            rho_global, _ = rho_hat_from_lookup(planner.lookup)
            half = ADAPTIVE_MAX_EPISODES // 2
            seed_records: list[dict[str, object]] = []
            per_agent_events: list[bool] = []
            per_agent_error_end: list[float] = []
            per_agent_proxy_half: list[float] = []
            per_agent_proxy_end: list[float] = []
            for seed in ADAPTIVE_SEEDS:
                rng = rng_for(seed, 404, ADAPTIVE_N, m, H)
                true_types = rng.integers(0, m, size=ADAPTIVE_N)
                uniforms = rng.random((ADAPTIVE_MAX_EPISODES, ADAPTIVE_N))
                noises = rng.standard_normal((ADAPTIVE_MAX_EPISODES, ADAPTIVE_N))
                log_posterior = np.full((ADAPTIVE_N, m), -math.log(m), dtype=float)
                first = np.full(ADAPTIVE_N, ADAPTIVE_MAX_EPISODES + 1.0, dtype=float)
                event = np.zeros(ADAPTIVE_N, dtype=bool)
                cumulative_proxy = np.zeros(ADAPTIVE_N, dtype=float)
                proxy_half = np.zeros(ADAPTIVE_N, dtype=float)
                error_end = np.ones(ADAPTIVE_N, dtype=float)
                actions: set[int] = set()
                for episode in range(1, ADAPTIVE_MAX_EPISODES + 1):
                    posterior = stable_posterior(log_posterior)
                    mass_before = posterior[np.arange(ADAPTIVE_N), true_types]
                    cumulative_proxy += H * (1.0 - mass_before)
                    sampled_types = sample_marginals(posterior, uniforms[episode - 1])
                    action_index = planner.plan_types(sampled_types)
                    actions.add(action_index)
                    digits = planner.grid.profile_digits(action_index)
                    total = int(np.sum(digits))
                    means = np.stack(
                        [planner.lookup[:, int(digits[agent]), total] for agent in range(ADAPTIVE_N)],
                        axis=0,
                    )
                    observations = means[np.arange(ADAPTIVE_N), true_types] + (SIGMA / math.sqrt(H)) * noises[episode - 1]
                    residual = observations[:, None] - means
                    log_posterior += -0.5 * H * (residual / SIGMA) ** 2
                    posterior_after = stable_posterior(log_posterior)
                    mass_after = posterior_after[np.arange(ADAPTIVE_N), true_types]
                    newly = (~event) & (mass_after > THRESHOLD)
                    first[newly] = episode
                    event[newly] = True
                    if episode == half:
                        proxy_half = cumulative_proxy.copy()
                    if episode == ADAPTIVE_MAX_EPISODES:
                        error_end = 1.0 - mass_before
                per_agent_events.extend(event.tolist())
                per_agent_error_end.extend(error_end.tolist())
                per_agent_proxy_half.extend(proxy_half.tolist())
                per_agent_proxy_end.extend(cumulative_proxy.tolist())
                record = {
                    "n": ADAPTIVE_N,
                    "m": m,
                    "H": H,
                    "seed": seed,
                    "mean_restricted_agent_first_episode": repr(float(np.mean(first))),
                    "all_agent_restricted_first_episode": repr(float(np.max(first))),
                    "censored_agents": int(ADAPTIVE_N - np.count_nonzero(event)),
                    "mean_error_final_preupdate": repr(float(np.mean(error_end))),
                    "mean_proxy_half": repr(float(np.mean(proxy_half))),
                    "mean_proxy_end": repr(float(np.mean(cumulative_proxy))),
                    "unique_actions": len(actions),
                    "rho_global": repr(float(rho_global)),
                }
                raw_rows.append(record)
                seed_records.append(record)

            errors = np.asarray(per_agent_error_end, dtype=float)
            proxy_half_array = np.asarray(per_agent_proxy_half, dtype=float)
            proxy_end_array = np.asarray(per_agent_proxy_end, dtype=float)
            mean_error = float(np.mean(errors))
            sem_error = float(np.std(errors, ddof=1) / math.sqrt(len(errors)))
            upper_error = mean_error + 1.96 * sem_error
            bound = error_bound(m, H, float(rho_global), ADAPTIVE_MAX_EPISODES)
            mean_half = float(np.mean(proxy_half_array))
            mean_end = float(np.mean(proxy_end_array))
            relative_increment = (mean_end - mean_half) / max(mean_end, 1e-15)
            censoring = 1.0 - float(np.mean(per_agent_events))
            summary_rows.append(
                {
                    "n": ADAPTIVE_N,
                    "m": m,
                    "H": H,
                    "seeds": len(ADAPTIVE_SEEDS),
                    "rho_global": repr(float(rho_global)),
                    "mean_error_final_preupdate": repr(mean_error),
                    "sem_error_final_preupdate": repr(sem_error),
                    "upper95_error_final_preupdate": repr(upper_error),
                    "global_rho_error_bound": repr(bound),
                    "upper95_below_bound": bool(upper_error <= bound),
                    "censoring_fraction_agents": repr(censoring),
                    "mean_proxy_half": repr(mean_half),
                    "mean_proxy_end": repr(mean_end),
                    "relative_proxy_increment": repr(relative_increment),
                }
            )

    max_censor = max(float(row["censoring_fraction_agents"]) for row in summary_rows)
    all_bounds = all(bool(row["upper95_below_bound"]) for row in summary_rows)
    max_increment = max(float(row["relative_proxy_increment"]) for row in summary_rows)
    gates = {
        "censoring": max_censor <= 0.05,
        "all_upper95_errors_below_global_bound": all_bounds,
        "relative_proxy_increment": max_increment <= 0.05,
    }
    result = {
        "max_censoring_fraction": max_censor,
        "max_relative_proxy_increment": max_increment,
        "gates": gates,
        "passed": all(gates.values()),
    }
    return raw_rows, summary_rows, result


def markdown_table(rows: list[dict[str, object]], fields: list[str]) -> list[str]:
    lines = ["| " + " | ".join(fields) + " |", "|" + "|".join("---" for _ in fields) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(row[field]) for field in fields) + " |")
    return lines


def write_report(
    results: dict[str, object],
    affinity_rows: list[dict[str, object]],
    fixed_summary: list[dict[str, object]],
    adaptive_summary: list[dict[str, object]],
) -> None:
    gate_rows = []
    for gate, payload in results["gates"].items():
        gate_rows.append({"gate": gate, "passed": payload["passed"], "details": json.dumps(payload, sort_keys=True)})
    lines = [
        "# HP-SPGG Claim B v3 — Confirmatory Results",
        "",
        f"Overall locked decision: **{'SUPPORTED' if results['claim_b_v3_supported'] else 'UNSUPPORTED'}**.",
        "",
        f"Preregistration JSON SHA-256: `{PREREG_SHA256}`.",
        f"Preregistration Markdown SHA-256: `{PREREG_MD_SHA256}`.",
        "",
        "The original `(n+1) log(m)/(rho H)` formula is not relabeled as supported. The tested claim is the corrected per-agent Hellinger-contraction statement plus a `log(n)` simultaneous-agent term.",
        "",
        "## Locked gate disposition",
        "",
        *markdown_table(gate_rows, ["gate", "passed", "details"]),
        "",
        "## Hellinger affinity core",
        "",
        *markdown_table(
            affinity_rows,
            [
                "gap",
                "target_information",
                "turns",
                "x_exact_information",
                "empirical_mean_root_lr",
                "theoretical_affinity_product",
                "standardized_error",
            ],
        ),
        "",
        "## Fixed-channel cell summaries",
        "",
        *markdown_table(
            fixed_summary,
            [
                "phase",
                "n",
                "m",
                "H",
                "rho_action",
                "restricted_mean_per_agent_episode",
                "restricted_mean_all_agent_episode",
                "censoring_fraction_agents",
                "censoring_fraction_seeds",
            ],
        ),
        "",
        "## Adaptive PACT robustness",
        "",
        *markdown_table(
            adaptive_summary,
            [
                "n",
                "m",
                "H",
                "rho_global",
                "upper95_error_final_preupdate",
                "global_rho_error_bound",
                "censoring_fraction_agents",
                "relative_proxy_increment",
            ],
        ),
        "",
        "## Complete machine-readable result",
        "",
        "```json",
        json.dumps(results, indent=2),
        "```",
        "",
        "## Interpretation boundary",
        "",
        "Passing supports the stochastic outcome-channel mechanism used by Proposition `prop:tid-collapse`: exact Hellinger root-odds contraction, a K-independent cumulative type-error proxy, inverse-H operational concentration, and logarithmic simultaneous-agent growth. It is not evidence for the retired linear-n formula, and it does not turn an upper bound into an exact equality.",
    ]
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="replace prior v3 outcome files, never preregistration files")
    args = parser.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if sha256(PREREG) != PREREG_SHA256 or sha256(PREREG_MD) != PREREG_MD_SHA256:
        raise AssertionError("locked preregistration hash mismatch")
    existing = [path for path in RESULT_FILES if path.exists()]
    if existing and not args.force:
        raise FileExistsError(f"confirmatory outcomes already exist: {existing[0]}; use --force only for exact reruns")
    for path in existing:
        path.unlink()

    affinity_batches, affinity_summary, affinity_result = run_affinity_core()
    fixed_cells, fixed_raw, fixed_summary, fixed_payload = run_fixed_phases()
    del fixed_cells
    adaptive_raw, adaptive_summary, adaptive_result = run_adaptive()

    write_csv(AFFINITY_BATCH_OUT, affinity_batches)
    write_csv(AFFINITY_SUMMARY_OUT, affinity_summary)
    write_csv(FIXED_RAW_OUT, fixed_raw)
    write_csv(FIXED_SUMMARY_OUT, fixed_summary)
    write_csv(PROXY_OUT, fixed_payload["proxy_rows"])
    write_csv(ADAPTIVE_RAW_OUT, adaptive_raw)
    write_csv(ADAPTIVE_SUMMARY_OUT, adaptive_summary)

    gate_results = {
        "G1_affinity_core": affinity_result,
        "G2_type_horizon": fixed_payload["results"]["type_horizon"],
        "G3_population": fixed_payload["results"]["population"],
        "G4_K_independent_proxy": fixed_payload["results"]["K_independent_proxy"],
        "G5_adaptive_robustness": adaptive_result,
    }
    supported = all(bool(payload["passed"]) for payload in gate_results.values())
    results: dict[str, object] = {
        "status": "supported" if supported else "unsupported",
        "claim_b_v3_supported": supported,
        "original_linear_n_formula_supported": False,
        "original_linear_n_formula_disposition": "retired as inconsistent with the current per-agent proposition",
        "preregistration_sha256": PREREG_SHA256,
        "preregistration_markdown_sha256": PREREG_MD_SHA256,
        "provider_calls": 0,
        "gates": gate_results,
        "row_counts": {
            "affinity_batches": len(affinity_batches),
            "affinity_summary": len(affinity_summary),
            "fixed_agent_results": len(fixed_raw),
            "fixed_cell_summary": len(fixed_summary),
            "proxy_checkpoints": len(fixed_payload["proxy_rows"]),
            "adaptive_seed_results": len(adaptive_raw),
            "adaptive_cell_summary": len(adaptive_summary),
        },
    }
    RESULTS_OUT.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    write_report(results, affinity_summary, fixed_summary, adaptive_summary)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
