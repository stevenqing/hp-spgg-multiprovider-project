"""Run LLM-based HP-SPGG coordinator baselines from a calibration tensor."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import time

import numpy as np

from .environment import load_calibration, rewards_for_types, welfare_for_types
from .llm_agent import call_player
from .personas import PERSONAS
from .coordinator import oracle_profile, CoordinatorState


ALGORITHMS = ("llm_greedy", "llm_belief")
ACTIVE_CACHE_PATH: Path | None = None


def run_seed(
    algorithm: str,
    reward_tensor: np.ndarray,
    action_profiles: np.ndarray,
    k_rounds: int,
    seed: int,
    model: str | None,
    cache: dict[str, str],
) -> tuple[np.ndarray, np.ndarray, list[dict[str, object]]]:
    rng = np.random.default_rng(seed)
    n, type_count, _ = reward_tensor.shape
    true_types = rng.integers(0, type_count, size=n)
    state = CoordinatorState.fresh(n, type_count, reward_tensor, action_profiles, beta=0.0)
    regrets = np.zeros(k_rounds, dtype=float)
    welfare = np.zeros(k_rounds, dtype=float)
    history: list[dict[str, object]] = []
    traces: list[dict[str, object]] = []

    for round_index in range(k_rounds):
        prompt = build_prompt(algorithm, action_profiles, history, round_index)
        reply = cached_llm_call(algorithm, prompt, model, cache)
        chosen, parsed = profile_from_reply(reply, action_profiles)
        oracle = oracle_profile(state, true_types)
        chosen_welfare = welfare_for_types(reward_tensor, true_types, chosen)
        oracle_welfare = welfare_for_types(reward_tensor, true_types, oracle)
        observed_rewards = rewards_for_types(reward_tensor, true_types, chosen)

        regrets[round_index] = max(0.0, oracle_welfare - chosen_welfare)
        welfare[round_index] = chosen_welfare
        event = {
            "round": round_index,
            "profile_index": int(chosen),
            "contributions": [float(value) for value in action_profiles[chosen]],
            "rewards": [float(value) for value in observed_rewards],
            "welfare": float(chosen_welfare),
            "oracle_welfare": float(oracle_welfare),
        }
        history.append(event)
        traces.append({**event, "parsed": parsed, "reply": reply[:1000]})

    return regrets, welfare, traces


def build_prompt(algorithm: str, action_profiles: np.ndarray, history: list[dict[str, object]], round_index: int) -> str:
    action_values = sorted({float(value) for value in action_profiles.reshape(-1)})
    personas = [f"{index}: {persona.label} - {persona.description}" for index, persona in enumerate(PERSONAS)]
    recent_history = history[-6:]
    mode = (
        "Choose the joint contribution profile that maximizes expected total welfare under persona uncertainty."
        if algorithm == "llm_greedy"
        else "Infer likely hidden persona types from the reward history, then choose the next joint contribution profile to maximize welfare and reduce uncertainty."
    )
    return json.dumps(
        {
            "task": "HP-SPGG coordinator baseline",
            "mode": mode,
            "round": round_index,
            "players": int(action_profiles.shape[1]),
            "allowed_contributions": action_values,
            "possible_personas": personas,
            "public_history": recent_history,
            "response_schema": {
                "contributions": ["one allowed contribution per player"],
                "reason": "brief reason",
                "inferred_personas": "optional for llm_belief",
            },
            "instruction": "Return only valid JSON. Do not include markdown or prose outside JSON.",
        },
        indent=2,
    )


def cached_llm_call(algorithm: str, prompt: str, model: str | None, cache: dict[str, str]) -> str:
    key = hashlib.sha256(f"{algorithm}\n{model or ''}\n{prompt}".encode("utf-8")).hexdigest()
    if key not in cache:
        system = "You are a careful multi-agent public-goods-game coordinator. Output valid JSON only."
        retries = int(os.getenv("LLM_BASELINE_CALL_RETRIES", "8"))
        base_delay = float(os.getenv("LLM_BASELINE_RETRY_BASE_SECONDS", "5"))
        last_error: Exception | None = None
        for attempt in range(retries):
            try:
                cache[key] = call_player(system, prompt, model=model, max_tokens=192, temperature=0.2)
                if ACTIVE_CACHE_PATH is not None:
                    save_cache(ACTIVE_CACHE_PATH, cache)
                break
            except Exception as exc:
                last_error = exc
                delay = min(base_delay * (2**attempt), 120.0)
                print(
                    f"CloudGPT call failed for {algorithm}; retry {attempt + 1}/{retries} after {delay:.1f}s: {exc}",
                    flush=True,
                )
                time.sleep(delay)
        else:
            raise RuntimeError(f"LLM baseline call failed after {retries} runner retries: {last_error}")
    return cache[key]


def profile_from_reply(reply: str, action_profiles: np.ndarray) -> tuple[int, dict[str, object]]:
    parsed: dict[str, object] = {}
    try:
        parsed = json.loads(extract_json(reply))
        raw = parsed.get("contributions", [])
        contributions = np.array([float(value) for value in raw], dtype=float)
    except Exception:
        contributions = np.full(action_profiles.shape[1], 0.5, dtype=float)
        parsed = {"parse_error": True}
    if contributions.shape != (action_profiles.shape[1],):
        contributions = np.resize(contributions, action_profiles.shape[1]).astype(float)
    distances = np.linalg.norm(action_profiles - contributions[None, :], axis=1)
    return int(np.argmin(distances)), parsed


def extract_json(text: str) -> str:
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON object found")
    return match.group(0)


def load_cache(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_cache(path: Path, cache: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def main() -> None:
    global ACTIVE_CACHE_PATH

    parser = argparse.ArgumentParser(description="Run LLM-based HP-SPGG coordinator baselines.")
    parser.add_argument("--K", type=int, default=10)
    parser.add_argument("--n", type=int, default=3)
    parser.add_argument("--seeds", type=int, default=2)
    parser.add_argument("--algos", nargs="+", default=list(ALGORITHMS))
    parser.add_argument("--calibration", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--trace-out")
    parser.add_argument("--cache", default="logs/llm_baseline_cache.json")
    parser.add_argument("--model")
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
    regrets = np.zeros((len(args.algos), args.seeds, args.K), dtype=float)
    welfare = np.zeros_like(regrets)
    all_traces: list[dict[str, object]] = []

    for algo_index, algorithm in enumerate(args.algos):
        if algorithm not in ALGORITHMS:
            raise ValueError(f"Unknown LLM baseline: {algorithm}")
        for seed_index in range(args.seeds):
            seed = 90_000 + 10_000 * algo_index + seed_index
            regrets[algo_index, seed_index], welfare[algo_index, seed_index], traces = run_seed(
                algorithm, reward_tensor, action_profiles, args.K, seed, args.model, cache
            )
            all_traces.append({"algorithm": algorithm, "seed_index": seed_index, "seed": seed, "trace": traces})
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
        model=args.model or "",
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