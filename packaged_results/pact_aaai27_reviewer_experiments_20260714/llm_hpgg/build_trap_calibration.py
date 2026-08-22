"""Construct deep-trap calibration tensors from an existing calibration file."""

from __future__ import annotations

import argparse

from .environment import build_reward_tensor, load_calibration, save_calibration, tid_min_gap


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an HP-SPGG deep-trap calibration tensor.")
    parser.add_argument("--in", dest="input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    calibration = load_calibration(args.input)
    bundle = build_reward_tensor(int(calibration.get("n", 3)), str(calibration.get("backend", "anthropic")), samples=args.samples, seed=args.seed, trap=True)
    save_calibration(bundle, args.out)
    print(f"saved={args.out}")
    print(f"tid_min_gap={tid_min_gap(bundle.reward_tensor):.4f}")


if __name__ == "__main__":
    main()
