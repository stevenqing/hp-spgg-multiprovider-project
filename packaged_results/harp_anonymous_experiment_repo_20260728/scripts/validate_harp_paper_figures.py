"""Validate HARP branding across every figure referenced by the paper."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

import fitz


ROOT = Path(__file__).resolve().parents[1]
INCLUDEGRAPHICS = re.compile(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}")
OLD_BRAND = re.compile(r"\bPACT(?:\+)?\b", flags=re.IGNORECASE)
NEW_BRAND = re.compile(r"\bHARP(?:\+)?\b", flags=re.IGNORECASE)
REDRAW_MANIFEST = "HARP_FIGURE_REDRAW_MANIFEST.json"


def figure_references(paper_dir: Path) -> list[str]:
    source = "\n".join(
        (paper_dir / name).read_text(encoding="utf-8")
        for name in ("main.tex", "appendix.tex")
    )
    return sorted(set(INCLUDEGRAPHICS.findall(source)))


def pdf_text(path: Path) -> str:
    with fitz.open(path) as document:
        return "\n".join(page.get_text() for page in document)


def normalize_pdf_text(text: str) -> str:
    # PDF extraction can split "compact" as "com- pact", which would create
    # a false whole-word PACT match after layout hyphenation.
    return re.sub(r"(?<=\w)-\s+(?=\w)", "", text)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-dir", type=Path, default=ROOT / "arr_paper")
    args = parser.parse_args()
    paper_dir = args.paper_dir.resolve()

    references = figure_references(paper_dir)
    if not references:
        raise AssertionError("the paper has no figure references")

    records: list[dict[str, object]] = []
    missing: list[str] = []
    old_brand_matches: list[dict[str, object]] = []
    raster_references: list[str] = []
    for reference in references:
        path = paper_dir / reference
        if not path.is_file() or path.stat().st_size == 0:
            missing.append(reference)
            continue
        record: dict[str, object] = {
            "path": reference,
            "bytes": path.stat().st_size,
            "old_brand_matches": 0,
            "new_brand_matches": 0,
        }
        if path.suffix.lower() == ".pdf":
            text = pdf_text(path)
            old_matches = OLD_BRAND.findall(text)
            new_matches = NEW_BRAND.findall(text)
            record["old_brand_matches"] = len(old_matches)
            record["new_brand_matches"] = len(new_matches)
            if old_matches:
                old_brand_matches.append(
                    {
                        "path": reference,
                        "matches": sorted(set(match.upper() for match in old_matches)),
                    }
                )
        else:
            raster_references.append(reference)
        records.append(record)

    overview_source = paper_dir / "figs" / "main.png"
    if not overview_source.is_file() or overview_source.stat().st_size == 0:
        raise AssertionError("the edited overview source figs/main.png is missing")
    if missing:
        raise AssertionError(f"missing or empty paper figures: {missing}")
    if old_brand_matches:
        raise AssertionError(
            "old PACT branding remains in referenced PDF text: "
            + json.dumps(old_brand_matches, sort_keys=True)
        )

    forbidden_overlay = ROOT / "scripts" / "rebrand_harp_paper_figures.py"
    if forbidden_overlay.exists():
        raise AssertionError("vector rebranding utility must not exist in the HARP release")
    manifest_path = paper_dir / REDRAW_MANIFEST
    if not manifest_path.is_file():
        raise AssertionError("figure redraw provenance manifest is missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if "overlays are prohibited" not in str(manifest.get("policy", "")):
        raise AssertionError("redraw manifest does not prohibit PDF overlays")
    manifest_outputs = {str(record["path"]): record for record in manifest.get("outputs", [])}
    if set(manifest_outputs) != set(references):
        raise AssertionError(
            f"redraw manifest figure set mismatch: missing={sorted(set(references)-set(manifest_outputs))} "
            f"extra={sorted(set(manifest_outputs)-set(references))}"
        )
    for reference in references:
        path = paper_dir / reference
        record = manifest_outputs[reference]
        if record.get("sha256") != sha256(path) or int(record.get("bytes", -1)) != path.stat().st_size:
            raise AssertionError(f"redraw provenance hash/size mismatch: {reference}")
        generator = str(record.get("generator", "")).split(" --", 1)[0]
        if not (ROOT / generator).is_file():
            raise AssertionError(f"redraw generator is missing for {reference}: {generator}")

    paper_records = []
    for name in ("main.pdf", "HARP_AAAI27.pdf"):
        path = paper_dir / name
        if not path.is_file() or path.stat().st_size == 0:
            raise AssertionError(f"compiled paper is missing: {name}")
        with fitz.open(path) as document:
            pages = len(document)
            text = normalize_pdf_text("\n".join(page.get_text() for page in document))
        if pages != 35:
            raise AssertionError(f"{name} has {pages} pages; expected 35")
        if "LLM Orchestration under Heterogeneous Preferences" not in text:
            raise AssertionError(f"{name} is missing the HARP paper title")
        if OLD_BRAND.search(text):
            raise AssertionError(f"old PACT branding remains visible in {name}")
        if not NEW_BRAND.search(text):
            raise AssertionError(f"HARP branding is missing from {name}")
        if "??" in text:
            raise AssertionError(f"unresolved reference marker remains in {name}")
        if path.stat().st_mtime_ns <= manifest_path.stat().st_mtime_ns:
            raise AssertionError(f"{name} is older than the completed figure redraw manifest")
        paper_records.append(
            {
                "path": name,
                "pages": pages,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "harp_matches": len(NEW_BRAND.findall(text)),
            }
        )
    if paper_records[0]["sha256"] != paper_records[1]["sha256"]:
        raise AssertionError("main.pdf and HARP_AAAI27.pdf are not byte-identical")

    print(
        json.dumps(
            {
                "status": "ok",
                "paper_dir": paper_dir.as_posix(),
                "figure_references": len(references),
                "pdf_references": sum(record["path"].endswith(".pdf") for record in records),
                "raster_references": raster_references,
                "pdfs_with_harp_text": sum(int(record["new_brand_matches"]) > 0 for record in records),
                "overview_source": overview_source.relative_to(paper_dir).as_posix(),
                "redraw_manifest": manifest_path.relative_to(ROOT).as_posix(),
                "redraw_commands": len(manifest.get("commands", [])),
                "compiled_papers": paper_records,
                "records": records,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
