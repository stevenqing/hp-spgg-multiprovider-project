"""Live-LLM planner baselines for online CourierDispatch matching.

Drivers remain analytic rule-based agents. Live LLMs act only as platform-side
planners that assign orders from a public order pool to drivers.
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
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_hpgg.llm_agent import backend_name, call_player, model_for  # noqa: E402
from llm_courier_dispatch.dispatch_env import ACTIONS, RULES, CourierDispatchEnv, CourierState, RulePosterior  # noqa: E402
from llm_courier_dispatch.live_llm_dispatch import compact_state, extract_json  # noqa: E402
from llm_courier_dispatch.matching_dispatch import (  # noqa: E402
    JointRulePosterior,
    all_assignments,
    expected_assignment_reward,
    expected_assignment_under_posteriors,
    observed_actions_for_assignment,
    pact_plus_exploration_scale,
    realized_assignment_reward,
    sample_order_pool,
    update_joint_matching,
)


ANALYSIS_DIR = ROOT / "analysis" / "courier_dispatch_matching"
CACHE_PATH = ANALYSIS_DIR / "courier_matching_live_llm_cache.json"
VERSION = "courier-matching-live-planner-v1"
CACHE_LOCK = threading.Lock()


def rule_labels(feature_mode: str, count: int = len(RULES)) -> list[str]:
    if feature_mode == "masked":
        return [f"r{idx}" for idx in range(int(count))]
    return list(RULES[: int(count)])


def compact_matching_state(state: CourierState, feature_mode: str) -> dict[str, object]:
    if feature_mode == "semantic":
        return compact_state(state)
    if feature_mode != "masked":
        raise ValueError(f"unknown feature mode: {feature_mode}")
    return {
        "features": {
            "f0": int(state.long_trip),
            "f1": int(state.leaves_zone),
            "f2": int(state.home_ward),
            "f3": int(state.surge),
            "x0": float(state.pay),
            "x1": int(state.after_deadline),
            "x2": float(state.congestion),
        },
        "menu_features": {
            "f0": int(state.menu_long_trip),
            "f1": int(state.menu_leaves_zone),
            "f2": int(state.menu_home_ward),
            "f3": int(state.menu_surge),
            "x0": float(state.menu_pay),
        },
    }


def masked_feature_codebook() -> dict[str, object]:
    return {
        "feature_mode": "masked",
        "binary_public_features": ["f0", "f1", "f2", "f3"],
        "numeric_public_features": ["x0", "x1", "x2"],
        "menu_features": "same feature codes for the alternate menu order",
        "posterior_rule_links": [
            {"rule_code": f"r{idx}", "linked_public_feature": f"f{idx}"}
            for idx in range(len(RULES))
        ],
        "instruction": "Feature names are intentionally masked. Do not infer semantic labels from code names.",
    }


def environment_model_spec(
    *,
    feature_mode: str,
    env_info_level: str,
    tau: float,
    penalty_scale: float,
    home_scale: float,
    menu_friction: float,
    couple_lambda: float = 0.0,
) -> dict[str, object]:
    if env_info_level == "none":
        return {}
    if env_info_level != "full":
        raise ValueError(f"unknown env info level: {env_info_level}")
    if feature_mode == "masked":
        rule = [f"r{idx}" for idx in range(len(RULES))]
        feature = [f"f{idx}" for idx in range(len(RULES))]
        pay = "x0"
        after_deadline = "x1"
        congestion = "x2"
        menu_prefix = "menu_features."
        codebook_note = "Rules and features are intentionally masked; use only these code-level equations."
    else:
        rule = list(RULES)
        feature = ["long_trip", "leaves_zone", "home_ward", "surge"]
        pay = "pay"
        after_deadline = "after_deadline"
        congestion = "congestion"
        menu_prefix = "menu_order."
        codebook_note = "Semantic names are public in this run."
    long_trip, leaves_zone, home_ward, surge = feature
    avoid_long, zone_loyal, home_pull, surge_only = rule
    menu_long = f"{menu_prefix}{long_trip}"
    menu_zone = f"{menu_prefix}{leaves_zone}"
    menu_home = f"{menu_prefix}{home_ward}"
    menu_surge = f"{menu_prefix}{surge}"
    menu_pay = f"{menu_prefix}{pay}"
    return {
        "env_info_level": "full",
        "codebook_note": codebook_note,
        "hidden_rule_space": "Each driver has a stable private binary vector over the listed rule positions. Infer it only from public action history or supplied belief summaries.",
        "action_generation": f"Observed driver action codes are sampled by softmax(action_utilities / tau), tau={tau:.3g}.",
        "reward_parameters": {
            "penalty_scale": float(penalty_scale),
            "home_scale": float(home_scale),
            "menu_friction": float(menu_friction),
            "couple_lambda": float(couple_lambda),
        },
        "base_accept_utility": (
            f"{pay} + 0.4*{surge} - penalty_scale*{avoid_long}*{long_trip} "
            f"- penalty_scale*{zone_loyal}*{leaves_zone} - penalty_scale*{surge_only}*(1-{surge}) "
            f"+ {home_pull}*{after_deadline}*(home_scale*{home_ward} - penalty_scale*(1-{home_ward}))"
        ),
        "action_utility_equations": {
            "accept": f"base_accept_utility(current_order) - 0.5*{congestion}",
            "decline-a": f"-0.18 + max(0,0.9-{pay}) + 0.30*{avoid_long}*{long_trip} + 0.20*{surge_only}*(1-{surge})",
            "decline-b": f"-0.22 + 0.90*{avoid_long}*{long_trip} + 0.35*{zone_loyal}*{leaves_zone} + 0.25*{home_pull}*{after_deadline}*(1-{home_ward}) + 0.10*{long_trip}",
            "decline-c": f"-0.22 + 0.90*{zone_loyal}*{leaves_zone} + 0.40*{home_pull}*{after_deadline}*(1-{home_ward}) + 0.20*max(0,0.9-{pay})",
            "decline-d": f"-0.22 + 0.95*{surge_only}*(1-{surge}) + 0.30*{avoid_long}*{long_trip} + 0.20*{zone_loyal}*{leaves_zone} + 0.10*(1-{surge})",
            "reposition": f"-0.20 + 1.55*{home_pull}*{after_deadline}*(1-{home_ward}) + 0.20*{after_deadline}",
            "choose-from-menu": (
                f"base_accept_utility(menu_order) - menu_friction - 0.35*{congestion} "
                f"+ 0.35*menu_relief + 0.12*current_pain"
            ),
        },
        "helper_terms": {
            "current_pain": f"{avoid_long}*{long_trip} + {zone_loyal}*{leaves_zone} + {surge_only}*(1-{surge}) + {home_pull}*{after_deadline}*(1-{home_ward})",
            "menu_relief": (
                f"{avoid_long}*max(0,{long_trip}-{menu_long}) + {zone_loyal}*max(0,{leaves_zone}-{menu_zone}) "
                f"+ {surge_only}*max(0,{menu_surge}-{surge}) + {home_pull}*{after_deadline}*max(0,{menu_home}-{home_ward})"
            ),
        },
        "realized_reward_equations": {
            "public_congestion": f"{congestion} + 0.25*max(0, accepted_driver_count - 1)",
            "accept": "base_accept_utility(current_order) - 0.5*public_congestion",
            "choose-from-menu": "base_accept_utility(menu_order) - menu_friction - 0.45*public_congestion",
            "reposition": f"-0.08 + 0.45*{home_pull}*{after_deadline}*(1-{home_ward})",
            "decline-a/b/c/d": "-0.06",
        },
        "matching_note": "For a driver-order pair, score expected realized reward after inferring that driver's hidden rule vector; final assignment must use distinct orders.",
    }


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
    tmp_path = CACHE_PATH.with_suffix(f"{CACHE_PATH.suffix}.tmp")
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


def prompt_payload(
    *,
    method: str,
    round_index: int,
    orders: list[CourierState],
    n_agents: int,
    history: list[dict[str, object]],
    max_history: int,
    feature_mode: str,
    posterior_summary: list[dict[str, object]] | None = None,
    exploration_guidance: dict[str, object] | None = None,
    env_info_level: str = "none",
    tau: float = 0.5,
    penalty_scale: float = 2.0,
    home_scale: float = 1.2,
    menu_friction: float = 0.2,
    couple_lambda: float = 0.0,
) -> dict[str, object]:
    include_history = method in {
        "live_llm_belief",
        "live_atom_tom1",
        "live_atom_adaptive_hedge",
        "live_econ_bne",
        "live_pact",
        "live_pact_plus",
        "live_map_greedy",
        "live_joint_psrl",
    }
    objective = "Assign one distinct order to each driver to maximize expected average driver reward this round."
    history_instruction = "Use recent neutral driver action codes to infer stable driver response patterns." if include_history else "Use current public order features only."
    if method == "live_atom_tom0":
        objective = "Use a zero-order theory-of-mind heuristic: predict responses from current order features only, without hidden-type inference."
    elif method == "live_atom_tom1":
        objective = "Use a one-step theory-of-mind heuristic: infer stable driver response patterns from public action history, then assign orders."
    elif method == "live_atom_adaptive_hedge":
        objective = "Hedge between zero-order and one-step theory-of-mind; use history only when it is informative."
    elif method == "live_econ_bne":
        objective = "Use an economic best-response / equilibrium-style heuristic: assign orders robustly to private driver constraints."
    elif method == "live_pact":
        objective = "Use the supplied numeric posterior over each driver's hidden operational rules to assign one distinct order to each driver."
    elif method == "live_pact_plus":
        objective = "Use the supplied numeric posterior. Follow the exploration guidance: prioritize high reward when exploration weight is low, and prefer informative assignments only when uncertainty remains high."
    elif method == "live_map_greedy":
        objective = "Use the supplied MAP hidden-rule estimate for each driver to assign one distinct order to each driver."
    elif method == "live_joint_psrl":
        objective = "Use the supplied joint-posterior Thompson sample and marginal posterior summary to assign one distinct order to each driver."
    elif method == "live_psrl_notype":
        objective = "Use the supplied prior-sampled rule hypothesis as an uninformative PSRL-NoType sample, without learning from history."
    privacy_boundary = "Drivers have private operational rules. You never see hidden rule tuples or rule names."
    if posterior_summary:
        privacy_boundary = "Drivers have private operational rules. You receive only masked or compact numeric belief summaries, not semantic rule names."
    return {
        "task": "CourierDispatch-Rules online matching assignment",
        "round": round_index,
        "method": method,
        "objective": objective,
        "privacy_boundary": privacy_boundary,
        "public_action_codes": list(ACTIONS),
        "drivers": [{"driver_id": driver} for driver in range(n_agents)],
        "orders": [{"order_id": idx, **compact_matching_state(order, feature_mode)} for idx, order in enumerate(orders)],
        "assignment_constraint": "Return one distinct order_id for each driver_id. Do not assign the same order to two drivers.",
        "history": history[-max_history:] if include_history else [],
        "history_instruction": history_instruction,
        "belief_state_summary": posterior_summary or [],
        "feature_codebook": masked_feature_codebook() if feature_mode == "masked" else {},
        "environment_model": environment_model_spec(
            feature_mode=feature_mode,
            env_info_level=env_info_level,
            tau=tau,
            penalty_scale=penalty_scale,
            home_scale=home_scale,
            menu_friction=menu_friction,
            couple_lambda=couple_lambda,
        ),
        "exploration_guidance": exploration_guidance or {},
        "response_schema": {"assignment": [{"driver_id": "integer", "order_id": "integer"}], "reason": "short"},
        "instruction": "Return valid JSON only. assignment must contain exactly one entry for each driver_id.",
    }


def posterior_summary(posteriors: list[RulePosterior], top_k: int = 3, feature_mode: str = "semantic") -> list[dict[str, object]]:
    summaries: list[dict[str, object]] = []
    for driver, posterior in enumerate(posteriors):
        labels = rule_labels(feature_mode, posterior.type_space.shape[1])
        probs = posterior.probs()
        top = np.argsort(probs)[::-1][:top_k]
        summaries.append(
            {
                "driver_id": driver,
                "confidence": round(float(np.max(probs)), 3),
                "rule_marginals": {label: round(float(value), 3) for label, value in zip(labels, probs @ posterior.type_space, strict=True)},
                "top_rule_tuples": [
                    {
                        "prob": round(float(probs[int(idx)]), 3),
                        "rules": {label: int(value) for label, value in zip(labels, posterior.type_space[int(idx)], strict=True)},
                    }
                    for idx in top
                ],
            }
        )
    return summaries


def map_summary(posteriors: list[RulePosterior], feature_mode: str = "semantic") -> list[dict[str, object]]:
    summaries: list[dict[str, object]] = []
    for driver, posterior in enumerate(posteriors):
        labels = rule_labels(feature_mode, posterior.type_space.shape[1])
        probs = posterior.probs()
        idx = int(np.argmax(probs))
        summaries.append(
            {
                "driver_id": driver,
                "map_probability": round(float(probs[idx]), 3),
                "map_rules": {label: int(value) for label, value in zip(labels, posterior.type_space[idx], strict=True)},
            }
        )
    return summaries


def sampled_rule_summary(sampled_types: np.ndarray, feature_mode: str = "semantic") -> list[dict[str, object]]:
    labels = rule_labels(feature_mode, sampled_types.shape[1])
    return [
        {
            "driver_id": driver,
            "sampled_rules": {label: int(value) for label, value in zip(labels, sampled_types[driver], strict=True)},
        }
        for driver in range(len(sampled_types))
    ]


def parse_assignment(reply: str, n_agents: int, order_count: int) -> tuple[tuple[int, ...], bool]:
    parsed = extract_json(reply)
    raw = parsed.get("assignment", parsed.get("assignments", None))
    assignment = [-1] * n_agents
    ok = True
    if isinstance(raw, list):
        for idx, item in enumerate(raw):
            if isinstance(item, dict):
                try:
                    driver = int(item.get("driver_id", item.get("driver", idx)))
                    order = int(item.get("order_id", item.get("order")))
                except Exception:
                    ok = False
                    continue
            else:
                try:
                    driver = idx
                    order = int(item)
                except Exception:
                    ok = False
                    continue
            if 0 <= driver < n_agents and 0 <= order < order_count:
                assignment[driver] = order
            else:
                ok = False
    elif isinstance(raw, dict):
        for key, value in raw.items():
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
        nums = [int(match) for match in re.findall(r"\b\d+\b", reply)]
        if len(nums) >= n_agents:
            assignment = nums[:n_agents]
            ok = False
    if any(order < 0 or order >= order_count for order in assignment) or len(set(assignment)) < n_agents:
        fallback = tuple(range(n_agents))
        return fallback, False
    return tuple(int(order) for order in assignment), ok


def call_planner(
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
        "You are a careful dispatch platform planner in an online matching benchmark. "
        "You only see public order features and neutral action codes. Return JSON only."
    )
    reply = call_player(system, json.dumps(payload, indent=2), model=model, max_tokens=max_tokens, temperature=temperature)
    with CACHE_LOCK:
        cache[key] = reply
        save_cache(cache)
    return reply, False


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
    pool_mode: str,
    feature_mode: str,
    env_info_level: str,
    cache: dict[str, str],
    max_history: int,
    max_tokens: int,
    temperature: float,
) -> list[dict[str, object]]:
    rng = np.random.default_rng(seed + 900_000)
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
    reference_posteriors = [RulePosterior(env.type_space) for _ in range(n_agents)]
    pact_posteriors = [RulePosterior(env.type_space) for _ in range(n_agents)]
    joint_posterior = JointRulePosterior(env.type_space, n_agents)
    history: list[dict[str, object]] = []
    rows: list[dict[str, object]] = []
    cumulative_reward = 0.0
    cumulative_regret = 0.0
    cumulative_exploration_cost = 0.0
    for round_index in range(horizon):
        orders = sample_order_pool(env, order_count, mode=pool_mode)
        joint_marginals = joint_posterior.marginal_posteriors()
        sampled_prior_types = env.type_space[rng.integers(0, len(env.type_space), size=n_agents)]
        sampled_joint_types = joint_posterior.sample(rng)
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
                {"joint_sampled_rules": sampled_rule_summary(sampled_joint_types, feature_mode=feature_mode)},
                {"marginal_posteriors": posterior_summary(joint_marginals, feature_mode=feature_mode)},
            ]
        elif method == "live_psrl_notype":
            belief_summary = sampled_rule_summary(sampled_prior_types, feature_mode=feature_mode)
        else:
            belief_summary = None
        exploration_guidance = None
        if method == "live_pact_plus":
            scale = pact_plus_exploration_scale(pact_posteriors, round_index, horizon)
            exploration_guidance = {
                "effective_exploration_weight": round(float(scale), 3),
                "reward_priority": "high" if scale < 0.25 else "balanced",
                "instruction": "Use informative assignments only when effective_exploration_weight is high; otherwise exploit the posterior for reward.",
            }
        payload = prompt_payload(
            method=method,
            round_index=round_index,
            orders=orders,
            n_agents=n_agents,
            history=history,
            max_history=max_history,
            feature_mode=feature_mode,
            posterior_summary=belief_summary,
            exploration_guidance=exploration_guidance,
            env_info_level=env_info_level,
            tau=tau,
            penalty_scale=penalty_scale,
            home_scale=home_scale,
            menu_friction=menu_friction,
        )
        reply, cache_hit = call_planner(model=model, method=method, payload=payload, cache=cache, max_tokens=max_tokens, temperature=temperature)
        assignment, parsed_ok = parse_assignment(reply, n_agents, order_count)
        observed_actions = observed_actions_for_assignment(env, orders, assignment, seed, round_index)
        rewards = realized_assignment_reward(env, orders, assignment, observed_actions)
        oracle_expected = max(expected_assignment_reward(env, orders, candidate, env.true_types) for candidate in assignments)
        chosen_true_expected = expected_assignment_reward(env, orders, assignment, env.true_types)
        posterior_rewards = [expected_assignment_under_posteriors(env, orders, candidate, active_posteriors, rng, samples=2) for candidate in assignments]
        posterior_greedy = float(max(posterior_rewards))
        chosen_reference = expected_assignment_under_posteriors(env, orders, assignment, active_posteriors, rng, samples=2)
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
        event = {
            "round": round_index,
            "assignment": list(assignment),
            "observed_actions": [ACTIONS[int(action)] for action in observed_actions],
            "model_note": str(extract_json(reply).get("reason", ""))[:200],
        }
        history.append(event)
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
                "mean_true_tuple_posterior": float(np.mean([posterior.prob_true(env.true_types[driver]) for driver, posterior in enumerate(pact_posteriors)])) if method in {"live_pact", "live_pact_plus", "live_map_greedy"} else (joint_posterior.prob_true(env.true_types) if method == "live_joint_psrl" else float(1.0 / env.n_types)),
                "mean_rule_marginal_accuracy": float(np.mean([posterior.rule_marginal_accuracy(env.true_types[driver]) for driver, posterior in enumerate(pact_posteriors)])) if method in {"live_pact", "live_pact_plus", "live_map_greedy"} else (joint_posterior.rule_marginal_accuracy(env.true_types) if method == "live_joint_psrl" else 0.5),
                "assignment": list(assignment),
                "llm_parsed_ok": parsed_ok,
                "llm_cache_hit": cache_hit,
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
                "live_parse_ok_rate": float(np.mean([bool(row["llm_parsed_ok"]) for row in group])),
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
        "llm_parsed_ok",
        "llm_cache_hit",
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


def parse_list(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def resolved_player_model(model_name: str | None) -> str:
    backend = backend_name("player")
    return model_for("player", backend, model_name)


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
                            pool_mode=args.pool_mode,
                            feature_mode=args.feature_mode,
                            env_info_level=args.env_info_level,
                            cache=cache,
                            max_history=args.max_history,
                            max_tokens=args.max_tokens,
                            temperature=args.temperature,
                        )
                    )
        completed = 0
        failed = 0
        for future in as_completed(jobs):
            try:
                rows.extend(future.result())
            except Exception as exc:
                failed += 1
                print(f"live_matching_episode_failed={failed}: {exc}", flush=True)
            completed += 1
            if completed % 4 == 0 or completed == len(jobs):
                print(f"live_matching_episodes_completed={completed}/{len(jobs)} failed={failed}", flush=True)
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
            "pool_mode": args.pool_mode,
            "feature_mode": args.feature_mode,
            "env_info_level": args.env_info_level,
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
    parser.add_argument("--live-methods", type=parse_list, default=parse_list("live_llm_greedy,live_llm_belief,live_atom_tom0,live_atom_tom1,live_atom_adaptive_hedge,live_econ_bne"))
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
    parser.add_argument("--pool-mode", choices=["random", "type_stress"], default="random")
    parser.add_argument("--feature-mode", choices=["masked", "semantic"], default="masked")
    parser.add_argument("--env-info-level", choices=["none", "full"], default="none")
    parser.add_argument("--max-history", type=int, default=6)
    parser.add_argument("--max-tokens", type=int, default=240)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--out-prefix", default="courier_matching_live_llm")
    args = parser.parse_args()
    result = run(args)
    print(json.dumps({key: value for key, value in result.items() if key != "payload"}, indent=2))
    for row in result["payload"]["summary"]:
        print(
            f"{row['model']} | {row['method']}: reward={row['final_mean_cumulative_reward']:.3f} "
            f"regret={row['final_mean_cumulative_regret']:.3f} parse={row['live_parse_ok_rate']:.3f}"
        )


if __name__ == "__main__":
    main()

