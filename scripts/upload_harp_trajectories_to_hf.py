"""Publish canonical project-generated trajectories to Hugging Face."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from huggingface_hub import HfApi


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
ALLOWED_SUFFIXES = {".json", ".jsonl", ".npz"}
NAME_PATTERN = re.compile(
    r"(trace|traject|rollout|episode|transcript|messages?|queue_snapshots|"
    r"histor|conversation|\.cache(?:\.|$)|_cache\.jsonl$)",
    re.IGNORECASE,
)
SCHEMA_PATTERN = re.compile(
    rb'"(transcript|trace|episodes|messages|replies|vehicle_queue|request_queue|'
    rb'generation_audit)"\s*:'
)
SECRET_PATTERNS = {
    "private_key": re.compile(
        rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    ),
    "github_token": re.compile(
        rb"(?:github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,})"
    ),
    "openai_style_key": re.compile(rb"sk-[A-Za-z0-9_-]{20,}"),
    "aws_access_key": re.compile(rb"AKIA[0-9A-Z]{16}"),
    "google_api_key": re.compile(rb"AIza[0-9A-Za-z_-]{30,}"),
}


@dataclass(frozen=True)
class TrajectoryFile:
    source: Path
    relative_path: Path
    category: str
    selected_by: str
    size_bytes: int
    sha256: str


def classify(relative_path: str) -> str:
    name = Path(relative_path).name.lower()
    if "queue_snapshots" in relative_path:
        return "queue_snapshots"
    if "/e_r3_raw/" in relative_path:
        return "sotopia_transcripts"
    if name.endswith("trace.json") or ".trace.json" in name:
        return "step_traces"
    if "cache" in name:
        return "llm_response_caches"
    if "message" in relative_path.lower():
        return "message_records"
    if "episode" in relative_path.lower():
        return "episode_records"
    return "schema_detected_records"


def inventory() -> tuple[list[TrajectoryFile], list[tuple[str, str]]]:
    candidates: list[tuple[Path, str]] = []
    for path in sorted(ANALYSIS.rglob("*")):
        if (
            not path.is_file()
            or "__pycache__" in path.parts
            or path.suffix.lower() not in ALLOWED_SUFFIXES
        ):
            continue
        relative_path = path.relative_to(ROOT).as_posix()
        selected_by = ""
        if NAME_PATTERN.search(relative_path) or "/e_r3_raw/" in relative_path:
            selected_by = "name_or_path"
        elif path.suffix.lower() in {".json", ".jsonl"}:
            with path.open("rb") as handle:
                if SCHEMA_PATTERN.search(handle.read(262_144)):
                    selected_by = "record_schema"
        if selected_by:
            candidates.append((path, selected_by))

    retained: list[TrajectoryFile] = []
    duplicates: list[tuple[str, str]] = []
    canonical_by_hash: dict[str, str] = {}
    for path, selected_by in candidates:
        content = path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        relative_path = path.relative_to(ROOT)
        relative_posix = relative_path.as_posix()
        canonical = canonical_by_hash.get(digest)
        if canonical is not None:
            duplicates.append((relative_posix, canonical))
            continue
        canonical_by_hash[digest] = relative_posix
        retained.append(
            TrajectoryFile(
                source=path,
                relative_path=relative_path,
                category=classify(relative_posix),
                selected_by=selected_by,
                size_bytes=len(content),
                sha256=digest,
            )
        )
    return retained, duplicates


def credential_hits(files: list[TrajectoryFile]) -> list[tuple[str, str]]:
    hits: list[tuple[str, str]] = []
    for trajectory_file in files:
        content = trajectory_file.source.read_bytes()
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(content):
                hits.append((trajectory_file.relative_path.as_posix(), label))
    return hits


def write_manifest(
    staging: Path,
    files: list[TrajectoryFile],
    duplicates: list[tuple[str, str]],
) -> None:
    with (staging / "MANIFEST.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["path", "category", "selected_by", "size_bytes", "sha256"]
        )
        for trajectory_file in files:
            writer.writerow(
                [
                    trajectory_file.relative_path.as_posix(),
                    trajectory_file.category,
                    trajectory_file.selected_by,
                    trajectory_file.size_bytes,
                    trajectory_file.sha256,
                ]
            )
    with (staging / "DUPLICATES.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["omitted_duplicate_path", "canonical_path"])
        writer.writerows(duplicates)


def write_readme(staging: Path, files: list[TrajectoryFile], duplicates: int) -> None:
    categories = Counter(file.category for file in files)
    total_bytes = sum(file.size_bytes for file in files)
    category_lines = "\n".join(
        f"- `{category}`: {count} files"
        for category, count in sorted(categories.items())
    )
    readme = f"""---
