"""Validate the two-panel E-B iterated Concordia figure and long-table data."""

from __future__ import annotations

import csv
from collections import defaultdict
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis" / "e_b_iterated_concordia"
SOURCE = DATA / "e_b_iterated_concordia_per_seed.csv"
LONG = DATA / "e_b_iterated_concordia_figure_v2_long.csv"
STATS = DATA / "e_b_iterated_concordia_figure_v2_stats.json"
FIGURE = ROOT / "arr_paper" / "figs" / "fig_e_b_iterated_concordia_v2.pdf"
T95_DF4 = 2.7764451051977987


def read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def close(left: float, right: float, tolerance: float = 1e-10) -> bool:
    return abs(left - right) <= tolerance * max(1.0, abs(left), abs(right))


def main() -> None:
    source = read(SOURCE)
    long = read(LONG)
    stats = json.loads(STATS.read_text(encoding="utf-8"))
    if len(source) != 4800 or len(long) != 4800:
        raise AssertionError(f"E-B row counts changed: source={len(source)}, long={len(long)}")
    if list(long[0]) != ["method", "config", "seed", "episode", "cum_regret"]:
        raise AssertionError(f"unexpected normalized schema: {list(long[0])}")
    keys = [(row["method"], row["config"], row["seed"], row["episode"]) for row in long]
    if len(keys) != len(set(keys)):
        raise AssertionError("normalized long table has duplicate keys")
    methods = {row["method"] for row in long}
    required = {"pact", "pact_plus", "joint_psrl_uniform", "psrl_notype"}
    if not required.issubset(methods):
        raise AssertionError(f"missing required methods: {required-methods}")
    if len({row["config"] for row in long}) != 6:
        raise AssertionError("normalized long table must contain six held-out configurations")
    if {int(row["seed"]) for row in long} != set(range(1000, 1005)):
        raise AssertionError("normalized long table has the wrong report seeds")
    if {int(row["episode"]) for row in long} != set(range(1, 21)):
        raise AssertionError("normalized long table has the wrong episode grid")

    lookup: dict[tuple[int, str, int], list[float]] = defaultdict(list)
    for row in long:
        lookup[(int(row["seed"]), row["method"], int(row["episode"]))].append(float(row["cum_regret"]))
    trajectories: dict[str, np.ndarray] = {}
    for method in required:
        trajectories[method] = np.asarray(
            [
                [np.mean(lookup[(seed, method, episode)]) for episode in range(1, 21)]
                for seed in range(1000, 1005)
            ],
            dtype=float,
        )
    paired = trajectories["pact"] - trajectories["joint_psrl_uniform"]
    mean = paired.mean(axis=0)
    sem = paired.std(axis=0, ddof=1) / math.sqrt(5)
    low = mean - T95_DF4 * sem
    high = mean + T95_DF4 * sem
    if not bool(np.all((low <= 0.0) & (high >= 0.0))):
        failed = [index + 1 for index, covered in enumerate((low <= 0.0) & (high >= 0.0)) if not covered]
        raise AssertionError(f"panel-a intervals miss zero: {failed}")
    panel_a = stats["panel_a"]
    if not panel_a["all_episodes_cover_zero"]:
        raise AssertionError("stats do not certify all-episode parity coverage")
    if not close(float(panel_a["k20_mean"]), float(mean[-1])) or not close(float(panel_a["k20_sem"]), float(sem[-1])):
        raise AssertionError("panel-a endpoint annotation is inconsistent")
    y_low, y_high = (float(value) for value in panel_a["y_limit"])
    if not close(abs(y_low), abs(y_high)) or y_high > 0.20 or y_high < float(np.max(np.abs(np.concatenate((low, high))))):
        raise AssertionError(f"panel-a y scale is not a tight symmetric readable range: {panel_a['y_limit']}")

    aggregate = read(DATA / "e_b_iterated_concordia_aggregate.csv")
    aggregate_lookup = {(row["scope"], row["method"]): row for row in aggregate}
    panel_b = stats["panel_b"]
    checks = (
        ("pact_plus", "pact_plus_k20_mean", "cumulative_regret_mean"),
        ("psrl_notype", "psrl_notype_k20_mean", "cumulative_regret_mean"),
        ("pact", "pact_k20_mean", "cumulative_regret_mean"),
        ("pact_plus", "pact_plus_late_rate", "late_instant_regret_mean"),
        ("psrl_notype", "psrl_notype_late_rate", "late_instant_regret_mean"),
    )
    for method, stat_key, aggregate_key in checks:
        expected = float(aggregate_lookup[("all_selected", method)][aggregate_key])
        if not close(float(panel_b[stat_key]), expected):
            raise AssertionError(f"panel-b {stat_key}={panel_b[stat_key]} != aggregate {expected}")
    if int(panel_b["mean_crossover_episode"]) != 6:
        raise AssertionError(f"PACT+/PSRL-NoType mean crossover changed: {panel_b['mean_crossover_episode']}")
    final_gap = float(trajectories["psrl_notype"].mean(axis=0)[-1] - trajectories["pact_plus"].mean(axis=0)[-1])
    if final_gap <= 1.0:
        raise AssertionError(f"panel-b terminal separation={final_gap}, expected >1")

    width, height = (float(value) for value in stats["figure_source_inches"])
    rendered_height = 3.25 * height / width
    if rendered_height > 1.5:
        raise AssertionError(f"single-column rendered height={rendered_height:.3f}in exceeds 1.5in")
    if not FIGURE.is_file() or FIGURE.stat().st_size < 10_000:
        raise AssertionError("v2 figure PDF is missing or empty")

    print(
        json.dumps(
            {
                "status": "ok",
                "long_rows": len(long),
                "all_20_t95_intervals_cover_zero": True,
                "k20_difference_mean": float(mean[-1]),
                "k20_difference_sem": float(sem[-1]),
                "panel_a_ylim": panel_a["y_limit"],
                "panel_b_crossover_episode": panel_b["mean_crossover_episode"],
                "pact_plus_late_rate": panel_b["pact_plus_late_rate"],
                "psrl_notype_late_rate": panel_b["psrl_notype_late_rate"],
                "rendered_height_inches_at_columnwidth": rendered_height,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
