"""Build a calibration tensor with live LLM-as-judge scores."""

from __future__ import annotations

import argparse
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np

from .environment import CalibrationBundle, build_reward_tensor, load_calibration, save_calibration, tid_min_gap
from .llm_agent import call_judge
from .personas import PERSONAS, judge_system_prompt


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an HP-SPGG calibration tensor with live judge calls.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--report", default=None)
    parser.add_argument("--backend", default=os.getenv("LLM_HPGG_BACKEND", "cloudgpt"))
    parser.add_argument("--n", type=int, default=3)
    parser.add_argument("--samples", type=int, default=1)
    parser.add_argument("--max-profiles", type=int, default=12, help="Number of joint action profiles to score live; the rest use synthetic fallback.")
    parser.add_argument("--profile-indices", default=None, help="Comma-separated action profile indices to score live.")
    parser.add_argument("--cell-budget", type=int, default=0, help="Maximum number of new player/persona/profile cells to call; 0 means no limit.")
    parser.add_argument("--base-calibration", default=None, help="Existing calibration .npy to continue from.")
    parser.add_argument("--cache", default=None, help="JSONL cache of completed live score cells.")
    parser.add_argument("--save-every", type=int, default=12, help="Save checkpoint after this many new live cells.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--judge-model", default=None)
    parser.add_argument("--trap", action="store_true", help="Use the G_trap reward surface for synthetic fallback and metadata.")
    parser.add_argument("--no-synthetic-fallback", action="store_true")
    parser.add_argument("--workers", type=int, default=1, help="Concurrent live judge calls. Use 1 for serial execution.")
    args = parser.parse_args()

    os.environ["LLM_HPGG_BACKEND"] = args.backend
    base = build_reward_tensor(args.n, args.backend, samples=3, seed=args.seed, trap=args.trap)
    reward_tensor = load_base_reward_tensor(args.base_calibration, base)
    cache_path = Path(args.cache) if args.cache else Path(args.out).with_suffix(".cache.jsonl")
    cache = load_cache(cache_path)
    cached_cells = apply_cache(reward_tensor, cache)
    live_profile_indices = parse_profile_indices(args.profile_indices, len(base.action_profiles))
    if live_profile_indices is None:
        live_profile_indices = select_profiles(len(base.action_profiles), args.max_profiles)
    parse_failures: list[dict[str, object]] = []
    new_live_cells = 0
    skipped_cached_cells = 0
    partial_cached_cells = 0
    pending_tasks: list[tuple[int, int, int, np.ndarray, str, dict[str, object] | None]] = []

    for profile_index in live_profile_indices:
        profile = base.action_profiles[profile_index]
        for player_index in range(args.n):
            for persona_index, persona in enumerate(PERSONAS):
                cache_key = make_cache_key(profile_index, player_index, persona_index, args.samples)
                cached_entry = cache.get(cache_key)
                if cached_entry is not None and cache_entry_complete(cached_entry, args.samples):
                    skipped_cached_cells += 1
                    continue
                if cached_entry is not None:
                    partial_cached_cells += 1
                if args.cell_budget and len(pending_tasks) >= args.cell_budget:
                    break
                pending_tasks.append((int(profile_index), int(player_index), int(persona_index), np.array(profile, copy=True), cache_key, cached_entry))
            if args.cell_budget and len(pending_tasks) >= args.cell_budget:
                break
        if args.cell_budget and len(pending_tasks) >= args.cell_budget:
            break

    if args.workers <= 1:
        for profile_index, player_index, persona_index, profile, cache_key, cached_entry in pending_tasks:
            result = score_live_cell(profile_index, player_index, persona_index, profile, cache_key, args.samples, args.judge_model, cached_entry)
            if result["scores"]:
                apply_live_cell_result(result, reward_tensor, cache_path, cache)
                new_live_cells += 1
                if args.save_every > 0 and new_live_cells % args.save_every == 0:
                    save_current_calibration(base, reward_tensor, args.backend, args.out, args.trap, args.judge_model)
                if len(result["scores"]) < args.samples:
                    parse_failures.extend(result["parse_failures"])
            else:
                parse_failures.extend(result["parse_failures"])
                if args.no_synthetic_fallback:
                    persona = PERSONAS[persona_index]
                    raise RuntimeError(
                        f"Only {len(result['scores'])}/{args.samples} live scores for "
                        f"profile={profile_index} player={player_index} persona={persona.key}"
                    )
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = [
                executor.submit(score_live_cell, profile_index, player_index, persona_index, profile, cache_key, args.samples, args.judge_model, cached_entry)
                for profile_index, player_index, persona_index, profile, cache_key, cached_entry in pending_tasks
            ]
            for future in as_completed(futures):
                result = future.result()
                if result["scores"]:
                    apply_live_cell_result(result, reward_tensor, cache_path, cache)
                    new_live_cells += 1
                    if args.save_every > 0 and new_live_cells % args.save_every == 0:
                        save_current_calibration(base, reward_tensor, args.backend, args.out, args.trap, args.judge_model)
                    if len(result["scores"]) < args.samples:
                        parse_failures.extend(result["parse_failures"])
                else:
                    parse_failures.extend(result["parse_failures"])
                    if args.no_synthetic_fallback:
                        raise RuntimeError(
                            f"Only {len(result['scores'])}/{args.samples} live scores for "
                            f"profile={result['profile_index']} player={result['player_index']} persona={result['persona']}"
                        )

    save_current_calibration(base, reward_tensor, args.backend, args.out, args.trap, args.judge_model)
    report = {
        "backend": args.backend,
        "out": args.out,
        "base_calibration": args.base_calibration,
        "cache": str(cache_path),
        "n": args.n,
        "samples": args.samples,
        "profile_count": int(len(base.action_profiles)),
        "live_profile_count": int(len(live_profile_indices)),
        "new_live_cells": new_live_cells,
        "cached_cells_loaded": cached_cells,
        "skipped_cached_cells": skipped_cached_cells,
        "partial_cached_cells_rescored": partial_cached_cells,
        "total_cells": int(np.prod(reward_tensor.shape)),
        "parse_failure_count": len(parse_failures),
        "parse_failures": parse_failures[:50],
        "workers": args.workers,
        "trap": bool(args.trap),
        "judge_model": args.judge_model or "",
        "tid_min_gap": tid_min_gap(reward_tensor),
    }
    report_path = Path(args.report) if args.report else Path(args.out).with_suffix(".report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "parse_failures"}, indent=2))


def select_profiles(profile_count: int, max_profiles: int) -> np.ndarray:
    if max_profiles <= 0 or max_profiles >= profile_count:
        return np.arange(profile_count, dtype=int)
    return np.unique(np.linspace(0, profile_count - 1, max_profiles, dtype=int))


def parse_profile_indices(raw: str | None, profile_count: int) -> np.ndarray | None:
    if not raw:
        return None
    indices = np.array([int(value.strip()) for value in raw.split(",") if value.strip()], dtype=int)
    if np.any(indices < 0) or np.any(indices >= profile_count):
        raise ValueError(f"Profile indices must be in [0, {profile_count - 1}]: {indices.tolist()}")
    return np.unique(indices)


def score_live_cell(
    profile_index: int,
    player_index: int,
    persona_index: int,
    profile: np.ndarray,
    cache_key: str,
    samples: int,
    judge_model: str | None,
    cached_entry: dict[str, object] | None = None,
) -> dict[str, object]:
    persona = PERSONAS[persona_index]
    scores = cached_score_values(cached_entry)[:samples]
    replies = cached_reply_values(cached_entry)
    parse_failures: list[dict[str, object]] = []
    for sample_index in range(len(scores), samples):
        prompt = build_judge_message(persona_index, player_index, profile, sample_index)
        try:
            reply = call_judge(judge_system_prompt(), prompt, model=judge_model, max_tokens=64, temperature=0.0)
            replies.append(reply)
            scores.append(parse_score(reply))
        except Exception as exc:
            parse_failures.append(
                {
                    "profile_index": int(profile_index),
                    "player_index": int(player_index),
                    "persona": persona.key,
                    "sample_index": int(sample_index),
                    "error": str(exc),
                    "reply": replies[-1] if replies else "",
                }
            )
    score = float(np.clip(np.mean(scores), 0.0, 1.0)) if scores else None
    return {
        "key": cache_key,
        "profile_index": int(profile_index),
        "player_index": int(player_index),
        "persona_index": int(persona_index),
        "persona": persona.key,
        "samples": int(samples),
        "scores": scores,
        "score": score,
        "replies": replies,
        "parse_failures": parse_failures,
    }


def apply_live_cell_result(result: dict[str, object], reward_tensor: np.ndarray, cache_path: Path, cache: dict[str, dict[str, object]]) -> None:
    score = float(result["score"])
    player_index = int(result["player_index"])
    persona_index = int(result["persona_index"])
    profile_index = int(result["profile_index"])
    reward_tensor[player_index, persona_index, profile_index] = score
    entry = {
        "key": result["key"],
        "profile_index": profile_index,
        "player_index": player_index,
        "persona_index": persona_index,
        "persona": result["persona"],
        "samples": result["samples"],
        "scores": result["scores"],
        "score": score,
        "replies": result["replies"],
    }
    append_cache(cache_path, entry)
    cache[str(result["key"])] = entry


def load_base_reward_tensor(base_calibration: str | None, synthetic_base: CalibrationBundle) -> np.ndarray:
    if not base_calibration:
        return np.array(synthetic_base.reward_tensor, copy=True)
    calibration = load_calibration(base_calibration)
    reward_tensor = np.asarray(calibration["reward_tensor"], dtype=float)
    if reward_tensor.shape != synthetic_base.reward_tensor.shape:
        raise ValueError(f"Base calibration shape {reward_tensor.shape} does not match expected {synthetic_base.reward_tensor.shape}")
    return np.array(reward_tensor, copy=True)


def save_current_calibration(base: CalibrationBundle, reward_tensor: np.ndarray, backend: str, out: str, trap: bool, judge_model: str | None) -> None:
    bundle = CalibrationBundle(
        reward_tensor=reward_tensor,
        action_profiles=base.action_profiles,
        persona_keys=base.persona_keys,
        actions=base.actions,
        n=base.n,
        backend=f"{backend}_live",
        trap=trap,
    )
    payload = bundle.to_dict()
    payload["judge_model"] = judge_model or ""
    payload["player_model"] = judge_model or ""
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    np.save(out, payload, allow_pickle=True)


def make_cache_key(profile_index: int, player_index: int, persona_index: int, samples: int) -> str:
    return f"p{profile_index}:a{player_index}:t{persona_index}:s{samples}"


def cache_entry_complete(entry: dict[str, object], samples: int) -> bool:
    return len(cached_score_values(entry)) >= samples


def cached_score_values(entry: dict[str, object] | None) -> list[float]:
    if entry is None:
        return []
    scores = entry.get("scores", [])
    if not isinstance(scores, list):
        return []
    values: list[float] = []
    for score in scores:
        try:
            values.append(float(score))
        except (TypeError, ValueError):
            continue
    return values


def cached_reply_values(entry: dict[str, object] | None) -> list[str]:
    if entry is None:
        return []
    replies = entry.get("replies", [])
    if not isinstance(replies, list):
        return []
    return [str(reply) for reply in replies]


def load_cache(path: Path) -> dict[str, dict[str, object]]:
    if not path.exists():
        return {}
    cache: dict[str, dict[str, object]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
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


def build_judge_message(persona_index: int, player_index: int, profile: np.ndarray, sample_index: int) -> str:
    persona = PERSONAS[persona_index]
    own = float(profile[player_index])
    group_mean = float(np.mean(profile))
    others = [float(value) for idx, value in enumerate(profile) if idx != player_index]
    return (
        "You are scoring exactly one HP-SPGG outcome. "
        "Your entire response must be one valid JSON object and nothing else. "
        "No explanation, no markdown, no prose. Use exactly this schema: {\"score\": 0.73}.\n"
        f"Persona key: {persona.key}\n"
        f"Persona description: {persona.description}\n"
        f"Player index: {player_index}\n"
        f"Player contribution: {own:.2f}\n"
        f"Other player contributions: {others}\n"
        f"Group mean contribution: {group_mean:.3f}\n"
        f"Sample index: {sample_index}\n"
        "Score satisfaction from 0.0 to 1.0 using the persona's private behavioural profile. "
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


if __name__ == "__main__":
    main()
