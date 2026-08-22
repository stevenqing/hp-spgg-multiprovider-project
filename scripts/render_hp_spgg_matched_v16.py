"""Render Figure 2 at its paper-facing single-column size."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from paper_comparison_methods import ORACLE_COLOR, ORACLE_LINESTYLE
from run_e_a_matched_likelihood import (
    BACKBONES,
    COLORS,
    DISPLAY,
    FIGURE2_PLOT_ORDER,
)


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis" / "e_a_matched_likelihood" / "matched_s10" / "e_a_matched_per_seed.csv"
OUT = ROOT / "arr_paper" / "figs"
PDF = OUT / "fig_e_a_hp_spgg_matched_v16.pdf"
PNG = OUT / "fig_e_a_hp_spgg_matched_v16.png"
FINGERPRINT = OUT / "fig_e_a_hp_spgg_matched_v16_data.json"
REQUESTED_PLOT_ORDER = tuple(
    algorithm for algorithm in FIGURE2_PLOT_ORDER if algorithm != "psrl_notype"
)


def read_payload() -> dict[str, object]:
    with DATA.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    grouped: dict[tuple[str, str], list[float]] = {}
    for row in rows:
        key = (row["model"], row["algorithm"])
        grouped.setdefault(key, []).append(float(row["final_cumulative_regret"]))

    plot_order = tuple(
        algorithm
        for algorithm in REQUESTED_PLOT_ORDER
        if all((backbone.label, algorithm) in grouped for backbone in BACKBONES)
    )

    means = []
    sems = []
    seed_counts = []
    for backbone in BACKBONES:
        backbone_means = []
        backbone_sems = []
        backbone_counts = []
        for algorithm in plot_order:
            values = np.asarray(grouped[(backbone.label, algorithm)], dtype=float)
            if len(values) != 10:
                raise AssertionError(
                    f"{backbone.label}/{algorithm} has {len(values)} seeds; expected 10"
                )
            backbone_means.append(float(values.mean()))
            backbone_sems.append(float(values.std(ddof=1) / math.sqrt(len(values))))
            backbone_counts.append(len(values))
        means.append(backbone_means)
        sems.append(backbone_sems)
        seed_counts.append(backbone_counts)
    return {
        "backbones": [backbone.label for backbone in BACKBONES],
        "algorithms": list(plot_order),
        "labels": [DISPLAY[algorithm] for algorithm in plot_order],
        "means": means,
        "sems": sems,
        "seed_counts": seed_counts,
        "K": 20,
    }


def payload_sha256(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def main() -> None:
    payload = read_payload()
    means = np.asarray(payload["means"], dtype=float)
    sems = np.asarray(payload["sems"], dtype=float)
    plot_order = tuple(str(algorithm) for algorithm in payload["algorithms"])
    y = np.arange(len(plot_order))

    mpl.rcParams.update({
        "font.family": "serif",
        "font.serif": ["DejaVu Serif"],
        "font.size": 6.5,
        "axes.titlesize": 8.0,
        "axes.labelsize": 7.5,
        "xtick.labelsize": 6.5,
        "ytick.labelsize": 6.5,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })
    fig, axes = plt.subplots(2, 2, figsize=(3.3, 2.55), sharex=False)
    fig.subplots_adjust(left=0.25, right=0.985, bottom=0.08, top=0.91, wspace=0.20, hspace=0.38)

    for panel_index, (axis, backbone) in enumerate(zip(axes.ravel(), BACKBONES)):
        panel_means = means[panel_index]
        panel_sems = sems[panel_index]
        axis.barh(
            y,
            panel_means,
            xerr=panel_sems,
            height=0.58,
            color=[COLORS[algorithm] for algorithm in plot_order],
            edgecolor="none",
            error_kw={"ecolor": "#111111", "elinewidth": 0.65, "capsize": 1.4},
            zorder=3,
        )
        axis.axvline(
            0.0,
            color=ORACLE_COLOR,
            linestyle=ORACLE_LINESTYLE,
            linewidth=0.75,
            zorder=1,
        )
        axis.set_yticks(y)
        if panel_index % 2 == 0:
            axis.set_yticklabels(payload["labels"], fontsize=6.2)
        else:
            axis.set_yticklabels([])
            axis.tick_params(axis="y", length=0)
        axis.invert_yaxis()
        axis.set_title(backbone.label, loc="left", fontweight="bold", fontsize=8.0, pad=1.0)
        axis.grid(axis="x", linestyle=":", linewidth=0.45, color="#d7d7d7")
        axis.set_axisbelow(True)
        axis.spines[["top", "right"]].set_visible(False)
        span = max(panel_means + panel_sems)
        label_padding = 0.025 * max(span, 1.0)
        for row_index, (value, sem) in enumerate(zip(panel_means, panel_sems)):
            axis.text(
                value + sem + label_padding,
                row_index,
                f"{value:.2f}",
                va="center",
                fontsize=5.3,
            )
        axis.set_xlim(-0.04 * max(span, 1.0), max(span * 1.26, 1.0))
        axis.tick_params(axis="x", labelsize=6.0, pad=1.0, length=2.0)
        axis.tick_params(axis="y", pad=1.0)

    fig.savefig(PDF, facecolor="white")
    fig.savefig(PNG, dpi=300, facecolor="white")
    plt.close(fig)

    fingerprint = {
        "schema_version": "1.0",
        "source": str(DATA.relative_to(ROOT)).replace("\\", "/"),
        "numeric_payload_sha256": payload_sha256(payload),
        "payload": payload,
    }
    FINGERPRINT.write_text(json.dumps(fingerprint, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "ok",
        "pdf": str(PDF.relative_to(ROOT)),
        "png": str(PNG.relative_to(ROOT)),
        "numeric_payload_sha256": fingerprint["numeric_payload_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
