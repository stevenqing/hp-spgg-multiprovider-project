"""Build a compact figures-and-data artifact bundle for the project.

The bundle keeps:
- figures actually referenced by ``arr_paper/main.tex`` and ``appendix.tex``;
- every other canonical PDF, PNG, and GIF in ``arr_paper/figs``;
- the current ``analysis/`` and ``tables/`` data layers, excluding caches;
- paper sources, provenance documentation, every detected figure renderer, and
    the plotting/analysis helper scripts.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import shutil
import subprocess
from collections import defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NAME = f"pact_figures_data_{date.today():%Y%m%d}"
FIGURE_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".gif"}
DATA_EXTENSIONS = {".csv", ".json", ".jsonl", ".md", ".txt", ".tex"}
PLOT_SCRIPT_PREFIXES = (
    "aggregate_",
    "analyze_",
    "animate_",
    "make_",
    "plot_",
    "summarize_",
)
PLOT_RENDER_RE = re.compile(
    r"\bsavefig\s*\(|\bmimsave\s*\(|\b(?:anim|animation)\.save\s*\(|\bwrite_image\s*\("
)
INCLUDEGRAPHICS_RE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def paper_figure_paths() -> list[Path]:
    paths: list[Path] = []
    for tex_name in ("main.tex", "appendix.tex"):
        tex_path = ROOT / "arr_paper" / tex_name
        for raw in INCLUDEGRAPHICS_RE.findall(tex_path.read_text(encoding="utf-8")):
            source = ROOT / "arr_paper" / raw.replace("/", "\\")
            if source.suffix:
                candidates = [source]
            else:
                candidates = [source.with_suffix(extension) for extension in FIGURE_EXTENSIONS]
            resolved = next((candidate for candidate in candidates if candidate.exists()), None)
            if resolved is None:
                raise FileNotFoundError(f"Paper figure not found for {raw!r} in {tex_path}")
            if resolved not in paths:
                paths.append(resolved)
    return paths


def other_canonical_figures(paper_figures: set[Path]) -> list[Path]:
    figure_root = ROOT / "arr_paper" / "figs"
    return sorted(
        path
        for path in figure_root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in FIGURE_EXTENSIONS
        and path not in paper_figures
    )


def include_data_file(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    lowered_parts = [part.lower() for part in relative.parts]
    lowered_name = path.name.lower()
    if path.suffix.lower() not in DATA_EXTENSIONS:
        return False
    if any(part in {"__pycache__", "animation_frames"} for part in lowered_parts):
        return False
    if "cache" in lowered_name or lowered_name.endswith(".tmp"):
        return False
    if lowered_name.startswith(("_replay_", "_mechanism_")):
        return False
    return True


def data_paths() -> list[Path]:
    paths: list[Path] = []
    for directory in (ROOT / "analysis", ROOT / "tables"):
        if not directory.exists():
            continue
        paths.extend(path for path in directory.rglob("*") if path.is_file() and include_data_file(path))
    return sorted(paths)


def plot_script_paths() -> list[Path]:
    paths = {
        path
        for path in (ROOT / "scripts").glob("*.py")
        if path.name.startswith(PLOT_SCRIPT_PREFIXES)
    }
    search_roots = [ROOT / "scripts", *(path for path in ROOT.glob("llm_*") if path.is_dir())]
    for search_root in search_roots:
        for path in search_root.rglob("*.py"):
            if PLOT_RENDER_RE.search(path.read_text(encoding="utf-8")):
                paths.add(path)
    return sorted(paths)


def paper_source_paths() -> list[Path]:
    names = (
        "main.tex",
        "appendix.tex",
        "math_commands.tex",
        "ref.bib",
        "acl.sty",
        "acl_natbib.bst",
        "main.bbl",
        "main.pdf",
    )
    return [ROOT / "arr_paper" / name for name in names if (ROOT / "arr_paper" / name).exists()]


def metadata_paths() -> list[Path]:
    names = (
        "README.md",
        "pyproject.toml",
        "requirements.txt",
        "uv.lock",
        "docs/data_provenance.md",
        "docs/concordia_structural_mapping.md",
        "docs/file_index.md",
        "docs/sotopia_structural_mapping.md",
        "llm_courier_dispatch_maassim/RESULTS_REVIEW.md",
        "scripts/package_project_figures_data.py",
    )
    return [ROOT / name for name in names if (ROOT / name).exists()]


def build_bundle(name: str, force: bool) -> tuple[Path, Path, list[dict[str, object]]]:
    output_root = ROOT / "packaged_results"
    package_root = output_root / name
    zip_path = output_root / f"{name}.zip"
    if package_root.exists():
        if not force:
            raise FileExistsError(f"{package_root} already exists; pass --force to replace it")
        shutil.rmtree(package_root)
    if zip_path.exists():
        if not force:
            raise FileExistsError(f"{zip_path} already exists; pass --force to replace it")
        zip_path.unlink()
    package_root.mkdir(parents=True, exist_ok=True)

    manifest: list[dict[str, object]] = []
    copied_destinations: set[Path] = set()

    def copy(source: Path, destination: Path, category: str) -> None:
        destination = Path(destination)
        if destination in copied_destinations:
            return
        target = package_root / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied_destinations.add(destination)
        manifest.append(
            {
                "category": category,
                "package_path": destination.as_posix(),
                "source_path": source.relative_to(ROOT).as_posix(),
                "bytes": target.stat().st_size,
                "sha256": sha256(target),
            }
        )

    paper_figures = paper_figure_paths()
    paper_figure_set = set(paper_figures)
    for source in paper_figures:
        copy(source, Path("figures/paper_referenced") / source.name, "paper_referenced_figure")
    for source in other_canonical_figures(paper_figure_set):
        relative = source.relative_to(ROOT / "arr_paper" / "figs")
        copy(source, Path("figures/all_other_canonical") / relative, "other_canonical_figure")
    for source in data_paths():
        copy(source, Path("data") / source.relative_to(ROOT), "data")
    for source in paper_source_paths():
        copy(source, Path("paper") / source.name, "paper_source")
    for source in plot_script_paths():
        copy(source, Path("plotting_code") / source.relative_to(ROOT), "plotting_code")
    for source in metadata_paths():
        copy(source, Path("provenance") / source.relative_to(ROOT), "provenance")

    manifest.sort(key=lambda row: (str(row["category"]), str(row["package_path"])))
    manifest_path = package_root / "MANIFEST.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["category", "package_path", "source_path", "bytes", "sha256"])
        writer.writeheader()
        writer.writerows(manifest)

    sums_path = package_root / "SHA256SUMS.txt"
    sums_path.write_text(
        "\n".join(f"{row['sha256']}  {row['package_path']}" for row in manifest) + "\n",
        encoding="utf-8",
    )

    counts: dict[str, int] = defaultdict(int)
    sizes: dict[str, int] = defaultdict(int)
    for row in manifest:
        category = str(row["category"])
        counts[category] += 1
        sizes[category] += int(row["bytes"])

    readme_lines = [
        "# PACT / HP-SPGG Figures and Data Bundle",
        "",
        f"Generated from repository commit `{git_commit()}` on `{date.today().isoformat()}`.",
        "",
        "## Contents",
        "",
        "| category | files | size (MB) |",
        "|---|---:|---:|",
    ]
    for category in sorted(counts):
        readme_lines.append(f"| {category} | {counts[category]} | {sizes[category] / (1024 * 1024):.2f} |")
    readme_lines.extend(
        [
            "",
            "## Layout",
            "",
            "- `figures/paper_referenced/`: every figure currently referenced by `arr_paper/main.tex` or `appendix.tex`.",
            "- `figures/all_other_canonical/`: every remaining PDF, PNG, and GIF from `arr_paper/figs`; together the two figure directories reproduce the complete canonical figure archive.",
            "- `data/analysis/` and `data/tables/`: current result data and reports. Cache files and temporary replay files are excluded.",
            "- `paper/`: paper source, bibliography/style files, and compiled PDF.",
            "- `plotting_code/`: every Python file detected as a figure renderer, plus plotting, aggregation, analysis, animation, and summarization helper scripts.",
            "- `provenance/`: project metadata and figure/data provenance documentation.",
            "",
            "## Validation",
            "",
            "`MANIFEST.csv` maps each packaged file back to its repository source. `SHA256SUMS.txt` contains checksums for integrity verification.",
            "",
            "Third-party checkouts, virtual environments, caches, and raw model credentials are intentionally excluded.",
        ]
    )
    (package_root / "README.md").write_text("\n".join(readme_lines) + "\n", encoding="utf-8")

    shutil.make_archive(str(output_root / name), "zip", root_dir=output_root, base_dir=name)
    return package_root, zip_path, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default=DEFAULT_NAME)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    package_root, zip_path, manifest = build_bundle(args.name, args.force)
    total_bytes = sum(int(row["bytes"]) for row in manifest)
    print(f"package={package_root.relative_to(ROOT)}")
    print(f"zip={zip_path.relative_to(ROOT)}")
    print(f"files={len(manifest)}")
    print(f"payload_mb={total_bytes / (1024 * 1024):.2f}")
    print(f"zip_mb={zip_path.stat().st_size / (1024 * 1024):.2f}")


if __name__ == "__main__":
    main()
