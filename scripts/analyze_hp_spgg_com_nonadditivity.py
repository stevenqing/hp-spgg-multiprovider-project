"""Analyze welfare action non-additivity for HP-SPGG-COM live-judge tensors."""

from __future__ import annotations

import csv
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

from llm_hpgg.environment import enumerate_action_profiles, load_calibration


ANALYSIS_DIR = ROOT / "analysis" / "hp_spgg_com"
FIG_DIRS = [ROOT / "figs", ROOT / "arr_paper" / "figs"]


@dataclass(frozen=True)
class JudgeSpec:
    name: str
    short_name: str
    calibration: Path
    cache: Path
    phase_rows: Path
    marker: str


JUDGES = [
    JudgeSpec(
        name="Llama-4-Maverick",
        short_name="Llama",
        calibration=ANALYSIS_DIR / "calibration_llama_4_maverick_n2_live_s10.npy",
        cache=ANALYSIS_DIR / "calibration_llama_4_maverick_n2_live_s10.cache.jsonl",
        phase_rows=ANALYSIS_DIR / "real_hp_spgg_com_llama_4_maverick_livejudge_n2_s10_phase_rows.csv",
        marker="^",
    ),
    JudgeSpec(
        name="Kimi-K2.6",
        short_name="Kimi",
        calibration=ANALYSIS_DIR / "calibration_kimi_k2_6_n2_live_s10.npy",
        cache=ANALYSIS_DIR / "calibration_kimi_k2_6_n2_live_s10.cache.jsonl",
        phase_rows=ANALYSIS_DIR / "real_hp_spgg_com_kimi_k2_6_livejudge_n2_s10_phase_rows.csv",
        marker="D",
    ),
    JudgeSpec(
        name="GPT-5.4-mini",
        short_name="GPT-mini",
        calibration=ANALYSIS_DIR / "calibration_gpt_5_4_mini_n2_live_s10.npy",
        cache=ANALYSIS_DIR / "calibration_gpt_5_4_mini_n2_live_s10.cache.jsonl",
        phase_rows=ANALYSIS_DIR / "real_hp_spgg_com_gpt54mini_livejudge_n2_s10_phase_rows.csv",
        marker="s",
    ),
    JudgeSpec(
        name="DeepSeek-V3.2",
        short_name="DeepSeek",
        calibration=ANALYSIS_DIR / "calibration_deepseek_v3_2_n2_live_s10.npy",
        cache=ANALYSIS_DIR / "calibration_deepseek_v3_2_n2_live_s10.cache.jsonl",
        phase_rows=ANALYSIS_DIR / "real_hp_spgg_com_deepseek_v3_2_livejudge_n2_s10_phase_rows.csv",
        marker="o",
    ),
]


