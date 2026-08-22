"""Consolidate every Figure-5 iterated-Concordia RQ2/RQ3 value into one Markdown file."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis" / "e_b_iterated_concordia"
LONG = DATA / "e_b_iterated_concordia_figure_v2_long.csv"
SOURCE = DATA / "e_b_iterated_concordia_per_seed.csv"
SUMMARY = DATA / "e_b_iterated_concordia_summary.csv"
AGGREGATE = DATA / "e_b_iterated_concordia_aggregate.csv"
METADATA = DATA / "e_b_iterated_concordia_metadata.json"
STATS = DATA / "e_b_iterated_concordia_figure_v2_stats.json"
FIGURE = ROOT / "arr_paper" / "figs" / "fig_e_b_iterated_concordia_v2.pdf"
OUT = DATA / "e_b_iterated_concordia_rq2_rq3_all_data.md"

METHOD_ORDER = (
    "pact",
    "pact_plus",
    "joint_psrl_uniform",
    "psrl_notype",
    "map_type_greedy",
    "econ_bne",
    "atom_tom1",
    "random",
)
METHOD_LABELS = {
    "pact": "PACT",
    "pact_plus": "PACT+",
    "joint_psrl_uniform": "Joint-PSRL",
    "psrl_notype": "PSRL-NoType",
    "map_type_greedy": "MAP-Type-Greedy",
    "econ_bne": "ECON-BNE",
    "atom_tom1": "A-ToM-1",
    "random": "Random",
}
METHOD_ROLES = {
    "pact": "panel (a) paired reference; thin panel (b) reference",
    "pact_plus": "panel (b) update-aware method",
    "joint_psrl_uniform": "panel (a) explicit-joint comparator",
    "psrl_notype": "panel (b) no-type/update-value control",
    "map_type_greedy": "retained endpoint control; not drawn in v2",
    "econ_bne": "retained endpoint control; not drawn in v2",
    "atom_tom1": "retained endpoint control; not drawn in v2",
    "random": "retained endpoint control; not drawn in v2",
}
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


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def escape(value: object) -> str:
    text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def table(rows: Iterable[dict[str, object] | dict[str, str]], columns: list[tuple[str, str]]) -> list[str]:
    data = list(rows)
    lines = [
        "| " + " | ".join(label for _, label in columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    lines.extend(
        "| " + " | ".join(escape(row.get(key, "")) for key, _ in columns) + " |"
        for row in data
    )
    return lines


def mean_sem(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return values.mean(axis=0), values.std(axis=0, ddof=1) / math.sqrt(values.shape[0])


def exact(value: float | np.floating[object]) -> str:
    return repr(float(value))


def close(left: float, right: float, tolerance: float = 1e-10) -> bool:
    return abs(left - right) <= tolerance * max(1.0, abs(left), abs(right))


def validate_inputs(
    long_rows: list[dict[str, str]],
    source_rows: list[dict[str, str]],
    summary_rows: list[dict[str, str]],
    aggregate_rows: list[dict[str, str]],
    metadata: dict[str, object],
) -> tuple[list[str], dict[tuple[str, str, int, int], float]]:
    if len(long_rows) != 4800 or len(source_rows) != 4800:
        raise AssertionError(f"E-B rows changed: long={len(long_rows)}, source={len(source_rows)}")
    if list(long_rows[0]) != ["method", "config", "seed", "episode", "cum_regret"]:
        raise AssertionError(f"unexpected long schema: {list(long_rows[0])}")
    if len(summary_rows) != 48 or len(aggregate_rows) != 16:
        raise AssertionError(f"summary grids changed: summary={len(summary_rows)}, aggregate={len(aggregate_rows)}")

    configs = [str(value) for value in metadata["configs"]]
    if len(configs) != 6 or len(set(configs)) != 6:
        raise AssertionError(f"expected six metadata configs, got {configs}")
    if metadata["selection_seeds"] != "0..4" or metadata["report_seed_range"] != "1000..1004":
        raise AssertionError("selection and report seed ranges are not the retained disjoint ranges")

    lookup: dict[tuple[str, str, int, int], float] = {}
    for row in long_rows:
        key = (row["method"], row["config"], int(row["seed"]), int(row["episode"]))
        if key in lookup:
            raise AssertionError(f"duplicate long-table key: {key}")
        lookup[key] = float(row["cum_regret"])
    expected = {
        (method, config, seed, episode)
        for method in METHOD_ORDER
        for config in configs
        for seed in SEEDS
        for episode in EPISODES
    }
    if set(lookup) != expected:
        raise AssertionError(f"long-table grid mismatch: missing={len(expected-set(lookup))}, extra={len(set(lookup)-expected)}")

    source_lookup = {
        (row["method"], row["config_id"], int(row["seed"]), int(row["episode"])):
        float(row["cumulative_regret"])
        for row in source_rows
    }
    if set(source_lookup) != expected:
        raise AssertionError("source per-episode grid does not match normalized long table")
    for key, value in lookup.items():
        if not close(value, source_lookup[key], tolerance=1e-13):
            raise AssertionError(f"normalized/source cumulative-regret mismatch at {key}")
    return configs, lookup


def trajectories(
    lookup: dict[tuple[str, str, int, int], float], configs: list[str]
) -> dict[str, np.ndarray]:
    output: dict[str, np.ndarray] = {}
    for method in METHOD_ORDER:
        output[method] = np.asarray(
            [
                [
                    np.mean([lookup[(method, config, seed, episode)] for config in configs])
                    for episode in EPISODES
                ]
                for seed in SEEDS
            ],
            dtype=float,
        )
    return output


def panel_a_rows(method_trajectories: dict[str, np.ndarray]) -> tuple[list[dict[str, object]], dict[str, np.ndarray]]:
    paired = method_trajectories["pact"] - method_trajectories["joint_psrl_uniform"]
    mean, sem = mean_sem(paired)
    low = mean - T95_DF4 * sem
    high = mean + T95_DF4 * sem
    covered = (low <= 0.0) & (high >= 0.0)
    rows: list[dict[str, object]] = []
    for index, episode in enumerate(EPISODES):
        row: dict[str, object] = {"episode": episode}
        row.update({f"seed_{seed}": exact(paired[seed_index, index]) for seed_index, seed in enumerate(SEEDS)})
        row.update(
            {
                "mean": exact(mean[index]),
                "sem": exact(sem[index]),
                "ci95_low": exact(low[index]),
                "ci95_high": exact(high[index]),
                "covers_zero": str(bool(covered[index])).lower(),
            }
        )
        rows.append(row)
    return rows, {"paired": paired, "mean": mean, "sem": sem, "low": low, "high": high, "covered": covered}


def panel_b_rows(method_trajectories: dict[str, np.ndarray]) -> tuple[list[dict[str, object]], dict[str, tuple[np.ndarray, np.ndarray]]]:
    curves = {method: mean_sem(method_trajectories[method]) for method in ("pact_plus", "psrl_notype", "pact")}
    rows: list[dict[str, object]] = []
    for index, episode in enumerate(EPISODES):
        rows.append(
            {
                "episode": episode,
                "pact_plus_mean": exact(curves["pact_plus"][0][index]),
                "pact_plus_sem": exact(curves["pact_plus"][1][index]),
                "psrl_notype_mean": exact(curves["psrl_notype"][0][index]),
                "psrl_notype_sem": exact(curves["psrl_notype"][1][index]),
                "pact_mean": exact(curves["pact"][0][index]),
                "pact_sem": exact(curves["pact"][1][index]),
            }
        )
    return rows, curves


def late_rate_rows(source_rows: list[dict[str, str]]) -> tuple[list[dict[str, object]], dict[str, tuple[float, float]]]:
    rows: list[dict[str, object]] = []
    stats: dict[str, tuple[float, float]] = {}
    for method in ("pact_plus", "psrl_notype", "pact"):
        per_seed = np.asarray(
            [
                np.mean(
                    [
                        float(row["instant_regret"])
                        for row in source_rows
                        if row["method"] == method and int(row["seed"]) == seed and int(row["episode"]) > 10
                    ]
                )
                for seed in SEEDS
            ],
            dtype=float,
        )
        mean = float(per_seed.mean())
        sem = float(per_seed.std(ddof=1) / math.sqrt(len(per_seed)))
        stats[method] = (mean, sem)
        row: dict[str, object] = {"method": method}
        row.update({f"seed_{seed}": exact(per_seed[index]) for index, seed in enumerate(SEEDS)})
        row.update({"mean": exact(mean), "sem": exact(sem)})
        rows.append(row)
    return rows, stats


def check_canonical_stats(
    stats: dict[str, object],
    panel_a: dict[str, np.ndarray],
    curves: dict[str, tuple[np.ndarray, np.ndarray]],
    late_rates: dict[str, tuple[float, float]],
) -> int:
    panel_a_stats = stats["panel_a"]
    panel_b_stats = stats["panel_b"]
    if not bool(np.all(panel_a["covered"])) or not panel_a_stats["all_episodes_cover_zero"]:
        raise AssertionError("panel (a) no longer has 20/20 t95 intervals covering zero")
    for key, value in (("k20_mean", panel_a["mean"][-1]), ("k20_sem", panel_a["sem"][-1])):
        if not close(float(panel_a_stats[key]), float(value)):
            raise AssertionError(f"canonical panel-a {key} is inconsistent")
    for method, prefix in (("pact_plus", "pact_plus"), ("psrl_notype", "psrl_notype"), ("pact", "pact")):
        if not close(float(panel_b_stats[f"{prefix}_k20_mean"]), float(curves[method][0][-1])):
            raise AssertionError(f"canonical panel-b {method} K=20 mean is inconsistent")
    for method, prefix in (("pact_plus", "pact_plus"), ("psrl_notype", "psrl_notype")):
        if not close(float(panel_b_stats[f"{prefix}_late_rate"]), late_rates[method][0]):
            raise AssertionError(f"canonical panel-b {method} late rate is inconsistent")
    crossover = next(
        episode
        for episode in EPISODES
        if curves["psrl_notype"][0][episode - 1] > curves["pact_plus"][0][episode - 1]
    )
    if crossover != int(panel_b_stats["mean_crossover_episode"]):
        raise AssertionError("canonical panel-b crossover is inconsistent")
    return crossover


def main() -> None:
    long_rows = read_csv(LONG)
    source_rows = read_csv(SOURCE)
    summary_rows = read_csv(SUMMARY)
    aggregate_rows = read_csv(AGGREGATE)
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    stats = json.loads(STATS.read_text(encoding="utf-8"))
    configs, lookup = validate_inputs(long_rows, source_rows, summary_rows, aggregate_rows, metadata)
    method_trajectories = trajectories(lookup, configs)
    paired_rows, paired_stats = panel_a_rows(method_trajectories)
    curve_rows, curves = panel_b_rows(method_trajectories)
    late_rows, late_rates = late_rate_rows(source_rows)
    crossover = check_canonical_stats(stats, paired_stats, curves, late_rates)

    method_rows = [
        {
            "method": method,
            "label": METHOD_LABELS[method],
            "role": METHOD_ROLES[method],
            "rows": sum(1 for row in long_rows if row["method"] == method),
        }
        for method in METHOD_ORDER
    ]
    selection_values = metadata["selection_mean_persona_decision_value"]
    config_rows = [
        {
            "config": config,
            "selection_mean_persona_decision_value": selection_values[config],
            "report_rows": sum(1 for row in long_rows if row["config"] == config),
        }
        for config in configs
    ]

    source_paths = (LONG, SOURCE, SUMMARY, AGGREGATE, METADATA, STATS, FIGURE)
    integrity_rows = [
        {"path": relative(path), "bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in source_paths
    ]

    lines = [
        "# Iterated Concordia RQ2 / RQ3 — Figure 5 Complete Data",
        "",
        "This document contains every row of the normalized `per (method, config, seed, episode)` long table used for the two-panel iterated-Concordia diagnostic, together with every plotted aggregate and its source-integrity record. It is generated from retained artifacts only and makes zero provider calls.",
        "",
        "## Scope and protocol",
        "",
        f"- Grid: {len(METHOD_ORDER)} methods x {len(configs)} held-out configurations x {len(SEEDS)} report seeds x {len(EPISODES)} episodes = {len(long_rows):,} unique rows.",
        f"- Report seeds: {metadata['report_seed_range']}; configuration-selection seeds: {metadata['selection_seeds']} (disjoint).",
        f"- Gaussian likelihood sigma: {metadata['sigma']}; frozen PACT+ beta: {metadata['beta']}.",
        f"- Planner: {metadata['planner']}.",
        f"- Prior factorization: {metadata['pf']}.",
        "- The benchmark is a constructed exact-payoff iterated diagnostic, not native dialogue Concordia; it is backbone-invariant and imposes PF.",
        "- The complete table preserves the CSV strings and precision; no values are interpolated.",
        "",
        "### Long-table schema",
        "",
        "| Column | Type | Meaning |",
        "|---|---|---|",
        "| method | string | algorithm identifier |",
        "| config | string | held-out Concordia-derived configuration identifier |",
        "| seed | integer | report seed, 1000 through 1004 |",
        "| episode | integer | episode index, 1 through 20 |",
        "| cum_regret | float | cumulative regret through the indicated episode |",
        "",
        "### Method coverage (all 8 methods)",
        "",
    ]
    lines.extend(table(method_rows, [("method", "method"), ("label", "paper label"), ("role", "v2 role"), ("rows", "long rows")]))
    lines.extend(["", "### Held-out configurations and selection diagnostics (all 6)", ""])
    lines.extend(table(config_rows, [("config", "config"), ("selection_mean_persona_decision_value", "selection mean persona decision value"), ("report_rows", "report rows")]))

    lines.extend(
        [
            "",
            "## Panel (a) — RQ2 paired parity",
            "",
            "For each report seed and episode, the paired value is the within-seed mean over all six configurations:",
            "",
            "$$d_{s,k}=\\frac{1}{6}\\sum_c\\left(R^{\\mathrm{PACT}}_{c,s,k}-R^{\\mathrm{Joint}}_{c,s,k}\\right).$$",
            "",
            "The table reports the five paired seed trajectories, their mean and SEM, and the two-sided Student-t 95% interval with df=4. All 20 intervals cover zero.",
            "",
            "### Panel (a) paired seed trajectories and t95 intervals (all 20 episodes)",
            "",
        ]
    )
    panel_a_columns = [("episode", "episode"), *[(f"seed_{seed}", str(seed)) for seed in SEEDS], ("mean", "mean"), ("sem", "SEM"), ("ci95_low", "t95 low"), ("ci95_high", "t95 high"), ("covers_zero", "covers zero")]
    lines.extend(table(paired_rows, panel_a_columns))

    lines.extend(
        [
            "",
            "## Panel (b) — RQ3 update value",
            "",
            "Each method curve first averages the six configurations within each seed, then reports the mean and seed-level SEM over five seeds. The plotted methods are PACT+, PSRL-NoType, and a thin PACT reference.",
            "",
            f"- Mean PSRL-NoType/PACT+ crossover episode: {crossover}.",
            f"- PACT+ late instantaneous-regret rate: {exact(late_rates['pact_plus'][0])} +/- {exact(late_rates['pact_plus'][1])} SEM.",
            f"- PSRL-NoType late instantaneous-regret rate: {exact(late_rates['psrl_notype'][0])} +/- {exact(late_rates['psrl_notype'][1])} SEM.",
            "",
            "### Panel (b) method trajectories and SEM bands (all 20 episodes)",
            "",
        ]
    )
    lines.extend(
        table(
            curve_rows,
            [
                ("episode", "episode"),
                ("pact_plus_mean", "PACT+ mean"), ("pact_plus_sem", "PACT+ SEM"),
                ("psrl_notype_mean", "PSRL-NoType mean"), ("psrl_notype_sem", "PSRL-NoType SEM"),
                ("pact_mean", "PACT mean"), ("pact_sem", "PACT SEM"),
            ],
        )
    )
    lines.extend(["", "### Panel (b) late-rate seed values (all 3 plotted methods)", ""])
    late_columns = [("method", "method"), *[(f"seed_{seed}", str(seed)) for seed in SEEDS], ("mean", "mean"), ("sem", "SEM")]
    lines.extend(table(late_rows, late_columns))

    lines.extend(["", "## Retained endpoint summaries", "", "### Config-by-method endpoint summaries (all 48 rows)", ""])
    lines.extend(table(summary_rows, [(column, column) for column in summary_rows[0]]))
    lines.extend(["", "### Scope-by-method aggregates (all 16 rows)", ""])
    lines.extend(table(aggregate_rows, [(column, column) for column in aggregate_rows[0]]))

    lines.extend(["", "## Canonical figure-statistics record", "", "```json", STATS.read_text(encoding="utf-8").rstrip(), "```"])
    lines.extend(["", "### Source integrity (all 7 artifacts)", ""])
    lines.extend(table(integrity_rows, [("path", "source"), ("bytes", "bytes"), ("sha256", "SHA-256")]))
    lines.extend(
        [
            "",
            "## Coverage checks",
            "",
            f"- Normalized long rows: {len(long_rows):,}; unique keys: {len(lookup):,}.",
            f"- Methods: {len(METHOD_ORDER)}; configurations: {len(configs)}; report seeds: {len(SEEDS)}; episodes: {len(EPISODES)}.",
            f"- Panel (a): {len(paired_rows)} episode rows; zero-covering t95 intervals: {sum(bool(value) for value in paired_stats['covered'])}/20.",
            f"- Panel (b): {len(curve_rows)} episode rows and {len(late_rows)} late-rate rows.",
            f"- Endpoint summaries: {len(summary_rows)} config-method rows and {len(aggregate_rows)} scope-method rows.",
            "- Every normalized cumulative-regret value was checked against the richer retained per-episode source table.",
            "",
            "## Complete normalized long table (all 4,800 rows)",
            "",
        ]
    )
    lines.extend(table(long_rows, [("method", "method"), ("config", "config"), ("seed", "seed"), ("episode", "episode"), ("cum_regret", "cum_regret")]))

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "ok",
                "output": relative(OUT),
                "bytes": OUT.stat().st_size,
                "lines": len(OUT.read_text(encoding="utf-8").splitlines()),
                "long_rows": len(long_rows),
                "panel_a_rows": len(paired_rows),
                "panel_b_rows": len(curve_rows),
                "summary_rows": len(summary_rows),
                "aggregate_rows": len(aggregate_rows),
                "source_files": len(source_paths),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
