"""Re-judge SOTOPIA intent-ablation transcripts at turn checkpoints k=1..5.

The full k=6 score is already stored in each experiment JSON. This script
creates a resumable partial-judge cache and a compact trajectory summary for
the six intent-ablation cells.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DIMENSIONS = {
    "believability": (0, 10),
    "relationship": (-5, 5),
    "knowledge": (0, 10),
    "secret": (-10, 0),
    "social_rules": (-10, 0),
    "financial_and_material_benefits": (-5, 5),
    "goal": (0, 10),
}

FAMILY_ALIASES = {
    "craigslist_bargains_00000": "craigslist_bargains",
    "revenge_plot": "revenge_plot",
    "sell_item": "sell_item",
}


def family_of(codename: str) -> str:
    return FAMILY_ALIASES.get(codename, re.sub(r"_\d+$", "", codename))


def load_cases(path: Path) -> dict[str, dict[str, Any]]:
    return {case["combo_pk"]: case for case in json.loads(path.read_text(encoding="utf-8"))}


def history_text(transcript: list[dict[str, Any]], k: int, case: dict[str, Any]) -> str:
    name_map = {
        "agent_1": case["agent_names"][0],
        "agent_2": case["agent_names"][1],
    }
    lines: list[str] = []
    for turn in transcript[:k]:
        for speaker, msg in (turn.get("actions", {}) or {}).items():
            msg = str(msg)
            if "did nothing" in msg:
                continue
            clean = msg.strip()
            match = re.match(r'^\s*said:\s*"(.*)"\s*$', clean)
            if match:
                clean = match.group(1)
            lines.append(f"{name_map.get(speaker, speaker)}: {clean}")
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
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object in evaluator reply: {text[:200]}")
    return match.group(0)


def normalise_scores(raw: dict[str, Any]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for agent_key in ("agent_1", "agent_2"):
        agent_scores = raw.get(agent_key, {}) or {}
        out[agent_key] = {}
        for dim, (lo, hi) in DIMENSIONS.items():
            item = agent_scores.get(dim, {})
            score = item.get("score", 0) if isinstance(item, dict) else item
            try:
                value = float(score)
            except (TypeError, ValueError):
                value = 0.0
            out[agent_key][dim] = max(lo, min(hi, value))
    return out


def overall(scores: dict[str, dict[str, float]]) -> dict[str, float]:
    return {agent: sum(scores[agent][dim] for dim in DIMENSIONS) / len(DIMENSIONS) for agent in ("agent_1", "agent_2")}


async def call_judge(system_prompt: str, user_prompt: str, model: str, semaphore: asyncio.Semaphore) -> str:
    from llm_hpgg.llm_agent import call_judge as provider_call_judge

    async with semaphore:
        return await asyncio.to_thread(provider_call_judge, system_prompt, user_prompt, model, 1800, 0.0)


def cache_key(source: Path, episode: dict[str, Any], k: int) -> str:
    return f"{source.stem}|{episode['combo_pk']}|k{k}"


async def run_one(task: dict[str, Any], cache: dict[str, Any], case_index: dict[str, dict[str, Any]], semaphore: asyncio.Semaphore) -> str:
    source: Path = task["source"]
    episode = task["episode"]
    k = task["k"]
    key = cache_key(source, episode, k)
    if key in cache["entries"] and "error" not in cache["entries"][key]:
        return "skip"
    case = case_index[episode["combo_pk"]]
    hist = history_text(episode.get("transcript", []), k, case)
    if not hist.strip():
        cache["entries"][key] = {
            "overall": {"agent_1": 0.0, "agent_2": 0.0},
            "family": family_of(episode.get("codename", "")),
            "empty": True,
        }
        return "empty"
    try:
        reply = await call_judge(
            "You are a careful SOTOPIA evaluator. Return valid JSON only.",
            build_prompt(hist, case),
            str(task["model"]),
            semaphore,
        )
        scores = normalise_scores(json.loads(extract_json(reply)))
        cache["entries"][key] = {
            "overall": overall(scores),
            "scores": scores,
            "family": family_of(episode.get("codename", "")),
            "codename": episode.get("codename", ""),
            "model": task["model"],
            "baseline": task["baseline"],
            "backbone": task["backbone"],
        }
        return "ok"
    except Exception as exc:
        cache["entries"][key] = {"error": str(exc)[:500]}
        return "error"


def source_metadata(path: Path, data: dict[str, Any]) -> tuple[str, str, str]:
    stem = path.stem
    backbone = "deepseek" if "_deepseek_" in stem else "llama_maverick"
    baseline = str(data.get("baseline", "unknown"))
    model = str(data.get("evaluator_model") or data.get("model") or "")
    return backbone, baseline, model


def write_summary(sources: list[Path], cache: dict[str, Any], out_prefix: Path) -> None:
    rows: list[dict[str, Any]] = []
    for source in sources:
        data = json.loads(source.read_text(encoding="utf-8"))
        backbone, baseline, _model = source_metadata(source, data)
        for episode in data.get("episodes", []):
            family = family_of(episode.get("codename", ""))
            for k in range(1, 7):
                if k == 6:
                    ov = episode.get("overall", {}) or {}
                else:
                    entry = cache["entries"].get(cache_key(source, episode, k), {})
                    ov = entry.get("overall", {}) or {}
                a1, a2 = ov.get("agent_1"), ov.get("agent_2")
                if not isinstance(a1, (int, float)) or not isinstance(a2, (int, float)):
                    continue
                rows.append(
                    {
                        "backbone": backbone,
                        "variant": baseline,
                        "family": family,
                        "k": k,
                        "combo_pk": episode.get("combo_pk", ""),
                        "focal_score": 0.5 * (float(a1) + float(a2)),
                    }
                )
    grouped: dict[tuple[str, str, str, int], list[float]] = defaultdict(list)
    for row in rows:
        grouped[(row["backbone"], row["variant"], row["family"], int(row["k"]))].append(float(row["focal_score"]))
    summary_rows = []
    for (backbone, variant, family, k), values in sorted(grouped.items()):
        arr = values
        mean = sum(arr) / len(arr)
        if len(arr) > 1:
            variance = sum((x - mean) ** 2 for x in arr) / (len(arr) - 1)
            sem = (variance ** 0.5) / (len(arr) ** 0.5)
        else:
            sem = 0.0
        summary_rows.append({"backbone": backbone, "variant": variant, "family": family, "k": k, "mean": mean, "sem": sem, "n": len(arr)})
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    with (out_prefix.with_suffix(".episodes.csv")).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader(); writer.writerows(rows)
    with (out_prefix.with_suffix(".summary.csv")).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader(); writer.writerows(summary_rows)
    out_prefix.with_suffix(".summary.json").write_text(json.dumps({"rows": summary_rows, "episodes": rows}, indent=2), encoding="utf-8")


async def main_async(args: argparse.Namespace) -> None:
    os.environ.setdefault("LLM_HPGG_BACKEND", "cloudgpt")
    sources = sorted(
        list(Path(args.results_dir).glob("sotopia_intent_*_s15.json"))
        + list(Path(args.results_dir).glob("sotopia_intent_*_donate_funds_s5.json"))
    )
    sources = [p for p in sources if not p.name.startswith("smoke") and "live_smoke" not in p.name]
    case_index = load_cases(Path(args.case_cache))
    cache_path = Path(args.cache)
    if cache_path.exists():
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
    else:
        cache = {"entries": {}}
    tasks = []
    for source in sources:
        data = json.loads(source.read_text(encoding="utf-8"))
        backbone, baseline, model = source_metadata(source, data)
        for episode in data.get("episodes", []):
            for k in args.k_points:
                tasks.append({"source": source, "episode": episode, "k": k, "backbone": backbone, "baseline": baseline, "model": model})
    print(f"queued={len(tasks)} sources={len(sources)}")
    semaphore = asyncio.Semaphore(args.concurrency)
    stats: dict[str, int] = defaultdict(int)
    for index, coro in enumerate(asyncio.as_completed([run_one(task, cache, case_index, semaphore) for task in tasks]), start=1):
        stats[await coro] += 1
        if index % max(10, args.concurrency * 3) == 0:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(cache, indent=1), encoding="utf-8")
            print(f"[{index}/{len(tasks)}] {dict(stats)}")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache, indent=1), encoding="utf-8")
    write_summary(sources, cache, Path(args.out_prefix))
    print(f"done {dict(stats)}")
    print(f"cache={cache_path}")
    print(f"summary={Path(args.out_prefix).with_suffix('.summary.csv')}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", default="analysis/sotopia_intent_ablation")
    parser.add_argument("--case-cache", default="_archive/external/sotopia_data_probe/sotopia_hard_cases_cache.json")
    parser.add_argument("--cache", default="analysis/sotopia_intent_ablation/partial_judge_cache.json")
    parser.add_argument("--out-prefix", default="analysis/sotopia_intent_ablation/trajectory")
    parser.add_argument("--k-points", nargs="+", type=int, default=[1, 2, 3, 4, 5])
    parser.add_argument("--concurrency", type=int, default=6)
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(main_async(parse_args()))