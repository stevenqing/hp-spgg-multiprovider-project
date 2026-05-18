"""Run project agents on reconstructed official SOTOPIA-Hard cases."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
from pathlib import Path
from typing import Any

os.environ.setdefault("SOTOPIA_STORAGE_BACKEND", "local")

from sotopia.agents import Agents
from sotopia.envs import ParallelSotopiaEnv
from sotopia.envs.evaluators import RuleBasedTerminatedEvaluator, unweighted_aggregate_evaluate
from sotopia.messages import AgentAction, Message

from llm_hpgg.llm_agent import call_judge

from .agents import HPGGSotopiaAgent
from .official_hard_data import HardCase, load_hard_cases, make_agent_profiles, make_environment_profile


DIMENSIONS = {
    "believability": (0, 10),
    "relationship": (-5, 5),
    "knowledge": (0, 10),
    "secret": (-10, 0),
    "social_rules": (-10, 0),
    "financial_and_material_benefits": (-5, 5),
    "goal": (0, 10),
}


class CloudGPTEpisodeEvaluator:
    """SOTOPIA-dimension evaluator using the project's provider wrapper."""

    def __init__(self, model: str | None = None) -> None:
        self.model = model

    async def evaluate(
        self,
        turn_number: int,
        messages: list[tuple[str, Message]],
        case: HardCase,
    ) -> dict[str, Any]:
        if self.model == "offline" or os.getenv("LLM_HPGG_OFFLINE", "0") == "1":
            return _offline_scores(case)

        history = _history_text(messages)
        prompt = json.dumps(
            {
                "task": "Evaluate a SOTOPIA interaction using the official SOTOPIA dimensions.",
                "scenario": case.scenario,
                "agents": [
                    {"label": "agent_1", "name": case.agent_names[0], "goal": case.agent_goals[0]},
                    {"label": "agent_2", "name": case.agent_names[1], "goal": case.agent_goals[1]},
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
        reply = await asyncio.to_thread(
            call_judge,
            "You are a careful SOTOPIA evaluator. Return valid JSON only.",
            prompt,
            self.model,
            1800,
            0.0,
        )
        return _normalise_scores(json.loads(_extract_json(reply)), case)


async def run_case(case: HardCase, baseline: str, model: str | None, evaluator_model: str | None, turns: int) -> dict[str, Any]:
    env_profile = make_environment_profile(case)
    agent_profiles = make_agent_profiles(case)
    env = ParallelSotopiaEnv(
        env_profile=env_profile,
        action_order="round-robin",
        evaluators=[RuleBasedTerminatedEvaluator(max_turn_number=turns, max_stale_turn=2)],
    )
    agent_map = {
        "agent_1": HPGGSotopiaAgent(
            "agent_1",
            baseline=baseline,
            model=model,
            agent_profile=agent_profiles[0],
            strategy_profile=os.getenv("SOTOPIA_AGENT_STRATEGY_PROFILE", "legacy"),
        ),
        "agent_2": HPGGSotopiaAgent(
            "agent_2",
            baseline=baseline,
            model=model,
            agent_profile=agent_profiles[1],
            strategy_profile=os.getenv("SOTOPIA_AGENT_STRATEGY_PROFILE", "legacy"),
        ),
    }
    agents = Agents(agent_map)
    observations = env.reset(agents=agents, include_background_observations=True)
    for index, agent_name in enumerate(env.agents):
        agents[agent_name].goal = env_profile.agent_goals[index]

    transcript: list[dict[str, Any]] = []
    terminated = {agent_name: False for agent_name in env.agents}
    while not all(terminated.values()):
        actions: dict[str, AgentAction] = {}
        for agent_name in env.agents:
            actions[agent_name] = await agents[agent_name].aact(observations[agent_name])
        transcript.append(
            {
                "turn": len(transcript),
                "actions": {agent_name: actions[agent_name].to_natural_language() for agent_name in env.agents},
            }
        )
        observations, _, terminated, _, _ = await env.astep(actions)

    evaluator = CloudGPTEpisodeEvaluator(evaluator_model)
    scores = await evaluator.evaluate(env.turn_number, env.inbox, case)
    response = unweighted_aggregate_evaluate(_scores_to_responses(scores))
    return {
        "combo_pk": case.combo_pk,
        "env_id": case.env_id,
        "agent_ids": list(case.agent_ids),
        "codename": case.codename,
        "agent_names": list(case.agent_names),
        "baseline": baseline,
        "agent_strategy_profile": os.getenv("SOTOPIA_AGENT_STRATEGY_PROFILE", "legacy"),
        "model": model or "",
        "evaluator_model": evaluator_model or "",
        "turns_completed": len(transcript),
        "transcript": transcript,
        "scores": scores,
        "overall": {
            "agent_1": response.p1_rate[0] if response.p1_rate else None,
            "agent_2": response.p2_rate[0] if response.p2_rate else None,
        },
    }


async def run(args: argparse.Namespace) -> dict[str, Any]:
    cases = load_hard_cases(
        Path(args.benchmark_agents),
        Path(args.episodes_jsonl),
        Path(args.cache),
        rebuild_cache=args.rebuild_cache,
    )
    if args.case_indices:
        requested_indices = [int(item) for item in args.case_indices]
        cases = [cases[index] for index in requested_indices]
    if args.limit:
        cases = cases[: args.limit]

    out_path = Path(args.out)
    episodes = _load_completed_episodes(out_path) if args.resume else []
    completed_combo_pks = {str(episode.get("combo_pk", "")) for episode in episodes}
    pending_cases = [case for case in cases if case.combo_pk not in completed_combo_pks]
    if episodes:
        print(f"resume_completed={len(episodes)} pending={len(pending_cases)}")
    for index, case in enumerate(cases, start=1):
        if case.combo_pk in completed_combo_pks:
            continue
        print(f"[{index}/{len(cases)}] {case.codename} {case.combo_pk}")
        episodes.append(await run_case(case, args.baseline, args.model, args.evaluator_model, args.turns))
        _write_result(out_path, args, episodes, target_case_count=len(cases))

    return {
        "task": "sotopia_hard_official_reconstructed",
        "baseline": args.baseline,
        "agent_strategy_profile": args.agent_strategy_profile,
        "case_indices": [int(item) for item in args.case_indices] if args.case_indices else None,
        "model": args.model or "",
        "evaluator_model": args.evaluator_model or "",
        "target_case_count": len(cases),
        "case_count": len(episodes),
        "complete": len(episodes) == len(cases),
        "summary": _summarise(episodes),
        "episodes": episodes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default="llm_belief", choices=["llm_greedy", "llm_belief", "atom_tom1", "econ_bne", "hpsmg_plus"])
    parser.add_argument("--model", default="offline")
    parser.add_argument("--evaluator-model", default="offline")
    parser.add_argument("--agent-strategy-profile", default=os.getenv("SOTOPIA_AGENT_STRATEGY_PROFILE", "legacy"), choices=["legacy", "sotopia_tuned"])
    parser.add_argument("--turns", type=int, default=6)
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--case-indices", nargs="*", help="Optional zero-based SOTOPIA-Hard case indices to run before applying --limit.")
    parser.add_argument("--benchmark-agents", default="external/sotopia_data_probe/benchmark_agents.json")
    parser.add_argument("--episodes-jsonl", default="external/sotopia_data_probe/sotopia_episodes_v1_hf.jsonl")
    parser.add_argument("--cache", default="external/sotopia_data_probe/sotopia_hard_cases_cache.json")
    parser.add_argument("--rebuild-cache", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Resume from an existing output JSON by combo_pk.")
    parser.add_argument("--out", default="analysis/sotopia_hard_official_smoke.json")
    args = parser.parse_args()
    os.environ["SOTOPIA_AGENT_STRATEGY_PROFILE"] = args.agent_strategy_profile

    result = asyncio.run(run(args))
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"case_count": result["case_count"], "summary": result["summary"]}, indent=2))
    print(f"saved={out_path}")


def _load_completed_episodes(out_path: Path) -> list[dict[str, Any]]:
    if not out_path.exists():
        return []
    try:
        data = json.loads(out_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    episodes = data.get("episodes", [])
    return episodes if isinstance(episodes, list) else []


def _write_result(out_path: Path, args: argparse.Namespace, episodes: list[dict[str, Any]], target_case_count: int) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "task": "sotopia_hard_official_reconstructed",
        "baseline": args.baseline,
        "agent_strategy_profile": args.agent_strategy_profile,
        "case_indices": [int(item) for item in args.case_indices] if args.case_indices else None,
        "model": args.model or "",
        "evaluator_model": args.evaluator_model or "",
        "target_case_count": target_case_count,
        "case_count": len(episodes),
        "complete": len(episodes) == target_case_count,
        "summary": _summarise(episodes),
        "episodes": episodes,
    }
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")


def _history_text(messages: list[tuple[str, Message]]) -> str:
    return "\n".join(
        f"{speaker}: {message.to_natural_language()}"
        for speaker, message in messages
        if "did nothing" not in message.to_natural_language()
    )


def _extract_json(text: str) -> str:
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in evaluator response")
    return match.group(0)


def _normalise_scores(raw: dict[str, Any], case: HardCase) -> dict[str, Any]:
    scores: dict[str, Any] = {}
    for agent_key in ("agent_1", "agent_2"):
        agent_scores = raw.get(agent_key, {})
        scores[agent_key] = {}
        for dimension, (low, high) in DIMENSIONS.items():
            item = agent_scores.get(dimension, {})
            score = item.get("score", 0) if isinstance(item, dict) else item
            try:
                numeric = float(score)
            except (TypeError, ValueError):
                numeric = 0.0
            scores[agent_key][dimension] = {
                "score": max(low, min(high, numeric)),
                "reasoning": str(item.get("reasoning", "")) if isinstance(item, dict) else "",
            }
    return scores


def _offline_scores(case: HardCase) -> dict[str, Any]:
    base = {
        "believability": 7,
        "relationship": 1,
        "knowledge": 3,
        "secret": 0,
        "social_rules": 0,
        "financial_and_material_benefits": 1,
        "goal": 5,
    }
    return {
        agent_key: {
            dimension: {"score": score, "reasoning": f"Offline deterministic smoke score for {case.codename}."}
            for dimension, score in base.items()
        }
        for agent_key in ("agent_1", "agent_2")
    }


def _scores_to_responses(scores: dict[str, Any]) -> list[tuple[str, tuple[tuple[str, int | float | bool], str]]]:
    responses = []
    for agent_key, agent_scores in scores.items():
        for dimension, item in agent_scores.items():
            responses.append((agent_key, ((dimension, float(item["score"])), str(item.get("reasoning", "")))))
    return responses


def _summarise(episodes: list[dict[str, Any]]) -> dict[str, Any]:
    if not episodes:
        return {}
    summary: dict[str, Any] = {"agent_1": {}, "agent_2": {}}
    for agent_key in ("agent_1", "agent_2"):
        for dimension in list(DIMENSIONS) + ["overall_score"]:
            values = []
            for episode in episodes:
                if dimension == "overall_score":
                    values.append(episode["overall"][agent_key])
                else:
                    values.append(episode["scores"][agent_key][dimension]["score"])
            values = [float(value) for value in values if value is not None]
            summary[agent_key][dimension] = sum(values) / len(values) if values else None
    summary["mean_overall"] = (summary["agent_1"]["overall_score"] + summary["agent_2"]["overall_score"]) / 2
    return summary


if __name__ == "__main__":
    main()