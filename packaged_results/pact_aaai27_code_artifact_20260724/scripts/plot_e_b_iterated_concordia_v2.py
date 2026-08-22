"""Render the two-panel E-B iterated Concordia RQ2/RQ3 diagnostic."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "analysis" / "e_b_iterated_concordia"
SOURCE = DATA_DIR / "e_b_iterated_concordia_per_seed.csv"
LONG_OUT = DATA_DIR / "e_b_iterated_concordia_figure_v2_long.csv"
STATS_OUT = DATA_DIR / "e_b_iterated_concordia_figure_v2_stats.json"
OUT_DIRS = (ROOT / "figs", ROOT / "arr_paper" / "figs")

METHODS = ("pact", "pact_plus", "joint_psrl_uniform", "psrl_notype")
SEEDS = tuple(range(1000, 1005))
EPISODES = tuple(range(1, 21))
T95_DF4 = 2.7764451051977987
COLORS = {
    "pact": "#557a95",
    "pact_plus": "#12345d",
    "joint_psrl_uniform": "#2f7d5b",
    "psrl_notype": "#9a5a2e",
}
LABELS = {
    "pact": "PACT",
    "pact_plus": "PACT+",
    "joint_psrl_uniform": "Joint-PSRL",
    "psrl_notype": "PSRL-NoType",
}


def read_source() -> list[dict[str, str]]:
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 4800:
        raise AssertionError(f"E-B source rows={len(rows)}, expected 4800")
    return rows


def normalize_long(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    normalized = [
        {
            "method": row["method"],
            "config": row["config_id"],
            "seed": int(row["seed"]),
            "episode": int(row["episode"]),
            "cum_regret": float(row["cumulative_regret"]),
        }
        for row in rows
    ]
    keys = [(row["method"], row["config"], row["seed"], row["episode"]) for row in normalized]
    if len(keys) != len(set(keys)):
        raise AssertionError("normalized E-B long table contains duplicate keys")
    with LONG_OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["method", "config", "seed", "episode", "cum_regret"])
        writer.writeheader()
        writer.writerows(normalized)
    return normalized


def mean_sem(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return values.mean(axis=0), values.std(axis=0, ddof=1) / math.sqrt(values.shape[0])


def per_seed_trajectories(rows: list[dict[str, object]]) -> dict[str, np.ndarray]:
    configs = sorted({str(row["config"]) for row in rows})
    if len(configs) != 6:
        raise AssertionError(f"E-B configs={configs}, expected 6")
    lookup = {
        (str(row["method"]), str(row["config"]), int(row["seed"]), int(row["episode"])): float(row["cum_regret"])
        for row in rows
    }
    trajectories: dict[str, np.ndarray] = {}
    for method in METHODS:
        array = np.empty((len(SEEDS), len(EPISODES)), dtype=float)
        for seed_index, seed in enumerate(SEEDS):
            for episode_index, episode in enumerate(EPISODES):
                array[seed_index, episode_index] = np.mean(
                    [lookup[(method, config, seed, episode)] for config in configs]
                )
        trajectories[method] = array
    return trajectories


def late_rate(rows: list[dict[str, str]], method: str) -> tuple[float, float]:
    by_seed: dict[int, list[float]] = {seed: [] for seed in SEEDS}
    for row in rows:
        if row["method"] != method or int(row["episode"]) <= 10:
            continue
        by_seed[int(row["seed"])].append(float(row["instant_regret"]))
    values = np.asarray([np.mean(by_seed[seed]) for seed in SEEDS], dtype=float)
    return float(values.mean()), float(values.std(ddof=1) / math.sqrt(len(values)))


def style_axis(axis: plt.Axes) -> None:
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.tick_params(labelsize=6.2, length=2.4, width=0.55)
    axis.grid(axis="y", color="#d7d7d7", linestyle=":", linewidth=0.45, zorder=0)


def render(trajectories: dict[str, np.ndarray], source_rows: list[dict[str, str]]) -> dict[str, object]:
    x = np.asarray(EPISODES, dtype=float)
    paired = trajectories["pact"] - trajectories["joint_psrl_uniform"]
    difference_mean, difference_sem = mean_sem(paired)
    difference_low = difference_mean - T95_DF4 * difference_sem
    difference_high = difference_mean + T95_DF4 * difference_sem
    covers_zero = (difference_low <= 0.0) & (difference_high >= 0.0)
    if not bool(np.all(covers_zero)):
        failed = [episode for episode, covered in zip(EPISODES, covers_zero, strict=True) if not covered]
        raise AssertionError(f"paired Student-t intervals miss zero at episodes {failed}")

    y_limit = max(0.15, float(np.max(np.abs(np.concatenate((difference_low, difference_high))))) * 1.08)
    y_limit = math.ceil(y_limit * 100.0) / 100.0

    late_plus, late_plus_sem = late_rate(source_rows, "pact_plus")
    late_notype, late_notype_sem = late_rate(source_rows, "psrl_notype")
    method_curves = {method: mean_sem(trajectories[method]) for method in ("pact_plus", "psrl_notype", "pact")}

    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["DejaVu Serif"],
            "font.size": 7.0,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    fig, axes = plt.subplots(1, 2, figsize=(4.75, 2.05), sharex=True)

    # (a) RQ2: paired parity on its own readable scale.
    ax = axes[0]
    ax.axhline(0.0, color="#111111", linewidth=0.75, zorder=1)
    ax.fill_between(x, difference_low, difference_high, color=COLORS["pact"], alpha=0.18, linewidth=0, zorder=2)
    ax.plot(x, difference_mean, color=COLORS["pact"], linewidth=1.25, zorder=3)
    ax.set_ylim(-y_limit, y_limit)
    ax.set_title("(a) RQ2: paired parity", loc="left", fontsize=7.4, pad=2.0)
    ax.set_ylabel("PACT $-$ Joint-PSRL", fontsize=6.7, labelpad=1.5)
    endpoint = float(difference_mean[-1])
    endpoint_sem = float(difference_sem[-1])
    ax.annotate(
        f"$K=20$\n{endpoint:+.3f} $\\pm$ {endpoint_sem:.3f} SEM",
        xy=(20, endpoint),
        xytext=(-50, -19 if endpoint <= 0 else 7),
        textcoords="offset points",
        fontsize=5.4,
        color=COLORS["pact"],
        arrowprops={"arrowstyle": "-", "color": COLORS["pact"], "linewidth": 0.45},
    )
    style_axis(ax)

    # (b) RQ3: update value and late-rate separation.
    ax = axes[1]
    for method, linewidth, alpha, zorder in (
        ("pact_plus", 1.35, 1.0, 4),
        ("psrl_notype", 1.35, 1.0, 4),
        ("pact", 0.8, 0.52, 2),
    ):
        curve, curve_sem = method_curves[method]
        ax.fill_between(x, np.maximum(0.0, curve - curve_sem), curve + curve_sem, color=COLORS[method], alpha=0.12 if method != "pact" else 0.06, linewidth=0, zorder=zorder - 1)
        ax.plot(x, curve, color=COLORS[method], linewidth=linewidth, alpha=alpha, label=LABELS[method], zorder=zorder)

    plus_curve = method_curves["pact_plus"][0]
    notype_curve = method_curves["psrl_notype"][0]
    tail_x = np.arange(14, 21, dtype=float)
    tail_reference = notype_curve[13] + late_notype * (tail_x - 14.0)
    ax.plot(tail_x, tail_reference, color="#777777", linestyle="--", linewidth=0.75, alpha=0.8, zorder=3)
    ax.text(13.2, plus_curve[13] + 0.08, f"late {late_plus:.4f}/ep", color=COLORS["pact_plus"], fontsize=5.2)
    ax.text(13.0, notype_curve[13] + 0.14, f"late {late_notype:.4f}/ep", color=COLORS["psrl_notype"], fontsize=5.2)
    upper = max(float(np.max(notype_curve + method_curves["psrl_notype"][1])), float(np.max(plus_curve + method_curves["pact_plus"][1])))
    ax.set_ylim(0.0, upper * 1.14)
    ax.set_title("(b) RQ3: update value", loc="left", fontsize=7.4, pad=2.0)
    ax.set_ylabel("Cumulative regret", fontsize=6.7, labelpad=1.5)
    ax.legend(frameon=False, fontsize=5.3, loc="upper left", handlelength=1.35, labelspacing=0.2, borderpad=0.1)
    style_axis(ax)

    for ax in axes:
        ax.set_xlim(1, 20)
        ax.set_xticks([1, 5, 10, 15, 20])
        ax.set_xlabel("Episode $k$", fontsize=6.7, labelpad=1.2)

    fig.tight_layout(w_pad=0.9, pad=0.35)
    for out_dir in OUT_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_dir / "fig_e_b_iterated_concordia_v2.pdf", bbox_inches="tight", pad_inches=0.02, facecolor="white")
        fig.savefig(out_dir / "fig_e_b_iterated_concordia_v2.png", dpi=260, bbox_inches="tight", pad_inches=0.02, facecolor="white")
    plt.close(fig)

    crossover = next(
        (episode for episode in EPISODES if method_curves["psrl_notype"][0][episode - 1] > method_curves["pact_plus"][0][episode - 1]),
        None,
    )
    stats: dict[str, object] = {
        "source_rows": len(source_rows),
        "normalized_rows": 4800,
        "configs": 6,
        "seeds": list(SEEDS),
        "episodes": 20,
        "panel_a": {
            "band": "two-sided Student-t 95% CI over five seed-level paired differences (df=4)",
            "all_episodes_cover_zero": bool(np.all(covers_zero)),
            "y_limit": [-y_limit, y_limit],
            "k20_mean": endpoint,
            "k20_sem": endpoint_sem,
            "k20_ci95": [float(difference_low[-1]), float(difference_high[-1])],
            "max_abs_mean": float(np.max(np.abs(difference_mean))),
        },
        "panel_b": {
            "bands": "seed-level SEM after within-seed averaging over six configurations",
            "pact_plus_k20_mean": float(method_curves["pact_plus"][0][-1]),
            "pact_plus_k20_sem": float(method_curves["pact_plus"][1][-1]),
            "psrl_notype_k20_mean": float(method_curves["psrl_notype"][0][-1]),
            "psrl_notype_k20_sem": float(method_curves["psrl_notype"][1][-1]),
            "pact_k20_mean": float(method_curves["pact"][0][-1]),
            "pact_k20_sem": float(method_curves["pact"][1][-1]),
            "pact_plus_late_rate": late_plus,
            "pact_plus_late_rate_sem": late_plus_sem,
            "psrl_notype_late_rate": late_notype,
            "psrl_notype_late_rate_sem": late_notype_sem,
            "mean_crossover_episode": crossover,
        },
        "figure_source_inches": [4.75, 2.05],
        "asset": "arr_paper/figs/fig_e_b_iterated_concordia_v2.pdf",
    }
    STATS_OUT.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    return stats


def main() -> None:
    source_rows = read_source()
    long_rows = normalize_long(source_rows)
    trajectories = per_seed_trajectories(long_rows)
    stats = render(trajectories, source_rows)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
