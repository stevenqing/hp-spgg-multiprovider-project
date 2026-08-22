"""Validate complete Markdown coverage for the Figure-5 iterated-Concordia data."""

from __future__ import annotations

import csv
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis" / "e_b_iterated_concordia"
REPORT = DATA / "e_b_iterated_concordia_rq2_rq3_all_data.md"
LONG = DATA / "e_b_iterated_concordia_figure_v2_long.csv"
SOURCE = DATA / "e_b_iterated_concordia_per_seed.csv"
SUMMARY = DATA / "e_b_iterated_concordia_summary.csv"
AGGREGATE = DATA / "e_b_iterated_concordia_aggregate.csv"
METADATA = DATA / "e_b_iterated_concordia_metadata.json"
STATS = DATA / "e_b_iterated_concordia_figure_v2_stats.json"
FIGURE = ROOT / "arr_paper" / "figs" / "fig_e_b_iterated_concordia_v2.pdf"
SEEDS = tuple(range(1000, 1005))
EPISODES = tuple(range(1, 21))
T95_DF4 = 2.7764451051977987


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def close(left: float, right: float, tolerance: float = 1e-10) -> bool:
    return abs(left - right) <= tolerance * max(1.0, abs(left), abs(right))


def split_table_row(line: str) -> list[str]:
    if not line.startswith("|") or not line.endswith("|"):
        raise AssertionError(f"not a Markdown table row: {line[:80]}")
    return [cell.strip().replace("\\|", "|") for cell in line[1:-1].split("|")]


def table_under(lines: list[str], heading: str) -> tuple[list[str], list[list[str]]]:
    try:
        index = lines.index(heading) + 1
    except ValueError as exc:
        raise AssertionError(f"missing report section: {heading}") from exc
    while index < len(lines) and not lines[index].startswith("|"):
        index += 1
    if index + 1 >= len(lines):
        raise AssertionError(f"missing table under {heading}")
    header = split_table_row(lines[index])
    if not lines[index + 1].startswith("|---"):
        raise AssertionError(f"missing separator under {heading}")
    output: list[list[str]] = []
    for line in lines[index + 2 :]:
        if not line.startswith("|"):
            break
        output.append(split_table_row(line))
    return header, output


def numeric_trajectories(long_rows: list[dict[str, str]]) -> tuple[list[str], dict[str, np.ndarray]]:
    configs = sorted({row["config"] for row in long_rows})
    lookup = {
        (row["method"], row["config"], int(row["seed"]), int(row["episode"])):
        float(row["cum_regret"])
        for row in long_rows
    }
    methods = sorted({row["method"] for row in long_rows})
    trajectories: dict[str, np.ndarray] = {}
    for method in methods:
        trajectories[method] = np.asarray(
            [
                [
                    np.mean([lookup[(method, config, seed, episode)] for config in configs])
                    for episode in EPISODES
                ]
                for seed in SEEDS
            ],
            dtype=float,
        )
    return configs, trajectories


