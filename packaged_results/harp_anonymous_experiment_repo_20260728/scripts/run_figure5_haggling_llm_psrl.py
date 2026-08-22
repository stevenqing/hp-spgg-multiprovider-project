"""Run the missing Figure 5 Haggling LLM-PSRL cells with checkpoints."""

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

from llm_hpgg_concordia.run_haggling_compact import (  # noqa: E402
    build_case,
    ensure_concordia_examples_on_path,
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
    ("haggling", "vegbrooke"),
    ("haggling", "vegbrooke_stubborn"),
    ("haggling_multi_item", "fruitville_gullible"),
    ("haggling", "fruitville"),
)
METHOD = "llm_psrl_verbal"
RELEASE_SUMMARY = ROOT / "arr_paper" / "data" / "figure5_haggling_llm_psrl.json"


def output_path(domain: str, config: str, tier: str) -> Path:
    return ROOT / "analysis" / "llm_psrl_verbal" / f"concordia_full_{domain}_{config}_{tier}_llmpsrl.json"


def seed_succeeded(row: dict[str, Any]) -> bool:
    deals = row.get("deals", [])
    return bool(deals) and all(deal.get("info", {}).get("sample_ok") is True for deal in deals)


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
    domain: str,
    config: str,
    model: str,
    rows_by_seed: dict[int, dict[str, Any]],
) -> None:
    rows = [rows_by_seed[seed] for seed in sorted(rows_by_seed)]
    payload = {
        "domain": domain,
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


def run_seed(domain: str, config_name: str, model: str, seed: int, attempts: int) -> dict[str, Any]:
    config = load_config(domain, config_name)
    for attempt in range(1, attempts + 1):
        row = run_method(build_case(domain, config, seed), METHOD, model_name=model)
        if seed_succeeded(row):
            return row
        errors = sorted(
            {
                deal.get("info", {}).get("error", "missing sample_ok")
                for deal in row.get("deals", [])
                if deal.get("info", {}).get("sample_ok") is not True
            }
        )
        print(
            f"RETRY domain={domain} config={config_name} model={model} "
            f"seed={seed} attempt={attempt}/{attempts} errors={errors}",
            flush=True,
        )
    failed = sum(
        deal.get("info", {}).get("sample_ok") is not True
        for deal in row.get("deals", [])
    )
    raise RuntimeError(
        f"LLM-PSRL did not produce valid actions for {failed} deals after {attempts} attempts: "
        f"domain={domain} config={config_name} model={model} seed={seed}"
    )


def run_cell(
    domain: str,
    config: str,
    tier: str,
    model: str,
    seeds: int,
    workers: int,
    attempts: int,
) -> None:
    path = output_path(domain, config, tier)
    rows_by_seed = load_completed(path, model)
    pending = [seed for seed in range(seeds) if seed not in rows_by_seed]
    print(
        f"CELL tier={tier} domain={domain} config={config} "
        f"complete={len(rows_by_seed)}/{seeds}",
        flush=True,
    )
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(run_seed, domain, config, model, seed, attempts): seed
            for seed in pending
        }
        for future in as_completed(futures):
            seed = futures[future]
            rows_by_seed[seed] = future.result()
            write_checkpoint(path, domain, config, model, rows_by_seed)
            print(f"OK tier={tier} domain={domain} config={config} seed={seed}", flush=True)
    expected = set(range(seeds))
    if set(rows_by_seed) != expected:
        raise AssertionError(f"Incomplete cell {path}: {sorted(rows_by_seed)}")
    write_checkpoint(path, domain, config, model, rows_by_seed)


def write_release_summary(seeds: int) -> bool:
    expected_seeds = list(range(seeds))
    configurations: dict[str, dict[str, Any]] = {}
    for domain, config in CONFIGURATIONS:
        key = f"{domain}/{config}"
        model_rows = []
        for tier, model in MODELS.items():
            path = output_path(domain, config, tier)
            if not path.is_file():
                return False
            payload = json.loads(path.read_text(encoding="utf-8"))
            episodes = payload.get("episodes", [])
            if payload.get("model") != model or payload.get("seeds") != expected_seeds:
                return False
            if not all(seed_succeeded(row) for row in episodes):
                return False
            summary = next(row for row in payload["summary"] if row["method"] == METHOD)
            model_rows.append(
                {
                    "tier": tier,
                    "model": model,
                    "seed_count": len(episodes),
                    "deal_count": sum(len(row.get("deals", [])) for row in episodes),
                    "sample_ok_count": sum(
                        deal.get("info", {}).get("sample_ok") is True
                        for row in episodes
                        for deal in row.get("deals", [])
                    ),
                    "focal_score_mean": float(summary["focal_score_mean"]),
                }
            )
        configurations[key] = {
            "domain": domain,
            "config": config,
            "models": model_rows,
            "four_backbone_focal_score_mean": sum(
                row["focal_score_mean"] for row in model_rows
            ) / len(model_rows),
        }
    payload = {
        "method": METHOD,
        "seed_schedule": expected_seeds,
        "aggregation": "unweighted mean of the four backbone-level 30-seed focal-score means",
        "configurations": configurations,
    }
    RELEASE_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    temporary = RELEASE_SUMMARY.with_suffix(RELEASE_SUMMARY.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(RELEASE_SUMMARY)
    print(f"Release summary: {RELEASE_SUMMARY.relative_to(ROOT)}", flush=True)
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tiers", nargs="*", choices=tuple(MODELS), default=list(MODELS))
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--seed-attempts", type=int, default=3)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if os.getenv("LLM_HPGG_OFFLINE", "0") == "1":
        raise RuntimeError("Refusing to generate Figure 5 data with LLM_HPGG_OFFLINE=1")
    ensure_concordia_examples_on_path()
    for tier in args.tiers:
        model = MODELS[tier]
        for domain, config in CONFIGURATIONS:
            run_cell(domain, config, tier, model, args.seeds, args.workers, args.seed_attempts)
    write_release_summary(args.seeds)
    print("Figure 5 Haggling LLM-PSRL sweep complete", flush=True)


if __name__ == "__main__":
    main()