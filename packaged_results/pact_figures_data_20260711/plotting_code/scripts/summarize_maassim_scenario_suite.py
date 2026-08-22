"""Summarize MaaSSim LLM scenario-suite results."""

from __future__ import annotations

import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis" / "courier_dispatch_maassim"
FIG_DIRS = [ROOT / "figs", ROOT / "arr_paper" / "figs"]

SCENARIOS = [
    {
        "scenario_id": "normal_p2",
        "label": "Normal",
        "description": "Original common-state replay, driver reject penalty 2.0",
        "files": ["maassim_llm_scenario_normal_p2_noecon_s5_m20.csv", "maassim_llm_scenario_normal_p2_econ_s5_m20.csv"],
    },
    {
        "scenario_id": "stress_p5",
        "label": "Reject-stress",
        "description": "Original common-state replay, driver reject penalty 5.0",
        "files": ["maassim_llm_prompt_stress_s5_m20.csv"],
    },
    {
        "scenario_id": "conflict_p5",
        "label": "Conflict-offer",
        "description": "Low-wait offers are made persona-risky; driver reject penalty 5.0",
        "files": ["maassim_llm_scenario_conflict_noecon_s5_m20.csv", "maassim_llm_scenario_conflict_econ_s5_m20.csv"],
    },
]

POLICY_LABELS = {
    "llm": "LLM-PACT",
    "llm_belief": "LLM-belief",
    "llm_psrl": "LLM-PSRL",
    "atom_tom1": "A-ToM-1",
    "econ_bne": "ECON-BNE",
    "nearest": "Nearest",
    "random": "Random",
    "oracle": "Oracle",
}
PURE_PROMPT = ["llm_belief", "llm_psrl", "atom_tom1", "econ_bne"]


def read_scenario(files: list[str]) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for file_name in files:
        path = ANALYSIS / file_name
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                rows[str(row["policy"])] = row
    return rows


def f(row: dict[str, str], key: str) -> float:
    value = row.get(key, "nan")
    try:
        return float(value)
    except Exception:
        return float("nan")


def fmt(value: float, digits: int = 2) -> str:
    if math.isnan(value):
        return "n/a"
    return f"{value:.{digits}f}"


def summarize() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    summary_rows = []
    detail_rows = []
    for spec in SCENARIOS:
        rows = read_scenario(spec["files"])
        for policy, row in rows.items():
            detail_rows.append(
                {
                    "scenario_id": spec["scenario_id"],
                    "scenario": spec["label"],
                    "policy": policy,
                    "label": POLICY_LABELS.get(policy, policy),
                    "utility": f(row, "realized_utility"),
                    "utility_sem": f(row, "realized_utility_sem"),
                    "driver_rejects": f(row, "driver_rejects"),
                    "driver_accept_rate": f(row, "driver_accept_rate"),
                    "served": f(row, "served"),
                }
            )
        llm_row = rows["llm"]
        best_prompt = max(PURE_PROMPT, key=lambda policy: f(rows[policy], "realized_utility"))
        best_row = rows[best_prompt]
        summary_rows.append(
            {
                "scenario_id": spec["scenario_id"],
                "scenario": spec["label"],
                "description": spec["description"],
                "llm_pact_utility": f(llm_row, "realized_utility"),
                "llm_pact_utility_sem": f(llm_row, "realized_utility_sem"),
                "llm_pact_driver_rejects": f(llm_row, "driver_rejects"),
                "best_prompt_policy": best_prompt,
                "best_prompt_label": POLICY_LABELS[best_prompt],
                "best_prompt_utility": f(best_row, "realized_utility"),
                "best_prompt_utility_sem": f(best_row, "realized_utility_sem"),
                "best_prompt_driver_rejects": f(best_row, "driver_rejects"),
                "utility_gap": f(llm_row, "realized_utility") - f(best_row, "realized_utility"),
                "driver_reject_gap": f(best_row, "driver_rejects") - f(llm_row, "driver_rejects"),
                "oracle_utility": f(rows["oracle"], "realized_utility"),
            }
        )
    return summary_rows, detail_rows