def main() -> None:
    if not REPORT.is_file() or REPORT.stat().st_size < 300_000:
        raise AssertionError("complete iterated-Concordia Markdown is missing or unexpectedly small")
    text = REPORT.read_text(encoding="utf-8")
    lines = text.splitlines()
    private_term = bytes.fromhex("762d73687571696e67736869").decode("utf-8")
    if private_term.lower() in text.lower():
        raise AssertionError("private local identity found in consolidated report")

    expected_counts = {
        "### Method coverage (all 8 methods)": 8,
        "### Held-out configurations and selection diagnostics (all 6)": 6,
        "### Panel (a) paired seed trajectories and t95 intervals (all 20 episodes)": 20,
        "### Panel (b) method trajectories and SEM bands (all 20 episodes)": 20,
        "### Panel (b) late-rate seed values (all 3 plotted methods)": 3,
        "### Config-by-method endpoint summaries (all 48 rows)": 48,
        "### Scope-by-method aggregates (all 16 rows)": 16,
        "### Source integrity (all 7 artifacts)": 7,
        "## Complete normalized long table (all 4,800 rows)": 4800,
    }
    parsed: dict[str, tuple[list[str], list[list[str]]]] = {}
    for heading, expected in expected_counts.items():
        parsed[heading] = table_under(lines, heading)
        observed = len(parsed[heading][1])
        if observed != expected:
            raise AssertionError(f"{heading}: rows={observed}, expected={expected}")

    long_source = read_csv(LONG)
    long_heading = "## Complete normalized long table (all 4,800 rows)"
    long_header, long_report = parsed[long_heading]
    if long_header != ["method", "config", "seed", "episode", "cum_regret"]:
        raise AssertionError(f"report long-table schema changed: {long_header}")
    expected_long = [[row[column] for column in long_header] for row in long_source]
    if long_report != expected_long:
        mismatch = next(
            (index for index, (observed, expected) in enumerate(zip(long_report, expected_long, strict=True)) if observed != expected),
            None,
        )
        raise AssertionError(f"report long table is not an exact copy of normalized CSV; first mismatch={mismatch}")

    keys = [(row["method"], row["config"], row["seed"], row["episode"]) for row in long_source]
    if len(keys) != len(set(keys)):
        raise AssertionError("source normalized long table contains duplicate keys")
    methods = {row["method"] for row in long_source}
    configs, trajectories = numeric_trajectories(long_source)
    if len(methods) != 8 or len(configs) != 6:
        raise AssertionError(f"normalized grid changed: methods={len(methods)}, configs={len(configs)}")
    if {int(row["seed"]) for row in long_source} != set(SEEDS):
        raise AssertionError("report seed grid changed")
    if {int(row["episode"]) for row in long_source} != set(EPISODES):
        raise AssertionError("episode grid changed")

    panel_a_heading = "### Panel (a) paired seed trajectories and t95 intervals (all 20 episodes)"
    panel_a_header, panel_a_report = parsed[panel_a_heading]
    expected_panel_a_header = ["episode", *[str(seed) for seed in SEEDS], "mean", "SEM", "t95 low", "t95 high", "covers zero"]
    if panel_a_header != expected_panel_a_header:
        raise AssertionError(f"panel-a schema changed: {panel_a_header}")
    paired = trajectories["pact"] - trajectories["joint_psrl_uniform"]
    paired_mean = paired.mean(axis=0)
    paired_sem = paired.std(axis=0, ddof=1) / math.sqrt(len(SEEDS))
    paired_low = paired_mean - T95_DF4 * paired_sem
    paired_high = paired_mean + T95_DF4 * paired_sem
    for index, report_row in enumerate(panel_a_report):
        if int(report_row[0]) != EPISODES[index]:
            raise AssertionError(f"panel-a episode order changed at row {index}")
        observed_seed_values = np.asarray([float(value) for value in report_row[1:6]], dtype=float)
        if not np.allclose(observed_seed_values, paired[:, index], rtol=1e-12, atol=1e-12):
            raise AssertionError(f"panel-a seed values changed at episode {index+1}")
        expected_values = (paired_mean[index], paired_sem[index], paired_low[index], paired_high[index])
        if any(not close(float(observed), float(expected)) for observed, expected in zip(report_row[6:10], expected_values, strict=True)):
            raise AssertionError(f"panel-a aggregate values changed at episode {index+1}")
        covered = paired_low[index] <= 0.0 <= paired_high[index]
        if report_row[10] != str(bool(covered)).lower() or not covered:
            raise AssertionError(f"panel-a interval coverage changed at episode {index+1}")

    panel_b_heading = "### Panel (b) method trajectories and SEM bands (all 20 episodes)"
    panel_b_header, panel_b_report = parsed[panel_b_heading]
    if panel_b_header != ["episode", "PACT+ mean", "PACT+ SEM", "PSRL-NoType mean", "PSRL-NoType SEM", "PACT mean", "PACT SEM"]:
        raise AssertionError(f"panel-b schema changed: {panel_b_header}")
    curve_stats: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for method in ("pact_plus", "psrl_notype", "pact"):
        curve_stats[method] = (
            trajectories[method].mean(axis=0),
            trajectories[method].std(axis=0, ddof=1) / math.sqrt(len(SEEDS)),
        )
    for index, report_row in enumerate(panel_b_report):
        expected_values = (
            curve_stats["pact_plus"][0][index], curve_stats["pact_plus"][1][index],
            curve_stats["psrl_notype"][0][index], curve_stats["psrl_notype"][1][index],
            curve_stats["pact"][0][index], curve_stats["pact"][1][index],
        )
        if int(report_row[0]) != EPISODES[index] or any(
            not close(float(observed), float(expected))
            for observed, expected in zip(report_row[1:], expected_values, strict=True)
        ):
            raise AssertionError(f"panel-b values changed at episode {index+1}")

    source_rows = read_csv(SOURCE)
    late_heading = "### Panel (b) late-rate seed values (all 3 plotted methods)"
    late_header, late_report = parsed[late_heading]
    if late_header != ["method", *[str(seed) for seed in SEEDS], "mean", "SEM"]:
        raise AssertionError(f"late-rate schema changed: {late_header}")
    instant: dict[tuple[str, int], list[float]] = defaultdict(list)
    for row in source_rows:
        if int(row["episode"]) > 10:
            instant[(row["method"], int(row["seed"]))].append(float(row["instant_regret"]))
    late_stats: dict[str, tuple[float, float]] = {}
    for report_row in late_report:
        method = report_row[0]
        expected_seed = np.asarray([np.mean(instant[(method, seed)]) for seed in SEEDS], dtype=float)
        observed_seed = np.asarray([float(value) for value in report_row[1:6]], dtype=float)
        if not np.allclose(observed_seed, expected_seed, rtol=1e-12, atol=1e-12):
            raise AssertionError(f"late-rate seed values changed for {method}")
        mean = float(expected_seed.mean())
        sem = float(expected_seed.std(ddof=1) / math.sqrt(len(SEEDS)))
        if not close(float(report_row[6]), mean) or not close(float(report_row[7]), sem):
            raise AssertionError(f"late-rate aggregate changed for {method}")
        late_stats[method] = (mean, sem)

    stats = json.loads(STATS.read_text(encoding="utf-8"))
    if not stats["panel_a"]["all_episodes_cover_zero"] or not close(float(stats["panel_a"]["k20_mean"]), float(paired_mean[-1])):
        raise AssertionError("canonical stats disagree with panel-a report")
    if not close(float(stats["panel_b"]["pact_plus_late_rate"]), late_stats["pact_plus"][0]):
        raise AssertionError("canonical stats disagree with PACT+ late rate")
    if not close(float(stats["panel_b"]["psrl_notype_late_rate"]), late_stats["psrl_notype"][0]):
        raise AssertionError("canonical stats disagree with PSRL-NoType late rate")
    crossover = next(
        episode
        for episode in EPISODES
        if curve_stats["psrl_notype"][0][episode - 1] > curve_stats["pact_plus"][0][episode - 1]
    )
    if crossover != 6 or int(stats["panel_b"]["mean_crossover_episode"]) != crossover:
        raise AssertionError(f"panel-b crossover changed: {crossover}")

    source_paths = (LONG, SOURCE, SUMMARY, AGGREGATE, METADATA, STATS, FIGURE)
    for path in source_paths:
        relative = path.relative_to(ROOT).as_posix()
        digest = sha256(path)
        if relative not in text or digest not in text:
            raise AssertionError(f"source path/hash missing from report: {relative}")

    required_values = (
        "-0.016807856201604826",
        "0.04364455895488382",
        "-0.13798457828040878",
        "0.10436886587719911",
        "0.001984569469402637",
        "0.07642943375547162",
        "Mean PSRL-NoType/PACT+ crossover episode: 6",
        "Normalized long rows: 4,800; unique keys: 4,800",
    )
    for value in required_values:
        if value not in text:
            raise AssertionError(f"required figure value missing from report: {value}")

    print(
        json.dumps(
            {
                "status": "ok",
                "report": REPORT.relative_to(ROOT).as_posix(),
                "bytes": REPORT.stat().st_size,
                "lines": len(lines),
                "long_rows": len(long_report),
                "methods": len(methods),
                "configs": len(configs),
                "seeds": len(SEEDS),
                "episodes": len(EPISODES),
                "panel_a_rows": len(panel_a_report),
                "panel_b_rows": len(panel_b_report),
                "all_20_t95_intervals_cover_zero": True,
                "mean_crossover_episode": crossover,
                "source_files": len(source_paths),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
