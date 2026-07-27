"""Validate a packaged PACT AAAI-27 code and data artifact.

Run this script from an extracted artifact. It checks the package inventory,
SHA-256 digests, anonymity-sensitive byte patterns, and the E-A--E-D release
grids without making network or provider calls.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "MANIFEST.csv"
SUMS = ROOT / "SHA256SUMS.txt"
INVENTORY_EXCLUSIONS = {"MANIFEST.csv", "SHA256SUMS.txt"}
FORBIDDEN_PARTS = {".git", ".venv", ".venvs", "__pycache__"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo"}
FORBIDDEN_BYTES = {
    bytes.fromhex("762d73687571696e67736869"): "local user name",
    bytes.fromhex("37326639383862662d383666312d343161662d393161622d326437636430313164623437"): "private tenant identifier",
    bytes.fromhex("66656237623636312d636163372d343461382d386463312d313633623633633233646632"): "private application identifier",
    bytes.fromhex("636c6f75646770742d6f70656e61692e617a7572652d6170692e6e6574"): "private provider endpoint",
    bytes.fromhex("4769744875622e636f70696c6f742d63686174"): "editor session path",
    bytes.fromhex("34323830616465"): "historical commit identifier",
}
VALIDATION_ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def validate_inventory() -> tuple[int, int]:
    if not MANIFEST.is_file() or not SUMS.is_file():
        raise FileNotFoundError("MANIFEST.csv and SHA256SUMS.txt must be at the artifact root")

    with MANIFEST.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required_columns = {"category", "path", "bytes", "sha256"}
    if not rows or set(rows[0]) != required_columns:
        raise AssertionError(f"unexpected manifest schema: {set(rows[0]) if rows else set()}")

    manifest_paths = [row["path"] for row in rows]
    if len(manifest_paths) != len(set(manifest_paths)):
        raise AssertionError("manifest contains duplicate paths")
    for raw in manifest_paths:
        path = Path(raw)
        if path.is_absolute() or ".." in path.parts or "\\" in raw:
            raise AssertionError(f"unsafe manifest path: {raw}")

    actual_paths = {
        relative(path)
        for path in ROOT.rglob("*")
        if path.is_file() and relative(path) not in INVENTORY_EXCLUSIONS
    }
    if set(manifest_paths) != actual_paths:
        missing = sorted(set(manifest_paths) - actual_paths)
        extra = sorted(actual_paths - set(manifest_paths))
        raise AssertionError(f"inventory mismatch: missing={missing[:5]} extra={extra[:5]}")

    expected_sums: dict[str, str] = {}
    for line in SUMS.read_text(encoding="utf-8").splitlines():
        digest, raw_path = line.split("  ", 1)
        expected_sums[raw_path] = digest
    if set(expected_sums) != set(manifest_paths):
        raise AssertionError("SHA256SUMS inventory differs from MANIFEST.csv")

    total_bytes = 0
    for row in rows:
        path = ROOT / row["path"]
        size = path.stat().st_size
        digest = sha256(path)
        if size != int(row["bytes"]):
            raise AssertionError(f"size mismatch: {row['path']}")
        if digest != row["sha256"] or digest != expected_sums[row["path"]]:
            raise AssertionError(f"SHA-256 mismatch: {row['path']}")
        total_bytes += size
    return len(rows), total_bytes


def validate_hygiene() -> None:
    for path in ROOT.rglob("*"):
        if any(part in FORBIDDEN_PARTS for part in path.parts) or path.suffix.lower() in FORBIDDEN_SUFFIXES:
            raise AssertionError(f"forbidden generated/private path: {relative(path)}")
        if not path.is_file():
            continue
        payload = path.read_bytes()
        for pattern, label in FORBIDDEN_BYTES.items():
            if pattern.lower() in payload.lower():
                raise AssertionError(f"{label} found in {relative(path)}")


def validate_experiments() -> dict[str, object]:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "validate_pact_aaai27_supplemental_experiments.py"),
        "--require-components",
        "--require-matched-e-a",
    ]
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        env=VALIDATION_ENV,
    )
    experiments = json.loads(result.stdout)
    scaling_summary = ROOT / "analysis" / "hp_spgg_analytic_scaling" / "scaling_summary.csv"
    if scaling_summary.exists():
        scaling_result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_hp_spgg_analytic_scaling.py")],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            env=VALIDATION_ENV,
        )
        experiments["analytic_scaling"] = json.loads(scaling_result.stdout)
        claim_a_report = ROOT / "analysis" / "hp_spgg_analytic_scaling" / "claim_a_parity_feasibility_all_data.md"
        if claim_a_report.exists():
            claim_a_result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "validate_hp_spgg_scaling_claim_a_md.py")],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
                env=VALIDATION_ENV,
            )
            experiments["analytic_scaling_claim_a_markdown"] = json.loads(claim_a_result.stdout)
    pilot_summary = ROOT / "analysis" / "hp_spgg_burn_in_v2_pilot" / "burn_in_v2_summary.csv"
    if pilot_summary.exists():
        pilot_result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_hp_spgg_burn_in_v2_pilot.py")],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            env=VALIDATION_ENV,
        )
        experiments["burn_in_v2_pilot"] = json.loads(pilot_result.stdout)
    confirmatory_results = ROOT / "analysis" / "hp_spgg_burn_in_v3_confirmatory" / "confirmatory_results.json"
    if confirmatory_results.exists():
        confirmatory_result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_hp_spgg_burn_in_v3_confirmatory.py")],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            env=VALIDATION_ENV,
        )
        experiments["burn_in_v3_confirmatory"] = json.loads(confirmatory_result.stdout)
        claim_b_all_data = ROOT / "analysis" / "hp_spgg_burn_in_v3_confirmatory" / "claim_b_all_data.md"
        if claim_b_all_data.exists():
            claim_b_result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "validate_hp_spgg_claim_b_all_data_md.py")],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
                env=VALIDATION_ENV,
            )
            experiments["claim_b_all_data_markdown"] = json.loads(claim_b_result.stdout)
    return experiments


def main() -> None:
    files, total_bytes = validate_inventory()
    validate_hygiene()
    experiments = validate_experiments()
    required = (
        ROOT / "README.md",
        ROOT / "arr_paper" / "PACT_AAAI27.pdf",
        ROOT / "arr_paper" / "main.pdf",
    )
    for path in required:
        if not path.is_file() or path.stat().st_size == 0:
            raise AssertionError(f"missing required release file: {relative(path)}")
    print(
        json.dumps(
            {
                "status": "ok",
                "manifest_files": files,
                "manifest_bytes": total_bytes,
                "experiments": experiments,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()