def write_csv(rows: list[dict[str, object]], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_md(summary_rows: list[dict[str, object]], detail_rows: list[dict[str, object]]) -> None:
    lines = [
        "# MaaSSim LLM Scenario Suite",
        "",
        "This suite implements the first three environment-design knobs: normal replay, reject-penalty stress, and conflict-offer stress. The comparison is LLM-PACT against pure LLM prompt baselines under the same legal-action interface.",
        "",
        "| Scenario | LLM-PACT utility | Best prompt baseline | Prompt utility | Utility gap | Driver reject gap | Oracle utility |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            "| {scenario} | {llm} +/- {llm_sem} | {prompt} | {prompt_u} +/- {prompt_sem} | {gap} | {reject_gap} | {oracle} |".format(
                scenario=row["scenario"],
                llm=fmt(float(row["llm_pact_utility"])),
                llm_sem=fmt(float(row["llm_pact_utility_sem"])),
                prompt=row["best_prompt_label"],
                prompt_u=fmt(float(row["best_prompt_utility"])),
                prompt_sem=fmt(float(row["best_prompt_utility_sem"])),
                gap=fmt(float(row["utility_gap"])),
                reject_gap=fmt(float(row["driver_reject_gap"]), 1),
                oracle=fmt(float(row["oracle_utility"])),
            )
        )
    lines.extend(
        [
            "",
            "Readout: the LLM-PACT advantage grows as the environment makes persona mistakes more consequential. The gap is small in the normal setting, larger under rejection-cost stress, and largest when low-wait offers are made persona-risky.",
            "",
            "## Detail Rows",
            "",
            "| Scenario | Policy | Utility | Driver rejects | Served | Driver accept |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in detail_rows:
        if str(row["policy"]) not in {"llm", "llm_belief", "llm_psrl", "atom_tom1", "econ_bne", "oracle"}:
            continue
        lines.append(
            "| {scenario} | {label} | {utility} +/- {sem} | {rejects} | {served} | {accept} |".format(
                scenario=row["scenario"],
                label=row["label"],
                utility=fmt(float(row["utility"])),
                sem=fmt(float(row["utility_sem"])),
                rejects=fmt(float(row["driver_rejects"]), 1),
                served=fmt(float(row["served"]), 1),
                accept=fmt(float(row["driver_accept_rate"]), 3),
            )
        )
    (ANALYSIS / "maassim_llm_scenario_suite_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def plot(summary_rows: list[dict[str, object]]) -> None:
    labels = [str(row["scenario"]) for row in summary_rows]
    x = range(len(summary_rows))
    gaps = [float(row["utility_gap"]) for row in summary_rows]
    reject_gaps = [float(row["driver_reject_gap"]) for row in summary_rows]
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Inter", "Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": 9})
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.1))
    axes[0].bar(x, gaps, color="#12345d", edgecolor="white")
    axes[0].set_xticks(list(x))
    axes[0].set_xticklabels(labels, rotation=15, ha="right")
    axes[0].set_ylabel("Utility gap")
    axes[0].set_title("LLM-PACT minus best prompt", loc="left", fontweight="semibold")
    axes[1].bar(x, reject_gaps, color="#2f7d5b", edgecolor="white")
    axes[1].set_xticks(list(x))
    axes[1].set_xticklabels(labels, rotation=15, ha="right")
    axes[1].set_ylabel("Fewer driver rejects")
    axes[1].set_title("Reject reduction", loc="left", fontweight="semibold")
    for ax in axes:
        ax.grid(axis="y", linestyle=":", linewidth=0.55, color="#d9dde3")
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
    fig.tight_layout()
    for out_dir in FIG_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_dir / "fig_maassim_llm_scenario_suite.png", bbox_inches="tight", facecolor="white")
        fig.savefig(out_dir / "fig_maassim_llm_scenario_suite.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    summary_rows, detail_rows = summarize()
    write_csv(summary_rows, ANALYSIS / "maassim_llm_scenario_suite_summary.csv")
    write_csv(detail_rows, ANALYSIS / "maassim_llm_scenario_suite_detail.csv")
    write_md(summary_rows, detail_rows)
    plot(summary_rows)
    print("OK: analysis/courier_dispatch_maassim/maassim_llm_scenario_suite_summary.md")


if __name__ == "__main__":
    main()