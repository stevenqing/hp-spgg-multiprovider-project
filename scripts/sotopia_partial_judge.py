"""Re-judge SOTOPIA-Hard episodes on truncated (partial) transcripts.

For each episode in the three in-scope families (craigslist_bargains,
revenge_plot, donate_funds), re-runs the same SOTOPIA evaluator on the
transcript truncated to the first ``k`` turns, for ``k`` in --k-points (default
``2 4``). The full-episode score at ``k=6`` is already in the source JSON, so
we only need the partial points.

Outputs a resumable cache JSON keyed by ``(combo_pk, baseline, backbone, k)``
at ``analysis/sotopia_partial_judge_cache.json``. Concurrency is bounded by
``--concurrency`` (default 8). Use ``--smoke`` to run only 2 episodes per
(backbone, baseline, family) at the first k-point to check the pipeline.

Usage:
  uv run python scripts/sotopia_partial_judge.py --smoke
  uv run python scripts/sotopia_partial_judge.py --k-points 2 4 --per-family 20
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Three in-scope SOTOPIA-Hard families (the ones in the main Fig. 5 panel).
FAMILIES = {"craigslist_bargains", "revenge_plot", "donate_funds"}

# Map (file backbone token) -> CloudGPT model name used as both player and judge.
BACKBONE_MODEL = {
    "DeepSeek_V3_2": "DeepSeek-V3.2",
    "gpt_5_4_nano_20260317": "gpt-5.4-nano-20260317",
    "Kimi_K2_6": "Kimi-K2.6",
    "Llama_4_Maverick_17B_128E_Instruct_FP8": "Llama-4-Maverick-17B-128E-Instruct-FP8",
}

# SOTOPIA evaluator dimension ranges (mirrors run_sotopia_hard_official.DIMENSIONS).
DIMENSIONS = {
    "believability": (0, 10),
    "relationship": (-5, 5),
    "knowledge": (0, 10),
    "secret": (-10, 0),
    "social_rules": (-10, 0),
    "financial_and_material_benefits": (-5, 5),
    "goal": (0, 10),
}

RESULT_FILE_RE = re.compile(
    r"^sotopia_hard_official_(?P<bb>" + "|".join(map(re.escape, BACKBONE_MODEL)) + r")_(?P<baseline>[a-z0-9_]+)_sotopia_tuned_all70\.json$"
)

CACHE_PATH = ROOT / "analysis" / "sotopia_partial_judge_cache.json"
CASE_CACHE_PATH = ROOT / "external" / "sotopia_data_probe" / "sotopia_hard_cases_cache.json"


def load_case_index() -> dict[str, dict[str, Any]]:
    cases = json.loads(CASE_CACHE_PATH.read_text(encoding="utf-8"))
    return {case["combo_pk"]: case for case in cases}


def family_of(codename: str) -> str:
    parts = codename.split("_")
    while parts and parts[-1].isdigit():
        parts.pop()
    return "_".join(parts)


def truncate_transcript(transcript: list[dict[str, Any]], k: int) -> list[tuple[str, str]]:
    """Return list of (speaker_label, utterance) for the first k turns,
    omitting 'did nothing' actions (matches the live evaluator's _history_text)."""
    out: list[tuple[str, str]] = []
    for turn in transcript[:k]:
        actions = turn.get("actions", {})
        for agent_key, text in actions.items():
            text = str(text)
            if "did nothing" in text:
                continue
            out.append((agent_key, text))
    return out


def history_text(history: list[tuple[str, str]], case: dict[str, Any]) -> str:
    name_map = {
        "agent_1": case["agent_names"][0],
        "agent_2": case["agent_names"][1],
    }
    lines = []
    for speaker, msg in history:
        name = name_map.get(speaker, speaker)
        # Strip leading ' said: "..."' format from the existing transcript text so the judge sees natural lines.
        clean = msg.strip()
        m = re.match(r"^\s*said:\s*\"(.*)\"\s*$", clean)
        if m:
            clean = m.group(1)
        lines.append(f"{name}: {clean}")
    return "\n".join(lines)


def build_prompt(history: str, case: dict[str, Any]) -> str:
    return json.dumps(
        {
            "task": "Evaluate a SOTOPIA interaction using the official SOTOPIA dimensions.",
            "scenario": case["scenario"],
            "agents": [
                {"label": "agent_1", "name": case["agent_names"][0], "goal": case["agent_goals"][0]},
                {"label": "agent_2", "name": case["agent_names"][1], "goal": case["agent_goals"][1]},
            ],
            "history": history,
            "dimension_score_ranges": DIMENSIONS,
            "response_schema": {
                "agent_1": {name: {"score": "number in range", "reasoning": "brief"} for name in DIMENSIONS},
                "agent_2": {name: {"score": "number in range", "reasoning": "brief"} for name in DIMENSIONS},
            },
            "instruction": "Return valid JSON only. Score each dimension for both agents.",
        },
        indent=2,
    )


def extract_json(text: str) -> str:
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        raise ValueError(f"No JSON object in evaluator reply: {text[:200]}")
    return m.group(0)


def normalise_scores(raw: dict[str, Any]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for agent_key in ("agent_1", "agent_2"):
        ag = raw.get(agent_key, {}) or {}
        out[agent_key] = {}
        for dim, (lo, hi) in DIMENSIONS.items():
            item = ag.get(dim, {})
            score = item.get("score", 0) if isinstance(item, dict) else item
            try:
                v = float(score)
            except (TypeError, ValueError):
                v = 0.0
            out[agent_key][dim] = max(lo, min(hi, v))
    return out


def overall_focal(scores: dict[str, dict[str, float]]) -> dict[str, float]:
    """Mirror SOTOPIA's unweighted_aggregate_evaluate aggregation: mean over all
    seven dimensions per agent. The original code multiplies each dimension by
    weight 1 / 7 in unweighted_aggregate; equivalently we take the arithmetic
    mean over DIMENSIONS for each agent."""
    out = {}
    for ag in ("agent_1", "agent_2"):
        vals = [scores[ag][d] for d in DIMENSIONS]
        out[ag] = sum(vals) / len(vals) if vals else 0.0
    return out


async def call_judge_async(system_prompt: str, user_prompt: str, model: str, semaphore: asyncio.Semaphore, max_tokens: int = 1800) -> str:
    from llm_hpgg.llm_agent_cloudgpt import _call_llm  # type: ignore
    async with semaphore:
        return await asyncio.to_thread(_call_llm, system_prompt, user_prompt, model, max_tokens, 0.0)


def load_cache() -> dict[str, Any]:
    if CACHE_PATH.exists():
        data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        # Drop previously-failed entries so they're retried this run.
        data["entries"] = {k: v for k, v in data.get("entries", {}).items() if "error" not in v}
        return data
    return {"entries": {}}


def save_cache(cache: dict[str, Any]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=1), encoding="utf-8")


def cache_key(combo_pk: str, baseline: str, backbone: str, k: int) -> str:
    return f"{backbone}|{baseline}|{combo_pk}|k{k}"


def enumerate_tasks(args: argparse.Namespace, case_index: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rng = random.Random(args.seed)
    tasks: list[dict[str, Any]] = []
    for path in sorted((ROOT / "analysis").glob("sotopia_hard_official_*_sotopia_tuned_all70.json")):
        m = RESULT_FILE_RE.match(path.name)
        if not m:
            continue
        backbone = m["bb"]
        baseline = m["baseline"]
        data = json.loads(path.read_text(encoding="utf-8"))
        # Bucket episodes by family.
        by_fam: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for ep in data.get("episodes", []):
            fam = family_of(ep.get("codename", ""))
            if fam in FAMILIES:
                by_fam[fam].append(ep)
        for fam, eps in by_fam.items():
            if args.per_family and len(eps) > args.per_family:
                # Deterministic subsample for reproducibility across backbones/baselines.
                eps_sorted = sorted(eps, key=lambda e: e["combo_pk"])
                step = max(1, len(eps_sorted) // args.per_family)
                eps = eps_sorted[::step][: args.per_family]
            for ep in eps:
                case = case_index.get(ep["combo_pk"])
                if case is None:
                    continue
                for k in args.k_points:
                    tasks.append({
                        "backbone": backbone,
                        "baseline": baseline,
                        "family": fam,
                        "combo_pk": ep["combo_pk"],
                        "codename": ep.get("codename"),
                        "k": k,
                        "transcript": ep.get("transcript", []),
                        "case": case,
                    })
    if args.smoke:
        # Keep only first 2 episodes per (backbone, baseline, family) at first k.
        seen: dict[tuple[str, str, str], int] = defaultdict(int)
        kept: list[dict[str, Any]] = []
        first_k = args.k_points[0]
        for t in tasks:
            if t["k"] != first_k:
                continue
            key = (t["backbone"], t["baseline"], t["family"])
            if seen[key] >= 2:
                continue
            seen[key] += 1
            kept.append(t)
        tasks = kept
    rng.shuffle(tasks)  # interleave backbones so failures are visible early
    return tasks


async def run_one(task: dict[str, Any], cache: dict[str, Any], semaphore: asyncio.Semaphore, stats: dict[str, int]) -> None:
    key = cache_key(task["combo_pk"], task["baseline"], task["backbone"], task["k"])
    if key in cache["entries"]:
        stats["skipped"] += 1
        return
    model = BACKBONE_MODEL[task["backbone"]]
    history = history_text(truncate_transcript(task["transcript"], task["k"]), task["case"])
    if not history.strip():
        # No utterance reached this checkpoint (e.g., k=1 with agent_2-first round); record empty.
        cache["entries"][key] = {"overall": {"agent_1": 0.0, "agent_2": 0.0}, "empty": True}
        stats["empty"] += 1
        return
    user_prompt = build_prompt(history, task["case"])
    try:
        reply = await call_judge_async(
            "You are a careful SOTOPIA evaluator. Return valid JSON only.",
            user_prompt,
            model,
            semaphore,
        )
        scores = normalise_scores(json.loads(extract_json(reply)))
        overall = overall_focal(scores)
        cache["entries"][key] = {
            "scores": scores,
            "overall": overall,
            "family": task["family"],
            "codename": task["codename"],
        }
        stats["ok"] += 1
    except Exception as exc:  # pragma: no cover
        cache["entries"][key] = {"error": str(exc)[:300]}
        stats["error"] += 1


async def main_async(args: argparse.Namespace) -> None:
    os.environ.setdefault("LLM_HPGG_BACKEND", "cloudgpt")
    case_index = load_case_index()
    tasks = enumerate_tasks(args, case_index)
    print(f"queued {len(tasks)} judge calls ({len(args.k_points)} k-points)")
    if args.dry_run:
        for t in tasks[:8]:
            print(f"  {t['backbone']:42s} {t['baseline']:12s} {t['family']:22s} {t['codename']} k={t['k']}")
        print(f"  ... ({len(tasks)} total)")
        return
    cache = load_cache()
    semaphore = asyncio.Semaphore(args.concurrency)
    stats = defaultdict(int)
    save_every = max(20, args.concurrency * 4)

    coros = [run_one(t, cache, semaphore, stats) for t in tasks]
    pending = list(coros)
    completed = 0
    t0 = time.time()
    for coro in asyncio.as_completed(pending):
        await coro
        completed += 1
        if completed % save_every == 0:
            save_cache(cache)
            elapsed = time.time() - t0
            rate = completed / max(elapsed, 1e-9)
            print(f"  [{completed:5d}/{len(tasks):5d}]  ok={stats['ok']:5d} skip={stats['skipped']:5d} empty={stats['empty']:3d} err={stats['error']:3d}  ({rate:.2f} call/s)")
    save_cache(cache)
    print(f"done. ok={stats['ok']} skipped={stats['skipped']} empty={stats['empty']} error={stats['error']}")
    print(f"cache: {CACHE_PATH}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--k-points", nargs="+", type=int, default=[2, 4])
    p.add_argument("--per-family", type=int, default=20,
                   help="Episodes per (backbone, baseline, family); 0 = use all.")
    p.add_argument("--concurrency", type=int, default=8)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--smoke", action="store_true", help="2 episodes per cell, first k only.")
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    asyncio.run(main_async(parse_args()))
