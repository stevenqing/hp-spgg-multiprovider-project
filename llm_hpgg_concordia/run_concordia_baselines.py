"""Run a small Concordia-adapter social-choice baseline sweep."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .cloudgpt_model import HPGGConcordiaLanguageModel
from .embedder import HashingEmbedder


DEFAULT_BASELINES = ["llm_greedy", "llm_belief", "atom_tom1", "econ_bne"]
VENUES = ["The Anchor", "The Crown", "Riverside Arms"]


def run_sweep(baselines: list[str], model_name: str | None) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    embedder = HashingEmbedder(dimensions=32)
    for baseline in baselines:
        model = HPGGConcordiaLanguageModel(
            model=model_name,
            system_prompt=(
                "You are a Concordia social-simulation agent using the "
                f"{baseline} baseline. Be concise and make one grounded choice."
            ),
        )
        prompt = json.dumps(
            {
                "task": "Concordia pub coordination adapter smoke task",
                "baseline": baseline,
                "scenario": "Three friends must choose one pub. Preferences are partly hidden.",
                "known_facts": [
                    "Alice likes The Anchor.",
                    "Blair said Riverside Arms is quieter.",
                    "Casey wants everyone to stay together.",
                ],
                "options": VENUES,
                "instruction": "Choose the venue most compatible with this baseline.",
            },
            indent=2,
        )
        index, choice, info = model.sample_choice(prompt, VENUES, seed=0)
        rows.append(
            {
                "baseline": baseline,
                "choice_index": index,
                "choice": choice,
                "info": dict(info),
                "prompt_embedding_norm": float((embedder(prompt) ** 2).sum() ** 0.5),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baselines", nargs="+", default=DEFAULT_BASELINES)
    parser.add_argument("--model")
    parser.add_argument("--out", default="analysis/concordia_baseline_choice_sweep.json")
    args = parser.parse_args()

    rows = run_sweep(args.baselines, args.model)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    for row in rows:
        print(f"{row['baseline']}: {row['choice']}")
    print(f"saved={out_path}")


if __name__ == "__main__":
    main()
