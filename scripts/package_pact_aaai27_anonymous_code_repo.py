"""Build a code-only anonymous repository ZIP for the PACT AAAI-27 submission."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import warnings
import zipfile

from package_pact_aaai27_code_artifact import SCRIPT_NAMES


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "packaged_results"
DEFAULT_NAME = "pact_aaai27_anonymous_code_repo_20260724"
SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SOURCE_DIRS = (
    "llm_hpgg",
    "llm_hpgg_com",
    "llm_hpgg_concordia",
    "llm_hpgg_sotopia",
    "llm_courier_dispatch",
    "llm_courier_dispatch_maassim",
)
EXCLUDED_SCRIPTS = {
    "build_arr_submission.ps1",
    "compile_arr_paper.ps1",
    "package_pact_aaai27_rq_paper.py",
    "validate_pact_aaai27_code_artifact.py",
}
TEXT_REPLACEMENTS = (
    ("source_git_4280ade", "source_snapshot"),
    ("4280ade6ff1b5ed2ac9c18683fd3badd92f620b0", "historical_snapshot"),
    ("4280ade", "historical_snapshot"),
    ("llm_agent_cloudgpt", "llm_agent_managed"),
    ("cloudgpt_model", "managed_model"),
    ("CLOUDGPT", "MANAGED_PROVIDER"),
    ("CloudGPT", "ManagedProvider"),
    ("cloudgpt", "managed"),
)
FORBIDDEN_BYTES = {
    bytes.fromhex("762d73687571696e67736869"): "local user name",
    bytes.fromhex("37326639383862662d383666312d343161662d393161622d326437636430313164623437"): "private tenant identifier",
    bytes.fromhex("66656237623636312d636163372d343461382d386463312d313633623633633233646632"): "private application identifier",
    bytes.fromhex("636c6f75646770742d6f70656e61692e617a7572652d6170692e6e6574"): "private provider endpoint",
    bytes.fromhex("4769744875622e636f70696c6f742d63686174"): "editor session path",
    bytes.fromhex("34323830616465"): "historical commit identifier",
    bytes.fromhex("636c6f7564677074"): "private provider alias",
}
FORBIDDEN_TOP_LEVEL = {
    ".git",
    ".github",
    ".venv",
    ".venvs",
    "analysis",
    "arr_paper",
    "external",
    "figs",
    "logs",
    "packaged_results",
    "results",
}
FORBIDDEN_SUFFIXES = {
    ".aux", ".blg", ".log", ".npy", ".npz", ".pdf", ".png", ".pyc", ".pyo", ".zip",
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
        raise FileNotFoundError(path)
    return path


def transform_text(text: str) -> str:
    text = text.removeprefix("\ufeff")
    for old, new in TEXT_REPLACEMENTS:
        text = text.replace(old, new)
    for root_text in (str(ROOT), str(ROOT).replace("\\", "/")):
        text = text.replace(root_text, "<REPOSITORY_ROOT>")
    return text


def destination_for(source: Path) -> Path:
    relative = source.relative_to(ROOT)
    parts = [part.replace("cloudgpt", "managed") for part in relative.parts]
    return Path(*parts)


def generated_readme(package_root: Path) -> None:
    source = require_file(ROOT / "docs" / "PACT_AAAI27_ANONYMOUS_CODE_REPO_README.md")
    (package_root / "README.md").write_text(transform_text(source.read_text(encoding="utf-8-sig")), encoding="utf-8")


def generated_environment(package_root: Path) -> None:
    requirements = """# Core and plotting dependencies
numpy>=1.24
matplotlib>=3.7
networkx>=3.2

# Public and generic managed-provider adapters
openai>=1.0
anthropic>=0.39
google-genai>=0.3
azure-identity>=1.17
azure-identity-broker>=1.1; sys_platform == "win32"
msal>=1.28
"""
    (package_root / "requirements.txt").write_text(requirements, encoding="utf-8")
    pyproject = """[project]
name = "pact-anonymous"
version = "1.0.0"
description = "Anonymous PACT multi-agent coordination implementation"
requires-python = ">=3.11"
dependencies = [
  "numpy>=1.24",
  "matplotlib>=3.7",
  "networkx>=3.2",
  "openai>=1.0",
  "anthropic>=0.39",
  "google-genai>=0.3",
  "azure-identity>=1.17",
  "azure-identity-broker>=1.1; sys_platform == 'win32'",
  "msal>=1.28",
]

[tool.uv]
package = false
"""
    (package_root / "pyproject.toml").write_text(pyproject, encoding="utf-8")
    gitignore = """# Python
.venv/
.venvs/
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/

# Secrets and local configuration
.env
.env.*
!config/providers.example.yaml
*.pem
*.key

# Generated experiments and figures
analysis/
figs/
logs/
results/
results_phase2/
*.npy
*.npz
*.pdf
*.png
*.gif
*.zip

# Third-party checkouts
external/

