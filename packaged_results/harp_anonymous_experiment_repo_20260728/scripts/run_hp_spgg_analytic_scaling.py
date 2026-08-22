"""Run additive zero-provider HP-SPGG analytic population/library scaling sweeps."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_hpgg.analytic_scaling import (  # noqa: E402
    ACTIONS,
    JOINT_BYTE_CAP,
    JOINT_UPDATE_SECONDS_CAP,
    PLANNER_EVALUATION_CAP,
    RHO_THRESHOLD,
    SIGMA,
    AnalyticPlanner,
    JointProbe,
    TypeLibrary,
    cell_seed_stream,
    dgp_probes,
    first_passage,
    joint_marginals,
    local_likelihoods,
    median_first_passage,
    posterior_true_mass,
    probe_joint_update,
    rho_hat_from_lookup,
    sample_marginals,
    synthesize_type_library,
    update_explicit_joint,
    update_factored,
)


OUT_DIR = ROOT / "analysis" / "hp_spgg_analytic_scaling"
NPZ_DIR = OUT_DIR / "npz"
SUMMARY_OUT = OUT_DIR / "scaling_summary.csv"
PARITY_OUT = OUT_DIR / "scaling_parity.csv"
MANIFEST_OUT = OUT_DIR / "manifest_scaling.json"
PROBES_OUT = OUT_DIR / "dgp_probes.csv"
LIBRARIES_OUT = OUT_DIR / "type_libraries.csv"
REPORT_OUT = OUT_DIR / "scaling_run_report.md"
K = 50
SEEDS = tuple(range(1000, 1010))
BETA = 0.25
H = 1
METHODS = ("oracle", "pact", "pact_plus", "joint_psrl_uniform", "psrl_notype")
FACTORED_METHODS = {"pact", "pact_plus", "psrl_notype"}
BURN_IN_METHODS = {"pact", "pact_plus", "joint_psrl_uniform"}
SWEEPS = {
    "s1_population_m4": [(n, 4) for n in range(2, 11)],
    "s2_library_n3": [(3, m) for m in (4, 8, 16)],
    "s3_frontier_m16": [(n, 16) for n in range(2, 9)],
}
SUMMARY_FIELDS = [
    "sweep", "n", "m", "method", "seeds", "K", "beta", "rho_hat",
    "final_regret_mean", "final_regret_sem", "median_burn_in_all_agents",
    "burn_in_censored_seeds", "median_agent_burn_in", "storage_entries",
    "storage_theoretical_bytes", "storage_allocated_bytes", "planner_ms_mean",
    "planner_ms_sem", "update_us_per_event_mean", "update_us_per_event_sem",
    "planner_feasible", "joint_feasible", "feasible", "cap_rule",
]
PARITY_FIELDS = [
    "sweep", "n", "m", "seeds", "pact_minus_joint_mean", "pact_minus_joint_sem",
    "ci95_low", "ci95_high", "ci_covers_zero", "max_abs_trajectory_gap",
    "action_mismatch_count", "joint_feasible",
]
T95_DF9 = 2.2621571627409915


@dataclass(frozen=True)
class CellFeasibility:
    planner_feasible: bool
    joint_probe: JointProbe
    rho_hat: float
    rho_witness: dict[str, object]


class CellRuntimeExceeded(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def deterministic_savez(path: Path, payload: dict[str, object]) -> None:
    """Write NPZ with fixed entry ordering/timestamps for byte-stable replay."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for key in sorted(payload):
            array = np.asanyarray(payload[key])
            buffer = io.BytesIO()
            np.lib.format.write_array(buffer, array, allow_pickle=False)
            info = zipfile.ZipInfo(f"{key}.npy", date_time=(2026, 7, 25, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, buffer.getvalue())


def load_npz(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as payload:
        return {key: np.array(payload[key], copy=True) for key in payload.files}


def npz_path(sweep: str, n: int, m: int, method: str, seed: int) -> Path:
    return NPZ_DIR / sweep / f"n{n:02d}_m{m:02d}" / f"{method}_seed{seed}.npz"


def synthetic_library_rows(libraries: dict[int, TypeLibrary], rho_by_m: dict[int, float]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for m, library in sorted(libraries.items()):
        for index, (label, parameters) in enumerate(zip(library.labels, library.parameters, strict=True)):
            rows.append(
                {
                    "m": m,
                    "type_index": index,
                    "label": label,
                    "target_contribution": repr(float(parameters[0])),
                    "cooperation_weight": repr(float(parameters[1])),
                    "self_interest_weight": repr(float(parameters[2])),
                    "fairness_weight": repr(float(parameters[3])),
                    "synthesis": library.synthesis,
                    "initial_rho_hat": "" if library.initial_rho_hat is None else repr(library.initial_rho_hat),
                    "respaced": library.respaced,
                    "rho_hat_min_across_cells": repr(rho_by_m[m]),
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def make_infeasible_payload(
    *,
    sweep: str,
    n: int,
    m: int,
    method: str,
    seed: int,
    rho_hat: float,
    planner_feasible: bool,
    joint_feasible: bool,
    cap_rule: str,
    storage_entries: int,
    storage_bytes: int,
) -> dict[str, object]:
    return {
        "action_indices": np.full(K, -1, dtype=np.int64),
        "beta": np.asarray(BETA),
        "burn_in_all_agents": np.asarray(np.nan),
        "burn_in_per_agent": np.full(n, np.nan),
        "cap_rule": np.asarray(cap_rule),
        "cumulative_regret": np.full(K, np.nan),
        "feasible": np.asarray(False),
        "instant_regret": np.full(K, np.nan),
        "joint_feasible": np.asarray(joint_feasible),
        "K": np.asarray(K),
        "m": np.asarray(m),
        "method": np.asarray(method),
        "n": np.asarray(n),
        "planner_feasible": np.asarray(planner_feasible),
        "planner_cache_hit": np.zeros(K, dtype=bool),
        "planner_ms": np.full(K, np.nan),
        "posterior_true_mass": np.full((K, n), np.nan),
        "rho_hat": np.asarray(rho_hat),
        "seed": np.asarray(seed),
        "storage_allocated_bytes": np.asarray(0),
        "storage_entries": np.asarray(storage_entries),
        "storage_theoretical_bytes": np.asarray(storage_bytes),
        "sweep": np.asarray(sweep),
        "true_types": np.full(n, -1, dtype=np.int64),
        "update_us_per_event": np.full(K, np.nan),
        "welfare": np.full(K, np.nan),
    }


def run_method_seed(
    *,
    planner: AnalyticPlanner,
    method: str,
    seed: int,
    rho_hat: float,
    sweep: str,
    joint_feasible: bool,
    cap_rule: str,
    max_cell_deadline: float,
) -> dict[str, object]:
    n, m = planner.n, planner.m
    true_types, uniforms = cell_seed_stream(seed, n, m, K)
    posterior = np.full((n, m), 1.0 / m, dtype=float)
    joint: np.ndarray | None = None
    if method == "joint_psrl_uniform":
        if not joint_feasible:
            return make_infeasible_payload(
                sweep=sweep,
                n=n,
                m=m,
                method=method,
                seed=seed,
                rho_hat=rho_hat,
                planner_feasible=True,
                joint_feasible=False,
                cap_rule=cap_rule,
                storage_entries=m**n,
                storage_bytes=(m**n) * 8,
            )
        joint = np.full(m**n, 1.0 / (m**n), dtype=float)
        posterior = joint_marginals(joint, n, m)

    instant_regret = np.zeros(K, dtype=float)
    cumulative_regret = np.zeros(K, dtype=float)
    welfare = np.zeros(K, dtype=float)
    action_indices = np.zeros(K, dtype=np.int64)
    posterior_mass = np.full((K, n), np.nan, dtype=float)
    planner_ms = np.zeros(K, dtype=float)
    update_us = np.zeros(K, dtype=float)
    planner_cache_hit = np.zeros(K, dtype=bool)

    oracle_cache_before = planner.type_cache_hits
    oracle_start = time.perf_counter_ns()
    cached_oracle_action = planner.plan_types(true_types)
    cached_oracle_ms = (time.perf_counter_ns() - oracle_start) / 1e6
    cached_oracle_welfare = planner.welfare(true_types, cached_oracle_action)
    del oracle_cache_before

    for episode in range(K):
        if time.perf_counter() > max_cell_deadline:
            raise CellRuntimeExceeded(f"n={n}, m={m} exceeded the 30-minute cell cap")
        planner_start = time.perf_counter_ns()
        cache_hits_before = planner.type_cache_hits
        if method == "oracle":
            action = cached_oracle_action
        elif method == "pact":
            sampled = sample_marginals(posterior, uniforms[episode])
            action = planner.plan_types(sampled)
        elif method == "pact_plus":
            action = planner.plan_posterior(posterior, bonus=True)
        elif method == "joint_psrl_uniform":
            sampled = sample_marginals(posterior, uniforms[episode])
            action = planner.plan_types(sampled)
        elif method == "psrl_notype":
            uniform_posterior = np.full((n, m), 1.0 / m, dtype=float)
            sampled = sample_marginals(uniform_posterior, uniforms[episode])
            action = planner.plan_types(sampled)
        else:
            raise ValueError(method)
        planner_ms[episode] = (time.perf_counter_ns() - planner_start) / 1e6
        planner_cache_hit[episode] = planner.type_cache_hits > cache_hits_before
        if method == "oracle":
            planner_ms[episode] = cached_oracle_ms
            planner_cache_hit[episode] = episode > 0

        rewards = planner.rewards(true_types, action)
        chosen_welfare = float(rewards.sum())
        instant_regret[episode] = max(0.0, cached_oracle_welfare - chosen_welfare)
        cumulative_regret[episode] = instant_regret[: episode + 1].sum()
        welfare[episode] = chosen_welfare
        action_indices[episode] = action

        digits = planner.grid.profile_digits(action)
        likelihoods = local_likelihoods(planner.lookup, digits, int(digits.sum()), rewards, sigma=SIGMA)
        if method in {"pact", "pact_plus"}:
            update_start = time.perf_counter_ns()
            update_factored(posterior, likelihoods)
            update_us[episode] = (time.perf_counter_ns() - update_start) / 1e3 / n
            posterior_mass[episode] = posterior_true_mass(posterior, true_types)
        elif method == "joint_psrl_uniform":
            assert joint is not None
            joint, marginals, elapsed = update_explicit_joint(joint, likelihoods, return_marginals=True)
            assert marginals is not None
            posterior = marginals
            update_us[episode] = elapsed * 1e6 / n
            posterior_mass[episode] = posterior_true_mass(posterior, true_types)
        elif method == "psrl_notype":
            posterior_mass[episode] = 1.0 / m

    if method in BURN_IN_METHODS:
        per_agent_burn, all_burn = first_passage(posterior_mass)
    else:
        per_agent_burn, all_burn = np.full(n, np.nan), math.nan

    if method == "joint_psrl_uniform":
        storage_entries = m**n
        storage_bytes = storage_entries * 8
        allocated_bytes = int(joint.nbytes if joint is not None else 0)
    elif method in FACTORED_METHODS:
        storage_entries = n * m
        storage_bytes = storage_entries * 8
        allocated_bytes = int(posterior.nbytes)
    else:
        storage_entries = 0
        storage_bytes = 0
        allocated_bytes = 0

    return {
        "action_indices": action_indices,
        "beta": np.asarray(BETA),
        "burn_in_all_agents": np.asarray(all_burn),
        "burn_in_per_agent": per_agent_burn,
        "cap_rule": np.asarray("none"),
        "cumulative_regret": cumulative_regret,
        "feasible": np.asarray(True),
        "instant_regret": instant_regret,
        "joint_feasible": np.asarray(joint_feasible),
        "K": np.asarray(K),
        "m": np.asarray(m),
        "method": np.asarray(method),
        "n": np.asarray(n),
        "planner_feasible": np.asarray(True),
        "planner_ms": planner_ms,
        "planner_cache_hit": planner_cache_hit,
        "posterior_true_mass": posterior_mass,
        "rho_hat": np.asarray(rho_hat),
        "seed": np.asarray(seed),
        "storage_allocated_bytes": np.asarray(allocated_bytes),
        "storage_entries": np.asarray(storage_entries),
        "storage_theoretical_bytes": np.asarray(storage_bytes),
        "sweep": np.asarray(sweep),
        "true_types": true_types,
        "update_us_per_event": update_us,
        "welfare": welfare,
    }


def first_joint_likelihoods(planner: AnalyticPlanner, seed: int) -> np.ndarray:
    true_types, uniforms = cell_seed_stream(seed, planner.n, planner.m, K)
    uniform = np.full((planner.n, planner.m), 1.0 / planner.m, dtype=float)
    sampled = sample_marginals(uniform, uniforms[0])
    action = planner.plan_types(sampled)
    rewards = planner.rewards(true_types, action)
    digits = planner.grid.profile_digits(action)
    return local_likelihoods(planner.lookup, digits, int(digits.sum()), rewards, sigma=SIGMA)


def cell_feasibility(planner: AnalyticPlanner, rho_hat: float, witness: dict[str, object]) -> CellFeasibility:
    if not planner.grid.planner_feasible:
        probe = JointProbe(False, "planner_evaluations_gt_2^24", None, 0, planner.m**planner.n, (planner.m**planner.n) * 8)
        return CellFeasibility(False, probe, rho_hat, witness)
    likelihoods = first_joint_likelihoods(planner, SEEDS[0])
    probe = probe_joint_update(planner.n, planner.m, likelihoods)
    return CellFeasibility(True, probe, rho_hat, witness)


def requested_methods(sweep: str) -> tuple[str, ...]:
    return METHODS


def payload_scientific_hash(payload: dict[str, np.ndarray]) -> str:
    digest = hashlib.sha256()
    for key in sorted(payload):
        if key in {"planner_ms", "planner_cache_hit", "update_us_per_event"}:
            continue
        digest.update(key.encode("utf-8"))
        digest.update(np.ascontiguousarray(payload[key]).tobytes())
    return digest.hexdigest()


def determinism_gate(
    planner: AnalyticPlanner,
    source_payload: dict[str, np.ndarray],
    deadline: float,
) -> dict[str, object]:
    replay = run_method_seed(
        planner=planner,
        method="pact",
        seed=SEEDS[0],
        rho_hat=float(source_payload["rho_hat"]),
        sweep="s1_population_m4",
        joint_feasible=True,
        cap_rule="none",
        max_cell_deadline=deadline,
    )
    replay_arrays = {key: np.asanyarray(value) for key, value in replay.items()}
    scientific_equal = payload_scientific_hash(source_payload) == payload_scientific_hash(replay_arrays)
    # Wall-clock arrays are physically non-deterministic.  Reuse the original
    # measured clocks to test byte-stable NPZ reconstruction of the full file.
    replay_arrays["planner_ms"] = np.array(source_payload["planner_ms"], copy=True)
    replay_arrays["planner_cache_hit"] = np.array(source_payload["planner_cache_hit"], copy=True)
    replay_arrays["update_us_per_event"] = np.array(source_payload["update_us_per_event"], copy=True)
    with io.BytesIO() as _:
        pass
    temp = OUT_DIR / ".determinism_replay.npz"
    deterministic_savez(temp, replay_arrays)
    source = npz_path("s1_population_m4", 3, 4, "pact", SEEDS[0])
    byte_equal = source.read_bytes() == temp.read_bytes()
    temp.unlink(missing_ok=True)
    return {
        "passed": bool(scientific_equal and byte_equal),
        "scientific_arrays_bitwise": bool(scientific_equal),
        "full_npz_reconstruction_bitwise": bool(byte_equal),
        "timing_policy": "original measured wall-clock arrays reused because physical clocks are nondeterministic",
        "source": source.relative_to(ROOT).as_posix(),
    }


def kernel_planner_regression(library: TypeLibrary) -> dict[str, object]:
    """Check the new memory-aware planner against retained n=3 tensor code."""
    from itertools import product

    from llm_hpgg.coordinator import CoordinatorState, expected_profile_scores, posterior_expected_profile_scores
    from llm_hpgg.environment import build_reward_tensor

    bundle = build_reward_tensor(n=3, backend="mixed", samples=1, seed=0, trap=False)
    planner = AnalyticPlanner(3, library.parameters, beta=BETA)
    reward_max_diff = 0.0
    for profile_index in range(planner.grid.profile_count):
        digits = planner.grid.profile_digits(profile_index)
        # Check every player/type entry, not only one symmetric row.
        for player in range(3):
            rewards = planner.lookup[:, digits[player], int(digits.sum())]
            expected = bundle.reward_tensor[player, :, profile_index]
            reward_max_diff = max(reward_max_diff, float(np.max(np.abs(rewards - expected))))
    sampled_actions_equal = True
    state = CoordinatorState.fresh(3, 4, bundle.reward_tensor, bundle.action_profiles, BETA)
    for combo in product(range(4), repeat=3):
        types = np.asarray(combo, dtype=int)
        old_action = int(np.argmax(expected_profile_scores(state, types, uncertainty_bonus=False)))
        if planner.plan_types(types) != old_action:
            sampled_actions_equal = False
            break
    posterior_actions_equal = True
    rng = np.random.default_rng(20260725)
    posterior_cases = [np.full((3, 4), 0.25)]
    posterior_cases.extend(rng.dirichlet(np.ones(4), size=3) for _ in range(5))
    for posterior in posterior_cases:
        state.posterior = np.asarray(posterior, dtype=float)
        old_action = int(np.argmax(posterior_expected_profile_scores(state, uncertainty_bonus=True)))
        if planner.plan_posterior(state.posterior, bonus=True) != old_action:
            posterior_actions_equal = False
            break
    return {
        "passed": bool(reward_max_diff <= 1e-12 and sampled_actions_equal and posterior_actions_equal),
        "max_reward_tensor_difference": reward_max_diff,
        "all_64_sampled_profile_actions_equal": sampled_actions_equal,
        "posterior_mean_bonus_actions_equal": posterior_actions_equal,
        "reference": "build_reward_tensor(n=3, backend=mixed, samples=1, seed=0)",
    }


def summarize_npzs() -> list[dict[str, object]]:
    # PACT and explicit Joint-PSRL are pathwise coupled and invoke the same
    # deterministic planner on the same sampled profile.  The shared exact
    # planner cache makes the later-executed joint call a cache hit; normalize
    # its timing arrays to the corresponding measured PACT calls so planner
    # cost is representation-neutral rather than execution-order dependent.
    for sweep, cells in SWEEPS.items():
        for n, m in cells:
            for seed in SEEDS:
                pact_path = npz_path(sweep, n, m, "pact", seed)
                joint_path = npz_path(sweep, n, m, "joint_psrl_uniform", seed)
                pact = load_npz(pact_path)
                joint = load_npz(joint_path)
                if bool(pact["feasible"]) and bool(joint["feasible"]):
                    if not np.array_equal(pact["action_indices"], joint["action_indices"]):
                        raise AssertionError(f"PACT/joint actions diverge before timing normalization: {sweep}, n={n}, m={m}, seed={seed}")
                    joint["planner_ms"] = np.array(pact["planner_ms"], copy=True)
                    joint["planner_cache_hit"] = np.array(pact["planner_cache_hit"], copy=True)
                    deterministic_savez(joint_path, joint)

    rows: list[dict[str, object]] = []
    for sweep, cells in SWEEPS.items():
        for n, m in cells:
            for method in requested_methods(sweep):
                payloads = [load_npz(npz_path(sweep, n, m, method, seed)) for seed in SEEDS]
                feasible = bool(payloads[0]["feasible"])
                final = np.asarray([payload["cumulative_regret"][-1] for payload in payloads], dtype=float)
                planner_values = np.concatenate([payload["planner_ms"] for payload in payloads])
                update_values = np.concatenate([payload["update_us_per_event"] for payload in payloads])
                burn_values = [float(payload["burn_in_all_agents"]) for payload in payloads]
                per_agent = np.concatenate([payload["burn_in_per_agent"] for payload in payloads])
                if feasible:
                    final_mean = float(np.mean(final))
                    final_sem = float(np.std(final, ddof=1) / math.sqrt(len(final)))
                    planner_mean = float(np.nanmean(planner_values))
                    planner_sem = float(np.nanstd(planner_values, ddof=1) / math.sqrt(np.isfinite(planner_values).sum()))
                    update_mean = float(np.nanmean(update_values))
                    update_sem = float(np.nanstd(update_values, ddof=1) / math.sqrt(np.isfinite(update_values).sum()))
                else:
                    final_mean = final_sem = planner_mean = planner_sem = update_mean = update_sem = math.nan
                burn_median, censored = median_first_passage(burn_values)
                agent_finite = per_agent[np.isfinite(per_agent)]
                agent_median = float(np.median(agent_finite)) if len(agent_finite) else math.nan
                rows.append(
                    {
                        "sweep": sweep,
                        "n": n,
                        "m": m,
                        "method": method,
                        "seeds": len(SEEDS),
                        "K": K,
                        "beta": BETA,
                        "rho_hat": repr(float(payloads[0]["rho_hat"])),
                        "final_regret_mean": repr(final_mean),
                        "final_regret_sem": repr(final_sem),
                        "median_burn_in_all_agents": repr(burn_median),
                        "burn_in_censored_seeds": censored,
                        "median_agent_burn_in": repr(agent_median),
                        "storage_entries": int(payloads[0]["storage_entries"]),
                        "storage_theoretical_bytes": int(payloads[0]["storage_theoretical_bytes"]),
                        "storage_allocated_bytes": int(payloads[0]["storage_allocated_bytes"]),
                        "planner_ms_mean": repr(planner_mean),
                        "planner_ms_sem": repr(planner_sem),
                        "update_us_per_event_mean": repr(update_mean),
                        "update_us_per_event_sem": repr(update_sem),
                        "planner_feasible": bool(payloads[0]["planner_feasible"]),
                        "joint_feasible": bool(payloads[0]["joint_feasible"]),
                        "feasible": feasible,
                        "cap_rule": str(payloads[0]["cap_rule"]),
                    }
                )
    write_csv(SUMMARY_OUT, rows, SUMMARY_FIELDS)
    return rows


def summarize_parity() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for sweep, cells in SWEEPS.items():
        for n, m in cells:
            pact_payloads = [load_npz(npz_path(sweep, n, m, "pact", seed)) for seed in SEEDS]
            joint_payloads = [load_npz(npz_path(sweep, n, m, "joint_psrl_uniform", seed)) for seed in SEEDS]
            feasible = bool(joint_payloads[0]["feasible"])
            if feasible:
                gaps = np.asarray(
                    [
                        float(pact["cumulative_regret"][-1] - joint["cumulative_regret"][-1])
                        for pact, joint in zip(pact_payloads, joint_payloads, strict=True)
                    ]
                )
                mean = float(gaps.mean())
                sem = float(gaps.std(ddof=1) / math.sqrt(len(gaps)))
                low = mean - T95_DF9 * sem
                high = mean + T95_DF9 * sem
                max_gap = max(
                    float(np.max(np.abs(pact["cumulative_regret"] - joint["cumulative_regret"])))
                    for pact, joint in zip(pact_payloads, joint_payloads, strict=True)
                )
                action_mismatches = sum(
                    int(np.count_nonzero(pact["action_indices"] != joint["action_indices"]))
                    for pact, joint in zip(pact_payloads, joint_payloads, strict=True)
                )
            else:
                mean = sem = low = high = max_gap = math.nan
                action_mismatches = 0
            rows.append(
                {
                    "sweep": sweep,
                    "n": n,
                    "m": m,
                    "seeds": len(SEEDS),
                    "pact_minus_joint_mean": repr(mean),
                    "pact_minus_joint_sem": repr(sem),
                    "ci95_low": repr(low),
                    "ci95_high": repr(high),
                    "ci_covers_zero": bool(feasible and low <= 0.0 <= high),
                    "max_abs_trajectory_gap": repr(max_gap),
                    "action_mismatch_count": action_mismatches,
                    "joint_feasible": feasible,
                }
            )
    write_csv(PARITY_OUT, rows, PARITY_FIELDS)
    return rows


def run_report(
    *,
    summary_rows: list[dict[str, object]],
    manifest: dict[str, object],
    total_seconds: float,
) -> None:
    frontier = manifest["joint_feasibility_frontier"]
    lines = [
        "# HP-SPGG Analytic Scaling Run Report",
        "",
        f"Generated UTC: {manifest['generated_utc']}.",
        f"NPZ artifact wall-clock span: {total_seconds:.3f} seconds (a lower bound when reconstructed in a later summarize pass).",
        "Provider calls: 0.",
        "",
        "## Completion",
        "",
        f"- Requested sweep cells: {sum(len(cells) for cells in SWEEPS.values())}.",
        f"- Unique $(n,m)$ cells: {len({cell for cells in SWEEPS.values() for cell in cells})}.",
        f"- Cell-method summaries: {len(summary_rows)}.",
        f"- NPZ files: {sum(str(record['path']).endswith('.npz') for record in manifest['artifacts'])}.",
        f"- Planner action count read from substrate: {manifest['action_value_count']}.",
        f"- Joint frontier for S3: {frontier}.",
        "",
        "## Type separation",
        "",
        "| m | rho_hat | threshold applies | synthesis |",
        "|---:|---:|---|---|",
    ]
    for m, record in manifest["type_libraries"].items():
        lines.append(
            f"| {m} | {record['rho_hat_min_across_cells']:.9g} | {int(m) > 4} | {record['synthesis']} |"
        )
    parity_rows = []
    if PARITY_OUT.exists():
        with PARITY_OUT.open(newline="", encoding="utf-8") as handle:
            parity_rows = list(csv.DictReader(handle))
    lines.extend(
        [
            "",
            "## Factored / explicit-joint parity",
            "",
            "| sweep | n | m | joint feasible | PACT-Joint mean | 95% CI | max trajectory gap | action mismatches |",
            "|---|---:|---:|---|---:|---:|---:|---:|",
        ]
    )
    for row in parity_rows:
        lines.append(
            f"| {row['sweep']} | {row['n']} | {row['m']} | {row['joint_feasible']} | "
            f"{row['pact_minus_joint_mean']} | [{row['ci95_low']}, {row['ci95_high']}] | "
            f"{row['max_abs_trajectory_gap']} | {row['action_mismatch_count']} |"
        )
    lines.extend(
        [
            "",
            "## Feasibility events",
            "",
            "| sweep | n | m | method | feasible | rule |",
            "|---|---:|---:|---|---|---|",
        ]
    )
    for row in summary_rows:
        if row["method"] == "joint_psrl_uniform" or not bool(row["planner_feasible"]):
            lines.append(
                f"| {row['sweep']} | {row['n']} | {row['m']} | {row['method']} | "
                f"{row['feasible']} | {row['cap_rule']} |"
            )
    lines.extend(
        [
            "",
            "## Correctness gates",
            "",
            "```json",
            json.dumps(manifest["correctness_gates"], indent=2),
            "```",
            "",
            "## Notes",
            "",
            "- The repository action grid has five values, so S1 n=10 enumerates 5^10=9,765,625 profiles, not 4^10.",
            "- Synthetic m=8 and m=16 libraries are re-spaced only after direct archetype interpolation fails rho_hat >= 1e-3.",
            "- The m=4 library is retained unchanged even though its empirical full-grid rho_hat is below the synthetic-library threshold.",
            "- Cells are additive; no existing experiment output or LaTeX file is modified.",
        ]
    )
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("run", "summarize", "all"), default="all")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--smoke", action="store_true", help="Run only n=2,m=4 and n=3,m=16 cells.")
    parser.add_argument("--max-cell-minutes", type=float, default=30.0)
    parser.add_argument("--seed-workers", type=int, default=2)
    args = parser.parse_args()

    started = time.perf_counter()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    libraries = {m: synthesize_type_library(m) for m in (4, 8, 16)}
    selected_sweeps = SWEEPS
    if args.smoke:
        selected_sweeps = {
            "s1_population_m4": [(2, 4), (3, 4)],
            "s2_library_n3": [(3, 16)],
        }

    probes: list[dict[str, object]] = []
    cell_records: dict[tuple[int, int], dict[str, object]] = {}
    unique_cells = sorted({cell for cells in selected_sweeps.values() for cell in cells})

    if args.stage in {"run", "all"}:
        if args.force:
            for sweep in selected_sweeps:
                shutil.rmtree(NPZ_DIR / sweep, ignore_errors=True)
        for n, m in unique_cells:
            print(f"CELL n={n} m={m} start", flush=True)
            cell_start = time.perf_counter()
            deadline = cell_start + args.max_cell_minutes * 60.0
            library = libraries[m]
            planner_grid_count = len(ACTIONS) ** n
            if planner_grid_count > PLANNER_EVALUATION_CAP:
                feasibility = CellFeasibility(
                    False,
                    JointProbe(False, "planner_evaluations_gt_2^24", None, 0, m**n, (m**n) * 8),
                    math.nan,
                    {},
                )
                planner = None
            else:
                planner = AnalyticPlanner(n, library.parameters, beta=BETA)
                rho_hat, witness = rho_hat_from_lookup(planner.lookup, sigma=SIGMA)
                feasibility = cell_feasibility(planner, rho_hat, witness)
            probe = dgp_probes(n, library, SEEDS[0])
            probes.append({"n": n, "m": m, **probe})
            cell_records[(n, m)] = {
                "planner_profiles": planner_grid_count,
                "planner_feasible": feasibility.planner_feasible,
                "rho_hat": feasibility.rho_hat,
                "rho_witness": feasibility.rho_witness,
                "joint_probe": feasibility.joint_probe.__dict__,
                "dgp_probe": probe,
                "planner_allocated_bytes": 0 if planner is None else planner.allocated_bytes,
            }
            for sweep, cells in selected_sweeps.items():
                if (n, m) not in cells:
                    continue
                for method in requested_methods(sweep):
                    pending = [
                        seed
                        for seed in SEEDS
                        if args.force or not npz_path(sweep, n, m, method, seed).exists()
                    ]
                    def run_pending_seed(seed: int) -> tuple[int, dict[str, object]]:
                        if not feasibility.planner_feasible or planner is None:
                            payload = make_infeasible_payload(
                                sweep=sweep,
                                n=n,
                                m=m,
                                method=method,
                                seed=seed,
                                rho_hat=feasibility.rho_hat,
                                planner_feasible=False,
                                joint_feasible=False,
                                cap_rule="planner_evaluations_gt_2^24",
                                storage_entries=(m**n if method == "joint_psrl_uniform" else n * m),
                                storage_bytes=(m**n if method == "joint_psrl_uniform" else n * m) * 8,
                            )
                        else:
                            joint_ok = feasibility.joint_probe.feasible
                            joint_rule = feasibility.joint_probe.rule
                            payload = run_method_seed(
                                planner=planner,
                                method=method,
                                seed=seed,
                                rho_hat=feasibility.rho_hat,
                                sweep=sweep,
                                joint_feasible=joint_ok,
                                cap_rule=joint_rule,
                                max_cell_deadline=deadline,
                            )
                        return seed, payload

                    with ThreadPoolExecutor(max_workers=max(1, args.seed_workers)) as executor:
                        futures = [executor.submit(run_pending_seed, seed) for seed in pending]
                        for future in as_completed(futures):
                            seed, payload = future.result()
                            deterministic_savez(npz_path(sweep, n, m, method, seed), payload)
            cell_records[(n, m)]["cell_wallclock_seconds"] = time.perf_counter() - cell_start
            print(
                f"CELL n={n} m={m} complete in {cell_records[(n, m)]['cell_wallclock_seconds']:.2f}s "
                f"joint={feasibility.joint_probe.feasible} rule={feasibility.joint_probe.rule}",
                flush=True,
            )

    if args.stage in {"summarize", "all"}:
        # Reconstruct cell metadata when summarizing an existing full run.
        if not cell_records:
            for n, m in sorted({cell for cells in SWEEPS.values() for cell in cells}):
                library = libraries[m]
                planner = AnalyticPlanner(n, library.parameters, beta=BETA)
                rho_hat, witness = rho_hat_from_lookup(planner.lookup, sigma=SIGMA)
                likelihoods = first_joint_likelihoods(planner, SEEDS[0])
                joint_probe = probe_joint_update(n, m, likelihoods)
                probe = dgp_probes(n, library, SEEDS[0])
                probes.append({"n": n, "m": m, **probe})
                cell_records[(n, m)] = {
                    "planner_profiles": planner.grid.profile_count,
                    "planner_feasible": True,
                    "rho_hat": rho_hat,
                    "rho_witness": witness,
                    "joint_probe": joint_probe.__dict__,
                    "dgp_probe": probe,
                    "planner_allocated_bytes": planner.allocated_bytes,
                }
                cell_paths = [
                    path
                    for sweep, cells in SWEEPS.items()
                    if (n, m) in cells
                    for path in (NPZ_DIR / sweep / f"n{n:02d}_m{m:02d}").glob("*.npz")
                ]
                if cell_paths:
                    timestamps = [path.stat().st_mtime for path in cell_paths]
                    cell_records[(n, m)]["npz_artifact_wallclock_span_seconds"] = max(timestamps) - min(timestamps)
        summary_rows = summarize_npzs()
        parity_rows = summarize_parity()
        write_csv(PROBES_OUT, probes, ["n", "m", "seed", "true_types", "pf_pass", "ti_pass", "rl_pass", "all_pass"])

        rho_by_m = {
            m: min(record["rho_hat"] for (n_value, m_value), record in cell_records.items() if m_value == m)
            for m in libraries
        }
        library_rows = synthetic_library_rows(libraries, rho_by_m)
        write_csv(
            LIBRARIES_OUT,
            library_rows,
            [
                "m", "type_index", "label", "target_contribution", "cooperation_weight",
                "self_interest_weight", "fairness_weight", "synthesis", "initial_rho_hat",
                "respaced", "rho_hat_min_across_cells",
            ],
        )

        # Correctness gates.
        gate_cell = (3, 4)
        pact_payloads = [load_npz(npz_path("s1_population_m4", *gate_cell, "pact", seed)) for seed in SEEDS]
        joint_payloads = [load_npz(npz_path("s1_population_m4", *gate_cell, "joint_psrl_uniform", seed)) for seed in SEEDS]
        action_equal = all(np.array_equal(p["action_indices"], j["action_indices"]) for p, j in zip(pact_payloads, joint_payloads, strict=True))
        regret_equal = all(np.allclose(p["cumulative_regret"], j["cumulative_regret"], atol=1e-8, rtol=0.0) for p, j in zip(pact_payloads, joint_payloads, strict=True))
        max_regret_diff = max(float(np.max(np.abs(p["cumulative_regret"] - j["cumulative_regret"]))) for p, j in zip(pact_payloads, joint_payloads, strict=True))
        oracle_max = 0.0
        no_type_r2: dict[str, float] = {}
        for sweep, cells in SWEEPS.items():
            for n, m in cells:
                oracle_payloads = [load_npz(npz_path(sweep, n, m, "oracle", seed)) for seed in SEEDS]
                if bool(oracle_payloads[0]["feasible"]):
                    oracle_max = max(oracle_max, max(float(np.nanmax(payload["cumulative_regret"])) for payload in oracle_payloads))
                no_type_payloads = [load_npz(npz_path(sweep, n, m, "psrl_notype", seed)) for seed in SEEDS]
                if bool(no_type_payloads[0]["feasible"]):
                    mean_trajectory = np.mean([payload["cumulative_regret"] for payload in no_type_payloads], axis=0)
                    from llm_hpgg.analytic_scaling import r_squared_linear

                    no_type_r2[f"{sweep}:n{n}:m{m}"] = r_squared_linear(mean_trajectory)
        min_r2 = min(no_type_r2.values())
        determinism = determinism_gate(
            AnalyticPlanner(3, libraries[4].parameters, beta=BETA),
            pact_payloads[0],
            time.perf_counter() + args.max_cell_minutes * 60.0,
        )
        correctness = {
            "kernel_planner_regression": kernel_planner_regression(libraries[4]),
            "pathwise_identity_n3_m4": {
                "passed": bool(action_equal and regret_equal and max_regret_diff <= 1e-8),
                "actions_identical": action_equal,
                "regrets_identical_atol_1e-8": regret_equal,
                "max_abs_regret_diff": max_regret_diff,
            },
            "oracle_sanity": {"passed": oracle_max < 1e-6, "max_cumulative_regret": oracle_max},
            "psrl_notype_linearity": {"passed": min_r2 > 0.9, "minimum_r_squared": min_r2, "cells": no_type_r2},
            "determinism": determinism,
            "dgp_probes": {"passed": all(bool(row["all_pass"]) for row in probes), "rows": len(probes)},
        }
        if not all(bool(record["passed"]) for record in correctness.values()):
            diff_path = OUT_DIR / "correctness_gate_failure.json"
            diff_path.write_text(json.dumps(correctness, indent=2) + "\n", encoding="utf-8")
            raise AssertionError(f"scaling correctness gate failed; see {diff_path}")

        s3_joint = [
            row for row in summary_rows
            if row["sweep"] == "s3_frontier_m16" and row["method"] == "joint_psrl_uniform"
        ]
        feasible_ns = [int(row["n"]) for row in s3_joint if bool(row["feasible"])]
        first_infeasible = min((int(row["n"]) for row in s3_joint if not bool(row["feasible"])), default=None)
        frontier = {"largest_feasible_n": max(feasible_ns) if feasible_ns else None, "first_infeasible_n": first_infeasible}

        manifest: dict[str, object] = {
            "schema_version": "1.0",
            "experiment": "HP-SPGG analytic population/library scaling",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "git_commit": git_commit(),
            "provider_calls": 0,
            "K": K,
            "beta": BETA,
            "sigma": SIGMA,
            "H": H,
            "seeds": list(SEEDS),
            "action_values": ACTIONS.tolist(),
            "action_value_count": len(ACTIONS),
            "caps": {
                "joint_table_bytes": JOINT_BYTE_CAP,
                "joint_first_update_seconds": JOINT_UPDATE_SECONDS_CAP,
                "planner_evaluations_per_step": PLANNER_EVALUATION_CAP,
                "cell_wallclock_minutes": args.max_cell_minutes,
            },
            "seed_workers": args.seed_workers,
            "sweeps": {key: [{"n": n, "m": m} for n, m in cells] for key, cells in SWEEPS.items()},
            "type_libraries": {
                str(m): {
                    "synthesis": library.synthesis,
                    "respaced": library.respaced,
                    "initial_rho_hat": library.initial_rho_hat,
                    "rho_hat_min_across_cells": rho_by_m[m],
                    "threshold": RHO_THRESHOLD if m > 4 else None,
                    "parameters": library.parameters.tolist(),
                }
                for m, library in libraries.items()
            },
            "cells": {f"n{n}_m{m}": record for (n, m), record in cell_records.items()},
            "joint_feasibility_frontier": frontier,
            "correctness_gates": correctness,
            "timing_determinism_note": "physical wall-clock arrays are measured and inherently nondeterministic; bitwise replay holds those arrays fixed while independently rerunning every scientific array",
            "artifacts": [],
        }
        all_npz_paths = sorted(NPZ_DIR.rglob("*.npz"))
        if all_npz_paths:
            npz_timestamps = [path.stat().st_mtime for path in all_npz_paths]
            manifest["npz_artifact_wallclock_span_seconds"] = max(npz_timestamps) - min(npz_timestamps)
        artifacts = sorted(NPZ_DIR.rglob("*.npz")) + [SUMMARY_OUT, PARITY_OUT, PROBES_OUT, LIBRARIES_OUT]
        manifest["artifacts"] = [
            {"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in artifacts
            if path.exists()
        ]
        MANIFEST_OUT.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        reported_wallclock = float(manifest.get("npz_artifact_wallclock_span_seconds", time.perf_counter() - started))
        run_report(summary_rows=summary_rows, manifest=manifest, total_seconds=reported_wallclock)
        print(
            json.dumps(
                {
                    "status": "ok",
                    "summary_rows": len(summary_rows),
                    "npz_files": len(list(NPZ_DIR.rglob("*.npz"))),
                    "frontier": frontier,
                    "rho_hat_per_m": rho_by_m,
                    "correctness_gates": correctness,
                    "wallclock_seconds": time.perf_counter() - started,
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
