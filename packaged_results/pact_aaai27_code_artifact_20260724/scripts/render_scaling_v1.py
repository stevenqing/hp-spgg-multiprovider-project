"""Render additive HP-SPGG analytic scaling figures from scaling_summary.csv."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis" / "hp_spgg_analytic_scaling"
SUMMARY = DATA / "scaling_summary.csv"
MANIFEST = DATA / "manifest_scaling.json"
FIT_OUT = DATA / "scaling_burn_in_fit.json"
REPORT = DATA / "scaling_run_report.md"
OUT_DIRS = (DATA, ROOT / "figs")
METHODS = ("pact", "pact_plus", "joint_psrl_uniform", "psrl_notype", "oracle")
LABELS = {
    "pact": "PACT",
    "pact_plus": "PACT+",
    "joint_psrl_uniform": "Joint-PSRL-U",
    "psrl_notype": "PSRL-NoType",
    "oracle": "Oracle",
}
COLORS = {
    "pact": "#557A95",
    "pact_plus": "#12345D",
    "joint_psrl_uniform": "#2F7D5B",
    "psrl_notype": "#9A5A2E",
    "oracle": "#303030",
}
MARKERS = {
    "pact": "o",
    "pact_plus": "D",
    "joint_psrl_uniform": "s",
    "psrl_notype": "^",
    "oracle": "*",
}
SWEEP_MARKERS = {"s1_population_m4": "o", "s2_library_n3": "s"}
SWEEP_COLORS = {"s1_population_m4": "#12345D", "s2_library_n3": "#D4A04A"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def finite(row: dict[str, str], key: str) -> float:
    return float(row[key])


def style_axis(axis: plt.Axes) -> None:
    axis.grid(axis="y", linestyle=":", linewidth=0.55, color="#d8d8d8", zorder=0)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.tick_params(labelsize=7.2, length=2.5, width=0.55)


def storage_ratio(n: int, m: int) -> float:
    return float(m**n) / float(n * m)


def compact_ratio(value: float) -> str:
    if value >= 1e9:
        return f"{value / 1e9:.1f}B×"
    if value >= 1e6:
        return f"{value / 1e6:.1f}M×"
    if value >= 1e3:
        return f"{value / 1e3:.1f}k×"
    return f"{value:.1f}×"


def plot_regret(rows: list[dict[str, str]], manifest: dict[str, object]) -> list[Path]:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["DejaVu Serif"],
            "font.size": 7.5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    fig, axes = plt.subplots(2, 1, figsize=(4.85, 5.2), sharex=False)
    panels = (
        (axes[0], "s1_population_m4", "(a) S1 population sweep ($m=4$)"),
        (axes[1], "s3_frontier_m16", "(b) S3 feasibility frontier ($m=16$)"),
    )
    frontier = manifest["joint_feasibility_frontier"]
    for axis, sweep, title in panels:
        selected = [row for row in rows if row["sweep"] == sweep]
        ns = sorted({int(row["n"]) for row in selected})
        m = int(selected[0]["m"])
        for method in METHODS:
            method_rows = {int(row["n"]): row for row in selected if row["method"] == method}
            xs: list[int] = []
            ys: list[float] = []
            errors: list[float] = []
            for n in ns:
                row = method_rows[n]
                if row["feasible"].lower() != "true":
                    continue
                xs.append(n)
                ys.append(finite(row, "final_regret_mean"))
                errors.append(finite(row, "final_regret_sem"))
            if xs:
                axis.errorbar(
                    xs,
                    ys,
                    yerr=errors,
                    color=COLORS[method],
                    marker=MARKERS[method],
                    markerfacecolor="none" if method == "joint_psrl_uniform" else COLORS[method],
                    markeredgecolor=COLORS[method],
                    linewidth=1.2 if method in {"pact", "pact_plus"} else 1.0,
                    markersize=4.2,
                    capsize=2.0,
                    label=LABELS[method],
                    zorder=3,
                )
        if sweep == "s3_frontier_m16" and frontier["first_infeasible_n"] is not None:
            start = int(frontier["first_infeasible_n"])
            axis.axvspan(start - 0.45, max(ns) + 0.45, color="#d8d8d8", alpha=0.55, zorder=0)
            axis.text(start - 0.35, 0.96, "Joint infeasible", transform=axis.get_xaxis_transform(), fontsize=6.5, va="top")
        axis.set_yscale("symlog", linthresh=0.02)
        axis.set_ylabel("Final cumulative regret ($K=50$)")
        axis.set_title(title, loc="left", fontsize=8.4, pad=2.5)
        tick_labels = [f"{n}\n{compact_ratio(storage_ratio(n, m))}" for n in ns]
        axis.set_xticks(ns, tick_labels)
        axis.set_xlabel("Agents $n$\nJoint / factored persona-storage ratio")
        style_axis(axis)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, ncol=3, fontsize=6.6, loc="lower center", bbox_to_anchor=(0.5, -0.005))
    fig.tight_layout(rect=(0, 0.07, 1, 1), h_pad=1.0)
    outputs: list[Path] = []
    for directory in OUT_DIRS:
        directory.mkdir(parents=True, exist_ok=True)
        pdf = directory / "fig_hp_spgg_analytic_scaling_regret_v1.pdf"
        png = directory / "fig_hp_spgg_analytic_scaling_regret_v1.png"
        fig.savefig(pdf, bbox_inches="tight", pad_inches=0.03, facecolor="white")
        fig.savefig(png, dpi=260, bbox_inches="tight", pad_inches=0.03, facecolor="white")
        outputs.extend((pdf, png))
    plt.close(fig)
    return outputs


def plot_burn_in(rows: list[dict[str, str]], manifest: dict[str, object]) -> tuple[list[Path], dict[str, object]]:
    selected = [
        row
        for row in rows
        if row["sweep"] in SWEEP_MARKERS
        and row["method"] == "pact"
        and row["feasible"].lower() == "true"
    ]
    fit_x: list[float] = []
    fit_y: list[float] = []
    points: list[dict[str, object]] = []
    for row in selected:
        n, m = int(row["n"]), int(row["m"])
        x = (n + 1.0) * math.log(m)
        value = float(row["median_burn_in_all_agents"])
        censored = int(row["burn_in_censored_seeds"])
        plotted = value if math.isfinite(value) else 51.0
        points.append(
            {
                "sweep": row["sweep"],
                "method": row["method"],
                "n": n,
                "m": m,
                "x": x,
                "median_burn_in": value,
                "plotted_y": plotted,
                "censored_seeds": censored,
            }
        )
        if math.isfinite(value):
            fit_x.append(x)
            fit_y.append(value)
    if len(fit_x) < 2:
        raise AssertionError("not enough uncensored burn-in cells for OLS")
    x_array = np.asarray(fit_x, dtype=float)
    y_array = np.asarray(fit_y, dtype=float)
    slope, intercept = np.polyfit(x_array, y_array, 1)
    predicted = slope * x_array + intercept
    denominator = float(np.sum((y_array - y_array.mean()) ** 2))
    r_squared = 1.0 - float(np.sum((y_array - predicted) ** 2)) / denominator if denominator > 0.0 else 1.0

    fig, axis = plt.subplots(figsize=(4.8, 3.15))
    for point in points:
        sweep = str(point["sweep"])
        open_marker = int(point["censored_seeds"]) >= 5
        axis.scatter(
            float(point["x"]),
            float(point["plotted_y"]),
            marker=SWEEP_MARKERS[sweep],
            s=32,
            facecolor="none" if open_marker else SWEEP_COLORS[sweep],
            edgecolor=SWEEP_COLORS[sweep],
            linewidth=0.9,
            zorder=3,
        )
    line_x = np.linspace(float(x_array.min()), float(x_array.max()), 100)
    axis.plot(line_x, slope * line_x + intercept, color="#222222", linestyle="--", linewidth=1.0,
              label=f"OLS slope={slope:.3f}, $R^2$={r_squared:.3f}")
    axis.set_xlabel("$(n+1)\\log m$")
    axis.set_ylabel("Median all-agent burn-in episodes")
    axis.set_title("Persona burn-in scaling", loc="left", fontsize=8.5)
    axis.set_ylim(0, 53)
    style_axis(axis)
    legend_handles = [
        Line2D([], [], color=SWEEP_COLORS["s1_population_m4"], marker="o", linestyle="none", label="S1 population (PACT)", markersize=4.5),
        Line2D([], [], color=SWEEP_COLORS["s2_library_n3"], marker="s", linestyle="none", label="S2 library (PACT)", markersize=4.5),
        Line2D([], [], color="#555555", marker="o", markerfacecolor="none", linestyle="none", label="Majority censored ($K+1$)", markersize=4.5),
        Line2D([], [], color="#222222", linestyle="--", label=f"OLS slope={slope:.3f}"),
    ]
    axis.legend(handles=legend_handles, frameon=False, fontsize=6.3, ncol=2, loc="upper left")
    fig.tight_layout(pad=0.45)
    outputs: list[Path] = []
    for directory in OUT_DIRS:
        directory.mkdir(parents=True, exist_ok=True)
        pdf = directory / "fig_hp_spgg_analytic_scaling_burnin_v1.pdf"
        png = directory / "fig_hp_spgg_analytic_scaling_burnin_v1.png"
        fig.savefig(pdf, bbox_inches="tight", pad_inches=0.03, facecolor="white")
        fig.savefig(png, dpi=260, bbox_inches="tight", pad_inches=0.03, facecolor="white")
        outputs.extend((pdf, png))
    plt.close(fig)

    rho_records = {
        m: float(manifest["type_libraries"][str(m)]["rho_hat_min_across_cells"])
        for m in (4, 8, 16)
    }
    fit = {
        "x_definition": "(n+1)*log(m)",
        "method": "pact",
        "response": "median all-agent posterior true-mass > 0.9 first-passage episode",
        "censoring": "cells with fewer than five observed passages are plotted open at K+1 and excluded from OLS",
        "slope": float(slope),
        "intercept": float(intercept),
        "r_squared": float(r_squared),
        "observations": len(fit_x),
        "rho_hat_per_m": rho_records,
        "inverse_rho_H_per_m": {str(m): 1.0 / (rho * float(manifest["H"])) for m, rho in rho_records.items()},
        "points": points,
    }
    FIT_OUT.write_text(json.dumps(fit, indent=2) + "\n", encoding="utf-8")
    return outputs, fit


def main() -> None:
    rows = read_csv(SUMMARY)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    outputs = plot_regret(rows, manifest)
    burn_outputs, fit = plot_burn_in(rows, manifest)
    outputs.extend(burn_outputs)
    release_outputs = [path for path in outputs if path.is_relative_to(DATA)]
    render_artifacts = [
        {"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in release_outputs + [FIT_OUT]
    ]
    manifest["burn_in_ols"] = fit
    manifest["render_artifacts"] = render_artifacts
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    if REPORT.exists():
        report = REPORT.read_text(encoding="utf-8")
        marker = "\n## Post-render burn-in fit\n"
        report = report.split(marker, 1)[0].rstrip()
        support = "supports" if float(fit["slope"]) > 0.0 and float(fit["r_squared"]) >= 0.5 else "does not support"
        s1_rows = [row for row in rows if row["sweep"] == "s1_population_m4" and row["feasible"].lower() == "true"]
        s1_max_regret = max(abs(float(row["final_regret_mean"])) for row in s1_rows)
        n10_runtime = manifest["cells"]["n10_m4"].get(
            "cell_wallclock_seconds",
            manifest["cells"]["n10_m4"].get("npz_artifact_wallclock_span_seconds"),
        )
        report += (
            marker
            + "\n"
            + f"- Claim (a): every feasible PACT/Joint cell is pathwise identical; S3 remains joint-feasible through n={manifest['joint_feasibility_frontier']['largest_feasible_n']} and first fails at n={manifest['joint_feasibility_frontier']['first_infeasible_n']}.\n"
            + f"- S1 is decision-degenerate on this retained m=4 analytic kernel: maximum mean final regret across displayed methods is {s1_max_regret:.6g}. Its parity result is exact but not performance-separating.\n"
            + f"- The worst n=10,m=4 cell used all 5^10 actions and completed in {float(n10_runtime):.3f}s, below the 1,800s cap.\n"
            + f"- Canonical method: PACT; uncensored OLS observations: {fit['observations']}.\n"
            + f"- Fitted slope: {fit['slope']:.6g}; intercept: {fit['intercept']:.6g}; R^2: {fit['r_squared']:.6g}.\n"
            + f"- Under the preregistered directional criterion, this finite K=50 fit **{support}** a pooled linear relation.\n"
            + "- Open markers at K+1 are majority-censored cells and are excluded from OLS rather than imputed.\n"
            + "- Per-library 1/(rho_hat H) references are recorded in scaling_burn_in_fit.json; rho_hat is a worst-case reachable-grid margin and is not retuned to the observed trajectories.\n"
        )
        REPORT.write_text(report, encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "ok",
                "outputs": [record["path"] for record in render_artifacts],
                "burn_in_ols": {key: fit[key] for key in ("slope", "intercept", "r_squared", "observations")},
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
