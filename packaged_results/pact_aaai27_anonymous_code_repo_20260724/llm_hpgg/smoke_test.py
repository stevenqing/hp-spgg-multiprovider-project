"""Smoke-test configured LLM backends."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .llm_agent import call_judge, call_player
from .personas import PERSONAS, judge_system_prompt, persona_system_prompt


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Smoke-test one player and one judge call.")
    parser.add_argument("--backend", default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    if args.backend:
        os.environ["LLM_HPGG_BACKEND"] = args.backend
    player_reply = call_player(
        persona_system_prompt(PERSONAS[0]),
        "Round 1: choose a contribution from {0.0, 0.25, 0.5, 0.75, 1.0}. Return JSON with contribution and reason.",
        max_tokens=128,
    )
    judge_reply = call_judge(
        judge_system_prompt(),
        "Persona=altruistic_builder, contribution=1.0, group_mean=0.9. Score satisfaction.",
        max_tokens=64,
        temperature=0.0,
    )
    result = {"backend": os.getenv("LLM_HPGG_BACKEND", "anthropic"), "player_reply": player_reply, "judge_reply": judge_reply}
    text = json.dumps(result, indent=2)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
