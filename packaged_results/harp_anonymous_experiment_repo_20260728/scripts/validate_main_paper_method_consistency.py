"""Validate the restored method sets and styles in main-paper Figures 2, 4, and 5."""

from __future__ import annotations

import json
from pathlib import Path

import fitz

from paper_comparison_methods import METHOD_COLORS, METHOD_LABELS, METHOD_ORDER, ORACLE_COLOR
import plot_maassim_main_figure as maassim
import render_harp_maassim_main_v21 as maassim_v21
import run_e_a_matched_likelihood as hp_spgg


ROOT = Path(__file__).resolve().parents[1]
FIGURES = {
    2: ROOT / "arr_paper" / "figs" / "fig_e_a_hp_spgg_matched.pdf",
    4: ROOT / "arr_paper" / "figs" / "fig_maassim_combined_v21.pdf",
    5: ROOT / "arr_paper" / "figs" / "fig2_concordia_select_v15.pdf",
}
EXPECTED_LABELS = {
    2: ("Oracle", "HARP+", "HARP", "Joint-PSRL", "LLM-PSRL", "PSRL-NoType", "A-ToM-1", "ECON-BNE"),
    4: ("HARP", "LLM-belief", "LLM-PSRL", "A-ToM-1", "ECON-BNE", "Nearest", "Oracle"),
    5: ("HARP family (ours)", "LLM-PSRL", "A-ToM-1", "ECON-BNE", "Oracle reference"),
}
FIGURE5_DATA = ROOT / "arr_paper" / "data" / "figure5_haggling_llm_psrl.json"
FIGURE5_BAR_DATA = ROOT / "arr_paper" / "data" / "figure5_bar_data.json"
FIGURE5_CONFIGS = (
    "haggling/vegbrooke",
    "haggling/vegbrooke_stubborn",
    "haggling_multi_item/fruitville_gullible",
    "haggling/fruitville",
)
FIGURE5_TIERS = ("deepseek", "gpt5_nano", "kimi_k2", "llama_maverick")


def pdf_text(path: Path) -> str:
    with fitz.open(path) as document:
        return "\n".join(page.get_text() for page in document)


