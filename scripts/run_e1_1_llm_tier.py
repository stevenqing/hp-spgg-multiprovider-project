"""E-1.1 LLM-tier n-scaling runner (live LLM judge per backbone).

WARNING: launches live LLM judge calibration calls. Estimated calls per
(n, backbone) = n * |Theta| * |A|^n = 4 * 5^n cells (one judge call each),
plus K * H * n * seeds player calls. Aggregated over n in {3,4,5,6} and two
backbones this is approximately 96k calls. Run only after confirming budget.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results_phase2" / "e1_1_llm_tier"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BACKBONES = {
    "deepseek": "DeepSeek-V3.2",
    "llama_maverick": "Llama-4-Maverick-17B-128E-Instruct-FP8",
    "kimi_k2": "Kimi-K2.6",
    "gpt5_nano": "gpt-5.4-nano-20260317",
}
NS = [3, 4, 5, 6]
SEEDS = 5
K = 20
ALGOS = [
    "hpsmg_plus",
    "hpsmg",
    "joint_psrl",
    "map_greedy",
    "psrl_notype",
    "iql_independent_actions",
    "iql",
    "random",
    "oracle",
]


MAX_PROFILES = 12


def build_calibration(n: int, backbone_key: str, model: str, dry_run: bool, max_profiles: int) -> Path:
    cal = OUT_DIR / f"calibration_live_n{n}_{backbone_key}.npy"
    if cal.exists():
        print(f"SKIP existing calibration {cal.name}")
        return cal
    cmd = [
        sys.executable,
        "-m",
        "llm_hpgg.calibration_live",
        "--out", str(cal),
        "--n", str(n),
        "--samples", "1",
        "--max-profiles", str(max_profiles),
        "--judge-model", model,
        "--workers", "4",
    ]
    print("BUILD-CAL", " ".join(cmd))
    if dry_run:
        return cal
    subprocess.run(cmd, check=True, cwd=str(ROOT))
    return cal


def run(n: int, backbone_key: str, model: str, dry_run: bool, max_profiles: int) -> None:
    out_npz = OUT_DIR / f"E1_1_llm_n{n}_{backbone_key}.npz"
    if out_npz.exists():
        print(f"SKIP existing {out_npz.name}")
        return
    cal = build_calibration(n, backbone_key, model, dry_run, max_profiles)
    cmd = [
        sys.executable,
        "-m",
        "llm_hpgg.run_experiment",
        "--K", str(K),
        "--n", str(n),
        "--seeds", str(SEEDS),
        "--beta", "0.25",
        "--algos", *ALGOS,
        "--calibration", str(cal),
        "--out", str(out_npz),
        "--record-posterior",
        "--matched-seeds",
        "--player-model", model,
        "--judge-model", model,
    ]
    print("RUN", " ".join(cmd))
    if dry_run:
        return
    subprocess.run(cmd, check=True, cwd=str(ROOT))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--backbones", nargs="+", default=list(BACKBONES.keys()))
    parser.add_argument("--ns", nargs="+", type=int, default=NS)
    parser.add_argument("--max-profiles", type=int, default=MAX_PROFILES,
                        help="override calibration --max-profiles (default 12)")
    args = parser.parse_args()

    plan = []
    for n in args.ns:
        for bk in args.backbones:
            plan.append({"n": n, "backbone": bk, "model": BACKBONES[bk]})
    print(json.dumps({"plan_cells": plan}, indent=2))

    for cell in plan:
        run(cell["n"], cell["backbone"], cell["model"], args.dry_run, args.max_profiles)


if __name__ == "__main__":
    main()
