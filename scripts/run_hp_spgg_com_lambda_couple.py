"""Build lambda-coupled HP-SPGG-COM tensors and measure decoupling error."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_hpgg.environment import load_calibration  # noqa: E402
from llm_hpgg.personas import PERSONAS  # noqa: E402
from llm_hpgg_com.real_hp_spgg_com import (  # noqa: E402
    RealMessagePolicy,
    action_preferences,
    evaluate_factorized,
    make_real_model,
    named_policies,
)


ANALYSIS_DIR = ROOT / "analysis" / "hp_spgg_com"
FIG_DIRS = [ROOT / "figs", ROOT / "arr_paper" / "figs"]


@dataclass(frozen=True)
class JudgeSpec:
    name: str
    short_name: str
    calibration: Path
    color: str
    marker: str


JUDGES = [
    JudgeSpec(
        name="GPT-5.4-mini",
        short_name="GPT-mini",
        calibration=ANALYSIS_DIR / "calibration_gpt_5_4_mini_n2_live_s10.npy",
        color="#c0463f",
        marker="s",
    ),
    JudgeSpec(
        name="DeepSeek-V3.2",
        short_name="DeepSeek",
        calibration=ANALYSIS_DIR / "calibration_deepseek_v3_2_n2_live_s10.npy",
        color="#1b3a6f",
        marker="o",
    ),
    JudgeSpec(
        name="Kimi-K2.6",
        short_name="Kimi",
        calibration=ANALYSIS_DIR / "calibration_kimi_k2_6_n2_live_s10.npy",
        color="#2c7a5e",
        marker="D",
    ),
    JudgeSpec(
        name="Llama-4-Maverick",
        short_name="Llama",
        calibration=ANALYSIS_DIR / "calibration_llama_4_maverick_n2_live_s10.npy",
        color="#b8723d",
        marker="^",
    ),
]


@dataclass(frozen=True)
class CoupledModel:
    reward_tensor: np.ndarray  # (2, type_count, type_count, profile_count)
    action_profiles: np.ndarray
    actions: np.ndarray
    prior: np.ndarray  # (2, type_count)
    action_likelihood: np.ndarray  # (2, type_count, type_count, action_count)
    comm_cost: float
    identifiability: float

    @property
    def type_count(self) -> int:
        return int(self.reward_tensor.shape[1])

    @property
    def profile_count(self) -> int:
        return int(self.reward_tensor.shape[-1])


def parse_lam_grid(raw: str) -> list[float]:
    return [float(item.strip()) for item in raw.split(",") if item.strip()]


def load_base(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    payload = load_calibration(path)
    reward_tensor = np.asarray(payload["reward_tensor"], dtype=float)
    action_profiles = np.asarray(payload["action_profiles"], dtype=float)
    actions = np.asarray(payload["actions"], dtype=float)
    if reward_tensor.shape != (2, 4, 25):
        raise ValueError(f"Unexpected reward tensor shape for {path}: {reward_tensor.shape}")
    if action_profiles.shape != (25, 2):
        raise ValueError(f"Unexpected action profile shape for {path}: {action_profiles.shape}")
    return reward_tensor, action_profiles, actions


def build_type_match_coupling(base: np.ndarray, action_profiles: np.ndarray) -> tuple[np.ndarray, dict[str, float | str]]:
    n_agents, type_count, profile_count = base.shape
    raw = np.zeros((n_agents, type_count, type_count, profile_count), dtype=float)
    targets = np.array([float(persona.target_contribution) for persona in PERSONAS[:type_count]], dtype=float)
    cooperation = np.array([float(persona.cooperation_weight) for persona in PERSONAS[:type_count]], dtype=float)
    sensitivity = 0.75 + 0.25 * (cooperation / max(float(np.max(cooperation)), 1e-12))
    for agent in range(n_agents):
        own_actions = action_profiles[:, agent]
        for own_type in range(type_count):
            for partner_type in range(type_count):
                fit_to_partner = 1.0 - np.abs(own_actions - targets[partner_type])
                raw[agent, own_type, partner_type] = sensitivity[own_type] * fit_to_partner

    centered = raw - raw.mean(axis=2, keepdims=True)
    scale = float(base.std() / (centered.std() + 1e-12))
    coupling = centered * scale
    return coupling, {
        "design": "centered type-match coordination: agent action fits teammate target_contribution, scaled to base reward std",
        "base_std": float(base.std()),
        "raw_std": float(raw.std()),
        "centered_raw_std": float(centered.std()),
        "coupling_std": float(coupling.std()),
        "coupling_min": float(coupling.min()),
        "coupling_max": float(coupling.max()),
    }


def build_coupled_tensor(base: np.ndarray, coupling: np.ndarray, lam: float) -> np.ndarray:
    return base[:, :, None, :] + float(lam) * coupling


def verify_lambda_zero_anchor(base: np.ndarray, coupling: np.ndarray) -> None:
    coupled = build_coupled_tensor(base, coupling, 0.0)
    if not np.allclose(coupled[:, :, 0, :], base):
        raise AssertionError("lambda=0 first teammate-type slice does not equal base")
    for partner_type in range(coupled.shape[2]):
        if not np.allclose(coupled[:, :, partner_type, :], base):
            raise AssertionError(f"lambda=0 teammate-type slice {partner_type} does not equal base")


def softmax(values: np.ndarray, temperature: float) -> np.ndarray:
    scaled = np.asarray(values, dtype=float) / max(float(temperature), 1e-12)
    scaled -= float(np.max(scaled))
    exp = np.exp(scaled)
    return exp / float(exp.sum())


def coupled_action_likelihood(
    reward_tensor: np.ndarray,
    action_profiles: np.ndarray,
    actions: np.ndarray,
    identifiability: float,
    temperature: float = 0.08,
) -> np.ndarray:
    n_agents, type_count, _, _ = reward_tensor.shape
    uniform = np.full(len(actions), 1.0 / len(actions), dtype=float)
    rho = min(max(float(identifiability), 0.0), 1.0)
    likelihood = np.zeros((n_agents, type_count, type_count, len(actions)), dtype=float)
    for agent in range(n_agents):
        for own_type in range(type_count):
            for partner_type in range(type_count):
                scores = []
                for action in actions:
                    mask = np.isclose(action_profiles[:, agent], action)
                    scores.append(float(np.mean(reward_tensor[agent, own_type, partner_type, mask])))
                type_policy = softmax(np.asarray(scores, dtype=float), temperature)
                likelihood[agent, own_type, partner_type] = (1.0 - rho) * uniform + rho * type_policy
    return likelihood


def make_coupled_model(
    base: np.ndarray,
    action_profiles: np.ndarray,
    actions: np.ndarray,
    coupling: np.ndarray,
    lam: float,
    identifiability: float,
    comm_cost: float,
) -> CoupledModel:
    reward_tensor = build_coupled_tensor(base, coupling, lam)
    prior = np.full(base.shape[:2], 1.0 / base.shape[1], dtype=float)
    likelihood = coupled_action_likelihood(reward_tensor, action_profiles, actions, identifiability)
    return CoupledModel(
        reward_tensor=reward_tensor,
        action_profiles=action_profiles,
        actions=actions,
        prior=prior,
        action_likelihood=likelihood,
        comm_cost=float(comm_cost),
        identifiability=float(identifiability),
    )


def teammate(agent: int) -> int:
    return 1 - int(agent)


def reveal_obs(theta: int) -> int:
    return 100 + int(theta)


def is_reveal_obs(obs: int) -> bool:
    return int(obs) >= 100


def obs_revealed_type(obs: int) -> int:
    return int(obs) - 100


def type_profiles(type_count: int) -> np.ndarray:
    return np.asarray(list(product(range(type_count), repeat=2)), dtype=int)


def welfare_by_type_profile(model: CoupledModel) -> np.ndarray:
    profiles = type_profiles(model.type_count)
    welfare = np.zeros((len(profiles), model.profile_count), dtype=float)
    for idx, (theta_0, theta_1) in enumerate(profiles):
        welfare[idx] = model.reward_tensor[0, theta_0, theta_1] + model.reward_tensor[1, theta_1, theta_0]
    return welfare


def possible_observations(model: CoupledModel, policy: RealMessagePolicy, agent: int) -> list[int]:
    observations: set[int] = set()
    for theta in range(model.type_count):
        if policy.reveals(agent, theta):
            observations.add(reveal_obs(theta))
        else:
            observations.update(range(len(model.actions)))
    return sorted(observations)


def observation_likelihood(model: CoupledModel, policy: RealMessagePolicy, theta_profile: np.ndarray, agent: int, obs: int) -> float:
    own_type = int(theta_profile[agent])
    partner_type = int(theta_profile[teammate(agent)])
    if is_reveal_obs(obs):
        return 1.0 if policy.reveals(agent, own_type) and own_type == obs_revealed_type(obs) else 0.0
    if policy.reveals(agent, own_type):
        return 0.0
    return float(model.action_likelihood[agent, own_type, partner_type, int(obs)])


def exact_value(model: CoupledModel, policy: RealMessagePolicy) -> float:
    profiles = type_profiles(model.type_count)
    prior_weights = np.full(len(profiles), 1.0 / len(profiles), dtype=float)
    welfare = welfare_by_type_profile(model)
    obs_lists = [possible_observations(model, policy, agent) for agent in range(2)]
    total = 0.0
    for obs_0, obs_1 in product(*obs_lists):
        weights = prior_weights.copy()
        for profile_index, theta_profile in enumerate(profiles):
            weights[profile_index] *= observation_likelihood(model, policy, theta_profile, 0, obs_0)
            weights[profile_index] *= observation_likelihood(model, policy, theta_profile, 1, obs_1)
        obs_prob = float(weights.sum())
        if obs_prob <= 0.0:
            continue
        messages = int(is_reveal_obs(obs_0)) + int(is_reveal_obs(obs_1))
        unnormalized_scores = weights @ welfare
        total += float(np.max(unnormalized_scores)) - obs_prob * model.comm_cost * messages
    return float(total)


def marginal_likelihood(model: CoupledModel, agent: int) -> np.ndarray:
    partner_prior = model.prior[teammate(agent)]
    return np.einsum("p,ops->os", partner_prior, model.action_likelihood[agent])


def decoupled_agent_outcomes(model: CoupledModel, agent: int, policy: RealMessagePolicy) -> list[tuple[float, np.ndarray, int]]:
    outcomes: list[tuple[float, np.ndarray, int]] = []
    lbar = marginal_likelihood(model, agent)
    for theta in range(model.type_count):
        if policy.reveals(agent, theta):
            belief = np.zeros(model.type_count, dtype=float)
            belief[theta] = 1.0
            outcomes.append((float(model.prior[agent, theta]), belief, 1))
    for signal in range(len(model.actions)):
        unnormalized = np.zeros(model.type_count, dtype=float)
        for theta in range(model.type_count):
            if policy.reveals(agent, theta):
                continue
            unnormalized[theta] = model.prior[agent, theta] * lbar[theta, signal]
        prob = float(unnormalized.sum())
        if prob <= 0.0:
            continue
        outcomes.append((prob, unnormalized / prob, 0))
    return outcomes


def decoupled_expected_profile_scores(model: CoupledModel, beliefs: tuple[np.ndarray, np.ndarray]) -> np.ndarray:
    belief_0, belief_1 = beliefs
    scores = np.zeros(model.profile_count, dtype=float)
    for profile_index in range(model.profile_count):
        scores[profile_index] += float(np.einsum("i,j,ij->", belief_0, belief_1, model.reward_tensor[0, :, :, profile_index]))
        scores[profile_index] += float(np.einsum("i,j,ij->", belief_1, belief_0, model.reward_tensor[1, :, :, profile_index]))
    return scores


def decoupled_closed_form_value(model: CoupledModel, policy: RealMessagePolicy) -> float:
    outcomes = [decoupled_agent_outcomes(model, agent, policy) for agent in range(2)]
    total = 0.0
    for outcome_0, outcome_1 in product(*outcomes):
        prob_0, belief_0, message_0 = outcome_0
        prob_1, belief_1, message_1 = outcome_1
        prob = prob_0 * prob_1
        messages = message_0 + message_1
        scores = decoupled_expected_profile_scores(model, (belief_0, belief_1))
        total += prob * (float(np.max(scores)) - model.comm_cost * messages)
    return float(total)


def enumerate_policies(type_count: int) -> Iterable[RealMessagePolicy]:
    for bits in product([False, True], repeat=2 * type_count):
        reveal = np.asarray(bits, dtype=bool).reshape(2, type_count)
        yield RealMessagePolicy("POLICY", reveal)


def expected_messages(model: CoupledModel, policy: RealMessagePolicy) -> float:
    return float(np.sum(model.prior * policy.reveal))


def decoupled_pact_local_policy(model: CoupledModel) -> RealMessagePolicy:
    current = RealMessagePolicy("PACT_LOCAL", np.zeros((2, model.type_count), dtype=bool))
    improved = True
    while improved:
        improved = False
        base_value = decoupled_closed_form_value(model, current)
        for agent in range(2):
            for theta in range(model.type_count):
                candidate_reveal = current.reveal.copy()
                candidate_reveal[agent, theta] = not candidate_reveal[agent, theta]
                candidate = RealMessagePolicy("PACT_LOCAL", candidate_reveal)
                value = decoupled_closed_form_value(model, candidate)
                if value > base_value + 1e-12:
                    current = candidate
                    base_value = value
                    improved = True
    return current


def exact_global_opt(model: CoupledModel) -> tuple[float, RealMessagePolicy]:
    best_value = -float("inf")
    best_policy: RealMessagePolicy | None = None
    for policy in enumerate_policies(model.type_count):
        value = exact_value(model, policy)
        if value > best_value + 1e-12:
            best_value = value
            best_policy = policy
    assert best_policy is not None
    return float(best_value), RealMessagePolicy("JOINT_AWARE_GLOBAL_OPT", best_policy.reveal.copy())


def base_anchor_value(calibration: Path, identifiability: float, comm_cost: float, policy_name: str) -> tuple[float, RealMessagePolicy]:
    base_model = make_real_model(calibration=str(calibration), identifiability=identifiability, comm_cost=comm_cost)
    policy = named_policies(base_model)[policy_name]
    return evaluate_factorized(base_model, policy), policy


def is_non_decreasing(values: list[float], tolerance: float = 1e-10) -> bool:
    return all(values[idx + 1] + tolerance >= values[idx] for idx in range(len(values) - 1))


def run_curve(args: argparse.Namespace) -> dict[str, object]:
    lam_grid = parse_lam_grid(args.lam_grid)
    all_rows: list[dict[str, object]] = []
    judge_summaries = []
    for spec in JUDGES:
        base, action_profiles, actions = load_base(spec.calibration)
        coupling, coupling_summary = build_type_match_coupling(base, action_profiles)
        verify_lambda_zero_anchor(base, coupling)
        no_comm_anchor_value, no_comm_anchor_policy = base_anchor_value(spec.calibration, args.identifiability, args.comm_cost, "NO_COMM")
        pact_anchor_value, pact_anchor_policy = base_anchor_value(spec.calibration, args.identifiability, args.comm_cost, "PACT_LOCAL")
        judge_rows = []
        for lam in lam_grid:
            model = make_coupled_model(base, action_profiles, actions, coupling, lam, args.identifiability, args.comm_cost)
            diagnostic_policy = RealMessagePolicy("NO_COMM", np.zeros((2, model.type_count), dtype=bool))
            decoupled_value = decoupled_closed_form_value(model, diagnostic_policy)
            exact_policy_value = exact_value(model, diagnostic_policy)
            pact_policy = decoupled_pact_local_policy(model)
            pact_decoupled_value = decoupled_closed_form_value(model, pact_policy)
            pact_exact_value = exact_value(model, pact_policy)
            exact_opt_value, exact_opt_policy = exact_global_opt(model)
            row = {
                "judge": spec.name,
                "lambda_couple": float(lam),
                "diagnostic_policy": "NO_COMM",
                "decoupled_value": decoupled_value,
                "exact_value": exact_policy_value,
                "abs_error": float(abs(decoupled_value - exact_policy_value)),
                "pact_local_decoupled_value": pact_decoupled_value,
                "pact_local_exact_value": pact_exact_value,
                "pact_local_decoupled_abs_error": float(abs(pact_decoupled_value - pact_exact_value)),
                "joint_aware_global_opt_value": exact_opt_value,
                "pact_local_gap_vs_joint_oracle": float(exact_opt_value - pact_exact_value),
                "pact_local_expected_messages": expected_messages(model, pact_policy),
                "joint_oracle_expected_messages": expected_messages(model, exact_opt_policy),
                "pact_local_reveal_matrix": pact_policy.reveal.astype(int).tolist(),
                "joint_oracle_reveal_matrix": exact_opt_policy.reveal.astype(int).tolist(),
                "lambda_zero_anchor_abs_error_to_existing_base": None,
                "lambda_zero_pact_anchor_abs_error_to_existing_base": None,
            }
            if abs(float(lam)) <= 1e-12:
                row["lambda_zero_anchor_abs_error_to_existing_base"] = float(abs(exact_policy_value - no_comm_anchor_value))
                row["lambda_zero_policy_matches_existing_base"] = bool(np.array_equal(diagnostic_policy.reveal, no_comm_anchor_policy.reveal))
                row["lambda_zero_pact_anchor_abs_error_to_existing_base"] = float(abs(pact_exact_value - pact_anchor_value))
                row["lambda_zero_pact_policy_matches_existing_base"] = bool(np.array_equal(pact_policy.reveal, pact_anchor_policy.reveal))
            judge_rows.append(row)
            all_rows.append(row)
        errors = [float(row["abs_error"]) for row in judge_rows]
        gaps = [float(row["pact_local_gap_vs_joint_oracle"]) for row in judge_rows]
        judge_summaries.append(
            {
                "judge": spec.name,
                "calibration": str(spec.calibration.relative_to(ROOT)),
                "coupling_summary": coupling_summary,
                "diagnostic_policy": "NO_COMM",
                "lambda_zero_anchor_value": no_comm_anchor_value,
                "lambda_zero_anchor_abs_error_to_existing_base": judge_rows[0]["lambda_zero_anchor_abs_error_to_existing_base"],
                "lambda_zero_policy_matches_existing_base": judge_rows[0].get("lambda_zero_policy_matches_existing_base", False),
                "lambda_zero_pact_anchor_value": pact_anchor_value,
                "lambda_zero_pact_anchor_abs_error_to_existing_base": judge_rows[0]["lambda_zero_pact_anchor_abs_error_to_existing_base"],
                "lambda_zero_pact_policy_matches_existing_base": judge_rows[0].get("lambda_zero_pact_policy_matches_existing_base", False),
                "abs_error_monotone_non_decreasing": is_non_decreasing(errors),
                "pact_local_gap_monotone_non_decreasing": is_non_decreasing(gaps),
                "max_abs_error": float(max(errors)),
                "max_pact_local_gap_vs_joint_oracle": float(max(gaps)),
            }
        )
    return {
        "setting": {
            "n_agents": 2,
            "type_count": 4,
            "n_actions": 5,
            "identifiability": float(args.identifiability),
            "comm_cost": float(args.comm_cost),
            "lambda_grid": lam_grid,
            "coupling_design": "Analytic centered type-match coordination term; lambda_couple scales teammate-type reward dependence.",
            "central_identity": "lambda_couple = strength of reward dependence on teammate type = degree of reward-locality violation.",
            "primary_abs_error_policy": "NO_COMM fixed reveal policy, used to isolate posterior decoupling error from adaptive reveal-policy switching.",
            "decision_quality_metric": "Adaptive decoupled PACT_LOCAL gap against the joint-aware global reveal-policy oracle.",
        },
        "pf_check": {
            "pf_statement": "PF is the factorized prior over persona types: P(theta_1, theta_2) = P_1(theta_1) P_2(theta_2).",
            "pf_untouched_by_lambda_couple": True,
            "explanation": "lambda_couple changes reward and induced action-signal likelihood dependence on teammate type, but the initial prior remains uniform and factorized. Posterior non-factorization for lambda>0 is the measured consequence of RL violation, not a separate PF perturbation.",
        },
        "honesty_statement": "For lambda_couple > 0, the decoupled evaluator is a deliberately misspecified approximation. The primary abs_error curve uses a fixed NO_COMM policy to isolate posterior decoupling error; the PACT_LOCAL curve separately measures decision quality under the adaptive decoupled reveal rule. Neither curve claims optimality under coupling.",
        "judge_summaries": judge_summaries,
        "rows": all_rows,
        "overall": {
            "all_lambda_zero_anchors_exact": all(float(summary["lambda_zero_anchor_abs_error_to_existing_base"]) <= 1e-10 for summary in judge_summaries),
            "all_abs_error_curves_monotone": all(bool(summary["abs_error_monotone_non_decreasing"]) for summary in judge_summaries),
            "all_pact_gap_curves_monotone": all(bool(summary["pact_local_gap_monotone_non_decreasing"]) for summary in judge_summaries),
        },
    }


def plot_curve(payload: dict[str, object]) -> None:
    rows = payload["rows"]
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.0), sharex=True)
    for spec in JUDGES:
        judge_rows = [row for row in rows if row["judge"] == spec.name]
        xs = [float(row["lambda_couple"]) for row in judge_rows]
        errors = [float(row["abs_error"]) for row in judge_rows]
        gaps = [float(row["pact_local_gap_vs_joint_oracle"]) for row in judge_rows]
        axes[0].plot(xs, errors, marker=spec.marker, color=spec.color, linewidth=1.8, markersize=5, label=spec.short_name)
        axes[1].plot(xs, gaps, marker=spec.marker, color=spec.color, linewidth=1.8, markersize=5, label=spec.short_name)
    axes[0].set_title("Decoupled value error")
    axes[0].set_ylabel("|decoupled - exact|")
    axes[1].set_title("Decision-quality gap")
    axes[1].set_ylabel("Joint oracle - PACT-local")
    for ax in axes:
        ax.set_xlabel(r"Coupling strength $\lambda_{couple}$")
        ax.grid(alpha=0.25, linewidth=0.7)
    axes[1].legend(frameon=False, fontsize=8, loc="upper left")
    fig.suptitle("PACT-COM lambda-couple: cost of decoupled approximation under RL violation", fontsize=12, fontweight="semibold")
    fig.tight_layout()
    for out_dir in FIG_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_dir / "fig_lambda_couple_decoupling_error.png", dpi=220, bbox_inches="tight")
        fig.savefig(out_dir / "fig_lambda_couple_decoupling_error.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--identifiability", type=float, default=0.35)
    parser.add_argument("--comm-cost", type=float, default=0.15)
    parser.add_argument("--lam-grid", default="0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0,1.25,1.5,2.0")
    args = parser.parse_args()
    payload = run_curve(args)
    out_path = ANALYSIS_DIR / "lambda_couple_curve.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    plot_curve(payload)
    print(json.dumps({"output": str(out_path.relative_to(ROOT)), "overall": payload["overall"]}, indent=2))


if __name__ == "__main__":
    main()