def main() -> None:
    expected = tuple(METHOD_ORDER)
    expected_figure2_order = ("oracle", "hpsmg_plus", "hpsmg", "joint_psrl", "llm_psrl_verbal", "psrl_notype", "atom_tom1", "econ_bne")
    if tuple(hp_spgg.FIGURE2_PLOT_ORDER) != expected_figure2_order:
        raise AssertionError(f"Figure 2 method order changed: {tuple(hp_spgg.FIGURE2_PLOT_ORDER)}")
    if tuple(maassim.POLICY_METHOD_MAP) != expected:
        raise AssertionError(f"Figure 4 core method order changed: {tuple(maassim.POLICY_METHOD_MAP)}")
    expected_figure2_colors = {
        "hpsmg_plus": METHOD_COLORS["pact_family"],
        "llm_psrl_verbal": METHOD_COLORS["llm_psrl"],
        "atom_tom1": METHOD_COLORS["atom_tom1"],
        "econ_bne": METHOD_COLORS["econ_bne"],
    }
    for method, color in expected_figure2_colors.items():
        if hp_spgg.COLORS[method] != color:
            raise AssertionError(f"Figure 2 color drift for {method}: {hp_spgg.COLORS[method]}")
    figure4_colors = {policy: color for policy, _, color in maassim_v21.POLICIES}
    expected_figure4_colors = {
        "llm": METHOD_COLORS["pact_family"],
        "llm_psrl": METHOD_COLORS["llm_psrl"],
        "atom_tom1": METHOD_COLORS["atom_tom1"],
        "econ_bne": METHOD_COLORS["econ_bne"],
    }
    for policy, color in expected_figure4_colors.items():
        if figure4_colors[policy] != color:
            raise AssertionError(f"Figure 4(a) color drift for {policy}: {figure4_colors[policy]}")
    if maassim_v21.ORACLE_COLOR != ORACLE_COLOR:
        raise AssertionError(f"Figure 4(a) Oracle color drift: {maassim_v21.ORACLE_COLOR}")

    concordia_candidates = (
        ROOT / "arr_paper" / "figs" / "make_fig2_v15.py",
        ROOT / "scripts" / "plot_concordia_selected_main.py",
    )
    concordia_path = next((path for path in concordia_candidates if path.is_file()), None)
    if concordia_path is None:
        raise FileNotFoundError("Figure 5 generator is missing")
    concordia_source = concordia_path.read_text(encoding="utf-8")
    required_source_tokens = (
        "METHOD_COLORS",
        "METHOD_LABELS",
        "ORACLE_LINESTYLE",
        "figure5_bar_data.json",
        "yerr=errors",
        "PLOT_METHODS = ('pact_family', 'llm_psrl', 'atom_tom1', 'econ_bne')",
    )
    for token in required_source_tokens:
        if token not in concordia_source:
            raise AssertionError(f"Figure 5 no longer uses shared style token: {token}")
    if "A-ToM-2" in concordia_source:
        raise AssertionError("Figure 5 source reintroduced A-ToM-2")

    figure5_data = json.loads(FIGURE5_DATA.read_text(encoding="utf-8"))
    if figure5_data.get("seed_schedule") != list(range(30)):
        raise AssertionError("Figure 5 LLM-PSRL seed schedule is not exactly 0..29")
    configurations = figure5_data.get("configurations", {})
    if tuple(configurations) != FIGURE5_CONFIGS:
        raise AssertionError(f"Unexpected Figure 5 configurations: {tuple(configurations)}")
    for config, cell in configurations.items():
        models = cell.get("models", [])
        if tuple(row.get("tier") for row in models) != FIGURE5_TIERS:
            raise AssertionError(f"Unexpected Figure 5 tiers for {config}: {models}")
        for row in models:
            if row.get("seed_count") != 30:
                raise AssertionError(f"Incomplete Figure 5 seeds for {config}/{row.get('tier')}")
            if row.get("sample_ok_count") != row.get("deal_count"):
                raise AssertionError(f"Figure 5 fallback response for {config}/{row.get('tier')}")

    bar_data = json.loads(FIGURE5_BAR_DATA.read_text(encoding="utf-8"))
    bar_configurations = bar_data.get("configurations", {})
    if len(bar_configurations) != 8:
        raise AssertionError(f"Figure 5 mean/SEM table has {len(bar_configurations)} configurations")
    expected_bar_methods = {"pact_family", "llm_psrl", "atom_tom1", "econ_bne", "oracle"}
    for config, cell in bar_configurations.items():
        methods = cell.get("methods", {})
        if set(methods) != expected_bar_methods:
            raise AssertionError(f"Unexpected Figure 5 methods for {config}: {set(methods)}")
        for method, estimate in methods.items():
            if int(estimate.get("n", 0)) <= 0:
                raise AssertionError(f"Figure 5 has no observations for {config}/{method}")
            if float(estimate.get("sem", -1.0)) < 0.0:
                raise AssertionError(f"Figure 5 has invalid SEM for {config}/{method}")

    details: dict[int, dict[str, object]] = {}
    for number, path in FIGURES.items():
        if not path.is_file() or path.stat().st_size < 10_000:
            raise AssertionError(f"Figure {number} is missing or unexpectedly small: {path}")
        text = pdf_text(path)
        required_labels = EXPECTED_LABELS[number]
        missing = [label for label in required_labels if label not in text]
        if missing:
            raise AssertionError(f"Figure {number}: missing={missing}")
        if number == 2:
            forbidden = [label for label in ("A-ToM-0", "A-ToM-2") if label in text]
            if forbidden:
                raise AssertionError(f"Figure 2 retained removed methods: {forbidden}")
        details[number] = {
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "methods": list(required_labels),
        }

    print(
        json.dumps(
            {
                "status": "ok",
                "method_order": list(expected),
                "figure_label_sets": {str(number): list(labels) for number, labels in EXPECTED_LABELS.items()},
                "oracle_role": "neutral reference, not a compared LLM method",
                "shared_palette": METHOD_COLORS,
                "figure5_llm_psrl": {
                    "configurations": list(FIGURE5_CONFIGS),
                    "tiers": list(FIGURE5_TIERS),
                    "seeds_per_cell": 30,
                    "fallback_deals": 0,
                },
                "figure5_error_bars": {
                    "configurations": len(bar_configurations),
                    "method_estimates_per_configuration": len(expected_bar_methods),
                    "measure": "SEM",
                },
                "figures": details,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
