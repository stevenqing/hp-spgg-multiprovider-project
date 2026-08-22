"""Run CourierDispatch-Rules analytic PACT/PACT+ experiments."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from dataclasses import dataclass
from itertools import product
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_courier_dispatch.dispatch_env import (  # noqa: E402
    ACCEPT,
    ACTIONS,
    MESSAGES,
    RULES,
    CourierDispatchEnv,
    CourierState,
    RulePosterior,
    softmax,
)


ANALYSIS_DIR = ROOT / "analysis" / "courier_dispatch"
FIG_DIRS = [ROOT / "figs", ROOT / "arr_paper" / "figs"]


@dataclass(frozen=True)
class PlanChoice:
    state: CourierState
    expected_reward: float
    bonus: float
    objective: float
    greedy_reward: float
    exploration_cost: float
    candidate_index: int


class JointRulePosterior:
    """Categorical posterior over joint driver rule-tuples."""

    def __init__(self, type_space: np.ndarray, n_agents: int):
        self.type_space = np.asarray(type_space, dtype=int)
        self.n_agents = int(n_agents)
        self.profile_indices = np.asarray(list(product(range(len(self.type_space)), repeat=self.n_agents)), dtype=int)
        self.log_probs = np.full(len(self.profile_indices), -np.log(len(self.profile_indices)), dtype=float)

    def probs(self) -> np.ndarray:
        shifted = self.log_probs - float(np.max(self.log_probs))
        probs = np.exp(shifted)
        total = float(probs.sum())
        if total <= 0.0:
            return np.full(len(self.profile_indices), 1.0 / len(self.profile_indices), dtype=float)
        return probs / total

    def sample(self, rng: np.random.Generator) -> np.ndarray:
        idx = int(rng.choice(len(self.profile_indices), p=self.probs()))
        return self.type_space[self.profile_indices[idx]].copy()

    def update(self, env: CourierDispatchEnv, state: CourierState, actions: np.ndarray) -> None:
        for idx, profile in enumerate(self.profile_indices):
            log_likelihood = 0.0
            for driver, type_index in enumerate(profile):
                likelihood = max(env.likelihood(int(actions[driver]), state, self.type_space[int(type_index)]), 1e-12)
                log_likelihood += float(np.log(likelihood))
            self.log_probs[idx] += log_likelihood
        self.log_probs -= float(np.max(self.log_probs))

    def marginal_posteriors(self) -> list[RulePosterior]:
        probs = self.probs()
        marginals = np.zeros((self.n_agents, len(self.type_space)), dtype=float)
        for weight, profile in zip(probs, self.profile_indices, strict=True):
            for driver, type_index in enumerate(profile):
                marginals[driver, int(type_index)] += float(weight)
        posteriors: list[RulePosterior] = []
        for driver in range(self.n_agents):
            posterior = RulePosterior(self.type_space)
            posterior.log_probs = np.log(np.maximum(marginals[driver], 1e-12))
            posterior.log_probs -= float(np.max(posterior.log_probs))
            posteriors.append(posterior)
        return posteriors

    def prob_true(self, true_types: np.ndarray) -> float:
        marginal_posteriors = self.marginal_posteriors()
        return float(np.mean([posterior.prob_true(true_types[driver]) for driver, posterior in enumerate(marginal_posteriors)]))

    def prob_true_joint_profile(self, true_types: np.ndarray) -> float:
        true_indices = self._type_indices(true_types)
        matches = np.where(np.all(self.profile_indices == true_indices[None, :], axis=1))[0]
        if len(matches) == 0:
            return 0.0
        return float(self.probs()[int(matches[0])])

    def rule_marginal_accuracy(self, true_types: np.ndarray) -> float:
        probs = self.probs()
        marginals = np.zeros_like(true_types, dtype=float)
        for weight, profile in zip(probs, self.profile_indices, strict=True):
            marginals += float(weight) * self.type_space[profile]
        return float(1.0 - np.mean(np.abs(marginals - true_types)))

    def _type_indices(self, types: np.ndarray) -> np.ndarray:
        indices = []
        for row in types:
            match = np.where(np.all(self.type_space == row, axis=1))[0]
            if len(match) == 0:
                raise ValueError("true type not present in type_space")
            indices.append(int(match[0]))
        return np.asarray(indices, dtype=int)


def deterministic_rng(seed: int, round_index: int, candidate_index: int, driver: int, channel: str) -> np.random.Generator:
    raw = f"courier|{seed}|{round_index}|{candidate_index}|{driver}|{channel}".encode("utf-8")
    digest = hashlib.sha256(raw).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "little", signed=False))


def deterministic_joint_actions(
    env: CourierDispatchEnv,
    state: CourierState,
    seed: int,
    round_index: int,
    candidate_index: int,
) -> np.ndarray:
    return np.asarray(
        [
            env.simulate_action(
                state,
                env.true_types[driver],
                deterministic_rng(seed, round_index, candidate_index, driver, "action"),
                agent=driver,
                all_types=env.true_types,
            )
            for driver in range(env.n_agents)
        ],
        dtype=int,
    )


def action_distribution_under_belief(env: CourierDispatchEnv, state: CourierState, posterior: RulePosterior) -> np.ndarray:
    probs = np.zeros(len(ACTIONS), dtype=float)
    for weight, theta in zip(posterior.probs(), posterior.type_space, strict=True):
        probs += float(weight) * softmax(env.action_utilities(state, theta), env.tau)
    return probs


def expected_reward_under_posteriors(
    env: CourierDispatchEnv,
    state: CourierState,
    posteriors: list[RulePosterior],
    rng: np.random.Generator,
    samples: int = 8,
) -> float:
    total = 0.0
    for _ in range(samples):
        sampled_types = np.asarray([posterior.sample(rng) for posterior in posteriors], dtype=int)
        joint = []
        for driver in range(env.n_agents):
            probs = softmax(env.action_utilities(state, sampled_types[driver]), env.tau)
            joint.append(int(rng.choice(len(ACTIONS), p=probs)))
        total += float(np.mean(env.reward_fn(state, joint, sampled_types)))
    return float(total / max(samples, 1))


def expected_reward_sampled_world(
    env: CourierDispatchEnv,
    state: CourierState,
    sampled_types: np.ndarray,
    rng: np.random.Generator,
    samples: int = 8,
) -> float:
    action_probs = [softmax(env.action_utilities(state, sampled_types[i]), env.tau) for i in range(env.n_agents)]
    total = 0.0
    for _ in range(samples):
        joint = [int(rng.choice(len(ACTIONS), p=action_probs[driver])) for driver in range(env.n_agents)]
        total += float(np.mean(env.reward_fn(state, joint, sampled_types)))
    return float(total / max(samples, 1))


def disagreement_bonus(env: CourierDispatchEnv, state: CourierState, posteriors: list[RulePosterior]) -> float:
    accept_joint = np.full(env.n_agents, ACCEPT, dtype=int)
    total = 0.0
    for driver, posterior in enumerate(posteriors):
        probs = posterior.probs()
        values = []
        for theta in posterior.type_space:
            types = np.zeros((env.n_agents, env.rule_count), dtype=int)
            types[driver] = theta
            values.append(float(env.reward_fn(state, accept_joint, types)[driver]))
        values_arr = np.asarray(values, dtype=float)
        diff = np.abs(values_arr[:, None] - values_arr[None, :])
        total += float(np.sum(probs[:, None] * probs[None, :] * diff))
    return float(total)


def choose_state(
    env: CourierDispatchEnv,
    candidates: list[CourierState],
    posteriors: list[RulePosterior],
    rng: np.random.Generator,
    method: str,
    beta: float,
    verbal_belief: list[np.ndarray] | None = None,
    sampled_types_override: np.ndarray | None = None,
) -> PlanChoice:
    if method == "random":
        greedy_rewards = [expected_reward_under_posteriors(env, state, posteriors, rng) for state in candidates]
        idx = int(rng.integers(0, len(candidates)))
        reward = greedy_rewards[idx]
        greedy = float(max(greedy_rewards))
        return PlanChoice(candidates[idx], reward, 0.0, reward, greedy, max(0.0, greedy - reward), idx)

    if method == "oracle":
        pseudo_posteriors = []
        for true_type in env.true_types:
            posterior = RulePosterior(env.type_space)
            posterior.log_probs[:] = -50.0
            idx = np.where(np.all(env.type_space == true_type, axis=1))[0][0]
            posterior.log_probs[idx] = 0.0
            pseudo_posteriors.append(posterior)
        rewards = [expected_reward_under_posteriors(env, state, pseudo_posteriors, rng) for state in candidates]
        idx = int(np.argmax(rewards))
        return PlanChoice(candidates[idx], float(rewards[idx]), 0.0, float(rewards[idx]), float(rewards[idx]), 0.0, idx)

    planning_posteriors = posteriors
    if method in {"atom_tom0", "llm_greedy"}:
        planning_posteriors = [RulePosterior(env.type_space) for _ in range(env.n_agents)]
    elif method in {"atom_tom1", "llm_belief"} and verbal_belief is not None:
        planning_posteriors = []
        for belief in verbal_belief:
            posterior = RulePosterior(env.type_space)
            posterior.log_probs = np.log(np.maximum(belief, 1e-12))
            planning_posteriors.append(posterior)

    if sampled_types_override is not None:
        sampled_types = np.asarray(sampled_types_override, dtype=int)
    elif method == "map_greedy":
        sampled_types = np.asarray([posterior.type_space[int(np.argmax(posterior.probs()))] for posterior in planning_posteriors], dtype=int)
    elif method == "psrl_notype":
        sampled_types = env.type_space[rng.integers(0, len(env.type_space), size=env.n_agents)].copy()
    else:
        sampled_types = np.asarray([posterior.sample(rng) for posterior in planning_posteriors], dtype=int)
    base_rewards = [expected_reward_sampled_world(env, state, sampled_types, rng) for state in candidates]
    greedy_rewards = [expected_reward_under_posteriors(env, state, posteriors, rng) for state in candidates]
    bonuses = [disagreement_bonus(env, state, posteriors) if method == "pact_plus" else 0.0 for state in candidates]
    objectives = [reward + beta * bonus for reward, bonus in zip(base_rewards, bonuses, strict=True)]
    idx = int(np.argmax(objectives))
    greedy = float(max(greedy_rewards))
    chosen_expected = float(greedy_rewards[idx])
    return PlanChoice(
        candidates[idx],
        chosen_expected,
        float(bonuses[idx]),
        float(objectives[idx]),
        greedy,
        max(0.0, greedy - chosen_expected),
        idx,
    )


def update_verbal_belief(env: CourierDispatchEnv, state: CourierState, actions: np.ndarray, rng: np.random.Generator) -> list[np.ndarray]:
    beliefs = []
    uniform = np.full(len(env.type_space), 1.0 / len(env.type_space), dtype=float)
    for action in actions:
        likelihoods = np.array([env.likelihood(int(action), state, theta) for theta in env.type_space], dtype=float)
        if float(likelihoods.sum()) <= 0.0:
            beliefs.append(uniform.copy())
            continue
        posterior = likelihoods / float(likelihoods.sum())
        # Prompt-style belief is deliberately unstable: it is a fresh verbal
        # guess with smoothing and small noise, not a persistent Bayes product.
        noise = rng.dirichlet(np.ones(len(env.type_space)))
        beliefs.append(0.70 * posterior + 0.20 * uniform + 0.10 * noise)
    return beliefs


def most_uncertain_driver(posteriors: list[RulePosterior]) -> int:
    uncertainties = [1.0 - float(np.max(posterior.probs())) for posterior in posteriors]
    return int(np.argmax(uncertainties))


def run_episode(
    method: str,
    beta: float,
    seed: int,
    n_agents: int,
    rule_count: int,
    horizon: int,
    tau: float,
    penalty_scale: float,
    home_scale: float,
    menu_friction: float,
    candidate_count: int,
    couple_lambda: float,
    message_cost: float = 0.03,
) -> list[dict[str, object]]:
    rng = np.random.default_rng(seed + 100_000)
    env = CourierDispatchEnv(
        n_agents=n_agents,
        rule_count=rule_count,
        horizon=horizon,
        tau=tau,
        penalty_scale=penalty_scale,
        home_scale=home_scale,
        menu_friction=menu_friction,
        couple_lambda=couple_lambda,
        seed=seed,
    )
    state_payload, info = env.reset(seed)
    posteriors = [RulePosterior(env.type_space) for _ in range(env.n_agents)]
    joint_posterior = JointRulePosterior(env.type_space, env.n_agents) if method == "joint_psrl" else None
    verbal_belief: list[np.ndarray] | None = None
    rows = []
    cumulative_reward = 0.0
    cumulative_probe_cost = 0.0
    cumulative_message_cost = 0.0
    for t in range(horizon):
        state = env.state
        candidates = env.sample_candidate_states(candidate_count)
        if joint_posterior is not None:
            posteriors = joint_posterior.marginal_posteriors()
        if method == "oracle":
            candidate_actions = [deterministic_joint_actions(env, candidate, seed, t, idx) for idx, candidate in enumerate(candidates)]
            candidate_rewards = [env.reward_fn(candidate, actions, env.true_types) for candidate, actions in zip(candidates, candidate_actions, strict=True)]
            candidate_mean_rewards = [float(np.mean(rewards)) for rewards in candidate_rewards]
            choice_idx = int(np.argmax(candidate_mean_rewards))
            choice = PlanChoice(
                candidates[choice_idx],
                candidate_mean_rewards[choice_idx],
                0.0,
                candidate_mean_rewards[choice_idx],
                candidate_mean_rewards[choice_idx],
                0.0,
                choice_idx,
            )
            observed_actions = candidate_actions[choice_idx]
        elif joint_posterior is not None:
            choice = choose_state(env, candidates, posteriors, rng, method, beta, verbal_belief, sampled_types_override=joint_posterior.sample(rng))
            observed_actions = deterministic_joint_actions(env, choice.state, seed, t, choice.candidate_index)
        else:
            choice = choose_state(env, candidates, posteriors, rng, method, beta, verbal_belief)
            observed_actions = deterministic_joint_actions(env, choice.state, seed, t, choice.candidate_index)
        rewards = env.reward_fn(choice.state, observed_actions, env.true_types)
        observed_messages: list[str] = []
        if method in {"pact", "pact_plus", "pact_message", "map_greedy"}:
            for driver in range(env.n_agents):
                posteriors[driver].update(env, choice.state, int(observed_actions[driver]))
            if method == "pact_message":
                queried_driver = most_uncertain_driver(posteriors)
                message = env.simulate_message(
                    choice.state,
                    env.true_types[queried_driver],
                    deterministic_rng(seed, t, choice.candidate_index, queried_driver, "message"),
                )
                posteriors[queried_driver].update_message(env, choice.state, message)
                observed_messages.append(f"driver{queried_driver}:{MESSAGES[message]}")
                cumulative_message_cost += float(message_cost)
        elif joint_posterior is not None:
            joint_posterior.update(env, choice.state, observed_actions)
            posteriors = joint_posterior.marginal_posteriors()
        elif method in {"atom_tom1", "llm_belief"}:
            verbal_belief = update_verbal_belief(env, choice.state, observed_actions, rng)
        cumulative_reward += float(np.mean(rewards))
        cumulative_probe_cost += choice.exploration_cost
        if method == "oracle":
            mean_true_prob = 1.0
            mean_rule_acc = 1.0
        elif joint_posterior is not None:
            mean_true_prob = joint_posterior.prob_true(env.true_types)
            mean_rule_acc = joint_posterior.rule_marginal_accuracy(env.true_types)
        else:
            true_probs = [posterior.prob_true(env.true_types[i]) for i, posterior in enumerate(posteriors)]
            rule_acc = [posterior.rule_marginal_accuracy(env.true_types[i]) for i, posterior in enumerate(posteriors)]
            mean_true_prob = float(np.mean(true_probs))
            mean_rule_acc = float(np.mean(rule_acc))
        rows.append(
            {
                "method": method,
                "beta": beta,
                "seed": seed,
                "round": t,
                "couple_lambda": couple_lambda,
                "mean_reward": float(np.mean(rewards)),
                "cumulative_reward": cumulative_reward,
                "exploration_cost": choice.exploration_cost,
                "cumulative_exploration_cost": cumulative_probe_cost,
                "message_cost": float(message_cost) if observed_messages else 0.0,
                "cumulative_message_cost": cumulative_message_cost,
                "cumulative_total_information_cost": cumulative_probe_cost + cumulative_message_cost,
                "mean_true_tuple_posterior": mean_true_prob,
                "mean_rule_marginal_accuracy": mean_rule_acc,
                "chosen_state": choice.state.to_dict(),
                "chosen_candidate": choice.candidate_index,
                "observed_actions": [ACTIONS[int(action)] for action in observed_actions],
                "observed_messages": observed_messages,
                "true_types": [dict(zip(RULES[:rule_count], map(int, row), strict=True)) for row in env.true_types],
            }
        )
    return rows


def summarize(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, float, float], list[dict[str, object]]] = {}
    for row in rows:
        key = (str(row["method"]), float(row["beta"]), float(row["couple_lambda"]))
        grouped.setdefault(key, []).append(row)
    summary = []
    for (method, beta, couple_lambda), group in sorted(grouped.items()):
        final_round = max(int(row["round"]) for row in group)
        final = [row for row in group if int(row["round"]) == final_round]
        summary.append(
            {
                "method": method,
                "beta": beta,
                "couple_lambda": couple_lambda,
                "episodes": len({int(row["seed"]) for row in group}),
                "final_mean_cumulative_reward": float(np.mean([float(row["cumulative_reward"]) for row in final])),
                "final_mean_true_tuple_posterior": float(np.mean([float(row["mean_true_tuple_posterior"]) for row in final])),
                "final_mean_rule_marginal_accuracy": float(np.mean([float(row["mean_rule_marginal_accuracy"]) for row in final])),
                "final_mean_cumulative_exploration_cost": float(np.mean([float(row["cumulative_exploration_cost"]) for row in final])),
                "final_mean_cumulative_message_cost": float(np.mean([float(row["cumulative_message_cost"]) for row in final])),
                "final_mean_cumulative_total_information_cost": float(np.mean([float(row["cumulative_total_information_cost"]) for row in final])),
            }
        )
    return summary


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "method",
        "beta",
        "seed",
        "round",
        "couple_lambda",
        "mean_reward",
        "cumulative_reward",
        "exploration_cost",
        "cumulative_exploration_cost",
        "message_cost",
        "cumulative_message_cost",
        "cumulative_total_information_cost",
        "mean_true_tuple_posterior",
        "mean_rule_marginal_accuracy",
        "chosen_candidate",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in fields})


def plot_learning(rows: list[dict[str, object]], out_prefix: str) -> None:
    base_rows = [row for row in rows if float(row["couple_lambda"]) == 0.0]
    methods = sorted({(str(row["method"]), float(row["beta"])) for row in base_rows})
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.0), sharex=True)
    for method, beta in methods:
        group = [row for row in base_rows if row["method"] == method and float(row["beta"]) == beta]
        rounds = sorted({int(row["round"]) for row in group})
        label = f"{method}" if method != "pact_plus" else f"pact+ beta={beta:g}"
        acc = [np.mean([float(row["mean_rule_marginal_accuracy"]) for row in group if int(row["round"]) == r]) for r in rounds]
        prob = [np.mean([float(row["mean_true_tuple_posterior"]) for row in group if int(row["round"]) == r]) for r in rounds]
        axes[0].plot(rounds, prob, linewidth=1.6, label=label)
        axes[1].plot(rounds, acc, linewidth=1.6, label=label)
    axes[0].set_title("Posterior concentration")
    axes[0].set_ylabel("P(true rule tuple)")
    axes[1].set_title("Rule-marginal accuracy")
    axes[1].set_ylabel("Accuracy")
    for ax in axes:
        ax.set_xlabel("Round")
        ax.grid(alpha=0.25)
    axes[1].legend(fontsize=7, frameon=False, loc="lower right")
    fig.tight_layout()
    for out_dir in FIG_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_dir / f"{out_prefix}_learning.png", dpi=220, bbox_inches="tight")
        fig.savefig(out_dir / f"{out_prefix}_learning.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_probe_cost(summary: list[dict[str, object]], out_prefix: str) -> None:
    rows = [row for row in summary if row["method"] == "pact_plus" and float(row["couple_lambda"]) == 0.0]
    rows = sorted(rows, key=lambda row: float(row["beta"]))
    fig, ax = plt.subplots(figsize=(5.8, 4.0))
    xs = [float(row["final_mean_cumulative_exploration_cost"]) for row in rows]
    ys = [float(row["final_mean_true_tuple_posterior"]) for row in rows]
    labels = [f"beta={float(row['beta']):g}" for row in rows]
    ax.plot(xs, ys, marker="o", linewidth=1.8)
    for x, y, label in zip(xs, ys, labels, strict=True):
        ax.annotate(label, (x, y), textcoords="offset points", xytext=(6, 5), fontsize=8)
    ax.set_xlabel("Cumulative exploration cost")
    ax.set_ylabel("Final P(true rule tuple)")
    ax.set_title("PACT+ probe-cost trade-off")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    for out_dir in FIG_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_dir / f"{out_prefix}_probe_cost.png", dpi=220, bbox_inches="tight")
        fig.savefig(out_dir / f"{out_prefix}_probe_cost.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_couple_lambda(summary: list[dict[str, object]], out_prefix: str) -> None:
    rows = [row for row in summary if row["method"] in {"pact", "pact_plus"} and float(row["beta"]) in {0.0, 0.25}]
    fig, ax = plt.subplots(figsize=(5.8, 4.0))
    for method in ["pact", "pact_plus"]:
        subset = sorted([row for row in rows if row["method"] == method], key=lambda row: float(row["couple_lambda"]))
        if not subset:
            continue
        ax.plot(
            [float(row["couple_lambda"]) for row in subset],
            [float(row["final_mean_true_tuple_posterior"]) for row in subset],
            marker="o",
            linewidth=1.8,
            label=method,
        )
    ax.set_xlabel("couple_lambda")
    ax.set_ylabel("Final P(true rule tuple)")
    ax.set_title("Factored-posterior stress under RL violation")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    for out_dir in FIG_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_dir / f"{out_prefix}_couple_lambda.png", dpi=220, bbox_inches="tight")
        fig.savefig(out_dir / f"{out_prefix}_couple_lambda.pdf", bbox_inches="tight")
    plt.close(fig)


def run(args: argparse.Namespace) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    base_methods = [
        ("pact", 0.0),
        ("pact_plus", 0.0),
        ("pact_plus", 0.1),
        ("pact_plus", 0.25),
        ("pact_plus", 0.5),
        ("pact_message", 0.0),
        ("map_greedy", 0.0),
        ("joint_psrl", 0.0),
        ("psrl_notype", 0.0),
        ("atom_tom0", 0.0),
        ("atom_tom1", 0.0),
        ("random", 0.0),
        ("oracle", 0.0),
    ]
    for seed in range(args.seeds):
        for method, beta in base_methods:
            rows.extend(
                run_episode(
                    method,
                    beta,
                    seed=args.seed_offset + seed,
                    n_agents=args.n_agents,
                    rule_count=args.rule_count,
                    horizon=args.horizon,
                    tau=args.tau,
                    penalty_scale=args.penalty_scale,
                    home_scale=args.home_scale,
                    menu_friction=args.menu_friction,
                    candidate_count=args.candidates,
                    couple_lambda=0.0,
                    message_cost=args.message_cost,
                )
            )
        for lam in args.couple_lambdas:
            if lam == 0.0:
                continue
            for method, beta in [("pact", 0.0), ("pact_plus", 0.25)]:
                rows.extend(
                    run_episode(
                        method,
                        beta,
                        seed=args.seed_offset + seed,
                        n_agents=args.n_agents,
                        rule_count=args.rule_count,
                        horizon=args.horizon,
                        tau=args.tau,
                        penalty_scale=args.penalty_scale,
                        home_scale=args.home_scale,
                        menu_friction=args.menu_friction,
                        candidate_count=args.candidates,
                        couple_lambda=lam,
                        message_cost=args.message_cost,
                    )
                )
    return rows, summarize(rows)


def parse_float_list(raw: str) -> list[float]:
    return [float(item.strip()) for item in raw.split(",") if item.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-agents", type=int, default=3)
    parser.add_argument("--rule-count", type=int, default=4)
    parser.add_argument("--horizon", type=int, default=8)
    parser.add_argument("--seeds", type=int, default=1)
    parser.add_argument("--seed-offset", type=int, default=0)
    parser.add_argument("--tau", type=float, default=0.5)
    parser.add_argument("--penalty-scale", type=float, default=2.0)
    parser.add_argument("--home-scale", type=float, default=1.2)
    parser.add_argument("--menu-friction", type=float, default=0.2)
    parser.add_argument("--message-cost", type=float, default=0.03)
    parser.add_argument("--candidates", type=int, default=4)
    parser.add_argument("--couple-lambdas", type=parse_float_list, default=parse_float_list("0,1,2,4"))
    parser.add_argument("--out-prefix", default="courier_dispatch")
    args = parser.parse_args()

    env = CourierDispatchEnv(
        args.n_agents,
        args.rule_count,
        args.horizon,
        args.tau,
        args.penalty_scale,
        args.home_scale,
        args.menu_friction,
    )
    env.assert_transition_independence()
    env.assert_reward_locality()
    env.assert_prior_factorization()

    rows, summary = run(args)
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(ANALYSIS_DIR / f"{args.out_prefix}_rows.csv", rows)
    payload = {
        "setting": {
            "n_agents": args.n_agents,
            "rule_count": args.rule_count,
            "rules": RULES[: args.rule_count],
            "actions": ACTIONS,
            "messages": MESSAGES,
            "horizon": args.horizon,
            "seeds": args.seeds,
            "tau": args.tau,
            "penalty_scale": args.penalty_scale,
            "home_scale": args.home_scale,
            "menu_friction": args.menu_friction,
            "message_cost": args.message_cost,
            "candidate_states_per_round": args.candidates,
            "couple_lambdas": args.couple_lambdas,
            "conditions": {
                "TI": "Public transition depends on public state and joint action, not hidden rules.",
                "RL": "At couple_lambda=0, reward_i is invariant to theta_-i; tested by assert_reward_locality().",
                "PF": "Initial rule tuples are sampled independently across drivers; smoke-tested by assert_prior_factorization().",
            },
        },
        "summary": summary,
    }
    (ANALYSIS_DIR / f"{args.out_prefix}_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    plot_learning(rows, f"fig_{args.out_prefix}")
    plot_probe_cost(summary, f"fig_{args.out_prefix}")
    plot_couple_lambda(summary, f"fig_{args.out_prefix}")
    print(json.dumps({"summary": str((ANALYSIS_DIR / f'{args.out_prefix}_summary.json').relative_to(ROOT)), "rows": len(rows)}, indent=2))
    for row in summary:
        if row["couple_lambda"] == 0.0:
            print(
                f"{row['method']} beta={row['beta']}: reward={row['final_mean_cumulative_reward']:.3f} "
                f"Ptrue={row['final_mean_true_tuple_posterior']:.3f} rule_acc={row['final_mean_rule_marginal_accuracy']:.3f} "
                f"probe_cost={row['final_mean_cumulative_exploration_cost']:.3f} "
                f"info_cost={row['final_mean_cumulative_total_information_cost']:.3f}"
            )


if __name__ == "__main__":
    main()