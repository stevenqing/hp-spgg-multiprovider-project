"""Memory-aware analytic HP-SPGG primitives for additive scaling experiments."""

from __future__ import annotations

from dataclasses import dataclass
import math
import time
from typing import Iterable

import numpy as np

from .environment import ACTIONS
from .personas import PERSONAS


SIGMA = 0.08
RHO_THRESHOLD = 1e-3
JOINT_BYTE_CAP = 4_000_000_000
JOINT_UPDATE_SECONDS_CAP = 1.0
PLANNER_EVALUATION_CAP = 2**24
PARAMETER_NAMES = ("target_contribution", "cooperation_weight", "self_interest_weight", "fairness_weight")
BASE_PARAMETERS = np.asarray(
    [
        [
            persona.target_contribution,
            persona.cooperation_weight,
            persona.self_interest_weight,
            persona.fairness_weight,
        ]
        for persona in PERSONAS
    ],
    dtype=float,
)


@dataclass(frozen=True)
class TypeLibrary:
    size: int
    parameters: np.ndarray
    labels: tuple[str, ...]
    synthesis: str
    initial_rho_hat: float | None
    respaced: bool


@dataclass(frozen=True)
class JointProbe:
    feasible: bool
    rule: str
    elapsed_seconds: float | None
    entries_processed: int
    total_entries: int
    table_bytes: int


def squared_hellinger_gaussians(left: np.ndarray, right: np.ndarray, sigma: float = SIGMA) -> np.ndarray:
    """Squared Hellinger distance for equal-variance Gaussian channels."""
    return 1.0 - np.exp(-((np.asarray(left) - np.asarray(right)) ** 2) / (8.0 * sigma**2))


def _interpolated_parameters(size: int) -> np.ndarray:
    locations = np.linspace(0.0, 1.0, len(BASE_PARAMETERS))
    target = np.linspace(0.0, 1.0, size)
    return np.column_stack(
        [np.interp(target, locations, BASE_PARAMETERS[:, column]) for column in range(BASE_PARAMETERS.shape[1])]
    )


def _respaced_parameters(size: int) -> np.ndarray:
    """Monotone grid within the coordinate bounds of the four archetypes.

    A direct interpolation through the archetypes creates crossing reward
    channels.  This re-spaced line keeps all four parameter coordinates inside
    the archetype bounding box while making channel order monotone.  The exact
    Hellinger gate is still checked after construction.
    """
    z = np.linspace(0.0, 1.0, size)
    return np.column_stack(
        [
            np.full(size, 0.5),
            0.10 + 1.10 * z,
            0.15 + 0.95 * z,
            0.15 + 0.85 * z,
        ]
    )


def synthesize_type_library(size: int) -> TypeLibrary:
    if size == 4:
        return TypeLibrary(
            size=4,
            parameters=BASE_PARAMETERS.copy(),
            labels=tuple(persona.key for persona in PERSONAS),
            synthesis="retained four-archetype Fischbacher-Gaechter-Fehr library",
            initial_rho_hat=None,
            respaced=False,
        )
    if size not in {8, 16}:
        raise ValueError(f"supported type-library sizes are 4, 8, and 16; got {size}")
    initial = _interpolated_parameters(size)
    initial_rho = rho_hat_for_parameters(initial, n=3)
    if initial_rho >= RHO_THRESHOLD:
        parameters = initial
        respaced = False
        synthesis = "piecewise-linear interpolation through four archetypes"
    else:
        parameters = _respaced_parameters(size)
        respaced = True
        synthesis = "re-spaced monotone grid inside four-archetype parameter bounds"
    final_rho = rho_hat_for_parameters(parameters, n=3)
    if final_rho < RHO_THRESHOLD:
        raise AssertionError(
            f"m={size} synthetic type grid fails rho gate after re-spacing: {final_rho} < {RHO_THRESHOLD}"
        )
    labels = tuple(f"synthetic_{index:02d}" for index in range(size))
    return TypeLibrary(size, parameters, labels, synthesis, initial_rho, respaced)


def local_reward_lookup(n: int, parameters: np.ndarray) -> np.ndarray:
    """Reward[type, own action index, total contribution units]."""
    if n < 2:
        raise ValueError("HP-SPGG scaling requires n >= 2")
    parameters = np.asarray(parameters, dtype=float)
    m = len(parameters)
    max_total_units = 4 * n
    lookup = np.full((m, len(ACTIONS), max_total_units + 1), np.nan, dtype=float)
    target, cooperation, self_interest, fairness = parameters.T
    for own_index, own in enumerate(ACTIONS):
        own_units = int(round(float(own) * 4.0))
        for total_units in range(max_total_units + 1):
            other_units = total_units - own_units
            if other_units < 0 or other_units > 4 * (n - 1):
                continue
            mean_all = (float(total_units) / 4.0) / n
            mean_other = (float(other_units) / 4.0) / (n - 1)
            reward = (
                0.72 * mean_all
                + 0.50 * (1.0 - float(own)) * self_interest
                + 0.38 * cooperation * (1.0 - np.abs(float(own) - target))
                + 0.18 * fairness * (1.0 - abs(float(own) - mean_other))
            ) / 1.8
            lookup[:, own_index, total_units] = np.clip(reward, 0.0, 1.0)
    return lookup


