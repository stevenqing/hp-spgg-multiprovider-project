"""Run E-B: an iterated, fixed-persona Concordia-derived compact benchmark.

This is not the native one-shot Concordia protocol.  It reuses the upstream
config samplers, exact payoff functions, and finite action menus, then places a
four-template local persona utility layer over those payoffs.  A persona profile
is sampled once per report seed and held fixed for K episodes.  All methods in a
cell share the case, types, initial posterior, and pre-generated random streams.

Config selection first used the retained one-shot margins, then screened
persona decision value on seeds 0..4.  The held-out report uses case/type
seeds 1000..1004 by default.  Because this exact
payoff replay makes no LLM calls, it is backbone-invariant; the output does not
replicate identical rows under four model names.
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
from typing import Any, Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_hpgg.personas import PERSONAS
from llm_hpgg_concordia import run_haggling_compact as hag
from llm_hpgg_concordia import run_pub_coordination_compact as pub


DEFAULT_OUT_DIR = ROOT / "analysis" / "e_b_iterated_concordia"
METHODS = (
    "pact",
    "pact_plus",
    "joint_psrl_uniform",
    "psrl_notype",
    "map_type_greedy",
    "econ_bne",
    "atom_tom1",
    "random",
)
LABELS = {
    "pact": "HARP",
    "pact_plus": "HARP+",
    "joint_psrl_uniform": "Joint-PSRL",
    "psrl_notype": "PSRL-NoType",
    "map_type_greedy": "MAP-Type-Greedy",
    "econ_bne": "ECON-BNE",
    "atom_tom1": "A-ToM-1",
    "random": "Random",
}
COLORS = {
    "pact": "#557a95",
    "pact_plus": "#12345d",
    "joint_psrl_uniform": "#2f7d5b",
    "psrl_notype": "#9a5a2e",
    "map_type_greedy": "#6f8f68",
    "econ_bne": "#b64b45",
    "atom_tom1": "#d4a04a",
    "random": "#999999",
}

# Selected by persona decision value on seeds 0..4 after the retained one-shot
# margin screen; report seeds are disjoint.
CONFIG_SPECS = (
    ("pub", "london", "Pub: london"),
    ("pub", "london_mini", "Pub: london_mini"),
    ("haggling", "fruitville", "Haggling: fruitville"),
    ("haggling", "vegbrooke", "Haggling: vegbrooke"),
    ("haggling_multi_item", "vegbrooke", "Multi-item: vegbrooke"),
    ("haggling_multi_item", "fruitville_multi", "Multi-item: fruitville"),
)
SELECTION_DECISION_VALUE = {
    "haggling/fruitville": 0.05890,
    "haggling_multi_item/vegbrooke": 0.05300,
    "haggling_multi_item/fruitville_multi": 0.05266,
    "haggling/vegbrooke": 0.04937,
    "pub/london": 0.00845,
    "pub/london_mini": 0.00736,
}


@dataclass
class IteratedModel:
    config_id: str
    label: str
    domain: str
    reward_tensor: np.ndarray  # (n, type_count, action_count), normalized to [0,1]
    action_labels: list[str]
    objective_weights: np.ndarray  # (n,)
    baseline_actions: dict[str, int]
    provenance: dict[str, Any]

    @property
    def n(self) -> int:
        return int(self.reward_tensor.shape[0])

    @property
    def type_count(self) -> int:
        return int(self.reward_tensor.shape[1])

    @property
    def action_count(self) -> int:
        return int(self.reward_tensor.shape[2])


PERSONA_KEYS = [persona.key for persona in PERSONAS]


def one_hot_persona(key: str) -> dict[str, float]:
    return {candidate: (1.0 if candidate == key else 0.0) for candidate in PERSONA_KEYS}


def normalize_reward_tensor(raw: np.ndarray) -> np.ndarray:
    result = np.empty_like(raw, dtype=float)
    for player in range(raw.shape[0]):
        low = float(np.min(raw[player]))
        high = float(np.max(raw[player]))
        if high - low <= 1e-12:
            result[player] = 0.5
        else:
            result[player] = (raw[player] - low) / (high - low)
    return np.clip(result, 0.0, 1.0)


def action_key(action: dict[str, str]) -> str:
    return json.dumps(action, sort_keys=True, separators=(",", ":"))


def build_pub_model(config_name: str, label: str, case_seed: int) -> IteratedModel:
    pub.ensure_concordia_examples_on_path()
    config = pub.load_config(config_name)
    case = pub.build_case(config, case_seed)
    players = list(case["focal_players"])
    background = [name for name in case["people"] if name not in players]
    open_venues = [venue for venue in case["venues"] if venue not in case["closed_venues"]] or list(case["venues"])
    fixed_background = {
        name: (case["person_preferences"][name] if case["person_preferences"][name] in open_venues else open_venues[0])
        for name in background
    }
    assignments = list(product(open_venues, repeat=len(players)))
    action_dicts: list[dict[str, str]] = []
    for assignment in assignments:
        joint = dict(fixed_background)
        joint.update(dict(zip(players, assignment, strict=True)))
        action_dicts.append(joint)

    payoff = pub.payoff_for_case(case)
    raw = np.zeros((len(players), len(PERSONAS), len(action_dicts)), dtype=float)
    for action_index, joint in enumerate(action_dicts):
        base_scores = dict(payoff.action_to_scores(joint))
        for player_index, player in enumerate(players):
            own_base = float(base_scores.get(player, 0.0))
            venue = joint[player]
            for persona_index, persona in enumerate(PERSONAS):
                persona_fit = pub.persona_weighted_venue_score(case, player, venue, one_hot_persona(persona.key))
                raw[player_index, persona_index, action_index] = 0.70 * own_base + 0.30 * persona_fit
    tensor = normalize_reward_tensor(raw)
    label_to_index = {action_key(action): index for index, action in enumerate(action_dicts)}
    econ_action, _ = pub.choose_econ_bne_mech(case)
    atom_action, _ = pub.choose_atom_tom1_mech(case)

    def project_to_focal_menu(action: dict[str, str]) -> dict[str, str]:
        projected = dict(fixed_background)
        for player in players:
            venue = action.get(player, open_venues[0])
            projected[player] = venue if venue in open_venues else open_venues[0]
        return projected

    baseline_actions = {
        "econ_bne": label_to_index[action_key(project_to_focal_menu(econ_action))],
        "atom_tom1": label_to_index[action_key(project_to_focal_menu(atom_action))],
    }
    return IteratedModel(
        config_id=f"pub/{config_name}",
        label=label,
        domain="pub",
        reward_tensor=tensor,
        action_labels=[action_key(action) for action in action_dicts],
        objective_weights=np.ones(len(players), dtype=float),
        baseline_actions=baseline_actions,
        provenance={
            "case_seed": case_seed,
            "upstream_config": config.__name__,
            "focal_players": players,
            "fixed_background_actions": fixed_background,
            "persona_layer": "0.70 * exact PubCoordinationPayoff + 0.30 * one-hot persona venue score",
            "normalization": "per-player affine to [0,1] across all types/actions",
        },
    )


def persona_haggling_utility(persona_key: str, own: float, other: float) -> float:
    if persona_key == "altruistic_builder":
        return 0.65 * own + 0.35 * other
    if persona_key == "conditional_cooperator":
        return 0.75 * own + 0.25 * min(own, other)
    if persona_key == "risk_averse_balancer":
        return 0.70 * own + 0.30 * min(own, other) - 0.10 * abs(own - other)
    return own


def enumerate_haggling_actions(case: dict[str, Any], deal: dict[str, Any]) -> list[dict[str, str]]:
    if case["domain"] == "haggling":
        prices = [hag.price_value(option) for option in case["price_options"]]
        return [hag.make_single_action(deal, price, accept) for price in prices for accept in (False, True)]
    return [
        hag.make_multi_action(deal, item, float(price), accept)
        for item in case["items"]
        for price in case["prices"]
        for accept in (False, True)
    ]


def select_representative_deal(case: dict[str, Any]) -> dict[str, Any]:
    focal = set(case["focal_players"])
    for deal in case["deals"]:
        if (deal["buyer"] in focal) ^ (deal["seller"] in focal):
            return deal
    return case["deals"][0]


def build_haggling_model(domain: str, config_name: str, label: str, case_seed: int) -> IteratedModel:
    hag.ensure_concordia_examples_on_path()
    config = hag.load_config(domain, config_name)
    case = hag.build_case(domain, config, case_seed)
    deal = select_representative_deal(case)
    players = [deal["buyer"], deal["seller"]]
    actions = enumerate_haggling_actions(case, deal)
    raw = np.zeros((2, len(PERSONAS), len(actions)), dtype=float)
    for action_index, action in enumerate(actions):
        scores = hag.score_deal(case, deal, action)
        buyer_score = float(scores.get(players[0], 0.0))
        seller_score = float(scores.get(players[1], 0.0))
        for persona_index, persona in enumerate(PERSONAS):
            raw[0, persona_index, action_index] = persona_haggling_utility(persona.key, buyer_score, seller_score)
            raw[1, persona_index, action_index] = persona_haggling_utility(persona.key, seller_score, buyer_score)
    tensor = normalize_reward_tensor(raw)
    label_to_index = {action_key(action): index for index, action in enumerate(actions)}
    econ_action, _ = hag.choose_action(case, deal, "econ_bne_mech")
    atom_action, _ = hag.choose_action(case, deal, "atom_tom1_mech")
    focal = set(case["focal_players"])
    weights = np.asarray([1.0 if player in focal else 0.0 for player in players], dtype=float)
    if float(weights.sum()) <= 0.0:
        weights[:] = 1.0
    return IteratedModel(
        config_id=f"{domain}/{config_name}",
        label=label,
        domain=domain,
        reward_tensor=tensor,
        action_labels=[action_key(action) for action in actions],
        objective_weights=weights,
        baseline_actions={
            "econ_bne": label_to_index[action_key(econ_action)],
            "atom_tom1": label_to_index[action_key(atom_action)],
        },
        provenance={
            "case_seed": case_seed,
            "upstream_config": config.__name__,
            "deal": deal,
            "players": players,
            "focal_players": list(case["focal_players"]),
            "persona_layer": "persona-specific own/partner utility transform over exact HagglingPayoff",
            "normalization": "per-player affine to [0,1] across all types/actions",
        },
    )


def build_model(domain: str, config_name: str, label: str, case_seed: int) -> IteratedModel:
    if domain == "pub":
        return build_pub_model(config_name, label, case_seed)
    return build_haggling_model(domain, config_name, label, case_seed)


def combos_for(model: IteratedModel) -> np.ndarray:
    return np.asarray(list(product(range(model.type_count), repeat=model.n)), dtype=int)


def combo_lookup(combos: np.ndarray) -> dict[tuple[int, ...], int]:
    return {tuple(int(value) for value in combo): index for index, combo in enumerate(combos)}


def sample_categorical(probabilities: np.ndarray, uniform: float) -> int:
    probs = np.asarray(probabilities, dtype=float)
    probs = probs / probs.sum()
    return int(np.searchsorted(np.cumsum(probs), min(float(uniform), np.nextafter(1.0, 0.0)), side="right"))


def objective_scores(model: IteratedModel, type_profile: np.ndarray) -> np.ndarray:
    rewards = model.reward_tensor[np.arange(model.n)[:, None], type_profile[:, None], np.arange(model.action_count)[None, :]]
    return model.objective_weights @ rewards


def plan_for_types(model: IteratedModel, type_profile: np.ndarray) -> int:
    return int(np.argmax(objective_scores(model, type_profile)))


def discrimination_bonus(model: IteratedModel, posterior: np.ndarray) -> np.ndarray:
    bonus = np.zeros(model.action_count, dtype=float)
    for player in range(model.n):
        pairwise = np.abs(
            model.reward_tensor[player, :, None, :] - model.reward_tensor[player, None, :, :]
        )
        expected = np.einsum("i,j,ija->a", posterior[player], posterior[player], pairwise)
        bonus += model.objective_weights[player] * expected
    return bonus


def update_factored(posterior: np.ndarray, model: IteratedModel, action: int, observed: np.ndarray, sigma: float) -> None:
    for player in range(model.n):
        expected = model.reward_tensor[player, :, action]
        log_like = -0.5 * ((float(observed[player]) - expected) / sigma) ** 2
        log_like -= float(np.max(log_like))
        posterior[player] *= np.exp(log_like) + 1e-12
        total = float(posterior[player].sum())
        posterior[player] = posterior[player] / total if total > 0.0 else 1.0 / model.type_count


def update_joint(joint: np.ndarray, combos: np.ndarray, model: IteratedModel, action: int, observed: np.ndarray, sigma: float) -> None:
    expected = model.reward_tensor[np.arange(model.n)[None, :], combos, action]
    residual = expected - observed[None, :]
    log_like = -0.5 * np.sum((residual / sigma) ** 2, axis=1)
    log_like -= float(np.max(log_like))
    joint *= np.exp(log_like) + 1e-15
    total = float(joint.sum())
    joint[:] = joint / total if total > 0.0 else 1.0 / len(joint)


def run_cell(model: IteratedModel, seed: int, episodes: int, sigma: float, beta: float) -> list[dict[str, object]]:
    combos = combos_for(model)
    lookup = combo_lookup(combos)
    rng = np.random.default_rng(seed + 93_000)
    true_types = rng.integers(0, model.type_count, size=model.n)
    true_combo = lookup[tuple(int(value) for value in true_types)]
    marginal_uniforms = rng.random((episodes, model.n))
    joint_uniforms = rng.random(episodes)
    notype_uniforms = rng.random((episodes, model.n))
    random_uniforms = rng.random(episodes)

    true_objective = objective_scores(model, true_types)
    oracle_action = int(np.argmax(true_objective))
    oracle_value = float(true_objective[oracle_action])
    true_rewards_by_action = model.reward_tensor[np.arange(model.n)[:, None], true_types[:, None], np.arange(model.action_count)[None, :]]
    rows: list[dict[str, object]] = []

    for method in METHODS:
        posterior = np.full((model.n, model.type_count), 1.0 / model.type_count, dtype=float)
        joint = np.full(len(combos), 1.0 / len(combos), dtype=float)
        cumulative = 0.0
        for episode in range(episodes):
            if method in {"pact", "pact_plus"}:
                sampled = np.asarray(
                    [sample_categorical(posterior[player], marginal_uniforms[episode, player]) for player in range(model.n)],
                    dtype=int,
                )
                scores = objective_scores(model, sampled)
                if method == "pact_plus":
                    scores = scores + beta * discrimination_bonus(model, posterior)
                chosen = int(np.argmax(scores))
            elif method == "joint_psrl_uniform":
                sampled_combo = sample_categorical(joint, joint_uniforms[episode])
                chosen = plan_for_types(model, combos[sampled_combo])
            elif method == "psrl_notype":
                sampled = np.asarray(
                    [min(int(notype_uniforms[episode, player] * model.type_count), model.type_count - 1) for player in range(model.n)],
                    dtype=int,
                )
                chosen = plan_for_types(model, sampled)
            elif method == "map_type_greedy":
                chosen = plan_for_types(model, np.argmax(posterior, axis=1))
            elif method in {"econ_bne", "atom_tom1"}:
                chosen = int(model.baseline_actions[method])
            else:
                chosen = min(int(random_uniforms[episode] * model.action_count), model.action_count - 1)

            observed = true_rewards_by_action[:, chosen]
            value = float(model.objective_weights @ observed)
            instant = max(0.0, oracle_value - value)
            cumulative += instant
            if method in {"pact", "pact_plus", "map_type_greedy"}:
                update_factored(posterior, model, chosen, observed, sigma)
                type_mass = float(np.mean(posterior[np.arange(model.n), true_types]))
            elif method == "joint_psrl_uniform":
                update_joint(joint, combos, model, chosen, observed, sigma)
                type_mass = float(joint[true_combo])
            else:
                type_mass = 1.0 / (model.type_count**model.n)

            rows.append(
                {
                    "config_id": model.config_id,
                    "config_label": model.label,
                    "domain": model.domain,
                    "backbone": "exact-payoff (backbone-invariant)",
                    "seed": seed,
                    "method": method,
                    "episode": episode + 1,
                    "instant_regret": instant,
                    "cumulative_regret": cumulative,
                    "chosen_action": chosen,
                    "oracle_action": oracle_action,
                    "objective_value": value,
                    "oracle_value": oracle_value,
                    "posterior_true_mass": type_mass,
                    "true_types": "|".join(str(int(value)) for value in true_types),
                    "n_agents": model.n,
                    "type_count": model.type_count,
                    "factored_storage": model.n * model.type_count,
                    "joint_storage": model.type_count**model.n,
                }
            )
    return rows


def mean_sem(values: list[float]) -> tuple[float, float]:
    array = np.asarray(values, dtype=float)
    return float(array.mean()), float(array.std(ddof=1) / math.sqrt(len(array))) if len(array) > 1 else 0.0


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def summarise(rows: list[dict[str, object]], episodes: int) -> list[dict[str, object]]:
    groups: dict[tuple[str, str], list[dict[str, object]]] = {}
    for row in rows:
        if int(row["episode"]) == episodes:
            groups.setdefault((str(row["config_id"]), str(row["method"])), []).append(row)
    summary: list[dict[str, object]] = []
    for (config_id, method), group in sorted(groups.items()):
        regret_mean, regret_sem = mean_sem([float(row["cumulative_regret"]) for row in group])
        mass_mean, mass_sem = mean_sem([float(row["posterior_true_mass"]) for row in group])
        late_slope_mean, late_slope_sem = mean_sem(
            [
                sum(
                    float(row["instant_regret"])
                    for row in rows
                    if str(row["config_id"]) == config_id
                    and str(row["method"]) == method
                    and int(row["seed"]) == int(final["seed"])
                    and int(row["episode"]) > episodes // 2
                )
                / max(1, episodes - episodes // 2)
                for final in group
            ]
        )
        summary.append(
            {
                "config_id": config_id,
                "config_label": group[0]["config_label"],
                "domain": group[0]["domain"],
                "method": method,
                "seeds": len(group),
                "episodes": episodes,
                "cumulative_regret_mean": regret_mean,
                "cumulative_regret_sem": regret_sem,
                "late_instant_regret_mean": late_slope_mean,
                "late_instant_regret_sem": late_slope_sem,
                "posterior_true_mass_mean": mass_mean,
                "posterior_true_mass_sem": mass_sem,
                "n_agents": group[0]["n_agents"],
                "factored_storage": group[0]["factored_storage"],
                "joint_storage": group[0]["joint_storage"],
            }
        )
    return summary


def aggregate_trajectory(rows: list[dict[str, object]], method: str, episode: int) -> tuple[float, float]:
    per_seed_config: dict[tuple[int, str], float] = {}
    for row in rows:
        if str(row["method"]) == method and int(row["episode"]) == episode:
            per_seed_config[(int(row["seed"]), str(row["config_id"]))] = float(row["cumulative_regret"])
    by_seed: dict[int, list[float]] = {}
    for (seed, _), value in per_seed_config.items():
        by_seed.setdefault(seed, []).append(value)
    values = [float(np.mean(config_values)) for config_values in by_seed.values()]
    return mean_sem(values)


def aggregate_methods(rows: list[dict[str, object]], episodes: int) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for scope, include in (
        ("all_selected", lambda config_id: True),
        ("informative_haggling", lambda config_id: not config_id.startswith("pub/")),
    ):
        finals: dict[tuple[int, str], list[float]] = {}
        late: dict[tuple[int, str], list[float]] = {}
        for row in rows:
            config_id = str(row["config_id"])
            if not include(config_id):
                continue
            key = (int(row["seed"]), str(row["method"]))
            if int(row["episode"]) == episodes:
                finals.setdefault(key, []).append(float(row["cumulative_regret"]))
            if int(row["episode"]) > episodes // 2:
                late.setdefault(key, []).append(float(row["instant_regret"]))
        per_method: dict[str, list[float]] = {}
        for method in METHODS:
            seeds = sorted(seed for seed, candidate in finals if candidate == method)
            final_values = [float(np.mean(finals[(seed, method)])) for seed in seeds]
            late_values = [float(np.mean(late[(seed, method)])) for seed in seeds]
            regret_mean, regret_sem = mean_sem(final_values)
            late_mean, late_sem = mean_sem(late_values)
            per_method[method] = final_values
            output.append(
                {
                    "scope": scope,
                    "method": method,
                    "seeds": len(seeds),
                    "cumulative_regret_mean": regret_mean,
                    "cumulative_regret_sem": regret_sem,
                    "late_instant_regret_mean": late_mean,
                    "late_instant_regret_sem": late_sem,
                    "paired_gap_vs_pact_plus_mean": "",
                    "paired_gap_vs_pact_plus_sem": "",
                }
            )
        pact_plus = np.asarray(per_method["pact_plus"], dtype=float)
        for item in output:
            if item["scope"] != scope:
                continue
            method_values = np.asarray(per_method[str(item["method"])], dtype=float)
            gap_mean, gap_sem = mean_sem((method_values - pact_plus).tolist())
            item["paired_gap_vs_pact_plus_mean"] = gap_mean
            item["paired_gap_vs_pact_plus_sem"] = gap_sem
    return output


def plot_results(rows: list[dict[str, object]], episodes: int, out_dir: Path) -> None:
    focus_methods = ("pact", "pact_plus", "joint_psrl_uniform", "psrl_notype", "econ_bne")
    fig, ax = plt.subplots(figsize=(6.6, 3.8))
    x = np.arange(1, episodes + 1)
    for method in focus_methods:
        means = []
        sems = []
        for episode in x:
            mean, sem = aggregate_trajectory(rows, method, int(episode))
            means.append(mean)
            sems.append(sem)
        ax.plot(x, means, label=LABELS[method], color=COLORS[method], linewidth=1.5)
        ax.fill_between(x, np.asarray(means) - sems, np.asarray(means) + sems, color=COLORS[method], alpha=0.14)
    ax.set_xlabel("Episode")
    ax.set_ylabel("Mean cumulative regret across configs")
    ax.set_title("Iterated Concordia-derived exact-payoff replay", loc="left")
    ax.grid(axis="y", linestyle=":", linewidth=0.6, color="#d7d7d7")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, ncol=2, fontsize=8)
    fig.tight_layout()
    for target in (out_dir, ROOT / "figs", ROOT / "arr_paper" / "figs"):
        target.mkdir(parents=True, exist_ok=True)
        fig.savefig(target / "fig_e_b_iterated_concordia.pdf", bbox_inches="tight", facecolor="white")
        fig.savefig(target / "fig_e_b_iterated_concordia.png", dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def write_markdown(
    path: Path,
    summary: list[dict[str, object]],
    aggregate: list[dict[str, object]],
    metadata: dict[str, Any],
) -> None:
    lines = [
        "# E-B: Iterated Concordia-Derived Compact Benchmark",
        "",
        "This is a constructed iterated variant, not Concordia's native one-shot protocol. "
        "Types are fixed for K episodes and PF is imposed. Exact upstream payoff functions and finite action menus are reused.",
        "",
        "The replay is backbone-invariant because no LLM is called; duplicating the same exact-payoff rows under four model names would not constitute independent evidence.",
        "",
        "| config | method | cumulative regret | late instant regret | true-type mass | storage |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(
            f"| {row['config_label']} | {LABELS[str(row['method'])]} | "
            f"{float(row['cumulative_regret_mean']):.3f} $\\pm$ {float(row['cumulative_regret_sem']):.3f} | "
            f"{float(row['late_instant_regret_mean']):.4f} | {float(row['posterior_true_mass_mean']):.3f} | "
            f"{row['factored_storage']} / {row['joint_storage']} |"
        )
    lines.extend(
        [
            "",
            "## Aggregate across selected configs",
            "",
            "| scope | method | cumulative regret | late instant regret | paired gap vs HARP+ |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for row in aggregate:
        if str(row["method"]) not in {"pact", "pact_plus", "joint_psrl_uniform", "psrl_notype"}:
            continue
        lines.append(
            f"| {row['scope']} | {LABELS[str(row['method'])]} | "
            f"{float(row['cumulative_regret_mean']):.3f} $\\pm$ {float(row['cumulative_regret_sem']):.3f} | "
            f"{float(row['late_instant_regret_mean']):.4f} $\\pm$ {float(row['late_instant_regret_sem']):.4f} | "
            f"{float(row['paired_gap_vs_pact_plus_mean']):+.3f} $\\pm$ {float(row['paired_gap_vs_pact_plus_sem']):.3f} |"
        )
    lines.extend(
        [
            "",
            f"Persona-value selection seeds: {metadata['selection_seeds']}; held-out report seeds: {metadata['report_seed_range']}.",
            "Gaussian likelihood sigma is 0.08 after per-player normalization to [0,1]. All planning is exact enumeration, not a CCE LP.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--seed-offset", type=int, default=1000)
    parser.add_argument("--sigma", type=float, default=0.08)
    parser.add_argument("--beta", type=float, default=0.25)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--limit-configs", type=int, default=0, help="Smoke-only; 0 runs all selected configs.")
    args = parser.parse_args()
    report_seeds = set(range(args.seed_offset, args.seed_offset + args.seeds))
    if report_seeds.intersection(range(5)):
        raise ValueError("E-B report seeds must be disjoint from selection seeds 0..4")

    specs = list(CONFIG_SPECS)
    if args.limit_configs:
        specs = specs[: args.limit_configs]
    all_rows: list[dict[str, object]] = []
    provenance: list[dict[str, Any]] = []
    for seed_index in range(args.seeds):
        report_seed = args.seed_offset + seed_index
        for domain, config_name, label in specs:
            model = build_model(domain, config_name, label, report_seed)
            provenance.append({"seed": report_seed, "config_id": model.config_id, **model.provenance})
            all_rows.extend(run_cell(model, report_seed, args.episodes, args.sigma, args.beta))

    args.out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = args.out_dir / "e_b_iterated_concordia_per_seed.csv"
    summary_path = args.out_dir / "e_b_iterated_concordia_summary.csv"
    write_csv(raw_path, all_rows)
    summary = summarise(all_rows, args.episodes)
    write_csv(summary_path, summary)
    aggregate = aggregate_methods(all_rows, args.episodes)
    write_csv(args.out_dir / "e_b_iterated_concordia_aggregate.csv", aggregate)
    metadata = {
        "experiment": "E-B iterated Concordia-derived compact benchmark",
        "native_protocol": False,
        "backbone_invariant": True,
        "selection_source": "retained one-shot margin screen followed by persona decision-value scan",
        "selection_seeds": "0..4",
        "selection_mean_persona_decision_value": SELECTION_DECISION_VALUE,
        "report_seed_range": f"{args.seed_offset}..{args.seed_offset + args.seeds - 1}",
        "episodes": args.episodes,
        "seeds": args.seeds,
        "sigma": args.sigma,
        "beta": args.beta,
        "configs": [f"{domain}/{config}" for domain, config, _ in specs],
        "planner": "exact exhaustive finite-action argmax",
        "pf": "imposed independent four-type marginals",
        "provenance": provenance,
    }
    (args.out_dir / "e_b_iterated_concordia_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    if (
        len(specs) == len(CONFIG_SPECS)
        and args.episodes == 20
        and args.seeds == 5
        and args.seed_offset == 1000
        and args.out_dir.resolve() == DEFAULT_OUT_DIR.resolve()
    ):
        from plot_e_b_iterated_concordia_v2 import main as plot_v2
        from summarize_e_b_iterated_concordia_v2_all_data import main as summarize_v2_all_data

        plot_v2()
        summarize_v2_all_data()
    else:
        plot_results(all_rows, args.episodes, args.out_dir)
    write_markdown(args.out_dir / "e_b_iterated_concordia.md", summary, aggregate, metadata)
    print(f"raw={raw_path}")
    print(f"summary={summary_path}")
    for row in summary:
        if str(row["method"]) in {"pact", "pact_plus", "joint_psrl_uniform", "psrl_notype"}:
            print(
                f"{row['config_id']} {row['method']}: regret={float(row['cumulative_regret_mean']):.4f}"
                f"+-{float(row['cumulative_regret_sem']):.4f} late={float(row['late_instant_regret_mean']):.4f}"
            )


if __name__ == "__main__":
    main()
