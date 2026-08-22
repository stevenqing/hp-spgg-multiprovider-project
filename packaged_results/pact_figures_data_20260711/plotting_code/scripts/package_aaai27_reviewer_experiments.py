"""Package PACT AAAI-27 reviewer experiment outputs and reproduction code."""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NAME = "pact_aaai27_reviewer_experiments_20260714"
SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def require_file(path: Path) -> Path:
    if not path.is_file():
        raise FileNotFoundError(f"required artifact source is missing: {path}")
    return path


def validate_name(name: str) -> None:
    if not SAFE_NAME.fullmatch(name) or name in {".", ".."} or Path(name).name != name:
        raise ValueError(f"unsafe artifact name: {name!r}")


def require_clean_tree() -> None:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or result.stdout.strip():
        raise RuntimeError("refusing to package a dirty tracked/untracked Git tree")


def validate_release() -> None:
    for script in (
        ROOT / "scripts" / "summarize_aaai27_reviewer_experiments.py",
        ROOT / "scripts" / "validate_aaai27_reviewer_experiments.py",
    ):
        subprocess.run([sys.executable, str(script)], cwd=ROOT, check=True)


def build(name: str, force: bool) -> tuple[Path, Path, list[dict[str, object]]]:
    validate_name(name)
    output_root = ROOT / "packaged_results"
    package_root = output_root / name
    zip_path = output_root / f"{name}.zip"
    resolved_output = output_root.resolve()
    if package_root.resolve().parent != resolved_output or zip_path.resolve().parent != resolved_output:
        raise ValueError(f"artifact path escapes packaged_results: {name!r}")
    if package_root.exists():
        if not force:
            raise FileExistsError(package_root)
        shutil.rmtree(package_root)
    if zip_path.exists():
        if not force:
            raise FileExistsError(zip_path)
        zip_path.unlink()
    package_root.mkdir(parents=True)

    sources: list[tuple[Path, Path, str]] = []

    def add(source: Path, category: str) -> None:
        source = require_file(source)
        sources.append((source, source.relative_to(ROOT), category))

    data_root = ROOT / "analysis" / "aaai27_review"
    for filename in (
        "PACT_AAAI27_REVIEWER_EXPERIMENTS.md",
        "e_r0_maassim_per_seed.csv",
        "e_r1_noise_analytic_mixed.csv",
        "e_r2_expansion_analytic_mixed.csv",
        "e_r2_loo_analytic_mixed.csv",
        "e_r3_menu_corruption.csv",
        "e_r4_planner_concordia.csv",
    ):
        require_file(data_root / filename)
    expected_raw = {
        data_root / "e_r3_raw" / f"p{str(p).replace('.', 'p')}_r{replicate}.json"
        for p in (0.0, 0.1, 0.2, 0.3)
        for replicate in range(4)
    }
    actual_raw = set((data_root / "e_r3_raw").glob("p*_r*.json"))
    if actual_raw != expected_raw:
        raise RuntimeError(
            f"unexpected E-R3 raw inventory: missing={sorted(str(path) for path in expected_raw - actual_raw)} "
            f"extra={sorted(str(path) for path in actual_raw - expected_raw)}"
        )
    for source in sorted(path for path in data_root.rglob("*") if path.is_file()):
        add(source, "data")

    maassim_root = ROOT / "analysis" / "courier_dispatch_maassim"
    for filename in ("maassim_llm_scenario_suite_detail.csv", "maassim_llm_scenario_suite_summary.csv"):
        add(maassim_root / filename, "data")
    for seed in range(5):
        for suffix in ("personas.json", "queue_snapshots.jsonl"):
            add(maassim_root / f"nearest_persona_v2_main_s{seed}_{suffix}", "data")
    for source in (
        ROOT / "analysis" / "sotopia_tuned_all70_full_report.md",
        ROOT / "packaged_results" / "sotopia_font13_recovered_aggregates.json",
        ROOT / "external" / "sotopia_data_probe" / "benchmark_agents.json",
        ROOT / "external" / "sotopia_data_probe" / "sotopia_hard_cases_cache.json",
        ROOT / "config" / "aaai27_sotopia_historical_comparators.csv",
        ROOT / "config" / "aaai27_sotopia_input_manifest.csv",
    ):
        add(source, "data")

    for relative in (
        "scripts/run_aaai27_reviewer_experiments.py",
        "scripts/run_sotopia_menu_corruption_suite.py",
        "scripts/summarize_aaai27_reviewer_experiments.py",
        "scripts/validate_aaai27_reviewer_experiments.py",
        "scripts/package_aaai27_reviewer_experiments.py",
        "scripts/replay_maassim_llm_smoke.py",
        "scripts/replay_maassim_pact_persona_mechanism.py",
        "pyproject.toml",
        "requirements.txt",
        "llm_hpgg_sotopia/agents.py",
        "llm_hpgg_sotopia/run_sotopia_hard_official.py",
        "docs/sotopia_structural_mapping.md",
        "docs/data_provenance.md",
    ):
        add(ROOT / relative, "reproduction")
    included_destinations = {destination for _, destination, _ in sources}
    for module_root in sorted(path for path in ROOT.glob("llm_*") if path.is_dir()):
        for source in sorted(module_root.rglob("*.py")):
            if "__pycache__" in source.parts:
                continue
            destination = source.relative_to(ROOT)
            if destination not in included_destinations:
                sources.append((source, destination, "reproduction"))
                included_destinations.add(destination)

    destinations = [destination for _, destination, _ in sources]
    if len(destinations) != len(set(destinations)):
        duplicates = sorted({path.as_posix() for path in destinations if destinations.count(path) > 1})
        raise RuntimeError(f"duplicate package destinations: {duplicates}")

    manifest: list[dict[str, object]] = []
    for source, destination, category in sources:
        target = package_root / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        manifest.append(
            {
                "category": category,
                "package_path": destination.as_posix(),
                "source_path": source.relative_to(ROOT).as_posix(),
                "bytes": target.stat().st_size,
                "sha256": sha256(target),
            }
        )
    manifest.sort(key=lambda row: (str(row["category"]), str(row["package_path"])))
    with (package_root / "MANIFEST.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["category", "package_path", "source_path", "bytes", "sha256"])
        writer.writeheader()
        writer.writerows(manifest)
    (package_root / "SHA256SUMS.txt").write_text(
        "\n".join(f"{row['sha256']}  {row['package_path']}" for row in manifest) + "\n",
        encoding="utf-8",
    )
    (package_root / "README.md").write_text(
        "\n".join(
            [
                "# PACT AAAI-27 Reviewer Experiment Artifact",
                "",
                f"Generated from code commit `{git_commit()}` with a clean Git tree; ignored experiment data are identified by `MANIFEST.csv` hashes.",
                "",
                "- `analysis/aaai27_review/`: consolidated report, requested CSVs, and SOTOPIA raw checkpoints.",
                "- `analysis/courier_dispatch_maassim/`: fixed E-R0 snapshots/personas and retained aggregate comparator.",
                "- `analysis/sotopia_tuned_all70_full_report.md` and `config/aaai27_sotopia_historical_comparators.csv`: E-R3 comparator provenance.",
                "- `external/sotopia_data_probe/`: public metadata and reconstructed 70-case cache; the 180 MB public JSONL is referenced by SHA-256 in the report.",
                "- `scripts/`, `llm_*/`, `docs/`, `pyproject.toml`, and `requirements.txt`: reproduction code and documentation at their repository-relative paths.",
                "- `MANIFEST.csv` and `SHA256SUMS.txt`: source mapping and integrity.",
                "",
                "Run the summarizer and validator from this artifact root. E-R3 requires SOTOPIA 0.1.5 on Python 3.12 (the completed run pinned `litellm==1.80.11`); E-R4 requires the public google-deepmind/concordia checkout compatible with gdm-concordia 2.4.0 under `external/concordia`. The public source-data URLs and input hashes are in the consolidated report.",
                "",
                "The report distinguishes completed experiments from infrastructure-blocked requests and must be read before interpreting the CSVs. Mutable/provider decision caches are intentionally excluded; E-R0 records the cache-hit/live-fill counts and is a provenance-labelled reconstruction, not recovery of deleted original seed rows.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    shutil.make_archive(str(output_root / name), "zip", root_dir=output_root, base_dir=name)
    return package_root, zip_path, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default=DEFAULT_NAME)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    validate_release()
    require_clean_tree()
    package_root, zip_path, manifest = build(args.name, args.force)
    print(f"package={package_root.relative_to(ROOT)}")
    print(f"zip={zip_path.relative_to(ROOT)}")
    print(f"files={len(manifest)}")
    print(f"zip_mb={zip_path.stat().st_size / (1024 * 1024):.2f}")
    with zipfile.ZipFile(zip_path) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("ZIP CRC validation failed")


if __name__ == "__main__":
    main()
