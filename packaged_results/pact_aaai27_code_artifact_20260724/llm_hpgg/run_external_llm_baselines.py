"""Run full external-style LLM coordination baselines adapted to HP-SPGG.

Implemented families:
- A-ToM: 0/1/2-order Theory-of-Mind agents plus FTL/Hedge adaptive ToM.
- ECON: coordinator/executor belief-driven BNE refinement with final commitment.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
import os
from pathlib import Path
import re
import time
from typing import Any
import threading
import uuid

import numpy as np

from .coordinator import CoordinatorState, oracle_profile
from .environment import load_calibration, rewards_for_types, welfare_for_types
from .llm_agent import call_player
from .personas import PERSONAS


ALGORITHMS = (
    "atom_tom0",
    "atom_tom1",
    "atom_tom2",
    "atom_adaptive_ftl",
    "atom_adaptive_hedge",
    "econ_bne",
)

ACTIVE_CACHE_PATH: Path | None = None
CACHE_LOCK = threading.Lock()
CACHE_NEW_SINCE_SAVE = 0
PARSE_REPAIR_COUNT = 0


def run_seed(
    algorithm: str,
    reward_tensor: np.ndarray,
    action_profiles: np.ndarray,
    k_rounds: int,
    seed: int,
    model: str | None,
    cache: dict[str, str],
    econ_rounds: int,
    offline: bool,
) -> tuple[np.ndarray, np.ndarray, list[dict[str, Any]], np.ndarray]:
    rng = np.random.default_rng(seed)
    n, type_count, _ = reward_tensor.shape
    true_types = rng.integers(0, type_count, size=n)
    state = CoordinatorState.fresh(n, type_count, reward_tensor, action_profiles, beta=0.0)
    action_values = sorted({float(value) for value in action_profiles.reshape(-1)})
    profile_lookup = {tuple(float(value) for value in profile): index for index, profile in enumerate(action_profiles)}
    regrets = np.zeros(k_rounds, dtype=float)
    welfare = np.zeros(k_rounds, dtype=float)
    history: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    atom_states = [AdaptiveToMState() for _ in range(n)]

    for round_index in range(k_rounds):
        if algorithm.startswith("atom_"):
            chosen, info = choose_atom_profile(
                algorithm,
                round_index,
                action_values,
                action_profiles,
                profile_lookup,
                history,
                atom_states,
                model,
                cache,
                rng,
                offline,
            )
        elif algorithm == "econ_bne":
            chosen, info = choose_econ_profile(
                round_index,
                action_values,
                action_profiles,
                history,
                model,
                cache,
                rng,
                econ_rounds,
                offline,
            )
        else:
            raise ValueError(f"Unknown external LLM baseline: {algorithm}")

        oracle = oracle_profile(state, true_types)
        chosen_welfare = welfare_for_types(reward_tensor, true_types, chosen)
        oracle_welfare = welfare_for_types(reward_tensor, true_types, oracle)
        observed_rewards = rewards_for_types(reward_tensor, true_types, chosen)

        event = {
            "round": round_index,
            "profile_index": int(chosen),
            "contributions": [float(value) for value in action_profiles[chosen]],
            "rewards": [float(value) for value in observed_rewards],
            "welfare": float(chosen_welfare),
            "oracle_welfare": float(oracle_welfare),
            "info": info,
        }
        history.append(event)
        traces.append(event)
        update_atom_losses(atom_states, info, event["contributions"])
        regrets[round_index] = max(0.0, oracle_welfare - chosen_welfare)
        welfare[round_index] = chosen_welfare
    return regrets, welfare, traces, true_types


class AdaptiveToMState:
    def __init__(self) -> None:
        self.loss = np.zeros(3, dtype=float)
        self.loss_history: list[list[float]] = []
        self.prob_history: list[list[float]] = []


def choose_atom_profile(
    algorithm: str,
    round_index: int,
    action_values: list[float],
    action_profiles: np.ndarray,
    profile_lookup: dict[tuple[float, ...], int],
    history: list[dict[str, Any]],
    atom_states: list[AdaptiveToMState],
    model: str | None,
    cache: dict[str, str],
    rng: np.random.Generator,
    offline: bool,
) -> tuple[int, dict[str, Any]]:
    n = action_profiles.shape[1]
    player_rng_seeds = rng.integers(0, np.iinfo(np.int64).max, size=n, dtype=np.int64)

    def choose_for_player(player_index: int) -> tuple[float, dict[str, Any]]:
        player_rng = np.random.default_rng(int(player_rng_seeds[player_index]))
        if algorithm == "atom_tom0":
            prediction = []
            selected_level = 0
        elif algorithm == "atom_tom1":
            prediction = predict_other_actions(0, player_index, action_values, history, model, cache, player_rng, offline)
            selected_level = 1
        elif algorithm == "atom_tom2":
            prediction = predict_other_actions(1, player_index, action_values, history, model, cache, player_rng, offline)
            selected_level = 2
        else:
            candidates = [
                predict_other_actions(level, player_index, action_values, history, model, cache, player_rng, offline)
                for level in range(3)
            ]
            selected_level, probabilities = select_tom_level(atom_states[player_index], algorithm, player_rng)
            atom_states[player_index].prob_history.append(probabilities)
            prediction = candidates[selected_level]
        action, parsed = choose_atom_action(
            player_index,
            selected_level,
            prediction,
            action_values,
            history,
            model,
            cache,
            player_rng,
            offline,
        )
        return action, {"player": player_index, "tom_level": selected_level, "predicted_others": prediction, "parsed": parsed}

    agent_workers = external_agent_workers(n, model)
    with ThreadPoolExecutor(max_workers=agent_workers) as executor:
        player_results = list(executor.map(choose_for_player, range(n)))
    chosen_actions = [result[0] for result in player_results]
    per_player = [result[1] for result in player_results]
    profile = tuple(float(value) for value in chosen_actions)
    return profile_lookup[profile], {"family": "A-ToM", "round": round_index, "players": per_player}


def select_tom_level(state: AdaptiveToMState, algorithm: str, rng: np.random.Generator) -> tuple[int, list[float]]:
    if algorithm == "atom_adaptive_ftl":
        selected = int(np.argmin(state.loss))
        probabilities = [0.0, 0.0, 0.0]
        probabilities[selected] = 1.0
        return selected, probabilities
    if algorithm == "atom_adaptive_hedge":
        weights = np.exp(-state.loss)
        probabilities = (weights / weights.sum()).astype(float)
        return int(rng.choice(3, p=probabilities)), probabilities.tolist()
    raise ValueError(f"Unknown A-ToM algorithm: {algorithm}")


def predict_other_actions(
    tom_level: int,
    player_index: int,
    action_values: list[float],
    history: list[dict[str, Any]],
    model: str | None,
    cache: dict[str, str],
    rng: np.random.Generator,
    offline: bool,
) -> list[float]:
    if offline:
        return heuristic_predict_others(player_index, action_values, history, tom_level)
    prompt = {
        "task": "A-ToM HP-SPGG partner action prediction",
        "tom_level": tom_level,
        "player_index": player_index,
        "allowed_contributions": action_values,
        "recent_public_history": history[-6:],
        "instruction": "Predict the next contributions of every other player. Return only JSON.",
        "response_schema": {"other_contributions": "array of allowed contribution numbers, excluding this player"},
    }
    reply = cached_llm_call("atom_predict", json.dumps(prompt, indent=2), model, cache, max_tokens=160, temperature=0.2)
    try:
        parsed = json.loads(extract_json(reply))
        values = [nearest_action(float(value), action_values) for value in parsed.get("other_contributions", [])]
    except Exception as exc:
        if os.getenv("EXTERNAL_STRICT_PARSING", "0") == "1":
            repair_prompt = strict_repair_prompt(json.dumps(prompt, indent=2), reply, '{"other_contributions": [0.5, 0.5]}')
            repaired = cached_llm_call("atom_predict_repair", repair_prompt, model, cache, max_tokens=512, temperature=0.0)
            try:
                parsed = json.loads(extract_json(repaired))
                values = [nearest_action(float(value), action_values) for value in parsed.get("other_contributions", [])]
            except Exception as repair_exc:
                invalidate_cached_llm_call("atom_predict_repair", repair_prompt, model, cache, temperature=0.0)
                raise ValueError(f"A-ToM prediction repair failed: {repaired[:300]!r}") from repair_exc
            parsed["_repaired"] = True
            record_parse_repair()
        else:
            values = []
    needed = max(0, inferred_player_count(history, default=3) - 1)
    while len(values) < needed:
        values.append(heuristic_default_action(action_values, history))
    return values[:needed]


def choose_atom_action(
    player_index: int,
    tom_level: int,
    predicted_others: list[float],
    action_values: list[float],
    history: list[dict[str, Any]],
    model: str | None,
    cache: dict[str, str],
    rng: np.random.Generator,
    offline: bool,
) -> tuple[float, dict[str, Any]]:
    if offline:
        return heuristic_action(action_values, history, player_index, predicted_others, rng), {"offline": True}
    prompt = {
        "task": "A-ToM HP-SPGG action selection",
        "player_index": player_index,
        "tom_level": tom_level,
        "allowed_contributions": action_values,
        "predicted_other_player_contributions": predicted_others,
        "recent_public_history": history[-6:],
        "instruction": "Choose this player's next contribution to improve long-run public-goods welfare. Return only JSON.",
        "response_schema": {"contribution": "one allowed contribution number", "reason": "short"},
    }
    reply = cached_llm_call("atom_act", json.dumps(prompt, indent=2), model, cache, max_tokens=160, temperature=0.2)
    try:
        parsed = json.loads(extract_json(reply))
        return nearest_action(float(parsed.get("contribution", 0.5)), action_values), parsed
    except Exception as exc:
        if os.getenv("EXTERNAL_STRICT_PARSING", "0") == "1":
            original_prompt = json.dumps(prompt, indent=2)
            repair_prompt = strict_repair_prompt(original_prompt, reply, '{"contribution": 0.5, "reason": "short"}')
            repaired = cached_llm_call("atom_act_repair", repair_prompt, model, cache, max_tokens=512, temperature=0.0)
            try:
                parsed = json.loads(extract_json(repaired))
                parsed["_repaired"] = True
                record_parse_repair()
                return nearest_action(float(parsed.get("contribution", 0.5)), action_values), parsed
            except Exception as repair_exc:
                invalidate_cached_llm_call("atom_act_repair", repair_prompt, model, cache, temperature=0.0)
                raise ValueError(f"A-ToM action repair failed: {repaired[:300]!r}") from repair_exc
        return heuristic_action(action_values, history, player_index, predicted_others, rng), {"parse_error": True, "reply": reply[:300]}


def update_atom_losses(atom_states: list[AdaptiveToMState], info: dict[str, Any], contributions: list[float]) -> None:
    if info.get("family") != "A-ToM":
        return
    for player_info in info.get("players", []):
        player_index = int(player_info["player"])
        state = atom_states[player_index]
        predicted = player_info.get("predicted_others", [])
        if not predicted:
            continue
        actual = [float(value) for idx, value in enumerate(contributions) if idx != player_index]
        state.loss_history.append(state.loss.tolist())
        selected = int(player_info.get("tom_level", 0))
        if selected < len(state.loss) and any(not math.isclose(a, p, abs_tol=1e-9) for a, p in zip(actual, predicted)):
            state.loss[selected] += 1.0


def choose_econ_profile(
    round_index: int,
    action_values: list[float],
    action_profiles: np.ndarray,
    history: list[dict[str, Any]],
    model: str | None,
    cache: dict[str, str],
    rng: np.random.Generator,
    econ_rounds: int,
    offline: bool,
) -> tuple[int, dict[str, Any]]:
    n = action_profiles.shape[1]
    if offline:
        contributions = [heuristic_default_action(action_values, history)] * n
        return nearest_profile(contributions, action_profiles), {"family": "ECON", "offline": True, "round": round_index}

    observation = build_econ_observation(round_index, action_values, history, n)
    strategy = econ_strategy(observation, model, cache)
    commitment: list[float] | None = None
    iteration_history: list[dict[str, Any]] = []
    temperature_schedule = np.linspace(0.2, 0.6, n).tolist()

    for iteration in range(max(1, econ_rounds)):
        agent_workers = external_agent_workers(n, model)
        with ThreadPoolExecutor(max_workers=agent_workers) as executor:
            executor_outputs = list(
                executor.map(
                    lambda agent_index: econ_executor_response(
                        observation,
                        strategy,
                        agent_index,
                        commitment,
                        temperature_schedule[agent_index],
                        model,
                        cache,
                    ),
                    range(n),
                )
            )
        new_commitment, parsed = econ_commitment(observation, strategy, executor_outputs, action_values, model, cache)
        iteration_history.append({"iteration": iteration, "commitment": new_commitment, "executors": executor_outputs})
        if commitment is not None and all(math.isclose(a, b, abs_tol=1e-9) for a, b in zip(commitment, new_commitment)):
            commitment = new_commitment
            break
        commitment = new_commitment
        temperature_schedule = [max(0.1, value * 0.85) for value in temperature_schedule]
    chosen = nearest_profile(commitment or [0.5] * n, action_profiles)
    return chosen, {"family": "ECON", "strategy": strategy[:500], "iterations": iteration_history}


def build_econ_observation(round_index: int, action_values: list[float], history: list[dict[str, Any]], n: int) -> str:
    return json.dumps(
        {
            "task": "HP-SPGG ECON coordination",
            "round": round_index,
            "players": n,
            "allowed_contributions": action_values,
            "possible_personas": [f"{idx}: {persona.label} - {persona.description}" for idx, persona in enumerate(PERSONAS)],
            "recent_public_history": history[-6:],
            "goal": "Choose a joint contribution profile with high expected total welfare under hidden persona uncertainty.",
        },
        indent=2,
    )


def econ_strategy(observation: str, model: str | None, cache: dict[str, str]) -> str:
    prompt = observation + "\nReturn a concise coordination strategy only, no final action profile."
    return cached_llm_call("econ_strategy", prompt, model, cache, max_tokens=180, temperature=0.1)


def econ_executor_response(
    observation: str,
    strategy: str,
    agent_index: int,
    previous_commitment: list[float] | None,
    temperature: float,
    model: str | None,
    cache: dict[str, str],
) -> str:
    prompt = json.dumps(
        {
            "observation": json.loads(observation),
            "strategy": strategy,
            "executor_agent_index": agent_index,
            "previous_commitment": previous_commitment,
            "instruction": "Act as one ECON executor. State your belief about personas and propose a complete joint contribution profile. Return JSON only.",
            "response_schema": {"belief": "short", "contributions": "array, one allowed contribution per player", "confidence": "0 to 1"},
        },
        indent=2,
    )
    return cached_llm_call(f"econ_executor_{agent_index}", prompt, model, cache, max_tokens=220, temperature=temperature)


def econ_commitment(
    observation: str,
    strategy: str,
    executor_outputs: list[str],
    action_values: list[float],
    model: str | None,
    cache: dict[str, str],
) -> tuple[list[float], dict[str, Any]]:
    prompt = json.dumps(
        {
            "observation": json.loads(observation),
            "strategy": strategy,
            "executor_outputs": executor_outputs,
            "instruction": "Act as the ECON coordinator. Aggregate executor beliefs into one final commitment. Return JSON only.",
            "response_schema": {"contributions": "array, one allowed contribution per player", "confidence": "0 to 1", "reason": "short"},
        },
        indent=2,
    )
    reply = cached_llm_call("econ_commitment", prompt, model, cache, max_tokens=220, temperature=0.1)
    try:
        parsed = json.loads(extract_json(reply))
        contributions = [nearest_action(float(value), action_values) for value in parsed.get("contributions", [])]
    except Exception as exc:
        if os.getenv("EXTERNAL_STRICT_PARSING", "0") == "1":
            repair_prompt = strict_repair_prompt(prompt, reply, '{"contributions": [0.5, 0.5, 0.5], "confidence": 0.5, "reason": "short"}')
            repaired = cached_llm_call("econ_commitment_repair", repair_prompt, model, cache, max_tokens=512, temperature=0.0)
            try:
                parsed = json.loads(extract_json(repaired))
                parsed["_repaired"] = True
                record_parse_repair()
                contributions = [nearest_action(float(value), action_values) for value in parsed.get("contributions", [])]
            except Exception as repair_exc:
                invalidate_cached_llm_call("econ_commitment_repair", repair_prompt, model, cache, temperature=0.0)
                raise ValueError(f"ECON commitment repair failed: {repaired[:300]!r}") from repair_exc
        else:
            parsed = {"parse_error": True, "reply": reply[:300]}
            contributions = []
    n = int(json.loads(observation).get("players", 3))
    while len(contributions) < n:
        contributions.append(heuristic_default_action(action_values, []))
    return contributions[:n], parsed


def cached_llm_call(kind: str, prompt: str, model: str | None, cache: dict[str, str], max_tokens: int, temperature: float) -> str:
    global CACHE_NEW_SINCE_SAVE
    key = hashlib.sha256(f"{kind}\n{model or ''}\n{temperature}\n{prompt}".encode("utf-8")).hexdigest()
    with CACHE_LOCK:
        cached = cache.get(key)
    if cached is None:
        if os.getenv("EXTERNAL_CACHE_ONLY", "0") == "1":
            raise KeyError(f"External response cache miss for {kind}: {key}")
        system = "You are a careful multi-agent public-goods-game coordinator. Return valid JSON when requested."
        retries = int(os.getenv("EXTERNAL_LLM_CALL_RETRIES", "8"))
        base_delay = float(os.getenv("EXTERNAL_LLM_RETRY_BASE_SECONDS", "5"))
        last_error: Exception | None = None
        for attempt in range(retries):
            try:
                reply = call_player(system, prompt, model=model, max_tokens=max_tokens, temperature=temperature)
                with CACHE_LOCK:
                    if key not in cache:
                        cache[key] = reply
                        CACHE_NEW_SINCE_SAVE += 1
                    save_every = max(1, int(os.getenv("EXTERNAL_CACHE_SAVE_EVERY", "10")))
                    if ACTIVE_CACHE_PATH is not None and CACHE_NEW_SINCE_SAVE >= save_every:
                        save_cache(ACTIVE_CACHE_PATH, cache)
                        CACHE_NEW_SINCE_SAVE = 0
                break
            except Exception as exc:
                last_error = exc
                if "401" in str(exc) or "Unauthorized" in str(exc):
                    raise RuntimeError("CloudGPT access token expired or is invalid") from exc
                delay = min(base_delay * (2**attempt), 120.0)
                print(
                    f"CloudGPT call failed for {kind}; retry {attempt + 1}/{retries} after {delay:.1f}s: {exc}",
                    flush=True,
                )
                time.sleep(delay)
        else:
            raise RuntimeError(f"External LLM call failed after {retries} runner retries: {last_error}")
    with CACHE_LOCK:
        return cache[key]


def invalidate_cached_llm_call(
    kind: str,
    prompt: str,
    model: str | None,
    cache: dict[str, str],
    temperature: float,
) -> None:
    key = hashlib.sha256(f"{kind}\n{model or ''}\n{temperature}\n{prompt}".encode("utf-8")).hexdigest()
    with CACHE_LOCK:
        cache.pop(key, None)
        if ACTIVE_CACHE_PATH is not None:
            save_cache(ACTIVE_CACHE_PATH, cache)


def extract_json(text: str) -> str:
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON object found")
    return match.group(0)


def strict_repair_prompt(original_prompt: str, invalid_reply: str, schema_example: str) -> str:
    return (
        "Reformat the previous reply without changing its selected action or prediction. "
        "Copy the required numeric decision fields, but do not repeat any explanation. "
        "If a reason field is required, set it to exactly 'format repair'. "
        "Return one compact JSON object only, with no markdown or prose.\n"
        f"Required schema example: {schema_example}\n"
        f"Original request:\n{original_prompt}\n"
        f"Previous invalid reply:\n{invalid_reply}"
    )


def external_agent_workers(n: int, model: str | None) -> int:
    model_name = (model or "").lower()
    variable = "EXTERNAL_KIMI_AGENT_WORKERS" if model_name.startswith("kimi-") else "EXTERNAL_AGENT_WORKERS"
    default = os.getenv("EXTERNAL_AGENT_WORKERS", "1")
    return min(n, max(1, int(os.getenv(variable, default))))


def record_parse_repair() -> None:
    global PARSE_REPAIR_COUNT
    with CACHE_LOCK:
        PARSE_REPAIR_COUNT += 1


def nearest_action(value: float, action_values: list[float]) -> float:
    return float(min(action_values, key=lambda candidate: abs(candidate - value)))


def nearest_profile(contributions: list[float], action_profiles: np.ndarray) -> int:
    values = np.array(contributions, dtype=float)
    if values.shape != (action_profiles.shape[1],):
        values = np.resize(values, action_profiles.shape[1]).astype(float)
    distances = np.linalg.norm(action_profiles - values[None, :], axis=1)
    return int(np.argmin(distances))


def inferred_player_count(history: list[dict[str, Any]], default: int) -> int:
    if history:
        return len(history[-1].get("contributions", []))
    return default


def heuristic_default_action(action_values: list[float], history: list[dict[str, Any]]) -> float:
    if not history:
        return nearest_action(0.5, action_values)
    recent = np.array([event["contributions"] for event in history[-3:]], dtype=float)
    return nearest_action(float(np.mean(recent)), action_values)


def heuristic_predict_others(player_index: int, action_values: list[float], history: list[dict[str, Any]], tom_level: int) -> list[float]:
    n = inferred_player_count(history, default=3)
    if not history:
        base = 0.5 + 0.25 * (tom_level == 2)
        return [nearest_action(base, action_values) for _ in range(n - 1)]
    recent = np.array([event["contributions"] for event in history[-3:]], dtype=float)
    mean_actions = np.mean(recent, axis=0)
    return [nearest_action(float(mean_actions[idx]), action_values) for idx in range(n) if idx != player_index]


def heuristic_action(
    action_values: list[float],
    history: list[dict[str, Any]],
    player_index: int,
    predicted_others: list[float],
    rng: np.random.Generator,
) -> float:
    if predicted_others and float(np.mean(predicted_others)) >= 0.5:
        target = 0.75
    elif history:
        target = float(np.mean([event["contributions"][player_index] for event in history[-3:]]))
    else:
        target = 0.5
    if rng.random() < 0.05:
        return float(rng.choice(action_values))
    return nearest_action(target, action_values)


def load_cache(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_cache(path: Path, cache: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(json.dumps(cache, indent=2), encoding="utf-8")
    last_error: PermissionError | None = None
    for _ in range(20):
        try:
            temporary.replace(path)
            return
        except PermissionError as exc:
            last_error = exc
            time.sleep(0.1)
    temporary.unlink(missing_ok=True)
    if last_error is not None:
        raise last_error


def main() -> None:
    global ACTIVE_CACHE_PATH

    parser = argparse.ArgumentParser(description="Run full external-style LLM baselines adapted to HP-SPGG.")
    parser.add_argument("--K", type=int, default=10)
    parser.add_argument("--n", type=int, default=3)
    parser.add_argument("--seeds", type=int, default=2)
    parser.add_argument("--algos", nargs="+", default=list(ALGORITHMS))
    parser.add_argument("--calibration", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--trace-out")
    parser.add_argument("--cache", default="logs/external_llm_baseline_cache.json")
    parser.add_argument("--model")
    parser.add_argument("--econ-rounds", type=int, default=3)
    parser.add_argument("--seed-indices", nargs="+", type=int, help="Run only these zero-based seed indices.")
    parser.add_argument("--seed-workers", type=int, default=1, help="Independent seed trajectories run concurrently.")
    parser.add_argument("--matched-seeds", action="store_true", help="Use --seed-offset + seed_index for every algorithm.")
    parser.add_argument("--seed-offset", type=int, default=0)
    parser.add_argument("--offline", action="store_true", help="Use deterministic offline heuristics for smoke tests.")
    args = parser.parse_args()

    calibration = load_calibration(args.calibration)
    reward_tensor = np.asarray(calibration["reward_tensor"], dtype=float)
    action_profiles = np.asarray(calibration["action_profiles"], dtype=float)
    n, _, _ = reward_tensor.shape
    if args.n != n:
        raise ValueError(f"Calibration n={n} does not match --n={args.n}")

    cache_path = Path(args.cache)
    ACTIVE_CACHE_PATH = cache_path
    cache = load_cache(cache_path)
    seed_indices = list(range(args.seeds)) if args.seed_indices is None else list(args.seed_indices)
    if not seed_indices:
        raise ValueError("At least one seed index is required.")
    if any(seed_index < 0 or seed_index >= args.seeds for seed_index in seed_indices):
        raise ValueError(f"Seed indices must be in [0, {args.seeds}).")
    regrets = np.zeros((len(args.algos), len(seed_indices), args.K), dtype=float)
    welfare = np.zeros_like(regrets)
    true_types = np.zeros((len(args.algos), len(seed_indices), n), dtype=int)
    rng_seeds = np.zeros((len(args.algos), len(seed_indices)), dtype=int)
    all_traces: list[dict[str, Any]] = []

    for algo_index, algorithm in enumerate(args.algos):
        if algorithm not in ALGORITHMS:
            raise ValueError(f"Unknown external LLM baseline: {algorithm}")
        canonical_algo_index = ALGORITHMS.index(algorithm)
        def run_one_seed(seed_position_and_index: tuple[int, int]) -> tuple[int, int, np.ndarray, np.ndarray, list[dict[str, Any]], np.ndarray]:
            seed_position, seed_index = seed_position_and_index
            seed = (
                args.seed_offset + seed_index
                if args.matched_seeds
                else 120_000 + 10_000 * canonical_algo_index + seed_index
            )
            seed_regrets, seed_welfare, traces, seed_true_types = run_seed(
                algorithm,
                reward_tensor,
                action_profiles,
                args.K,
                seed,
                args.model,
                cache,
                args.econ_rounds,
                args.offline,
            )
            return seed_position, seed, seed_regrets, seed_welfare, traces, seed_true_types

        with ThreadPoolExecutor(max_workers=max(1, args.seed_workers)) as executor:
            seed_results = list(executor.map(run_one_seed, enumerate(seed_indices)))
        for seed_position, seed, seed_regrets, seed_welfare, traces, seed_true_types in seed_results:
            seed_index = seed_indices[seed_position]
            regrets[algo_index, seed_position] = seed_regrets
            welfare[algo_index, seed_position] = seed_welfare
            true_types[algo_index, seed_position] = seed_true_types
            rng_seeds[algo_index, seed_position] = seed
            all_traces.append(
                {
                    "algorithm": algorithm,
                    "seed_index": seed_index,
                    "seed": seed,
                    "true_types": seed_true_types.astype(int).tolist(),
                    "initial_state_id": "fixed_hp_spgg_initial_state",
                    "trace": traces,
                }
            )
            save_cache(cache_path, cache)

    cumulative_regret = np.cumsum(regrets, axis=2)
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        output_path,
        algorithms=np.array(args.algos),
        regrets=regrets,
        cumulative_regret=cumulative_regret,
        welfare=welfare,
        backend=os.getenv("LLM_HPGG_BACKEND", str(calibration.get("backend", "unknown"))),
        K=args.K,
        seeds=args.seeds,
        seed_indices=np.array(seed_indices, dtype=int),
        model=args.model or "",
        econ_rounds=args.econ_rounds,
        matched_seeds=bool(args.matched_seeds),
        seed_offset=int(args.seed_offset),
        rng_seeds=rng_seeds,
        true_types=true_types,
        initial_state_id="fixed_hp_spgg_initial_state",
        response_cache=str(cache_path),
        response_cache_entries=len(cache),
        seed_workers=int(args.seed_workers),
        parse_repair_count=int(PARSE_REPAIR_COUNT),
    )
    if args.trace_out:
        trace_path = Path(args.trace_out)
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        trace_path.write_text(json.dumps(all_traces, indent=2), encoding="utf-8")
    for algorithm, value in zip(args.algos, cumulative_regret[:, :, -1].mean(axis=1)):
        print(f"{algorithm}: final_cumulative_regret_mean={value:.4f}")
    print(f"saved={output_path}")


if __name__ == "__main__":
    main()