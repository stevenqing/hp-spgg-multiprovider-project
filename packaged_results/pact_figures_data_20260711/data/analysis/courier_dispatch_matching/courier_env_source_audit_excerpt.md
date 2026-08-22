# CourierDispatch-Rules Source Audit Excerpt

This note records the source paths and core implementation used by the current CloudGPT structured-solver matching results.

Source files:

- `llm_courier_dispatch/dispatch_env.py`
- `llm_courier_dispatch/matching_dispatch.py`
- `llm_courier_dispatch/live_structured_matching_dispatch.py`

Headline result file:

- `analysis/courier_dispatch_matching/courier_matching_structured_live_expected_pact_masked_type_stress_s5h8_allmodels_summary.json`

## Environment Constants

```python
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
```

## State And Type Space

```python
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


def enumerate_rule_types(rule_count: int = len(RULES)) -> np.ndarray:
    return np.asarray(list(product([0, 1], repeat=rule_count)), dtype=int)


def softmax(values: np.ndarray, tau: float) -> np.ndarray:
    tau = max(float(tau), 1e-9)
    scaled = np.asarray(values, dtype=float) / tau
    scaled -= float(np.max(scaled))
    exp = np.exp(scaled)
    return exp / float(exp.sum())
```

## Rule Posterior Update

```python
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
```

## Menu State And Accept Utility

`choose-from-menu` evaluates the alternate menu order by swapping current/menu public fields through `menu_state`, subtracting menu friction, and adding menu-relief shaping in the action utility.

```python
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
```

## Action Utilities And Likelihood

```python
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
```

## Reward Function

```python
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
```

## Transition Independence, Reward Locality, Prior Factorization Self-Checks

```python
def assert_transition_independence(self, seed: int = 7) -> None:
    env_a = CourierDispatchEnv(self.n_agents, self.rule_count, self.horizon, self.tau, self.penalty_scale, self.home_scale, self.menu_friction, self.couple_lambda, seed)
    env_b = CourierDispatchEnv(self.n_agents, self.rule_count, self.horizon, self.tau, self.penalty_scale, self.home_scale, self.menu_friction, self.couple_lambda, seed)
    env_a.reset(seed)
    env_b.reset(seed)
    joint = np.full(self.n_agents, ACCEPT, dtype=int)
    next_a, *_ = env_a.step(joint)
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
    for driver in range(self.n_agents):
        counts = np.zeros(len(self.type_space), dtype=float)
        for sample in samples[:, driver, :]:
            idx = np.where(np.all(self.type_space == sample, axis=1))[0][0]
            counts[idx] += 1
        empirical = counts / counts.sum()
        if float(np.max(np.abs(empirical - 1.0 / len(self.type_space)))) > 0.04:
            raise AssertionError("PF smoke check failed: empirical marginal not close to uniform")
```

## Matching Expected Reward

```python
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
```

## Exact Factored Posterior Exploitation

PACT and PACT+ now use this exact factored posterior value for exploitation. If the type grid is too large, it falls back to Monte Carlo sampling.

```python
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
    ...
```

The implementation vectorizes exact enumeration over all independent driver type profiles and reproduces slow exact enumeration to numerical precision.

## PACT+ Disagreement Bonus D

The implemented disagreement bonus is local to each assigned driver/order. For each driver, it computes the posterior-pair expected absolute difference between type-conditioned one-driver values on that assigned order.

```python
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
```

## Structured Solver Objective

In the CloudGPT live structured runner, every method calls the LLM for driver-order score advice. For PACT+, the solver objective is

```text
objective(a) = E_{theta~posterior}[reward(a, theta)] + beta * D(a) + llm_score_weight * LLMScore(a)
```

where `D(a)` already includes the confidence/time gate.

```python
if method == "live_pact_plus":
    structured_scores = [
        expected_assignment_under_factored_posteriors(env, orders, assignment, posteriors, rng, posterior_samples)
        for assignment in assignments
    ]
    scale = pact_plus_exploration_scale(posteriors, round_index, horizon)
    bonuses = [scale * assignment_disagreement_bonus(env, orders, assignment, posteriors) for assignment in assignments]
...
if method == "live_pact_plus":
    objectives = [base + pact_plus_beta * bonus + llm_score_weight * llm for base, bonus, llm in zip(structured_scores, bonuses, llm_scores, strict=True)]
```

## Why PACT+ Can Have Lowest Regret But Lower Recovery

In this implementation, PACT+ is not optimizing posterior recovery directly. It optimizes immediate posterior expected assignment value plus a time/confidence-gated disagreement bonus. The gate is high early and decays over the horizon. Once the posterior is confident enough or the episode is late, the policy exploits high-value assignments. Therefore PACT+ can minimize regret by selecting assignments that are good under the current posterior while not necessarily querying the most type-diagnostic assignments all the way to the end. Joint-PSRL can maintain higher final type recovery because its joint posterior sampling keeps more type-directed variation, but that variation is not always regret-optimal in the short H=8 matching horizon.

## Audit Checks Run

Command:

```powershell
uv run python - <<'PY'
from itertools import product
import numpy as np
from llm_courier_dispatch.dispatch_env import CourierDispatchEnv, RulePosterior
from llm_courier_dispatch.matching_dispatch import all_assignments, expected_assignment_reward, expected_assignment_under_factored_posteriors, sample_order_pool

env = CourierDispatchEnv(n_agents=3, rule_count=4, horizon=8, couple_lambda=0.0, seed=7)
env.assert_transition_independence()
env.assert_reward_locality()
env.assert_prior_factorization()
print('TI_RL_PF_self_checks=pass')

env = CourierDispatchEnv(n_agents=3, rule_count=4, horizon=8, seed=123)
env.reset(123)
orders = sample_order_pool(env, 4, mode='type_stress')
posteriors = [RulePosterior(env.type_space) for _ in range(env.n_agents)]
for driver, posterior in enumerate(posteriors):
    action = env.simulate_action(orders[driver], env.true_types[driver], np.random.default_rng(200 + driver))
    posterior.update(env, orders[driver], action)

def slow_exact(assignment):
    probs = [posterior.probs() for posterior in posteriors]
    total = 0.0
    for profile in product(*[range(len(posterior.type_space)) for posterior in posteriors]):
        weight = 1.0
        types = []
        for driver, idx in enumerate(profile):
            weight *= probs[driver][idx]
            types.append(posteriors[driver].type_space[idx])
        total += weight * expected_assignment_reward(env, orders, assignment, np.asarray(types, dtype=int))
    return total

max_err = 0.0
for assignment in all_assignments(3, 4):
    fast = expected_assignment_under_factored_posteriors(env, orders, assignment, posteriors)
    slow = slow_exact(assignment)
    max_err = max(max_err, abs(fast - slow))
print('factored_value_max_abs_error', f'{max_err:.3e}')
PY
```

Observed output:

```text
TI_RL_PF_self_checks=pass
factored_value_max_abs_error 3.531e-14
```
