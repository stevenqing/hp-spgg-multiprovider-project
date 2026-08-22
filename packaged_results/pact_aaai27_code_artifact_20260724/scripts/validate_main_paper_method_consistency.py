"""Validate the shared LLM-method comparison in main-paper Figures 2, 4, and 6."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile

from paper_comparison_methods import METHOD_LABELS, METHOD_ORDER
import plot_maassim_main_figure as maassim
import run_e_a_matched_likelihood as hp_spgg


ROOT = Path(__file__).resolve().parents[1]
FIGURES = {
    2: ROOT / "arr_paper" / "figs" / "fig_e_a_hp_spgg_matched.pdf",
    4: ROOT / "arr_paper" / "figs" / "fig2_concordia_select_v15.pdf",
    6: ROOT / "arr_paper" / "figs" / "fig_maassim_combined_v22.pdf",
}
REMOVED_COMPARATORS = ("A-ToM-0", "A-ToM-2", "LLM-belief", "Nearest", "PSRL-NoType")


def pdf_text(path: Path) -> str:
    # Poppler stdout is intermittently empty under Windows process capture;
    # using an explicit temporary output file is stable across sequential PDFs.
    with tempfile.TemporaryDirectory(prefix="pact_figure_text_") as temp_name:
        output = Path(temp_name) / "figure.txt"
        subprocess.run(["pdftotext", str(path), str(output)], check=True, capture_output=True)
        return output.read_text(encoding="utf-8", errors="replace")


def main() -> None:
    expected = tuple(METHOD_ORDER)
    if tuple(hp_spgg.PLOT_METHOD_MAP) != expected:
        raise AssertionError(f"Figure 2 method order changed: {tuple(hp_spgg.PLOT_METHOD_MAP)}")
    if tuple(maassim.POLICY_METHOD_MAP) != expected:
        raise AssertionError(f"Figure 6 method order changed: {tuple(maassim.POLICY_METHOD_MAP)}")

    concordia_candidates = (
        ROOT / "arr_paper" / "figs" / "make_fig2_v15.py",
        ROOT / "scripts" / "plot_concordia_selected_main.py",
    )
    concordia_path = next((path for path in concordia_candidates if path.is_file()), None)
    if concordia_path is None:
        raise FileNotFoundError("Figure 4 generator is missing")
    concordia_source = concordia_path.read_text(encoding="utf-8")
    required_source_tokens = (
        "METHOD_COLORS",
        "METHOD_LABELS",
        "METHOD_MARKERS",
        "ORACLE_LINESTYLE",
        '("econ_bne", 1)',
        '("atom_tom1", 2)',
        '("llm_psrl", 4)',
    )
    for token in required_source_tokens:
        if token not in concordia_source:
            raise AssertionError(f"Figure 4 no longer uses shared style token: {token}")
    if "A-ToM-2" in concordia_source:
        raise AssertionError("Figure 4 source reintroduced A-ToM-2")

    required_labels = tuple(METHOD_LABELS[method] for method in METHOD_ORDER)
    details: dict[int, dict[str, object]] = {}
    for number, path in FIGURES.items():
        if not path.is_file() or path.stat().st_size < 10_000:
            raise AssertionError(f"Figure {number} is missing or unexpectedly small: {path}")
        text = pdf_text(path)
        missing = [label for label in required_labels if label not in text]
        removed = [label for label in REMOVED_COMPARATORS if label in text]
        if missing or removed:
            raise AssertionError(f"Figure {number}: missing={missing}, removed labels present={removed}")
        details[number] = {
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "methods": list(required_labels),
            "removed_comparators_present": [],
        }

    print(
        json.dumps(
            {
                "status": "ok",
                "method_order": list(expected),
                "method_labels": list(required_labels),
                "oracle_role": "neutral reference, not a compared LLM method",
                "figures": details,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
