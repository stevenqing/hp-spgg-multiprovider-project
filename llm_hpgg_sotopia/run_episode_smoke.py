"""Run a small official SOTOPIA environment loop with project baseline agents."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

os.environ.setdefault("SOTOPIA_STORAGE_BACKEND", "local")

from sotopia.agents import Agents
from sotopia.database.persistent_profile import AgentProfile, EnvironmentProfile, RelationshipType
from sotopia.envs import ParallelSotopiaEnv

from .agents import HPGGSotopiaAgent


def make_agent_profile(first_name: str, last_name: str, secret: str) -> AgentProfile:
    return AgentProfile(
        first_name=first_name,
        last_name=last_name,
        age=31,
        occupation="research participant",
        gender="",
        gender_pronoun="they/them",
        public_info="They are participating in a structured social interaction study.",
        personality_and_values="Pragmatic, polite, and attentive to fairness.",
        secret=secret,
        pk=f"phase2_{first_name.lower()}_{last_name.lower()}",
    )


async def run_episode(baseline: str, model: str | None, turns: int) -> dict[str, object]:
    env_profile = EnvironmentProfile(
        pk="phase2_sotopia_smoke_env",
        codename="phase2_sotopia_smoke",
        scenario=(
            "Two participants must agree on how to divide limited time between a joint task "
            "and their private priorities. Both prefer agreement over walking away."
        ),
        agent_goals=[
            "Secure enough time for the joint task while preserving a friendly relationship.",
            "Protect private preparation time while still finding a cooperative compromise.",
        ],
        relationship=RelationshipType.acquaintance,
        tag="phase2_smoke",
    )
    env = ParallelSotopiaEnv(env_profile=env_profile, action_order="round-robin")
    agents = Agents(
        {
            "agent1": HPGGSotopiaAgent(
                "agent1",
                baseline=baseline,
                model=model,
                agent_profile=make_agent_profile("Avery", "Stone", "They need the joint task to succeed."),
            ),
            "agent2": HPGGSotopiaAgent(
                "agent2",
                baseline=baseline,
                model=model,
                agent_profile=make_agent_profile("Blair", "Reed", "They have a private deadline after the meeting."),
            ),
        }
    )
    observations = env.reset(agents=agents, include_background_observations=True)
    for index, agent_name in enumerate(env.agents):
        agents[agent_name].goal = env_profile.agent_goals[index]

    transcript: list[dict[str, object]] = []
    for turn in range(turns):
        actions = {}
        for agent_name in env.agents:
            actions[agent_name] = await agents[agent_name].aact(observations[agent_name])
        transcript.append(
            {
                "turn": turn,
                "actions": {
                    agent_name: actions[agent_name].to_natural_language()
                    for agent_name in env.agents
                },
            }
        )
        observations, rewards, terminated, _, info = await env.astep(actions)
        if all(terminated.values()):
            break

    return {
        "baseline": baseline,
        "model": model or "",
        "turns_requested": turns,
        "turns_completed": len(transcript),
        "transcript": transcript,
        "last_rewards": rewards,
        "last_info": info,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default="llm_belief")
    parser.add_argument("--model")
    parser.add_argument("--turns", type=int, default=3)
    parser.add_argument("--out", default="analysis/sotopia_official_episode_smoke.json")
    args = parser.parse_args()

    result = asyncio.run(run_episode(args.baseline, args.model, args.turns))
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"baseline": result["baseline"], "turns_completed": result["turns_completed"]}, indent=2))
    print(f"saved={out_path}")


if __name__ == "__main__":
    main()
