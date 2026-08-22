"""Pilot a theory-aligned stochastic-channel HP-SPGG burn-in experiment."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_hpgg.analytic_scaling import (  # noqa: E402
    ACTIONS,
    SIGMA,
    local_reward_lookup,
    squared_hellinger_gaussians,
    synthesize_type_library,
)


OUT_DIR = ROOT / "analysis" / "hp_spgg_burn_in_v2_pilot"
RAW_OUT = OUT_DIR / "burn_in_v2_raw.csv"
SUMMARY_OUT = OUT_DIR / "burn_in_v2_summary.csv"
CONTRACTION_OUT = OUT_DIR / "burn_in_v2_contraction.csv"
FIT_OUT = OUT_DIR / "burn_in_v2_fits.json"
REPORT_OUT = OUT_DIR / "burn_in_v2_design_and_results.md"
SEEDS = tuple(range(2000, 2200))
TYPE_SWEEP = (4, 8, 16)
H_SWEEP = (1, 4, 16)
N_SWEEP = (2, 4, 8, 16)
MAX_TURNS = 2000
THRESHOLD = 0.9


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def fixed_channel(n: int, m: int) -> tuple[np.ndarray, float]:
    library = synthesize_type_library(m)
    lookup = local_reward_lookup(n, library.parameters)
    means = lookup[:, len(ACTIONS) - 1, 4 * n]  # all agents contribute 1.0
    distances = squared_hellinger_gaussians(means[:, None], means[None, :])
    distances[np.tril_indices(m)] = np.inf
    return means, float(np.min(distances))


def simulate_cell(n: int, m: int) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    means, rho_action = fixed_channel(n, m)
    raw: list[dict[str, object]] = []
    checkpoint_errors: dict[int, list[float]] = {turn: [] for turn in (1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2000)}
    for seed in SEEDS:
        rng = np.random.default_rng(seed + 100_000 * m + 1_000 * n)
        true_types = rng.integers(0, m, size=n)
        posterior = np.full((n, m), 1.0 / m, dtype=float)
        first_turn = np.full(n, np.nan, dtype=float)
        for turn in range(1, MAX_TURNS + 1):
            observations = rng.normal(means[true_types], SIGMA)
            residual = observations[:, None] - means[None, :]
            posterior *= np.exp(-0.5 * (residual / SIGMA) ** 2) + 1e-300
            posterior /= posterior.sum(axis=1, keepdims=True)
            mass = posterior[np.arange(n), true_types]
            newly = np.isnan(first_turn) & (mass > THRESHOLD)
            first_turn[newly] = turn
            if turn in checkpoint_errors:
                checkpoint_errors[turn].extend((1.0 - mass).tolist())
            if np.all(np.isfinite(first_turn)) and turn >= max(checkpoint_errors):
                break
        for agent in range(n):
            raw.append(
                {
                    "n": n,
                    "m": m,
                    "seed": seed,
                    "agent": agent,
                    "true_type": int(true_types[agent]),
                    "first_turn": repr(float(first_turn[agent])),
                    "censored": bool(not math.isfinite(first_turn[agent])),
                    "rho_action": repr(rho_action),
                }
            )
    contraction = [
        {
            "n": n,
            "m": m,
            "turn": turn,
            "rho_action": repr(rho_action),
            "scaled_information": repr(turn * rho_action),
            "mean_posterior_error": repr(float(np.mean(values))),
            "sem_posterior_error": repr(float(np.std(values, ddof=1) / math.sqrt(len(values)))),
            "observations": len(values),
        }
        for turn, values in checkpoint_errors.items()
        if values
    ]
    return raw, contraction


def ols(x: list[float], y: list[float]) -> dict[str, float]:
    x_array = np.asarray(x, dtype=float)
    y_array = np.asarray(y, dtype=float)
    slope, intercept = np.polyfit(x_array, y_array, 1)
    predicted = slope * x_array + intercept
    denominator = float(np.sum((y_array - y_array.mean()) ** 2))
    r_squared = 1.0 - float(np.sum((y_array - predicted) ** 2)) / denominator if denominator > 0.0 else 1.0
    return {"slope": float(slope), "intercept": float(intercept), "r_squared": float(r_squared), "observations": len(x)}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cells = sorted({(3, m) for m in TYPE_SWEEP} | {(n, 8) for n in N_SWEEP})
    base_raw: dict[tuple[int, int], list[dict[str, object]]] = {}
    contraction_rows: list[dict[str, object]] = []
    for n, m in cells:
        raw, contraction = simulate_cell(n, m)
        base_raw[(n, m)] = raw
        contraction_rows.extend(contraction)

    raw_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    for m in TYPE_SWEEP:
        cell = base_raw[(3, m)]
        rho = float(cell[0]["rho_action"])
        log_c = math.log(m * math.sqrt(m))
        for H in H_SWEEP:
            passages_by_seed: dict[int, list[float]] = {seed: [] for seed in SEEDS}
            per_agent_episodes: list[float] = []
            for row in cell:
                first_turn = float(row["first_turn"])
                first_episode = math.ceil(first_turn / H) if math.isfinite(first_turn) else math.nan
                passages_by_seed[int(row["seed"])].append(first_episode)
                per_agent_episodes.append(first_episode)
                raw_rows.append({"phase": "type_horizon", "H": H, **row, "first_episode": repr(first_episode)})
            all_agent = np.asarray(
                [max(values) if all(math.isfinite(value) for value in values) else math.nan for values in passages_by_seed.values()]
            )
            finite_agents = np.asarray([value for value in per_agent_episodes if math.isfinite(value)])
            finite_all = all_agent[np.isfinite(all_agent)]
            summary_rows.append(
                {
                    "phase": "type_horizon",
                    "n": 3,
                    "m": m,
                    "H": H,
                    "rho_action": repr(rho),
                    "predictor_per_agent": repr(log_c / (rho * H)),
                    "predictor_all_agent": repr((log_c + math.log(3)) / (rho * H)),
                    "median_per_agent_episode": repr(float(np.median(finite_agents))) if len(finite_agents) else "nan",
                    "median_all_agent_episode": repr(float(np.median(finite_all))) if len(finite_all) >= len(SEEDS) / 2 else "nan",
                    "censored_agents": len(per_agent_episodes) - len(finite_agents),
                    "censored_seeds": len(all_agent) - len(finite_all),
                }
            )

    for n in N_SWEEP:
        m, H = 8, 4
        cell = base_raw[(n, m)]
        rho = float(cell[0]["rho_action"])
        log_c = math.log(m * math.sqrt(m))
        passages_by_seed: dict[int, list[float]] = {seed: [] for seed in SEEDS}
        per_agent_episodes: list[float] = []
        for row in cell:
            first_turn = float(row["first_turn"])
            first_episode = math.ceil(first_turn / H) if math.isfinite(first_turn) else math.nan
            passages_by_seed[int(row["seed"])].append(first_episode)
            per_agent_episodes.append(first_episode)
            raw_rows.append({"phase": "population", "H": H, **row, "first_episode": repr(first_episode)})
        all_agent = np.asarray(
            [max(values) if all(math.isfinite(value) for value in values) else math.nan for values in passages_by_seed.values()]
        )
        finite_agents = np.asarray([value for value in per_agent_episodes if math.isfinite(value)])
        finite_all = all_agent[np.isfinite(all_agent)]
        summary_rows.append(
            {
                "phase": "population",
                "n": n,
                "m": m,
                "H": H,
                "rho_action": repr(rho),
                "predictor_per_agent": repr(log_c / (rho * H)),
                "predictor_all_agent": repr((log_c + math.log(n)) / (rho * H)),
                "median_per_agent_episode": repr(float(np.median(finite_agents))) if len(finite_agents) else "nan",
                "median_all_agent_episode": repr(float(np.median(finite_all))) if len(finite_all) >= len(SEEDS) / 2 else "nan",
                "censored_agents": len(per_agent_episodes) - len(finite_agents),
                "censored_seeds": len(all_agent) - len(finite_all),
            }
        )

    type_rows = [row for row in summary_rows if row["phase"] == "type_horizon" and math.isfinite(float(row["median_per_agent_episode"]))]
    population_rows = [row for row in summary_rows if row["phase"] == "population" and math.isfinite(float(row["median_all_agent_episode"]))]
    type_fit = ols([float(row["predictor_per_agent"]) for row in type_rows], [float(row["median_per_agent_episode"]) for row in type_rows])
    population_fit = ols([float(row["predictor_all_agent"]) for row in population_rows], [float(row["median_all_agent_episode"]) for row in population_rows])

    write_csv(RAW_OUT, raw_rows, list(raw_rows[0]))
    write_csv(SUMMARY_OUT, summary_rows, list(summary_rows[0]))
    write_csv(CONTRACTION_OUT, contraction_rows, list(contraction_rows[0]))
    fits = {
        "status": "pilot",
        "provider_calls": 0,
        "stochastic_channel": "y ~ Normal(mu_true(action), sigma^2)",
        "diagnostic_action": "all agents contribute 1.0",
        "seeds": list(SEEDS),
        "max_turns": MAX_TURNS,
        "threshold": THRESHOLD,
        "type_horizon_fit": type_fit,
        "population_fit": population_fit,
        "limitations": [
            "H points reuse one stochastic turn stream and are regrouped into episodes; they are not independent cells.",
            "Only three unique type-library sizes and four population sizes are included.",
            "The diagnostic action is fixed rather than selected by the adaptive PACT planner.",
            "OLS is on cell medians; a full study should fit seed/agent first-passage data with bootstrap or survival methods.",
            "The action-specific rho is not the proposition's worst-case uniform rho over every reachable action.",
        ],
    }
    FIT_OUT.write_text(json.dumps(fits, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Claim B v2 — Theory-Aligned Stochastic-Channel Pilot",
        "",
        "This is a new pilot, not a replacement or retuning of the completed preregistered scaling run. It targets the per-agent posterior contraction used in Proposition `prop:tid-collapse`.",
        "",
        "## Design",
        "",
        "- Outcomes are sampled from the Gaussian channel used by the likelihood: `y ~ Normal(mu_true, sigma^2)`.",
        "- A fixed all-contribution HP-SPGG action isolates the outcome channel and gives a measured action-specific Hellinger margin.",
        "- Type/horizon phase: n=3, m in {4,8,16}, H in {1,4,16}.",
        "- Population phase: m=8, H=4, n in {2,4,8,16}.",
        "- 200 seeds, posterior threshold 0.9, maximum 2,000 turns; censored observations are retained.",
        "- Per-agent predictor: log(m*sqrt(m))/(rho_action*H), matching the proof switching term up to constants.",
        "- All-agent predictor: [log(m*sqrt(m))+log(n)]/(rho_action*H), using log(n), not linear n.",
        "",
        "## Cell summaries",
        "",
        "| phase | n | m | H | rho action | per-agent predictor | all-agent predictor | median per-agent | median all-agent | censored agents | censored seeds |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['phase']} | {row['n']} | {row['m']} | {row['H']} | {row['rho_action']} | "
            f"{row['predictor_per_agent']} | {row['predictor_all_agent']} | {row['median_per_agent_episode']} | "
            f"{row['median_all_agent_episode']} | {row['censored_agents']} | {row['censored_seeds']} |"
        )
    lines.extend(
        [
            "",
            "## Pilot fits",
            "",
            "```json",
            json.dumps(fits, indent=2),
            "```",
            "",
            "## Interpretation rule",
            "",
            "The pilot is promising only if the type/horizon fit has a positive slope and materially nonzero R-squared, H approximately rescales first-passage episodes inversely, and the population fit is compatible with log(n). Censored cells remain censored; they are not deleted or imputed into OLS.",
            "",
            "## Pilot limitations",
            "",
            "The high R-squared values are evidence that the corrected variables are aligned, not final theorem validation. H points reuse the same stochastic turn streams and differ by episode grouping; only three m values and four n values are available; the action is fixed; and OLS treats cell medians rather than seed/agent first-passage observations. A confirmatory run should use independent cell replicates or a hierarchical/survival model and should separately test the adaptive planner with realized information accumulation.",
        ]
    )
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "raw_rows": len(raw_rows), "summary_rows": len(summary_rows), "contraction_rows": len(contraction_rows), "fits": fits}, indent=2))


if __name__ == "__main__":
    main()
