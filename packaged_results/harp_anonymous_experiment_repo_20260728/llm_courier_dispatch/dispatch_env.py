"""Analytic CourierDispatch-Rules environment.

The benchmark models independent courier drivers with private operational rules.
The platform observes accept/reject/reposition behaviour and maintains a numeric
posterior over finite rule tuples. Coupling between drivers enters through
public congestion, while rewards depend on each driver's own hidden rules unless
``couple_lambda`` is explicitly set above zero for the RL-violation stress test.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterable

import numpy as np


RULES = ("avoid_long", "zone_loyal", "home_pull", "surge_only")
ACTIONS = ("accept", "decline-a", "decline-b", "decline-c", "decline-d", "reposition", "choose-from-menu")
MESSAGES = ("none", "msg-a", "msg-b", "msg-c", "msg-d")
ACCEPT = ACTIONS.index("accept")
DECLINE_A = ACTIONS.index("decline-a")
DECLINE_B = ACTIONS.index("decline-b")
DECLINE_C = ACTIONS.index("decline-c")
DECLINE_D = ACTIONS.index("decline-d")
REPOSITION = ACTIONS.index("reposition")
CHOOSE_FROM_MENU = ACTIONS.index("choose-from-menu")
MSG_NONE = MESSAGES.index("none")
MSG_A = MESSAGES.index("msg-a")
MSG_B = MESSAGES.index("msg-b")
MSG_C = MESSAGES.index("msg-c")
MSG_D = MESSAGES.index("msg-d")


@dataclass(frozen=True)
class Discrete:
    n: int


@dataclass(frozen=True)
class CourierState:
    long_trip: int
    leaves_zone: int
    home_ward: int
    surge: int
    pay: float
    after_deadline: int
    congestion: float
    menu_long_trip: int = 0
    menu_leaves_zone: int = 0
    menu_home_ward: int = 0
    menu_surge: int = 0
    menu_pay: float = 1.0
    t: int = 0

    def to_dict(self) -> dict[str, float | int]:
        return {
            "long_trip": int(self.long_trip),
            "leaves_zone": int(self.leaves_zone),
            "home_ward": int(self.home_ward),
            "surge": int(self.surge),
            "pay": float(self.pay),
            "after_deadline": int(self.after_deadline),
            "congestion": float(self.congestion),
            "menu_long_trip": int(self.menu_long_trip),
            "menu_leaves_zone": int(self.menu_leaves_zone),
            "menu_home_ward": int(self.menu_home_ward),
            "menu_surge": int(self.menu_surge),
            "menu_pay": float(self.menu_pay),
            "t": int(self.t),
        }


def state_from_dict(payload: dict[str, float | int]) -> CourierState:
    return CourierState(
        long_trip=int(payload["long_trip"]),
        leaves_zone=int(payload["leaves_zone"]),
        home_ward=int(payload["home_ward"]),
        surge=int(payload["surge"]),
        pay=float(payload["pay"]),
        after_deadline=int(payload["after_deadline"]),
        congestion=float(payload["congestion"]),
        menu_long_trip=int(payload.get("menu_long_trip", 0)),
        menu_leaves_zone=int(payload.get("menu_leaves_zone", 0)),
        menu_home_ward=int(payload.get("menu_home_ward", 0)),
        menu_surge=int(payload.get("menu_surge", 0)),
        menu_pay=float(payload.get("menu_pay", payload.get("pay", 1.0))),
        t=int(payload.get("t", 0)),
    )


def enumerate_rule_types(rule_count: int = len(RULES)) -> np.ndarray:
    return np.asarray(list(product([0, 1], repeat=rule_count)), dtype=int)


def softmax(values: np.ndarray, tau: float) -> np.ndarray:
    tau = max(float(tau), 1e-9)
    scaled = np.asarray(values, dtype=float) / tau
    scaled -= float(np.max(scaled))
    exp = np.exp(scaled)
    return exp / float(exp.sum())


def rule_dict(rule_tuple: np.ndarray) -> dict[str, int]:
    return {name: int(value) for name, value in zip(RULES, rule_tuple, strict=True)}


class RulePosterior:
    """Categorical posterior over enumerable binary rule tuples."""

    def __init__(self, type_space: np.ndarray):
        self.type_space = np.asarray(type_space, dtype=int)
        self.log_probs = np.full(len(self.type_space), -np.log(len(self.type_space)), dtype=float)

    def probs(self) -> np.ndarray:
        shifted = self.log_probs - float(np.max(self.log_probs))
        probs = np.exp(shifted)
        total = float(probs.sum())
        if total <= 0.0:
            return np.full(len(self.type_space), 1.0 / len(self.type_space), dtype=float)
        return probs / total

    def update(self, env: "CourierDispatchEnv", state: CourierState, action: int) -> None:
        for idx, rule_tuple in enumerate(self.type_space):
            likelihood = max(env.likelihood(int(action), state, rule_tuple), 1e-12)
            self.log_probs[idx] += np.log(likelihood)
        self.log_probs -= float(np.max(self.log_probs))

    def update_message(self, env: "CourierDispatchEnv", state: CourierState, message: int) -> None:
        for idx, rule_tuple in enumerate(self.type_space):
            likelihood = max(env.message_likelihood(int(message), state, rule_tuple), 1e-12)
            self.log_probs[idx] += np.log(likelihood)
        self.log_probs -= float(np.max(self.log_probs))

    def sample(self, rng: np.random.Generator) -> np.ndarray:
        idx = int(rng.choice(len(self.type_space), p=self.probs()))
        return self.type_space[idx].copy()

    def prob_true(self, true_type: np.ndarray) -> float:
        matches = np.where(np.all(self.type_space == true_type, axis=1))[0]
        if len(matches) == 0:
            return 0.0
        return float(self.probs()[int(matches[0])])

    def rule_marginals(self) -> dict[str, float]:
        probs = self.probs()
        marginals = probs @ self.type_space
        return {name: float(value) for name, value in zip(RULES, marginals, strict=True)}

    def rule_marginal_accuracy(self, true_type: np.ndarray) -> float:
        probs = self.probs()
        marginals = probs @ self.type_space
        return float(1.0 - np.mean(np.abs(marginals - true_type)))


class CourierDispatchEnv:
    """Small controlled courier-dispatch simulator.

    Public state transitions are independent of hidden rules. Rewards are local
    in hidden rules at ``couple_lambda=0`` and can be deliberately coupled by
    setting ``couple_lambda>0`` for the COM-MTDP/RL-violation stress test.
    """

    def __init__(
        self,
        n_agents: int = 3,
        rule_count: int = 4,
        horizon: int = 80,
        tau: float = 0.45,
        penalty_scale: float = 2.0,
        home_scale: float = 1.2,
        menu_friction: float = 0.20,
        couple_lambda: float = 0.0,
        seed: int | None = None,
    ) -> None:
        if rule_count > len(RULES):
            raise ValueError(f"rule_count must be <= {len(RULES)}")
        self.n_agents = int(n_agents)
        self.rule_count = int(rule_count)
        self.horizon = int(horizon)
        self.tau = float(tau)
        self.penalty_scale = float(penalty_scale)
        self.home_scale = float(home_scale)
        self.menu_friction = float(menu_friction)
        self.couple_lambda = float(couple_lambda)
        self.action_space = Discrete(len(ACTIONS))
        self.type_space = enumerate_rule_types(rule_count)
        self.n_types = len(self.type_space)
        self.rng = np.random.default_rng(seed)
        self.true_types = np.zeros((self.n_agents, self.rule_count), dtype=int)
        self.state = self._sample_state(t=0)
        self.t = 0

    @property
    def n_agents_attr(self) -> int:
        return self.n_agents

    def enumerate_types(self) -> list[tuple[int, ...]]:
        return [tuple(int(value) for value in row) for row in self.type_space]

    def reset(self, seed: int | None = None) -> tuple[dict[str, float | int], dict[str, object]]:
        if seed is not None:
            self.rng = np.random.default_rng(seed)
        indices = self.rng.integers(0, len(self.type_space), size=self.n_agents)
        self.true_types = self.type_space[indices].copy()
        self.t = 0
        self.state = self._sample_state(t=0)
        return self.state.to_dict(), {"true_types": self.true_types.copy(), "rule_names": RULES[: self.rule_count]}

    def _sample_state(self, t: int) -> CourierState:
        pay = float(np.round(self.rng.uniform(0.35, 1.8), 3))
        menu_pay = float(np.round(self.rng.uniform(0.35, 1.8), 3))
        return CourierState(
            long_trip=int(self.rng.random() < 0.35),
            leaves_zone=int(self.rng.random() < 0.40),
            home_ward=int(self.rng.random() < 0.35),
            surge=int(self.rng.random() < 0.30),
            pay=pay,
            after_deadline=int(self.rng.random() < 0.45),
            congestion=float(np.round(self.rng.uniform(0.0, 0.7), 3)),
            menu_long_trip=int(self.rng.random() < 0.35),
            menu_leaves_zone=int(self.rng.random() < 0.40),
            menu_home_ward=int(self.rng.random() < 0.35),
            menu_surge=int(self.rng.random() < 0.30),
            menu_pay=menu_pay,
            t=t,
        )

    def sample_candidate_states(self, count: int) -> list[CourierState]:
        return [self._sample_state(t=self.t) for _ in range(int(count))]

    def step(self, joint_action: Iterable[int]) -> tuple[dict[str, float | int], np.ndarray, bool, bool, dict[str, object]]:
        joint = np.asarray(list(joint_action), dtype=int)
        if joint.shape != (self.n_agents,):
            raise ValueError(f"joint_action must have shape ({self.n_agents},)")
        rewards = self.reward_fn(self.state, joint, self.true_types)
        accepted = int(np.sum((joint == ACCEPT) | (joint == CHOOSE_FROM_MENU)))
        repositioned = int(np.sum(joint == REPOSITION))
        next_congestion = min(1.0, max(0.0, 0.55 * self.state.congestion + 0.12 * accepted - 0.08 * repositioned))
        self.t += 1
        next_state = self._sample_state(t=self.t)
        self.state = CourierState(
            long_trip=next_state.long_trip,
            leaves_zone=next_state.leaves_zone,
            home_ward=next_state.home_ward,
            surge=next_state.surge,
            pay=next_state.pay,
            after_deadline=next_state.after_deadline,
            congestion=float(np.round(next_congestion, 3)),
            menu_long_trip=next_state.menu_long_trip,
            menu_leaves_zone=next_state.menu_leaves_zone,
            menu_home_ward=next_state.menu_home_ward,
            menu_surge=next_state.menu_surge,
            menu_pay=next_state.menu_pay,
            t=self.t,
        )
        terminated = self.t >= self.horizon
        return self.state.to_dict(), rewards, terminated, False, {"accepted": accepted, "repositioned": repositioned, "menu_chosen": int(np.sum(joint == CHOOSE_FROM_MENU))}

    def menu_state(self, state: CourierState) -> CourierState:
        return CourierState(
            long_trip=state.menu_long_trip,
            leaves_zone=state.menu_leaves_zone,
            home_ward=state.menu_home_ward,
            surge=state.menu_surge,
            pay=state.menu_pay,
            after_deadline=state.after_deadline,
            congestion=state.congestion,
            menu_long_trip=state.long_trip,
            menu_leaves_zone=state.leaves_zone,
            menu_home_ward=state.home_ward,
            menu_surge=state.surge,
            menu_pay=state.pay,
            t=state.t,
        )

    def base_accept_utility(self, state: CourierState, rule_tuple: np.ndarray) -> float:
        rules = self._pad_rules(rule_tuple)
        avoid_long, zone_loyal, home_pull, surge_only = rules
        home_term = home_pull * state.after_deadline * (self.home_scale * state.home_ward - self.penalty_scale * (1 - state.home_ward))
        return (
            float(state.pay)
            + 0.4 * state.surge
            - self.penalty_scale * avoid_long * state.long_trip
            - self.penalty_scale * zone_loyal * state.leaves_zone
            - self.penalty_scale * surge_only * (1 - state.surge)
            + home_term
        )

    def action_utilities(self, state: CourierState, rule_tuple: np.ndarray) -> np.ndarray:
        rules = self._pad_rules(rule_tuple)
        avoid_long, zone_loyal, home_pull, surge_only = rules
        utilities = np.zeros(len(ACTIONS), dtype=float)
        accept = self.base_accept_utility(state, rule_tuple) - 0.5 * state.congestion
        utilities[ACCEPT] = accept
        low_pay = max(0.0, 0.9 - float(state.pay))
        away_from_home = state.after_deadline * (1 - state.home_ward)
        no_surge = 1 - state.surge
        utilities[DECLINE_A] = -0.18 + low_pay + 0.30 * avoid_long * state.long_trip + 0.20 * surge_only * no_surge
        utilities[DECLINE_B] = -0.22 + 0.90 * avoid_long * state.long_trip + 0.35 * zone_loyal * state.leaves_zone + 0.25 * home_pull * away_from_home + 0.10 * state.long_trip
        utilities[DECLINE_C] = -0.22 + 0.90 * zone_loyal * state.leaves_zone + 0.40 * home_pull * away_from_home + 0.20 * low_pay
        utilities[DECLINE_D] = -0.22 + 0.95 * surge_only * no_surge + 0.30 * avoid_long * state.long_trip + 0.20 * zone_loyal * state.leaves_zone + 0.10 * no_surge
        utilities[REPOSITION] = -0.20 + 1.55 * home_pull * state.after_deadline * (1 - state.home_ward) + 0.20 * state.after_deadline
        menu_accept = self.base_accept_utility(self.menu_state(state), rule_tuple) - self.menu_friction - 0.35 * state.congestion
        current_pain = (
            avoid_long * state.long_trip
            + zone_loyal * state.leaves_zone
            + surge_only * (1 - state.surge)
            + home_pull * state.after_deadline * (1 - state.home_ward)
        )
        menu_relief = (
            avoid_long * max(0, state.long_trip - state.menu_long_trip)
            + zone_loyal * max(0, state.leaves_zone - state.menu_leaves_zone)
            + surge_only * max(0, state.menu_surge - state.surge)
            + home_pull * state.after_deadline * max(0, state.menu_home_ward - state.home_ward)
        )
        utilities[CHOOSE_FROM_MENU] = menu_accept + 0.35 * menu_relief + 0.12 * current_pain
        return utilities

    def likelihood(self, action: int, state: CourierState | dict[str, float | int], theta: Iterable[int], menu: object | None = None) -> float:
        state_obj = state_from_dict(state) if isinstance(state, dict) else state
        rule_tuple = np.asarray(list(theta), dtype=int)
        probs = softmax(self.action_utilities(state_obj, rule_tuple), self.tau)
        return float(probs[int(action)])

    def message_likelihood(self, message: int, state: CourierState | dict[str, float | int], theta: Iterable[int]) -> float:
        state_obj = state_from_dict(state) if isinstance(state, dict) else state
        rules = self._pad_rules(theta)
        avoid_long, zone_loyal, home_pull, surge_only = rules
        utilities = np.zeros(len(MESSAGES), dtype=float)
        low_pay = max(0.0, 0.9 - float(state_obj.pay))
        away_from_home = state_obj.after_deadline * (1 - state_obj.home_ward)
        no_surge = 1 - state_obj.surge
        menu_relief = (
            max(0, state_obj.long_trip - state_obj.menu_long_trip)
            + max(0, state_obj.leaves_zone - state_obj.menu_leaves_zone)
            + max(0, state_obj.menu_surge - state_obj.surge)
            + state_obj.after_deadline * max(0, state_obj.menu_home_ward - state_obj.home_ward)
        )
        utilities[MSG_NONE] = 0.15
        utilities[MSG_A] = 0.35 * low_pay + 0.35 * avoid_long * state_obj.long_trip + 0.20 * surge_only * no_surge
        utilities[MSG_B] = 0.45 * zone_loyal * state_obj.leaves_zone + 0.35 * home_pull * away_from_home + 0.15 * state_obj.congestion
        utilities[MSG_C] = 0.25 * menu_relief + 0.20 * avoid_long * state_obj.long_trip + 0.20 * zone_loyal * state_obj.leaves_zone + 0.20 * home_pull * away_from_home + 0.20 * surge_only * no_surge
        utilities[MSG_D] = 0.20 * (1 - zone_loyal) + 0.15 * state_obj.surge + 0.10 * (1 - avoid_long)
        return float(softmax(utilities, max(self.tau, 0.25))[int(message)])

    def simulate_action(
        self,
        state: CourierState,
        theta: np.ndarray,
        rng: np.random.Generator | None = None,
        *,
        agent: int | None = None,
        all_types: np.ndarray | None = None,
    ) -> int:
        generator = rng or self.rng
        utilities = self.action_utilities(state, theta)
        if self.couple_lambda and agent is not None and all_types is not None:
            utilities = utilities.copy()
            for action in range(len(ACTIONS)):
                utilities[action] += self.couple_lambda * self._coupled_type_term(int(agent), state, int(action), np.asarray(all_types, dtype=int))
        probs = softmax(utilities, self.tau)
        return int(generator.choice(len(ACTIONS), p=probs))

    def simulate_message(
        self,
        state: CourierState,
        theta: np.ndarray,
        rng: np.random.Generator | None = None,
    ) -> int:
        generator = rng or self.rng
        probs = np.asarray([self.message_likelihood(message, state, theta) for message in range(len(MESSAGES))], dtype=float)
        probs /= float(probs.sum())
        return int(generator.choice(len(MESSAGES), p=probs))

    def reward_fn(
        self,
        state: CourierState | dict[str, float | int],
        joint_action: Iterable[int],
        types: np.ndarray,
    ) -> np.ndarray:
        state_obj = state_from_dict(state) if isinstance(state, dict) else state
        joint = np.asarray(list(joint_action), dtype=int)
        type_arr = np.asarray(types, dtype=int)
        accepted = int(np.sum((joint == ACCEPT) | (joint == CHOOSE_FROM_MENU)))
        public_congestion = float(state_obj.congestion + 0.25 * max(0, accepted - 1))
        rewards = np.zeros(self.n_agents, dtype=float)
        for i in range(self.n_agents):
            own_type = type_arr[i]
            action = int(joint[i])
            if action == ACCEPT:
                reward = self.base_accept_utility(state_obj, own_type) - 0.5 * public_congestion
            elif action == CHOOSE_FROM_MENU:
                reward = self.base_accept_utility(self.menu_state(state_obj), own_type) - self.menu_friction - 0.45 * public_congestion
            elif action == REPOSITION:
                rules = self._pad_rules(own_type)
                home_pull = rules[2]
                reward = -0.08 + 0.45 * home_pull * state_obj.after_deadline * (1 - state_obj.home_ward)
            else:
                reward = -0.06
            if self.couple_lambda:
                reward += self.couple_lambda * self._coupled_type_term(i, state_obj, action, type_arr)
            rewards[i] = float(reward)
        return rewards

    def _coupled_type_term(self, agent: int, state: CourierState, action: int, types: np.ndarray) -> float:
        if self.n_agents <= 1:
            return 0.0
        own_rules = self._pad_rules(types[agent])
        partner_values = []
        for j in range(self.n_agents):
            if j == agent:
                continue
            partner_rules = self._pad_rules(types[j])
            # Stress term: payoff is better when accepting while partners are
            # unlikely to reject the same order for hidden operational reasons.
            partner_reject_pressure = (
                partner_rules[0] * state.long_trip
                + partner_rules[1] * state.leaves_zone
                + partner_rules[3] * (1 - state.surge)
                + partner_rules[2] * state.after_deadline * (1 - state.home_ward)
            ) / 4.0
            own_accept_need = 1.0 if action in {ACCEPT, CHOOSE_FROM_MENU} else -0.35
            partner_values.append(own_accept_need * (0.5 - partner_reject_pressure) + 0.1 * own_rules[1] * partner_rules[1])
        return float(np.mean(partner_values))

    def _pad_rules(self, rule_tuple: Iterable[int]) -> np.ndarray:
        arr = np.zeros(len(RULES), dtype=int)
        raw = np.asarray(list(rule_tuple), dtype=int)
        arr[: len(raw)] = raw
        return arr

    def assert_transition_independence(self, seed: int = 7) -> None:
        env_a = CourierDispatchEnv(self.n_agents, self.rule_count, self.horizon, self.tau, self.penalty_scale, self.home_scale, self.menu_friction, self.couple_lambda, seed)
        env_b = CourierDispatchEnv(self.n_agents, self.rule_count, self.horizon, self.tau, self.penalty_scale, self.home_scale, self.menu_friction, self.couple_lambda, seed)
        env_a.reset(seed)
        env_b.reset(seed)
        joint = np.full(self.n_agents, ACCEPT, dtype=int)
        next_a, *_ = env_a.step(joint)
        # Perturb hidden types only. Same public state, action, and RNG seed
        # must produce the same transition because theta is not used in step().
        env_b.true_types = 1 - env_b.true_types
        next_b, *_ = env_b.step(joint)
        if next_a != next_b:
            raise AssertionError("TI violated: transition changed after hidden-type perturbation")

    def assert_reward_locality(self) -> None:
        if self.couple_lambda != 0.0:
            raise AssertionError("Reward locality is intentionally violated when couple_lambda != 0")
        state = CourierState(1, 1, 0, 0, 1.0, 1, 0.2)
        joint = np.full(self.n_agents, ACCEPT, dtype=int)
        types = np.zeros((self.n_agents, self.rule_count), dtype=int)
        baseline = self.reward_fn(state, joint, types)
        for driver in range(self.n_agents):
            for other in range(self.n_agents):
                if other == driver:
                    continue
                perturbed = types.copy()
                perturbed[other] = 1 - perturbed[other]
                check = self.reward_fn(state, joint, perturbed)
                if abs(check[driver] - baseline[driver]) > 1e-12:
                    raise AssertionError("RL violated at couple_lambda=0")

    def assert_prior_factorization(self, seed: int = 11) -> None:
        rng = np.random.default_rng(seed)
        samples = self.type_space[rng.integers(0, len(self.type_space), size=(2048, self.n_agents))]
        # Weak smoke check: each driver's empirical marginal should be close to
        # uniform independent draws over the enumerable type grid.
        for driver in range(self.n_agents):
            counts = np.zeros(len(self.type_space), dtype=float)
            for sample in samples[:, driver, :]:
                idx = np.where(np.all(self.type_space == sample, axis=1))[0][0]
                counts[idx] += 1
            empirical = counts / counts.sum()
            if float(np.max(np.abs(empirical - 1.0 / len(self.type_space)))) > 0.04:
                raise AssertionError("PF smoke check failed: empirical marginal not close to uniform")
