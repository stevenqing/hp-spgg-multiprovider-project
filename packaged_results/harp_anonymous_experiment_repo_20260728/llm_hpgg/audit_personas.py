"""Persona fidelity audit for HP-SPGG calibration tensors."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import numpy as np

from .environment import build_reward_tensor, enumerate_action_profiles, load_calibration, tid_min_gap
from .personas import PERSONAS


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit persona reward ordering and contribution bands.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--backend", default=os.getenv("LLM_HPGG_BACKEND", "anthropic"))
    parser.add_argument("--n", type=int, default=3)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--calibration", default=None)
    args = parser.parse_args()

    if args.calibration:
        calibration = load_calibration(args.calibration)
        reward_tensor = np.asarray(calibration["reward_tensor"], dtype=float)
        profiles = np.asarray(calibration["action_profiles"], dtype=float)
        backend = str(calibration.get("backend", args.backend))
    else:
        bundle = build_reward_tensor(args.n, args.backend, samples=args.samples, seed=args.seed)
        reward_tensor = bundle.reward_tensor
        profiles = enumerate_action_profiles(args.n)
        backend = args.backend
    lines = [f"backend={backend}", f"tid_min_gap={tid_min_gap(reward_tensor):.4f}"]
    for persona_index, persona in enumerate(PERSONAS):
        best_indices = np.argmax(reward_tensor[:, persona_index, :], axis=1)
        best_contribs = [profiles[index, player] for player, index in enumerate(best_indices)]
        lines.append(f"{persona.key}: mean_best_contribution={np.mean(best_contribs):.3f} best_by_player={','.join(f'{value:.2f}' for value in best_contribs)}")
    text = "\n".join(lines) + "\n"
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
