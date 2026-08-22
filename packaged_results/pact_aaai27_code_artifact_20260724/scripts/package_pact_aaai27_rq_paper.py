"""Build the clean anonymous RQ-restructured AAAI-27 paper ZIP."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "arr_paper"
OUTPUT = ROOT / "PACT_AAAI27_rq_restructured.zip"
SIDECAR = ROOT / "PACT_AAAI27_rq_restructured.zip.sha256"
ARCHIVE_ROOT = "PACT_AAAI27_rq_restructured"
CORE_FILES = (
    "aaai2027.sty",
    "aaai2027.bst",
    "main.tex",
    "appendix.tex",
    "ref.bib",
    "main.bbl",
    "ReproducibilityChecklist.tex",
    "main.pdf",
    "PACT_AAAI27.pdf",
)
TEXT_SUFFIXES = {".tex", ".bib", ".bbl", ".bst", ".sty", ".md", ".csv", ".txt"}
FORBIDDEN_BYTES = {
    bytes.fromhex("762d73687571696e67736869"): "local user name",
    bytes.fromhex("37326639383862662d383666312d343161662d393161622d326437636430313164623437"): "private tenant identifier",
    bytes.fromhex("66656237623636312d636163372d343461382d386463312d313633623633633233646632"): "private application identifier",
    bytes.fromhex("636c6f75646770742d6f70656e61692e617a7572652d6170692e6e6574"): "private provider endpoint",
    bytes.fromhex("433a5c5c5573657273"): "absolute Windows user path",
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(path: Path) -> Path:
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def referenced_figures() -> list[Path]:
    source = "\n".join(
        (PAPER / filename).read_text(encoding="utf-8")
        for filename in ("main.tex", "appendix.tex")
    )
    names = sorted(set(re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", source)))
    figures: list[Path] = []
    for name in names:
        pure = PurePosixPath(name)
        if pure.is_absolute() or ".." in pure.parts:
            raise AssertionError(f"unsafe figure reference: {name}")
        figures.append(require(PAPER / Path(*pure.parts)))
    return figures


def pdf_pages(path: Path) -> int:
    result = subprocess.run(
        ["pdfinfo", str(path)],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    match = re.search(r"(?m)^Pages:\s+(\d+)", result.stdout)
    if not match:
        raise AssertionError(f"could not read page count: {path}")
    return int(match.group(1))


def pdf_text(path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", str(path), "-"],
        check=True,
        capture_output=True,
    )
    return result.stdout.decode("utf-8", errors="replace")


def validate_source() -> dict[str, object]:
    for filename in CORE_FILES:
        require(PAPER / filename)
    figures = referenced_figures()
    if pdf_pages(PAPER / "main.pdf") != 29:
        raise AssertionError("full paper must contain 29 pages")
    if pdf_pages(PAPER / "PACT_AAAI27.pdf") != 11:
        raise AssertionError("canonical submission must contain 11 pages")

    submission_text = pdf_text(PAPER / "PACT_AAAI27.pdf")
    full_text = pdf_text(PAPER / "main.pdf")
    required_submission = (
        "Figure 3: E-G analytic HP-SPGG component ladder",
        "Figure 5: Iterated Concordia diagnostic",
        "Figure 6: MaaSSim RQ diagnostics",
        "eight of nine nominal utility CIs cover zero",
        "Reproducibility Checklist",
    )
    for phrase in required_submission:
        if phrase not in submission_text:
            raise AssertionError(f"submission PDF is missing: {phrase}")
    if "Claim-Organized Empirical Supplement" in submission_text:
        raise AssertionError("canonical submission unexpectedly includes the technical appendix")
    if "Claim-Organized Empirical Supplement" not in full_text:
        raise AssertionError("full paper is missing the technical appendix")
    if "??" in submission_text or "??" in full_text:
        raise AssertionError("unresolved reference marker found in a PDF")

    text_sources = [PAPER / filename for filename in CORE_FILES if Path(filename).suffix in TEXT_SUFFIXES]
    text_sources.extend(path for path in figures if path.suffix.lower() in TEXT_SUFFIXES)
    for path in text_sources:
        payload = path.read_bytes().lower()
        for pattern, label in FORBIDDEN_BYTES.items():
            if pattern.lower() in payload:
                raise AssertionError(f"{label} found in {path.relative_to(ROOT).as_posix()}")
    return {"figures": figures, "submission_text": submission_text}


def readme() -> bytes:
    return (
        "# PACT AAAI-27 Anonymous Paper Package\n\n"
        "This archive contains the RQ-restructured anonymous paper, its full technical supplement, "
        "the official AAAI-27 style files, bibliography, and exactly the referenced figure assets.\n\n"
        "## Canonical PDFs\n\n"
        "- `PACT_AAAI27.pdf`: 11-page submission artifact (main text + references + checklist; no technical appendix).\n"
        "- `main.pdf`: 29-page full review bundle including the technical supplement and checklist.\n\n"
        "Figure 3 is the analytic HP-SPGG RQ3 component ladder. Figure 5 is the two-panel "
        "iterated-Concordia RQ2/RQ3 diagnostic. Figure 6 reports the final MaaSSim grid with "
        "lambda in {0, 0.5, 1}.\n\n"
        "## Build\n\n"
        "With MiKTeX/TeX Live and BibTeX installed, build the full bundle from this directory:\n\n"
        "```text\n"
        "pdflatex -interaction=nonstopmode main.tex\n"
        "bibtex main\n"
        "pdflatex -interaction=nonstopmode main.tex\n"
        "pdflatex -interaction=nonstopmode main.tex\n"
        "```\n\n"
        "The package is anonymous and intentionally omits logs, auxiliary files, experiment data, provider configuration, "
        "historical figure drafts, and local paths. File hashes are recorded in `SHA256SUMS.txt` and `MANIFEST.csv`.\n"
    ).encode("utf-8")


def manifest_payload(files: dict[str, bytes]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["path", "bytes", "sha256"])
    for name in sorted(files):
        writer.writerow([name, len(files[name]), sha256_bytes(files[name])])
    return output.getvalue().encode("utf-8")


def sums_payload(files: dict[str, bytes]) -> bytes:
    return ("\n".join(f"{sha256_bytes(files[name])}  {name}" for name in sorted(files)) + "\n").encode("utf-8")


def validate_payloads(files: dict[str, bytes], figures: list[Path]) -> None:
    expected = set(CORE_FILES) | {path.relative_to(PAPER).as_posix() for path in figures} | {
        "README.md",
        "MANIFEST.csv",
        "SHA256SUMS.txt",
    }
    if set(files) != expected:
        raise AssertionError(f"package file set mismatch: missing={expected-set(files)}, extra={set(files)-expected}")
    forbidden_suffixes = {".aux", ".blg", ".log", ".out", ".synctex", ".zip"}
    for name, payload in files.items():
        pure = PurePosixPath(name)
        if pure.is_absolute() or ".." in pure.parts or Path(name).suffix.lower() in forbidden_suffixes:
            raise AssertionError(f"unsafe/generated package path: {name}")
        if Path(name).suffix.lower() in TEXT_SUFFIXES:
            lower = payload.lower()
            for pattern, label in FORBIDDEN_BYTES.items():
                if pattern.lower() in lower:
                    raise AssertionError(f"{label} found in packaged {name}")


def build() -> dict[str, object]:
    source = validate_source()
    figures = source["figures"]
    files: dict[str, bytes] = {filename: (PAPER / filename).read_bytes() for filename in CORE_FILES}
    for path in figures:
        files[path.relative_to(PAPER).as_posix()] = path.read_bytes()
    files["README.md"] = readme()
    files["MANIFEST.csv"] = manifest_payload(files)
    files["SHA256SUMS.txt"] = sums_payload(files)
    validate_payloads(files, figures)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pact_rq_paper_", dir=OUTPUT.parent) as temp_name:
        temp_zip = Path(temp_name) / OUTPUT.name
        with zipfile.ZipFile(temp_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name in sorted(files):
                info = zipfile.ZipInfo(f"{ARCHIVE_ROOT}/{name}", date_time=(2026, 7, 24, 12, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, files[name])
        with zipfile.ZipFile(temp_zip) as archive:
            bad = archive.testzip()
            if bad is not None:
                raise AssertionError(f"corrupt archive member: {bad}")
            names = archive.namelist()
            expected_names = [f"{ARCHIVE_ROOT}/{name}" for name in sorted(files)]
            if names != expected_names:
                raise AssertionError("archive member order or names changed")
        shutil.copyfile(temp_zip, OUTPUT)

    digest = sha256(OUTPUT)
    SIDECAR.write_text(f"{digest}  {OUTPUT.name}\n", encoding="utf-8")
    result = {
        "status": "ok",
        "output": OUTPUT.relative_to(ROOT).as_posix(),
        "bytes": OUTPUT.stat().st_size,
        "sha256": digest,
        "files": len(files),
        "figures": len(figures),
        "full_pages": pdf_pages(PAPER / "main.pdf"),
        "submission_pages": pdf_pages(PAPER / "PACT_AAAI27.pdf"),
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    build()
