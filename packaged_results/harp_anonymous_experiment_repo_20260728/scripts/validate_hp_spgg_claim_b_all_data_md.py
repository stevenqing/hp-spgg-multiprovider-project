"""Strictly validate the single complete HP-SPGG Claim-B Markdown."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCALING = ROOT / "analysis" / "hp_spgg_analytic_scaling"
V2 = ROOT / "analysis" / "hp_spgg_burn_in_v2_pilot"
V3 = ROOT / "analysis" / "hp_spgg_burn_in_v3_confirmatory"
REPORT = V3 / "claim_b_all_data.md"

JSON_SECTIONS = (
    ("ORIGINAL_FIT_JSON", SCALING / "scaling_burn_in_fit.json"),
    ("ORIGINAL_DIAGNOSTIC_JSON", SCALING / "burn_in_support_diagnostic.json"),
    ("V2_FITS_JSON", V2 / "burn_in_v2_fits.json"),
    ("V3_PREREGISTRATION_JSON", V3 / "preregistration.json"),
    ("V3_RESULTS_JSON", V3 / "confirmatory_results.json"),
)
MARKDOWN_SECTIONS = (
    ("ORIGINAL_DIAGNOSTIC_MD", SCALING / "burn_in_support_diagnostic.md"),
    ("V3_PREREGISTRATION_MD", V3 / "PREREGISTRATION.md"),
)
CSV_SECTIONS = (
    ("## V2 cell summaries (all 13 rows)", V2 / "burn_in_v2_summary.csv", 13),
    ("## V2 contraction checkpoints (all 84 rows)", V2 / "burn_in_v2_contraction.csv", 84),
    ("## V2 raw agent results (all 11,400 rows)", V2 / "burn_in_v2_raw.csv", 11_400),
    ("## V3 Hellinger-affinity summaries (all 15 rows)", V3 / "affinity_summary.csv", 15),
    ("## V3 Hellinger-affinity batches (all 3,000 rows)", V3 / "affinity_batches.csv", 3_000),
    ("## V3 fixed-channel cell summaries (all 34 rows)", V3 / "fixed_channel_cell_summary.csv", 34),
    ("## V3 posterior-error proxy checkpoints (all 84 rows)", V3 / "posterior_error_proxy_checkpoints.csv", 84),
    ("## V3 adaptive PACT cell summaries (all 6 rows)", V3 / "adaptive_cell_summary.csv", 6),
    ("## V3 adaptive PACT seed results (all 1,200 rows)", V3 / "adaptive_seed_results.csv", 1_200),
    ("## V3 fixed-channel agent results (all 105,000 rows)", V3 / "fixed_channel_agent_results.csv", 105_000),
)
INTEGRITY_FILES = (
    SCALING / "scaling_burn_in_fit.json",
    SCALING / "burn_in_support_diagnostic.md",
    SCALING / "burn_in_support_diagnostic.json",
    SCALING / "fig_hp_spgg_analytic_scaling_burnin_v1.pdf",
    V2 / "burn_in_v2_raw.csv",
    V2 / "burn_in_v2_summary.csv",
    V2 / "burn_in_v2_contraction.csv",
    V2 / "burn_in_v2_fits.json",
    V2 / "burn_in_v2_design_and_results.md",
    V2 / "fig_hp_spgg_burn_in_v2_pilot.pdf",
    V2 / "fig_hp_spgg_burn_in_v2_pilot.png",
    V3 / "preregistration.json",
    V3 / "PREREGISTRATION.md",
    V3 / "PREREGISTRATION.sha256",
    V3 / "affinity_batches.csv",
    V3 / "affinity_summary.csv",
    V3 / "fixed_channel_agent_results.csv",
    V3 / "fixed_channel_cell_summary.csv",
    V3 / "posterior_error_proxy_checkpoints.csv",
    V3 / "adaptive_seed_results.csv",
    V3 / "adaptive_cell_summary.csv",
    V3 / "confirmatory_results.json",
    V3 / "claim_b_v3_confirmatory_results.md",
    V3 / "fig_hp_spgg_burn_in_v3_confirmatory.pdf",
    V3 / "fig_hp_spgg_burn_in_v3_confirmatory.png",
    ROOT / "llm_hpgg" / "analytic_scaling.py",
    ROOT / "scripts" / "analyze_hp_spgg_burn_in_support.py",
    ROOT / "scripts" / "run_hp_spgg_burn_in_v2_pilot.py",
    ROOT / "scripts" / "render_hp_spgg_burn_in_v2_pilot.py",
    ROOT / "scripts" / "validate_hp_spgg_burn_in_v2_pilot.py",
    ROOT / "scripts" / "run_hp_spgg_burn_in_v3_confirmatory.py",
    ROOT / "scripts" / "render_hp_spgg_burn_in_v3_confirmatory.py",
    ROOT / "scripts" / "validate_hp_spgg_burn_in_v3_confirmatory.py",
    ROOT / "scripts" / "summarize_hp_spgg_claim_b_all_data.py",
    ROOT / "scripts" / "validate_hp_spgg_claim_b_all_data_md.py",
)
EXPECTED_TOTAL_CSV_ROWS = 120_836


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_markdown_row(line: str) -> list[str]:
    if not line.startswith("|") or not line.endswith("|"):
        raise AssertionError(f"not a Markdown table row: {line[:80]}")
    cells: list[str] = []
    current: list[str] = []
    index = 1
    while index < len(line) - 1:
        character = line[index]
        if character == "\\" and index + 1 < len(line) - 1:
            next_character = line[index + 1]
            if next_character in {"\\", "|"}:
                current.append(next_character)
                index += 2
                continue
        if character == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(character)
        index += 1
    cells.append("".join(current).strip())
    return cells


def table(lines: list[str], heading: str) -> tuple[list[str], list[list[str]]]:
    try:
        index = lines.index(heading) + 1
    except ValueError as exc:
        raise AssertionError(f"missing Claim-B section: {heading}") from exc
    while index < len(lines) and not lines[index].startswith("|"):
        index += 1
    if index + 1 >= len(lines):
        raise AssertionError(f"missing table after {heading}")
    header = parse_markdown_row(lines[index])
    separator = parse_markdown_row(lines[index + 1])
    if len(separator) != len(header) or not all(set(cell) <= {"-", ":"} for cell in separator):
        raise AssertionError(f"bad table separator after {heading}")
    rows: list[list[str]] = []
    for line in lines[index + 2 :]:
        if not line.startswith("|"):
            break
        row = parse_markdown_row(line)
        if len(row) != len(header):
            raise AssertionError(f"column mismatch after {heading}")
        rows.append(row)
    return header, rows


def csv_payload(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or ())
        rows = [[row[field] for field in fields] for row in reader]
    return fields, rows


def extract_block(text: str, marker: str, fence: str) -> str:
    start_token = f"<!-- BEGIN {marker} -->\n{fence}\n"
    end_fence = "```" if fence == "```json" else "~~~"
    end_token = f"\n{end_fence}\n<!-- END {marker} -->"
    start = text.find(start_token)
    if start < 0:
        raise AssertionError(f"missing block start: {marker}")
    start += len(start_token)
    end = text.find(end_token, start)
    if end < 0:
        raise AssertionError(f"missing block end: {marker}")
    return text[start:end]


def source_integrity_row(path: Path) -> list[str]:
    records = ""
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8") as handle:
            records = str(sum(1 for _ in csv.DictReader(handle)))
    return [
        path.relative_to(ROOT).as_posix(),
        str(path.stat().st_size),
        records,
        sha256(path),
    ]


def main() -> None:
    if not REPORT.is_file() or REPORT.stat().st_size < 20_000_000:
        raise AssertionError("single Claim-B Markdown is missing or unexpectedly small")
    text = REPORT.read_text(encoding="utf-8")
    lines = text.splitlines()
    private = bytes.fromhex("762d73687571696e67736869").decode("utf-8")
    if private.lower() in text.lower():
        raise AssertionError("private local identity found in Claim-B Markdown")

    for marker, source in JSON_SECTIONS:
        observed = extract_block(text, marker, "```json")
        expected = source.read_text(encoding="utf-8").rstrip("\n")
        if observed != expected:
            raise AssertionError(f"embedded JSON differs from source: {marker}")
        json.loads(observed)
    for marker, source in MARKDOWN_SECTIONS:
        observed = extract_block(text, marker, "~~~markdown")
        expected = source.read_text(encoding="utf-8").rstrip("\n")
        if observed != expected:
            raise AssertionError(f"embedded Markdown differs from source: {marker}")

    checked_rows = 0
    table_counts: dict[str, int] = {}
    for heading, source, expected_count in CSV_SECTIONS:
        observed_fields, observed_rows = table(lines, heading)
        source_fields, source_rows = csv_payload(source)
        if observed_fields != source_fields:
            raise AssertionError(f"header differs from source: {heading}")
        if len(observed_rows) != expected_count or len(source_rows) != expected_count:
            raise AssertionError(f"row count differs from expectation: {heading}")
        for index, (observed, expected) in enumerate(zip(observed_rows, source_rows, strict=True), start=1):
            if observed != expected:
                raise AssertionError(f"row {index} differs from source: {heading}")
        table_counts[heading] = len(observed_rows)
        checked_rows += len(observed_rows)
    if checked_rows != EXPECTED_TOTAL_CSV_ROWS:
        raise AssertionError(f"total embedded CSV rows mismatch: {checked_rows}")

    integrity_header, integrity_rows = table(lines, "## Source integrity")
    if integrity_header != ["path", "bytes", "records", "sha256"]:
        raise AssertionError("source-integrity header mismatch")
    expected_integrity = [source_integrity_row(path) for path in INTEGRITY_FILES]
    if integrity_rows != expected_integrity:
        raise AssertionError("source-integrity table differs from current files")

    gate_header, gate_rows = table(lines, "## V3 locked-gate headline")
    if gate_header != ["gate", "passed", "result"] or len(gate_rows) != 5:
        raise AssertionError("locked-gate headline mismatch")
    if any(row[1] != "True" for row in gate_rows):
        raise AssertionError("a locked v3 gate is not marked as passing")
    v3 = json.loads((V3 / "confirmatory_results.json").read_text(encoding="utf-8"))
    if v3["claim_b_v3_supported"] is not True or v3["original_linear_n_formula_supported"] is not False:
        raise AssertionError("Claim-B disposition mismatch")
    expected_gate_names = list(v3["gates"])
    if [row[0] for row in gate_rows] != expected_gate_names:
        raise AssertionError("gate order/names differ from machine-readable result")
    for row in gate_rows:
        if json.loads(row[2]) != v3["gates"][row[0]]:
            raise AssertionError(f"gate payload differs: {row[0]}")

    inventory_header, inventory_rows = table(lines, "## Included row inventory")
    if inventory_header != ["section", "source", "rows"] or len(inventory_rows) != len(CSV_SECTIONS) + 1:
        raise AssertionError("row inventory mismatch")
    if inventory_rows[-1] != ["Total embedded CSV rows", "all tables below", str(EXPECTED_TOTAL_CSV_ROWS)]:
        raise AssertionError("total row inventory mismatch")

    required = (
        "Original pooled fit:",
        "**unsupported**",
        "Original `(n+1) log(m)/(rho H)` formula: **retired**",
        "V3 locked decision: **SUPPORTED**",
        "all five preregistered gates pass",
    )
    for phrase in required:
        if phrase not in text:
            raise AssertionError(f"required disposition missing: {phrase}")

    result = {
        "status": "ok",
        "report": REPORT.relative_to(ROOT).as_posix(),
        "bytes": REPORT.stat().st_size,
        "lines": len(lines),
        "embedded_csv_rows": checked_rows,
        "table_counts": table_counts,
        "json_blocks_checked": len(JSON_SECTIONS),
        "markdown_blocks_checked": len(MARKDOWN_SECTIONS),
        "source_hashes_checked": len(INTEGRITY_FILES),
        "sha256": sha256(REPORT),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
