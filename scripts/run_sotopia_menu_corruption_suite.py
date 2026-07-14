"""Run the AAAI-27 E-R3 SOTOPIA intent-menu corruption suite.

The suite selects the 30 official cases in craigslist_bargains, revenge_plot,
and donate_funds; repeats each case four times for 120 episodes per corruption
level; and checkpoints every completed episode.  Each partner utterance has
probability p of receiving a non-identity random permutation of the four
surrogate score increments before the recurrent posterior update.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import re
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

os.environ.setdefault("SOTOPIA_STORAGE_BACKEND", "local")
os.environ.setdefault("LLM_HPGG_BACKEND", "cloudgpt")
os.environ.setdefault("SOTOPIA_AGENT_STRATEGY_PROFILE", "sotopia_tuned")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_hpgg_sotopia.official_hard_data import HardCase, load_hard_cases
from llm_hpgg_sotopia.run_sotopia_hard_official import run_case


OUT_DIR = ROOT / "analysis" / "aaai27_review"
RAW_DIR = OUT_DIR / "e_r3_raw"
TARGET_FAMILIES = {"craigslist_bargains", "revenge_plot", "donate_funds"}


def family_of(codename: str) -> str:
    parts = codename.split("_")
    while parts and parts[-1].isdigit():
        parts.pop()
    return "_".join(parts)


def p_slug(value: float) -> str:
    return str(value).replace(".", "p")


def raw_path(p: float, replicate: int) -> Path:
    return RAW_DIR / f"p{p_slug(p)}_r{replicate}.json"


def load_raw(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"episodes": [], "failures": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"episodes": [], "failures": []}
    return data if isinstance(data, dict) else {"episodes": [], "failures": []}


def write_raw(
    path: Path,
    *,
    p: float,
    replicate: int,
    model: str,
    evaluator_model: str,
    episodes: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    target_count: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "experiment": "AAAI27 E-R3 SOTOPIA intent-menu corruption",
        "p": p,
        "replicate": replicate,
        "model": model,
        "evaluator_model": evaluator_model,
        "target_count": target_count,
        "case_count": len(episodes),
        "complete": len(episodes) == target_count and not failures,
        "failures": failures,
        "episodes": episodes,
    }
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temp.replace(path)


async def run_cell(
    cases: list[HardCase],
    *,
    p: float,
    replicate: int,
    model: str,
    evaluator_model: str,
    turns: int,
    concurrency: int,
    base_seed: int,
    retries: int,
) -> None:
    path = raw_path(p, replicate)
    prior = load_raw(path)
    episodes = list(prior.get("episodes", []))
    failures: list[dict[str, Any]] = []
    completed = {str(episode.get("combo_pk", "")) for episode in episodes}
    pending = [case for case in cases if case.combo_pk not in completed]
    print(f"cell p={p} replicate={replicate} completed={len(episodes)} pending={len(pending)}", flush=True)
    queue: asyncio.Queue[HardCase | None] = asyncio.Queue()
    for case in pending:
        queue.put_nowait(case)
    workers = min(max(1, concurrency), max(1, len(pending)))
    for _ in range(workers):
        queue.put_nowait(None)
    lock = asyncio.Lock()

    async def worker(worker_id: int) -> None:
        while True:
            case = await queue.get()
            if case is None:
                return
            last_error = ""
            episode: dict[str, Any] | None = None
            for attempt in range(retries + 1):
                try:
                    episode = await run_case(
                        case,
                        "hpsmg_plus",
                        model,
                        evaluator_model,
                        turns,
                        1,
                        p,
                        base_seed + replicate,
                    )
                    break
                except Exception as exc:  # provider/evaluator failures are persisted
                    last_error = f"{type(exc).__name__}: {exc}"
                    print(
                        f"worker={worker_id} p={p} r={replicate} case={case.combo_pk} "
                        f"attempt={attempt + 1}/{retries + 1} error={last_error[:240]}",
                        flush=True,
                    )
                    if attempt < retries:
                        await asyncio.sleep(min(2 ** attempt, 8))
            async with lock:
                if episode is not None and case.combo_pk not in completed:
                    episode["replicate"] = replicate
                    episode["episode_id"] = f"{case.combo_pk}_r{replicate}"
                    episodes.append(episode)
                    completed.add(case.combo_pk)
                    print(
                        f"done p={p} r={replicate} {len(episodes)}/{len(cases)} "
                        f"case={case.combo_pk}",
                        flush=True,
                    )
                elif episode is None:
                    failures.append(
                        {
                            "combo_pk": case.combo_pk,
                            "codename": case.codename,
                            "error": last_error,
                        }
                    )
                write_raw(
                    path,
                    p=p,
                    replicate=replicate,
                    model=model,
                    evaluator_model=evaluator_model,
                    episodes=episodes,
                    failures=failures,
                    target_count=len(cases),
                )

    if pending:
        await asyncio.gather(*(worker(index + 1) for index in range(workers)))
    write_raw(
        path,
        p=p,
        replicate=replicate,
        model=model,
        evaluator_model=evaluator_model,
        episodes=episodes,
        failures=failures,
        target_count=len(cases),
    )


def aggregate_csv(p_values: list[float], replicates: int) -> Path:
    rows: list[dict[str, Any]] = []
    for p in p_values:
        for replicate in range(replicates):
            data = load_raw(raw_path(p, replicate))
            for episode in data.get("episodes", []):
                overall = episode.get("overall", {}) or {}
                scores = [
                    float(value)
                    for value in (overall.get("agent_1"), overall.get("agent_2"))
                    if isinstance(value, (int, float))
                ]
                audit = episode.get("menu_corruption", {}) or {}
                generation = episode.get("generation_audit", {}) or {}
                rows.append(
                    {
                        "family": family_of(str(episode.get("codename", ""))),
                        "p": p,
                        "episode_id": episode.get("episode_id", f"{episode.get('combo_pk', '')}_r{replicate}"),
                        "focal_score": sum(scores) / len(scores) if scores else "",
                        "combo_pk": episode.get("combo_pk", ""),
                        "codename": episode.get("codename", ""),
                        "replicate": replicate,
                        "turns_completed": episode.get("turns_completed", ""),
                        "corruption_updates": sum(int(item.get("updates", 0)) for item in audit.values()),
                        "corruption_events": sum(int(item.get("events", 0)) for item in audit.values()),
                        "generation_calls": sum(int(item.get("calls", 0)) for item in generation.values()),
                        "generation_failures": sum(int(item.get("failures", 0)) for item in generation.values()),
                    }
                )
    rows.sort(key=lambda row: (float(row["p"]), str(row["family"]), str(row["episode_id"])))
    path = OUT_DIR / "e_r3_menu_corruption.csv"
    if rows:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    return path


async def async_main(args: argparse.Namespace) -> None:
    cases = load_hard_cases(
        Path(args.benchmark_agents),
        Path(args.episodes_jsonl),
        Path(args.cache),
    )
    target_cases = [case for case in cases if family_of(case.codename) in TARGET_FAMILIES]
    if len(target_cases) != 30:
        raise RuntimeError(f"Expected 30 target cases, found {len(target_cases)}")
    if args.limit_cases:
        target_cases = target_cases[: args.limit_cases]
    p_values = [float(value) for value in args.p_values.split(",") if value.strip()]
    for p in p_values:
        if not 0.0 <= p <= 1.0:
            raise ValueError(f"p must be in [0,1], got {p}")
        for replicate in range(args.replicates):
            await run_cell(
                target_cases,
                p=p,
                replicate=replicate,
                model=args.model,
                evaluator_model=args.evaluator_model,
                turns=args.turns,
                concurrency=args.concurrency,
                base_seed=args.seed,
                retries=args.retries,
            )
            aggregate_csv(p_values, args.replicates)
    output = aggregate_csv(p_values, args.replicates)
    print(f"saved={output}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p-values", default="0,0.1,0.2,0.3")
    parser.add_argument("--replicates", type=int, default=4)
    parser.add_argument("--model", default="gpt-5.4-nano-20260317")
    parser.add_argument("--evaluator-model", default="gpt-5.4-nano-20260317")
    parser.add_argument("--turns", type=int, default=6)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--seed", type=int, default=2701)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--limit-cases", type=int, default=0, help="Smoke-only limit; 0 runs all 30 target cases.")
    parser.add_argument("--benchmark-agents", default="external/sotopia_data_probe/benchmark_agents.json")
    parser.add_argument("--episodes-jsonl", default="external/sotopia_data_probe/sotopia_episodes_v1_hf.jsonl")
    parser.add_argument("--cache", default="external/sotopia_data_probe/sotopia_hard_cases_cache.json")
    args = parser.parse_args()
    asyncio.run(async_main(args))


if __name__ == "__main__":
    main()