def rho_hat_from_lookup(lookup: np.ndarray, sigma: float = SIGMA) -> tuple[float, dict[str, object]]:
    m = lookup.shape[0]
    best = math.inf
    witness: dict[str, object] = {}
    for own_index in range(lookup.shape[1]):
        for total_units in range(lookup.shape[2]):
            values = lookup[:, own_index, total_units]
            if not np.all(np.isfinite(values)):
                continue
            distances = squared_hellinger_gaussians(values[:, None], values[None, :], sigma=sigma)
            distances[np.tril_indices(m)] = np.inf
            pair = np.unravel_index(int(np.argmin(distances)), distances.shape)
            value = float(distances[pair])
            if value < best:
                best = value
                witness = {
                    "own_action": float(ACTIONS[own_index]),
                    "total_contribution": float(total_units) / 4.0,
                    "type_pair": [int(pair[0]), int(pair[1])],
                    "channel_means": [float(values[pair[0]]), float(values[pair[1]])],
                }
    if not math.isfinite(best):
        raise AssertionError("could not compute rho_hat over reachable action grid")
    return best, witness


def rho_hat_for_parameters(parameters: np.ndarray, n: int, sigma: float = SIGMA) -> float:
    return rho_hat_from_lookup(local_reward_lookup(n, parameters), sigma=sigma)[0]


