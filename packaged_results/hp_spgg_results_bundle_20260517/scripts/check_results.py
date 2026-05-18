"""Validate generated HP-SPGG benchmark result files."""

from __future__ import annotations

import argparse
import glob
from pathlib import Path

import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser(description="Check HP-SPGG benchmark outputs.")
    parser.add_argument("--results", nargs="+", required=True)
    args = parser.parse_args()

    failures: list[str] = []
    result_paths = expand_inputs(args.results)
    if not result_paths:
        raise FileNotFoundError(f"No result files matched: {args.results}")

    for result_path in result_paths:
        path = Path(result_path)
        data = np.load(path, allow_pickle=True)
        algorithms = [str(value) for value in data["algorithms"]]
        cumulative = data["cumulative_regret"]
        storage = data["storage"]
        print(f"{path}:")
        for algo_index, algorithm in enumerate(algorithms):
            final = cumulative[algo_index, :, -1]
            print(f"  {algorithm}: mean={float(np.mean(final)):.4f} sem={sem(final):.4f} storage={int(storage[algo_index])}")
        if "oracle" in algorithms:
            oracle_index = algorithms.index("oracle")
            oracle_final = float(np.mean(cumulative[oracle_index, :, -1]))
            if abs(oracle_final) > 1e-8:
                failures.append(f"{path}: oracle regret is {oracle_final:.6f}")
        if "random" in algorithms and "hpsmg_plus" in algorithms:
            random_final = float(np.mean(cumulative[algorithms.index("random"), :, -1]))
            plus_final = float(np.mean(cumulative[algorithms.index("hpsmg_plus"), :, -1]))
            if random_final <= plus_final:
                failures.append(f"{path}: random does not exceed hpsmg_plus")
    if failures:
        print("FAILURES:")
        for failure in failures:
            print(f"  {failure}")
        raise SystemExit(1)
    print("all checks passed")


def sem(values: np.ndarray) -> float:
    if len(values) <= 1:
        return 0.0
    return float(np.std(values, ddof=1) / np.sqrt(len(values)))


def expand_inputs(patterns: list[str]) -> list[str]:
    paths: list[str] = []
    for pattern in patterns:
        matches = sorted(glob.glob(pattern))
        paths.extend(matches if matches else [pattern])
    return paths


if __name__ == "__main__":
    main()
