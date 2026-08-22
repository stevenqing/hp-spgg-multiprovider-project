"""Multi-model driver for pub_coordination type-recovery v2.

Loops over the four paper-aligned CloudGPT model deployments and produces a
per-model JSON + an aggregate JSON / Markdown summary suitable for the
type-recovery figure in HP-SPGG_Multi_Provider_Research_Plan.md.

Usage (PowerShell):
  $env:LLM_HPGG_BACKEND='cloudgpt'
  .\.venvs\concordia-py314\Scripts\python.exe -u `
      -m llm_hpgg_concordia.run_pub_coordination_type_recovery_v2_multi_model `
      --config capetown --seeds 5 --rounds 8 --epsilon 0.15 `
      --out-dir analysis\pub_coord_type_recovery_v2_multi
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path
from typing import Any

from llm_hpgg_concordia.run_pub_coordination_type_recovery_v2 import (
    DEFAULT_METHODS,
    METHOD_REGISTRY,
    build_case,
    ensure_concordia_examples_on_path,
    load_config,
    run_episode,
    summarize,
    write_summary_md,
)


# Paper models: same four families used in the HP-SPGG cross-model figures
# (see packaged_results/.../check_proposed_vs_baselines.py).
PAPER_MODELS: list[tuple[str, str]] = [
    ("gpt-5.4-nano", "gpt-5.4-nano-20260317"),
    ("DeepSeek-V3.2", "DeepSeek-V3.2"),
    ("Kimi-K2.6", "Kimi-K2.6"),
    ("Llama-4-Maverick", "Llama-4-Maverick-17B-128E-Instruct-FP8"),
]


def _slug(name: str) -> str:
    return name.replace("/", "_").replace(".", "_").replace("-", "_")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="capetown")
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--seed-offset", type=int, default=0)
    parser.add_argument("--rounds", type=int, default=8)
    parser.add_argument("--epsilon", type=float, default=0.15)
    parser.add_argument("--methods", nargs="+", default=DEFAULT_METHODS,
                        choices=list(METHOD_REGISTRY))
    parser.add_argument("--models", nargs="+", default=None,
                        help="Override model deployment ids (defaults to PAPER_MODELS).")
    parser.add_argument("--model-labels", nargs="+", default=None,
                        help="Display labels for --models (same length).")
    parser.add_argument("--out-dir", default="analysis/pub_coord_type_recovery_v2_multi")
    args = parser.parse_args()

    if args.models:
        if args.model_labels and len(args.model_labels) != len(args.models):
            sys.exit("--model-labels must match --models length")
        labels = args.model_labels or list(args.models)
        models = list(zip(labels, args.models))
    else:
        models = PAPER_MODELS

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ensure_concordia_examples_on_path()
    config = load_config(args.config)
    seeds = [args.seed_offset + i for i in range(args.seeds)]

    aggregate: dict[str, Any] = {
        "config": args.config,
        "rounds": args.rounds,
        "epsilon": args.epsilon,
        "seeds": seeds,
        "methods": list(args.methods),
        "models": [label for label, _ in models],
        "by_model": {},
    }

    for label, model_id in models:
        slug = _slug(label)
        print(f"\n========== MODEL: {label}  (id={model_id}) ==========\n", flush=True)
        t0 = time.time()
        rows: list[dict[str, Any]] = []
        for seed in seeds:
            case = build_case(config, seed)
            rng = random.Random(seed * 7919 + 1)
            print(f"=== seed={seed} venues={case['venues']} people={case['people']} ===",
                  flush=True)
            episode_rows = run_episode(
                case, args.methods, args.rounds, args.epsilon, model_id, rng,
            )
            rows.extend(episode_rows)
        summary = summarize(rows, rounds=args.rounds)
        elapsed = time.time() - t0
        payload = {
            "config": args.config,
            "model": label,
            "model_id": model_id,
            "seeds": seeds,
            "methods": list(args.methods),
            "rounds": args.rounds,
            "epsilon": args.epsilon,
            "summary": summary,
            "episodes": rows,
            "total_elapsed_sec": elapsed,
        }
        out_json = out_dir / f"type_recovery_{slug}.json"
        with out_json.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        out_md = out_dir / f"type_recovery_{slug}.md"
        write_summary_md(out_md, payload)
        print(f"wrote {out_json}\nwrote {out_md}\n[{label}] elapsed={elapsed:.1f}s",
              flush=True)
        aggregate["by_model"][label] = {
            "model_id": model_id,
            "elapsed_seconds": elapsed,
            "summary": summary,
        }

    agg_json = out_dir / "aggregate.json"
    with agg_json.open("w", encoding="utf-8") as fh:
        json.dump(aggregate, fh, indent=2)
    print(f"\nwrote {agg_json}", flush=True)

    method_order = list(args.methods)
    header = "| method | " + " | ".join(label for label, _ in models) + " |"
    sep = "|---|" + "---:|" * len(models)
    lines = [
        "# Pub Coordination Type Recovery (v2) - Multi-Model",
        "",
        f"- config: `{args.config}`",
        f"- seeds: {args.seeds}, rounds: {args.rounds}, epsilon: {args.epsilon}",
        f"- methods: {', '.join(args.methods)}",
        f"- models: {', '.join(label for label, _ in models)}",
        "",
        "## Final-round top-1 accuracy (higher = better)",
        "",
        header,
        sep,
    ]
    for method in method_order:
        cells = [method]
        for label, _ in models:
            summary = aggregate["by_model"].get(label, {}).get("summary", {})
            final = summary.get("final", []) if summary else []
            row = next((r for r in final if r["method"] == method), None)
            cells.append(f"{row['top1_accuracy_mean']:.3f}" if row else "-")
        lines.append("| " + " | ".join(cells) + " |")
    lines += [
        "",
        "## Final-round NLL (lower = better)",
        "",
        header,
        sep,
    ]
    for method in method_order:
        cells = [method]
        for label, _ in models:
            summary = aggregate["by_model"].get(label, {}).get("summary", {})
            final = summary.get("final", []) if summary else []
            row = next((r for r in final if r["method"] == method), None)
            cells.append(f"{row['nll_mean']:.3f}" if row else "-")
        lines.append("| " + " | ".join(cells) + " |")
    agg_md = out_dir / "aggregate.md"
    agg_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {agg_md}")


if __name__ == "__main__":
    main()
