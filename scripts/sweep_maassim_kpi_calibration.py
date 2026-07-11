"""Sweep MaaSSim KPI policy weights for controlled synthetic runs."""

from __future__ import annotations

import csv
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis" / "courier_dispatch_maassim"
RUNNER = ROOT / "scripts" / "run_maassim_shadow_smoke.py"
WAIT_WEIGHTS = [0.04, 0.08, 0.12]
REJECT_PENALTIES = [0.0, 0.25, 0.5]
FARE_WEIGHTS = [0.0, 0.5]
SEEDS = list(range(5))


def tag(value: float) -> str:
    return str(value).replace(".", "p")


def mean(values: list[float]) -> float:
    return float(sum(values) / len(values)) if values else float("nan")


def sem(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = mean(values)
    return float(math.sqrt(sum((value - avg) ** 2 for value in values) / (len(values) - 1)) / math.sqrt(len(values)))


def run_one(wait_weight: float, reject_penalty: float, fare_weight: float, seed: int) -> Path:
    prefix = f"pact_kpi_calib_w{tag(wait_weight)}_r{tag(reject_penalty)}_f{tag(fare_weight)}_s{seed}"
    summary = ANALYSIS / f"{prefix}_summary.json"
    if summary.exists():
        return summary
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{ROOT / 'external' / 'maassim'};{ROOT}"
    cmd = [
        sys.executable,
        str(RUNNER),
        "--seed",
        str(seed),
        "--config",
        str(ROOT / "external" / "maassim" / "MaaSSim" / "data" / "config.json"),
        "--root-path",
        str(ROOT / "external" / "maassim" / "MaaSSim"),
        "--n-passengers",
        "40",
        "--n-vehicles",
        "8",
        "--batch-time",
        "120",
        "--policy",
        "pact_kpi",
        "--beta",
        "0.25",
        "--control-match",
        "--synthetic-rules",
        "--intervene-driver-rules",
        "--long-trip-seconds",
        "300",
        "--far-pickup-seconds",
        "180",
        "--surge-fare-per-second",
        "0.006",
        "--home-after-seconds",
        "2700",
        "--kpi-wait-weight",
        str(wait_weight),
        "--kpi-reject-penalty",
        str(reject_penalty),
        "--kpi-fare-weight",
        str(fare_weight),
        "--out",
        str(ANALYSIS / f"{prefix}_queue_snapshots.jsonl"),
        "--posterior-out",
        str(ANALYSIS / f"{prefix}_rule_posterior.csv"),
        "--rides-out",
        str(ANALYSIS / f"{prefix}_rides.csv"),
        "--trips-out",
        str(ANALYSIS / f"{prefix}_trips.csv"),
        "--summary-out",
        str(summary),
    ]
    subprocess.run(cmd, check=True, cwd=ROOT, env=env)
    return summary


def value(payload: dict, section: str, key: str) -> float:
    return float((payload.get(section) or {}).get(key, float("nan")))


def summarize(paths_by_combo: dict[tuple[float, float, float], list[Path]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for (wait_weight, reject_penalty, fare_weight), paths in sorted(paths_by_combo.items()):
        payloads = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
        row = {
            "wait_weight": wait_weight,
            "reject_penalty": reject_penalty,
            "fare_weight": fare_weight,
            "seeds": len(payloads),
        }
        metrics = {
            "mean_wait": ("maassim_summary", "pax_wait_mean"),
            "rides": ("maassim_summary", "veh_nrides_sum"),
            "rejects": ("maassim_summary", "veh_nrejects_sum"),
            "lost_patience": ("maassim_summary", "pax_loses_patience_mean"),
            "ptrue": ("posterior_summary", "mean_final_ptrue"),
            "rule_acc": ("posterior_summary", "mean_final_rule_acc"),
            "decline_rate": ("posterior_summary", "synthetic_decline_rate"),
        }
        for metric, (section, key) in metrics.items():
            vals = [value(payload, section, key) for payload in payloads]
            row[metric] = mean(vals)
            row[f"{metric}_sem"] = sem(vals)
        rows.append(row)
    return rows


def write_outputs(rows: list[dict[str, object]]) -> None:
    csv_path = ANALYSIS / "maassim_kpi_calibration_sweep.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "# MaaSSim KPI Calibration Sweep",
        "",
        "Batch controlled synthetic setting: `nP=40`, `nV=8`, `batch_time=120`, seeds `{0,1,2,3,4}`.",
        "",
        "| wait_weight | reject_penalty | fare_weight | Mean wait | Rides | Rejects | Lost patience | P(true) | Rule acc |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {wait:.3f} | {reject:.2f} | {fare:.1f} | {mw:.1f} +/- {mwsem:.1f} | {rides:.1f} | {rejects:.1f} | {lost:.1f} | {p:.3f} | {acc:.3f} |".format(
                wait=float(row["wait_weight"]),
                reject=float(row["reject_penalty"]),
                fare=float(row["fare_weight"]),
                mw=float(row["mean_wait"]),
                mwsem=float(row["mean_wait_sem"]),
                rides=float(row["rides"]),
                rejects=float(row["rejects"]),
                lost=float(row["lost_patience"]),
                p=float(row["ptrue"]),
                acc=float(row["rule_acc"]),
            )
        )
    best_wait = min(rows, key=lambda row: float(row["mean_wait"]))
    best_reject = min(rows, key=lambda row: float(row["rejects"]))
    lines.extend(
        [
            "",
            f"Best mean wait: `wait_weight={best_wait['wait_weight']}`, `reject_penalty={best_wait['reject_penalty']}`, `fare_weight={best_wait['fare_weight']}` with mean wait `{float(best_wait['mean_wait']):.1f}`.",
            f"Fewest rejects: `wait_weight={best_reject['wait_weight']}`, `reject_penalty={best_reject['reject_penalty']}`, `fare_weight={best_reject['fare_weight']}` with rejects `{float(best_reject['rejects']):.1f}`.",
        ]
    )
    (ANALYSIS / "maassim_kpi_calibration_sweep.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    plot_heatmaps(rows)
    print(json.dumps({"rows": len(rows), "csv": str(csv_path.relative_to(ROOT))}, indent=2))


def plot_heatmaps(rows: list[dict[str, object]]) -> None:
    waits = sorted({float(row["wait_weight"]) for row in rows})
    rejects = sorted({float(row["reject_penalty"]) for row in rows})
    fares = sorted({float(row["fare_weight"]) for row in rows})
    fig, axes = plt.subplots(len(fares), 2, figsize=(8.2, 3.4 * len(fares)), squeeze=False)
    metrics = [("mean_wait", "Mean wait"), ("rejects", "Rejects")]
    for row_idx, fare_weight in enumerate(fares):
        subset = [row for row in rows if float(row["fare_weight"]) == fare_weight]
        for col_idx, (metric, title) in enumerate(metrics):
            matrix = np.full((len(waits), len(rejects)), np.nan)
            for row in subset:
                i = waits.index(float(row["wait_weight"]))
                j = rejects.index(float(row["reject_penalty"]))
                matrix[i, j] = float(row[metric])
            ax = axes[row_idx, col_idx]
            image = ax.imshow(matrix, aspect="auto", cmap="viridis_r" if metric == "mean_wait" else "magma_r")
            ax.set_xticks(range(len(rejects)))
            ax.set_xticklabels([f"{value:g}" for value in rejects])
            ax.set_yticks(range(len(waits)))
            ax.set_yticklabels([f"{value:g}" for value in waits])
            ax.set_xlabel("reject_penalty")
            ax.set_ylabel("wait_weight")
            ax.set_title(f"{title}, fare_weight={fare_weight:g}")
            for i in range(len(waits)):
                for j in range(len(rejects)):
                    ax.text(j, i, f"{matrix[i, j]:.1f}", ha="center", va="center", color="white", fontsize=8)
            fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.suptitle("MaaSSim KPI calibration sweep", x=0.02, y=1.0, ha="left", fontsize=12, fontweight="semibold")
    fig.tight_layout()
    for out_dir in [ROOT / "figs", ROOT / "arr_paper" / "figs"]:
        out_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_dir / "fig_maassim_kpi_calibration_sweep.png", bbox_inches="tight", facecolor="white")
        fig.savefig(out_dir / "fig_maassim_kpi_calibration_sweep.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    paths_by_combo: dict[tuple[float, float, float], list[Path]] = {}
    for wait_weight in WAIT_WEIGHTS:
        for reject_penalty in REJECT_PENALTIES:
            for fare_weight in FARE_WEIGHTS:
                paths = []
                for seed in SEEDS:
                    paths.append(run_one(wait_weight, reject_penalty, fare_weight, seed))
                paths_by_combo[(wait_weight, reject_penalty, fare_weight)] = paths
    write_outputs(summarize(paths_by_combo))


if __name__ == "__main__":
    main()