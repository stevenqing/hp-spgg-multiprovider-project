"""Run offline HP-SPGG deployment-robustness diagnostics.

This experiment uses the analytic HP-SPGG calibration surface and therefore
makes no LLM/API calls.  It separates five deployment failure modes:

* likelihood-temperature mismatch;
* additive noise on per-type log likelihoods;
* top-k truncation of the type likelihood vector;
* fixed calibration drift in the candidate reward model;
* out-of-library personas represented by convex mixtures of templates;
* approximate planning through a restricted random candidate set.

The environment uses the unperturbed reward tensor.  PACT+ plans and updates
with the perturbed inference model, so regret is always measured against the
exact full-information optimum in the true environment.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_hpgg.coordinator import CoordinatorState, posterior_expected_profile_scores
from llm_hpgg.environment import build_reward_tensor, rewards_for_types, welfare_for_types


DEFAULT_JSON = ROOT / "analysis" / "hp_spgg_deployment_robustness.json"
DEFAULT_CSV = ROOT / "analysis" / "hp_spgg_deployment_robustness.csv"
DEFAULT_MD = ROOT / "analysis" / "hp_spgg_deployment_robustness.md"


@dataclass(frozen=True)
class Condition:
    name: str
    family: str
    value: float | int | None = None
    likelihood_temperature: float = 1.0
    log_likelihood_noise: float = 0.0
    top_k: int | None = None
    calibration_drift: float = 0.0
    persona_mixture: float = 0.0
    planner_candidates: int | None = None


CONDITIONS = (
    Condition("reference", "reference"),
    Condition("temperature_0.5", "likelihood_temperature", 0.5, likelihood_temperature=0.5),
    Condition("temperature_2", "likelihood_temperature", 2.0, likelihood_temperature=2.0),
    Condition("temperature_4", "likelihood_temperature", 4.0, likelihood_temperature=4.0),
    Condition("log_noise_0.25", "log_likelihood_noise", 0.25, log_likelihood_noise=0.25),
    Condition("log_noise_0.5", "log_likelihood_noise", 0.5, log_likelihood_noise=0.5),
    Condition("log_noise_1.0", "log_likelihood_noise", 1.0, log_likelihood_noise=1.0),
    Condition("top_k_2", "top_k", 2, top_k=2),
    Condition("top_k_1", "top_k", 1, top_k=1),
    Condition("calibration_drift_0.02", "calibration_drift", 0.02, calibration_drift=0.02),
    Condition("calibration_drift_0.05", "calibration_drift", 0.05, calibration_drift=0.05),
    Condition("calibration_drift_0.10", "calibration_drift", 0.10, calibration_drift=0.10),
    Condition("persona_mix_0.10", "persona_mixture", 0.10, persona_mixture=0.10),
    Condition("persona_mix_0.25", "persona_mixture", 0.25, persona_mixture=0.25),
    Condition("persona_mix_0.50", "persona_mixture", 0.50, persona_mixture=0.50),
    Condition("planner_candidates_32", "planner_candidates", 32, planner_candidates=32),
    Condition("planner_candidates_8", "planner_candidates", 8, planner_candidates=8),
)


def true_reward_tensor(base: np.ndarray, mixture: float) -> np.ndarray:
    if mixture <= 0.0:
        return np.array(base, copy=True)
    mixed = np.empty_like(base)
    type_count = base.shape[1]
    for type_index in range(type_count):
        neighbour = (type_index + 1) % type_count
        mixed[:, type_index, :] = (1.0 - mixture) * base[:, type_index, :] + mixture * base[:, neighbour, :]
    return mixed


def inference_reward_tensor(base: np.ndarray, drift: float, seed: int) -> np.ndarray:
    if drift <= 0.0:
        return np.array(base, copy=True)
    rng = np.random.default_rng(seed + 1_000_003)
    return np.clip(base + rng.normal(0.0, drift, size=base.shape), 0.0, 1.0)


def distorted_update(
    state: CoordinatorState,
    profile_index: int,
    observed_rewards: np.ndarray,
    rng: np.random.Generator,
    condition: Condition,
    likelihood_sigma: float,
) -> None:
    for player_index in range(state.posterior.shape[0]):
        residual = observed_rewards[player_index] - state.reward_tensor[player_index, :, profile_index]
        log_likelihood = -0.5 * (residual / likelihood_sigma) ** 2
        log_likelihood /= condition.likelihood_temperature
        if condition.log_likelihood_noise > 0.0:
            log_likelihood += rng.normal(0.0, condition.log_likelihood_noise, size=log_likelihood.shape)
        if condition.top_k is not None and condition.top_k < len(log_likelihood):
            retained = np.argpartition(log_likelihood, -condition.top_k)[-condition.top_k:]
            mask = np.ones(len(log_likelihood), dtype=bool)
            mask[retained] = False
            log_likelihood[mask] = -np.inf
        finite = np.isfinite(log_likelihood)
        weights = np.zeros_like(log_likelihood)
        if finite.any():
            weights[finite] = np.exp(log_likelihood[finite] - float(np.max(log_likelihood[finite])))
        state.posterior[player_index] *= weights
        total = float(np.sum(state.posterior[player_index]))
        if total <= 0.0:
            state.posterior[player_index] = 1.0 / state.posterior.shape[1]
        else:
            state.posterior[player_index] /= total


def choose_profile(
    state: CoordinatorState,
    rng: np.random.Generator,
    planner_candidates: int | None,
) -> int:
    scores = posterior_expected_profile_scores(state, uncertainty_bonus=True)
    if planner_candidates is None or planner_candidates >= len(scores):
        return int(np.argmax(scores))
    candidates = rng.choice(len(scores), size=planner_candidates, replace=False)
    return int(candidates[int(np.argmax(scores[candidates]))])


def run_seed(
    base_tensor: np.ndarray,
    action_profiles: np.ndarray,
    condition: Condition,
    seed: int,
    episodes: int,
    beta: float,
    likelihood_sigma: float,
) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    n, type_count, _ = base_tensor.shape
    truth_tensor = true_reward_tensor(base_tensor, condition.persona_mixture)
    inference_tensor = inference_reward_tensor(base_tensor, condition.calibration_drift, seed)
    true_types = rng.integers(0, type_count, size=n)
    state = CoordinatorState.fresh(n, type_count, inference_tensor, action_profiles, beta)
    cumulative_regret = 0.0

    true_welfare = np.array(
        [welfare_for_types(truth_tensor, true_types, index) for index in range(len(action_profiles))],
        dtype=float,
    )
    oracle_welfare = float(np.max(true_welfare))

    for _ in range(episodes):
        chosen = choose_profile(state, rng, condition.planner_candidates)
        observed_rewards = rewards_for_types(truth_tensor, true_types, chosen)
        cumulative_regret += max(0.0, oracle_welfare - float(true_welfare[chosen]))
        distorted_update(state, chosen, observed_rewards, rng, condition, likelihood_sigma)

    true_mass = float(np.mean(state.posterior[np.arange(n), true_types]))
    map_accuracy = float(np.mean(np.argmax(state.posterior, axis=1) == true_types))
    clipped = np.clip(state.posterior, 1e-15, 1.0)
    entropy = float(np.mean(-np.sum(clipped * np.log(clipped), axis=1) / math.log(type_count)))
    return {
        "cumulative_regret": cumulative_regret,
        "true_type_mass": true_mass,
        "map_accuracy": map_accuracy,
        "normalized_entropy": entropy,
    }


def mean_sem(values: list[float]) -> tuple[float, float]:
    array = np.asarray(values, dtype=float)
    mean = float(np.mean(array))
    sem = float(np.std(array, ddof=1) / math.sqrt(len(array))) if len(array) > 1 else 0.0
    return mean, sem


def run_experiment(seeds: int, episodes: int, beta: float, likelihood_sigma: float) -> dict[str, Any]:
    bundle = build_reward_tensor(n=3, backend="mixed", samples=3, seed=19, trap=False)
    summaries: list[dict[str, Any]] = []
    raw: dict[str, list[dict[str, float]]] = {}
    for condition in CONDITIONS:
        records = [
            run_seed(
                bundle.reward_tensor,
                bundle.action_profiles,
                condition,
                seed,
                episodes,
                beta,
                likelihood_sigma,
            )
            for seed in range(seeds)
        ]
        raw[condition.name] = records
        summary: dict[str, Any] = {
            "condition": condition.name,
            "family": condition.family,
            "value": condition.value,
        }
        for metric in ("cumulative_regret", "true_type_mass", "map_accuracy", "normalized_entropy"):
            mean, sem = mean_sem([record[metric] for record in records])
            summary[f"{metric}_mean"] = mean
            summary[f"{metric}_sem"] = sem
        summaries.append(summary)
        print(
            f"{condition.name:24s} "
            f"regret={summary['cumulative_regret_mean']:.4f}+-{summary['cumulative_regret_sem']:.4f} "
            f"mass={summary['true_type_mass_mean']:.3f} "
            f"acc={summary['map_accuracy_mean']:.3f}"
        )
    return {
        "schema_version": "1.0",
        "experiment": "HP-SPGG offline deployment robustness",
        "data_source": "analytic reward surface with mixed-backend noise profile, seed 19",
        "llm_calls": 0,
        "n": 3,
        "type_count": 4,
        "action_profile_count": int(len(bundle.action_profiles)),
        "episodes": episodes,
        "seeds": seeds,
        "beta": beta,
        "likelihood_sigma": likelihood_sigma,
        "conditions": [asdict(condition) for condition in CONDITIONS],
        "summary": summaries,
        "raw": raw,
    }


def write_csv(path: Path, summaries: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(summaries[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# HP-SPGG Deployment Robustness",
        "",
        "Offline diagnostic; no LLM/API calls. Regret is measured in the unperturbed environment against exact full-information enumeration.",
        "",
        "| condition | family | value | cumulative regret | true-type mass | MAP accuracy | entropy |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in payload["summary"]:
        value = "--" if row["value"] is None else str(row["value"])
        lines.append(
            f"| {row['condition']} | {row['family']} | {value} | "
            f"{row['cumulative_regret_mean']:.3f} $\\pm$ {row['cumulative_regret_sem']:.3f} | "
            f"{row['true_type_mass_mean']:.3f} | {row['map_accuracy_mean']:.3f} | "
            f"{row['normalized_entropy_mean']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation guardrails",
            "",
            "- Likelihood temperature and additive log-likelihood noise perturb the Bayes update only.",
            "- Calibration drift perturbs both the planner's candidate reward model and its likelihood centers.",
            "- Persona mixtures are genuinely out of library: the environment interpolates adjacent templates while inference retains the original discrete menu.",
            "- Restricted candidate planning measures search-budget sensitivity; it is not a CCE solver experiment.",
            "- These controlled analytic diagnostics do not quantify SOTOPIA's project-defined keyword projection, for which no native intent labels exist.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=500)
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--beta", type=float, default=0.25)
    parser.add_argument("--likelihood-sigma", type=float, default=0.08)
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()

    payload = run_experiment(args.seeds, args.episodes, args.beta, args.likelihood_sigma)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_csv(args.csv, payload["summary"])
    write_markdown(args.markdown, payload)
    print(f"json={args.json}")
    print(f"csv={args.csv}")
    print(f"markdown={args.markdown}")


if __name__ == "__main__":
    main()
