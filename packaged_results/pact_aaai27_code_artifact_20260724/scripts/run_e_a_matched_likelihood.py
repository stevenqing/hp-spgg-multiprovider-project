"""Run and summarize the four-backbone environment-matched HP-SPGG control.

The protocol pins one complete live calibration tensor per backbone, then applies
one common seed schedule to every native and live baseline.  All methods read
realized rewards and the oracle from the same pinned tensor.  Every LLM response
is checkpointed so interrupted jobs can resume without repeating accepted calls.
"""

from __future__ import annotations

import argparse
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np

from paper_comparison_methods import (
    METHOD_COLORS,
    METHOD_LABELS,
    METHOD_MARKERS,
    METHOD_ORDER,
    ORACLE_COLOR,
    ORACLE_LINESTYLE,
)


@dataclass(frozen=True)
class Backbone:
    label: str
    model: str
    slug: str


BACKBONES = (
    Backbone("DeepSeek-V3.2", "DeepSeek-V3.2", "DeepSeek_V3_2"),
    Backbone("GPT-5.4-nano", "gpt-5.4-nano-20260317", "gpt_5_4_nano_20260317"),
    Backbone("Kimi-K2.6", "Kimi-K2.6", "Kimi_K2_6"),
    Backbone(
        "Llama-4-Maverick",
        "Llama-4-Maverick-17B-128E-Instruct-FP8",
        "Llama_4_Maverick_17B_128E_Instruct_FP8",
    ),
)
NATIVE_ALGORITHMS = (
    "oracle",
    "hpsmg_plus",
    "hpsmg",
    "joint_psrl",
    "llm_psrl_verbal",
    "psrl_notype",
)
EXTERNAL_ALGORITHMS = ("atom_tom0", "atom_tom1", "atom_tom2", "econ_bne")
DISPLAY = {
    "oracle": "Oracle",
    "hpsmg_plus": "PACT+",
    "hpsmg": "PACT",
    "joint_psrl": "Joint-PSRL",
    "llm_psrl_verbal": "LLM-PSRL",
    "psrl_notype": "PSRL-NoType",
    "atom_tom0": "A-ToM-0",
    "atom_tom1": "A-ToM-1",
    "atom_tom2": "A-ToM-2",
    "econ_bne": "ECON-BNE",
}
PLOT_METHOD_MAP = {
    "pact_family": "hpsmg_plus",
    "llm_psrl": "llm_psrl_verbal",
    "atom_tom1": "atom_tom1",
    "econ_bne": "econ_bne",
}
PLOT_ORDER = tuple(PLOT_METHOD_MAP[method] for method in METHOD_ORDER)
COLORS = {
    "oracle": "#111111",
    "hpsmg_plus": METHOD_COLORS["pact_family"],
    "hpsmg": "#3f72b5",
    "joint_psrl": "#91afd2",
    "llm_psrl_verbal": METHOD_COLORS["llm_psrl"],
    "psrl_notype": "#4b4b4b",
    "atom_tom0": "#d9a23f",
    "atom_tom1": METHOD_COLORS["atom_tom1"],
    "atom_tom2": "#a96334",
    "econ_bne": METHOD_COLORS["econ_bne"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("calibrate", "run", "aggregate", "all"), default="all")
    parser.add_argument("--root", type=Path, default=Path("analysis/e_a_matched_likelihood/matched_s10"))
    parser.add_argument("--paper-fig-dir", type=Path, default=Path("arr_paper/figs"))
    parser.add_argument("--models", nargs="*", default=None, help="Optional backbone labels, models, or slugs.")
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--seed-offset", type=int, default=0)
    parser.add_argument("--K", type=int, default=20)
    parser.add_argument("--beta", type=float, default=0.25)
    parser.add_argument("--calibration-workers", type=int, default=12)
    parser.add_argument("--calibration-model-workers", type=int, default=1,
                        help="Backbones calibrated concurrently; each uses --calibration-workers cell workers.")
    parser.add_argument("--run-workers", type=int, default=8)
    parser.add_argument("--external-seed-workers", type=int, default=5)
    parser.add_argument("--native-seed-workers", type=int, default=5)
    parser.add_argument("--econ-rounds", type=int, default=3)
    parser.add_argument("--force", action="store_true", help="Recompute result NPZs; response caches are retained.")
    parser.add_argument("--offline", action="store_true", help="Use the repository offline LLM stub for smoke tests.")
    return parser.parse_args()


def selected_backbones(raw: list[str] | None) -> list[Backbone]:
    if not raw:
        return list(BACKBONES)
    wanted = {value.lower() for value in raw}
    selected = [
        backbone
        for backbone in BACKBONES
        if {backbone.label.lower(), backbone.model.lower(), backbone.slug.lower()} & wanted
    ]
    if len(selected) != len(wanted):
        known = {value.lower() for backbone in BACKBONES for value in (backbone.label, backbone.model, backbone.slug)}
        missing = sorted(wanted - known)
        if missing:
            raise ValueError(f"Unknown backbone selector(s): {missing}")
    return selected


def python_command() -> str:
    return sys.executable


def calibration_paths(root: Path, backbone: Backbone) -> tuple[Path, Path, Path]:
    base = root / "calibration" / f"e_a_c19_fullgrid_{backbone.slug}"
    return base.with_suffix(".npy"), base.with_suffix(".cache.jsonl"), base.with_suffix(".report.json")


def native_paths(root: Path, backbone: Backbone) -> tuple[Path, Path]:
    return root / "native" / f"{backbone.slug}.npz", root / "native" / f"{backbone.slug}.verbal_cache.json"


def external_paths(root: Path, backbone: Backbone, algorithm: str) -> tuple[Path, Path, Path]:
    base = root / "external" / f"{backbone.slug}_{algorithm}"
    return base.with_suffix(".npz"), base.with_suffix(".cache.json"), base.with_suffix(".trace.json")


def base_environment(offline: bool) -> dict[str, str]:
    environment = os.environ.copy()
    environment["LLM_HPGG_BACKEND"] = "cloudgpt"
    environment.setdefault("CLOUDGPT_ATTEMPTS", "6")
    environment.setdefault("CLOUDGPT_TIMEOUT", "120")
    environment.setdefault("EXTERNAL_LLM_CALL_RETRIES", "8")
    environment.setdefault("LLM_BASELINE_CALL_RETRIES", "8")
    environment.setdefault("VERBAL_LLM_CALL_RETRIES", "8")
    environment.setdefault("EXTERNAL_AGENT_WORKERS", "1")
    environment["EXTERNAL_STRICT_PARSING"] = "1"
    environment["LLM_PSRL_STRICT"] = "1"
    if offline:
        environment["LLM_HPGG_OFFLINE"] = "1"
    else:
        environment.pop("LLM_HPGG_OFFLINE", None)
    return environment


def run_command(command: list[str], environment: dict[str, str]) -> None:
    print("RUN", " ".join(command), flush=True)
    subprocess.run(command, check=True, env=environment)


def valid_npz(path: Path, required_keys: tuple[str, ...]) -> bool:
    if not path.exists():
        return False
    try:
        with np.load(path, allow_pickle=True) as payload:
            return all(key in payload.files for key in required_keys)
    except (OSError, ValueError):
        return False


def valid_native_npz(path: Path) -> bool:
    if not valid_npz(
        path,
        ("algorithms", "regrets", "cumulative_regret", "welfare", "true_types", "matched_seeds"),
    ):
        return False
    try:
        with np.load(path, allow_pickle=True) as payload:
            return (
                int(np.asarray(payload["verbal_sample_fallback"], dtype=int).sum()) == 0
                and int(np.asarray(payload["verbal_update_failed"], dtype=int).sum()) == 0
            )
    except (OSError, ValueError, KeyError):
        return False


def run_calibrations(args: argparse.Namespace, backbones: list[Backbone]) -> None:
    environment = base_environment(args.offline)
    jobs: list[tuple[str, list[str]]] = []
    for backbone in backbones:
        tensor, cache, report = calibration_paths(args.root, backbone)
        if tensor.exists() and report.exists() and not args.force:
            metadata = json.loads(report.read_text(encoding="utf-8"))
            if int(metadata.get("incomplete_required_cells", 1)) == 0:
                print(f"SKIP complete calibration {backbone.label}: {tensor}")
                continue
        command = [
            python_command(), "-m", "llm_hpgg.calibration_live",
            "--out", str(tensor), "--cache", str(cache), "--report", str(report),
            "--n", "3", "--samples", "1", "--max-profiles", "0",
            "--judge-model", backbone.model,
            "--snapshot-id", f"e_a_c19_fullgrid_{backbone.slug}_20260722",
            "--workers", str(args.calibration_workers), "--save-every", "24",
            "--no-synthetic-fallback",
        ]
        jobs.append((backbone.label, command))
    if not jobs:
        return
    failures: list[str] = []
    with ThreadPoolExecutor(max_workers=max(1, args.calibration_model_workers)) as executor:
        futures = {executor.submit(run_command, command, environment): label for label, command in jobs}
        for future in as_completed(futures):
            label = futures[future]
            try:
                future.result()
                print(f"DONE calibration:{label}", flush=True)
            except Exception as exc:
                failures.append(f"{label}: {exc}")
                print(f"FAILED calibration:{label}: {exc}", flush=True)
    if failures:
        raise RuntimeError("Calibration failures; rerun to resume from cache:\n" + "\n".join(failures))


def build_run_jobs(args: argparse.Namespace, backbones: list[Backbone]) -> list[tuple[str, list[str]]]:
    jobs: list[tuple[str, list[str]]] = []
    calibrations: dict[str, Path] = {}
    for backbone in backbones:
        calibration, _, report = calibration_paths(args.root, backbone)
        if not calibration.exists():
            raise FileNotFoundError(f"Missing calibration for {backbone.label}: {calibration}")
        if not report.exists():
            raise FileNotFoundError(f"Missing calibration report for {backbone.label}: {report}")
        calibration_report = json.loads(report.read_text(encoding="utf-8"))
        if int(calibration_report.get("incomplete_required_cells", 1)) != 0:
            raise AssertionError(f"Calibration is incomplete; resume calibration first: {report}")
        if int(calibration_report.get("live_profile_count", 0)) != 125:
            raise AssertionError(f"Calibration is not the required full 125-profile grid: {report}")
        calibrations[backbone.slug] = calibration

    # Round-robin by method so concurrent jobs target different deployments.
    for backbone in backbones:
        calibration = calibrations[backbone.slug]
        native_out, verbal_cache = native_paths(args.root, backbone)
        if args.force or not valid_native_npz(native_out):
            command = [
                python_command(), "-m", "llm_hpgg.run_experiment",
                "--calibration", str(calibration), "--out", str(native_out),
                "--n", "3", "--K", str(args.K), "--seeds", str(args.seeds),
                "--seed-offset", str(args.seed_offset), "--matched-seeds",
                "--beta", str(args.beta), "--record-posterior",
                "--algos", *NATIVE_ALGORITHMS,
                "--verbal-model", backbone.model, "--verbal-cache", str(verbal_cache),
                "--player-model", backbone.model, "--judge-model", backbone.model,
                "--seed-workers", str(args.native_seed_workers),
            ]
            jobs.append((f"native:{backbone.label}", command))

    for algorithm in EXTERNAL_ALGORITHMS:
        for backbone in backbones:
            calibration = calibrations[backbone.slug]
            output, cache, trace = external_paths(args.root, backbone, algorithm)
            if not args.force and valid_npz(
                output,
                ("algorithms", "regrets", "cumulative_regret", "welfare", "true_types", "rng_seeds", "matched_seeds"),
            ):
                continue
            command = [
                python_command(), "-m", "llm_hpgg.run_external_llm_baselines",
                "--calibration", str(calibration), "--out", str(output),
                "--cache", str(cache), "--trace-out", str(trace),
                "--n", "3", "--K", str(args.K), "--seeds", str(args.seeds),
                "--seed-offset", str(args.seed_offset), "--matched-seeds",
                "--algos", algorithm, "--model", backbone.model,
                "--econ-rounds", str(args.econ_rounds),
                "--seed-workers", str(args.external_seed_workers),
            ]
            if args.offline:
                command.append("--offline")
            jobs.append((f"external:{backbone.label}:{algorithm}", command))

    queues = {backbone.label: [] for backbone in backbones}
    for job in jobs:
        queues[job[0].split(":", 2)[1]].append(job)
    round_robin: list[tuple[str, list[str]]] = []
    while any(queues.values()):
        for backbone in backbones:
            if queues[backbone.label]:
                round_robin.append(queues[backbone.label].pop(0))
    return round_robin


def run_experiments(args: argparse.Namespace, backbones: list[Backbone]) -> None:
    jobs = build_run_jobs(args, backbones)
    if not jobs:
        print("All matched result files already exist.")
        return
    environment = base_environment(args.offline)
    queues = {backbone.label: [] for backbone in backbones}
    for job in jobs:
        queues[job[0].split(":", 2)[1]].append(job)

    def run_backbone_queue(backbone_label: str) -> list[str]:
        failures: list[str] = []
        for label, command in queues[backbone_label]:
            try:
                run_command(command, environment)
                print(f"DONE {label}", flush=True)
            except Exception as exc:
                failures.append(f"{label}: {exc}")
                print(f"FAILED {label}: {exc}", flush=True)
        return failures

    failures: list[str] = []
    active_backbones = [backbone.label for backbone in backbones if queues[backbone.label]]
    with ThreadPoolExecutor(max_workers=min(max(1, args.run_workers), len(active_backbones))) as executor:
        futures = {executor.submit(run_backbone_queue, label): label for label in active_backbones}
        for future in as_completed(futures):
            failures.extend(future.result())
    if failures:
        raise RuntimeError("Matched run failures:\n" + "\n".join(failures))


def mean_sem(values: Iterable[float]) -> tuple[float, float]:
    array = np.asarray(list(values), dtype=float)
    if len(array) == 0:
        return float("nan"), float("nan")
    sem = float(array.std(ddof=1) / math.sqrt(len(array))) if len(array) > 1 else 0.0
    return float(array.mean()), sem


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strict_repair_template_sha256() -> str:
    source = Path("llm_hpgg/run_external_llm_baselines.py").read_text(encoding="utf-8")
    start = source.index("def strict_repair_prompt(")
    end = source.index("\ndef external_agent_workers", start)
    return hashlib.sha256(source[start:end].encode("utf-8")).hexdigest()


def count_json_cache(path: Path) -> int:
    if not path.exists():
        return 0
    payload = json.loads(path.read_text(encoding="utf-8"))
    return len(payload) if isinstance(payload, dict) else 0


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"No rows for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def load_rows(args: argparse.Namespace, backbones: list[Backbone]) -> tuple[list[dict[str, object]], dict[str, dict[str, np.ndarray]]]:
    rows: list[dict[str, object]] = []
    type_reference: dict[str, np.ndarray] = {}
    raw_by_model: dict[str, dict[str, np.ndarray]] = {}
    for backbone in backbones:
        calibration_path, _, _ = calibration_paths(args.root, backbone)
        calibration_digest = sha256(calibration_path)
        per_seed_dir = args.root / "per_seed" / backbone.slug
        per_seed_dir.mkdir(parents=True, exist_ok=True)
        native_path, _ = native_paths(args.root, backbone)
        native = np.load(native_path, allow_pickle=True)
        native_algorithms = [str(value) for value in native["algorithms"]]
        if tuple(native_algorithms) != NATIVE_ALGORITHMS:
            raise AssertionError(
                f"Native method set/order mismatch in {native_path}: "
                f"observed={native_algorithms}, expected={list(NATIVE_ALGORITHMS)}"
            )
        native_episode_regret = np.asarray(native["regrets"], dtype=float)
        native_cumulative = np.asarray(native["cumulative_regret"], dtype=float)
        native_welfare = np.asarray(native["welfare"], dtype=float)
        native_regret = native_cumulative[:, :, -1]
        native_types = np.asarray(native["true_types"], dtype=int)
        verbal_sample_fallback = int(np.asarray(native["verbal_sample_fallback"], dtype=int).sum())
        verbal_update_failed = int(np.asarray(native["verbal_update_failed"], dtype=int).sum())
        if verbal_sample_fallback or verbal_update_failed:
            raise AssertionError(
                f"LLM-PSRL contains fallbacks in {native_path}: "
                f"sample_fallback={verbal_sample_fallback}, update_failed={verbal_update_failed}; "
                "rerun the native cell after clearing any invalid cached reply."
            )
        if not bool(native["matched_seeds"]):
            raise AssertionError(f"Native output is not marked matched: {native_path}")
        if int(np.asarray(native["seed_offset"]).item()) != args.seed_offset:
            raise AssertionError(f"Native seed offset mismatch in {native_path}")
        if int(np.asarray(native["seeds"]).item()) != args.seeds:
            raise AssertionError(f"Native seed count mismatch in {native_path}")
        if not np.all(native_types == native_types[0:1]):
            raise AssertionError(f"Native true types differ across algorithms: {native_path}")
        expected_seeds = np.arange(args.seed_offset, args.seed_offset + args.seeds, dtype=int)
        reference = native_types[0]
        type_reference[backbone.label] = reference
        raw_by_model[backbone.label] = {}
        for algorithm_index, algorithm in enumerate(native_algorithms):
            values = native_regret[algorithm_index]
            raw_by_model[backbone.label][algorithm] = values
            for seed_index, value in enumerate(values):
                write_per_seed_npz(
                    per_seed_dir / f"{algorithm}_seed{seed_index:02d}.npz",
                    backbone, algorithm, seed_index, int(expected_seeds[seed_index]),
                    reference[seed_index], native_episode_regret[algorithm_index, seed_index],
                    native_cumulative[algorithm_index, seed_index],
                    native_welfare[algorithm_index, seed_index], calibration_path,
                    calibration_digest, args,
                )
                rows.append(
                    {
                        "model": backbone.label,
                        "model_snapshot": backbone.model,
                        "algorithm": algorithm,
                        "family": "native",
                        "seed_index": seed_index,
                        "rng_seed": int(expected_seeds[seed_index]),
                        "true_types": "|".join(str(int(item)) for item in reference[seed_index]),
                        "initial_state_id": "fixed_hp_spgg_initial_state",
                        "final_cumulative_regret": float(value),
                        "matched_seed": True,
                        "source_file": str(native_path),
                    }
                )
        for algorithm in EXTERNAL_ALGORITHMS:
            output, _, _ = external_paths(args.root, backbone, algorithm)
            external = np.load(output, allow_pickle=True)
            ext_algorithms = [str(value) for value in external["algorithms"]]
            if ext_algorithms != [algorithm]:
                raise AssertionError(f"Unexpected algorithms in {output}: {ext_algorithms}")
            if not bool(external["matched_seeds"]):
                raise AssertionError(f"External output is not marked matched: {output}")
            ext_types = np.asarray(external["true_types"], dtype=int)
            ext_seeds = np.asarray(external["rng_seeds"], dtype=int)
            if ext_types.ndim == 3 and ext_types.shape[0] == 1:
                ext_types = ext_types[0]
            if ext_seeds.ndim == 2 and ext_seeds.shape[0] == 1:
                ext_seeds = ext_seeds[0]
            if ext_types.shape != (args.seeds, 3) or ext_seeds.shape != (args.seeds,):
                raise AssertionError(
                    f"Unexpected external provenance shapes in {output}: "
                    f"true_types={ext_types.shape}, rng_seeds={ext_seeds.shape}"
                )
            if not np.array_equal(ext_types, reference):
                raise AssertionError(f"True types do not match native output: {output}")
            if not np.array_equal(ext_seeds, expected_seeds):
                raise AssertionError(f"RNG seeds do not match protocol: {output}")
            values = np.asarray(external["cumulative_regret"], dtype=float)[0, :, -1]
            ext_episode_regret = np.asarray(external["regrets"], dtype=float)[0]
            ext_cumulative = np.asarray(external["cumulative_regret"], dtype=float)[0]
            ext_welfare = np.asarray(external["welfare"], dtype=float)[0]
            raw_by_model[backbone.label][algorithm] = values
            for seed_index, value in enumerate(values):
                write_per_seed_npz(
                    per_seed_dir / f"{algorithm}_seed{seed_index:02d}.npz",
                    backbone, algorithm, seed_index, int(ext_seeds[seed_index]),
                    ext_types[seed_index], ext_episode_regret[seed_index],
                    ext_cumulative[seed_index], ext_welfare[seed_index],
                    calibration_path, calibration_digest, args,
                )
                rows.append(
                    {
                        "model": backbone.label,
                        "model_snapshot": backbone.model,
                        "algorithm": algorithm,
                        "family": "LLM-coordination",
                        "seed_index": seed_index,
                        "rng_seed": int(ext_seeds[seed_index]),
                        "true_types": "|".join(str(int(item)) for item in ext_types[seed_index]),
                        "initial_state_id": "fixed_hp_spgg_initial_state",
                        "final_cumulative_regret": float(value),
                        "matched_seed": True,
                        "source_file": str(output),
                    }
                )
    return rows, raw_by_model


def write_per_seed_npz(
    path: Path,
    backbone: Backbone,
    algorithm: str,
    seed_index: int,
    rng_seed: int,
    true_types: np.ndarray,
    regrets: np.ndarray,
    cumulative_regret: np.ndarray,
    welfare: np.ndarray,
    calibration_path: Path,
    calibration_sha256: str,
    args: argparse.Namespace,
) -> None:
    np.savez_compressed(
        path,
        model=backbone.label,
        model_snapshot=backbone.model,
        algorithm=algorithm,
        seed_index=int(seed_index),
        rng_seed=int(rng_seed),
        seed_offset=int(args.seed_offset),
        expected_rng_seed=int(args.seed_offset + seed_index),
        true_types=np.asarray(true_types, dtype=int),
        initial_state_id="fixed_hp_spgg_initial_state",
        calibration_path=str(calibration_path),
        calibration_sha256=calibration_sha256,
        regrets=np.asarray(regrets, dtype=float),
        cumulative_regret=np.asarray(cumulative_regret, dtype=float),
        welfare=np.asarray(welfare, dtype=float),
        K=int(args.K),
        beta=float(args.beta),
        matched_seed=True,
    )


def summarize(args: argparse.Namespace, backbones: list[Backbone], rows: list[dict[str, object]], raw: dict[str, dict[str, np.ndarray]]) -> list[dict[str, object]]:
    summaries: list[dict[str, object]] = []
    for backbone in backbones:
        values = raw[backbone.label]
        method_stats = {algorithm: mean_sem(method_values) for algorithm, method_values in values.items()}
        best_baseline = min(EXTERNAL_ALGORITHMS, key=lambda algorithm: method_stats[algorithm][0])
        best_family = min(("hpsmg", "hpsmg_plus"), key=lambda algorithm: method_stats[algorithm][0])
        pact_plus = values["hpsmg_plus"]
        pact = values["hpsmg"]
        joint = values["joint_psrl"]
        baseline = values[best_baseline]
        pact_gap_mean, pact_gap_sem = mean_sem(baseline - pact_plus)
        family_gap_mean, family_gap_sem = mean_sem(baseline - values[best_family])
        pact_joint_mean, pact_joint_sem = mean_sem(pact - joint)
        calibration, cache, report = calibration_paths(args.root, backbone)
        calibration_report = json.loads(report.read_text(encoding="utf-8"))
        if int(calibration_report.get("incomplete_required_cells", -1)) != 0:
            raise AssertionError(f"Incomplete calibration: {report}")
        if int(calibration_report.get("live_profile_count", -1)) != 125:
            raise AssertionError(f"Calibration is not full-grid: {report}")
        actual_hash = sha256(calibration)
        if calibration_report.get("tensor_sha256") != actual_hash:
            raise AssertionError(f"Calibration hash mismatch: {calibration}")
        summaries.append(
            {
                "model": backbone.label,
                "model_snapshot": backbone.model,
                "pact_plus_regret_mean": method_stats["hpsmg_plus"][0],
                "pact_plus_regret_sem": method_stats["hpsmg_plus"][1],
                "pact_regret_mean": method_stats["hpsmg"][0],
                "pact_regret_sem": method_stats["hpsmg"][1],
                "joint_psrl_regret_mean": method_stats["joint_psrl"][0],
                "joint_psrl_regret_sem": method_stats["joint_psrl"][1],
                "llm_psrl_regret_mean": method_stats["llm_psrl_verbal"][0],
                "llm_psrl_regret_sem": method_stats["llm_psrl_verbal"][1],
                "best_pact_family_method": best_family,
                "best_pact_family_regret_mean": method_stats[best_family][0],
                "best_pact_family_regret_sem": method_stats[best_family][1],
                "best_llm_coordination_baseline": best_baseline,
                "best_baseline_regret_mean": method_stats[best_baseline][0],
                "best_baseline_regret_sem": method_stats[best_baseline][1],
                "pact_plus_ratio": method_stats[best_baseline][0] / method_stats["hpsmg_plus"][0] if method_stats["hpsmg_plus"][0] > 0 else float("inf"),
                "best_family_ratio": method_stats[best_baseline][0] / method_stats[best_family][0] if method_stats[best_family][0] > 0 else float("inf"),
                "paired_baseline_minus_pact_plus_mean": pact_gap_mean,
                "paired_baseline_minus_pact_plus_sem": pact_gap_sem,
                "paired_baseline_minus_best_family_mean": family_gap_mean,
                "paired_baseline_minus_best_family_sem": family_gap_sem,
                "paired_pact_minus_joint_mean": pact_joint_mean,
                "paired_pact_minus_joint_sem": pact_joint_sem,
                "calibration_snapshot_id": calibration_report["snapshot_id"],
                "calibration_sha256": actual_hash,
                "calibration_cache_cells": count_jsonl(cache),
                "calibration_parse_failures": int(calibration_report["parse_failure_count"]),
                "atom_tom0_regret_mean": method_stats["atom_tom0"][0],
                "atom_tom1_regret_mean": method_stats["atom_tom1"][0],
                "atom_tom2_regret_mean": method_stats["atom_tom2"][0],
                "econ_bne_regret_mean": method_stats["econ_bne"][0],
                "baseline_selection_rule": "minimum mean cumulative regret among fixed ECON-BNE and A-ToM-{0,1,2}",
                "matched_seeds": True,
                "seed_count": args.seeds,
                "K": args.K,
            }
        )
    return summaries


def plot_results(args: argparse.Namespace, backbones: list[Backbone], raw: dict[str, dict[str, np.ndarray]]) -> None:
    args.paper_fig_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 10.5,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 4.8), sharex=False)
    y = np.arange(len(PLOT_ORDER))
    for axis, backbone in zip(axes.ravel(), backbones):
        means = np.array([raw[backbone.label][algorithm].mean() for algorithm in PLOT_ORDER])
        sems = np.array([
            raw[backbone.label][algorithm].std(ddof=1) / math.sqrt(len(raw[backbone.label][algorithm]))
            for algorithm in PLOT_ORDER
        ])
        for index, method in enumerate(METHOD_ORDER):
            algorithm = PLOT_METHOD_MAP[method]
            axis.errorbar(
                means[index],
                index,
                xerr=sems[index],
                fmt=METHOD_MARKERS[method],
                markersize=5.0,
                color=METHOD_COLORS[method],
                markeredgecolor="white",
                markeredgewidth=0.55,
                elinewidth=1.0,
                capsize=2.0,
                zorder=3,
            )
        axis.axvline(0.0, color=ORACLE_COLOR, linestyle=ORACLE_LINESTYLE, linewidth=0.9, zorder=1)
        axis.set_yticks(y, [METHOD_LABELS[method] for method in METHOD_ORDER])
        axis.invert_yaxis()
        axis.set_title(backbone.label, loc="left", fontweight="bold", fontsize=10.2)
        axis.grid(axis="x", linestyle=":", linewidth=0.55, color="#d7d7d7")
        axis.set_axisbelow(True)
        axis.spines[["top", "right"]].set_visible(False)
        span = max(means + sems)
        for index, value in enumerate(means):
            axis.text(value + 0.018 * max(span, 1.0), index, f"{value:.2f}", va="center", fontsize=7.2)
        axis.set_xlim(-0.04 * max(span, 1.0), max(span * 1.20, 1.0))
        axis.tick_params(labelsize=7.7)
    fig.supxlabel(f"Cumulative Bayesian regret at $K={args.K}$ (mean $\\pm$ SEM; {args.seeds} common environments)", fontsize=9.0)
    fig.tight_layout(rect=(0, 0.04, 1, 1), w_pad=1.0, h_pad=0.9)
    for suffix in ("pdf", "png"):
        output = args.paper_fig_dir / f"fig_e_a_hp_spgg_matched.{suffix}"
        fig.savefig(output, dpi=220 if suffix == "png" else None, bbox_inches="tight")
    plt.close(fig)


