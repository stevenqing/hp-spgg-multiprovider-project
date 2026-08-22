"""Live-LLM CourierDispatch baseline runner.

Live LLMs act as platform-side dispatch planners. They choose among public
candidate states from neutral action/message histories; hidden rule tuples are
never shown to the model.
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
from llm_courier_dispatch.demo_dispatch import (  # noqa: E402
    choose_state,
    deterministic_joint_actions,
    expected_reward_under_posteriors,
    run_episode,
)
from llm_courier_dispatch.dispatch_env import (  # noqa: E402
    ACTIONS,
    MESSAGES,
    RULES,
    CourierDispatchEnv,
    CourierState,
    RulePosterior,
)


ANALYSIS_DIR = ROOT / "analysis" / "courier_dispatch"
CACHE_PATH = ANALYSIS_DIR / "courier_dispatch_live_llm_cache.json"
VERSION = "courier-live-neutral-v1"
CACHE_LOCK = threading.Lock()


def parse_list(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def resolved_player_model(model_name: str | None) -> str:
    backend = backend_name("player")
    return model_for("player", backend, model_name)


def model_slug(model: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", model).strip("_").lower()
    return slug[:80] or "model"


def extract_json(text: str) -> dict[str, object]:
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if not match:
            return {}
        try:
            parsed = json.loads(match.group(0))
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}


def parse_choice(reply: str, candidate_count: int) -> tuple[int, bool]:
    parsed = extract_json(reply)
    for key in ("choice", "candidate", "candidate_id", "selected_candidate"):
        if key in parsed:
            try:
                choice = int(parsed[key])
                if 0 <= choice < candidate_count:
                    return choice, True
            except Exception:
                pass
    match = re.search(r"\b([0-9]+)\b", reply)
    if match:
        choice = int(match.group(1))
        if 0 <= choice < candidate_count:
            return choice, False
    return 0, False


def compact_state(state: CourierState) -> dict[str, float | int | dict[str, float | int]]:
    return {
        "current_order": {
            "long_trip": state.long_trip,
            "leaves_zone": state.leaves_zone,
            "home_ward": state.home_ward,
            "surge": state.surge,
            "pay": round(float(state.pay), 3),
        },
        "menu_order": {
            "long_trip": state.menu_long_trip,
            "leaves_zone": state.menu_leaves_zone,
            "home_ward": state.menu_home_ward,
            "surge": state.menu_surge,
            "pay": round(float(state.menu_pay), 3),
        },
        "after_deadline": state.after_deadline,
        "congestion": round(float(state.congestion), 3),
    }


def prompt_payload(
    *,
    method: str,
    round_index: int,
    candidates: list[CourierState],
    history: list[dict[str, object]],
    max_history: int,
) -> dict[str, object]:
    include_history = method in {"live_llm_belief", "live_atom_tom1", "live_atom_adaptive_hedge", "live_econ_bne"}
    objective = "Choose the candidate state expected to produce the highest average driver reward over this round."
    history_instruction = "Use history to infer stable driver response patterns." if include_history else "Ignore history; act as a myopic no-belief baseline."
    if method == "live_atom_tom0":
        objective = "Use a zero-order theory-of-mind heuristic: predict driver responses from current public features only, without hidden-type inference."
    elif method == "live_atom_tom1":
        objective = "Use a one-step theory-of-mind heuristic: infer stable driver response patterns from public history, then choose the best candidate."
        history_instruction = "Infer driver response patterns from recent neutral action codes, but do not invent hidden rule names."
    elif method == "live_atom_adaptive_hedge":
        objective = "Hedge between zero-order and one-step theory-of-mind: use history when it is informative, otherwise choose a robust public-state candidate."
        history_instruction = "Use recent neutral action codes only if they reveal stable response patterns; otherwise prefer robust current features."
    elif method == "live_econ_bne":
        objective = "Use an economic equilibrium-style heuristic: treat drivers as rational responders with private constraints and choose a candidate robust to their likely best responses."
        history_instruction = "Use public history to calibrate likely response incentives, not to name hidden rules."
    return {
        "task": "CourierDispatch-Rules candidate selection",
        "round": round_index,
        "method": method,
        "objective": objective,
        "privacy_boundary": "Drivers have stable private operational constraints. You never see hidden rule tuples or rule names.",
        "public_action_codes": list(ACTIONS),
        "public_message_codes": list(MESSAGES),
        "code_warning": "decline-a/b/c/d and msg-a/b/c/d are neutral platform codes, not literal reasons.",
        "candidate_schema": {
            "long_trip": "0/1 public route flag",
            "leaves_zone": "0/1 public route flag",
            "home_ward": "0/1 public route flag",
            "surge": "0/1 public pricing flag",
            "pay": "public normalized pay",
            "after_deadline": "0/1 public timing flag",
            "congestion": "public congestion level",
        },
        "history": history[-max_history:] if include_history else [],
        "history_instruction": history_instruction,
        "candidates": [{"candidate_id": idx, **compact_state(state)} for idx, state in enumerate(candidates)],
        "response_schema": {"choice": "integer candidate_id", "reason": "short", "belief_note": "short optional"},
        "instruction": "Return valid JSON only. The choice must be one of the listed candidate_id values.",
    }


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


def load_cache() -> dict[str, str]:
    with CACHE_LOCK:
        if CACHE_PATH.exists():
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        return {}


def save_cache(cache: dict[str, str]) -> None:
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def call_live_planner(
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
        "You are a careful dispatch planner in a controlled benchmark. "
        "You only observe public candidate features and neutral public action codes. "
        "Do not invent hidden rule names. Return JSON only."
    )
    reply = call_player(system, json.dumps(payload, indent=2), model=model, max_tokens=max_tokens, temperature=temperature)
    with CACHE_LOCK:
        cache[key] = reply
        save_cache(cache)
    return reply, False


def run_live_llm_episode(
    *,
    method: str,
    model: str,
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
    cache: dict[str, str],
    max_history: int,
    max_tokens: int,
    temperature: float,
) -> list[dict[str, object]]:
    rng = np.random.default_rng(seed + 300_000)
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
    reference_posteriors = [RulePosterior(env.type_space) for _ in range(env.n_agents)]
    history: list[dict[str, object]] = []
    rows: list[dict[str, object]] = []
    cumulative_reward = 0.0
    cumulative_probe_cost = 0.0
    for round_index in range(horizon):
        candidates = env.sample_candidate_states(candidate_count)
        greedy_rewards = [expected_reward_under_posteriors(env, state, reference_posteriors, rng) for state in candidates]
        greedy = float(max(greedy_rewards))
        payload = prompt_payload(method=method, round_index=round_index, candidates=candidates, history=history, max_history=max_history)
        reply, cache_hit = call_live_planner(
            model=model,
            method=method,
            payload=payload,
            cache=cache,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        choice_idx, parsed_ok = parse_choice(reply, len(candidates))
        choice_state = candidates[choice_idx]
        observed_actions = deterministic_joint_actions(env, choice_state, seed, round_index, choice_idx)
        rewards = env.reward_fn(choice_state, observed_actions, env.true_types)
        cumulative_reward += float(np.mean(rewards))
        chosen_expected = float(greedy_rewards[choice_idx])
        exploration_cost = max(0.0, greedy - chosen_expected)
        cumulative_probe_cost += exploration_cost
        event = {
            "round": round_index,
            "chosen_candidate": choice_idx,
            "chosen_public_state": compact_state(choice_state),
            "observed_actions": [ACTIONS[int(action)] for action in observed_actions],
            "accepted_count": int(np.sum(observed_actions == ACTIONS.index("accept"))),
            "menu_chosen_count": int(np.sum(observed_actions == ACTIONS.index("choose-from-menu"))),
            "model_note": str(extract_json(reply).get("belief_note", extract_json(reply).get("reason", "")))[:240],
        }
        history.append(event)
        rows.append(
            {
                "model": model,
                "method": method,
                "beta": 0.0,
                "seed": seed,
                "round": round_index,
                "couple_lambda": couple_lambda,
                "mean_reward": float(np.mean(rewards)),
                "cumulative_reward": cumulative_reward,
                "exploration_cost": exploration_cost,
                "cumulative_exploration_cost": cumulative_probe_cost,
                "message_cost": 0.0,
                "cumulative_message_cost": 0.0,
                "cumulative_total_information_cost": cumulative_probe_cost,
                "mean_true_tuple_posterior": float(1.0 / env.n_types),
                "mean_rule_marginal_accuracy": 0.5,
                "chosen_candidate": choice_idx,
                "chosen_state": choice_state.to_dict(),
                "observed_actions": [ACTIONS[int(action)] for action in observed_actions],
                "true_types": [dict(zip(RULES[:rule_count], map(int, row), strict=True)) for row in env.true_types],
                "llm_reply": reply,
                "llm_parsed_ok": parsed_ok,
                "llm_cache_hit": cache_hit,
            }
        )
    return rows


def add_model(rows: list[dict[str, object]], model: str, rename: dict[str, str] | None = None) -> list[dict[str, object]]:
    rename = rename or {}
    out = []
    for row in rows:
        copied = dict(row)
        copied["model"] = model
        copied["method"] = rename.get(str(copied["method"]), str(copied["method"]))
        copied.setdefault("llm_reply", "")
        copied.setdefault("llm_parsed_ok", True)
        copied.setdefault("llm_cache_hit", True)
        out.append(copied)
    return out


def summarize(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, float, float], list[dict[str, object]]] = {}
    for row in rows:
        key = (str(row["model"]), str(row["method"]), float(row["beta"]), float(row["couple_lambda"]))
        grouped.setdefault(key, []).append(row)
    summary: list[dict[str, object]] = []
    for (model, method, beta, couple_lambda), group in sorted(grouped.items()):
        final_round = max(int(row["round"]) for row in group)
        final = [row for row in group if int(row["round"]) == final_round]
        live_rows = [row for row in group if str(row.get("llm_reply", ""))]
        summary.append(
            {
                "model": model,
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
                "live_calls": len(live_rows),
                "live_parse_ok_rate": float(np.mean([bool(row.get("llm_parsed_ok", False)) for row in live_rows])) if live_rows else None,
            }
        )
    return summary


def write_rows_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields = [
        "model",
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


def run(args: argparse.Namespace) -> dict[str, object]:
    if args.backend:
        os.environ["LLM_HPGG_BACKEND"] = args.backend
    if args.offline:
        os.environ["LLM_HPGG_OFFLINE"] = "1"
    cache = load_cache()
    rows: list[dict[str, object]] = []
    analytic_methods = [
        ("random", 0.0),
        ("oracle", 0.0),
        ("map_greedy", 0.0),
        ("joint_psrl", 0.0),
        ("psrl_notype", 0.0),
        ("atom_tom0", 0.0),
        ("atom_tom1", 0.0),
        ("pact", 0.0),
        ("pact_plus", 0.0),
        ("pact_plus", 0.1),
        ("pact_plus", 0.25),
        ("pact_plus", 0.5),
        ("pact_message", 0.0),
    ]
    live_methods = args.live_methods
    resolved_models = [resolved_player_model(model) for model in args.models]
    if not args.skip_analytic:
        analytic_rows_all: list[dict[str, object]] = []
        for seed in range(args.seeds):
            seed_value = args.seed_offset + seed
            for method, beta in analytic_methods:
                analytic_rows_all.extend(
                    run_episode(
                        method,
                        beta,
                        seed=seed_value,
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
        for model in resolved_models:
            rows.extend(add_model(analytic_rows_all, model))

    live_jobs = []
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as executor:
        for model in resolved_models:
            for seed in range(args.seeds):
                seed_value = args.seed_offset + seed
                for method in live_methods:
                    live_jobs.append(
                        executor.submit(
                            run_live_llm_episode,
                            method=method,
                            model=model,
                            seed=seed_value,
                            n_agents=args.n_agents,
                            rule_count=args.rule_count,
                            horizon=args.horizon,
                            tau=args.tau,
                            penalty_scale=args.penalty_scale,
                            home_scale=args.home_scale,
                            menu_friction=args.menu_friction,
                            candidate_count=args.candidates,
                            couple_lambda=0.0,
                            cache=cache,
                            max_history=args.max_history,
                            max_tokens=args.max_tokens,
                            temperature=args.temperature,
                        )
                    )
        completed = 0
        for future in as_completed(live_jobs):
            rows.extend(future.result())
            completed += 1
            if completed % 4 == 0 or completed == len(live_jobs):
                print(f"live_episodes_completed={completed}/{len(live_jobs)}", flush=True)
    save_cache(cache)
    summary = summarize(rows)
    payload = {
        "setting": {
            "backend": os.getenv("LLM_HPGG_BACKEND", "anthropic"),
            "models": resolved_models,
            "horizon": args.horizon,
            "seeds": args.seeds,
            "candidate_states_per_round": args.candidates,
            "n_agents": args.n_agents,
            "rule_count": args.rule_count,
            "actions": list(ACTIONS),
            "messages": list(MESSAGES),
            "tau": args.tau,
            "penalty_scale": args.penalty_scale,
            "home_scale": args.home_scale,
            "menu_friction": args.menu_friction,
            "message_cost": args.message_cost,
            "live_methods": live_methods,
            "analytic_methods": [list(item) for item in analytic_methods],
            "cache_path": str(CACHE_PATH.relative_to(ROOT)),
            "version": VERSION,
        },
        "summary": summary,
        "rows": rows,
    }
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = ANALYSIS_DIR / f"{args.out_prefix}_summary.json"
    rows_csv = ANALYSIS_DIR / f"{args.out_prefix}_rows.csv"
    summary_csv = ANALYSIS_DIR / f"{args.out_prefix}_summary.csv"
    summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_rows_csv(rows_csv, rows)
    write_summary_csv(summary_csv, summary)
    return {"summary_path": str(summary_path.relative_to(ROOT)), "rows_csv": str(rows_csv.relative_to(ROOT)), "summary_csv": str(summary_csv.relative_to(ROOT)), "payload": payload}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", default="cloudgpt")
    parser.add_argument("--models", type=parse_list, default=parse_list("gpt-5.4-mini-20260317"))
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
    parser.add_argument("--max-history", type=int, default=6)
    parser.add_argument("--max-tokens", type=int, default=220)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument(
        "--live-methods",
        type=parse_list,
        default=parse_list("live_llm_greedy,live_llm_belief,live_atom_tom0,live_atom_tom1,live_atom_adaptive_hedge,live_econ_bne"),
    )
    parser.add_argument("--skip-analytic", action="store_true")
    parser.add_argument("--out-prefix", default="courier_dispatch_live_llm")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    result = run(args)
    printable = {key: value for key, value in result.items() if key != "payload"}
    print(json.dumps(printable, indent=2))
    for row in result["payload"]["summary"]:
        if row["couple_lambda"] == 0.0:
            print(
                f"{row['model']} | {row['method']} beta={row['beta']}: "
                f"reward={row['final_mean_cumulative_reward']:.3f} "
                f"Ptrue={row['final_mean_true_tuple_posterior']:.3f} "
                f"rule_acc={row['final_mean_rule_marginal_accuracy']:.3f} "
                f"info_cost={row['final_mean_cumulative_total_information_cost']:.3f} "
                f"parse={row['live_parse_ok_rate']}"
            )


if __name__ == "__main__":
    main()