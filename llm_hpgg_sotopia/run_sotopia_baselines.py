"""Run a small SOTOPIA-compatible baseline action sweep."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sotopia.messages import Observation

from .agents import HPGGSotopiaAgent


DEFAULT_BASELINES = ["llm_greedy", "llm_belief", "atom_tom1", "econ_bne"]


def run_sweep(baselines: list[str], model: str | None) -> list[dict[str, object]]:
    observations = [
        Observation(
            last_turn="You meet another participant who wants to negotiate a shared plan.",
            turn_number=1,
            available_actions=["speak", "none"],
            action_instruction="Choose one action that continues the social interaction.",
        ),
        Observation(
            last_turn='agent_2 said: "I can cooperate, but I need the result to be fair."',
            turn_number=2,
            available_actions=["speak", "action", "none", "leave"],
            action_instruction="Respond with a concrete proposal or utterance.",
        ),
    ]
    rows: list[dict[str, object]] = []
    for baseline in baselines:
        agent = HPGGSotopiaAgent("agent_1", baseline=baseline, model=model)
        agent.goal = "Reach a mutually acceptable agreement without exploiting the other participant."
        for obs_index, observation in enumerate(observations):
            action = agent.act(observation)
            rows.append(
                {
                    "baseline": baseline,
                    "observation_index": obs_index,
                    "action_type": action.action_type,
                    "argument": action.argument,
                    "to": action.to,
                    "natural_language": action.to_natural_language(),
                }
            )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baselines", nargs="+", default=DEFAULT_BASELINES)
    parser.add_argument("--model")
    parser.add_argument("--out", default="analysis/sotopia_baseline_action_sweep.json")
    args = parser.parse_args()

    rows = run_sweep(args.baselines, args.model)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    for row in rows:
        print(f"{row['baseline']}[{row['observation_index']}]: {row['natural_language']}")
    print(f"saved={out_path}")


if __name__ == "__main__":
    main()
