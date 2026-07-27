"""Consolidate the complete HP-SPGG Claim-B lineage into one Markdown file."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCALING = ROOT / "analysis" / "hp_spgg_analytic_scaling"
V2 = ROOT / "analysis" / "hp_spgg_burn_in_v2_pilot"
V3 = ROOT / "analysis" / "hp_spgg_burn_in_v3_confirmatory"
OUTPUT = V3 / "claim_b_all_data.md"

JSON_SECTIONS = (
    ("ORIGINAL_FIT_JSON", "Original preregistered fit — complete JSON", SCALING / "scaling_burn_in_fit.json"),
    ("ORIGINAL_DIAGNOSTIC_JSON", "Original-null diagnosis — complete JSON", SCALING / "burn_in_support_diagnostic.json"),
    ("V2_FITS_JSON", "Claim-B v2 pilot fits — complete JSON", V2 / "burn_in_v2_fits.json"),
    ("V3_PREREGISTRATION_JSON", "Claim-B v3 locked preregistration — complete JSON", V3 / "preregistration.json"),
    ("V3_RESULTS_JSON", "Claim-B v3 locked decision — complete JSON", V3 / "confirmatory_results.json"),
)

MARKDOWN_SOURCE_SECTIONS = (
    ("ORIGINAL_DIAGNOSTIC_MD", "Original-null diagnosis narrative — complete source", SCALING / "burn_in_support_diagnostic.md"),
    ("V3_PREREGISTRATION_MD", "Claim-B v3 preregistration narrative — complete source", V3 / "PREREGISTRATION.md"),
)

CSV_SECTIONS = (
    ("## V2 cell summaries (all 13 rows)", V2 / "burn_in_v2_summary.csv"),
    ("## V2 contraction checkpoints (all 84 rows)", V2 / "burn_in_v2_contraction.csv"),
    ("## V2 raw agent results (all 11,400 rows)", V2 / "burn_in_v2_raw.csv"),
    ("## V3 Hellinger-affinity summaries (all 15 rows)", V3 / "affinity_summary.csv"),
    ("## V3 Hellinger-affinity batches (all 3,000 rows)", V3 / "affinity_batches.csv"),
    ("## V3 fixed-channel cell summaries (all 34 rows)", V3 / "fixed_channel_cell_summary.csv"),
    ("## V3 posterior-error proxy checkpoints (all 84 rows)", V3 / "posterior_error_proxy_checkpoints.csv"),
    ("## V3 adaptive PACT cell summaries (all 6 rows)", V3 / "adaptive_cell_summary.csv"),
    ("## V3 adaptive PACT seed results (all 1,200 rows)", V3 / "adaptive_seed_results.csv"),
    ("## V3 fixed-channel agent results (all 105,000 rows)", V3 / "fixed_channel_agent_results.csv"),
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def escape(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\r", "").replace("\n", "<br>")


def csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = list(reader.fieldnames or ())
    if not fields or not rows:
        raise AssertionError(f"empty Claim-B source table: {path}")
    return fields, rows


def write_table(handle, fields: list[str], rows: list[dict[str, object]]) -> None:
    handle.write("| " + " | ".join(escape(field) for field in fields) + " |\n")
    handle.write("|" + "|".join("---" for _ in fields) + "|\n")
    for row in rows:
        handle.write("| " + " | ".join(escape(row[field]) for field in fields) + " |\n")


def source_row(path: Path) -> dict[str, object]:
    suffix = path.suffix.lower()
    records: int | str = ""
    if suffix == ".csv":
        with path.open(newline="", encoding="utf-8") as handle:
            records = sum(1 for _ in csv.DictReader(handle))
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "records": records,
        "sha256": sha256(path),
    }


def main() -> None:
    for _, _, path in JSON_SECTIONS:
        if not path.is_file():
            raise FileNotFoundError(path)
    for _, _, path in MARKDOWN_SOURCE_SECTIONS:
        if not path.is_file():
            raise FileNotFoundError(path)
    for _, path in CSV_SECTIONS:
        if not path.is_file():
            raise FileNotFoundError(path)
    for path in INTEGRITY_FILES:
        if not path.is_file():
            raise FileNotFoundError(path)

    original_fit = json.loads((SCALING / "scaling_burn_in_fit.json").read_text(encoding="utf-8"))
    v2_fits = json.loads((V2 / "burn_in_v2_fits.json").read_text(encoding="utf-8"))
    v3_results = json.loads((V3 / "confirmatory_results.json").read_text(encoding="utf-8"))
    if v3_results.get("claim_b_v3_supported") is not True:
        raise AssertionError("Claim-B v3 locked decision is not supported")
    if v3_results.get("original_linear_n_formula_supported") is not False:
        raise AssertionError("retired linear-n formula was incorrectly relabeled")

    csv_payloads: list[tuple[str, Path, list[str], list[dict[str, str]]]] = []
    total_csv_rows = 0
    for heading, path in CSV_SECTIONS:
        fields, rows = csv_rows(path)
        csv_payloads.append((heading, path, fields, rows))
        total_csv_rows += len(rows)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("# HP-SPGG Claim B — Complete Lineage and All Data\n\n")
        handle.write(
            "This single document consolidates the complete Claim-B record: the original preregistered null, "
            "the post-hoc diagnosis, the v2 stochastic pilot, the hash-locked v3 preregistration and decision, "
            "every v2/v3 CSV record, and SHA-256 integrity metadata. It does not overwrite or hide the original null.\n\n"
        )
        handle.write("## Disposition\n\n")
        handle.write(
            f"- Original pooled fit: slope `{original_fit['slope']}`, R-squared `{original_fit['r_squared']}`, "
            f"observations `{original_fit['observations']}` — **unsupported**.\n"
        )
        handle.write(
            "- Original `(n+1) log(m)/(rho H)` formula: **retired**, because Proposition `prop:tid-collapse` "
            "is per-agent and simultaneous-agent control contributes `log(n)`, not linear `n`.\n"
        )
        handle.write(
            f"- V2 pilot type/horizon R-squared: `{v2_fits['type_horizon_fit']['r_squared']}`; "
            f"population R-squared: `{v2_fits['population_fit']['r_squared']}` — promising pilot only.\n"
        )
        handle.write(
            "- V3 corrected target: per-agent `log(m*sqrt(m))/(rho_action*H)` and all-agent "
            "`[log(m*sqrt(m))+log(n)]/(rho_action*H)`.\n"
        )
        handle.write("- V3 locked decision: **SUPPORTED**; all five preregistered gates pass.\n")
        handle.write("- Provider calls across v2 and v3: `0`.\n\n")

        handle.write("## V3 locked-gate headline\n\n")
        gate_rows: list[dict[str, object]] = []
        for gate_name, payload in v3_results["gates"].items():
            gate_rows.append(
                {
                    "gate": gate_name,
                    "passed": payload["passed"],
                    "result": json.dumps(payload, sort_keys=True, separators=(",", ":")),
                }
            )
        write_table(handle, ["gate", "passed", "result"], gate_rows)
        handle.write("\n")

        for marker, title, path in JSON_SECTIONS:
            handle.write(f"## {title}\n\n")
            handle.write(f"<!-- BEGIN {marker} -->\n```json\n")
            handle.write(path.read_text(encoding="utf-8").rstrip("\n"))
            handle.write(f"\n```\n<!-- END {marker} -->\n\n")

        for marker, title, path in MARKDOWN_SOURCE_SECTIONS:
            handle.write(f"## {title}\n\n")
            handle.write(f"<!-- BEGIN {marker} -->\n~~~markdown\n")
            handle.write(path.read_text(encoding="utf-8").rstrip("\n"))
            handle.write(f"\n~~~\n<!-- END {marker} -->\n\n")

        handle.write("## Source integrity\n\n")
        integrity_rows = [source_row(path) for path in INTEGRITY_FILES]
        write_table(handle, ["path", "bytes", "records", "sha256"], integrity_rows)
        handle.write("\n")

        handle.write("## Included row inventory\n\n")
        inventory_rows = []
        for heading, path, _, rows in csv_payloads:
            inventory_rows.append(
                {
                    "section": heading.removeprefix("## "),
                    "source": path.relative_to(ROOT).as_posix(),
                    "rows": len(rows),
                }
            )
        inventory_rows.append({"section": "Total embedded CSV rows", "source": "all tables below", "rows": total_csv_rows})
        write_table(handle, ["section", "source", "rows"], inventory_rows)
        handle.write("\n")

        for heading, path, fields, rows in csv_payloads:
            handle.write(heading + "\n\n")
            handle.write(f"Source: `{path.relative_to(ROOT).as_posix()}`.\n\n")
            write_table(handle, fields, rows)
            handle.write("\n")

    print(
        json.dumps(
            {
                "status": "ok",
                "output": OUTPUT.relative_to(ROOT).as_posix(),
                "bytes": OUTPUT.stat().st_size,
                "csv_rows": total_csv_rows,
                "source_files_hashed": len(INTEGRITY_FILES),
                "sha256": sha256(OUTPUT),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
