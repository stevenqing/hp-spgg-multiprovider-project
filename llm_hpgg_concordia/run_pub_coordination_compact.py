"""Run a compact Concordia Pub Coordination scoring sweep.

This runner reuses Concordia's official Pub Coordination sampling and payoff
code, but skips the long conversation scenes. It is intended for fast validation
tables before scheduling full official Concordia simulations.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path
import sys
from typing import Any

from .cloudgpt_model import HPGGConcordiaLanguageModel
from llm_hpgg.personas import PERSONAS


DEFAULT_METHODS = [
    "llm_greedy",
    "llm_belief",
    "atom_tom1",
    "econ_bne",
    "atom_tom1_mech",
    "econ_bne_mech",
    "hpsmg_plus_proxy",
    "hpsmg_plus_joint_proxy",
    "oracle_joint",
]


def ensure_concordia_examples_on_path() -> None:
    root = Path(__file__).resolve().parents[1]
    examples_root = root / "external" / "concordia"
    if examples_root.exists():
        sys.path.insert(0, str(examples_root))


def load_config(config_name: str) -> Any:
    import importlib

    if "." not in config_name:
        config_name = f"examples.games.pub_coordination.configs.{config_name}"
    return importlib.import_module(config_name)


def build_case(config: Any, seed: int) -> dict[str, Any]:
    from examples.games.pub_coordination import simulation

    num_main = getattr(config, "NUM_MAIN_PLAYERS", 4)
    num_background = getattr(config, "NUM_BACKGROUND_PLAYERS", 2)
    num_supporting = getattr(config, "NUM_SUPPORTING_PLAYERS", 0)
    num_people = num_main + num_background + num_supporting

    venues, people, rng = simulation.sample_parameters(
        venue_preferences=getattr(config, "VENUE_PREFERENCES"),
        male_names=getattr(config, "MALE_NAMES"),
        female_names=getattr(config, "FEMALE_NAMES"),
        num_venues=getattr(config, "NUM_VENUES"),
        num_people=num_people,
        seed=seed,
    )
    focal_players = people[:num_main]
    background_players = people[num_main : num_main + num_background]
    supporting_players = people[num_main + num_background :]

    use_custom = getattr(config, "USE_CUSTOM_RELATIONSHIPS", False)
    if use_custom and hasattr(config, "make_tough_friendship_matrix"):
        relational_matrix = config.make_tough_friendship_matrix(people)
    else:
        relational_matrix = simulation.sample_symmetric_relationship_matrix(people, rng)
    relationship_statements = simulation.generate_relationship_statements(people, relational_matrix, rng)

    preferences_config = getattr(config, "PERSON_PREFERENCES", {})
    focal_venue_idx = getattr(config, "FOCAL_PREFERS_VENUE_INDEX", None)
    friend_venue_idx = getattr(config, "FRIEND_PREFERS_VENUE_INDEX", None)
    person_preferences: dict[str, str] = {}
    for index, name in enumerate(people):
        if name in preferences_config:
            favorite = preferences_config[name]
        elif index == 0 and focal_venue_idx is not None and len(venues) > focal_venue_idx:
            favorite = venues[focal_venue_idx]
        elif index == 1 and friend_venue_idx is not None and len(venues) > friend_venue_idx:
            favorite = venues[friend_venue_idx]
        else:
            favorite = rng.choice(venues)
        person_preferences[name] = favorite

    closed_venues: list[str] = []
    if rng.random() < getattr(config, "PUB_CLOSED_PROBABILITY", 0.0):
        closed_venues = [rng.choice(venues)]

    return {
        "seed": seed,
        "venues": venues,
        "people": people,
        "focal_players": focal_players,
        "background_players": background_players,
        "supporting_players": supporting_players,
        "person_preferences": person_preferences,
        "relationship_statements": relationship_statements,
        "relational_matrix": relational_matrix,
        "closed_venues": closed_venues,
        "venue_preferences": getattr(config, "VENUE_PREFERENCES"),
        "location": getattr(config, "LOCATION", ""),
        "event": getattr(config, "EVENT", ""),
    }


def payoff_for_case(case: dict[str, Any]):
    from examples.games.pub_coordination import simulation

    venues = case["venues"]
    closed = set(case["closed_venues"])
    return simulation.PubCoordinationPayoff(
        player_names=case["people"],
        person_preferences=case["person_preferences"],
        player_multipliers={name: {venue: 1.0 for venue in venues} for name in case["people"]},
        option_multipliers={venue: 0.0 if venue in closed else 1.0 for venue in venues},
        relational_matrix=case["relational_matrix"],
    )


def run_method(case: dict[str, Any], method: str, model_name: str | None) -> dict[str, Any]:
    if method == "oracle_joint":
        joint_action, info = choose_oracle_joint(case)
    elif method == "hpsmg_plus_proxy":
        joint_action, info = choose_hpsmg_plus_proxy(case)
    elif method == "hpsmg_plus_joint_proxy":
        joint_action, info = choose_hpsmg_plus_joint_proxy(case)
    elif method == "atom_tom1_mech":
        joint_action, info = choose_atom_tom1_mech(case)
    elif method == "econ_bne_mech":
        joint_action, info = choose_econ_bne_mech(case)
    else:
        joint_action, info = choose_llm_actions(case, method, model_name)

    payoff = payoff_for_case(case)
    scores = dict(payoff.action_to_scores(joint_action))
    focal_scores = [float(scores.get(name, 0.0)) for name in case["focal_players"]]
    choices = [joint_action.get(name, "") for name in case["focal_players"]]
    valid_choices = [choice in case["venues"] for choice in joint_action.values()]
    coordination_rate = max((choices.count(venue) for venue in case["venues"]), default=0) / max(1, len(choices))

    return {
        "method": method,
        "seed": case["seed"],
        "venues": list(case["venues"]),
        "focal_players": list(case["focal_players"]),
        "joint_action": joint_action,
        "scores": scores,
        "focal_score_mean": sum(focal_scores) / max(1, len(focal_scores)),
        "focal_score_min": min(focal_scores) if focal_scores else 0.0,
        "coordination_rate": coordination_rate,
        "valid_action_rate": sum(valid_choices) / max(1, len(valid_choices)),
        "information_scope": information_scope_for_method(method),
        "info": info,
    }


def information_scope_for_method(method: str) -> dict[str, Any]:
    if method == "oracle_joint":
        return {
            "mode": "privileged_upper_bound",
            "sees_all_person_preferences": True,
            "sees_full_relationship_matrix": True,
            "uses_known_payoff_model": True,
            "uses_privileged_oracle_objective": True,
            "comparable_as_baseline": False,
        }
    if method in {"hpsmg_plus_proxy", "hpsmg_plus_joint_proxy", "atom_tom1_mech", "econ_bne_mech"}:
        return {
            "mode": "centralized_full_case",
            "sees_all_person_preferences": True,
            "sees_full_relationship_matrix": True,
            "uses_known_payoff_model": True,
            "uses_privileged_oracle_objective": False,
            "comparable_as_baseline": True,
        }
    return {
        "mode": "decentralized_per_player_prompt",
        "sees_all_person_preferences": False,
        "sees_full_relationship_matrix": False,
        "uses_known_payoff_model": False,
        "uses_privileged_oracle_objective": False,
        "comparable_as_baseline": True,
    }


def choose_llm_actions(
    case: dict[str, Any], method: str, model_name: str | None
) -> tuple[dict[str, str], dict[str, Any]]:
    model = HPGGConcordiaLanguageModel(
        model=model_name,
        system_prompt=(
            "You are a concise social-simulation decision agent. "
            f"Use the {method} method and choose one valid pub option."
        ),
    )
    joint_action: dict[str, str] = {}
    replies: dict[str, Any] = {}
    for player in case["people"]:
        prompt = build_player_prompt(case, player, method)
        index, choice, info = model.sample_choice(prompt, case["venues"], seed=case["seed"])
        del index
        joint_action[player] = choice
        replies[player] = dict(info)
    return joint_action, {"llm_replies": replies}


def build_player_prompt(case: dict[str, Any], player: str, method: str) -> str:
    favorite = case["person_preferences"][player]
    relationship_lines = case["relationship_statements"].get(player, [])
    venue_descriptions = {
        venue: case["venue_preferences"].get(venue, [""])[0]
        for venue in case["venues"]
    }
    method_instructions = {
        "llm_greedy": "Choose the venue that maximizes your own expected enjoyment.",
        "llm_belief": "Infer where friends may go, then balance your preference with group coordination.",
        "atom_tom1": "Model each friend's likely choice once, then choose your best response.",
        "econ_bne": "Choose a stable coordination action as if seeking a practical equilibrium.",
    }
    return json.dumps(
        {
            "task": "Compact Concordia Pub Coordination decision",
            "method": method,
            "location": case["location"],
            "event": case["event"],
            "player": player,
            "private_favorite_pub": favorite,
            "available_venues": case["venues"],
            "closed_venues": case["closed_venues"],
            "venue_descriptions": venue_descriptions,
            "relationships": relationship_lines,
            "instruction": method_instructions.get(method, "Choose one valid venue."),
        },
        indent=2,
    )


def choose_hpsmg_plus_proxy(case: dict[str, Any]) -> tuple[dict[str, str], dict[str, Any]]:
    joint_action: dict[str, str] = {}
    posterior_by_player: dict[str, dict[str, float]] = {}
    for player in case["people"]:
        posterior = infer_pub_persona_posterior(case, player)
        posterior_by_player[player] = posterior
        best_venue = max(
            case["venues"],
            key=lambda venue: posterior_expected_score(case, player, venue, posterior),
        )
        joint_action[player] = best_venue
    return joint_action, {
        "policy": "posterior_expected_social_score",
        "persona_posteriors": posterior_by_player,
    }


def choose_hpsmg_plus_joint_proxy(case: dict[str, Any]) -> tuple[dict[str, str], dict[str, Any]]:
    payoff = payoff_for_case(case)
    people = case["people"]
    posterior_by_player = {player: infer_pub_persona_posterior(case, player) for player in people}
    best_action: dict[str, str] | None = None
    best_value = float("-inf")
    for assignment in itertools.product(case["venues"], repeat=len(people)):
        joint_action = dict(zip(people, assignment, strict=True))
        scores = payoff.action_to_scores(joint_action)
        value = posterior_joint_objective(case, scores, joint_action, posterior_by_player)
        if value > best_value:
            best_value = value
            best_action = joint_action
    return best_action or {}, {
        "policy": "posterior_guided_joint_social_objective",
        "best_value": best_value,
        "persona_posteriors": posterior_by_player,
    }


def posterior_joint_objective(
    case: dict[str, Any],
    scores: dict[str, float],
    joint_action: dict[str, str],
    posterior_by_player: dict[str, dict[str, float]] | None = None,
) -> float:
    people = case["people"]
    focal = case["focal_players"]
    all_mean = sum(float(scores.get(name, 0.0)) for name in people) / max(1, len(people))
    focal_min = min((float(scores.get(name, 0.0)) for name in focal), default=0.0)
    coordination = max(
        (list(joint_action.values()).count(venue) for venue in case["venues"]),
        default=0,
    ) / max(1, len(people))
    favorite_satisfaction = sum(
        1.0 for name, venue in joint_action.items() if case["person_preferences"][name] == venue
    ) / max(1, len(people))
    persona_bonus = 0.0
    if posterior_by_player:
        for player in people:
            posterior = posterior_by_player.get(player, {})
            venue = joint_action[player]
            persona_bonus += persona_weighted_venue_score(case, player, venue, posterior)
        persona_bonus /= max(1, len(people))
    return all_mean + 0.25 * focal_min + 0.10 * coordination + 0.05 * favorite_satisfaction + 0.15 * persona_bonus


def choose_atom_tom1_mech(case: dict[str, Any]) -> tuple[dict[str, str], dict[str, Any]]:
    joint_action: dict[str, str] = {}
    per_player: dict[str, Any] = {}
    for player in case["people"]:
        predicted_others = {
            other: zero_order_favorite_choice(case, other)
            for other in case["people"]
            if other != player
        }
        best_venue = max(
            case["venues"],
            key=lambda venue: best_response_score(case, player, venue, predicted_others),
        )
        joint_action[player] = best_venue
        per_player[player] = {"predicted_others": predicted_others, "selected": best_venue}
    return joint_action, {"family": "A-ToM", "tom_level": 1, "players": per_player}


def choose_econ_bne_mech(case: dict[str, Any], rounds: int = 6) -> tuple[dict[str, str], dict[str, Any]]:
    commitment = {player: zero_order_favorite_choice(case, player) for player in case["people"]}
    iteration_history: list[dict[str, Any]] = []
    for iteration in range(rounds):
        next_commitment: dict[str, str] = {}
        for player in case["people"]:
            others = {other: commitment[other] for other in case["people"] if other != player}
            next_commitment[player] = max(
                case["venues"],
                key=lambda venue: best_response_score(case, player, venue, others),
            )
        iteration_history.append({"iteration": iteration, "commitment": next_commitment})
        if next_commitment == commitment:
            commitment = next_commitment
            break
        commitment = next_commitment
    return commitment, {"family": "ECON", "policy": "iterated_best_response", "iterations": iteration_history}


def zero_order_favorite_choice(case: dict[str, Any], player: str) -> str:
    favorite = case["person_preferences"][player]
    if favorite not in case["closed_venues"]:
        return favorite
    return next(venue for venue in case["venues"] if venue not in case["closed_venues"])


def best_response_score(
    case: dict[str, Any], player: str, venue: str, predicted_others: dict[str, str]
) -> float:
    if venue in case["closed_venues"]:
        return float("-inf")
    score = 0.5 if case["person_preferences"][player] == venue else 0.0
    matrix = case["relational_matrix"][player]
    max_social = sum(matrix.values()) - matrix[player]
    if max_social <= 0:
        return score
    same_choice_mass = sum(
        matrix[other]
        for other, predicted_venue in predicted_others.items()
        if predicted_venue == venue
    )
    return score + same_choice_mass / max_social


def posterior_expected_score(case: dict[str, Any], player: str, venue: str, posterior: dict[str, float] | None = None) -> float:
    posterior = posterior or infer_pub_persona_posterior(case, player)
    return persona_weighted_venue_score(case, player, venue, posterior)


def persona_weighted_venue_score(case: dict[str, Any], player: str, venue: str, posterior: dict[str, float]) -> float:
    if venue in case["closed_venues"]:
        return -1.0

    private_match = 1.0 if case["person_preferences"][player] == venue else 0.0
    matrix = case["relational_matrix"][player]
    max_social = sum(matrix.values()) - matrix[player]
    social_alignment = 0.0
    risk_penalty = 0.0 if venue not in case["closed_venues"] else 1.0
    if max_social > 0:
        same_choice_mass = 0.0
        for other in case["people"]:
            if other == player:
                continue
            if case["person_preferences"][other] == venue:
                same_choice_mass += matrix[other]
        social_alignment = same_choice_mass / max_social

    score = 0.0
    for persona_key, prob in posterior.items():
        pref_weight, social_weight, risk_weight = persona_venue_weights(persona_key)
        score += prob * (pref_weight * private_match + social_weight * social_alignment - risk_weight * risk_penalty)
    return score


def infer_pub_persona_posterior(case: dict[str, Any], player: str) -> dict[str, float]:
    keys = [persona.key for persona in PERSONAS]
    log_scores = {key: math.log(1.0 / len(keys)) for key in keys}
    statements = " ".join(case["relationship_statements"].get(player, [])).lower()
    relation_mass = float(sum(case["relational_matrix"].get(player, {}).values()))

    coop_signal = sum(token in statements for token in ["friend", "trust", "care", "close", "support"])
    conditional_signal = sum(token in statements for token in ["if", "depends", "unless", "maybe", "sometimes"])
    risk_signal = sum(token in statements for token in ["careful", "safe", "avoid", "uncertain", "wary"])
    selfish_signal = sum(token in statements for token in ["self", "alone", "independent", "rival", "dislike"])

    if relation_mass >= len(case["people"]) + 2:
        coop_signal += 1
    if relation_mass <= len(case["people"]) - 1:
        selfish_signal += 1

    log_scores["altruistic_builder"] += 0.45 * coop_signal - 0.20 * selfish_signal
    log_scores["conditional_cooperator"] += 0.40 * conditional_signal + 0.20 * coop_signal
    log_scores["risk_averse_balancer"] += 0.50 * risk_signal + 0.15 * conditional_signal
    log_scores["free_rider"] += 0.45 * selfish_signal - 0.20 * coop_signal

    max_log = max(log_scores.values())
    probs = {key: math.exp(value - max_log) for key, value in log_scores.items()}
    total = sum(probs.values())
    if total <= 0.0 or not math.isfinite(total):
        uniform = round(1.0 / len(keys), 4)
        return {key: uniform for key in keys}
    return {key: round(value / total, 4) for key, value in probs.items()}


def persona_venue_weights(persona_key: str) -> tuple[float, float, float]:
    if persona_key == "altruistic_builder":
        return 0.35, 0.65, 0.05
    if persona_key == "conditional_cooperator":
        return 0.45, 0.50, 0.10
    if persona_key == "risk_averse_balancer":
        return 0.55, 0.30, 0.30
    return 0.80, 0.15, 0.05


def choose_oracle_joint(case: dict[str, Any]) -> tuple[dict[str, str], dict[str, Any]]:
    payoff = payoff_for_case(case)
    people = case["people"]
    best_action: dict[str, str] | None = None
    best_value = float("-inf")
    for assignment in itertools.product(case["venues"], repeat=len(people)):
        joint_action = dict(zip(people, assignment, strict=True))
        scores = payoff.action_to_scores(joint_action)
        focal_values = [float(scores.get(name, 0.0)) for name in case["focal_players"]]
        value = sum(focal_values) / max(1, len(focal_values))
        if value > best_value:
            best_value = value
            best_action = joint_action
    return best_action or {}, {"policy": "best_focal_mean", "best_value": best_value}


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_method: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_method.setdefault(row["method"], []).append(row)
    summary = []
    for method, method_rows in by_method.items():
        summary.append(
            {
                "method": method,
                "episodes": len(method_rows),
                "focal_score_mean": mean(row["focal_score_mean"] for row in method_rows),
                "focal_score_min_mean": mean(row["focal_score_min"] for row in method_rows),
                "coordination_rate_mean": mean(row["coordination_rate"] for row in method_rows),
                "valid_action_rate_mean": mean(row["valid_action_rate"] for row in method_rows),
            }
        )
    summary.sort(key=lambda row: (-row["focal_score_mean"], -row["coordination_rate_mean"], row["method"]))
    return summary


def mean(values: Any) -> float:
    values = list(values)
    return float(sum(values) / max(1, len(values)))


def write_summary_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Compact Concordia Pub Coordination Results",
        "",
        f"Config: `{payload['config']}`",
        f"Model: `{payload['model']}`",
        f"Seeds: `{payload['seeds']}`",
        "",
        "| method | episodes | focal_score_mean | focal_score_min_mean | coordination_rate_mean | valid_action_rate_mean |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in payload["summary"]:
        lines.append(
            "| {method} | {episodes} | {focal_score_mean:.4f} | {focal_score_min_mean:.4f} | {coordination_rate_mean:.4f} | {valid_action_rate_mean:.4f} |".format(
                **row
            )
        )
    if payload.get("information_audit"):
        lines.extend(
            [
                "",
                "## Information Fairness Audit",
                "",
                "| method | mode | all_preferences | full_relationship_matrix | known_payoff_model | privileged_oracle_objective | comparable_baseline |",
                "|---|---|---|---|---|---|---|",
            ]
        )
        for method, scope in payload["information_audit"].items():
            lines.append(
                "| {method} | {mode} | {prefs} | {matrix} | {payoff} | {oracle} | {comparable} |".format(
                    method=method,
                    mode=scope["mode"],
                    prefs=str(scope["sees_all_person_preferences"]).lower(),
                    matrix=str(scope["sees_full_relationship_matrix"]).lower(),
                    payoff=str(scope["uses_known_payoff_model"]).lower(),
                    oracle=str(scope["uses_privileged_oracle_objective"]).lower(),
                    comparable=str(scope["comparable_as_baseline"]).lower(),
                )
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="london_mini")
    parser.add_argument("--model")
    parser.add_argument("--methods", nargs="+", default=DEFAULT_METHODS)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--seed-offset", type=int, default=0)
    parser.add_argument("--out", default="analysis/concordia_pub_coordination_compact.json")
    parser.add_argument("--summary-out", default="")
    args = parser.parse_args()

    ensure_concordia_examples_on_path()
    config = load_config(args.config)
    seeds = [args.seed_offset + index for index in range(args.seeds)]
    rows: list[dict[str, Any]] = []
    for seed in seeds:
        case = build_case(config, seed)
        for method in args.methods:
            row = run_method(case, method, args.model)
            rows.append(row)
            print(
                f"seed={seed} method={method} focal_mean={row['focal_score_mean']:.3f} coordination={row['coordination_rate']:.3f}",
                flush=True,
            )

    payload = {
        "config": args.config,
        "model": args.model or "",
        "seeds": seeds,
        "methods": args.methods,
        "information_audit": {method: information_scope_for_method(method) for method in args.methods},
        "summary": summarize(rows),
        "episodes": rows,
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if args.summary_out:
        write_summary_md(Path(args.summary_out), payload)
    print(f"saved={out_path}")
    if args.summary_out:
        print(f"summary={args.summary_out}")


if __name__ == "__main__":
    main()