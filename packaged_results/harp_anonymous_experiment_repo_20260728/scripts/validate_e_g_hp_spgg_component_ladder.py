"""Strict validation for the E-G analytic HP-SPGG component ladder."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from llm_hpgg.environment import build_reward_tensor, load_calibration  # noqa: E402


DATA = ROOT / "analysis" / "e_g_hp_spgg_component_ladder"
CALIBRATION = DATA / "calibration_analytic_n3.npy"
LONG = DATA / "e_g_hp_spgg_component_ladder_long.csv"
SUMMARY = DATA / "e_g_hp_spgg_component_ladder_summary.csv"
METADATA = DATA / "e_g_hp_spgg_component_ladder_metadata.json"
NPZ = DATA / "e_g_hp_spgg_component_ladder.npz"
REPORT = DATA / "e_g_hp_spgg_component_ladder.md"
MAIN_FIGURE = ROOT / "arr_paper" / "figs" / "fig_e_g_hp_spgg_component_ladder.pdf"
TRAJECTORY_FIGURE = ROOT / "arr_paper" / "figs" / "fig_e_g_hp_spgg_component_trajectories.pdf"
VARIANTS = ("full", "minus_bonus", "minus_update", "minus_identity", "minus_dispatch")
SEEDS = tuple(range(10))
EPISODES = tuple(range(1, 21))
T95_DF9 = 2.2621571627409915
CANONICAL_MEANS = {
    "full": 0.014803811559212865,
    "minus_bonus": 0.015594443719659812,
    "minus_update": 0.6752610309174041,
    "minus_identity": 0.7000513484402628,
    "minus_dispatch": 6.3236933621419436,
}


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


def markdown_table_rows(lines: list[str], heading: str) -> list[str]:
    try:
        index = lines.index(heading) + 1
    except ValueError as exc:
        raise AssertionError(f"E-G Markdown section missing: {heading}") from exc
    while index < len(lines) and not lines[index].startswith("|"):
        index += 1
    if index + 1 >= len(lines) or not lines[index + 1].startswith("|---"):
        raise AssertionError(f"E-G Markdown table missing under: {heading}")
    output: list[str] = []
    for line in lines[index + 2 :]:
        if not line.startswith("|"):
            break
        output.append(line)
    return output


def main() -> None:
    required = (CALIBRATION, LONG, SUMMARY, METADATA, NPZ, REPORT, MAIN_FIGURE, TRAJECTORY_FIGURE)
    for path in required:
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(path)

    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    if metadata["provider_calls"] != 0 or metadata["n"] != 3 or metadata["type_count"] != 4:
        raise AssertionError("E-G protocol metadata changed")
    if metadata["K"] != 20 or metadata["beta"] != 0.25 or metadata["sigma"] != 0.08:
        raise AssertionError("E-G horizon/beta/sigma changed")
    if metadata["common_environment_seeds"] != list(SEEDS):
        raise AssertionError("E-G common environment seeds changed")
    if metadata["calibration_sha256"] != sha256(CALIBRATION):
        raise AssertionError("E-G calibration hash mismatch")

    actual_calibration = load_calibration(CALIBRATION)
    expected_calibration = build_reward_tensor(n=3, backend="mixed", samples=3, seed=0, trap=False)
    if not np.array_equal(np.asarray(actual_calibration["reward_tensor"]), expected_calibration.reward_tensor):
        raise AssertionError("E-G calibration is not the pinned analytic mixed/seed-0 kernel")
    if not np.array_equal(np.asarray(actual_calibration["action_profiles"]), expected_calibration.action_profiles):
        raise AssertionError("E-G action-profile grid changed")

    long_rows = read_csv(LONG)
    summary_rows = read_csv(SUMMARY)
    if list(long_rows[0]) != ["variant", "seed", "episode", "cum_regret"]:
        raise AssertionError(f"E-G long schema changed: {list(long_rows[0])}")
    if len(long_rows) != 1000 or len(summary_rows) != 5:
        raise AssertionError(f"E-G row counts changed: long={len(long_rows)}, summary={len(summary_rows)}")
    keys = [(row["variant"], int(row["seed"]), int(row["episode"])) for row in long_rows]
    expected_keys = [(variant, seed, episode) for variant in VARIANTS for seed in SEEDS for episode in EPISODES]
    if keys != expected_keys or len(keys) != len(set(keys)):
        raise AssertionError("E-G long table is not the exact ordered 5x10x20 grid")

    with np.load(NPZ, allow_pickle=True) as payload:
        variants = tuple(str(value) for value in payload["variants"])
        regrets = np.asarray(payload["regrets"], dtype=float)
        cumulative = np.asarray(payload["cumulative_regret"], dtype=float)
        posterior = np.asarray(payload["posterior_history"], dtype=float)
        local = np.asarray(payload["decentralized_local_posterior_history"], dtype=float)
        true_types = np.asarray(payload["true_types"], dtype=int)
        derangements = np.asarray(payload["derangements"], dtype=int)
        if variants != VARIANTS:
            raise AssertionError(f"E-G NPZ variants changed: {variants}")
        if regrets.shape != (5, 10, 20) or cumulative.shape != (5, 10, 20):
            raise AssertionError(f"E-G regret tensor shapes changed: {regrets.shape}, {cumulative.shape}")
        if posterior.shape != (5, 10, 20, 3, 4) or local.shape != (10, 20, 3, 3, 4):
            raise AssertionError(f"E-G posterior shapes changed: {posterior.shape}, {local.shape}")
        if true_types.shape != (5, 10, 3) or derangements.shape != (10, 3):
            raise AssertionError("E-G type/derangement shapes changed")
        if not np.allclose(cumulative, np.cumsum(regrets, axis=2), rtol=0.0, atol=1e-14):
            raise AssertionError("E-G cumulative regret is not the cumsum of instant regret")
        if np.any(regrets < -1e-14) or np.any(np.diff(cumulative, axis=2) < -1e-14):
            raise AssertionError("E-G regret is negative or cumulative paths decrease")
        for variant_index in range(1, len(VARIANTS)):
            if not np.array_equal(true_types[variant_index], true_types[0]):
                raise AssertionError("E-G true type profiles are not environment-matched")
        uniform = np.full((10, 20, 3, 4), 0.25)
        if not np.array_equal(posterior[VARIANTS.index("minus_update")], uniform):
            raise AssertionError("E-G minus-update posterior changed from the uniform prior")
        if not np.allclose(local[:, :, 0], local[:, :, 1], rtol=0.0, atol=1e-14) or not np.allclose(
            local[:, :, 0], local[:, :, 2], rtol=0.0, atol=1e-14
        ):
            raise AssertionError("E-G decentralized actors do not share the same public-history belief input")
        expected_derangements = np.asarray([[1, 2, 0] if seed % 2 == 0 else [2, 0, 1] for seed in SEEDS])
        if not np.array_equal(derangements, expected_derangements):
            raise AssertionError(f"E-G derangement schedule changed: {derangements.tolist()}")
        if np.any(derangements == np.arange(3)[None, :]):
            raise AssertionError("E-G identity permutation has a fixed point")

        for row_index, row in enumerate(long_rows):
            variant_index = VARIANTS.index(row["variant"])
            expected = cumulative[variant_index, int(row["seed"]), int(row["episode"]) - 1]
            if not close(float(row["cum_regret"]), float(expected), tolerance=1e-13):
                raise AssertionError(f"E-G long/NPZ mismatch at row {row_index}")

        summary = {row["variant"]: row for row in summary_rows}
        full = cumulative[0, :, -1]
        for variant_index, variant in enumerate(VARIANTS):
            endpoints = cumulative[variant_index, :, -1]
            mean = float(endpoints.mean())
            sem = float(endpoints.std(ddof=1) / math.sqrt(len(endpoints)))
            paired = endpoints - full
            paired_mean = float(paired.mean())
            paired_sem = float(paired.std(ddof=1) / math.sqrt(len(paired)))
            low = paired_mean - T95_DF9 * paired_sem
            high = paired_mean + T95_DF9 * paired_sem
            row = summary[variant]
            checks = (
                ("cumulative_regret_mean", mean),
                ("cumulative_regret_sem", sem),
                ("paired_minus_full_mean", paired_mean),
                ("paired_minus_full_sem", paired_sem),
                ("ci95_low", low),
                ("ci95_high", high),
            )
            for key, expected in checks:
                if not close(float(row[key]), expected):
                    raise AssertionError(f"E-G summary mismatch: {variant} {key}")
            if str(low <= 0.0 <= high) != row["ci_covers_zero"]:
                raise AssertionError(f"E-G CI coverage mismatch: {variant}")
            if not close(mean, CANONICAL_MEANS[variant]):
                raise AssertionError(f"E-G canonical mean changed: {variant}={mean}")

    coverage = {row["variant"]: row["ci_covers_zero"] == "True" for row in summary_rows}
    if coverage != {
        "full": True,
        "minus_bonus": True,
        "minus_update": False,
        "minus_identity": True,
        "minus_dispatch": False,
    }:
        raise AssertionError(f"E-G paired-CI pattern changed: {coverage}")
    if metadata["identity_minus_no_update"]["significantly_worse"]:
        raise AssertionError("E-G identity is no longer the preregistered non-amber result")
    report_text = REPORT.read_text(encoding="utf-8")
    report_lines = report_text.splitlines()
    expected_report_tables = {
        "## Common environments and fixed derangements": 10,
        "## K=20 endpoint summary": 5,
        "## Per-seed K=20 endpoints and paired differences": 50,
        "## Identity minus no-update paired contrast": 10,
        "## Episode-level aggregate trajectories": 100,
        "## Semantic and acceptance checks": 6,
        "## Source integrity": 10,
        "## Complete long table (all 1,000 rows)": 1000,
    }
    report_table_counts: dict[str, int] = {}
    for heading, expected in expected_report_tables.items():
        observed = len(markdown_table_rows(report_lines, heading))
        report_table_counts[heading] = observed
        if observed != expected:
            raise AssertionError(f"E-G Markdown {heading}: rows={observed}, expected={expected}")
    report_long_rows = re.findall(
        r"^\| (?:full|minus_bonus|minus_update|minus_identity|minus_dispatch) \| \d+ \| \d+ \|",
        report_text,
        flags=re.MULTILINE,
    )
    if len(report_long_rows) != 1000 or "Complete long table (all 1,000 rows)" not in report_text:
        raise AssertionError("E-G Markdown does not contain the complete long table")
    report_sources = [
        CALIBRATION,
        LONG,
        SUMMARY,
        METADATA,
        NPZ,
        MAIN_FIGURE,
        TRAJECTORY_FIGURE,
        ROOT / "scripts" / "run_e_g_hp_spgg_component_ladder.py",
        ROOT / "scripts" / "plot_e_g_hp_spgg_component_ladder.py",
        ROOT / "scripts" / "validate_e_g_hp_spgg_component_ladder.py",
    ]
    for path in report_sources:
        relative = path.relative_to(ROOT).as_posix()
        digest = sha256(path)
        if relative not in report_text or digest not in report_text:
            raise AssertionError(f"E-G Markdown source path/hash missing: {relative}")
    required_report_values = (
        "0.014803811559212865",
        "-0.0016425044806740417",
        "0.9150662577723234",
        "1.511507453601963",
        "-0.7669890671501177",
        "7.307294886728645",
        '"provider_calls": 0',
        "Complete long rows: 1000",
    )
    for value in required_report_values:
        if value not in report_text:
            raise AssertionError(f"E-G Markdown required value missing: {value}")
    if REPORT.stat().st_size < 55_000:
        raise AssertionError(f"E-G complete Markdown is unexpectedly small: {REPORT.stat().st_size}")
    if MAIN_FIGURE.stat().st_size < 10_000 or TRAJECTORY_FIGURE.stat().st_size < 10_000:
        raise AssertionError("E-G figures are missing or unexpectedly small")

    print(
        json.dumps(
            {
                "status": "ok",
                "long_rows": len(long_rows),
                "summary_rows": len(summary_rows),
                "canonical_means": CANONICAL_MEANS,
                "paired_ci_covers_zero": coverage,
                "identity_minus_no_update": metadata["identity_minus_no_update"],
                "calibration_sha256": metadata["calibration_sha256"],
                "report_bytes": REPORT.stat().st_size,
                "report_lines": len(report_lines),
                "report_table_counts": report_table_counts,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