def load_reward_tensor(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    payload = load_calibration(path)
    reward_tensor = np.asarray(payload["reward_tensor"], dtype=float)
    action_profiles = np.asarray(payload["action_profiles"], dtype=float)
    actions = np.asarray(payload["actions"], dtype=float)
    return reward_tensor, action_profiles, actions


def verify_action_profile_order(action_profiles: np.ndarray, actions: np.ndarray) -> None:
    expected = enumerate_action_profiles(action_profiles.shape[1])
    if not np.allclose(action_profiles, expected):
        raise ValueError("Calibration action_profiles ordering does not match environment.enumerate_action_profiles")
    if len(action_profiles) > 1 and not np.allclose(action_profiles[1], [actions[0], actions[1]]):
        raise ValueError(f"Unexpected profile-index mapping at index 1: {action_profiles[1].tolist()}")


def welfare_action_nonadditivity(reward_tensor: np.ndarray, action_profiles: np.ndarray, actions: np.ndarray) -> float:
    n_agents, _, profile_count = reward_tensor.shape
    n_actions = len(actions)
    if profile_count != n_actions**n_agents:
        raise ValueError(f"Profile count {profile_count} does not match {n_actions}^{n_agents}")

    welfare_flat = reward_tensor.mean(axis=1).sum(axis=0)
    grid = np.zeros([n_actions] * n_agents, dtype=float)
    action_to_index = {float(action): idx for idx, action in enumerate(actions)}
    for profile_index, profile in enumerate(action_profiles):
        grid_index = tuple(action_to_index[float(action)] for action in profile)
        grid[grid_index] = welfare_flat[profile_index]

    mean_value = float(grid.mean())
    additive = np.full_like(grid, mean_value)
    for agent in range(n_agents):
        axes = tuple(axis for axis in range(n_agents) if axis != agent)
        main_effect = grid.mean(axis=axes) - mean_value
        shape = [1] * n_agents
        shape[agent] = n_actions
        additive += main_effect.reshape(shape)

    residual = grid - additive
    return float(np.sqrt(np.mean(residual**2)) / (float(grid.std()) + 1e-12))


def latest_cache_entries(path: Path) -> dict[str, dict[str, object]]:
    entries: dict[str, dict[str, object]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        entries[str(entry["key"])] = entry
    return entries


def residual_judge_variance(path: Path, samples: int = 10) -> tuple[float, dict[str, object]]:
    entries = latest_cache_entries(path)
    per_cell_variance = []
    score_lengths: dict[int, int] = {}
    for key, entry in entries.items():
        scores = [float(score) for score in entry.get("scores", [])][-samples:]
        score_lengths[len(scores)] = score_lengths.get(len(scores), 0) + 1
        if len(scores) != samples:
            raise ValueError(f"{path}: cache key {key} has {len(scores)} scores, expected {samples}")
        per_cell_variance.append(float(np.var(scores, ddof=1)))
    return float(np.mean(per_cell_variance)), {
        "unique_cache_keys": len(entries),
        "score_length_counts": {str(key): value for key, value in sorted(score_lengths.items())},
    }


def pact_local_metrics(path: Path) -> dict[str, float | int]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    subset = [row for row in rows if row["strategy"] == "PACT_LOCAL"]
    if not subset:
        raise ValueError(f"No PACT_LOCAL rows in {path}")
    gaps = [float(row["suboptimality"]) for row in subset]
    messages = [float(row["expected_messages"]) for row in subset]
    return {
        "mean_gap": float(np.mean(gaps)),
        "max_gap": float(np.max(gaps)),
        "mean_messages": float(np.mean(messages)),
        "zero_gap_cells": int(sum(gap <= 1e-12 for gap in gaps)),
        "grid_cells": len(gaps),
    }


def ranks(values: Iterable[float]) -> np.ndarray:
    arr = np.asarray(list(values), dtype=float)
    order = np.argsort(arr, kind="mergesort")
    out = np.zeros(len(arr), dtype=float)
    start = 0
    while start < len(arr):
        end = start + 1
        while end < len(arr) and arr[order[end]] == arr[order[start]]:
            end += 1
        out[order[start:end]] = (start + end - 1) / 2.0 + 1.0
        start = end
    return out


def spearman_rho(x: Iterable[float], y: Iterable[float]) -> float:
    rank_x = ranks(x)
    rank_y = ranks(y)
    if float(rank_x.std()) == 0.0 or float(rank_y.std()) == 0.0:
        return float("nan")
    return float(np.corrcoef(rank_x, rank_y)[0, 1])


def monotone_nonadditivity(rows: list[dict[str, object]]) -> tuple[bool, list[str], list[str], list[str]]:
    by_gap = [str(row["judge"]) for row in sorted(rows, key=lambda row: (float(row["pact_local_mean_gap"]), str(row["judge"])))]
    by_nonadditivity = [
        str(row["judge"]) for row in sorted(rows, key=lambda row: (float(row["welfare_action_nonadditivity"]), str(row["judge"])))
    ]
    by_variance = [str(row["judge"]) for row in sorted(rows, key=lambda row: (float(row["residual_judge_variance"]), str(row["judge"])))]
    return by_gap == by_nonadditivity, by_gap, by_nonadditivity, by_variance


def make_scatter(
    rows: list[dict[str, object]],
    x_key: str,
    output_name: str,
    xlabel: str,
    correlation: float,
) -> None:
    colors = {
        "GPT-5.4-mini": "#c0463f",
        "DeepSeek-V3.2": "#1b3a6f",
        "Kimi-K2.6": "#2c7a5e",
        "Llama-4-Maverick": "#b8723d",
    }
    fig, ax = plt.subplots(figsize=(5.8, 4.2))
    for row in rows:
        judge = str(row["judge"])
        x_value = float(row[x_key])
        y_value = float(row["pact_local_mean_gap"])
        ax.scatter(x_value, y_value, s=78, marker=str(row["marker"]), color=colors[judge], edgecolor="white", linewidth=0.8, zorder=3)
        ax.annotate(
            str(row["short_name"]),
            (x_value, y_value),
            textcoords="offset points",
            xytext=(6, 5),
            fontsize=9,
        )
    ax.set_xlabel(xlabel)
    ax.set_ylabel("PACT-local mean gap")
    ax.set_title(f"Spearman rho = {correlation:.3f}")
    ax.grid(alpha=0.25, linewidth=0.7)
    fig.tight_layout()
    for out_dir in FIG_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_dir / output_name, dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    rows: list[dict[str, object]] = []
    for spec in JUDGES:
        reward_tensor, action_profiles, actions = load_reward_tensor(spec.calibration)
        if reward_tensor.shape != (2, 4, 25):
            raise ValueError(f"{spec.name}: unexpected reward tensor shape {reward_tensor.shape}")
        verify_action_profile_order(action_profiles, actions)
        pact_metrics = pact_local_metrics(spec.phase_rows)
        variance, cache_summary = residual_judge_variance(spec.cache)
        rows.append(
            {
                "judge": spec.name,
                "short_name": spec.short_name,
                "marker": spec.marker,
                "calibration": str(spec.calibration.relative_to(ROOT)),
                "cache": str(spec.cache.relative_to(ROOT)),
                "phase_rows": str(spec.phase_rows.relative_to(ROOT)),
                "pact_local_mean_gap": pact_metrics["mean_gap"],
                "pact_local_max_gap": pact_metrics["max_gap"],
                "pact_local_mean_messages": pact_metrics["mean_messages"],
                "pact_local_zero_gap_cells": pact_metrics["zero_gap_cells"],
                "grid_cells": pact_metrics["grid_cells"],
                "welfare_action_nonadditivity": welfare_action_nonadditivity(reward_tensor, action_profiles, actions),
                "residual_judge_variance": variance,
                "cache_summary": cache_summary,
            }
        )

    nonadditivity_values = [float(row["welfare_action_nonadditivity"]) for row in rows]
    variance_values = [float(row["residual_judge_variance"]) for row in rows]
    gaps = [float(row["pact_local_mean_gap"]) for row in rows]
    rho_nonadditivity = spearman_rho(nonadditivity_values, gaps)
    rho_variance = spearman_rho(variance_values, gaps)
    monotone, gap_order, nonadditivity_order, variance_order = monotone_nonadditivity(rows)
    highest_gap = gap_order[-1]
    highest_variance = variance_order[-1]

    if monotone and rho_nonadditivity >= 0.99:
        decision = {
            "claim": "mechanism",
            "summary": "PACT_LOCAL local-global gap is monotone in welfare action non-additivity across the four s10 tensors.",
        }
    else:
        decision = {
            "claim": "robustness",
            "summary": (
                "Do not claim a monotone mechanism: welfare action non-additivity does not rank-order the four PACT_LOCAL gaps. "
                "Residual judge variance also does not isolate the largest-gap judge as a clear noise outlier."
            ),
        }
    decision.update(
        {
            "gap_order_low_to_high": gap_order,
            "nonadditivity_order_low_to_high": nonadditivity_order,
            "residual_variance_order_low_to_high": variance_order,
            "highest_gap_judge": highest_gap,
            "highest_residual_variance_judge": highest_variance,
            "highest_gap_is_highest_variance": highest_gap == highest_variance,
            "hard_rule_triggered": not monotone,
        }
    )

    payload = {
        "scope_lock": {
            "reward_tensor_shape": "R[i, theta_i, a]",
            "reward_locality_satisfied_by_construction": True,
            "explained_mechanism_candidate": "welfare action non-additivity in joint action",
            "out_of_scope": "Posterior-decoupling / RL violation requires R[i, theta_i, theta_j, a].",
            "persona_prior": "uniform over each agent's four personas, matching make_real_model prior",
            "action_profile_ordering": "llm_hpgg.environment.enumerate_action_profiles = itertools.product(ACTIONS, repeat=n)",
        },
        "rows": rows,
        "correlations": {
            "welfare_action_nonadditivity_vs_pact_local_mean_gap": {"spearman_rho": rho_nonadditivity},
            "residual_judge_variance_vs_pact_local_mean_gap": {"spearman_rho": rho_variance},
        },
        "decision": decision,
    }
    out_path = ANALYSIS_DIR / "nonadditivity_summary.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    make_scatter(
        rows,
        "welfare_action_nonadditivity",
        "fig_nonadditivity_vs_gap.png",
        "Welfare action non-additivity",
        rho_nonadditivity,
    )
    make_scatter(
        rows,
        "residual_judge_variance",
        "fig_judge_variance_vs_gap.png",
        "Residual judge variance",
        rho_variance,
    )
    print(json.dumps({"summary": str(out_path.relative_to(ROOT)), "decision": decision, "correlations": payload["correlations"]}, indent=2))


if __name__ == "__main__":
    main()