pretty_name: HARP Trajectories
task_categories:
- text-generation
- reinforcement-learning
language:
- en
license: other
---

# HARP Trajectories

Canonical project-generated trajectory records for the HARP experiments.

## Contents

{category_lines}

Total: {len(files)} unique files ({total_bytes:,} bytes). The upload omits
{duplicates} byte-identical duplicate files; `DUPLICATES.csv` maps each omitted
path to its retained canonical path. `MANIFEST.csv` records source-relative paths,
categories, byte sizes, and SHA-256 hashes.

The original `analysis/` directory layout is preserved. Records may include model
replies, evaluator reasoning, synthetic personas, and per-step environment state.
They do not contain intentionally collected personal data.

## Upstream data

The public SOTOPIA source episodes are not redistributed here. Their source is
`https://huggingface.co/datasets/cmu-lti/sotopia` and the project records exact
input provenance in `config/aaai27_sotopia_input_manifest.csv`.

## License

Use is subject to the licenses and terms of the underlying environments and model
providers. This private repository is intended for research artifact sharing.
"""
    (staging / "README.md").write_text(readme, encoding="utf-8")


def stage(files: list[TrajectoryFile], duplicates: list[tuple[str, str]], path: Path) -> None:
    for trajectory_file in files:
        destination = path / trajectory_file.relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(trajectory_file.source, destination)
    write_manifest(path, files, duplicates)
    write_readme(path, files, len(duplicates))


def verify_remote(api: HfApi, repo_id: str, files: list[TrajectoryFile]) -> None:
    expected = {
        "README.md",
        "MANIFEST.csv",
        "DUPLICATES.csv",
        *(file.relative_path.as_posix() for file in files),
    }
    actual = set(api.list_repo_files(repo_id=repo_id, repo_type="dataset"))
    missing = sorted(expected - actual)
    if missing:
        raise RuntimeError(f"remote dataset is missing {len(missing)} files")
    info = api.repo_info(repo_id=repo_id, repo_type="dataset")
    if not info.private:
        raise RuntimeError("remote dataset is not private")
    print(json.dumps({
        "status": "ok",
        "repo_id": repo_id,
        "private": info.private,
        "uploaded_files": len(expected),
        "trajectory_files": len(files),
        "remote_revision": info.sha,
    }, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--upload", action="store_true")
    args = parser.parse_args()

    files, duplicates = inventory()
    hits = credential_hits(files)
    summary = {
        "trajectory_files": len(files),
        "total_bytes": sum(file.size_bytes for file in files),
        "duplicates_omitted": len(duplicates),
        "credential_hits": len(hits),
        "categories": dict(sorted(Counter(file.category for file in files).items())),
    }
    print(json.dumps(summary, indent=2))
    if hits:
        for path, pattern_class in hits:
            print(f"credential-like content: {pattern_class}: {path}")
        raise SystemExit("refusing to upload files with credential-like content")
    if not args.upload:
        return

    api = HfApi()
    api.create_repo(
        repo_id=args.repo_id,
        repo_type="dataset",
        private=True,
        exist_ok=True,
    )
    with tempfile.TemporaryDirectory(prefix="harp-trajectories-") as temporary:
        staging = Path(temporary)
        stage(files, duplicates, staging)
        api.upload_folder(
            repo_id=args.repo_id,
            repo_type="dataset",
            folder_path=staging,
            commit_message="Publish HARP experiment trajectories",
        )
    verify_remote(api, args.repo_id, files)


if __name__ == "__main__":
    main()