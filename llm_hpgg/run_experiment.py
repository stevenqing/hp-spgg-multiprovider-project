"""Run HP-SPGG regret experiments from a calibration tensor."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import numpy as np

from .coordinator import CoordinatorState, dispatch, oracle_profile, profile_count_for_storage, update_posterior
from .environment import load_calibration, rewards_for_types, welfare_for_types


def action_value_lookup(action_profiles: np.ndarray) -> tuple[np.ndarray, dict[tuple[float, ...], int]]:
    action_values = np.array(sorted({float(value) for value in action_profiles.reshape(-1)}), dtype=float)
    lookup = {tuple(float(value) for value in profile): index for index, profile in enumerate(action_profiles)}
    return action_values, lookup


def initialize_prior(state: CoordinatorState, true_types: np.ndarray, mode: str, mass: float) -> None:
    mode = mode.lower()
    if mode == "uniform":
        return
    if not 0.0 < mass < 1.0:
        raise ValueError("prior mass must be in (0, 1)")
    type_count = state.posterior.shape[1]
    if type_count < 2 and mode == "adversarial":
        raise ValueError("adversarial prior requires at least two types")
    off_mass = (1.0 - mass) / max(type_count - 1, 1)
    for player_index, true_type in enumerate(true_types):
        favored_type = int(true_type)
        if mode == "adversarial":
            favored_type = int((true_type + 1) % type_count)
        elif mode != "correct":
            raise ValueError(f"Unknown prior mode: {mode}")
        state.posterior[player_index] = off_mass
        state.posterior[player_index, favored_type] = mass
    joint = np.ones(len(state.joint_type_profiles), dtype=float)
    for combo_index, combo in enumerate(state.joint_type_profiles):
        for player_index, type_index in enumerate(combo):
            joint[combo_index] *= state.posterior[player_index, type_index]
    joint_sum = float(joint.sum())
    state.joint_posterior = joint / joint_sum if joint_sum > 0.0 else np.full_like(joint, 1.0 / len(joint))


def run_seed(
    algorithm: str,
    reward_tensor: np.ndarray,
    action_profiles: np.ndarray,
    k_rounds: int,
    beta: float,
    seed: int,
    prior_mode: str = "uniform",
    prior_mass: float = 0.7,
    record_posterior: bool = False,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None, np.ndarray]:
    algorithm = algorithm.lower()
    rng = np.random.default_rng(seed)
    n, type_count, _ = reward_tensor.shape
    true_types = rng.integers(0, type_count, size=n)
    state = CoordinatorState.fresh(n, type_count, reward_tensor, action_profiles, beta)
    initialize_prior(state, true_types, prior_mode, prior_mass)
    iql_q = np.zeros((n, len(action_profiles)), dtype=float)
    action_values, action_lookup = action_value_lookup(action_profiles)
    independent_iql_q = np.zeros((n, len(action_values)), dtype=float)
    iql_alpha = 0.1
    iql_epsilon = 0.2
    regrets = np.zeros(k_rounds, dtype=float)
    welfare = np.zeros(k_rounds, dtype=float)
    posterior_history = np.zeros((k_rounds, n, type_count), dtype=float) if record_posterior else None

    for round_index in range(k_rounds):
        if algorithm in {"iql", "joint_profile_iql"}:
            if rng.random() < iql_epsilon:
                chosen = int(rng.integers(0, len(action_profiles)))
            else:
                chosen = int(np.argmax(iql_q.sum(axis=0)))
        elif algorithm == "iql_independent_actions":
            chosen_action_indices = np.zeros(n, dtype=int)
            for player_index in range(n):
                if rng.random() < iql_epsilon:
                    chosen_action_indices[player_index] = int(rng.integers(0, len(action_values)))
                else:
                    chosen_action_indices[player_index] = int(np.argmax(independent_iql_q[player_index]))
            chosen_profile = tuple(float(action_values[action_index]) for action_index in chosen_action_indices)
            chosen = action_lookup[chosen_profile]
        else:
            chosen = dispatch(algorithm, state, rng, true_types=true_types)
        oracle = oracle_profile(state, true_types)
        chosen_welfare = welfare_for_types(reward_tensor, true_types, chosen)
        oracle_welfare = welfare_for_types(reward_tensor, true_types, oracle)
        observed_rewards = rewards_for_types(reward_tensor, true_types, chosen)
        if algorithm in {"iql", "joint_profile_iql"}:
            iql_q[:, chosen] += iql_alpha * (observed_rewards - iql_q[:, chosen])
        elif algorithm == "iql_independent_actions":
            for player_index, action_value in enumerate(action_profiles[chosen]):
                action_index = int(np.where(np.isclose(action_values, action_value))[0][0])
                independent_iql_q[player_index, action_index] += iql_alpha * (observed_rewards[player_index] - independent_iql_q[player_index, action_index])
        elif algorithm != "oracle":
            update_posterior(state, chosen, observed_rewards)
        if posterior_history is not None:
            posterior_history[round_index] = state.posterior
        welfare[round_index] = chosen_welfare
        regrets[round_index] = max(0.0, oracle_welfare - chosen_welfare)
    return regrets, welfare, posterior_history, true_types


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an HP-SPGG experiment.")
    parser.add_argument("--K", type=int, default=30)
    parser.add_argument("--n", type=int, default=3)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--beta", type=float, default=1.0)
    parser.add_argument(
        "--algos",
        nargs="+",
        default=["hpsmg_plus", "hpsmg", "joint_psrl", "map_greedy", "psrl_notype", "iql_independent_actions", "iql", "random", "oracle"],
    )
    parser.add_argument("--calibration", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--player-model")
    parser.add_argument("--judge-model")
    parser.add_argument("--record-posterior", action="store_true", help="Save posterior_history and true_types arrays in the NPZ output.")
    parser.add_argument("--prior-mode", choices=["uniform", "correct", "adversarial"], default="uniform")
    parser.add_argument("--prior-mass", type=float, default=0.7)
    parser.add_argument("--matched-seeds", action="store_true", help="Use the same random seeds across algorithms.")
    parser.add_argument("--seed-offset", type=int, default=0)
    args = parser.parse_args()

    calibration = load_calibration(args.calibration)
    reward_tensor = np.asarray(calibration["reward_tensor"], dtype=float)
    action_profiles = np.asarray(calibration["action_profiles"], dtype=float)
    n, type_count, _ = reward_tensor.shape
    if args.n != n:
        raise ValueError(f"Calibration n={n} does not match --n={args.n}")

    regrets = np.zeros((len(args.algos), args.seeds, args.K), dtype=float)
    welfare = np.zeros_like(regrets)
    posterior_history = np.zeros((len(args.algos), args.seeds, args.K, n, type_count), dtype=float) if args.record_posterior else None
    true_types = np.zeros((len(args.algos), args.seeds, n), dtype=int) if args.record_posterior else None
    storage = np.zeros(len(args.algos), dtype=int)
    for algo_index, algorithm in enumerate(args.algos):
        action_values, _ = action_value_lookup(action_profiles)
        storage[algo_index] = profile_count_for_storage(algorithm, n, type_count, len(action_profiles), len(action_values))
        for seed_index in range(args.seeds):
            seed = args.seed_offset + seed_index if args.matched_seeds else args.seed_offset + 10_000 * algo_index + seed_index
            seed_regrets, seed_welfare, seed_posterior, seed_true_types = run_seed(
                algorithm,
                reward_tensor,
                action_profiles,
                args.K,
                args.beta,
                seed,
                prior_mode=args.prior_mode,
                prior_mass=args.prior_mass,
                record_posterior=args.record_posterior,
            )
            regrets[algo_index, seed_index] = seed_regrets
            welfare[algo_index, seed_index] = seed_welfare
            if posterior_history is not None and true_types is not None and seed_posterior is not None:
                posterior_history[algo_index, seed_index] = seed_posterior
                true_types[algo_index, seed_index] = seed_true_types

    cumulative_regret = np.cumsum(regrets, axis=2)
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "algorithms": np.array(args.algos),
        "regrets": regrets,
        "cumulative_regret": cumulative_regret,
        "welfare": welfare,
        "storage": storage,
        "backend": os.getenv("LLM_HPGG_BACKEND", str(calibration.get("backend", "unknown"))),
        "beta": args.beta,
        "K": args.K,
        "seeds": args.seeds,
        "prior_mode": args.prior_mode,
        "prior_mass": args.prior_mass,
        "matched_seeds": args.matched_seeds,
        "seed_offset": args.seed_offset,
        "player_model": args.player_model or "",
        "judge_model": args.judge_model or "",
    }
    if posterior_history is not None and true_types is not None:
        output["posterior_history"] = posterior_history
        output["true_types"] = true_types
    np.savez(output_path, **output)
    for algorithm, value in zip(args.algos, cumulative_regret[:, :, -1].mean(axis=1)):
        print(f"{algorithm}: final_cumulative_regret_mean={value:.4f}")
    print(f"saved={output_path}")


if __name__ == "__main__":
    main()
