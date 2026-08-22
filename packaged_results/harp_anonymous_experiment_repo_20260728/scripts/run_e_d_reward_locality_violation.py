"""Run the E-D true reward-locality violation experiment.

The intervention mirrors the appendix necessity example: only agent 0 receives
an envy/social-comparison term,

        r_0 = (r_0_local(theta_0) - alpha * r_1_local(theta_1) + alpha)
            / (1 + alpha),

while agents 1..n-1 retain local rewards.  This asymmetric edge is deliberate:
a cyclic subtraction would cancel from total welfare and make the intervention
invisible to the centralised regret metric.

PACT knows the coupled reward form for planning but projects the likelihood back
to per-agent marginals.  Joint-PSRL-Coupled maintains the correctly specified
joint posterior.  PSRL-NoType knows the coupled reward form but never learns.
All methods share true types, initial state, and pre-generated random streams.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_hpgg.environment import build_reward_tensor, load_calibration


DEFAULT_OUT_DIR = ROOT / "analysis" / "e_d_reward_locality_violation"
ALGORITHMS = ("pact_factored", "joint_psrl_coupled", "psrl_notype")
LABELS = {
    "pact_factored": "HARP (factored)",
    "joint_psrl_coupled": "Joint-PSRL-Coupled",
    "psrl_notype": "PSRL-NoType",
}
COLORS = {
    "pact_factored": "#12345d",
    "joint_psrl_coupled": "#2f7d5b",
    "psrl_notype": "#9a5a2e",
}


@dataclass(frozen=True)
class CalibrationSpec:
    label: str
    path: Path | None


def parse_float_grid(raw: str) -> list[float]:
    values = [float(item.strip()) for item in raw.split(",") if item.strip()]
    if not values:
        raise ValueError("at least one alpha is required")
    if any(value < 0.0 for value in values):
        raise ValueError("alpha values must be non-negative")
    return values


def parse_action_grid(raw: str | None) -> list[float] | None:
    if raw is None or not raw.strip():
        return None
    values = sorted({float(item.strip()) for item in raw.split(",") if item.strip()})
    if not values:
        raise ValueError("action grid cannot be empty")
    return values


def parse_calibrations(raw_specs: Iterable[str]) -> list[CalibrationSpec]:
    specs: list[CalibrationSpec] = []
    for raw in raw_specs:
        if "=" not in raw:
            raise ValueError(f"calibration must be LABEL=PATH, got {raw!r}")
        label, raw_path = raw.split("=", 1)
        path = Path(raw_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(path)
        specs.append(CalibrationSpec(label.strip(), path))
    return specs or [CalibrationSpec("analytic-mixed", None)]


def select_action_grid(
    tensor: np.ndarray,
    profiles: np.ndarray,
    action_grid: list[float] | None,
) -> tuple[np.ndarray, np.ndarray]:
    if action_grid is None:
        return tensor, profiles
    mask = np.all(
        np.any(np.isclose(profiles[:, :, None], np.asarray(action_grid)[None, None, :]), axis=2),
        axis=1,
    )
    if not np.any(mask):
        raise ValueError(f"no joint profiles match action grid {action_grid}")
    return tensor[:, :, mask], profiles[mask]


def load_bundle(
    spec: CalibrationSpec,
    action_grid: list[float] | None,
) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    if spec.path is None:
        bundle = build_reward_tensor(n=3, backend="mixed", samples=3, seed=19, trap=False)
        tensor, profiles = select_action_grid(
            np.asarray(bundle.reward_tensor, dtype=float),
            np.asarray(bundle.action_profiles, dtype=float),
            action_grid,
        )
        return (
            tensor,
            profiles,
            {"source": "analytic build_reward_tensor", "backend": "mixed", "seed": 19},
        )
    payload = load_calibration(spec.path)
    tensor = np.asarray(payload["reward_tensor"], dtype=float)
    profiles = np.asarray(payload["action_profiles"], dtype=float)
    if tensor.shape[:2] != (3, 4):
        raise ValueError(f"E-D requires n=3 and four types; got {tensor.shape} from {spec.path}")
    tensor, profiles = select_action_grid(tensor, profiles, action_grid)
    return tensor, profiles, {
        "source": str(spec.path.relative_to(ROOT) if spec.path.is_relative_to(ROOT) else spec.path),
        "backend": str(payload.get("backend", "unknown")),
    }


def joint_type_profiles(n: int, type_count: int) -> np.ndarray:
    return np.asarray(list(product(range(type_count), repeat=n)), dtype=int)


def coupled_reward_cube(base: np.ndarray, combos: np.ndarray, alpha: float) -> np.ndarray:
    """Return reward[combo, agent, action] under one directed RL violation."""
    combo_count, n = combos.shape
    action_count = base.shape[2]
    rewards = np.empty((combo_count, n, action_count), dtype=float)
    action_axis = np.arange(action_count)
    for combo_index, combo in enumerate(combos):
        local = base[np.arange(n)[:, None], combo[:, None], action_axis[None, :]]
        rewards[combo_index] = local
        rewards[combo_index, 0] = (
            local[0] - float(alpha) * local[1] + float(alpha)
        ) / (1.0 + float(alpha))
    return rewards


def sample_categorical(probabilities: np.ndarray, uniform: float) -> int:
    probs = np.asarray(probabilities, dtype=float)
    probs = probs / probs.sum()
    return int(np.searchsorted(np.cumsum(probs), min(float(uniform), np.nextafter(1.0, 0.0)), side="right"))


def combo_index_map(combos: np.ndarray) -> dict[tuple[int, ...], int]:
    return {tuple(int(value) for value in combo): index for index, combo in enumerate(combos)}


def product_joint_probabilities(factored: np.ndarray, combos: np.ndarray) -> np.ndarray:
    probabilities = np.ones(len(combos), dtype=float)
    for combo_index, combo in enumerate(combos):
        probabilities[combo_index] = float(
            np.prod(factored[np.arange(factored.shape[0]), combo])
        )
    return probabilities / probabilities.sum()


def plan_for_combo(reward_cube: np.ndarray, combo_index: int) -> int:
    welfare = reward_cube[combo_index].sum(axis=0)
    return int(np.argmax(welfare))


def update_factored(
    posterior: np.ndarray,
    base: np.ndarray,
    action_index: int,
    observed_rewards: np.ndarray,
    alpha: float,
    sigma: float,
) -> None:
    """Projected marginal update under the coupled model.

    Agent 0's candidate likelihood marginalises the unknown comparison-agent
    type under the current marginal.  This is the natural factored projection,
    but it discards the posterior dependence induced by the observed cross term.
    """
    n, type_count = posterior.shape
    old = np.array(posterior, copy=True)
    for agent in range(n):
        if agent == 0:
            comparison_mean = float(old[1] @ base[1, :, action_index])
            expected = (
                base[0, :, action_index] - float(alpha) * comparison_mean + float(alpha)
            ) / (1.0 + float(alpha))
        else:
            expected = base[agent, :, action_index]
        log_like = -0.5 * ((float(observed_rewards[agent]) - expected) / sigma) ** 2
        log_like -= float(np.max(log_like))
        posterior[agent] *= np.exp(log_like) + 1e-12
        total = float(posterior[agent].sum())
        posterior[agent] = posterior[agent] / total if total > 0.0 else np.full(type_count, 1.0 / type_count)


def update_joint(
    posterior: np.ndarray,
    reward_cube: np.ndarray,
    action_index: int,
    observed_rewards: np.ndarray,
    sigma: float,
) -> None:
    residual = reward_cube[:, :, action_index] - observed_rewards[None, :]
    log_like = -0.5 * np.sum((residual / sigma) ** 2, axis=1)
    log_like -= float(np.max(log_like))
    posterior *= np.exp(log_like) + 1e-15
    total = float(posterior.sum())
    posterior[:] = posterior / total if total > 0.0 else 1.0 / len(posterior)


def marginal_true_mass(posterior: np.ndarray, true_types: np.ndarray) -> float:
    return float(np.mean(posterior[np.arange(len(true_types)), true_types]))


def joint_true_mass(posterior: np.ndarray, true_combo_index: int) -> float:
    return float(posterior[true_combo_index])


def joint_marginals(joint: np.ndarray, combos: np.ndarray, n: int, type_count: int) -> np.ndarray:
    marginals = np.zeros((n, type_count), dtype=float)
    for combo_index, combo in enumerate(combos):
        for agent, type_index in enumerate(combo):
            marginals[agent, int(type_index)] += float(joint[combo_index])
    return marginals


def run_seed(
    *,
    model: str,
    base: np.ndarray,
    action_profiles: np.ndarray,
    alpha: float,
    seed: int,
    episodes: int,
    sigma: float,
) -> list[dict[str, object]]:
    del action_profiles  # retained in the interface/provenance; planning uses its index order.
    n, type_count, _ = base.shape
    combos = joint_type_profiles(n, type_count)
    combo_lookup = combo_index_map(combos)
    reward_cube = coupled_reward_cube(base, combos, alpha)
    if math.isclose(alpha, 0.0):
        for combo_index, combo in enumerate(combos):
            expected = base[np.arange(n), combo]
            if not np.allclose(reward_cube[combo_index], expected, atol=1e-12, rtol=0.0):
                raise AssertionError("alpha=0 did not recover the reward-local model")

    design_rng = np.random.default_rng(seed + 71_000)
    true_types = design_rng.integers(0, type_count, size=n)
    true_combo = combo_lookup[tuple(int(value) for value in true_types)]
    joint_uniforms = design_rng.random(episodes)
    notype_uniforms = design_rng.random(episodes)

    true_welfare = reward_cube[true_combo].sum(axis=0)
    oracle_action = int(np.argmax(true_welfare))
    oracle_welfare = float(true_welfare[oracle_action])
    rows: list[dict[str, object]] = []

    for algorithm in ALGORITHMS:
        factored = np.full((n, type_count), 1.0 / type_count, dtype=float)
        joint = np.full(len(combos), 1.0 / len(combos), dtype=float)
        shadow_joint = np.full(len(combos), 1.0 / len(combos), dtype=float)
        cumulative = 0.0
        for episode in range(episodes):
            if algorithm == "pact_factored":
                sampled_combo = sample_categorical(
                    product_joint_probabilities(factored, combos),
                    joint_uniforms[episode],
                )
            elif algorithm == "joint_psrl_coupled":
                sampled_combo = sample_categorical(joint, joint_uniforms[episode])
            else:
                sampled_combo = min(int(notype_uniforms[episode] * len(combos)), len(combos) - 1)

            chosen = plan_for_combo(reward_cube, sampled_combo)
            observed = reward_cube[true_combo, :, chosen]
            chosen_welfare = float(observed.sum())
            instant = max(0.0, oracle_welfare - chosen_welfare)
            cumulative += instant

            if algorithm == "pact_factored":
                update_factored(factored, base, chosen, observed, alpha, sigma)
                update_joint(shadow_joint, reward_cube, chosen, observed, sigma)
                true_mass = marginal_true_mass(factored, true_types)
                exact_marginals = joint_marginals(shadow_joint, combos, n, type_count)
                posterior_l1 = float(np.mean(0.5 * np.sum(np.abs(factored - exact_marginals), axis=1)))
            elif algorithm == "joint_psrl_coupled":
                update_joint(joint, reward_cube, chosen, observed, sigma)
                true_mass = joint_true_mass(joint, true_combo)
                posterior_l1 = 0.0
            else:
                true_mass = 1.0 / len(combos)
                posterior_l1 = float("nan")

            rows.append(
                {
                    "model": model,
                    "alpha": float(alpha),
                    "seed": int(seed),
                    "algorithm": algorithm,
                    "episode": episode + 1,
                    "instant_regret": instant,
                    "cumulative_regret": cumulative,
                    "chosen_action": chosen,
                    "oracle_action": oracle_action,
                    "chosen_welfare": chosen_welfare,
                    "oracle_welfare": oracle_welfare,
                    "posterior_true_mass": true_mass,
                    "posterior_marginal_tv_vs_joint": posterior_l1,
                    "true_types": "|".join(str(int(value)) for value in true_types),
                }
            )
    return rows


def mean_sem(values: list[float]) -> tuple[float, float]:
    array = np.asarray(values, dtype=float)
    return (
        float(array.mean()),
        float(array.std(ddof=1) / math.sqrt(len(array))) if len(array) > 1 else 0.0,
    )


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def summarise(rows: list[dict[str, object]], episodes: int) -> list[dict[str, object]]:
    groups: dict[tuple[str, float, str], list[dict[str, object]]] = {}
    final_by_seed: dict[tuple[str, float, str, int], float] = {}
    for row in rows:
        if int(row["episode"]) == episodes:
            key = (str(row["model"]), float(row["alpha"]), str(row["algorithm"]))
            groups.setdefault(key, []).append(row)
            final_by_seed[(key[0], key[1], key[2], int(row["seed"]))] = float(row["cumulative_regret"])
    summary: list[dict[str, object]] = []
    for (model, alpha, algorithm), group in sorted(groups.items()):
        regret_mean, regret_sem = mean_sem([float(row["cumulative_regret"]) for row in group])
        mass_mean, mass_sem = mean_sem([float(row["posterior_true_mass"]) for row in group])
        divergence_values = [
            float(row["posterior_marginal_tv_vs_joint"])
            for row in group
            if math.isfinite(float(row["posterior_marginal_tv_vs_joint"]))
        ]
        divergence_mean, divergence_sem = mean_sem(divergence_values) if divergence_values else (float("nan"), float("nan"))
        item = {
            "model": model,
            "alpha": alpha,
            "algorithm": algorithm,
            "seeds": len(group),
            "cumulative_regret_mean": regret_mean,
            "cumulative_regret_sem": regret_sem,
            "posterior_true_mass_mean": mass_mean,
            "posterior_true_mass_sem": mass_sem,
            "posterior_marginal_tv_vs_joint_mean": divergence_mean,
            "posterior_marginal_tv_vs_joint_sem": divergence_sem,
        }
        summary.append(item)
    for item in summary:
        model = str(item["model"])
        alpha = float(item["alpha"])
        algorithm = str(item["algorithm"])
        paired = [
            final_by_seed[(model, alpha, algorithm, seed)]
            - final_by_seed[(model, alpha, "joint_psrl_coupled", seed)]
            for seed in sorted(
                key[3]
                for key in final_by_seed
                if key[0] == model and key[1] == alpha and key[2] == algorithm
            )
        ]
        gap_mean, gap_sem = mean_sem(paired)
        item["regret_gap_vs_joint"] = gap_mean
        item["regret_gap_vs_joint_sem"] = gap_sem
    return summary


def plot_results(rows: list[dict[str, object]], summary: list[dict[str, object]], out_dir: Path) -> None:
    models = list(dict.fromkeys(str(row["model"]) for row in rows))
    fig, axes = plt.subplots(len(models), 2, figsize=(8.2, 3.2 * len(models)), squeeze=False)
    for model_index, model in enumerate(models):
        ax_curve, ax_final = axes[model_index]
        alphas = sorted({float(row["alpha"]) for row in rows if str(row["model"]) == model})
        alpha_max = max(alphas)
        for algorithm in ("pact_factored", "joint_psrl_coupled"):
            curve = []
            sems = []
            for episode in sorted({int(row["episode"]) for row in rows}):
                values = [
                    float(row["cumulative_regret"])
                    for row in rows
                    if str(row["model"]) == model
                    and math.isclose(float(row["alpha"]), alpha_max)
                    and str(row["algorithm"]) == algorithm
                    and int(row["episode"]) == episode
                ]
                mean, sem = mean_sem(values)
                curve.append(mean)
                sems.append(sem)
            x = np.arange(1, len(curve) + 1)
            ax_curve.plot(x, curve, color=COLORS[algorithm], label=LABELS[algorithm], linewidth=1.5)
            ax_curve.fill_between(x, np.asarray(curve) - sems, np.asarray(curve) + sems, color=COLORS[algorithm], alpha=0.14)

        gap_rows = [
            row
            for row in summary
            if str(row["model"]) == model and str(row["algorithm"]) == "pact_factored"
        ]
        gap_rows.sort(key=lambda row: float(row["alpha"]))
        ax_final.errorbar(
            [float(row["alpha"]) for row in gap_rows],
            [float(row["posterior_marginal_tv_vs_joint_mean"]) for row in gap_rows],
            yerr=[float(row["posterior_marginal_tv_vs_joint_sem"]) for row in gap_rows],
            marker="o",
            capsize=2,
            color=COLORS["pact_factored"],
        )
        ax_curve.set_title(f"{model}: trajectory at $\\alpha={alpha_max:g}$", loc="left")
        ax_curve.set_xlabel("Episode")
        ax_curve.set_ylabel("Cumulative regret")
        ax_final.set_title(f"{model}: posterior coupling", loc="left")
        ax_final.set_xlabel("Coupling strength $\\alpha$")
        ax_final.set_ylabel("Factored vs joint marginal TV")
        for ax in (ax_curve, ax_final):
            ax.grid(axis="y", linestyle=":", linewidth=0.6, color="#d7d7d7")
            ax.spines[["top", "right"]].set_visible(False)
        ax_curve.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    for target in (out_dir, ROOT / "figs", ROOT / "arr_paper" / "figs"):
        target.mkdir(parents=True, exist_ok=True)
        fig.savefig(target / "fig_e_d_reward_locality_violation.pdf", bbox_inches="tight", facecolor="white")
        fig.savefig(target / "fig_e_d_reward_locality_violation.png", dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def write_markdown(path: Path, summary: list[dict[str, object]], metadata: dict[str, object]) -> None:
    lines = [
        "# E-D: True Reward-Locality Violation",
        "",
        "This is a controlled HP-SPGG-derived DGP. Only agent 0 has the cross-agent reward "
        "$r_0=(r_0^{\\theta_0}-\\alpha r_1^{\\theta_1}+\\alpha)/(1+\\alpha)$; the other rewards remain local. "
        "The affine normalization keeps rewards in $[0,1]$, and the asymmetric edge prevents cancellation in total welfare.",
        "",
        f"Episodes: {metadata['episodes']}; seeds: {metadata['seeds']}; Gaussian sigma: {metadata['sigma']}.",
        "",
        "| calibration | alpha | method | cumulative regret | gap vs joint | true-type mass | marginal TV |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(
            f"| {row['model']} | {float(row['alpha']):.2f} | {LABELS[str(row['algorithm'])]} | "
            f"{float(row['cumulative_regret_mean']):.3f} $\\pm$ {float(row['cumulative_regret_sem']):.3f} | "
            f"{float(row['regret_gap_vs_joint']):+.3f} $\\pm$ {float(row['regret_gap_vs_joint_sem']):.3f} | "
            f"{float(row['posterior_true_mass_mean']):.3f} | "
            f"{float(row['posterior_marginal_tv_vs_joint_mean']):.3f} |"
        )
    lines.extend(
        [
            "",
            "HARP uses the correct coupled reward for planning but projects the likelihood to independent marginals; "
            "Joint-PSRL-Coupled uses the full joint likelihood. No CCE program is solved: all 27 actions in the "
            "Cartesian subgrid $\\{0,0.5,1\\}^3$ are enumerated exactly.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--alphas", default="0,0.25,0.5,1")
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--seed-offset", type=int, default=40_000)
    parser.add_argument("--sigma", type=float, default=0.08)
    parser.add_argument("--action-values", default=None, help="Optional comma-separated Cartesian action subgrid, e.g. 0,0.5,1.")
    parser.add_argument("--calibration", action="append", default=[], help="Optional LABEL=PATH; repeat for multiple tensors.")
    parser.add_argument("--include-analytic", action="store_true", help="Include the analytic mixed calibration alongside supplied live tensors.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    alphas = parse_float_grid(args.alphas)
    action_grid = parse_action_grid(args.action_values)
    specs = parse_calibrations(args.calibration)
    if args.include_analytic and args.calibration:
        specs.insert(0, CalibrationSpec("analytic-mixed", None))
    all_rows: list[dict[str, object]] = []
    provenance: dict[str, object] = {}
    for spec in specs:
        base, profiles, source = load_bundle(spec, action_grid)
        provenance[spec.label] = source
        for alpha in alphas:
            for seed_index in range(args.seeds):
                all_rows.extend(
                    run_seed(
                        model=spec.label,
                        base=base,
                        action_profiles=profiles,
                        alpha=alpha,
                        seed=args.seed_offset + seed_index,
                        episodes=args.episodes,
                        sigma=args.sigma,
                    )
                )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = args.out_dir / "e_d_reward_locality_violation_per_seed.csv"
    summary_path = args.out_dir / "e_d_reward_locality_violation_summary.csv"
    write_csv(raw_path, all_rows)
    summary = summarise(all_rows, args.episodes)
    write_csv(summary_path, summary)
    metadata = {
        "experiment": "E-D true reward-locality violation",
        "episodes": args.episodes,
        "seeds": args.seeds,
        "seed_offset": args.seed_offset,
        "alphas": alphas,
        "sigma": args.sigma,
        "action_values": action_grid,
        "beta": None,
        "coupling": "(agent0_local_reward - alpha * agent1_local_reward + alpha) / (1 + alpha)",
        "reward_range_preserved": True,
        "planner": "exact exhaustive joint-action argmax",
        "provenance": provenance,
    }
    (args.out_dir / "e_d_reward_locality_violation_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    plot_results(all_rows, summary, args.out_dir)
    write_markdown(args.out_dir / "e_d_reward_locality_violation.md", summary, metadata)
    print(f"raw={raw_path}")
    print(f"summary={summary_path}")
    for row in summary:
        print(
            f"{row['model']} alpha={float(row['alpha']):.2f} {row['algorithm']}: "
            f"regret={float(row['cumulative_regret_mean']):.4f}+-{float(row['cumulative_regret_sem']):.4f} "
            f"gap={float(row['regret_gap_vs_joint']):+.4f}"
        )


if __name__ == "__main__":
    main()