def write_report(args: argparse.Namespace, backbones: list[Backbone], summaries: list[dict[str, object]]) -> None:
    lines = [
        "# E-A Environment-Matched HP-SPGG Control",
        "",
        f"Protocol: n=3, |Theta_i|=4, K={args.K}, {args.seeds} common seeds, beta={args.beta}. ",
        "Within each backbone every method uses the same complete 125-profile live tensor, true-type profile, uniform prior, no additional board state, and exact tensor oracle; each method receives its own realized-reward history from that tensor.",
        "",
        "| backbone | PACT+ | PACT | Joint-PSRL | LLM-PSRL | best coordination baseline | PACT+ ratio | best-family ratio |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summaries:
        lines.append(
            f"| {row['model']} | {float(row['pact_plus_regret_mean']):.3f} ± {float(row['pact_plus_regret_sem']):.3f} | "
            f"{float(row['pact_regret_mean']):.3f} ± {float(row['pact_regret_sem']):.3f} | "
            f"{float(row['joint_psrl_regret_mean']):.3f} ± {float(row['joint_psrl_regret_sem']):.3f} | "
            f"{float(row['llm_psrl_regret_mean']):.3f} ± {float(row['llm_psrl_regret_sem']):.3f} | "
            f"{DISPLAY[str(row['best_llm_coordination_baseline'])]} {float(row['best_baseline_regret_mean']):.3f} ± {float(row['best_baseline_regret_sem']):.3f} | "
            f"{float(row['pact_plus_ratio']):.2f}x | {float(row['best_family_ratio']):.2f}x |"
        )
    ratios = [float(row["best_family_ratio"]) for row in summaries]
    lines.extend(
        [
            "",
            f"Matched best-family ratio range: **{min(ratios):.2f}x–{max(ratios):.2f}x**.",
            "",
            "Ratios are ratios of per-backbone mean cumulative regrets. SEM uses sample standard deviation over the ten common seeds. "
            "The selected strongest coordination baseline is chosen by the lowest mean regret within ECON-BNE and A-ToM-{0,1,2}; paired gaps use the same seed indices.",
        ]
    )
    path = args.root / "e_a_matched_likelihood.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_latex_table(args: argparse.Namespace, summaries: list[dict[str, object]]) -> None:
    lines = [
        r"\begin{table*}[t]",
        r"\centering\scriptsize",
        r"\caption{Environment-matched HP-SPGG control ($K{=}20$, $10$ common seeds). Within each backbone every method shares the pinned full-grid live reward tensor, true-type profile, uniform prior, no additional board state, and exact tensor oracle; each receives its own realised-reward history from that tensor. Provider sampling seeds are unavailable; accepted responses are cache-pinned. Values are cumulative regret, mean $\pm$ SEM; the ratio is the strongest LLM-coordination baseline divided by the lower-regret PACT-family member.}",
        r"\label{tab:hp-spgg-matched}",
        r"\setlength{\tabcolsep}{3pt}",
        r"\begin{tabular}{lrrrrlr}",
        r"\toprule",
        r"Backbone & PACT$^+$ & PACT & Joint-PSRL & LLM-PSRL & Best coordination & Coord./best PACT \\",
        r"\midrule",
    ]
    for row in summaries:
        label = latex_escape(str(row["model"]))
        lines.append(
            f"{label} & ${float(row['pact_plus_regret_mean']):.3f}\\pm{float(row['pact_plus_regret_sem']):.3f}$ & "
            f"${float(row['pact_regret_mean']):.3f}\\pm{float(row['pact_regret_sem']):.3f}$ & "
            f"${float(row['joint_psrl_regret_mean']):.3f}\\pm{float(row['joint_psrl_regret_sem']):.3f}$ & "
            f"${float(row['llm_psrl_regret_mean']):.3f}\\pm{float(row['llm_psrl_regret_sem']):.3f}$ & "
            f"{DISPLAY[str(row['best_llm_coordination_baseline'])]} ${float(row['best_baseline_regret_mean']):.3f}\\pm{float(row['best_baseline_regret_sem']):.3f}$ & "
            f"${float(row['best_family_ratio']):.2f}\\times$ \\\\" 
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table*}"])
    (args.root / "e_a_matched_control_table.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "#": r"\#",
        "_": r"\_",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
        "$": r"\$",
    }
    return "".join(replacements.get(character, character) for character in text)


def aggregate(args: argparse.Namespace, backbones: list[Backbone]) -> None:
    if len(backbones) != 4:
        print("Warning: aggregate contains a subset of the four flagship backbones.")
    rows, raw = load_rows(args, backbones)
    summaries = summarize(args, backbones, rows, raw)
    write_csv(args.root / "e_a_matched_per_seed.csv", rows)
    write_csv(args.root / "e_a_matched_summary.csv", summaries)
    plot_results(args, backbones, raw)
    write_report(args, backbones, summaries)
    write_latex_table(args, summaries)

    accepted_calls = 0
    calibration_judge_cache_cells: dict[str, int] = {}
    verbal_response_cache_entries: dict[str, int] = {}
    external_response_cache_entries: dict[str, dict[str, int]] = {}
    external_parse_repairs = 0
    artifact_hashes: dict[str, str] = {}
    for backbone in backbones:
        calibration, calibration_cache, calibration_report = calibration_paths(args.root, backbone)
        native, verbal_cache = native_paths(args.root, backbone)
        calibration_judge_cache_cells[backbone.label] = count_jsonl(calibration_cache)
        verbal_response_cache_entries[backbone.label] = count_json_cache(verbal_cache)
        external_response_cache_entries[backbone.label] = {}
        accepted_calls += calibration_judge_cache_cells[backbone.label] + verbal_response_cache_entries[backbone.label]
        for path in (calibration, calibration_cache, calibration_report, native, verbal_cache):
            if path.exists():
                artifact_hashes[str(path)] = sha256(path)
        for algorithm in EXTERNAL_ALGORITHMS:
            output, cache, trace = external_paths(args.root, backbone, algorithm)
            external_response_cache_entries[backbone.label][algorithm] = count_json_cache(cache)
            accepted_calls += external_response_cache_entries[backbone.label][algorithm]
            if output.exists():
                with np.load(output, allow_pickle=True) as payload:
                    if "parse_repair_count" in payload.files:
                        external_parse_repairs += int(np.asarray(payload["parse_repair_count"]).item())
            for path in (output, cache, trace):
                if path.exists():
                    artifact_hashes[str(path)] = sha256(path)
    for path in sorted((args.root / "per_seed").glob("*/*.npz")):
        artifact_hashes[str(path)] = sha256(path)
    metadata = {
        "experiment": "E-A environment-matched HP-SPGG control",
        "status": "complete",
        "backbones": [backbone.label for backbone in backbones],
        "model_snapshots": {backbone.label: backbone.model for backbone in backbones},
        "n": 3,
        "type_count": 4,
        "K": args.K,
        "seeds": args.seeds,
        "seed_offset": args.seed_offset,
        "beta": args.beta,
        "matched_seed": True,
        "initial_state": "true types drawn IID-uniform per matched seed; uniform prior and no additional stochastic board state",
        "calibration": "complete 125-profile x 3-player x 4-persona live-judge tensor, one LLM-sampled score per cell, cache-pinned for deterministic replay",
        "oracle": "exact joint-action argmax on the same pinned tensor",
        "observation_sigma": 0.08,
        "provider_sampling_seed": "unavailable from the provider API; provider outputs are content-hash cache-pinned, not pathwise RNG-matched",
        "provider_temperature_constraints": {
            "Kimi-K2.6": "CloudGPT does not accept custom temperature for Kimi-K2.6; requested calibration/action temperatures are sent as temperature=1",
        },
        "response_replay": "persistent SHA-256-keyed raw response caches; resumed runs replay accepted responses",
        "strict_parsing": "no heuristic parse fallbacks; malformed JSON is accepted only after a cache-pinned format-repair call preserving the selected action",
        "strict_repair_template_sha256": strict_repair_template_sha256(),
        "external_parse_repairs": external_parse_repairs,
        "final_verbal_update": "skipped only after episode K because no subsequent decision consumes it",
        "calibration_judge_cache_cells": calibration_judge_cache_cells,
        "verbal_response_cache_entries": verbal_response_cache_entries,
        "external_response_cache_entries": external_response_cache_entries,
        "accepted_response_cache_entries": accepted_calls,
        "artifacts": artifact_hashes,
    }
    (args.root / "e_a_matched_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    ratios = [float(row["best_family_ratio"]) for row in summaries]
    print(json.dumps({"status": "complete", "rows": len(rows), "ratio_min": min(ratios), "ratio_max": max(ratios), "accepted_calls": accepted_calls}, indent=2))


def main() -> None:
    args = parse_args()
    backbones = selected_backbones(args.models)
    args.root.mkdir(parents=True, exist_ok=True)
    if args.stage in {"calibrate", "all"}:
        run_calibrations(args, backbones)
    if args.stage in {"run", "all"}:
        run_experiments(args, backbones)
    if args.stage in {"aggregate", "all"}:
        aggregate(args, backbones)


if __name__ == "__main__":
    main()
