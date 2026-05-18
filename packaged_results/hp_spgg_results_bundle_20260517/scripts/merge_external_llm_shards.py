from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np


def load_trace(path: str | None) -> list[dict[str, Any]]:
    if not path:
        return []
    trace_path = Path(path)
    if not trace_path.exists():
        return []
    return json.loads(trace_path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge external LLM baseline seed-index shards.")
    parser.add_argument("--base", help="Existing complete result, usually seeds=3. Optional when all seeds are supplied as shards.")
    parser.add_argument("--base-trace", help="Trace for the existing complete result.")
    parser.add_argument("--shard", action="append", required=True, help="Shard .npz result. Repeat for multiple shards.")
    parser.add_argument("--shard-trace", action="append", default=[], help="Shard trace JSON. Repeat in any order.")
    parser.add_argument("--algorithms", nargs="+", help="Algorithm order when no base result is provided.")
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--out", required=True)
    parser.add_argument("--trace-out")
    args = parser.parse_args()

    base = np.load(args.base, allow_pickle=True) if args.base else None
    if base is not None:
        algorithms = [str(value) for value in base["algorithms"]]
        base_regrets = np.asarray(base["regrets"], dtype=float)
        base_welfare = np.asarray(base["welfare"], dtype=float)
        k_rounds = int(base["K"])
        total_seeds = max(args.seeds, int(base["seeds"]))
        backend = str(base["backend"])
        model = str(base["model"])
        econ_rounds = int(base["econ_rounds"])
    else:
        if not args.algorithms:
            raise ValueError("--algorithms is required when --base is not provided.")
        algorithms = list(args.algorithms)
        first_shard = np.load(args.shard[0], allow_pickle=True)
        k_rounds = int(first_shard["K"])
        total_seeds = args.seeds
        backend = str(first_shard["backend"])
        model = str(first_shard["model"])
        econ_rounds = int(first_shard["econ_rounds"])

    regrets = np.full((len(algorithms), total_seeds, k_rounds), np.nan, dtype=float)
    welfare = np.full_like(regrets, np.nan)
    if base is not None:
        regrets[:, : base_regrets.shape[1], :] = base_regrets
        welfare[:, : base_welfare.shape[1], :] = base_welfare

    for shard_path in args.shard:
        shard = np.load(shard_path, allow_pickle=True)
        shard_algorithms = [str(value) for value in shard["algorithms"]]
        seed_indices = shard["seed_indices"] if "seed_indices" in shard.files else np.arange(np.asarray(shard["regrets"]).shape[1])
        shard_regrets = np.asarray(shard["regrets"], dtype=float)
        shard_welfare = np.asarray(shard["welfare"], dtype=float)
        for shard_algo_index, algorithm in enumerate(shard_algorithms):
            target_algo_index = algorithms.index(algorithm)
            for seed_position, seed_index in enumerate(seed_indices):
                regrets[target_algo_index, int(seed_index), :] = shard_regrets[shard_algo_index, seed_position, :]
                welfare[target_algo_index, int(seed_index), :] = shard_welfare[shard_algo_index, seed_position, :]

    if np.isnan(regrets).any() or np.isnan(welfare).any():
        missing = np.argwhere(np.isnan(regrets[:, :, 0]))
        labels = [(algorithms[int(algo_index)], int(seed_index)) for algo_index, seed_index in missing]
        raise ValueError(f"Missing algorithm/seed shard results: {labels}")

    cumulative_regret = np.cumsum(regrets, axis=2)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        out_path,
        algorithms=np.array(algorithms),
        regrets=regrets,
        cumulative_regret=cumulative_regret,
        welfare=welfare,
        backend=backend,
        K=k_rounds,
        seeds=total_seeds,
        seed_indices=np.arange(total_seeds, dtype=int),
        model=model,
        econ_rounds=econ_rounds,
    )

    if args.trace_out:
        traces = load_trace(args.base_trace)
        for trace_path in args.shard_trace:
            traces.extend(load_trace(trace_path))
        trace_out = Path(args.trace_out)
        trace_out.parent.mkdir(parents=True, exist_ok=True)
        trace_out.write_text(json.dumps(traces, indent=2), encoding="utf-8")

    for algorithm, value in zip(algorithms, cumulative_regret[:, :, -1].mean(axis=1)):
        print(f"{algorithm}: final_cumulative_regret_mean={value:.4f}")
    print(f"saved={out_path}")


if __name__ == "__main__":
    main()