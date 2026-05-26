"""Produce SOTOPIA revenge_plot seed-21..100 data dumps.

Data-only script: no paper edits and no figures.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import random
import re
import statistics
import sys
import time
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("SOTOPIA_STORAGE_BACKEND", "local")

from sotopia.agents import Agents
from sotopia.envs import ParallelSotopiaEnv
from sotopia.envs.evaluators import RuleBasedTerminatedEvaluator, unweighted_aggregate_evaluate
from sotopia.messages import AgentAction, Message, Observation

from llm_hpgg.personas import PERSONAS
from llm_hpgg_sotopia.agents import (
    HPGGSotopiaAgent,
    _persona_log_likelihood_increment,
    _posterior_from_log_scores,
    oracle_one_hot_from_profile,
)
from llm_hpgg_sotopia.official_hard_data import HardCase, load_hard_cases, make_agent_profiles, make_environment_profile
from llm_hpgg_sotopia.run_sotopia_hard_official import (
    CloudGPTEpisodeEvaluator,
    _scores_to_responses,
)


MODEL_SPECS = {
    "DeepSeek-V3.2": "DeepSeek-V3.2",
    "Llama-4-Maverick": "Llama-4-Maverick-17B-128E-Instruct-FP8",
}
VARIANT_TO_BASELINE = {
    "surrogate-only": "surrogate_only",
    "naive-belief": "naive_belief",
    "PACT+": "hpsmg_plus",
}
PERSONA_KEYS = ["altruistic_builder", "conditional_cooperator", "strategic_hedger", "free_rider"]
INTERNAL_TO_SPEC_PERSONA = {"risk_averse_balancer": "strategic_hedger"}
SPEC_TO_INTERNAL_PERSONA = {"strategic_hedger": "risk_averse_balancer"}


class SeededSotopiaAgent(HPGGSotopiaAgent):
    def __init__(self, *args: Any, run_seed: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.run_seed = run_seed

    def _build_prompt(self, obs: Observation) -> str:
        payload = json.loads(super()._build_prompt(obs))
        payload["replicate_seed"] = self.run_seed
        payload["seed_tie_breaking_instruction"] = (
            "Use replicate_seed only to break ties among equally reasonable concrete utterances. "
            "Do not mention the seed."
        )
        return json.dumps(payload, indent=2)


def persona_to_spec(key: str) -> str:
    return INTERNAL_TO_SPEC_PERSONA.get(key, key)


def persona_to_internal(key: str) -> str:
    return SPEC_TO_INTERNAL_PERSONA.get(key, key)


def spec_dict_from_internal(values: dict[str, float]) -> dict[str, float]:
    return {persona_to_spec(key): float(value) for key, value in values.items() if persona_to_spec(key) in PERSONA_KEYS}


def uniform_spec() -> dict[str, float]:
    return {key: 1.0 / len(PERSONA_KEYS) for key in PERSONA_KEYS}


def likelihood_for_text(text: str) -> dict[str, float]:
    increments = _persona_log_likelihood_increment(text)
    max_inc = max(increments.values()) if increments else 0.0
    weights = {persona_to_spec(key): math.exp(value - max_inc) for key, value in increments.items()}
    total = sum(weights.values())
    if total <= 0:
        return uniform_spec()
    return {key: weights.get(key, 0.0) / total for key in PERSONA_KEYS}


def update_log_scores(log_scores: dict[str, float], text: str) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    pre = spec_dict_from_internal(_posterior_from_log_scores(log_scores))
    increments = _persona_log_likelihood_increment(text)
    for key, increment in increments.items():
        log_scores[key] += increment
    post = spec_dict_from_internal(_posterior_from_log_scores(log_scores))
    return pre, post, likelihood_for_text(text)


def clean_utterance(raw: str) -> str:
    text = str(raw).strip()
    match = re.match(r'^\s*said:\s*"(.*)"\s*$', text, flags=re.DOTALL)
    if match:
        return match.group(1)
    if text.startswith("said:"):
        return text[5:].strip().strip('"')
    return text


def true_persona_for_profile(profile: Any) -> str:
    one_hot = oracle_one_hot_from_profile(profile)
    key = max(one_hot.items(), key=lambda item: item[1])[0]
    return persona_to_spec(key)


def scenario_codename(case: HardCase, revenge_cases: list[HardCase]) -> str:
    return f"revenge_plot_{revenge_cases.index(case) + 1:03d}"


def seed_to_case(seed: int, revenge_cases: list[HardCase]) -> HardCase:
    return revenge_cases[(seed - 21) % len(revenge_cases)]


def mean_score(episode: dict[str, Any]) -> float:
    overall = episode.get("overall", {}) or {}
    vals = [overall.get("agent_1"), overall.get("agent_2")]
    nums = [float(v) for v in vals if isinstance(v, (int, float))]
    return sum(nums) / len(nums) if nums else float("nan")


async def run_one_episode(
    case: HardCase,
    seed: int,
    variant: str,
    model: str,
    evaluator_model: str,
    turns: int,
    out_file: Path,
    revenge_cases: list[HardCase],
) -> dict[str, Any]:
    baseline = VARIANT_TO_BASELINE[variant]
    env_profile = make_environment_profile(case)
    agent_profiles = make_agent_profiles(case)
    env = ParallelSotopiaEnv(
        env_profile=env_profile,
        action_order="round-robin",
        evaluators=[RuleBasedTerminatedEvaluator(max_turn_number=turns, max_stale_turn=2)],
    )
    agent_map = {
        "agent_1": SeededSotopiaAgent(
            "agent_1",
            baseline=baseline,
            model=model,
            agent_profile=agent_profiles[0],
            strategy_profile="sotopia_tuned",
            run_seed=seed,
        ),
        "agent_2": SeededSotopiaAgent(
            "agent_2",
            baseline=baseline,
            model=model,
            agent_profile=agent_profiles[1],
            strategy_profile="sotopia_tuned",
            run_seed=seed,
        ),
    }
    agents = Agents(agent_map)
    observations = env.reset(agents=agents, include_background_observations=True)
    for index, agent_name in enumerate(env.agents):
        agents[agent_name].goal = env_profile.agent_goals[index]

    internal_personas = [persona.key for persona in PERSONAS]
    log_scores = {
        "agent_1": {key: math.log(1.0 / len(internal_personas)) for key in internal_personas},
        "agent_2": {key: math.log(1.0 / len(internal_personas)) for key in internal_personas},
    }
    true_personas = {
        "agent_1": true_persona_for_profile(agent_profiles[0]),
        "agent_2": true_persona_for_profile(agent_profiles[1]),
    }
    transcript: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    terminated = {agent_name: False for agent_name in env.agents}
    while not all(terminated.values()):
        actions: dict[str, AgentAction] = {}
        turn_idx = len(transcript) + 1
        for agent_name in env.agents:
            actions[agent_name] = await agents[agent_name].aact(observations[agent_name])
        action_text = {agent_name: actions[agent_name].to_natural_language() for agent_name in env.agents}
        transcript.append({"turn": len(transcript), "actions": action_text})
        for agent_name in env.agents:
            utterance = clean_utterance(action_text[agent_name])
            if variant == "PACT+":
                posterior_pre, posterior_post, likelihood = update_log_scores(log_scores[agent_name], utterance)
            elif variant == "surrogate-only":
                posterior_pre = uniform_spec()
                posterior_post = uniform_spec()
                likelihood = likelihood_for_text(utterance)
            else:
                posterior_pre = None
                posterior_post = None
                likelihood = likelihood_for_text(utterance)
            rows.append(
                {
                    "seed": seed,
                    "scenario_codename": scenario_codename(case, revenge_cases),
                    "turn_idx": turn_idx,
                    "agent_idx": 1 if agent_name == "agent_1" else 2,
                    "true_persona": true_personas[agent_name],
                    "utterance_text": utterance,
                    "posterior_pre": posterior_pre,
                    "posterior_post": posterior_post,
                    "likelihood": likelihood,
                    "token_logprobs": None,
                }
            )
        observations, _, terminated, _, _ = await env.astep(actions)

    evaluator = CloudGPTEpisodeEvaluator(evaluator_model)
    scores = await evaluator.evaluate(env.turn_number, env.inbox, case)
    response = unweighted_aggregate_evaluate(_scores_to_responses(scores))
    episode = {
        "seed": seed,
        "combo_pk": case.combo_pk,
        "codename": case.codename,
        "scenario_codename": scenario_codename(case, revenge_cases),
        "variant": variant,
        "baseline": baseline,
        "model": model,
        "evaluator_model": evaluator_model,
        "turns_completed": len(transcript),
        "transcript": transcript,
        "scores": scores,
        "overall": {
            "agent_1": response.p1_rate[0] if response.p1_rate else None,
            "agent_2": response.p2_rate[0] if response.p2_rate else None,
        },
    }
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return episode


def load_episode_score(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


async def produce(args: argparse.Namespace) -> dict[str, Any]:
    start = time.time()
    random.seed(args.seed)
    cases = load_hard_cases(Path(args.benchmark_agents), Path(args.episodes_jsonl), Path(args.cache))
    revenge_cases = [case for case in cases if case.codename == "revenge_plot"]
    if len(revenge_cases) != 5:
        raise RuntimeError(f"Expected 5 local revenge_plot cases, found {len(revenge_cases)}")
    out_root = Path(args.out_root)
    score_dir = out_root / "_scores"
    score_dir.mkdir(parents=True, exist_ok=True)
    tasks: list[tuple[str, str, int]] = []
    for backbone in args.backbones:
        for variant in args.variants:
            for seed in range(args.seed_start, args.seed_end + 1):
                tasks.append((backbone, variant, seed))

    semaphore = asyncio.Semaphore(args.concurrency)
    stats = defaultdict(int)

    async def run_task(backbone: str, variant: str, seed: int) -> None:
        model = MODEL_SPECS[backbone]
        case = seed_to_case(seed, revenge_cases)
        variant_dir = out_root / backbone / variant
        out_file = variant_dir / f"seed_{seed:03d}.jsonl"
        score_file = score_dir / backbone / variant / f"seed_{seed:03d}.json"
        if out_file.exists() and load_episode_score(score_file):
            stats["skip"] += 1
            return
        async with semaphore:
            while True:
                try:
                    episode = await run_one_episode(case, seed, variant, model, model, args.turns, out_file, revenge_cases)
                    score_file.parent.mkdir(parents=True, exist_ok=True)
                    score_file.write_text(json.dumps(episode, indent=2, ensure_ascii=False), encoding="utf-8")
                    stats["ok"] += 1
                    print(f"ok {backbone} {variant} seed={seed} score={mean_score(episode):.3f}", flush=True)
                    return
                except Exception as exc:
                    stats["error"] += 1
                    print(f"retry {backbone} {variant} seed={seed}: {exc}", flush=True)
                    await asyncio.sleep(args.retry_sleep)

    coros = [run_task(*task) for task in tasks]
    for index, coro in enumerate(asyncio.as_completed(coros), start=1):
        await coro
        if index % max(1, args.status_every) == 0:
            print(f"progress {index}/{len(tasks)} {dict(stats)}", flush=True)

    summary = build_summary(out_root, args, elapsed_hours=(time.time() - start) / 3600.0)
    (out_root / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_readme(out_root, summary)
    package(out_root, Path(args.zip_out))
    return summary


def values_for(out_root: Path, backbone: str, variant: str) -> dict[int, float]:
    out: dict[int, float] = {}
    for path in sorted((out_root / "_scores" / backbone / variant).glob("seed_*.json")):
        ep = json.loads(path.read_text(encoding="utf-8"))
        out[int(ep["seed"])] = mean_score(ep)
    return out


def mean_sem_ci(values: list[float]) -> dict[str, float | int]:
    n = len(values)
    mean = statistics.fmean(values) if values else float("nan")
    sem = statistics.stdev(values) / math.sqrt(n) if n > 1 else 0.0
    return {"mean": mean, "sem": sem, "ci95_low": mean - 1.96 * sem, "ci95_high": mean + 1.96 * sem, "n": n}


def percentile(xs: list[float], q: float) -> float:
    if not xs:
        return float("nan")
    ordered = sorted(xs)
    pos = (len(ordered) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] * (hi - pos) + ordered[hi] * (pos - lo)


def paired_bootstrap_diff(a: dict[int, float], b: dict[int, float], reps: int = 1000, seed: int = 13) -> dict[str, float]:
    common = sorted(set(a) & set(b))
    diffs = [a[item] - b[item] for item in common]
    rng = random.Random(seed)
    boot = [statistics.fmean(rng.choice(diffs) for _ in diffs) for _ in range(reps)] if diffs else []
    diff = statistics.fmean(diffs) if diffs else float("nan")
    return {"diff": diff, "ci95_low": percentile(boot, 0.025), "ci95_high": percentile(boot, 0.975)}


def welch_p(a: list[float], b: list[float]) -> float:
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    ma, mb = statistics.fmean(a), statistics.fmean(b)
    va, vb = statistics.variance(a), statistics.variance(b)
    denom = math.sqrt(va / len(a) + vb / len(b))
    if denom == 0:
        return 1.0 if ma == mb else 0.0
    t = abs((ma - mb) / denom)
    try:
        from scipy import stats  # type: ignore

        return float(2 * stats.t.sf(t, stats.ttest_ind(a, b, equal_var=False).df))
    except Exception:
        return float(math.erfc(t / math.sqrt(2)))


def build_summary(out_root: Path, args: argparse.Namespace, elapsed_hours: float) -> dict[str, Any]:
    cells: dict[str, Any] = {}
    contrasts: dict[str, Any] = {}
    pooled_pact: dict[int, list[float]] = defaultdict(list)
    pooled_naive: dict[int, list[float]] = defaultdict(list)
    for backbone in args.backbones:
        cells[backbone] = {}
        per_variant = {variant: values_for(out_root, backbone, variant) for variant in args.variants}
        for variant, by_seed in per_variant.items():
            cells[backbone][variant] = mean_sem_ci(list(by_seed.values()))
        if "PACT+" not in per_variant or "naive-belief" not in per_variant:
            continue
        pact = per_variant["PACT+"]
        naive = per_variant["naive-belief"]
        contrast = paired_bootstrap_diff(pact, naive, reps=args.bootstrap_reps, seed=args.seed)
        contrast["welch_p"] = welch_p(list(pact.values()), list(naive.values()))
        contrasts[backbone] = {"PACT+_minus_naive": contrast}
        for seed, value in pact.items():
            pooled_pact[seed].append(value)
        for seed, value in naive.items():
            pooled_naive[seed].append(value)
    pooled_pact_mean = {seed: statistics.fmean(values) for seed, values in pooled_pact.items() if values}
    pooled_naive_mean = {seed: statistics.fmean(values) for seed, values in pooled_naive.items() if values}
    contrasts["pooled"] = {"PACT+_minus_naive": paired_bootstrap_diff(pooled_pact_mean, pooled_naive_mean, reps=args.bootstrap_reps, seed=args.seed)}
    pooled = contrasts["pooled"]["PACT+_minus_naive"]
    acceptance_failed = bool(math.isfinite(pooled["diff"]) and (pooled["diff"] < 0.05 or pooled["ci95_low"] <= 0 <= pooled["ci95_high"]))
    weakened_effect = bool(math.isfinite(pooled["diff"]) and not acceptance_failed and pooled["diff"] < 0.10)
    summary: dict[str, Any] = {
        "n_per_cell": 100,
        "n_new_per_cell": args.seed_end - args.seed_start + 1,
        "seed_scheme": "Seeds 21..100 are repeated rollouts over the five local revenge_plot cases, case=(seed-21) mod 5.",
        "cells": cells,
        "contrasts": contrasts,
        "compute": {
            "new_tokens_used": 0,
            "new_tokens_used_note": "Provider token usage was not exposed by the project CloudGPT wrapper; value is unavailable and set to 0.",
            "wall_clock_hours": elapsed_hours,
        },
        "token_logprobs_top_k": None,
        "token_logprobs_note": "CloudGPT chat wrapper in this repository does not expose token logprobs; token_logprobs is null in dumps.",
        "acceptance_failed": acceptance_failed,
    }
    if weakened_effect:
        summary["weakened_effect"] = True
    return summary


def write_readme(out_root: Path, summary: dict[str, Any]) -> None:
    text = (
        "SOTOPIA revenge_plot n=100 data package. Deviations: the local SOTOPIA-Hard cache has five "
        "revenge_plot cases rather than explicit seed-indexed cases, so seeds 21..100 are implemented as "
        "80 repeated rollouts over those five cases with case=(seed-21) mod 5; existing seeds 1..20 were not "
        "re-run and are expected to be merged downstream. The summary statistics in this package are computed "
        "from the new seed 21..100 files only while retaining n_per_cell=100 as the target scale. Token-level "
        "logprobs top-K: unavailable/null because the repository CloudGPT wrapper does not expose logprobs. "
        "API-error re-runs are handled by automatic retry; see terminal logs for retry counts.\n"
    )
    (out_root / "README.txt").write_text(text, encoding="utf-8")


def package(out_root: Path, zip_out: Path) -> None:
    zip_out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(out_root.resolve().rglob("*")):
            if path.is_file() and "_scores" not in path.parts:
                zf.write(path, path.relative_to(ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", default="results_phase2/sotopia_revenge_n100")
    parser.add_argument("--zip-out", default="results_phase2/sotopia_revenge_n100_package.zip")
    parser.add_argument("--seed-start", type=int, default=21)
    parser.add_argument("--seed-end", type=int, default=100)
    parser.add_argument("--turns", type=int, default=6)
    parser.add_argument("--concurrency", type=int, default=3)
    parser.add_argument("--retry-sleep", type=float, default=5.0)
    parser.add_argument("--status-every", type=int, default=10)
    parser.add_argument("--bootstrap-reps", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--backbones", nargs="+", default=["DeepSeek-V3.2", "Llama-4-Maverick"], choices=list(MODEL_SPECS))
    parser.add_argument("--variants", nargs="+", default=["surrogate-only", "naive-belief", "PACT+"], choices=list(VARIANT_TO_BASELINE))
    parser.add_argument("--benchmark-agents", default="_archive/external/sotopia_data_probe/benchmark_agents.json")
    parser.add_argument("--episodes-jsonl", default="_archive/external/sotopia_data_probe/sotopia_episodes_v1_hf.jsonl")
    parser.add_argument("--cache", default="_archive/external/sotopia_data_probe/sotopia_hard_cases_cache.json")
    args = parser.parse_args()
    summary = asyncio.run(produce(args))
    print(json.dumps({"summary": Path(args.out_root) / "summary.json", "pooled": summary["contrasts"]["pooled"]}, indent=2, default=str))


if __name__ == "__main__":
    main()