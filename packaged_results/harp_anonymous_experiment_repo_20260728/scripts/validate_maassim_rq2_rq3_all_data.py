"""Validate the consolidated MaaSSim RQ2/RQ3 Markdown coverage and integrity."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "analysis" / "maassim_rq2_rq3_all_data.md"
MAASSIM = ROOT / "analysis" / "courier_dispatch_maassim"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def row_count(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def table_rows(lines: list[str], heading: str) -> int:
    try:
        start = lines.index(heading) + 1
    except ValueError as exc:
        raise AssertionError(f"missing section: {heading}") from exc
    selected: list[str] = []
    for line in lines[start:]:
        if line.startswith("## ") or line.startswith("### "):
            break
        if line.startswith("|") and not line.startswith("|---"):
            selected.append(line)
    if not selected:
        raise AssertionError(f"no table under {heading}")
    return len(selected) - 1  # remove table header


def main() -> None:
    if not REPORT.is_file() or REPORT.stat().st_size < 200_000:
        raise AssertionError("consolidated MaaSSim report is missing or unexpectedly small")
    text = REPORT.read_text(encoding="utf-8")
    lines = text.splitlines()
    forbidden = (
        "matched-seed",
        "pathwise matched",
        bytes.fromhex("762d73687571696e67736869").decode("utf-8"),
    )
    for term in forbidden:
        if term.lower() in text.lower():
            raise AssertionError(f"forbidden terminology/private string in report: {term}")

    expected_tables = {
        "### Paired utility gaps and posterior identity (all 9 required cells)": 9,
        "### Tracker aggregates (all 24 rows)": 24,
        "### Complete tracker/environment rows (all 240 rows)": 240,
        "### Operational outcomes (complete mechanism-summary columns, part 1)": 6,
        "### Wait, oracle, and belief metrics (complete mechanism-summary columns, part 2)": 6,
        "### Supporting closed-loop Persona-v2 summary (all rows)": 5,
        "### Supporting common-state policy summary (all rows)": 6,
        "### Concentration by within-driver observation count": 17,
        "### Event-type information gain": 2,
        "### Complete retained driver posterior event rows (all 667 rows)": 667,
        "## RQ3 axis 3 — centralized dispatch carrier": 4,
        "### Tracker aggregates (all 2 rows)": 2,
        "### Complete tracker/environment rows (all 20 rows)": 20,
        "## Source integrity": 20,
    }
    for heading, expected in expected_tables.items():
        observed = table_rows(lines, heading)
        if observed != expected:
            raise AssertionError(f"{heading}: rows={observed}, expected {expected}")

    source_paths = [
        ROOT / "analysis" / "e_e_maassim_rq2" / "e_e_maassim_tracker_parity.csv",
        ROOT / "analysis" / "e_e_maassim_rq2" / "e_e_maassim_tracker_parity_summary.csv",
        ROOT / "analysis" / "e_e_maassim_rq2" / "e_e_maassim_tracker_parity_gaps.csv",
        ROOT / "analysis" / "e_e_maassim_rq2" / "e_e_maassim_tracker_parity_metadata.json",
        ROOT / "analysis" / "e_f_maassim_bonus" / "e_f_maassim_bonus_per_seed.csv",
        ROOT / "analysis" / "e_f_maassim_bonus" / "e_f_maassim_bonus_summary.csv",
        ROOT / "analysis" / "e_f_maassim_bonus" / "e_f_maassim_bonus_metadata.json",
        MAASSIM / "maassim_pact_persona_mechanism_summary.csv",
        MAASSIM / "maassim_persona_v2_main_summary.csv",
        MAASSIM / "maassim_common_state_replay_summary.csv",
        *(MAASSIM / f"pact_kpi_persona_v2_main_s{seed}_driver_posterior.csv" for seed in range(10)),
    ]
    for path in source_paths:
        digest = sha256(path)
        relative = path.relative_to(ROOT).as_posix()
        if relative not in text or digest not in text:
            raise AssertionError(f"source path/hash missing from report: {relative}")

    expected_source_counts = {
        source_paths[0]: 240,
        source_paths[1]: 24,
        source_paths[2]: 9,
        source_paths[4]: 20,
        source_paths[5]: 2,
        source_paths[7]: 6,
        source_paths[8]: 5,
        source_paths[9]: 6,
    }
    for path, expected in expected_source_counts.items():
        observed = row_count(path)
        if observed != expected:
            raise AssertionError(f"source row count changed: {path}={observed}, expected {expected}")
    posterior_rows = sum(row_count(path) for path in source_paths[10:])
    if posterior_rows != 667:
        raise AssertionError(f"driver posterior rows={posterior_rows}, expected 667")

    required_values = (
        "2.5479618415147343e-14",
        "1.848999999999999",
        "0.1923556128836823",
        "3.505644387116316",
        "-3.039",
        "2.6290000000000013",
        "0.0378580935",
        "0.0220589567",
        "-0.24699999999999775",
        "4/406 assignments",
    )
    for value in required_values:
        if value not in text:
            raise AssertionError(f"required value missing: {value}")

    print(
        {
            "status": "ok",
            "report": REPORT.relative_to(ROOT).as_posix(),
            "bytes": REPORT.stat().st_size,
            "lines": len(lines),
            "source_files": len(source_paths),
            "ee_rows": 240,
            "driver_events": posterior_rows,
            "ef_rows": 20,
        }
    )


if __name__ == "__main__":
    main()
