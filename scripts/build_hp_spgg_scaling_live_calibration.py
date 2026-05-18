"""Build E2/E3 HP-SPGG scaling calibrations with live LLM-as-judge cells."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_hpgg.llm_agent import call_judge
from llm_hpgg.personas import judge_system_prompt
from scripts.build_hp_spgg_scaling_calibration import PERSONA_LIBRARY, build_tensor


def main() -> None:
    parser = argparse.ArgumentParser(description="Build live LLM-judge scaling calibration for E2/E3.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--cache", required=True)
    parser.add_argument("--n", type=int, required=True)
    parser.add_argument("--type-count", type=int, required=True)
    parser.add_argument("--backend", default="cloudgpt")
    parser.add_argument("--judge-model", required=True)
    parser.add_argument("--profile-count", type=int, default=19)
    parser.add_argument("--profile-indices", default=None)
    parser.add_argument("--samples", type=int, default=1)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--trap", action="store_true")
    args = parser.parse_args()

    os.environ["LLM_HPGG_BACKEND"] = args.backend
    base = build_tensor(args.n, args.type_count, args.judge_model, samples=3, seed=args.seed, trap=args.trap)
    reward_tensor = np.array(base["reward_tensor"], copy=True)
    action_profiles = np.asarray(base["action_profiles"], dtype=float)
    profile_indices = parse_profile_indices(args.profile_indices, len(action_profiles))
    if profile_indices is None:
        profile_indices = select_profiles(len(action_profiles), args.profile_count)

    cache_path = Path(args.cache)
    cache = load_cache(cache_path)
    cached_cells = apply_cache(reward_tensor, cache)
    tasks = []
    for profile_index in profile_indices:
        for player_index in range(args.n):
            for persona_index in range(args.type_count):
                key = make_key(profile_index, player_index, persona_index, args.samples, args.judge_model)
                if key not in cache:
                    tasks.append((int(profile_index), int(player_index), int(persona_index), key))

    parse_failures: list[dict[str, object]] = []
    completed = 0
    if args.workers <= 1:
        for task in tasks:
            completed += run_task(task, action_profiles, reward_tensor, args.samples, args.judge_model, cache_path, cache, parse_failures)
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = [executor.submit(score_cell, task, action_profiles, args.samples, args.judge_model) for task in tasks]
            for future in as_completed(futures):
                result = future.result()
                if result["score"] is None:
                    parse_failures.extend(result["parse_failures"])
                    continue
                apply_result(result, reward_tensor, cache_path, cache)
                completed += 1

    payload = dict(base)
    payload["reward_tensor"] = reward_tensor
    payload["backend"] = f"{args.backend}_live_scaling"
    payload["judge_model"] = args.judge_model
    payload["live_profile_indices"] = np.array(profile_indices, dtype=int)
    payload["live_cell_count"] = int(len(profile_indices) * args.n * args.type_count)
    payload["new_live_cells"] = int(completed)
    payload["cached_cells_loaded"] = int(cached_cells)
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(output_path, **payload)

    report = {
        "out": str(output_path),
        "cache": str(cache_path),
        "backend": args.backend,
        "judge_model": args.judge_model,
        "n": args.n,
        "type_count": args.type_count,
        "profile_count": int(len(action_profiles)),
        "live_profile_indices": [int(value) for value in profile_indices],
        "live_cell_count": int(len(profile_indices) * args.n * args.type_count),
        "new_live_cells": int(completed),
        "cached_cells_loaded": int(cached_cells),
        "parse_failure_count": len(parse_failures),
        "parse_failures": parse_failures[:50],
        "workers": args.workers,
        "samples": args.samples,
    }
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "parse_failures"}, indent=2), flush=True)


def run_task(
    task: tuple[int, int, int, str],
    action_profiles: np.ndarray,
    reward_tensor: np.ndarray,
    samples: int,
    judge_model: str,
    cache_path: Path,
    cache: dict[str, dict[str, object]],
    parse_failures: list[dict[str, object]],
) -> int:
    result = score_cell(task, action_profiles, samples, judge_model)
    if result["score"] is None:
        parse_failures.extend(result["parse_failures"])
        return 0
    apply_result(result, reward_tensor, cache_path, cache)
    return 1


def score_cell(task: tuple[int, int, int, str], action_profiles: np.ndarray, samples: int, judge_model: str) -> dict[str, object]:
    profile_index, player_index, persona_index, key = task
    profile = action_profiles[profile_index]
    scores: list[float] = []
    replies: list[str] = []
    failures: list[dict[str, object]] = []
    for sample_index in range(samples):
        message = build_message(persona_index, player_index, profile, sample_index)
        try:
            reply = call_judge(judge_system_prompt(), message, model=judge_model, max_tokens=192, temperature=0.0)
            replies.append(reply)
            scores.append(parse_score(reply))
        except Exception as exc:
            failures.append(
                {
                    "profile_index": profile_index,
                    "player_index": player_index,
                    "persona_index": persona_index,
                    "sample_index": sample_index,
                    "error": str(exc),
                    "reply": replies[-1] if replies else "",
                }
            )
    return {
        "key": key,
        "profile_index": profile_index,
        "player_index": player_index,
        "persona_index": persona_index,
        "score": float(np.clip(np.mean(scores), 0.0, 1.0)) if scores else None,
        "scores": scores,
        "replies": replies,
        "parse_failures": failures,
    }


def apply_result(result: dict[str, object], reward_tensor: np.ndarray, cache_path: Path, cache: dict[str, dict[str, object]]) -> None:
    entry = {
        "key": str(result["key"]),
        "profile_index": int(result["profile_index"]),
        "player_index": int(result["player_index"]),
        "persona_index": int(result["persona_index"]),
        "score": float(result["score"]),
        "scores": result["scores"],
        "replies": result["replies"],
    }
    reward_tensor[entry["player_index"], entry["persona_index"], entry["profile_index"]] = entry["score"]
    append_cache(cache_path, entry)
    cache[entry["key"]] = entry


def build_message(persona_index: int, player_index: int, profile: np.ndarray, sample_index: int) -> str:
    persona = PERSONA_LIBRARY[persona_index]
    own = float(profile[player_index])
    others = [float(value) for index, value in enumerate(profile) if index != player_index]
    return (
        "You are scoring exactly one HP-SPGG outcome for a scaling experiment. "
        "Your entire response must be one valid JSON object and nothing else. "
        "Use exactly this schema: {\"score\": 0.73}.\n"
        f"Persona key: {persona.key}\n"
        f"Target contribution: {persona.target_contribution:.2f}\n"
        f"Cooperation weight: {persona.cooperation_weight:.2f}\n"
        f"Self-interest weight: {persona.self_interest_weight:.2f}\n"
        f"Fairness weight: {persona.fairness_weight:.2f}\n"
        f"Punishment weight: {persona.punishment_weight:.2f}\n"
        f"Player index: {player_index}\n"
        f"Player contribution: {own:.2f}\n"
        f"Other player contributions: {others}\n"
        f"Group mean contribution: {float(np.mean(profile)):.3f}\n"
        f"Sample index: {sample_index}\n"
        "Score this player's private satisfaction from 0.0 to 1.0 according to the persona profile. "
        "Return only the JSON object now."
    )


def parse_score(reply: str) -> float:
    try:
        payload = json.loads(reply)
        if isinstance(payload, dict) and "score" in payload:
            return float(np.clip(float(payload["score"]), 0.0, 1.0))
    except json.JSONDecodeError:
        pass
    match = re.search(r"(?:score\s*[:=]\s*)?([01](?:\.\d+)?)", reply, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"Could not parse score from reply: {reply!r}")
    return float(np.clip(float(match.group(1)), 0.0, 1.0))


def select_profiles(profile_count: int, profile_target: int) -> np.ndarray:
    if profile_target <= 0 or profile_target >= profile_count:
        return np.arange(profile_count, dtype=int)
    return np.unique(np.linspace(0, profile_count - 1, profile_target, dtype=int))


def parse_profile_indices(raw: str | None, profile_count: int) -> np.ndarray | None:
    if not raw:
        return None
    values = np.array([int(item.strip()) for item in raw.split(",") if item.strip()], dtype=int)
    if np.any(values < 0) or np.any(values >= profile_count):
        raise ValueError(f"profile indices out of range [0, {profile_count - 1}]: {values.tolist()}")
    return np.unique(values)


def make_key(profile_index: int, player_index: int, persona_index: int, samples: int, judge_model: str) -> str:
    return f"model={judge_model}:p={profile_index}:a={player_index}:t={persona_index}:s={samples}"


def load_cache(path: Path) -> dict[str, dict[str, object]]:
    if not path.exists():
        return {}
    cache: dict[str, dict[str, object]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entry = json.loads(line)
            cache[str(entry["key"])] = entry
    return cache


def append_cache(path: Path, entry: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def apply_cache(reward_tensor: np.ndarray, cache: dict[str, dict[str, object]]) -> int:
    applied = 0
    for entry in cache.values():
        reward_tensor[int(entry["player_index"]), int(entry["persona_index"]), int(entry["profile_index"])] = float(entry["score"])
        applied += 1
    return applied


if __name__ == "__main__":
    main()