# Editor and OS state
.vscode/
.idea/
.DS_Store
Thumbs.db
"""
    (package_root / ".gitignore").write_text(gitignore, encoding="utf-8")
    notice = (
        "# Anonymous submission notice\n\n"
        "This code-only repository is supplied for anonymous peer review and reproducibility evaluation. "
        "Third-party software, datasets, model outputs, provider configuration, and credentials are not redistributed.\n"
    )
    (package_root / "NOTICE.md").write_text(notice, encoding="utf-8")


def validate_tree(package_root: Path) -> dict[str, int]:
    present_top_level = {path.name for path in package_root.iterdir()}
    forbidden = sorted(present_top_level & FORBIDDEN_TOP_LEVEL)
    if forbidden:
        raise AssertionError(f"forbidden top-level paths: {forbidden}")

    python_files = sorted(package_root.rglob("*.py"))
    if not python_files:
        raise AssertionError("no Python source files were packaged")
    warnings.simplefilter("error", SyntaxWarning)
    for path in python_files:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")

    total_bytes = 0
    file_count = 0
    for path in package_root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(package_root)
        if "__pycache__" in relative.parts or path.suffix.lower() in FORBIDDEN_SUFFIXES:
            raise AssertionError(f"generated/binary file in code repository: {relative.as_posix()}")
        payload = path.read_bytes().lower()
        for pattern, label in FORBIDDEN_BYTES.items():
            if pattern.lower() in payload:
                raise AssertionError(f"{label} found in {relative.as_posix()}")
        total_bytes += path.stat().st_size
        file_count += 1

    environment = os.environ.copy()
    environment["LLM_HPGG_OFFLINE"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    smoke = subprocess.run(
        [sys.executable, "-m", "llm_hpgg.smoke_test"],
        cwd=package_root,
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )
    smoke_payload = json.loads(smoke.stdout)
    judge_payload = json.loads(smoke_payload["judge_reply"])
    if "offline smoke test" not in smoke_payload["player_reply"] or judge_payload.get("score") != 0.75:
        raise AssertionError(f"unexpected offline smoke output: {smoke.stdout}")
    subprocess.run(
        [sys.executable, "-m", "llm_hpgg.run_experiment", "--help"],
        cwd=package_root,
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )
    generated = sorted(package_root.rglob("*.pyc")) + sorted(package_root.rglob("__pycache__"))
    if generated:
        raise AssertionError(f"validation generated bytecode inside the repository: {generated[:3]}")
    return {"files": file_count, "python_files": len(python_files), "bytes": total_bytes}


def build(name: str, force: bool) -> tuple[Path, Path, dict[str, int]]:
    validate_name(name)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    package_root = OUTPUT_DIR / name
    zip_path = OUTPUT_DIR / f"{name}.zip"
    checksum_path = OUTPUT_DIR / f"{name}.zip.sha256"
    if package_root.exists():
        if not force:
            raise FileExistsError(package_root)
        shutil.rmtree(package_root)
    for path in (zip_path, checksum_path):
        if path.exists():
            if not force:
                raise FileExistsError(path)
            path.unlink()
    package_root.mkdir(parents=True)

    destinations: set[str] = set()

    def add(source: Path, destination: Path | None = None) -> None:
        source = require_file(source)
        destination = destination or destination_for(source)
        posix = destination.as_posix()
        pure = PurePosixPath(posix)
        if pure.is_absolute() or ".." in pure.parts or posix in destinations:
            raise ValueError(f"unsafe or duplicate destination: {posix}")
        target = package_root / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(transform_text(source.read_text(encoding="utf-8-sig")), encoding="utf-8")
        destinations.add(posix)

    generated_readme(package_root)
    generated_environment(package_root)
    destinations.update({"README.md", "requirements.txt", "pyproject.toml", ".gitignore", "NOTICE.md"})

    for directory in SOURCE_DIRS:
        for source in sorted((ROOT / directory).glob("*.py")):
            add(source)
    for filename in sorted(SCRIPT_NAMES - EXCLUDED_SCRIPTS):
        if filename.endswith(".py"):
            add(ROOT / "scripts" / filename)
    add(
        ROOT / "arr_paper" / "figs" / "make_fig2_v15.py",
        Path("scripts/plot_concordia_selected_main.py"),
    )
    for source in sorted((ROOT / "prompts").glob("*")):
        if source.is_file():
            add(source)
    add(ROOT / "config" / "providers.yaml", Path("config/providers.example.yaml"))

    stats = validate_tree(package_root)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(
            (path for path in package_root.rglob("*") if path.is_file()),
            key=lambda item: item.relative_to(OUTPUT_DIR).as_posix(),
        ):
            archive.write(path, path.relative_to(OUTPUT_DIR).as_posix())
    with zipfile.ZipFile(zip_path) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise RuntimeError(f"ZIP CRC validation failed at {bad}")
        names = archive.namelist()
        if any("/.git/" in f"/{name}/" or "/analysis/" in f"/{name}/" for name in names):
            raise AssertionError("ZIP contains Git metadata or experiment data")
    digest = sha256(zip_path)
    checksum_path.write_text(f"{digest}  {zip_path.name}\n", encoding="utf-8")
    stats["zip_bytes"] = zip_path.stat().st_size
    return package_root, zip_path, stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default=DEFAULT_NAME)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    package_root, zip_path, stats = build(args.name, args.force)
    print(
        json.dumps(
            {
                "status": "ok",
                "repository": package_root.relative_to(ROOT).as_posix(),
                "zip": zip_path.relative_to(ROOT).as_posix(),
                "zip_sha256": sha256(zip_path),
                **stats,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
