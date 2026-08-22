"""Run zero-LLM-call experiments from the PACT AAAI-27 reviewer spec.

Outputs are written to ``analysis/aaai27_review``:

* E-R1: controlled likelihood-interface perturbations on analytic HP-SPGG;
* E-R2: leave-one-persona-out and library-expansion diagnostics;
* E-R4: compact Concordia exact-enumeration versus best-response planners;
* E-R0: MaaSSim per-seed rows reconstructed from the retained replay cache.

E-R3 is live and is intentionally run through
``run_sotopia_menu_corruption_suite.py`` so each episode is checkpointed.
"""

from __future__ import annotations

import argparse
import csv
import importlib
import math
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
CONCORDIA_ROOT = ROOT / "external" / "concordia"
for path in (ROOT, SCRIPTS, CONCORDIA_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from llm_hpgg.coordinator import CoordinatorState, expected_profile_scores, posterior_expected_profile_scores
from llm_hpgg.environment import build_reward_tensor, rewards_for_types, welfare_for_types
from llm_hpgg.personas import PERSONAS

OUTPUT = ROOT / "analysis" / "aaai27_review"


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    if not rows:
        raise ValueError(f"No rows for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fieldnames or list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def entropy(probabilities: np.ndarray) -> float:
    clipped = np.clip(np.asarray(probabilities, dtype=float), 1e-15, 1.0)
    return float(-np.sum(clipped * np.log(clipped)))


def likelihood_update(
    posterior: np.ndarray,
    candidate_tensor: np.ndarray,
    profile_index: int,
    observed_rewards: np.ndarray,
    rng: np.random.Generator,
    *,
    likelihood_sigma: float = 0.08,
    temperature: float = 1.0,
    log_noise: float = 0.0,
    top_k: int | None = None,
) -> None:
    for player in range(posterior.shape[0]):
        residual = observed_rewards[player] - candidate_tensor[player, :, profile_index]
        log_likelihood = -0.5 * (residual / likelihood_sigma) ** 2 / temperature
        if log_noise > 0.0:
            log_likelihood += rng.normal(0.0, log_noise, size=len(log_likelihood))
        if top_k is not None and top_k < len(log_likelihood):
            retained = np.argpartition(log_likelihood, -top_k)[-top_k:]
            mask = np.ones(len(log_likelihood), dtype=bool)
            mask[retained] = False
            log_likelihood[mask] = -np.inf
        finite = np.isfinite(log_likelihood)
        weights = np.zeros_like(log_likelihood)
        if finite.any():
            weights[finite] = np.exp(log_likelihood[finite] - float(np.max(log_likelihood[finite])))
        posterior[player] *= weights
        total = float(np.sum(posterior[player]))
        posterior[player] = posterior[player] / total if total > 0.0 else 1.0 / posterior.shape[1]


def choose_hp_profile(
    variant: str,
    state: CoordinatorState,
    rng: np.random.Generator,
) -> int:
    if variant == "pact":
        sampled = np.array([rng.choice(state.posterior.shape[1], p=row) for row in state.posterior], dtype=int)
        return int(np.argmax(expected_profile_scores(state, sampled, uncertainty_bonus=False)))
    if variant == "pact_plus":
        return int(np.argmax(posterior_expected_profile_scores(state, uncertainty_bonus=True)))
    raise ValueError(variant)


def run_hp_episode_sequence(
    *,
    base_tensor: np.ndarray,
    action_profiles: np.ndarray,
    candidate_tensor: np.ndarray,
    candidate_names: list[str],
    true_types: np.ndarray,
    variant: str,
    seed: int,
    episodes: int = 20,
    beta: float = 0.25,
    temperature: float = 1.0,
    log_noise: float = 0.0,
    top_k: int | None = None,
    true_candidate_indices: np.ndarray | None = None,
) -> dict[str, Any]:
    policy_rng = np.random.default_rng(seed + 10_000_019)
    likelihood_rng = np.random.default_rng(seed + 20_000_033)
    state = CoordinatorState.fresh(len(true_types), candidate_tensor.shape[1], candidate_tensor, action_profiles, beta)
    oracle_welfare = np.array(
        [welfare_for_types(base_tensor, true_types, index) for index in range(len(action_profiles))],
        dtype=float,
    )
    exact = float(np.max(oracle_welfare))
    cumulative_regret = 0.0
    entropy_path: list[float] = []
    for _ in range(episodes):
        chosen = choose_hp_profile(variant, state, policy_rng)
        observed = rewards_for_types(base_tensor, true_types, chosen)
        cumulative_regret += max(0.0, exact - float(oracle_welfare[chosen]))
        likelihood_update(
            state.posterior,
            candidate_tensor,
            chosen,
            observed,
            likelihood_rng,
            temperature=temperature,
            log_noise=log_noise,
            top_k=top_k,
        )
        entropy_path.append(float(np.mean([entropy(row) for row in state.posterior])))
    argmax_names = [candidate_names[index] for index in np.argmax(state.posterior, axis=1)]
    exact_mass = float("nan")
    if true_candidate_indices is not None:
        exact_mass = float(np.mean(state.posterior[np.arange(len(true_types)), true_candidate_indices]))
    return {
        "cumulative_regret_k20": cumulative_regret,
        "exact_type_mass_k20": exact_mass,
        "final_entropy": entropy_path[-1],
        "entropy_trajectory": ";".join(f"{value:.9f}" for value in entropy_path),
        "argmax_persona": "|".join(argmax_names),
    }


def run_e_r1() -> Path:
    bundle = build_reward_tensor(n=3, backend="mixed", samples=3, seed=19)
    names = [persona.key for persona in PERSONAS]
    rows: list[dict[str, Any]] = []
    perturbations: list[tuple[str, str, dict[str, Any]]] = []
    for sigma in (0.0, 0.1, 0.25, 0.5, 1.0, 2.0):
        perturbations.append(("additive_log_noise", str(sigma), {"log_noise": sigma}))
    for tau in (0.5, 0.7, 1.0, 1.5, 2.0):
        perturbations.append(("temperature", str(tau), {"temperature": tau}))
    for label, top_k in (("1", 1), ("3", 3), ("5", 5), ("full", None)):
        perturbations.append(("top_k", label, {"top_k": top_k}))

    for variant in ("pact", "pact_plus"):
        for perturbation, level, kwargs in perturbations:
            for seed in range(500):
                rng = np.random.default_rng(seed)
                true_types = rng.integers(0, len(names), size=3)
                result = run_hp_episode_sequence(
                    base_tensor=bundle.reward_tensor,
                    action_profiles=bundle.action_profiles,
                    candidate_tensor=bundle.reward_tensor,
                    candidate_names=names,
                    true_types=true_types,
                    true_candidate_indices=true_types,
                    variant=variant,
                    seed=seed,
                    **kwargs,
                )
                rows.append(
                    {
                        "backbone": "analytic_mixed",
                        "variant": variant,
                        "perturbation_type": perturbation,
                        "level": level,
                        "seed": seed,
                        "cumulative_regret_k20": result["cumulative_regret_k20"],
                        "exact_type_mass_k20": result["exact_type_mass_k20"],
                    }
                )
    path = OUTPUT / "e_r1_noise_analytic_mixed.csv"
    write_csv(path, rows)
    return path


def tracker_tensor_with_distractors(base: np.ndarray, count: int) -> tuple[np.ndarray, list[str]]:
    tensors = [base]
    names = [persona.key for persona in PERSONAS]
    if count == 2:
        tensors.append(np.stack([(base[:, 0, :] + base[:, 1, :]) / 2, (base[:, 2, :] + base[:, 3, :]) / 2], axis=1))
        names.extend(["distractor_coop_blend", "distractor_risk_selfish_blend"])
    elif count == 4:
        extra = np.stack([(base[:, i, :] + base[:, (i + 1) % 4, :]) / 2 for i in range(4)], axis=1)
        tensors.append(extra)
        names.extend([f"distractor_cycle_{i}" for i in range(4)])
    return np.concatenate(tensors, axis=1), names


def run_e_r2() -> tuple[Path, Path]:
    bundle = build_reward_tensor(n=3, backend="mixed", samples=3, seed=19)
    names = [persona.key for persona in PERSONAS]
    loo_rows: list[dict[str, Any]] = []
    for excluded in range(4):
        true_types = np.full(3, excluded, dtype=int)
        keep = [index for index in range(4) if index != excluded]
        candidate_tensor = bundle.reward_tensor[:, keep, :]
        candidate_names = [names[index] for index in keep]
        for variant in ("pact", "pact_plus"):
            for seed in range(5):
                reference = run_hp_episode_sequence(
                    base_tensor=bundle.reward_tensor,
                    action_profiles=bundle.action_profiles,
                    candidate_tensor=bundle.reward_tensor,
                    candidate_names=names,
                    true_types=true_types,
                    true_candidate_indices=true_types,
                    variant=variant,
                    seed=seed,
                )
                result = run_hp_episode_sequence(
                    base_tensor=bundle.reward_tensor,
                    action_profiles=bundle.action_profiles,
                    candidate_tensor=candidate_tensor,
                    candidate_names=candidate_names,
                    true_types=true_types,
                    true_candidate_indices=None,
                    variant=variant,
                    seed=seed,
                )
                loo_rows.append(
                    {
                        "backbone": "analytic_mixed",
                        "excluded_persona": names[excluded],
                        "variant": variant,
                        "seed": seed,
                        "cumulative_regret_k20": result["cumulative_regret_k20"],
                        "in_library_reference_regret_k20": reference["cumulative_regret_k20"],
                        "regret_degradation": result["cumulative_regret_k20"] - reference["cumulative_regret_k20"],
                        "final_entropy": result["final_entropy"],
                        "argmax_persona": result["argmax_persona"],
                        "entropy_trajectory": result["entropy_trajectory"],
                        "status": "completed_offline_outcome_likelihood",
                    }
                )
        for prompt_variant in ("llm_belief", "atom_tom1"):
            for seed in range(5):
                loo_rows.append(
                    {
                        "backbone": "gpt-5.4-nano-20260317",
                        "excluded_persona": names[excluded],
                        "variant": prompt_variant,
                        "seed": seed,
                        "cumulative_regret_k20": "",
                        "in_library_reference_regret_k20": "",
                        "regret_degradation": "",
                        "final_entropy": "",
                        "argmax_persona": "not_applicable_no_discrete_tracker_library",
                        "entropy_trajectory": "",
                        "status": "not_run_no_cached_trajectory_and_no_shared_discrete_library",
                    }
                )
    loo_path = OUTPUT / "e_r2_loo_analytic_mixed.csv"
    write_csv(loo_path, loo_rows)

    expansion_rows: list[dict[str, Any]] = []
    for distractor_count in (0, 2, 4):
        tracker_tensor, candidate_names = tracker_tensor_with_distractors(bundle.reward_tensor, distractor_count)
        for variant in ("pact", "pact_plus"):
            for seed in range(5):
                rng = np.random.default_rng(seed)
                true_types = rng.integers(0, 4, size=3)
                result = run_hp_episode_sequence(
                    base_tensor=bundle.reward_tensor,
                    action_profiles=bundle.action_profiles,
                    candidate_tensor=tracker_tensor,
                    candidate_names=candidate_names,
                    true_types=true_types,
                    true_candidate_indices=true_types,
                    variant=variant,
                    seed=seed,
                )
                expansion_rows.append(
                    {
                        "backbone": "analytic_mixed",
                        "distractor_count": distractor_count,
                        "variant": variant,
                        "seed": seed,
                        "cumulative_regret_k20": result["cumulative_regret_k20"],
                        "exact_type_mass_k20": result["exact_type_mass_k20"],
                        "final_entropy": result["final_entropy"],
                        "argmax_persona": result["argmax_persona"],
                    }
                )
    expansion_path = OUTPUT / "e_r2_expansion_analytic_mixed.csv"
    write_csv(expansion_path, expansion_rows)
    return loo_path, expansion_path


def mean(values: Iterable[float]) -> float:
    values = list(values)
    return float(sum(values) / max(1, len(values)))


def sem(values: Iterable[float]) -> float:
    values = np.asarray(list(values), dtype=float)
    return float(values.std(ddof=1) / math.sqrt(len(values))) if len(values) > 1 else 0.0


def pub_best_response(case: dict[str, Any], action: dict[str, str], passes: int, pub: Any) -> dict[str, str]:
    payoff = pub.payoff_for_case(case)
    current = dict(action)
    for _ in range(passes):
        for player in case["people"]:
            best_venue = current[player]
            best_value = float("-inf")
            for venue in case["venues"]:
                candidate = dict(current)
                candidate[player] = venue
                value = float(payoff.action_to_scores(candidate).get(player, 0.0))
                if value > best_value:
                    best_value = value
                    best_venue = venue
            current[player] = best_venue
    return current


def pub_focal(case: dict[str, Any], action: dict[str, str], pub: Any) -> float:
    scores = pub.payoff_for_case(case).action_to_scores(action)
    return mean(float(scores.get(player, 0.0)) for player in case["focal_players"])


def haggling_best_response(case: dict[str, Any], deal: dict[str, Any], action: dict[str, str], passes: int, hag: Any) -> dict[str, str]:
    current = dict(action)
    for _ in range(passes):
        best_action = current["buyer_action"]
        best_value = float("-inf")
        for buyer_action in case["price_options"]:
            candidate = dict(current)
            candidate["buyer_action"] = buyer_action
            value = float(hag.score_deal(case, deal, candidate).get(deal["buyer"], 0.0))
            if value > best_value:
                best_value = value
                best_action = buyer_action
        current["buyer_action"] = best_action
        best_seller_action = current["seller_action"]
        best_value = float("-inf")
        for seller_action in ("reject", "accept"):
            candidate = dict(current)
            candidate["seller_action"] = seller_action
            value = float(hag.score_deal(case, deal, candidate).get(deal["seller"], 0.0))
            if value > best_value:
                best_value = value
                best_seller_action = seller_action
        current["seller_action"] = best_seller_action
    return current


def haggling_case_focal(case: dict[str, Any], actions: list[dict[str, str]], hag: Any) -> float:
    totals = {player: 0.0 for player in case["people"]}
    for deal, action in zip(case["deals"], actions, strict=True):
        for player, value in hag.score_deal(case, deal, action).items():
            totals[player] = totals.get(player, 0.0) + float(value)
    return mean(totals[player] for player in case["focal_players"])


def run_e_r4() -> Path:
    from llm_hpgg_concordia import run_haggling_compact as hag
    from llm_hpgg_concordia import run_pub_coordination_compact as pub

    pub.ensure_concordia_examples_on_path()
    hag.ensure_concordia_examples_on_path()
    pub_axes = [
        ("london_mini_s30", "london_mini", 30),
        ("capetown_s100", "capetown", 100),
        ("capetown_s30", "capetown", 30),
        ("london_mini_s5", "london_mini", 5),
        ("edinburgh_closures_s30", "edinburgh_closures", 30),
        ("london_s30", "london", 30),
        ("london_closures_s30", "london_closures", 30),
        ("edinburgh_s30", "edinburgh", 30),
        ("edinburgh_tough_friendship_s30", "edinburgh_tough_friendship", 30),
    ]
    hag_axes = [
        ("haggling", "fruitville", 30),
        ("haggling", "vegbrooke", 30),
        ("haggling", "fruitville_gullible", 30),
        ("haggling", "vegbrooke_stubborn", 30),
        ("haggling", "vegbrooke_strange_game", 30),
        ("haggling_multi_item", "vegbrooke", 30),
        ("haggling_multi_item", "fruitville_gullible", 30),
        ("haggling_multi_item", "fruitville_multi", 30),
        ("haggling_multi_item", "cumulative_score", 30),
    ]
    collected: dict[tuple[str, str, str], list[tuple[float, float]]] = {}

    for axis, config_name, seeds in pub_axes:
        config = pub.load_config(config_name)
        for seed in range(seeds):
            case = pub.build_case(config, seed)
            initial, _ = pub.choose_hpsmg_plus_joint_proxy(case)
            for solver, passes in (("exact_enumeration", 0), ("greedy_br_1pass", 1), ("iterated_br_3pass", 3)):
                started = time.perf_counter_ns()
                if passes == 0:
                    action, _ = pub.choose_oracle_joint(case)
                else:
                    action = pub_best_response(case, initial, passes, pub)
                elapsed_ms = (time.perf_counter_ns() - started) / 1e6
                collected.setdefault(("pub_coordination", axis, solver), []).append((pub_focal(case, action, pub), elapsed_ms))

    for domain, config_name, seeds in hag_axes:
        config = hag.load_config(domain, config_name)
        axis = f"{domain}_{config_name}_s{seeds}"
        for seed in range(seeds):
            case = hag.build_case(domain, config, seed)
            initial_actions = [hag.choose_action(case, deal, "hpsmg_plus_joint_proxy")[0] for deal in case["deals"]]
            for solver, passes in (("exact_enumeration", 0), ("greedy_br_1pass", 1), ("iterated_br_3pass", 3)):
                started = time.perf_counter_ns()
                if passes == 0:
                    actions = [hag.choose_action(case, deal, "oracle_focal")[0] for deal in case["deals"]]
                else:
                    actions = [haggling_best_response(case, deal, action, passes, hag) for deal, action in zip(case["deals"], initial_actions, strict=True)]
                elapsed_ms = (time.perf_counter_ns() - started) / 1e6
                collected.setdefault((domain, axis, solver), []).append((haggling_case_focal(case, actions, hag), elapsed_ms))

    rows = []
    for (substrate, config, solver), values in collected.items():
        focal = [value[0] for value in values]
        wall = [value[1] for value in values]
        rows.append(
            {
                "substrate": substrate,
                "config": config,
                "solver": solver,
                "focal_payoff": mean(focal),
                "focal_payoff_sem": sem(focal),
                "walltime_ms": mean(wall),
                "walltime_ms_sem": sem(wall),
                "seed_count": len(values),
            }
        )
    rows.sort(key=lambda row: (row["substrate"], row["config"], row["solver"]))
    path = OUTPUT / "e_r4_planner_concordia.csv"
    write_csv(path, rows)
    return path


def run_e_r0() -> Path:
    import replay_maassim_llm_smoke as replay

    cache = replay.load_cache()
    path = OUTPUT / "e_r0_maassim_per_seed.csv"
    existing_rows: list[dict[str, Any]] = []
    if path.exists():
        with path.open(newline="", encoding="utf-8") as handle:
            existing_rows = list(csv.DictReader(handle))
    completed = {
        (str(row["scenario"]), str(row["variant"]), int(row["seed"]))
        for row in existing_rows
    }
    model = "gpt-5.4-mini-20260317"
    scenarios = [
        ("normal_p2", "normal", 2.0, ["nearest", "random", "llm", "llm_belief", "llm_psrl", "atom_tom1", "econ_bne", "oracle"]),
        ("stress_p5", "normal", 5.0, ["nearest", "random", "llm", "llm_belief", "llm_psrl", "atom_tom0", "atom_tom1", "econ_bne", "oracle"]),
        ("conflict_p5", "conflict_offer", 5.0, ["nearest", "random", "llm", "llm_belief", "llm_psrl", "atom_tom0", "atom_tom1", "econ_bne", "oracle"]),
    ]
    rows: list[dict[str, Any]] = list(existing_rows)
    original = (replay.SCENARIO, replay.DRIVER_REJECT_PENALTY, replay.PASSENGER_REJECT_PENALTY)
    try:
        for scenario_id, scenario, reject_penalty, policies in scenarios:
            replay.SCENARIO = scenario
            replay.DRIVER_REJECT_PENALTY = reject_penalty
            replay.PASSENGER_REJECT_PENALTY = 0.5
            for policy in policies:
                for seed in range(5):
                    key = (scenario_id, policy, seed)
                    if key in completed:
                        continue
                    stats = replay.evaluate_policy_seed(policy, seed, model, cache, 20, 700, 0.0, "scored")
                    rows.append(
                        {
                            "variant": policy,
                            "scenario": scenario_id,
                            "seed": seed,
                            "utility": stats.realized_utility,
                            "rejects": stats.driver_rejects,
                            "wait": stats.total_wait / max(stats.served, 1),
                            "served": stats.served,
                            "llm_calls": stats.llm_calls,
                            "cache_hits": stats.cache_hits,
                        }
                    )
                    completed.add(key)
                    rows.sort(key=lambda row: (str(row["scenario"]), str(row["variant"]), int(row["seed"])))
                    write_csv(path, rows)
                    print(
                        f"E-R0 done {len(rows)}/130 scenario={scenario_id} policy={policy} seed={seed} "
                        f"calls={stats.llm_calls} cache_hits={stats.cache_hits}",
                        flush=True,
                    )
    finally:
        replay.SCENARIO, replay.DRIVER_REJECT_PENALTY, replay.PASSENGER_REJECT_PENALTY = original
    write_csv(path, rows)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", choices=["all", "e-r0", "e-r1", "e-r2", "e-r4"], default="all")
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    if args.only in {"all", "e-r1"}:
        outputs.append(run_e_r1())
    if args.only in {"all", "e-r2"}:
        outputs.extend(run_e_r2())
    if args.only in {"all", "e-r4"}:
        outputs.append(run_e_r4())
    if args.only in {"all", "e-r0"}:
        outputs.append(run_e_r0())
    for path in outputs:
        print(f"saved={path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
