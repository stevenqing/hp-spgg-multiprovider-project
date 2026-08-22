"""Run Figure 5 Pub Coordination LLM-PSRL cells with seed checkpoints."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "external" / "concordia"))

from llm_hpgg_concordia.run_pub_coordination_compact import (  # noqa: E402
    build_case,
    information_scope_for_method,
    load_config,
    run_method,
    summarize,
)


MODELS = {
    "deepseek": "DeepSeek-V3.2",
    "gpt5_nano": "gpt-5.4-nano-20260317",
    "kimi_k2": "Kimi-K2.6",
    "llama_maverick": "Llama-4-Maverick-17B-128E-Instruct-FP8",
}
CONFIGURATIONS = (
    ("london_mini_s30", "london_mini", 30),
    ("capetown_s100", "capetown", 100),
    ("london_s30", "london", 30),
    ("edinburgh_closures_s30", "edinburgh_closures", 30),
)
METHOD = "llm_psrl_verbal"


def output_path(key: str, tier: str) -> Path:
    return ROOT / "analysis" / "llm_psrl_verbal" / f"concordia_full_pub_{key}_{tier}_llmpsrl.json"


def seed_succeeded(row: dict[str, Any]) -> bool:
    return row.get("info", {}).get("sample_ok") is True


def load_completed(path: Path, model: str) -> dict[int, dict[str, Any]]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("model") != model:
        raise AssertionError(f"Model mismatch in {path}: {payload.get('model')!r}")
    return {
        int(row["seed"]): row
        for row in payload.get("episodes", [])
        if row.get("method") == METHOD and seed_succeeded(row)
    }


def write_checkpoint(
    path: Path,
    config: str,
    model: str,
    rows_by_seed: dict[int, dict[str, Any]],
) -> None:
    rows = [rows_by_seed[seed] for seed in sorted(rows_by_seed)]
    payload = {
        "config": config,
        "seeds": sorted(rows_by_seed),
        "methods": [METHOD],
        "model": model,
        "information_audit": {METHOD: information_scope_for_method(METHOD)},
        "summary": summarize(rows),
        "episodes": rows,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temporary.replace(path)


def run_seed(config_name: str, model: str, seed: int, attempts: int) -> dict[str, Any]:
    config = load_config(config_name)
    for attempt in range(1, attempts + 1):
        row = run_method(build_case(config, seed), METHOD, model_name=model)
        if seed_succeeded(row):
            return row
        print(
            f"RETRY config={config_name} model={model} seed={seed} "
            f"attempt={attempt}/{attempts}",
            flush=True,
        )
    raise RuntimeError(
        f"LLM-PSRL did not return a valid Pub hypothesis after {attempts} attempts: "
        f"config={config_name} model={model} seed={seed}"
    )


def run_cell(key: str, config: str, tier: str, model: str, seeds: int, workers: int, attempts: int) -> None:
    path = output_path(key, tier)
    rows_by_seed = load_completed(path, model)
    pending = [seed for seed in range(seeds) if seed not in rows_by_seed]
    print(f"CELL tier={tier} config={key} complete={len(rows_by_seed)}/{seeds}", flush=True)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(run_seed, config, model, seed, attempts): seed
            for seed in pending
        }
        for future in as_completed(futures):
            seed = futures[future]
            rows_by_seed[seed] = future.result()
            write_checkpoint(path, config, model, rows_by_seed)
            print(f"OK tier={tier} config={key} seed={seed}", flush=True)
    if set(rows_by_seed) != set(range(seeds)):
        raise AssertionError(f"Incomplete Pub cell {path}: {sorted(rows_by_seed)}")
    write_checkpoint(path, config, model, rows_by_seed)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tiers", nargs="*", choices=tuple(MODELS), default=list(MODELS))
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--seed-attempts", type=int, default=5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if os.getenv("LLM_HPGG_OFFLINE", "0") == "1":
        raise RuntimeError("Refusing to generate Figure 5 data with LLM_HPGG_OFFLINE=1")
    for tier in args.tiers:
        model = MODELS[tier]
        for key, config, seeds in CONFIGURATIONS:
            run_cell(key, config, tier, model, seeds, args.workers, args.seed_attempts)
    print("Figure 5 Pub Coordination LLM-PSRL sweep complete", flush=True)


if __name__ == "__main__":
    main()