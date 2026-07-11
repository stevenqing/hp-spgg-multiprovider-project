"""Online personalized matching benchmark for CourierDispatch-Rules.

Each round samples an order pool. The platform assigns one order to each driver,
observes neutral driver action codes, updates beliefs, and incurs online regret
against a true-type oracle assignment for that same public order pool.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from itertools import permutations, product
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_courier_dispatch.demo_dispatch import (  # noqa: E402
    JointRulePosterior,
    deterministic_rng,
    update_verbal_belief,
)
from llm_courier_dispatch.dispatch_env import (  # noqa: E402
    ACCEPT,
    ACTIONS,
    CHOOSE_FROM_MENU,
    REPOSITION,
    RULES,
    CourierDispatchEnv,
    CourierState,
    RulePosterior,
    softmax,
)


ANALYSIS_DIR = ROOT / "analysis" / "courier_dispatch_matching"


@dataclass(frozen=True)
class MatchingChoice:
    assignment: tuple[int, ...]
    expected_reward: float
    bonus: float
    objective: float
    posterior_greedy_reward: float
    exploration_cost: float


def all_assignments(n_agents: int, order_count: int) -> list[tuple[int, ...]]:
    if order_count < n_agents:
        raise ValueError("order_count must be >= n_agents")
    return [tuple(int(index) for index in assignment) for assignment in permutations(range(order_count), n_agents)]


def type_stress_order_pool(env: CourierDispatchEnv, count: int) -> list[CourierState]:
    """Build matching pools where public orders trade off different hidden rules.

    Random pools often contain nearly tied assignments or universally good orders.
    This stress pool keeps pay/congestion in a narrow band and makes each order
    violate a different operational rule, so online personalization has more
    room to affect regret.
    """

    templates = [
        # long-trip trap, otherwise attractive
        (1, 0, 1, 1, 1.76, 1, (0, 0, 1, 1, 0.62)),
        # zone-leaving trap, otherwise attractive
        (0, 1, 1, 1, 1.76, 1, (0, 0, 1, 1, 0.62)),
        # away-from-home late trap, otherwise attractive
        (0, 0, 0, 1, 1.76, 1, (0, 0, 1, 1, 0.60)),
        # no-surge trap with higher pay to tempt generic planners
        (0, 0, 1, 0, 1.92, 1, (0, 0, 1, 1, 0.58)),
        # mixed trap for larger pools
        (1, 1, 0, 1, 2.04, 1, (0, 0, 1, 1, 0.56)),
        # safe but lower-pay fallback
        (0, 0, 1, 1, 0.46, 0, (0, 0, 1, 1, 0.42)),
    ]
    orders: list[CourierState] = []
    for idx in range(int(count)):
        long_trip, leaves_zone, home_ward, surge, pay, after_deadline, menu = templates[idx % len(templates)]
        menu_long_trip, menu_leaves_zone, menu_home_ward, menu_surge, menu_pay = menu
        pay_jitter = float(np.round(env.rng.uniform(-0.06, 0.06), 3))
        menu_jitter = float(np.round(env.rng.uniform(-0.04, 0.04), 3))
        congestion = float(np.round(env.rng.uniform(0.05, 0.28), 3))
        orders.append(
            CourierState(
                long_trip=int(long_trip),
                leaves_zone=int(leaves_zone),
                home_ward=int(home_ward),
                surge=int(surge),
                pay=float(np.round(pay + pay_jitter, 3)),
                after_deadline=int(after_deadline),
                congestion=congestion,
                menu_long_trip=int(menu_long_trip),
                menu_leaves_zone=int(menu_leaves_zone),
                menu_home_ward=int(menu_home_ward),
                menu_surge=int(menu_surge),
                menu_pay=float(np.round(menu_pay + menu_jitter, 3)),
                t=env.t,
            )
        )
    permutation = env.rng.permutation(len(orders))
    return [orders[int(index)] for index in permutation]


def sample_order_pool(env: CourierDispatchEnv, count: int, mode: str = "random") -> list[CourierState]:
    if mode == "random":
        return env.sample_candidate_states(count)
    if mode == "type_stress":
        return type_stress_order_pool(env, count)
    raise ValueError(f"unknown matching pool mode: {mode}")


def local_reward(env: CourierDispatchEnv, state: CourierState, action: int, theta: np.ndarray, accepted_count: int) -> float:
    public_congestion = float(state.congestion + 0.25 * max(0, accepted_count - 1))
    if action == ACCEPT:
        return float(env.base_accept_utility(state, theta) - 0.5 * public_congestion)
    if action == CHOOSE_FROM_MENU:
        return float(env.base_accept_utility(env.menu_state(state), theta) - env.menu_friction - 0.45 * public_congestion)
    if action == REPOSITION:
        home_pull = int(env._pad_rules(theta)[2])
        return float(-0.08 + 0.45 * home_pull * state.after_deadline * (1 - state.home_ward))
    return -0.06


def assignment_action_probs(env: CourierDispatchEnv, orders: list[CourierState], assignment: tuple[int, ...], types: np.ndarray) -> list[np.ndarray]:
    return [softmax(env.action_utilities(orders[order_index], types[driver]), env.tau) for driver, order_index in enumerate(assignment)]


def expected_assignment_reward(env: CourierDispatchEnv, orders: list[CourierState], assignment: tuple[int, ...], types: np.ndarray) -> float:
    probs = assignment_action_probs(env, orders, assignment, types)
    expected_accepted = float(sum(float(prob[ACCEPT] + prob[CHOOSE_FROM_MENU]) for prob in probs))
    accepted_load = max(0.0, expected_accepted - 1.0)
    total = 0.0
    for driver, order_index in enumerate(assignment):
        state = orders[order_index]
        theta = types[driver]
        public_congestion = float(state.congestion + 0.25 * accepted_load)
        driver_reward = 0.0
        for action, probability in enumerate(probs[driver]):
            if action == ACCEPT:
                value = float(env.base_accept_utility(state, theta) - 0.5 * public_congestion)
            elif action == CHOOSE_FROM_MENU:
                value = float(env.base_accept_utility(env.menu_state(state), theta) - env.menu_friction - 0.45 * public_congestion)
            elif action == REPOSITION:
                home_pull = int(env._pad_rules(theta)[2])
                value = float(-0.08 + 0.45 * home_pull * state.after_deadline * (1 - state.home_ward))
            else:
                value = -0.06
            driver_reward += float(probability) * value
        total += driver_reward / env.n_agents
    return float(total)


def expected_assignment_under_posteriors(
    env: CourierDispatchEnv,
    orders: list[CourierState],
    assignment: tuple[int, ...],
    posteriors: list[RulePosterior],
    rng: np.random.Generator,
    samples: int,
) -> float:
    total = 0.0
    for _ in range(max(1, samples)):
        sampled_types = np.asarray([posterior.sample(rng) for posterior in posteriors], dtype=int)
        total += expected_assignment_reward(env, orders, assignment, sampled_types)
    return float(total / max(1, samples))


def expected_assignment_under_factored_posteriors(
    env: CourierDispatchEnv,
    orders: list[CourierState],
    assignment: tuple[int, ...],
    posteriors: list[RulePosterior],
    rng: np.random.Generator | None = None,
    samples: int = 4,
    max_exact_profiles: int = 10000,
) -> float:
    profile_count = 1
    for posterior in posteriors:
        profile_count *= len(posterior.type_space)
    if profile_count > max_exact_profiles:
        if rng is None:
            rng = np.random.default_rng(0)
        return expected_assignment_under_posteriors(env, orders, assignment, posteriors, rng, samples)
    posterior_probs = [posterior.probs() for posterior in posteriors]
    profile_indices = np.asarray(list(product(*[range(len(posterior.type_space)) for posterior in posteriors])), dtype=int)
    profile_weights = np.ones(len(profile_indices), dtype=float)
    for driver, probs in enumerate(posterior_probs):
        profile_weights *= probs[profile_indices[:, driver]]

    accepted_terms = np.zeros(len(profile_indices), dtype=float)
    driver_constants: list[np.ndarray] = []
    driver_load_coeffs: list[np.ndarray] = []
    for driver, order_index in enumerate(assignment):
        state = orders[order_index]
        type_space = posteriors[driver].type_space
        constants = np.zeros(len(type_space), dtype=float)
        accept_terms = np.zeros(len(type_space), dtype=float)
        load_coeffs = np.zeros(len(type_space), dtype=float)
        for type_index, theta in enumerate(type_space):
            probs = softmax(env.action_utilities(state, theta), env.tau)
            accept_terms[type_index] = float(probs[ACCEPT] + probs[CHOOSE_FROM_MENU])
            driver_value = 0.0
            load_coeff = 0.0
            for action, probability in enumerate(probs):
                if action == ACCEPT:
                    value = float(env.base_accept_utility(state, theta) - 0.5 * state.congestion)
                    load_coeff += float(probability) * 0.5 * 0.25
                elif action == CHOOSE_FROM_MENU:
                    value = float(env.base_accept_utility(env.menu_state(state), theta) - env.menu_friction - 0.45 * state.congestion)
                    load_coeff += float(probability) * 0.45 * 0.25
                elif action == REPOSITION:
                    home_pull = int(env._pad_rules(theta)[2])
                    value = float(-0.08 + 0.45 * home_pull * state.after_deadline * (1 - state.home_ward))
                else:
                    value = -0.06
                driver_value += float(probability) * value
            constants[type_index] = driver_value
            load_coeffs[type_index] = load_coeff
        indices = profile_indices[:, driver]
        accepted_terms += accept_terms[indices]
        driver_constants.append(constants[indices])
        driver_load_coeffs.append(load_coeffs[indices])

    accepted_load = np.maximum(0.0, accepted_terms - 1.0)
    profile_rewards = np.zeros(len(profile_indices), dtype=float)
    for constants, load_coeffs in zip(driver_constants, driver_load_coeffs, strict=True):
        profile_rewards += constants - load_coeffs * accepted_load
    profile_rewards /= env.n_agents
    return float(np.dot(profile_weights, profile_rewards))


def expected_assignment_sampled_world(
    env: CourierDispatchEnv,
    orders: list[CourierState],
    assignment: tuple[int, ...],
    sampled_types: np.ndarray,
) -> float:
    return expected_assignment_reward(env, orders, assignment, sampled_types)


def assignment_disagreement_bonus(env: CourierDispatchEnv, orders: list[CourierState], assignment: tuple[int, ...], posteriors: list[RulePosterior]) -> float:
    total = 0.0
    for driver, posterior in enumerate(posteriors):
        order = orders[assignment[driver]]
        weights = posterior.probs()
        values = []
        for theta in posterior.type_space:
            probs = softmax(env.action_utilities(order, theta), env.tau)
            driver_value = 0.0
            for action, probability in enumerate(probs):
                accepted_count = 1 if int(action) in {ACCEPT, CHOOSE_FROM_MENU} else 0
                driver_value += float(probability) * local_reward(env, order, int(action), theta, accepted_count)
            values.append(driver_value)
        value_arr = np.asarray(values, dtype=float)
        diff = np.abs(value_arr[:, None] - value_arr[None, :])
        total += float(np.sum(weights[:, None] * weights[None, :] * diff))
    return float(total)


def pact_plus_exploration_scale(posteriors: list[RulePosterior], round_index: int, horizon: int) -> float:
    if not posteriors:
        return 0.0
    uncertainties = [1.0 - float(np.max(posterior.probs())) for posterior in posteriors]
    uncertainty = float(np.mean(uncertainties))
    uncertainty_gate = min(1.0, max(0.0, (uncertainty - 0.20) / 0.70))
    time_gate = max(0.0, 1.0 - float(round_index) / max(1.0, float(horizon)))
    return float(uncertainty_gate * time_gate)


def update_joint_matching(joint: JointRulePosterior, env: CourierDispatchEnv, orders: list[CourierState], assignment: tuple[int, ...], actions: np.ndarray) -> None:
    for idx, profile in enumerate(joint.profile_indices):
        log_likelihood = 0.0
        for driver, type_index in enumerate(profile):
            theta = joint.type_space[int(type_index)]
            likelihood = max(env.likelihood(int(actions[driver]), orders[assignment[driver]], theta), 1e-12)
            log_likelihood += float(np.log(likelihood))
        joint.log_probs[idx] += log_likelihood
    joint.log_probs -= float(np.max(joint.log_probs))


def update_verbal_belief_matching(env: CourierDispatchEnv, orders: list[CourierState], assignment: tuple[int, ...], actions: np.ndarray, rng: np.random.Generator) -> list[np.ndarray]:
    beliefs = []
    uniform = np.full(len(env.type_space), 1.0 / len(env.type_space), dtype=float)
    for driver, action in enumerate(actions):
        order = orders[assignment[driver]]
        likelihoods = np.asarray([env.likelihood(int(action), order, theta) for theta in env.type_space], dtype=float)
        if float(likelihoods.sum()) <= 0.0:
            beliefs.append(uniform.copy())
            continue
        posterior = likelihoods / float(likelihoods.sum())
        noise = rng.dirichlet(np.ones(len(env.type_space)))
        beliefs.append(0.70 * posterior + 0.20 * uniform + 0.10 * noise)
    return beliefs


def choose_assignment(
    env: CourierDispatchEnv,
    orders: list[CourierState],
    assignments: list[tuple[int, ...]],
    posteriors: list[RulePosterior],
    rng: np.random.Generator,
    method: str,
    beta: float,
    samples: int,
    verbal_belief: list[np.ndarray] | None = None,
    sampled_types_override: np.ndarray | None = None,
    round_index: int = 0,
    horizon: int = 1,
) -> MatchingChoice:
    posterior_rewards = [expected_assignment_under_posteriors(env, orders, assignment, posteriors, rng, samples) for assignment in assignments]
    posterior_greedy = float(max(posterior_rewards))
    if method == "random":
        idx = int(rng.integers(0, len(assignments)))
        reward = float(posterior_rewards[idx])
        return MatchingChoice(assignments[idx], reward, 0.0, reward, posterior_greedy, max(0.0, posterior_greedy - reward))
    if method == "oracle":
        true_rewards = [expected_assignment_reward(env, orders, assignment, env.true_types) for assignment in assignments]
        idx = int(np.argmax(true_rewards))
        reward = float(true_rewards[idx])
        return MatchingChoice(assignments[idx], reward, 0.0, reward, reward, 0.0)

    planning_posteriors = posteriors
    if method in {"atom_tom0", "llm_greedy"}:
        planning_posteriors = [RulePosterior(env.type_space) for _ in range(env.n_agents)]
    elif method in {"atom_tom1", "llm_belief"} and verbal_belief is not None:
        planning_posteriors = []
        for belief in verbal_belief:
            posterior = RulePosterior(env.type_space)
            posterior.log_probs = np.log(np.maximum(belief, 1e-12))
            posterior.log_probs -= float(np.max(posterior.log_probs))
            planning_posteriors.append(posterior)

    if sampled_types_override is not None:
        sampled_types = np.asarray(sampled_types_override, dtype=int)
    elif method == "map_greedy":
        sampled_types = np.asarray([posterior.type_space[int(np.argmax(posterior.probs()))] for posterior in planning_posteriors], dtype=int)
    elif method == "psrl_notype":
        sampled_types = env.type_space[rng.integers(0, len(env.type_space), size=env.n_agents)].copy()
    else:
        sampled_types = np.asarray([posterior.sample(rng) for posterior in planning_posteriors], dtype=int)

    if method in {"pact", "pact_plus"}:
        base_rewards = [
            expected_assignment_under_factored_posteriors(env, orders, assignment, posteriors, rng, samples)
            for assignment in assignments
        ]
    else:
        base_rewards = [expected_assignment_sampled_world(env, orders, assignment, sampled_types) for assignment in assignments]
    pact_plus_scale = pact_plus_exploration_scale(posteriors, round_index, horizon) if method == "pact_plus" else 0.0
    bonuses = [pact_plus_scale * assignment_disagreement_bonus(env, orders, assignment, posteriors) if method == "pact_plus" else 0.0 for assignment in assignments]
    objectives = [reward + beta * bonus for reward, bonus in zip(base_rewards, bonuses, strict=True)]
    idx = int(np.argmax(objectives))
    return MatchingChoice(
        assignments[idx],
        float(posterior_rewards[idx]),
        float(bonuses[idx]),
        float(objectives[idx]),
        posterior_greedy,
        max(0.0, posterior_greedy - float(posterior_rewards[idx])),
    )


def observed_actions_for_assignment(env: CourierDispatchEnv, orders: list[CourierState], assignment: tuple[int, ...], seed: int, round_index: int) -> np.ndarray:
    actions = []
    for driver, order_index in enumerate(assignment):
        rng = deterministic_rng(seed, round_index, order_index, driver, "matching-action")
        actions.append(env.simulate_action(orders[order_index], env.true_types[driver], rng, agent=driver, all_types=env.true_types))
    return np.asarray(actions, dtype=int)


def realized_assignment_reward(env: CourierDispatchEnv, orders: list[CourierState], assignment: tuple[int, ...], actions: np.ndarray) -> np.ndarray:
    accepted_count = int(sum(1 for action in actions if int(action) in {ACCEPT, CHOOSE_FROM_MENU}))
    return np.asarray([local_reward(env, orders[assignment[driver]], int(action), env.true_types[driver], accepted_count) for driver, action in enumerate(actions)], dtype=float)


def run_episode(
    method: str,
    beta: float,
    seed: int,
    n_agents: int,
    rule_count: int,
    horizon: int,
    order_count: int,
    tau: float,
    penalty_scale: float,
    home_scale: float,
    menu_friction: float,
    samples: int,
    pool_mode: str,
) -> list[dict[str, object]]:
    rng = np.random.default_rng(seed + 700_000)
    env = CourierDispatchEnv(
        n_agents=n_agents,
        rule_count=rule_count,
        horizon=horizon,
        tau=tau,
        penalty_scale=penalty_scale,
        home_scale=home_scale,
        menu_friction=menu_friction,
        seed=seed,
    )
    env.reset(seed)
    assignments = all_assignments(n_agents, order_count)
    posteriors = [RulePosterior(env.type_space) for _ in range(env.n_agents)]
    joint_posterior = JointRulePosterior(env.type_space, env.n_agents) if method == "joint_psrl" else None
    verbal_belief: list[np.ndarray] | None = None
    rows: list[dict[str, object]] = []
    cumulative_reward = 0.0
    cumulative_regret = 0.0
    cumulative_exploration_cost = 0.0
    for round_index in range(horizon):
        orders = sample_order_pool(env, order_count, mode=pool_mode)
        if joint_posterior is not None:
            posteriors = joint_posterior.marginal_posteriors()
        sampled_override = joint_posterior.sample(rng) if joint_posterior is not None else None
        choice = choose_assignment(env, orders, assignments, posteriors, rng, method, beta, samples, verbal_belief, sampled_override, round_index, horizon)
        observed_actions = observed_actions_for_assignment(env, orders, choice.assignment, seed, round_index)
        rewards = realized_assignment_reward(env, orders, choice.assignment, observed_actions)

        oracle_expected = max(expected_assignment_reward(env, orders, assignment, env.true_types) for assignment in assignments)
        chosen_true_expected = expected_assignment_reward(env, orders, choice.assignment, env.true_types)
        regret = max(0.0, float(oracle_expected - chosen_true_expected))

        if method in {"pact", "pact_plus", "map_greedy"}:
            for driver, action in enumerate(observed_actions):
                posteriors[driver].update(env, orders[choice.assignment[driver]], int(action))
        elif joint_posterior is not None:
            update_joint_matching(joint_posterior, env, orders, choice.assignment, observed_actions)
            posteriors = joint_posterior.marginal_posteriors()
        elif method in {"atom_tom1", "llm_belief"}:
            verbal_belief = update_verbal_belief_matching(env, orders, choice.assignment, observed_actions, rng)

        cumulative_reward += float(np.mean(rewards))
        cumulative_regret += regret
        cumulative_exploration_cost += choice.exploration_cost
        if method == "oracle":
            mean_true_prob = 1.0
            mean_rule_acc = 1.0
        elif joint_posterior is not None:
            mean_true_prob = joint_posterior.prob_true(env.true_types)
            mean_rule_acc = joint_posterior.rule_marginal_accuracy(env.true_types)
        else:
            mean_true_prob = float(np.mean([posterior.prob_true(env.true_types[driver]) for driver, posterior in enumerate(posteriors)]))
            mean_rule_acc = float(np.mean([posterior.rule_marginal_accuracy(env.true_types[driver]) for driver, posterior in enumerate(posteriors)]))
        rows.append(
            {
                "method": method,
                "beta": beta,
                "seed": seed,
                "round": round_index,
                "mean_reward": float(np.mean(rewards)),
                "cumulative_reward": cumulative_reward,
                "instant_regret": regret,
                "cumulative_regret": cumulative_regret,
                "oracle_expected_reward": float(oracle_expected),
                "chosen_true_expected_reward": float(chosen_true_expected),
                "exploration_cost": choice.exploration_cost,
                "cumulative_exploration_cost": cumulative_exploration_cost,
                "mean_true_tuple_posterior": mean_true_prob,
                "mean_rule_marginal_accuracy": mean_rule_acc,
                "assignment": list(choice.assignment),
                "observed_actions": [ACTIONS[int(action)] for action in observed_actions],
            }
        )
    return rows


def summarize(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, float], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["method"]), float(row["beta"]))].append(row)
    summary = []
    for (method, beta), group in sorted(grouped.items()):
        final_round = max(int(row["round"]) for row in group)
        final = [row for row in group if int(row["round"]) == final_round]
        summary.append(
            {
                "method": method,
                "beta": beta,
                "episodes": len({int(row["seed"]) for row in group}),
                "final_mean_cumulative_reward": float(np.mean([float(row["cumulative_reward"]) for row in final])),
                "final_mean_cumulative_regret": float(np.mean([float(row["cumulative_regret"]) for row in final])),
                "final_mean_true_tuple_posterior": float(np.mean([float(row["mean_true_tuple_posterior"]) for row in final])),
                "final_mean_rule_marginal_accuracy": float(np.mean([float(row["mean_rule_marginal_accuracy"]) for row in final])),
                "final_mean_cumulative_exploration_cost": float(np.mean([float(row["cumulative_exploration_cost"]) for row in final])),
            }
        )
    return summary


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields = [
        "method",
        "beta",
        "seed",
        "round",
        "mean_reward",
        "cumulative_reward",
        "instant_regret",
        "cumulative_regret",
        "oracle_expected_reward",
        "chosen_true_expected_reward",
        "exploration_cost",
        "cumulative_exploration_cost",
        "mean_true_tuple_posterior",
        "mean_rule_marginal_accuracy",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def parse_method_specs(raw: str) -> list[tuple[str, float]]:
    specs = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        if ":" in item:
            method, beta = item.split(":", 1)
            specs.append((method.strip(), float(beta)))
        else:
            specs.append((item, 0.0))
    return specs


def run(args: argparse.Namespace) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    methods = parse_method_specs(args.methods)
    for seed in range(args.seeds):
        for method, beta in methods:
            rows.extend(
                run_episode(
                    method=method,
                    beta=beta,
                    seed=args.seed_offset + seed,
                    n_agents=args.n_agents,
                    rule_count=args.rule_count,
                    horizon=args.horizon,
                    order_count=args.orders,
                    tau=args.tau,
                    penalty_scale=args.penalty_scale,
                    home_scale=args.home_scale,
                    menu_friction=args.menu_friction,
                    samples=args.samples,
                    pool_mode=args.pool_mode,
                )
            )
    return rows, summarize(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-agents", type=int, default=3)
    parser.add_argument("--rule-count", type=int, default=4)
    parser.add_argument("--horizon", type=int, default=16)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--seed-offset", type=int, default=0)
    parser.add_argument("--orders", type=int, default=5)
    parser.add_argument("--tau", type=float, default=0.5)
    parser.add_argument("--penalty-scale", type=float, default=2.0)
    parser.add_argument("--home-scale", type=float, default=1.2)
    parser.add_argument("--menu-friction", type=float, default=0.2)
    parser.add_argument("--samples", type=int, default=4)
    parser.add_argument("--pool-mode", choices=["random", "type_stress"], default="random")
    parser.add_argument("--methods", default="oracle:0.0,pact:0.0,pact_plus:0.1,map_greedy:0.0,joint_psrl:0.0,psrl_notype:0.0,atom_tom1:0.0,random:0.0")
    parser.add_argument("--out-prefix", default="courier_matching")
    args = parser.parse_args()
    rows, summary = run(args)
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    rows_path = ANALYSIS_DIR / f"{args.out_prefix}_rows.csv"
    summary_path = ANALYSIS_DIR / f"{args.out_prefix}_summary.json"
    write_csv(rows_path, rows)
    payload = {
        "setting": {
            "n_agents": args.n_agents,
            "rule_count": args.rule_count,
            "horizon": args.horizon,
            "seeds": args.seeds,
            "orders_per_round": args.orders,
            "pool_mode": args.pool_mode,
            "tau": args.tau,
            "methods": parse_method_specs(args.methods),
            "regret": "online mean-field expected regret vs true-type oracle assignment for the same order pool",
        },
        "summary": summary,
    }
    summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path.relative_to(ROOT)), "rows": str(rows_path.relative_to(ROOT)), "n_rows": len(rows)}, indent=2))
    for row in summary:
        print(
            f"{row['method']} beta={row['beta']}: reward={row['final_mean_cumulative_reward']:.3f} "
            f"regret={row['final_mean_cumulative_regret']:.3f} Ptrue={row['final_mean_true_tuple_posterior']:.3f} "
            f"rule_acc={row['final_mean_rule_marginal_accuracy']:.3f}"
        )


if __name__ == "__main__":
    main()