class ActionProfileGrid:
    """Vectorized exhaustive joint-action grid in itertools.product order."""

    def __init__(self, n: int, action_values: np.ndarray = ACTIONS) -> None:
        self.n = int(n)
        self.action_values = np.asarray(action_values, dtype=float)
        self.action_count = len(self.action_values)
        self.profile_count = int(self.action_count**self.n)
        self.planner_feasible = self.profile_count <= PLANNER_EVALUATION_CAP
        self.powers = self.action_count ** np.arange(self.n - 1, -1, -1, dtype=np.int64)
        self.digits: np.ndarray | None = None
        self.total_units: np.ndarray | None = None
        self.spread: np.ndarray | None = None
        if self.planner_feasible:
            indices = np.arange(self.profile_count, dtype=np.int64)
            self.digits = ((indices[:, None] // self.powers[None, :]) % self.action_count).astype(np.uint8)
            self.total_units = self.digits.sum(axis=1, dtype=np.uint8)
            actions = self.action_values[self.digits]
            self.spread = np.std(actions, axis=1).astype(np.float32)

    @property
    def allocated_bytes(self) -> int:
        return int(
            sum(array.nbytes for array in (self.digits, self.total_units, self.spread) if array is not None)
        )

    def profile_digits(self, index: int) -> np.ndarray:
        if self.digits is None:
            raise RuntimeError("planner grid is infeasible")
        return np.asarray(self.digits[int(index)], dtype=int)


class AnalyticPlanner:
    def __init__(self, n: int, parameters: np.ndarray, beta: float = 0.25) -> None:
        self.n = int(n)
        self.parameters = np.asarray(parameters, dtype=float)
        self.m = len(parameters)
        self.beta = float(beta)
        self.grid = ActionProfileGrid(n)
        if not self.grid.planner_feasible:
            raise ValueError(
                f"planner cap exceeded: {self.grid.profile_count} > {PLANNER_EVALUATION_CAP}"
            )
        assert self.grid.digits is not None and self.grid.total_units is not None
        self.lookup = local_reward_lookup(n, parameters)
        self.variance_lookup = np.var(self.lookup, axis=0)
        self.type_plan_cache: dict[tuple[int, ...], int] = {}
        self.type_cache_hits = 0
        self.type_cache_misses = 0

    @property
    def allocated_bytes(self) -> int:
        return self.grid.allocated_bytes + self.lookup.nbytes + self.variance_lookup.nbytes

    def _argmax(self, scores: np.ndarray) -> int:
        return int(np.argmax(scores))

    def plan_types(self, type_profile: np.ndarray) -> int:
        key = tuple(int(value) for value in np.asarray(type_profile, dtype=int))
        cached = self.type_plan_cache.get(key)
        if cached is not None:
            self.type_cache_hits += 1
            return cached
        self.type_cache_misses += 1
        digits = self.grid.digits
        totals = self.grid.total_units
        assert digits is not None and totals is not None
        types = np.asarray(key, dtype=int)
        scores = np.zeros(self.grid.profile_count, dtype=float)
        for agent in range(self.n):
            scores += self.lookup[types[agent], digits[:, agent], totals]
        action = self._argmax(scores)
        self.type_plan_cache[key] = action
        return action

    def plan_posterior(self, posterior: np.ndarray, bonus: bool) -> int:
        digits = self.grid.digits
        totals = self.grid.total_units
        assert digits is not None and totals is not None
        posterior = np.asarray(posterior, dtype=float)
        scores = np.zeros(self.grid.profile_count, dtype=float)
        bonus_coefficient = np.zeros(self.grid.profile_count, dtype=float) if bonus else None
        uncertainty = 1.0 - np.max(posterior, axis=1)
        for agent in range(self.n):
            expected_lookup = np.tensordot(posterior[agent], self.lookup, axes=(0, 0))
            scores += expected_lookup[digits[:, agent], totals]
            if bonus and bonus_coefficient is not None:
                bonus_coefficient += uncertainty[agent] * self.variance_lookup[digits[:, agent], totals]
        if bonus and bonus_coefficient is not None:
            scores += self.beta * bonus_coefficient
            assert self.grid.spread is not None
            scores += 0.05 * self.beta * self.grid.spread
        return self._argmax(scores)

    def rewards(self, true_types: np.ndarray, action_index: int) -> np.ndarray:
        digits = self.grid.profile_digits(action_index)
        total = int(np.sum(digits))
        return self.lookup[np.asarray(true_types, dtype=int), digits, total]

    def welfare(self, true_types: np.ndarray, action_index: int) -> float:
        return float(np.sum(self.rewards(true_types, action_index)))


def sample_marginals(posterior: np.ndarray, uniforms: np.ndarray) -> np.ndarray:
    posterior = np.asarray(posterior, dtype=float)
    uniforms = np.asarray(uniforms, dtype=float)
    output = np.empty(posterior.shape[0], dtype=int)
    for agent in range(posterior.shape[0]):
        cdf = np.cumsum(posterior[agent])
        output[agent] = int(
            np.searchsorted(cdf, min(float(uniforms[agent]), np.nextafter(1.0, 0.0)), side="right")
        )
    return output


def local_likelihoods(
    lookup: np.ndarray,
    action_digits: np.ndarray,
    total_units: int,
    observed_rewards: np.ndarray,
    sigma: float = SIGMA,
) -> np.ndarray:
    n = len(action_digits)
    m = lookup.shape[0]
    likelihoods = np.empty((n, m), dtype=float)
    for agent in range(n):
        expected = lookup[:, int(action_digits[agent]), int(total_units)]
        residual = float(observed_rewards[agent]) - expected
        likelihoods[agent] = np.exp(-0.5 * (residual / sigma) ** 2) + 1e-9
    return likelihoods


def update_factored(posterior: np.ndarray, likelihoods: np.ndarray) -> np.ndarray:
    posterior *= likelihoods
    totals = posterior.sum(axis=1, keepdims=True)
    invalid = (~np.isfinite(totals)) | (totals <= 0.0)
    totals[invalid] = 1.0
    posterior /= totals
    for agent in np.where(invalid[:, 0])[0]:
        posterior[agent] = 1.0 / posterior.shape[1]
    return posterior


def joint_marginals(joint: np.ndarray, n: int, m: int) -> np.ndarray:
    view = joint.reshape((m,) * n)
    output = np.empty((n, m), dtype=float)
    for agent in range(n):
        moved = np.moveaxis(view, agent, 0)
        output[agent] = moved.reshape(m, -1).sum(axis=1)
    output /= output.sum(axis=1, keepdims=True)
    return output


def update_explicit_joint(
    joint: np.ndarray,
    likelihoods: np.ndarray,
    *,
    return_marginals: bool = True,
) -> tuple[np.ndarray, np.ndarray | None, float]:
    n, m = likelihoods.shape
    start = time.perf_counter()
    view = joint.reshape((m,) * n)
    for agent in range(n):
        shape = [1] * n
        shape[agent] = m
        view *= likelihoods[agent].reshape(shape)
    total = float(joint.sum())
    if not math.isfinite(total) or total <= 0.0:
        joint.fill(1.0 / len(joint))
    else:
        joint /= total
    marginals = joint_marginals(joint, n, m) if return_marginals else None
    elapsed = time.perf_counter() - start
    return joint, marginals, elapsed


def probe_joint_update(n: int, m: int, likelihoods: np.ndarray) -> JointProbe:
    entries = int(m**n)
    table_bytes = entries * np.dtype(np.float64).itemsize
    if table_bytes > JOINT_BYTE_CAP:
        return JointProbe(False, "joint_table_gt_4GB", None, 0, entries, table_bytes)

    # Exact full-table probe while the table is modest enough to allocate.
    if entries <= 20_000_000:
        joint = np.full(entries, 1.0 / entries, dtype=float)
        _, _, elapsed = update_explicit_joint(joint, likelihoods, return_marginals=True)
        feasible = elapsed <= JOINT_UPDATE_SECONDS_CAP
        return JointProbe(
            feasible,
            "none" if feasible else "first_update_gt_1s",
            elapsed,
            entries,
            entries,
            table_bytes,
        )

    # For a larger below-byte-cap table, execute the exact first-update kernel
    # in chunks and stop only after elapsed wall-clock itself exceeds one second.
    # Once that occurs the complete update cannot satisfy the hard cap.
    start = time.perf_counter()
    processed = 0
    chunk_size = 1_000_000
    powers = m ** np.arange(n - 1, -1, -1, dtype=np.int64)
    while processed < entries:
        stop = min(entries, processed + chunk_size)
        indices = np.arange(processed, stop, dtype=np.int64)
        digits = ((indices[:, None] // powers[None, :]) % m).astype(np.int16)
        weights = np.ones(stop - processed, dtype=float)
        for agent in range(n):
            weights *= likelihoods[agent, digits[:, agent]]
        _ = float(weights.sum())
        processed = stop
        elapsed = time.perf_counter() - start
        if elapsed > JOINT_UPDATE_SECONDS_CAP:
            return JointProbe(False, "first_update_gt_1s", elapsed, processed, entries, table_bytes)
    elapsed = time.perf_counter() - start
    return JointProbe(True, "none", elapsed, entries, entries, table_bytes)


def posterior_true_mass(posterior: np.ndarray, true_types: np.ndarray) -> np.ndarray:
    return posterior[np.arange(len(true_types)), np.asarray(true_types, dtype=int)]


def first_passage(mass_history: np.ndarray, threshold: float = 0.9) -> tuple[np.ndarray, float]:
    history = np.asarray(mass_history, dtype=float)
    per_agent = np.full(history.shape[1], np.nan, dtype=float)
    for agent in range(history.shape[1]):
        hits = np.where(history[:, agent] > threshold)[0]
        if len(hits):
            per_agent[agent] = float(hits[0] + 1)
    all_hits = np.where(np.all(history > threshold, axis=1))[0]
    all_agents = float(all_hits[0] + 1) if len(all_hits) else math.nan
    return per_agent, all_agents


def r_squared_linear(mean_cumulative_regret: np.ndarray) -> float:
    y = np.asarray(mean_cumulative_regret, dtype=float)
    x = np.arange(1, len(y) + 1, dtype=float)
    coefficients = np.polyfit(x, y, 1)
    predicted = np.polyval(coefficients, x)
    denominator = float(np.sum((y - y.mean()) ** 2))
    if denominator <= 0.0:
        return 1.0 if np.allclose(y, predicted) else 0.0
    return 1.0 - float(np.sum((y - predicted) ** 2)) / denominator


def dgp_probes(n: int, library: TypeLibrary, seed: int) -> dict[str, object]:
    rng = np.random.default_rng(seed)
    first = rng.integers(0, library.size, size=n)
    replay = np.random.default_rng(seed).integers(0, library.size, size=n)
    lookup = local_reward_lookup(n, library.parameters)
    pf = bool(np.array_equal(first, replay))
    ti = True  # The analytic substrate has no persona-dependent transition kernel.
    # Reward lookup has one type axis and no axes for other agents' types.
    rl = bool(lookup.shape == (library.size, len(ACTIONS), 4 * n + 1))
    return {
        "seed": int(seed),
        "true_types": first.tolist(),
        "pf_pass": pf,
        "ti_pass": ti,
        "rl_pass": rl,
        "all_pass": bool(pf and ti and rl),
    }


def cell_seed_stream(seed: int, n: int, m: int, episodes: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    true_types = rng.integers(0, m, size=n)
    uniforms = rng.random((episodes, n))
    return true_types, uniforms


def median_first_passage(values: Iterable[float]) -> tuple[float, int]:
    array = np.asarray(list(values), dtype=float)
    finite = array[np.isfinite(array)]
    censored = int(len(array) - len(finite))
    if len(finite) < math.ceil(len(array) / 2):
        return math.nan, censored
    return float(np.median(finite)), censored
