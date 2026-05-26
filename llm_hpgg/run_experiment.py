"""Run HP-SPGG regret experiments from a calibration tensor."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import numpy as np

from .coordinator import CoordinatorState, dispatch, expected_profile_scores, oracle_profile, profile_count_for_storage, update_posterior
from .decentralized import (
    DECENTRALIZED_ALGORITHMS,
    DecentralizedAgentState,
    decentralized_dispatch,
    update_decentralized,
)
from .environment import load_calibration, rewards_for_types, welfare_for_types
from .verbal_belief import make_initial_belief, sample_personas_verbal, update_belief_verbal


def action_value_lookup(action_profiles: np.ndarray) -> tuple[np.ndarray, dict[tuple[float, ...], int]]:
    action_values = np.array(sorted({float(value) for value in action_profiles.reshape(-1)}), dtype=float)
    lookup = {tuple(float(value) for value in profile): index for index, profile in enumerate(action_profiles)}
    return action_values, lookup


def initialize_prior(state: CoordinatorState, true_types: np.ndarray, mode: str, mass: float,
                     rng: np.random.Generator | None = None, dirichlet_alpha: float | None = None) -> None:
    mode = mode.lower()
    if mode == "uniform":
        return
    if mode == "joint_dirichlet":
        if dirichlet_alpha is None or dirichlet_alpha <= 0.0:
            raise ValueError("joint_dirichlet prior requires --joint-prior-alpha > 0")
        if rng is None:
            raise ValueError("joint_dirichlet prior requires an RNG")
        m = len(state.joint_type_profiles)
        n, type_count = state.posterior.shape
        # Sample joint prior p ~ Dirichlet(alpha * 1_m). For very large alpha the
        # sample concentrates around uniform.
        joint = rng.dirichlet(np.full(m, dirichlet_alpha))
        state.joint_posterior = joint
        # Derive marginals so the factorized PACT family inherits the same
        # information content available to a Bayesian agent that only stores
        # per-player marginals.
        marginals = np.zeros((n, type_count), dtype=float)
        for combo_index, combo in enumerate(state.joint_type_profiles):
            p = joint[combo_index]
            for player_index, type_index in enumerate(combo):
                marginals[player_index, type_index] += p
        row_sums = marginals.sum(axis=1, keepdims=True)
        row_sums[row_sums <= 0.0] = 1.0
        state.posterior = marginals / row_sums
        return
    if mode == "shared_type":
        # Strongly correlated structured prior: joint mass is concentrated on
        # the |Theta| combos where every player shares one common type.
        # Marginals are uniform, so PACT-family (factorized posterior) sees no
        # prior information whereas Joint-PSRL sees a tight |Theta|-atom prior.
        n, type_count = state.posterior.shape
        m = len(state.joint_type_profiles)
        joint = np.zeros(m, dtype=float)
        for combo_index, combo in enumerate(state.joint_type_profiles):
            if np.all(combo == combo[0]):
                joint[combo_index] = 1.0
        joint /= joint.sum()
        state.joint_posterior = joint
        state.posterior = np.full((n, type_count), 1.0 / type_count, dtype=float)
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
    joint_prior_alpha: float | None = None,
    true_type_mode: str = "iid",
    verbal_model: str | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None, np.ndarray, dict[str, int]]:
    algorithm = algorithm.lower()
    rng = np.random.default_rng(seed)
    n, type_count, _ = reward_tensor.shape
    if true_type_mode == "shared_type":
        shared_type = int(rng.integers(0, type_count))
        true_types = np.full(n, shared_type, dtype=int)
    elif true_type_mode == "iid":
        true_types = rng.integers(0, type_count, size=n)
    else:
        raise ValueError(f"Unknown true_type_mode: {true_type_mode}")
    state = CoordinatorState.fresh(n, type_count, reward_tensor, action_profiles, beta)
    initialize_prior(state, true_types, prior_mode, prior_mass, rng=rng, dirichlet_alpha=joint_prior_alpha)
    if algorithm == "joint_psrl_uniform":
        state.joint_posterior = np.full(len(state.joint_type_profiles), 1.0 / len(state.joint_type_profiles), dtype=float)
    elif algorithm == "joint_psrl_aware" and prior_mode != "shared_type":
        joint = np.zeros(len(state.joint_type_profiles), dtype=float)
        for combo_index, combo in enumerate(state.joint_type_profiles):
            if np.all(combo == combo[0]):
                joint[combo_index] = 1.0
        state.joint_posterior = joint / joint.sum()
    verbal_stats = {"sample_ok": 0, "sample_fallback": 0, "update_ok": 0, "update_failed": 0}
    if algorithm == "llm_psrl_verbal":
        verbal_model = verbal_model or os.environ.get("LLM_PSRL_VERBAL_MODEL")
        if not verbal_model:
            raise ValueError("llm_psrl_verbal requires --verbal-model or LLM_PSRL_VERBAL_MODEL")
        state.belief_text = make_initial_belief(n)
    iql_q = np.zeros((n, len(action_profiles)), dtype=float)
    action_values, action_lookup = action_value_lookup(action_profiles)
    independent_iql_q = np.zeros((n, len(action_values)), dtype=float)
    iql_alpha = 0.1
    iql_epsilon = 0.2
    regrets = np.zeros(k_rounds, dtype=float)
    welfare = np.zeros(k_rounds, dtype=float)
    posterior_history = np.zeros((k_rounds, n, type_count), dtype=float) if record_posterior else None

    is_decentralized = algorithm in DECENTRALIZED_ALGORITHMS
    if is_decentralized:
        decent_agents = [
            DecentralizedAgentState.fresh(player_index=i, n=n, type_count=type_count,
                                          reward_tensor=reward_tensor, action_profiles=action_profiles,
                                          action_values=action_values, beta=beta)
            for i in range(n)
        ]
    else:
        decent_agents = None

    for round_index in range(k_rounds):
        if is_decentralized:
            chosen = decentralized_dispatch(algorithm, decent_agents, rng, action_lookup, true_types=true_types)
        elif algorithm == "llm_psrl_verbal":
            assert state.belief_text is not None
            sampled_types, sample_ok = sample_personas_verbal(
                belief_text=state.belief_text,
                n=n,
                model=str(verbal_model),
                rng=rng,
                type_count=type_count,
                log_callback=print,
            )
            verbal_stats["sample_ok" if sample_ok else "sample_fallback"] += 1
            chosen = int(np.argmax(expected_profile_scores(state, sampled_types, uncertainty_bonus=False)))
        elif algorithm in {"iql", "joint_profile_iql"}:
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
        elif algorithm != "oracle" and algorithm != "llm_psrl_verbal":
            update_posterior(state, chosen, observed_rewards)
        if algorithm == "llm_psrl_verbal":
            assert state.belief_text is not None
            state.belief_text, update_ok = update_belief_verbal(
                belief_text=state.belief_text,
                action_values=action_profiles[chosen].astype(float),
                observed_rewards=observed_rewards,
                n=n,
                model=str(verbal_model),
                log_callback=print,
            )
            verbal_stats["update_ok" if update_ok else "update_failed"] += 1
        if is_decentralized and algorithm != "decent_oracle":
            for i, agent in enumerate(decent_agents):
                update_decentralized(agent, chosen, float(observed_rewards[i]))
        if posterior_history is not None:
            if is_decentralized:
                # stack each agent's OWN row to recover per-agent marginal beliefs
                posterior_history[round_index] = np.stack([decent_agents[i].posterior[i] for i in range(n)])
            else:
                posterior_history[round_index] = state.posterior
        welfare[round_index] = chosen_welfare
        regrets[round_index] = max(0.0, oracle_welfare - chosen_welfare)
    return regrets, welfare, posterior_history, true_types, verbal_stats


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
    parser.add_argument("--verbal-model", type=str, default=None,
                        help="Backbone model identifier for llm_psrl_verbal; falls back to LLM_PSRL_VERBAL_MODEL.")
    parser.add_argument("--record-posterior", action="store_true", help="Save posterior_history and true_types arrays in the NPZ output.")
    parser.add_argument("--prior-mode", choices=["uniform", "correct", "adversarial", "joint_dirichlet", "shared_type"], default="uniform")
    parser.add_argument("--prior-mass", type=float, default=0.7)
    parser.add_argument("--joint-prior-alpha", type=float, default=None,
                        help="Dirichlet concentration for joint-prior sampling (only used with --prior-mode joint_dirichlet).")
    parser.add_argument("--true-type-mode", choices=["iid", "shared_type"], default="iid")
    parser.add_argument("--matched-seeds", action="store_true", help="Use the same random seeds across algorithms.")
    parser.add_argument("--seed-offset", type=int, default=0)
    args = parser.parse_args()
    if args.verbal_model:
        os.environ["LLM_PSRL_VERBAL_MODEL"] = args.verbal_model

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
    verbal_sample_ok = np.zeros((len(args.algos), args.seeds), dtype=int)
    verbal_sample_fallback = np.zeros((len(args.algos), args.seeds), dtype=int)
    verbal_update_ok = np.zeros((len(args.algos), args.seeds), dtype=int)
    verbal_update_failed = np.zeros((len(args.algos), args.seeds), dtype=int)
    for algo_index, algorithm in enumerate(args.algos):
        action_values, _ = action_value_lookup(action_profiles)
        storage[algo_index] = profile_count_for_storage(algorithm, n, type_count, len(action_profiles), len(action_values))
        for seed_index in range(args.seeds):
            seed = args.seed_offset + seed_index if args.matched_seeds else args.seed_offset + 10_000 * algo_index + seed_index
            seed_regrets, seed_welfare, seed_posterior, seed_true_types, seed_verbal_stats = run_seed(
                algorithm,
                reward_tensor,
                action_profiles,
                args.K,
                args.beta,
                seed,
                prior_mode=args.prior_mode,
                prior_mass=args.prior_mass,
                record_posterior=args.record_posterior,
                joint_prior_alpha=args.joint_prior_alpha,
                true_type_mode=args.true_type_mode,
                verbal_model=args.verbal_model,
            )
            regrets[algo_index, seed_index] = seed_regrets
            welfare[algo_index, seed_index] = seed_welfare
            if posterior_history is not None and true_types is not None and seed_posterior is not None:
                posterior_history[algo_index, seed_index] = seed_posterior
                true_types[algo_index, seed_index] = seed_true_types
            verbal_sample_ok[algo_index, seed_index] = seed_verbal_stats.get("sample_ok", 0)
            verbal_sample_fallback[algo_index, seed_index] = seed_verbal_stats.get("sample_fallback", 0)
            verbal_update_ok[algo_index, seed_index] = seed_verbal_stats.get("update_ok", 0)
            verbal_update_failed[algo_index, seed_index] = seed_verbal_stats.get("update_failed", 0)

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
        "joint_prior_alpha": float(args.joint_prior_alpha) if args.joint_prior_alpha is not None else 0.0,
        "true_type_mode": args.true_type_mode,
        "matched_seeds": args.matched_seeds,
        "seed_offset": args.seed_offset,
        "player_model": args.player_model or "",
        "judge_model": args.judge_model or "",
        "verbal_model": args.verbal_model or os.environ.get("LLM_PSRL_VERBAL_MODEL", ""),
        "verbal_sample_ok": verbal_sample_ok,
        "verbal_sample_fallback": verbal_sample_fallback,
        "verbal_update_ok": verbal_update_ok,
        "verbal_update_failed": verbal_update_failed,
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
