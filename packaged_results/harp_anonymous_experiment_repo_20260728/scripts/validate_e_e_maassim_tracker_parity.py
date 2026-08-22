"""Validate E-E MaaSSim factored-versus-explicit-joint parity artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "analysis" / "e_e_maassim_rq2"
FLEET_SIZES = (2, 3, 4, 6, 8)
LAMBDAS = (0.0, 0.5, 1.0)
SEEDS = tuple(range(10))
JOINT_SIZES = {2, 3, 4}
TYPE_COUNT = 16


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def close(left: float, right: float, tolerance: float = 1e-9) -> bool:
    return abs(left - right) <= tolerance * max(1.0, abs(left), abs(right))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--require-figure", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()

    rows = read_csv(root / "e_e_maassim_tracker_parity.csv")
    summary = read_csv(root / "e_e_maassim_tracker_parity_summary.csv")
    gaps = read_csv(root / "e_e_maassim_tracker_parity_gaps.csv")
    metadata = json.loads((root / "e_e_maassim_tracker_parity_metadata.json").read_text(encoding="utf-8"))

    expected_keys = {
        (seed, n, strength, tracker)
        for n in FLEET_SIZES
        for strength in LAMBDAS
        for seed in SEEDS
        for tracker in (("factored", "joint") if n in JOINT_SIZES else ("factored",))
    }
    observed_keys = {
        (int(row["seed"]), int(row["n"]), float(row["lambda"]), row["tracker"])
        for row in rows
    }
    if len(rows) != len(observed_keys) or observed_keys != expected_keys:
        raise AssertionError(
            f"raw grid mismatch: rows={len(rows)} missing={sorted(expected_keys-observed_keys)[:5]} "
            f"extra={sorted(observed_keys-expected_keys)[:5]}"
        )
    required_columns = {"seed", "n", "lambda", "tracker", "utility", "max_tv", "wallclock", "peak_mem"}
    if not required_columns.issubset(rows[0]):
        raise AssertionError(f"E-E CSV misses required columns: {sorted(required_columns - set(rows[0]))}")

    by_key = {
        (int(row["seed"]), int(row["n"]), float(row["lambda"]), row["tracker"]): row
        for row in rows
    }
    max_tv = 0.0
    for seed, n, strength, tracker in sorted(expected_keys):
        row = by_key[(seed, n, strength, tracker)]
        expected_entries = TYPE_COUNT * n if tracker == "factored" else TYPE_COUNT**n
        expected_bytes = expected_entries * 8
        if int(row["belief_entries"]) != expected_entries:
            raise AssertionError(f"belief-entry mismatch: {(seed,n,strength,tracker)}")
        if int(row["peak_mem_bytes"]) != expected_bytes:
            raise AssertionError(f"belief-memory mismatch: {(seed,n,strength,tracker)}")
        if int(row["peak_mem"]) != expected_bytes or not close(float(row["wallclock"]), float(row["update_wallclock_s"]), 1e-12):
            raise AssertionError(f"requested memory/timing aliases mismatch: {(seed,n,strength,tracker)}")
        if int(row["factored_entries"]) != TYPE_COUNT * n or int(row["joint_entries"]) != TYPE_COUNT**n:
            raise AssertionError(f"storage metadata mismatch: {(seed,n,strength,tracker)}")
        if not close(float(row["storage_ratio"]), TYPE_COUNT**n / (TYPE_COUNT * n)):
            raise AssertionError(f"storage ratio mismatch: {(seed,n,strength,tracker)}")
        if int(row["events"]) <= 0 or int(row["snapshots"]) <= 0:
            raise AssertionError(f"empty replay cell: {(seed,n,strength,tracker)}")
        if float(row["mean_update_us"]) < 0.0 or float(row["update_wallclock_s"]) < 0.0:
            raise AssertionError(f"negative update timing: {(seed,n,strength,tracker)}")
        if n in JOINT_SIZES:
            tv = float(row["max_tv"])
            if not math.isfinite(tv):
                raise AssertionError(f"missing TV: {(seed,n,strength,tracker)}")
            max_tv = max(max_tv, tv)

    for n in JOINT_SIZES:
        for strength in LAMBDAS:
            for seed in SEEDS:
                factored = by_key[(seed, n, strength, "factored")]
                joint = by_key[(seed, n, strength, "joint")]
                for field in ("events", "joint_entries", "factored_entries", "oracle_utility"):
                    if factored[field] != joint[field]:
                        raise AssertionError(f"shared-field mismatch {field}: {(seed,n,strength)}")
                if int(factored["sampling_rng_seed"]) == int(joint["sampling_rng_seed"]):
                    raise AssertionError(f"tracker sampling RNGs were coupled: {(seed,n,strength)}")
        # Lambda changes payoff geometry only; the evidence count and posterior
        # identity diagnostic must remain unchanged within each tracker/seed.
        for seed in SEEDS:
            for tracker in ("factored", "joint"):
                reference = by_key[(seed, n, 0.0, tracker)]
                for strength in LAMBDAS[1:]:
                    comparison = by_key[(seed, n, strength, tracker)]
                    if reference["events"] != comparison["events"] or not close(float(reference["max_tv"]), float(comparison["max_tv"]), 1e-12):
                        raise AssertionError(f"lambda changed evidence/TV: {(seed,n,tracker,strength)}")

    if max_tv >= 1e-10:
        raise AssertionError(f"max marginal TV={max_tv} exceeds 1e-10")

    expected_summary = 24  # 9 joint/factored required cells + 6 factored-only cells.
    if len(summary) != expected_summary:
        raise AssertionError(f"summary rows={len(summary)}, expected {expected_summary}")
    if len(gaps) != 9:
        raise AssertionError(f"gap rows={len(gaps)}, expected 9")
    gap_keys = {(int(row["n"]), float(row["lambda"])) for row in gaps}
    if gap_keys != {(n, strength) for n in JOINT_SIZES for strength in LAMBDAS}:
        raise AssertionError(f"gap grid mismatch: {gap_keys}")
    for row in gaps:
        if int(row["seeds"]) != 10:
            raise AssertionError(f"paired gap seed count mismatch: {row}")
        mean = float(row["joint_minus_factored_mean"])
        sem = float(row["joint_minus_factored_sem"])
        if not close(float(row["ci95_low"]), mean - 2.262 * sem, 1e-8):
            raise AssertionError(f"lower CI mismatch: {row}")
        if not close(float(row["ci95_high"]), mean + 2.262 * sem, 1e-8):
            raise AssertionError(f"upper CI mismatch: {row}")

    if metadata.get("source_scheme") != "scheme i: closed-loop regeneration by fleet size":
        raise AssertionError("E-E did not record preferred scheme i")
    if metadata.get("provider_calls") != 0:
        raise AssertionError("E-E must make zero provider calls")
    if not str(metadata.get("likelihood", "")).startswith("per-driver binary accept/reject"):
        raise AssertionError("E-E did not record the required binary accept/reject likelihood")
    if metadata.get("include_n6_joint"):
        raise AssertionError("release validator expects the declared required matrix without optional n=6 joint")
    if metadata.get("common_environment_indices") != list(SEEDS):
        raise AssertionError("common environment indices are incomplete")
    artifacts = metadata.get("artifacts", [])
    if len(artifacts) != len(FLEET_SIZES) * len(SEEDS) * 4:
        raise AssertionError(f"source artifact inventory={len(artifacts)}, expected 200")
    for item in artifacts:
        path = ROOT / str(item["path"])
        if not path.is_file() or path.stat().st_size != int(item["bytes"]) or sha256(path) != item["sha256"]:
            raise AssertionError(f"source artifact hash mismatch: {path}")

    if args.require_figure:
        for path in (
            ROOT / "arr_paper" / "figs" / "fig_maassim_rq2_parity.pdf",
            ROOT / "arr_paper" / "figs" / "fig_maassim_combined_v22.pdf",
        ):
            if not path.is_file() or path.stat().st_size == 0:
                raise AssertionError(f"missing E-E figure: {path}")

    noncovering = [
        {"n": int(row["n"]), "lambda": float(row["lambda"]), "mean": float(row["joint_minus_factored_mean"]), "ci": [float(row["ci95_low"]), float(row["ci95_high"])]}
        for row in gaps
        if row["ci_covers_zero"].lower() != "true"
    ]
    print(
        json.dumps(
            {
                "status": "ok",
                "raw_rows": len(rows),
                "summary_rows": len(summary),
                "gap_rows": len(gaps),
                "max_marginal_tv": max_tv,
                "noncovering_nominal_95pct_cells": noncovering,
                "source_artifacts": len(artifacts),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
