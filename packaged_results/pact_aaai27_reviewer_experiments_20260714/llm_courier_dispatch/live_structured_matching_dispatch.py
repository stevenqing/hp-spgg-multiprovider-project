"""Solver-backed live-LLM matching for CourierDispatch-Rules.

Every method calls the live LLM each round for bounded driver-order score
advice, but the final assignment is selected by a deterministic assignment
solver. This keeps the live-LLM requirement while restoring the structured
belief-to-decision path that the direct-prompt matching runner deliberately
left to the model.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_hpgg.llm_agent import backend_name, call_player, model_for  # noqa: E402
from llm_courier_dispatch.dispatch_env import ACTIONS, RULES, CourierDispatchEnv, RulePosterior  # noqa: E402
from llm_courier_dispatch.live_llm_dispatch import extract_json  # noqa: E402
from llm_courier_dispatch.live_matching_dispatch import (  # noqa: E402
    compact_matching_state,
    environment_model_spec,
    map_summary,
    posterior_summary,
    prompt_payload,
    sampled_rule_summary,
)
from llm_courier_dispatch.matching_dispatch import (  # noqa: E402
    JointRulePosterior,
    all_assignments,
    assignment_disagreement_bonus,
    expected_assignment_reward,
    expected_assignment_under_factored_posteriors,
    expected_assignment_under_posteriors,
    observed_actions_for_assignment,
    pact_plus_exploration_scale,
    realized_assignment_reward,
    sample_order_pool,
    update_joint_matching,
)


ANALYSIS_DIR = ROOT / "analysis" / "courier_dispatch_matching"
CACHE_PATH = ANALYSIS_DIR / "courier_matching_structured_live_llm_cache.json"
VERSION = "courier-matching-structured-live-planner-v1"
CACHE_LOCK = threading.Lock()

POSTERIOR_METHODS = {"live_pact", "live_pact_plus", "live_map_greedy", "live_joint_psrl"}
PROMPT_SCORE_METHODS = {
    "live_llm_greedy",
    "live_llm_belief",
    "live_atom_tom0",
    "live_atom_tom1",
    "live_atom_adaptive_hedge",
    "live_econ_bne",
}
DIRECT_METHODS = {"live_random", "live_llm_psrl_verbal"}
ALL_METHODS = POSTERIOR_METHODS | PROMPT_SCORE_METHODS | {"live_psrl_notype"} | DIRECT_METHODS


def parse_list(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def resolved_player_model(model_name: str | None) -> str:
    backend = backend_name("player")
    return model_for("player", backend, model_name)


def load_cache() -> dict[str, str]:
    with CACHE_LOCK:
        if CACHE_PATH.exists():
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        return {}


def save_cache(cache: dict[str, str]) -> None:
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = CACHE_PATH.with_suffix(f"{CACHE_PATH.suffix}.{uuid.uuid4().hex}.tmp")
    tmp_path.write_text(json.dumps(cache, indent=2), encoding="utf-8")
    tmp_path.replace(CACHE_PATH)


def cache_key(model: str, method: str, payload: dict[str, object]) -> str:
    raw = json.dumps(
        {
            "version": VERSION,
            "backend": os.getenv("LLM_HPGG_BACKEND", "anthropic"),
            "offline": os.getenv("LLM_HPGG_OFFLINE", "0"),
            "model": model,
            "method": method,
            "payload": payload,
        },
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def score_prompt_payload(
    *,
    method: str,
    round_index: int,
    orders: list,
    n_agents: int,
    history: list[dict[str, object]],
    max_history: int,
    feature_mode: str,
    posterior_summary_payload: list[dict[str, object]] | None = None,
    exploration_guidance: dict[str, object] | None = None,
    env_info_level: str = "none",
    tau: float = 0.5,
    penalty_scale: float = 2.0,
    home_scale: float = 1.2,
    menu_friction: float = 0.2,
    couple_lambda: float = 0.0,
) -> dict[str, object]:
    payload = prompt_payload(
        method=method,
        round_index=round_index,
        orders=orders,
        n_agents=n_agents,
        history=history,
        max_history=max_history,
        feature_mode=feature_mode,
        posterior_summary=posterior_summary_payload,
        exploration_guidance=exploration_guidance,
        env_info_level=env_info_level,
        tau=tau,
        penalty_scale=penalty_scale,
        home_scale=home_scale,
        menu_friction=menu_friction,
        couple_lambda=couple_lambda,
    )
    payload["task"] = "CourierDispatch-Rules solver-backed driver-order scoring"
    payload["objective"] = (
        f"{payload['objective']} Instead of choosing the assignment directly, score every driver-order pair. "
        "A deterministic solver will choose the final distinct assignment."
    )
    payload["score_scale"] = "Use numeric scores in [-2, 2]. Higher means better expected reward for that driver-order pair."
    payload["response_schema"] = {
        "driver_order_scores": [
            {"driver_id": "integer", "order_id": "integer", "score": "number"}
        ],
        "reason": "very short, at most 12 words",
    }
    payload["instruction"] = (
        "Return valid JSON only. Include one driver_order_scores entry for every driver_id and every order_id. "
        "Do not return a final assignment. Keep reason under 12 words."
    )
    return payload


def call_scorer(
    *,
    model: str,
    method: str,
    payload: dict[str, object],
    cache: dict[str, str],
    max_tokens: int,
    temperature: float,
) -> tuple[str, bool]:
    key = cache_key(model, method, payload)
    with CACHE_LOCK:
        if key in cache:
            return cache[key], True
    system = (
        "You are a careful dispatch platform scoring assistant in an online matching benchmark. "
        "You only see public order features, neutral action codes, and any method-specific belief summaries. "
        "Return JSON only."
    )
    reply = call_player(system, json.dumps(payload, indent=2), model=model, max_tokens=max_tokens, temperature=temperature)
    with CACHE_LOCK:
        cache[key] = reply
        save_cache(cache)
    return reply, False


def call_cached_llm(
    *,
    model: str,
    method: str,
    payload: dict[str, object],
    cache: dict[str, str],
    max_tokens: int,
    temperature: float,
    system: str,
) -> tuple[str, bool]:
    key = cache_key(model, method, payload)
    with CACHE_LOCK:
        if key in cache:
            return cache[key], True
    reply = call_player(system, json.dumps(payload, indent=2), model=model, max_tokens=max_tokens, temperature=temperature)
    with CACHE_LOCK:
        cache[key] = reply
        save_cache(cache)
    return reply, False


def _clip_score(value: object) -> float:
    try:
        return float(np.clip(float(value), -2.0, 2.0))
    except Exception:
        return 0.0


def _parse_score_entries_by_regex(reply: str, n_agents: int, order_count: int) -> tuple[np.ndarray, bool]:
    matrix = np.zeros((n_agents, order_count), dtype=float)
    filled = np.zeros((n_agents, order_count), dtype=bool)
    pattern = re.compile(
        r'"driver_id"\s*:\s*(\d+).*?"order_id"\s*:\s*(\d+).*?"score"\s*:\s*([-+]?\d+(?:\.\d+)?)',
        flags=re.S,
    )
    for match in pattern.finditer(reply):
        driver = int(match.group(1))
        order = int(match.group(2))
        if 0 <= driver < n_agents and 0 <= order < order_count:
            matrix[driver, order] = _clip_score(match.group(3))
            filled[driver, order] = True
    return matrix, bool(np.all(filled))


def _safe_reason(reply: str) -> str:
    try:
        return str(extract_json(reply).get("reason", ""))[:200]
    except Exception:
        match = re.search(r'"reason"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)', reply, flags=re.S)
        if not match:
            return ""
        return match.group(1).replace("\\n", " ")[:200]


def parse_score_matrix(reply: str, n_agents: int, order_count: int) -> tuple[np.ndarray, bool]:
    matrix = np.zeros((n_agents, order_count), dtype=float)
    filled = np.zeros((n_agents, order_count), dtype=bool)
    ok = True
    try:
        parsed = extract_json(reply)
    except Exception:
        return _parse_score_entries_by_regex(reply, n_agents, order_count)

    raw = parsed.get("driver_order_scores", parsed.get("scores", parsed.get("utilities", parsed.get("utility_matrix"))))
    if isinstance(raw, list) and raw and all(isinstance(item, dict) for item in raw):
        for item in raw:
            try:
                driver = int(item.get("driver_id", item.get("driver")))
                order = int(item.get("order_id", item.get("order")))
            except Exception:
                ok = False
                continue
            if 0 <= driver < n_agents and 0 <= order < order_count:
                matrix[driver, order] = _clip_score(item.get("score", item.get("value", 0.0)))
                filled[driver, order] = True
            else:
                ok = False
    elif isinstance(raw, list) and raw and all(isinstance(row, list) for row in raw):
        for driver, row in enumerate(raw[:n_agents]):
            for order, value in enumerate(row[:order_count]):
                matrix[driver, order] = _clip_score(value)
                filled[driver, order] = True
    elif isinstance(raw, dict):
        for driver_key, order_scores in raw.items():
            try:
                driver = int(str(driver_key).replace("driver", "").replace("_", ""))
            except Exception:
                ok = False
                continue
            if not isinstance(order_scores, dict) or not 0 <= driver < n_agents:
                ok = False
                continue
            for order_key, value in order_scores.items():
                try:
                    order = int(str(order_key).replace("order", "").replace("_", ""))
                except Exception:
                    ok = False
                    continue
                if 0 <= order < order_count:
                    matrix[driver, order] = _clip_score(value)
                    filled[driver, order] = True
                else:
                    ok = False
    else:
        nums = [float(match) for match in re.findall(r"[-+]?\d+(?:\.\d+)?", reply)]
        expected = n_agents * order_count
        if len(nums) >= expected:
            values = nums[-expected:]
            matrix = np.asarray(values, dtype=float).reshape(n_agents, order_count)
            matrix = np.clip(matrix, -2.0, 2.0)
            filled[:, :] = True
            ok = False
        else:
            return matrix, False

    if not bool(np.all(filled)):
        ok = False
    return matrix, ok


def initial_verbal_note(driver: int) -> str:
    return f"Driver {driver}: no evidence yet about this driver's hidden rule tuple; all 16 binary tuples are initially plausible."


def verbal_driver_history(history: list[dict[str, object]], driver: int, max_history: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for event in history[-max_history:]:
        assignment = event.get("assignment", [])
        observed_actions = event.get("observed_actions", [])
        assigned_order_features = event.get("assigned_order_features", [])
        if not isinstance(assignment, list) or driver >= len(assignment):
            continue
        item: dict[str, object] = {
            "round": event.get("round"),
            "assigned_order_id": assignment[driver],
            "observed_action": observed_actions[driver] if isinstance(observed_actions, list) and driver < len(observed_actions) else "unknown",
        }
        if isinstance(assigned_order_features, list) and driver < len(assigned_order_features):
            item["assigned_order_features"] = assigned_order_features[driver]
        rows.append(item)
    return rows


def verbal_decision_payload(
    *,
    method: str,
    round_index: int,
    orders: list,
    n_agents: int,
    history: list[dict[str, object]],
    max_history: int,
    feature_mode: str,
    belief_notes: list[str],
    env_info_level: str = "none",
    tau: float = 0.5,
    penalty_scale: float = 2.0,
    home_scale: float = 1.2,
    menu_friction: float = 0.2,
    couple_lambda: float = 0.0,
) -> dict[str, object]:
    return {
        "task": "CourierDispatch-Rules matching with LLM-PSRL-verbal",
        "round": round_index,
        "method": method,
        "objective": (
            "Maintain a natural-language belief note for each driver, verbally sample one hidden rule hypothesis per driver, "
            "then choose one distinct order_id for each driver_id to maximize expected reward under that sampled verbal hypothesis."
        ),
        "important_constraints": [
            "Do not use Bayes rule or numeric posterior probabilities.",
            "Use only the belief notes and public history to form a verbal Thompson-sampling-style hypothesis.",
            "Return one distinct order_id for each driver_id.",
            "Feature and rule codes are masked; do not infer semantic labels from code names.",
        ],
        "public_action_codes": list(ACTIONS),
        "drivers": [
            {
                "driver_id": driver,
                "current_belief_note": belief_notes[driver],
                "public_history": verbal_driver_history(history, driver, max_history),
            }
            for driver in range(n_agents)
        ],
        "orders": [{"order_id": idx, **compact_matching_state(order, feature_mode)} for idx, order in enumerate(orders)],
        "masked_rule_positions": [f"r{idx}" for idx in range(len(RULES))],
        "environment_model": environment_model_spec(
            feature_mode=feature_mode,
            env_info_level=env_info_level,
            tau=tau,
            penalty_scale=penalty_scale,
            home_scale=home_scale,
            menu_friction=menu_friction,
            couple_lambda=couple_lambda,
        ),
        "response_schema": {
            "belief_notes": [{"driver_id": "integer", "belief_note": "updated natural-language note under 80 words"}],
            "sampled_rule_hypotheses": [{"driver_id": "integer", "rules": {"r0": "0 or 1", "r1": "0 or 1", "r2": "0 or 1", "r3": "0 or 1"}}],
            "assignment": [{"driver_id": "integer", "order_id": "integer"}],
            "reason": "very short",
        },
        "instruction": "Return valid JSON only. Keep each belief_note concise and carry forward concrete evidence from public action codes.",
    }


def parse_verbal_decision(reply: str, n_agents: int, order_count: int, prior_notes: list[str]) -> tuple[tuple[int, ...], list[str], bool]:
    try:
        parsed = extract_json(reply)
    except Exception:
        return tuple(range(n_agents)), prior_notes, False

    assignment = [-1] * n_agents
    ok = True
    raw_assignment = parsed.get("assignment", parsed.get("assignments", []))
    if isinstance(raw_assignment, list):
        for idx, item in enumerate(raw_assignment):
            if not isinstance(item, dict):
                ok = False
                continue
            try:
                driver = int(item.get("driver_id", item.get("driver", idx)))
                order = int(item.get("order_id", item.get("order")))
            except Exception:
                ok = False
                continue
            if 0 <= driver < n_agents and 0 <= order < order_count:
                assignment[driver] = order
            else:
                ok = False
    elif isinstance(raw_assignment, dict):
        for key, value in raw_assignment.items():
            try:
                driver = int(str(key).replace("driver", "").replace("_", ""))
                order = int(value)
            except Exception:
                ok = False
                continue
            if 0 <= driver < n_agents and 0 <= order < order_count:
                assignment[driver] = order
            else:
                ok = False
    else:
        ok = False
    if any(order < 0 or order >= order_count for order in assignment) or len(set(assignment)) < n_agents:
        assignment = list(range(n_agents))
        ok = False

    notes = list(prior_notes)
    raw_notes = parsed.get("belief_notes", parsed.get("updated_belief_notes", []))
    if isinstance(raw_notes, list):
        for idx, item in enumerate(raw_notes):
            if isinstance(item, dict):
                try:
                    driver = int(item.get("driver_id", item.get("driver", idx)))
                except Exception:
                    ok = False
                    continue
                note = str(item.get("belief_note", item.get("note", ""))).strip()
            else:
                driver = idx
                note = str(item).strip()
            if 0 <= driver < n_agents and note:
                notes[driver] = note[:900]
            else:
                ok = False
    elif isinstance(raw_notes, dict):
        for key, value in raw_notes.items():
            try:
                driver = int(str(key).replace("driver", "").replace("_", ""))
            except Exception:
                ok = False
                continue
            note = str(value).strip()
            if 0 <= driver < n_agents and note:
                notes[driver] = note[:900]
            else:
                ok = False
    else:
        ok = False

    return tuple(int(order) for order in assignment), notes, ok


def verbal_readout_payload(*, driver: int, belief_note: str) -> dict[str, object]:
    return {
        "task": "Read out a point estimate from an LLM-PSRL-verbal belief note",
        "driver_id": driver,
        "belief_note": belief_note,
        "rule_order": list(RULES),
        "masked_rule_order": [f"r{idx}" for idx in range(len(RULES))],
        "instruction": (
            "Given only the belief note, output the best-guess binary value for each rule position. "
            "This is a read-out for scoring, not a posterior probability. Return valid JSON only."
        ),
        "response_schema": {"rule_tuple": {"avoid_long": "0 or 1", "zone_loyal": "0 or 1", "home_pull": "0 or 1", "surge_only": "0 or 1"}},
    }


def _binary_value(value: object) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)) and float(value) in {0.0, 1.0}:
        return int(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on", "present"}:
        return 1
    if text in {"0", "false", "no", "off", "absent"}:
        return 0
    return None


def parse_rule_tuple_readout(reply: str, rule_count: int) -> tuple[np.ndarray | None, bool]:
    try:
        parsed = extract_json(reply)
    except Exception:
        numbers = [int(match) for match in re.findall(r"\b[01]\b", reply)]
        if len(numbers) >= rule_count:
            return np.asarray(numbers[:rule_count], dtype=int), False
        return None, False

    raw = parsed.get("rule_tuple", parsed.get("rules", parsed.get("guess", parsed)))
    values: list[int] = []
    if isinstance(raw, dict):
        for idx, name in enumerate(RULES[:rule_count]):
            value = raw.get(name, raw.get(f"r{idx}", raw.get(str(idx))))
            bit = _binary_value(value)
            if bit is None:
                return None, False
            values.append(bit)
    elif isinstance(raw, list):
        if len(raw) < rule_count:
            return None, False
        for value in raw[:rule_count]:
            bit = _binary_value(value)
            if bit is None:
                return None, False
            values.append(bit)
    else:
        numbers = [int(match) for match in re.findall(r"\b[01]\b", str(raw))]
        if len(numbers) < rule_count:
            return None, False
        values = numbers[:rule_count]
    return np.asarray(values, dtype=int), True


def verbal_recovery_metrics(readout_guesses: list[np.ndarray | None], true_types: np.ndarray, n_types: int) -> tuple[float, float, float, str]:
    ptrue_values: list[float] = []
    acc_values: list[float] = []
    parsed = 0
    for driver, guess in enumerate(readout_guesses):
        if guess is None:
            ptrue_values.append(0.0)
            acc_values.append(0.5)
            continue
        parsed += 1
        truth = true_types[driver]
        ptrue_values.append(float(np.all(guess == truth)))
        acc_values.append(float(np.mean(guess == truth)))
    parse_rate = float(parsed / max(1, len(readout_guesses)))
    return float(np.mean(ptrue_values)), float(np.mean(acc_values)), parse_rate, "verbal_point_estimate" if parsed else "verbal_readout_parse_failed"


def assignment_matrix_score(score_matrix: np.ndarray, assignment: tuple[int, ...]) -> float:
    return float(np.mean([score_matrix[driver, order] for driver, order in enumerate(assignment)]))


def posterior_expected_value(
    env: CourierDispatchEnv,
    orders: list,
    assignment: tuple[int, ...],
    posteriors: list[RulePosterior],
    rng: np.random.Generator,
    samples: int,
) -> float:
    return expected_assignment_under_posteriors(env, orders, assignment, posteriors, rng, samples=samples)

def nll_true_for_method(
    *,
    env: CourierDispatchEnv,
    method: str,
    posteriors: list[RulePosterior],
    joint_posterior: JointRulePosterior,
) -> float:
    if method in {"live_pact", "live_pact_plus", "live_map_greedy"}:
        probs = [max(posterior.prob_true(env.true_types[driver]), 1e-12) for driver, posterior in enumerate(posteriors)]
        return float(np.mean([-np.log(prob) for prob in probs]))
    if method == "live_joint_psrl":
        return float(-np.log(max(joint_posterior.prob_true(env.true_types), 1e-12)))
    return float(np.log(env.n_types))


def structured_objectives(
    *,
    env: CourierDispatchEnv,
    orders: list,
    assignments: list[tuple[int, ...]],
    method: str,
    posteriors: list[RulePosterior],
    joint_sampled_types: np.ndarray,
    prior_sampled_types: np.ndarray,
    score_matrix: np.ndarray,
    rng: np.random.Generator,
    posterior_samples: int,
    round_index: int,
    horizon: int,
    pact_plus_beta: float,
    llm_score_weight: float,
) -> tuple[list[float], list[float], list[float]]:
    llm_scores = [assignment_matrix_score(score_matrix, assignment) for assignment in assignments]
    structured_scores: list[float] = []
    bonuses: list[float] = []
    if method == "live_pact":
        structured_scores = [
            expected_assignment_under_factored_posteriors(env, orders, assignment, posteriors, rng, posterior_samples)
            for assignment in assignments
        ]
        bonuses = [0.0 for _ in assignments]
    elif method == "live_pact_plus":
        structured_scores = [
            expected_assignment_under_factored_posteriors(env, orders, assignment, posteriors, rng, posterior_samples)
            for assignment in assignments
        ]
        scale = pact_plus_exploration_scale(posteriors, round_index, horizon)
        bonuses = [scale * assignment_disagreement_bonus(env, orders, assignment, posteriors) for assignment in assignments]
    elif method == "live_map_greedy":
        map_types = np.asarray([posterior.type_space[int(np.argmax(posterior.probs()))] for posterior in posteriors], dtype=int)
        structured_scores = [expected_assignment_reward(env, orders, assignment, map_types) for assignment in assignments]
        bonuses = [0.0 for _ in assignments]
    elif method == "live_joint_psrl":
        structured_scores = [expected_assignment_reward(env, orders, assignment, joint_sampled_types) for assignment in assignments]
        bonuses = [0.0 for _ in assignments]
    elif method == "live_psrl_notype":
        structured_scores = [expected_assignment_reward(env, orders, assignment, prior_sampled_types) for assignment in assignments]
        bonuses = [0.0 for _ in assignments]
    elif method in PROMPT_SCORE_METHODS:
        structured_scores = [0.0 for _ in assignments]
        bonuses = [0.0 for _ in assignments]
    else:
        raise ValueError(f"unknown live structured method: {method}")

    if method == "live_pact_plus":
        objectives = [base + pact_plus_beta * bonus + llm_score_weight * llm for base, bonus, llm in zip(structured_scores, bonuses, llm_scores, strict=True)]
    elif method in PROMPT_SCORE_METHODS:
        objectives = llm_scores
    else:
        objectives = [base + llm_score_weight * llm for base, llm in zip(structured_scores, llm_scores, strict=True)]
    return structured_scores, bonuses, objectives


def run_live_episode(
    *,
    method: str,
    model: str,
    seed: int,
    n_agents: int,
    rule_count: int,
    horizon: int,
    order_count: int,
    tau: float,
    penalty_scale: float,
    home_scale: float,
    menu_friction: float,
    couple_lambda: float,
    pool_mode: str,
    feature_mode: str,
    env_info_level: str,
    cache: dict[str, str],
    max_history: int,
    max_tokens: int,
    temperature: float,
    posterior_samples: int,
    pact_plus_beta: float,
    llm_score_weight: float,
) -> list[dict[str, object]]:
    if method not in ALL_METHODS:
        raise ValueError(f"unknown method: {method}")
    rng = np.random.default_rng(seed + 1_100_000)
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
    env.reset(seed)
    assignments = all_assignments(n_agents, order_count)
    reference_posteriors = [RulePosterior(env.type_space) for _ in range(n_agents)]
    pact_posteriors = [RulePosterior(env.type_space) for _ in range(n_agents)]
    joint_posterior = JointRulePosterior(env.type_space, n_agents)
    history: list[dict[str, object]] = []
    verbal_notes = [initial_verbal_note(driver) for driver in range(n_agents)]
    rows: list[dict[str, object]] = []
    cumulative_reward = 0.0
    cumulative_regret = 0.0
    cumulative_exploration_cost = 0.0
    for round_index in range(horizon):
        orders = sample_order_pool(env, order_count, mode=pool_mode)
        joint_marginals = joint_posterior.marginal_posteriors()
        prior_sampled_types = env.type_space[rng.integers(0, len(env.type_space), size=n_agents)].copy()
        joint_sampled_types = joint_posterior.sample(rng)

        if method in {"live_pact", "live_pact_plus", "live_map_greedy"}:
            active_posteriors = pact_posteriors
        elif method == "live_joint_psrl":
            active_posteriors = joint_marginals
        else:
            active_posteriors = reference_posteriors

        if method in {"live_pact", "live_pact_plus"}:
            belief_summary = posterior_summary(pact_posteriors, feature_mode=feature_mode)
        elif method == "live_map_greedy":
            belief_summary = map_summary(pact_posteriors, feature_mode=feature_mode)
        elif method == "live_joint_psrl":
            belief_summary = [
                {"joint_sampled_rules": sampled_rule_summary(joint_sampled_types, feature_mode=feature_mode)},
                {"marginal_posteriors": posterior_summary(joint_marginals, feature_mode=feature_mode)},
            ]
        elif method == "live_psrl_notype":
            belief_summary = sampled_rule_summary(prior_sampled_types, feature_mode=feature_mode)
        else:
            belief_summary = None

        exploration_guidance = None
        if method == "live_pact_plus":
            scale = pact_plus_exploration_scale(pact_posteriors, round_index, horizon)
            exploration_guidance = {
                "effective_exploration_weight": round(float(scale), 3),
                "reward_priority": "high" if scale < 0.25 else "balanced",
                "instruction": "Scores can reflect informative assignments only when exploration weight is high; otherwise score reward exploitation.",
            }

        score_matrix = np.zeros((n_agents, order_count), dtype=float)
        score_parsed_ok = True
        cache_hit = False
        structured_scores = [0.0 for _ in assignments]
        bonuses = [0.0 for _ in assignments]
        objectives = [0.0 for _ in assignments]

        if method == "live_random":
            chosen_index = int(rng.integers(0, len(assignments)))
            assignment = assignments[chosen_index]
        elif method == "live_llm_psrl_verbal":
            payload = verbal_decision_payload(
                method=method,
                round_index=round_index,
                orders=orders,
                n_agents=n_agents,
                history=history,
                max_history=max_history,
                feature_mode=feature_mode,
                belief_notes=verbal_notes,
                env_info_level=env_info_level,
                tau=tau,
                penalty_scale=penalty_scale,
                home_scale=home_scale,
                menu_friction=menu_friction,
                couple_lambda=couple_lambda,
            )
            reply, cache_hit = call_cached_llm(
                model=model,
                method=method,
                payload=payload,
                cache=cache,
                max_tokens=max(620, max_tokens),
                temperature=temperature,
                system=(
                    "You are a careful dispatch coordinator using verbal posterior sampling. "
                    "Maintain concise natural-language beliefs and return valid JSON only."
                ),
            )
            assignment, verbal_notes, score_parsed_ok = parse_verbal_decision(reply, n_agents, order_count, verbal_notes)
            chosen_index = assignments.index(assignment)
        else:
            payload = score_prompt_payload(
                method=method,
                round_index=round_index,
                orders=orders,
                n_agents=n_agents,
                history=history,
                max_history=max_history,
                feature_mode=feature_mode,
                posterior_summary_payload=belief_summary,
                exploration_guidance=exploration_guidance,
                env_info_level=env_info_level,
                tau=tau,
                penalty_scale=penalty_scale,
                home_scale=home_scale,
                menu_friction=menu_friction,
                couple_lambda=couple_lambda,
            )
            reply, cache_hit = call_scorer(model=model, method=method, payload=payload, cache=cache, max_tokens=max_tokens, temperature=temperature)
            score_matrix, score_parsed_ok = parse_score_matrix(reply, n_agents, order_count)
            structured_scores, bonuses, objectives = structured_objectives(
                env=env,
                orders=orders,
                assignments=assignments,
                method=method,
                posteriors=active_posteriors,
                joint_sampled_types=joint_sampled_types,
                prior_sampled_types=prior_sampled_types,
                score_matrix=score_matrix,
                rng=rng,
                posterior_samples=posterior_samples,
                round_index=round_index,
                horizon=horizon,
                pact_plus_beta=pact_plus_beta,
                llm_score_weight=llm_score_weight,
            )
            chosen_index = int(np.argmax(objectives))
            assignment = assignments[chosen_index]
        observed_actions = observed_actions_for_assignment(env, orders, assignment, seed, round_index)
        rewards = realized_assignment_reward(env, orders, assignment, observed_actions)
        oracle_expected = max(expected_assignment_reward(env, orders, candidate, env.true_types) for candidate in assignments)
        chosen_true_expected = expected_assignment_reward(env, orders, assignment, env.true_types)
        posterior_rewards = [posterior_expected_value(env, orders, candidate, active_posteriors, rng, posterior_samples) for candidate in assignments]
        posterior_greedy = float(max(posterior_rewards))
        chosen_reference = posterior_expected_value(env, orders, assignment, active_posteriors, rng, posterior_samples)
        exploration_cost = max(0.0, posterior_greedy - chosen_reference)
        regret = max(0.0, float(oracle_expected - chosen_true_expected))
        cumulative_reward += float(np.mean(rewards))
        cumulative_regret += regret
        cumulative_exploration_cost += exploration_cost

        if method in {"live_pact", "live_pact_plus", "live_map_greedy"}:
            for driver, action in enumerate(observed_actions):
                pact_posteriors[driver].update(env, orders[assignment[driver]], int(action))
        elif method == "live_joint_psrl":
            update_joint_matching(joint_posterior, env, orders, assignment, observed_actions)

        type_readout_parse_rate = 1.0
        type_estimate_flag = "numeric_posterior"
        verbal_ptrue = float(1.0 / env.n_types)
        verbal_rule_acc = 0.5
        if method == "live_llm_psrl_verbal":
            readout_guesses: list[np.ndarray | None] = []
            readout_cache_hits: list[bool] = []
            for driver in range(n_agents):
                readout_reply, readout_cache_hit = call_cached_llm(
                    model=model,
                    method="live_llm_psrl_verbal_readout",
                    payload=verbal_readout_payload(driver=driver, belief_note=verbal_notes[driver]),
                    cache=cache,
                    max_tokens=180,
                    temperature=temperature,
                    system="You read out binary hidden-rule estimates from verbal belief notes. Return valid JSON only.",
                )
                readout_cache_hits.append(readout_cache_hit)
                guess, readout_ok = parse_rule_tuple_readout(readout_reply, rule_count)
                readout_guesses.append(guess if readout_ok else None)
            verbal_ptrue, verbal_rule_acc, type_readout_parse_rate, type_estimate_flag = verbal_recovery_metrics(readout_guesses, env.true_types, env.n_types)
            cache_hit = bool(cache_hit and all(readout_cache_hits))
        elif method not in {"live_pact", "live_pact_plus", "live_map_greedy", "live_joint_psrl"}:
            type_estimate_flag = "no_type_estimate_floor_by_construction"

        event = {
            "round": round_index,
            "assignment": list(assignment),
            "observed_actions": [ACTIONS[int(action)] for action in observed_actions],
            "assigned_order_features": [compact_matching_state(orders[assignment[driver]], feature_mode) for driver in range(n_agents)],
            "model_note": _safe_reason(reply) if method not in DIRECT_METHODS and score_parsed_ok else "",
        }
        history.append(event)
        if method in {"live_pact", "live_pact_plus", "live_map_greedy"}:
            mean_true_tuple = float(np.mean([posterior.prob_true(env.true_types[driver]) for driver, posterior in enumerate(pact_posteriors)]))
            mean_rule_acc = float(np.mean([posterior.rule_marginal_accuracy(env.true_types[driver]) for driver, posterior in enumerate(pact_posteriors)]))
            nll_true = nll_true_for_method(env=env, method=method, posteriors=pact_posteriors, joint_posterior=joint_posterior)
        elif method == "live_joint_psrl":
            mean_true_tuple = joint_posterior.prob_true(env.true_types)
            mean_rule_acc = joint_posterior.rule_marginal_accuracy(env.true_types)
            nll_true = nll_true_for_method(env=env, method=method, posteriors=pact_posteriors, joint_posterior=joint_posterior)
        elif method == "live_llm_psrl_verbal":
            mean_true_tuple = verbal_ptrue
            mean_rule_acc = verbal_rule_acc
            nll_true = float(np.log(env.n_types))
        else:
            mean_true_tuple = float(1.0 / env.n_types)
            mean_rule_acc = 0.5
            nll_true = float(np.log(env.n_types))
        rows.append(
            {
                "model": model,
                "method": method,
                "seed": seed,
                "round": round_index,
                "mean_reward": float(np.mean(rewards)),
                "cumulative_reward": cumulative_reward,
                "instant_regret": regret,
                "cumulative_regret": cumulative_regret,
                "exploration_cost": exploration_cost,
                "cumulative_exploration_cost": cumulative_exploration_cost,
                "mean_true_tuple_posterior": mean_true_tuple,
                "mean_rule_marginal_accuracy": mean_rule_acc,
                "nll_true": nll_true,
                "couple_lambda": float(couple_lambda),
                "type_readout_parse_rate": type_readout_parse_rate,
                "type_estimate_flag": type_estimate_flag,
                "assignment": list(assignment),
                "llm_score_parse_ok": score_parsed_ok,
                "llm_cache_hit": cache_hit,
                "llm_assignment_score": assignment_matrix_score(score_matrix, assignment),
                "structured_assignment_score": float(structured_scores[chosen_index]),
                "structured_bonus": float(bonuses[chosen_index]),
                "structured_objective": float(objectives[chosen_index]),
            }
        )
    return rows


def summarize(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault((str(row["model"]), str(row["method"])), []).append(row)
    summary: list[dict[str, object]] = []
    for (model, method), group in sorted(grouped.items()):
        final_round = max(int(row["round"]) for row in group)
        final = [row for row in group if int(row["round"]) == final_round]
        summary.append(
            {
                "model": model,
                "method": method,
                "episodes": len({int(row["seed"]) for row in group}),
                "final_mean_cumulative_reward": float(np.mean([float(row["cumulative_reward"]) for row in final])),
                "final_mean_cumulative_regret": float(np.mean([float(row["cumulative_regret"]) for row in final])),
                "final_mean_cumulative_exploration_cost": float(np.mean([float(row["cumulative_exploration_cost"]) for row in final])),
                "final_mean_true_tuple_posterior": float(np.mean([float(row["mean_true_tuple_posterior"]) for row in final])),
                "final_mean_rule_marginal_accuracy": float(np.mean([float(row["mean_rule_marginal_accuracy"]) for row in final])),
                "final_mean_nll_true": float(np.mean([float(row.get("nll_true", 0.0)) for row in final])),
                "live_score_parse_ok_rate": float(np.mean([bool(row["llm_score_parse_ok"]) for row in group])),
                "type_readout_parse_rate": float(np.mean([float(row.get("type_readout_parse_rate", 1.0)) for row in group])),
                "type_estimate_flag": ";".join(sorted({str(row.get("type_estimate_flag", "numeric_posterior")) for row in group})),
                "mean_llm_assignment_score": float(np.mean([float(row["llm_assignment_score"]) for row in final])),
                "mean_structured_assignment_score": float(np.mean([float(row["structured_assignment_score"]) for row in final])),
            }
        )
    return summary


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields = [
        "model",
        "method",
        "seed",
        "round",
        "mean_reward",
        "cumulative_reward",
        "instant_regret",
        "cumulative_regret",
        "exploration_cost",
        "cumulative_exploration_cost",
        "mean_true_tuple_posterior",
        "mean_rule_marginal_accuracy",
        "nll_true",
        "couple_lambda",
        "type_readout_parse_rate",
        "type_estimate_flag",
        "llm_score_parse_ok",
        "llm_cache_hit",
        "llm_assignment_score",
        "structured_assignment_score",
        "structured_bonus",
        "structured_objective",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_summary_csv(path: Path, summary: list[dict[str, object]]) -> None:
    fields = list(summary[0].keys()) if summary else []
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summary)


def run(args: argparse.Namespace) -> dict[str, object]:
    if args.backend:
        os.environ["LLM_HPGG_BACKEND"] = args.backend
    cache = load_cache()
    models = [resolved_player_model(model) for model in args.models]
    rows: list[dict[str, object]] = []
    jobs = []
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as executor:
        for model in models:
            for seed in range(args.seeds):
                for method in args.live_methods:
                    jobs.append(
                        executor.submit(
                            run_live_episode,
                            method=method,
                            model=model,
                            seed=args.seed_offset + seed,
                            n_agents=args.n_agents,
                            rule_count=args.rule_count,
                            horizon=args.horizon,
                            order_count=args.orders,
                            tau=args.tau,
                            penalty_scale=args.penalty_scale,
                            home_scale=args.home_scale,
                            menu_friction=args.menu_friction,
                            couple_lambda=args.couple_lambda,
                            pool_mode=args.pool_mode,
                            feature_mode=args.feature_mode,
                            env_info_level=args.env_info_level,
                            cache=cache,
                            max_history=args.max_history,
                            max_tokens=args.max_tokens,
                            temperature=args.temperature,
                            posterior_samples=args.posterior_samples,
                            pact_plus_beta=args.pact_plus_beta,
                            llm_score_weight=args.llm_score_weight,
                        )
                    )
        completed = 0
        failed = 0
        for future in as_completed(jobs):
            try:
                rows.extend(future.result())
            except Exception as exc:
                failed += 1
                print(f"structured_live_matching_episode_failed={failed}: {exc}", flush=True)
            completed += 1
            if completed % 4 == 0 or completed == len(jobs):
                print(f"structured_live_matching_episodes_completed={completed}/{len(jobs)} failed={failed}", flush=True)
    save_cache(cache)
    summary = summarize(rows)
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = ANALYSIS_DIR / f"{args.out_prefix}_summary.json"
    rows_path = ANALYSIS_DIR / f"{args.out_prefix}_rows.csv"
    summary_csv = ANALYSIS_DIR / f"{args.out_prefix}_summary.csv"
    payload = {
        "setting": {
            "backend": os.getenv("LLM_HPGG_BACKEND", "anthropic"),
            "models": models,
            "live_methods": args.live_methods,
            "horizon": args.horizon,
            "seeds": args.seeds,
            "orders_per_round": args.orders,
            "couple_lambda": args.couple_lambda,
            "pool_mode": args.pool_mode,
            "feature_mode": args.feature_mode,
            "env_info_level": args.env_info_level,
            "decision_mode": "structured_solver_with_llm_score_calls",
            "posterior_samples": args.posterior_samples,
            "pact_plus_beta": args.pact_plus_beta,
            "llm_score_weight": args.llm_score_weight,
            "regret": "online mean-field expected regret vs true-type oracle assignment for the same order pool",
            "cache_path": str(CACHE_PATH.relative_to(ROOT)),
        },
        "summary": summary,
        "rows": rows,
    }
    summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(rows_path, rows)
    write_summary_csv(summary_csv, summary)
    return {"summary_path": str(summary_path.relative_to(ROOT)), "rows_csv": str(rows_path.relative_to(ROOT)), "summary_csv": str(summary_csv.relative_to(ROOT)), "payload": payload}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", default="cloudgpt")
    parser.add_argument("--models", type=parse_list, default=parse_list("gpt-5.4-mini-20260317"))
    parser.add_argument(
        "--live-methods",
        type=parse_list,
        default=parse_list(
            "live_pact,live_pact_plus,live_map_greedy,live_joint_psrl,live_psrl_notype,"
            "live_llm_greedy,live_llm_belief,live_atom_tom0,live_atom_tom1,live_atom_adaptive_hedge,live_econ_bne,"
            "live_llm_psrl_verbal,live_random"
        ),
    )
    parser.add_argument("--n-agents", type=int, default=3)
    parser.add_argument("--rule-count", type=int, default=4)
    parser.add_argument("--horizon", type=int, default=8)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--seed-offset", type=int, default=0)
    parser.add_argument("--orders", type=int, default=4)
    parser.add_argument("--tau", type=float, default=0.5)
    parser.add_argument("--penalty-scale", type=float, default=2.0)
    parser.add_argument("--home-scale", type=float, default=1.2)
    parser.add_argument("--menu-friction", type=float, default=0.2)
    parser.add_argument("--couple-lambda", type=float, default=0.0)
    parser.add_argument("--pool-mode", choices=["random", "type_stress"], default="type_stress")
    parser.add_argument("--feature-mode", choices=["masked", "semantic"], default="masked")
    parser.add_argument("--env-info-level", choices=["none", "full"], default="none")
    parser.add_argument("--max-history", type=int, default=6)
    parser.add_argument("--max-tokens", type=int, default=420)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--posterior-samples", type=int, default=4)
    parser.add_argument("--pact-plus-beta", type=float, default=0.1)
    parser.add_argument("--llm-score-weight", type=float, default=0.02)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--out-prefix", default="courier_matching_structured_live")
    args = parser.parse_args()
    result = run(args)
    print(json.dumps({key: value for key, value in result.items() if key != "payload"}, indent=2))
    for row in result["payload"]["summary"]:
        print(
            f"{row['model']} | {row['method']}: reward={row['final_mean_cumulative_reward']:.3f} "
            f"regret={row['final_mean_cumulative_regret']:.3f} parse={row['live_score_parse_ok_rate']:.3f} "
            f"Ptrue={row['final_mean_true_tuple_posterior']:.3f} rule_acc={row['final_mean_rule_marginal_accuracy']:.3f}"
        )


if __name__ == "__main__":
    main()