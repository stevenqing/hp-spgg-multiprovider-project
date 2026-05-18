"""Build HP-SPGG reward calibration tensors."""

from __future__ import annotations

import argparse
import os

from .environment import build_reward_tensor, save_calibration, tid_min_gap


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an HP-SPGG calibration tensor.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--n", type=int, default=3)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--backend", default=os.getenv("LLM_HPGG_BACKEND", "anthropic"))
    parser.add_argument("--trap", action="store_true")
    args = parser.parse_args()

    bundle = build_reward_tensor(args.n, args.backend, samples=args.samples, seed=args.seed, trap=args.trap)
    save_calibration(bundle, args.out)
    print(f"saved={args.out}")
    print(f"backend={args.backend} n={args.n} samples={args.samples} trap={args.trap}")
    print(f"tid_min_gap={tid_min_gap(bundle.reward_tensor):.4f}")


if __name__ == "__main__":
    main()
