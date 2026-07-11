"""Run MaaSSim Persona v2 baseline experiments and aggregate outputs."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis" / "courier_dispatch_maassim"
RUNNER = ROOT / "scripts" / "run_maassim_shadow_smoke.py"
SUMMARIZER = ROOT / "scripts" / "summarize_maassim_baselines.py"


def parse_csv(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def run_command(cmd: list[str]) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{ROOT / 'external' / 'maassim'};{ROOT}"
    subprocess.run(cmd, check=True, cwd=ROOT, env=env)


def run_one(args: argparse.Namespace, policy: str, seed: int) -> None:
    prefix = f"{policy}_{args.prefix}_s{seed}"
    summary = ANALYSIS / f"{prefix}_summary.json"
    if summary.exists() and not args.force:
        return
    cmd = [
        sys.executable,
        str(RUNNER),
        "--seed",
        str(seed),
        "--config",
        str(ROOT / "external" / "maassim" / "MaaSSim" / "data" / "config.json"),
        "--root-path",
        str(ROOT / "external" / "maassim" / "MaaSSim"),
        "--n-passengers",
        str(args.n_passengers),
        "--n-vehicles",
        str(args.n_vehicles),
        "--batch-time",
        str(args.batch_time),
        "--policy",
        policy,
        "--beta",
        str(args.beta),
        "--control-match",
        "--synthetic-rules",
        "--intervene-driver-rules",
        "--passenger-personas",
        "--persona-assignment",
        args.persona_assignment,
        "--passenger-price-sensitive-fare",
        str(args.passenger_price_sensitive_fare),
        "--passenger-impatient-wait-ratio",
        str(args.passenger_impatient_wait_ratio),
        "--passenger-delay-sensitive-total-ratio",
        str(args.passenger_delay_sensitive_total_ratio),
        "--long-trip-seconds",
        str(args.long_trip_seconds),
        "--far-pickup-seconds",
        str(args.far_pickup_seconds),
        "--surge-fare-per-second",
        str(args.surge_fare_per_second),
        "--home-after-seconds",
        str(args.home_after_seconds),
        "--kpi-wait-weight",
        str(args.kpi_wait_weight),
        "--kpi-reject-penalty",
        str(args.kpi_reject_penalty),
        "--kpi-fare-weight",
        str(args.kpi_fare_weight),
        "--out",
        str(ANALYSIS / f"{prefix}_queue_snapshots.jsonl"),
        "--posterior-out",
        str(ANALYSIS / f"{prefix}_driver_posterior.csv"),
        "--passenger-posterior-out",
        str(ANALYSIS / f"{prefix}_passenger_posterior.csv"),
        "--rides-out",
        str(ANALYSIS / f"{prefix}_rides.csv"),
        "--trips-out",
        str(ANALYSIS / f"{prefix}_trips.csv"),
        "--persona-out",
        str(ANALYSIS / f"{prefix}_personas.json"),
        "--summary-out",
        str(summary),
    ]
    run_command(cmd)


def summarize(args: argparse.Namespace) -> None:
    run_command(
        [
            sys.executable,
            str(SUMMARIZER),
            "--prefix",
            args.prefix,
            "--out-prefix",
            args.out_prefix,
            "--fig-stem",
            args.fig_stem,
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix", default="persona_v2_main")
    parser.add_argument("--out-prefix", default="maassim_persona_v2_main_summary")
    parser.add_argument("--fig-stem", default="fig_maassim_persona_v2_main")
    parser.add_argument("--policies", default="nearest,random,pact,oracle")
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--n-passengers", type=int, default=40)
    parser.add_argument("--n-vehicles", type=int, default=8)
    parser.add_argument("--batch-time", type=int, default=120)
    parser.add_argument("--beta", type=float, default=0.25)
    parser.add_argument("--persona-assignment", choices=["cycle", "random"], default="random")
    parser.add_argument("--passenger-price-sensitive-fare", type=float, default=2.75)
    parser.add_argument("--passenger-impatient-wait-ratio", type=float, default=1.0)
    parser.add_argument("--passenger-delay-sensitive-total-ratio", type=float, default=3.0)
    parser.add_argument("--long-trip-seconds", type=float, default=300.0)
    parser.add_argument("--far-pickup-seconds", type=float, default=180.0)
    parser.add_argument("--surge-fare-per-second", type=float, default=0.006)
    parser.add_argument("--home-after-seconds", type=float, default=2700.0)
    parser.add_argument("--kpi-wait-weight", type=float, default=0.12)
    parser.add_argument("--kpi-reject-penalty", type=float, default=0.0)
    parser.add_argument("--kpi-fare-weight", type=float, default=0.0)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    for policy in parse_csv(args.policies):
        for seed in range(args.seeds):
            print(f"=== MaaSSim Persona v2 {policy} seed={seed} ===")
            run_one(args, policy, seed)
    summarize(args)


if __name__ == "__main__":
    main()