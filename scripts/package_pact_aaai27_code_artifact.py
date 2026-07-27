"""Build the anonymous PACT AAAI-27 code, data, and paper artifact."""

from __future__ import annotations

import argparse
import csv
from datetime import date
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "packaged_results"
DEFAULT_NAME = "pact_aaai27_code_artifact_20260724"
SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
TEXT_SUFFIXES = {
    ".bib", ".bst", ".cfg", ".csv", ".json", ".jsonl", ".md", ".ps1",
    ".py", ".sty", ".tex", ".toml", ".txt", ".yaml", ".yml",
}
CODE_DIRS = (
    "llm_hpgg",
    "llm_hpgg_concordia",
    "llm_hpgg_sotopia",
    "llm_courier_dispatch",
    "llm_courier_dispatch_maassim",
)
FINAL_ANALYSIS_DIRS = {
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
    "hp_spgg_analytic_scaling",
    "hp_spgg_burn_in_v2_pilot",
    "hp_spgg_burn_in_v3_confirmatory",
}
SCRIPT_NAMES = {
    "analyze_concordia_haggling_joint_optimal_intervals.py",
    "analyze_concordia_haggling_true_oracle_focal.py",
    "analyze_e_c_sotopia_corrected.py",
    "analyze_hp_spgg_burn_in_support.py",
    "audit_e_a_matched_likelihood.py",
    "build_arr_submission.ps1",
    "compile_arr_paper.ps1",
    "dump_e1_3_lb_all_baselines.py",
    "extract_concordia_fig10_v7_data.py",
    "make_figures_v3_all.py",
    "make_fig_e1.py",
    "make_fig_e2.py",
    "make_fig_e3.py",
    "make_fig_scaling_combined.py",
    "maassim_rq2_parity.py",
    "package_pact_aaai27_rq_paper.py",
    "paper_comparison_methods.py",
    "plot_e1_1_llm_tier.py",
    "plot_e1_1_n_scaling.py",
    "plot_e1_3_lower_bound.py",
    "plot_e1_3_pf_isolation.py",
    "plot_e_b_iterated_concordia_v2.py",
    "plot_e_g_hp_spgg_component_ladder.py",
    "plot_fig6_e5_trajectories.py",
    "plot_fig7_native_vs_llm_baselines.py",
    "plot_fig_concordia_main_v4.py",
    "plot_fig_decentralized_price.py",
    "plot_fig_haggling_pareto.py",
    "plot_fig_sotopia_hard_v2.py",
    "plot_fig_sotopia_three_exp.py",
    "plot_fig_sotopia_traj.py",
    "plot_llm_psrl_verbal_figures.py",
    "plot_maassim_experiment_figures.py",
    "plot_maassim_main_figure.py",
    "replay_maassim_common_states.py",
    "replay_maassim_llm_smoke.py",
    "replay_maassim_pact_persona_mechanism.py",
    "render_scaling_v1.py",
    "render_hp_spgg_burn_in_v2_pilot.py",
    "render_hp_spgg_burn_in_v3_confirmatory.py",
    "run_aaai27_reviewer_experiments.py",
    "run_e1_1_llm_tier.py",
    "run_e1_1_n_scaling.py",
    "run_e1_3_lower_bound_sweep.py",
    "run_e1_3_pf_isolation.py",
    "run_e_a_matched_likelihood.py",
    "run_e_b_iterated_concordia.py",
    "run_e_d_reward_locality_violation.py",
    "run_e_e_maassim_tracker_parity.py",
    "run_e_f_maassim_bonus.py",
    "run_e_g_hp_spgg_component_ladder.py",
    "run_hp_spgg_analytic_scaling.py",
    "run_hp_spgg_burn_in_v2_pilot.py",
    "run_hp_spgg_burn_in_v3_confirmatory.py",
    "run_hp_spgg_deployment_robustness.py",
    "run_maassim_persona_v2_baselines.py",
    "run_maassim_shadow_smoke.py",
    "run_sotopia_menu_corruption_suite.py",
    "summarize_aaai27_reviewer_experiments.py",
    "summarize_e_b_iterated_concordia_v2_all_data.py",
    "summarize_maassim_baselines.py",
    "summarize_maassim_scenario_suite.py",
    "summarize_maassim_rq2_rq3_all_data.py",
    "summarize_pact_aaai27_supplemental_experiments.py",
    "summarize_hp_spgg_scaling_claim_a.py",
    "summarize_hp_spgg_claim_b_all_data.py",
    "validate_aaai27_reviewer_experiments.py",
    "validate_e_e_maassim_tracker_parity.py",
    "validate_e_b_iterated_concordia_v2.py",
    "validate_e_b_iterated_concordia_v2_all_data.py",
    "validate_e_f_maassim_bonus.py",
    "validate_e_g_hp_spgg_component_ladder.py",
    "validate_maassim_rq2_rq3_all_data.py",
    "validate_hp_spgg_analytic_scaling.py",
    "validate_hp_spgg_burn_in_v2_pilot.py",
    "validate_hp_spgg_burn_in_v3_confirmatory.py",
    "validate_hp_spgg_claim_b_all_data_md.py",
    "validate_hp_spgg_scaling_claim_a_md.py",
    "validate_main_paper_method_consistency.py",
    "validate_pact_aaai27_code_artifact.py",
    "validate_pact_aaai27_supplemental_experiments.py",
}
DOC_NAMES = {
    "concordia_structural_mapping.md",
    "reviewer_response_validity_applicability.md",
    "sotopia_structural_mapping.md",
}
PAPER_ROOT_FILES = {
    "aaai2027.bst",
    "aaai2027.sty",
    "appendix.tex",
    "main.bbl",
    "main.pdf",
    "main.tex",
    "PACT_AAAI27.pdf",
    "ref.bib",
    "ReproducibilityChecklist.tex",
}
SENSITIVE_REPLACEMENTS = (
    ("source_git_4280ade", "source_snapshot"),
    ("4280ade6ff1b5ed2ac9c18683fd3badd92f620b0", "historical_snapshot"),
    ("4280ade", "historical_snapshot"),
    (bytes.fromhex("37326639383862662d383666312d343161662d393161622d326437636430313164623437").decode(), "<PRIVATE_TENANT_ID_REMOVED>"),
    (bytes.fromhex("66656237623636312d636163372d343461382d386463312d313633623633633233646632").decode(), "<PRIVATE_APP_ID_REMOVED>"),
    (bytes.fromhex("68747470733a2f2f636c6f75646770742d6f70656e61692e617a7572652d6170692e6e65742f6f70656e61692f").decode(), "<PRIVATE_PROVIDER_ENDPOINT_REMOVED>"),
    (bytes.fromhex("636c6f75646770742d6f70656e61692e617a7572652d6170692e6e6574").decode(), "<PRIVATE_PROVIDER_ENDPOINT_REMOVED>"),
    (bytes.fromhex("762d73687571696e67736869").decode(), "<LOCAL_USER>"),
)
FORBIDDEN_BYTES = {
    bytes.fromhex("762d73687571696e67736869"): "local user name",
    bytes.fromhex("37326639383862662d383666312d343161662d393161622d326437636430313164623437"): "private tenant identifier",
    bytes.fromhex("66656237623636312d636163372d343461382d386463312d313633623633633233646632"): "private application identifier",
    bytes.fromhex("636c6f75646770742d6f70656e61692e617a7572652d6170692e6e6574"): "private provider endpoint",
    bytes.fromhex("4769744875622e636f70696c6f742d63686174"): "editor session path",
    bytes.fromhex("34323830616465"): "historical commit identifier",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_name(name: str) -> None:
    if not SAFE_NAME.fullmatch(name) or name in {".", ".."} or Path(name).name != name:
        raise ValueError(f"unsafe artifact name: {name!r}")


def require_file(path: Path) -> Path:
    if not path.is_file():
        raise FileNotFoundError(f"required artifact source is missing: {path}")
    return path


def sanitize_text(text: str) -> str:
    replacements = list(SENSITIVE_REPLACEMENTS)
    replacements.extend(
        (
            (str(ROOT), "<REPOSITORY_ROOT>"),
            (str(ROOT).replace("\\", "/"), "<REPOSITORY_ROOT>"),
        )
    )
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def destination_for(source: Path) -> Path:
    relative = source.relative_to(ROOT)
    parts = list(relative.parts)
    if "source_git_4280ade" in parts:
        parts[parts.index("source_git_4280ade")] = "source_snapshot"
    return Path(*parts)


def paper_figure_sources() -> list[Path]:
    source = "\n".join(
        (ROOT / "arr_paper" / filename).read_text(encoding="utf-8")
        for filename in ("main.tex", "appendix.tex")
    )
    names = sorted(set(re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", source)))
    paths = [ROOT / "arr_paper" / name for name in names]
    for path in paths:
        require_file(path)
    return paths


def selected_analysis_sources() -> list[Path]:
    analysis = ROOT / "analysis"
    sources: list[Path] = []
    for child in sorted(analysis.iterdir()):
        if child.is_file():
            sources.append(child)
        elif child.name in FINAL_ANALYSIS_DIRS:
            sources.extend(sorted(path for path in child.rglob("*") if path.is_file()))
    return [
        path
        for path in sources
        if path.relative_to(ROOT).as_posix()
        != "analysis/aaai27_supplemental_experiments/manifest.json"
    ]


def validate_source_release() -> None:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "validate_pact_aaai27_supplemental_experiments.py"),
        "--require-components",
        "--require-matched-e-a",
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    for path in (ROOT / "arr_paper" / "main.pdf", ROOT / "arr_paper" / "PACT_AAAI27.pdf"):
        require_file(path)


def write_generated_files(package_root: Path, name: str) -> None:
    readme = require_file(ROOT / "docs" / "PACT_AAAI27_CODE_ARTIFACT_README.md")
    (package_root / "README.md").write_text(sanitize_text(readme.read_text(encoding="utf-8")), encoding="utf-8")
    (package_root / "requirements.txt").write_text(
        "\n".join(
            (
                "# Base dependencies for offline validation and finite experiments",
                "numpy>=1.24",
                "matplotlib>=3.7",
                "networkx>=3.2",
                "",
                "# Public provider adapters (optional for offline validation)",
                "openai>=1.0",
                "anthropic>=0.39",
                "google-genai>=0.3",
                "",
            )
        ),
        encoding="utf-8",
    )
    (package_root / "pyproject.toml").write_text(
        "\n".join(
            (
                "[project]",
                'name = "pact-aaai27-artifact"',
                'version = "1.0.0"',
                'description = "Anonymous PACT AAAI-27 code and data artifact"',
                'requires-python = ">=3.11"',
                "dependencies = [",
                '  "numpy>=1.24",',
                '  "matplotlib>=3.7",',
                '  "networkx>=3.2",',
                "]",
                "",
                "[project.optional-dependencies]",
                'providers = ["openai>=1.0", "anthropic>=0.39", "google-genai>=0.3"]',
                "",
                "[tool.uv]",
                "package = false",
                "",
            )
        ),
        encoding="utf-8",
    )
    metadata = {
        "schema_version": "1.0",
        "artifact": name,
        "release_date": date.today().isoformat(),
        "anonymized": True,
        "network_calls_required_for_validation": False,
        "source_submission_sha256": sha256(ROOT / "arr_paper" / "PACT_AAAI27.pdf"),
        "source_full_paper_sha256": sha256(ROOT / "arr_paper" / "main.pdf"),
        "integrity_files": ["MANIFEST.csv", "SHA256SUMS.txt"],
    }
    (package_root / "ARTIFACT_METADATA.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    (package_root / "NOTICE.md").write_text(
        "# Artifact notice\n\n"
        "This anonymous research artifact is supplied for peer review and reproducibility evaluation. "
        "Third-party Concordia, SOTOPIA, MaaSSim, model weights, provider endpoints, and credentials are not redistributed. "
        "Use those dependencies under their respective licenses and terms.\n",
        encoding="utf-8",
    )


def build(name: str, force: bool) -> tuple[Path, Path, int]:
    validate_name(name)
    package_root = OUTPUT_DIR / name
    zip_path = OUTPUT_DIR / f"{name}.zip"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if package_root.exists():
        if not force:
            raise FileExistsError(package_root)
        shutil.rmtree(package_root)
    if zip_path.exists():
        if not force:
            raise FileExistsError(zip_path)
        zip_path.unlink()
    package_root.mkdir(parents=True)

    copied: dict[str, str] = {}

    def add(source: Path, category: str, destination: Path | None = None) -> None:
        source = require_file(source)
        destination = destination or destination_for(source)
        posix = destination.as_posix()
        pure = PurePosixPath(posix)
        if pure.is_absolute() or ".." in pure.parts:
            raise ValueError(f"unsafe package destination: {posix}")
        if posix in copied:
            raise RuntimeError(f"duplicate package destination: {posix}")
        target = package_root / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix.lower() in TEXT_SUFFIXES:
            text = source.read_text(encoding="utf-8-sig")
            target.write_text(sanitize_text(text), encoding="utf-8")
        else:
            shutil.copy2(source, target)
        copied[posix] = category

    write_generated_files(package_root, name)
    copied.update(
        {
            "README.md": "documentation",
            "requirements.txt": "environment",
            "pyproject.toml": "environment",
            "ARTIFACT_METADATA.json": "metadata",
            "NOTICE.md": "documentation",
        }
    )

    for directory in CODE_DIRS:
        for source in sorted((ROOT / directory).glob("*.py")):
            add(source, "implementation")
    for filename in sorted(SCRIPT_NAMES):
        add(ROOT / "scripts" / filename, "reproduction")
    add(
        ROOT / "arr_paper" / "figs" / "make_fig2_v15.py",
        "reproduction",
        Path("scripts/plot_concordia_selected_main.py"),
    )
    for filename in sorted(DOC_NAMES):
        add(ROOT / "docs" / filename, "documentation")
    for source in sorted((ROOT / "prompts").glob("*")):
        if source.is_file():
            add(source, "prompts")

    for filename in ("aaai27_sotopia_historical_comparators.csv", "aaai27_sotopia_input_manifest.csv"):
        add(ROOT / "config" / filename, "configuration")
    add(ROOT / "config" / "providers.yaml", "configuration", Path("config/providers.example.yaml"))
    for filename in ("benchmark_agents.json", "sotopia_hard_cases_cache.json"):
        add(ROOT / "external" / "sotopia_data_probe" / filename, "public-input-cache")

    for filename in sorted(PAPER_ROOT_FILES):
        add(ROOT / "arr_paper" / filename, "paper")
    for source in paper_figure_sources():
        add(source, "paper-figure")

    for source in selected_analysis_sources():
        add(source, "experiment-data")

    rows = []
    for path in sorted((path for path in package_root.rglob("*") if path.is_file()), key=lambda item: item.relative_to(package_root).as_posix()):
        relative = path.relative_to(package_root).as_posix()
        rows.append(
            {
                "category": copied[relative],
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    with (package_root / "MANIFEST.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["category", "path", "bytes", "sha256"])
        writer.writeheader()
        writer.writerows(rows)
    (package_root / "SHA256SUMS.txt").write_text(
        "\n".join(f"{row['sha256']}  {row['path']}" for row in rows) + "\n",
        encoding="utf-8",
    )

    for path in package_root.rglob("*"):
        if not path.is_file():
            continue
        payload = path.read_bytes().lower()
        for pattern, label in FORBIDDEN_BYTES.items():
            if pattern.lower() in payload:
                raise AssertionError(f"{label} found in {path.relative_to(package_root)}")

    subprocess.run(
        [sys.executable, str(package_root / "scripts" / "validate_pact_aaai27_code_artifact.py")],
        cwd=package_root,
        check=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )

    expected_archive_paths = {
        *(row["path"] for row in rows),
        "MANIFEST.csv",
        "SHA256SUMS.txt",
    }
    actual_archive_paths = {
        path.relative_to(package_root).as_posix()
        for path in package_root.rglob("*")
        if path.is_file()
    }
    if actual_archive_paths != expected_archive_paths:
        missing = sorted(expected_archive_paths - actual_archive_paths)
        extra = sorted(actual_archive_paths - expected_archive_paths)
        raise AssertionError(f"post-validation inventory mismatch: missing={missing[:5]} extra={extra[:5]}")

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted((path for path in package_root.rglob("*") if path.is_file()), key=lambda item: item.relative_to(OUTPUT_DIR).as_posix()):
            archive.write(path, path.relative_to(OUTPUT_DIR).as_posix())
    with zipfile.ZipFile(zip_path) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise RuntimeError(f"ZIP CRC validation failed at {bad}")
    return package_root, zip_path, len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default=DEFAULT_NAME)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--skip-source-validation", action="store_true")
    args = parser.parse_args()
    if not args.skip_source_validation:
        validate_source_release()
    package_root, zip_path, files = build(args.name, args.force)
    print(
        json.dumps(
            {
                "status": "ok",
                "package": package_root.relative_to(ROOT).as_posix(),
                "zip": zip_path.relative_to(ROOT).as_posix(),
                "files": files,
                "zip_bytes": zip_path.stat().st_size,
                "zip_sha256": sha256(zip_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
