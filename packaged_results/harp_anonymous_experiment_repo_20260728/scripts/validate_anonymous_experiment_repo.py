"""Validate the anonymous HARP code-and-experiment repository without network calls."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import re
import warnings


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "MANIFEST.csv"
SUMS = ROOT / "SHA256SUMS.txt"
INVENTORY_EXCLUSIONS = {"MANIFEST.csv", "SHA256SUMS.txt"}
FORBIDDEN_PARTS = {".git", ".github", ".venv", ".venvs", ".vscode", "__pycache__"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo", ".zip"}
FORBIDDEN_BYTES = {
    bytes.fromhex("762d73687571696e67736869"): "local user name",
    bytes.fromhex("73746576656e71696e67"): "repository owner identity",
    bytes.fromhex("54454d502e5245444d4f4e44"): "local profile name",
    bytes.fromhex("4769744875622e636f70696c6f742d63686174"): "editor session path",
    bytes.fromhex("636c6f75646770742d6f70656e61692e617a7572652d6170692e6e6574"): "private provider endpoint",
    bytes.fromhex("37326639383862662d383666312d343161662d393161622d326437636430313164623437"): "private tenant identifier",
    bytes.fromhex("66656237623636312d636163372d343461382d386463312d313633623633633233646632"): "private application identifier",
}
ABSOLUTE_WINDOWS_PATH = re.compile(rb"[A-Za-z]:\\Users\\[^\\\r\n]+", re.IGNORECASE)
EXPECTED_ANALYSIS_DIRS = {
    "aaai27_review",
    "aaai27_supplemental_experiments",
    "courier_dispatch_maassim",
    "e_a_matched_likelihood",
    "e_b_iterated_concordia",
    "e_c_sotopia_corrected",
    "e_d_reward_locality_violation",
    "e_d_reward_locality_violation_combined",
    "e_d_reward_locality_violation_live",
    "e_e_maassim_rq2",
    "e_f_maassim_bonus",
    "e_g_hp_spgg_component_ladder",
    "e_h_maassim_grouped_prior",
    "hp_spgg_analytic_scaling",
    "hp_spgg_burn_in_v2_pilot",
    "hp_spgg_burn_in_v3_confirmatory",
}
EXPECTED_FINGERPRINTS = {
    "artifacts/figures/fig_e_a_hp_spgg_matched_v16_data.json": "c6414c4277e0f2fbad243353e23e0df3400d78813d6c77b2979deacc527bed6a",
    "artifacts/figures/fig_maassim_combined_v22_data.json": "fe622b5be6165591aecdea1466b08bc69e7c4766366eb07480e0fb17ba30eb16",
}
EXPECTED_PREREG_SHA256 = {
    "analysis/e_h_maassim_grouped_prior/confirmatory_seed20_59_preregistration.json": "c0e6764fefe338212d6bc74c22717fd7d1cfda7dd0e917f782ad97eab6f011e2",
    "analysis/e_h_maassim_grouped_prior/group_size_seed20_59_preregistration.json": "737bc90045c187a4ff55d1c8ca9100f4961fa7f2aba7a05d3edf7850d8017a1c",
}


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
        raise FileNotFoundError("MANIFEST.csv and SHA256SUMS.txt are required")
    with MANIFEST.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or set(rows[0]) != {"category", "path", "bytes", "sha256"}:
        raise AssertionError("unexpected manifest schema")
    paths = [row["path"] for row in rows]
    if len(paths) != len(set(paths)):
        raise AssertionError("duplicate manifest path")
    actual = {
        relative(path)
        for path in ROOT.rglob("*")
        if path.is_file() and relative(path) not in INVENTORY_EXCLUSIONS
    }
    if set(paths) != actual:
        raise AssertionError(
            f"inventory mismatch: missing={sorted(set(paths)-actual)[:5]} "
            f"extra={sorted(actual-set(paths))[:5]}"
        )
    sums = {}
    for line in SUMS.read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        sums[name] = digest
    if set(sums) != set(paths):
        raise AssertionError("SHA256SUMS inventory differs from MANIFEST")
    total = 0
    for row in rows:
        path = ROOT / row["path"]
        digest = sha256(path)
        size = path.stat().st_size
        if size != int(row["bytes"]):
            raise AssertionError(f"size mismatch: {row['path']}")
        if digest != row["sha256"] or digest != sums[row["path"]]:
            raise AssertionError(f"hash mismatch: {row['path']}")
        total += size
    return len(rows), total


def validate_hygiene() -> int:
    checked = 0
    for path in ROOT.rglob("*"):
        rel = path.relative_to(ROOT)
        if any(part in FORBIDDEN_PARTS for part in rel.parts):
            raise AssertionError(f"forbidden repository path: {rel.as_posix()}")
        if not path.is_file():
            continue
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            raise AssertionError(f"forbidden generated/archive file: {rel.as_posix()}")
        payload = path.read_bytes()
        lower = payload.lower()
        for pattern, label in FORBIDDEN_BYTES.items():
            if pattern.lower() in lower:
                raise AssertionError(f"{label} found in {rel.as_posix()}")
        if ABSOLUTE_WINDOWS_PATH.search(payload):
            raise AssertionError(f"absolute Windows user path found in {rel.as_posix()}")
        checked += 1
    return checked


def validate_python() -> int:
    warnings.simplefilter("error", SyntaxWarning)
    paths = sorted(ROOT.rglob("*.py"))
    for path in paths:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
    return len(paths)


def csv_rows(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def validate_experiments() -> dict[str, object]:
    present = {path.name for path in (ROOT / "analysis").iterdir() if path.is_dir()}
    missing = sorted(EXPECTED_ANALYSIS_DIRS - present)
    if missing:
        raise AssertionError(f"missing primary experiment directories: {missing}")

    e_a_rows = csv_rows(
        ROOT / "analysis" / "e_a_matched_likelihood" / "matched_s10" / "e_a_matched_per_seed.csv"
    )
    if e_a_rows != 400:
        raise AssertionError(f"E-A has {e_a_rows} per-seed rows; expected 400")

    e_b_rows = csv_rows(
        ROOT / "analysis" / "e_b_iterated_concordia" / "e_b_iterated_concordia_per_seed.csv"
    )
    if e_b_rows != 4800:
        raise AssertionError(f"E-B has {e_b_rows} rows; expected 4800")

    e_h = ROOT / "analysis" / "e_h_maassim_grouped_prior"
    softmax = e_h / "k20_softmax_crn_confirm_seed20_59"
    deterministic = e_h / "k20_deterministic_crn_confirm_seed20_59"
    expected_softmax = {
        f"e_h_rho{rho}p0_g{group}_n8_m2_s40.npz"
        for rho in (0, 1)
        for group in (2, 4)
    }
    missing_softmax = sorted(name for name in expected_softmax if not (softmax / name).is_file())
    if missing_softmax:
        raise AssertionError(f"missing E-H softmax CRN cells: {missing_softmax}")
    expected_deterministic = {
        f"e_h_rho{rho}p0_g4_n8_m2_s40.npz" for rho in (0, 1)
    }
    missing_deterministic = sorted(
        name for name in expected_deterministic if not (deterministic / name).is_file()
    )
    if missing_deterministic:
        raise AssertionError(f"missing E-H deterministic confirmatory cells: {missing_deterministic}")

    for raw, expected in EXPECTED_PREREG_SHA256.items():
        actual = sha256(ROOT / raw)
        if actual != expected:
            raise AssertionError(f"preregistration hash mismatch: {raw}: {actual}")

    fingerprints = {}
    for raw, expected in EXPECTED_FINGERPRINTS.items():
        payload = json.loads((ROOT / raw).read_text(encoding="utf-8"))
        actual = payload.get("numeric_payload_sha256")
        if actual != expected:
            raise AssertionError(f"figure data fingerprint mismatch: {raw}: {actual}")
        fingerprints[raw] = actual

    return {
        "analysis_directories": len(present),
        "e_a_per_seed_rows": e_a_rows,
        "e_b_episode_rows": e_b_rows,
        "e_h_softmax_crn_cells": len(expected_softmax),
        "e_h_deterministic_confirmatory_cells": len(expected_deterministic),
        "figure_data_fingerprints": fingerprints,
    }


def main() -> None:
    files, total_bytes = validate_inventory()
    hygiene_files = validate_hygiene()
    python_files = validate_python()
    experiments = validate_experiments()
    required = (
        ROOT / "README.md",
        ROOT / "REPOSITORY_METADATA.json",
        ROOT / "NOTICE.md",
    )
    for path in required:
        if not path.is_file() or path.stat().st_size == 0:
            raise AssertionError(f"missing required repository file: {relative(path)}")
    print(json.dumps({
        "status": "ok",
        "manifest_files": files,
        "manifest_bytes": total_bytes,
        "hygiene_files_checked": hygiene_files,
        "python_files_compiled": python_files,
        "experiments": experiments,
    }, indent=2))


if __name__ == "__main__":
    main()
