"""Run compact Concordia haggling scoring sweeps.

This runner reuses Concordia's official haggling payoff classes and config
sampling conventions while skipping slow dialogue scenes. It supports both
single-item and multi-item haggling examples.
"""

from __future__ import annotations

import argparse
import importlib
import json
import math
from pathlib import Path
import sys
from typing import Any, Iterable

from llm_hpgg_concordia.cloudgpt_model import HPGGConcordiaLanguageModel
from llm_hpgg.personas import PERSONAS


DEFAULT_METHODS = [
    "random",
    "atom_tom1_mech",
    "atom_tom2_mech",
    "econ_bne_mech",
    "llm_psrl_verbal",
    "hpsmg_plus_proxy",
    "hpsmg_proxy",
    "hpsmg_plus_joint_proxy",
    "hpsmg_joint_proxy",
    "hpsmg_plus_focal_proxy",
    "hpsmg_focal_proxy",
    "oracle_joint",
    "oracle_focal",
]


def ensure_concordia_examples_on_path() -> None:
    root = Path(__file__).resolve().parents[1]
    examples_root = root / "external" / "concordia"
    if examples_root.exists():
        sys.path.insert(0, str(examples_root))


def load_config(domain: str, config_name: str) -> Any:
    if "." not in config_name:
        config_name = f"examples.games.{domain}.configs.{config_name}"
    return importlib.import_module(config_name)


def build_case(domain: str, config: Any, seed: int) -> dict[str, Any]:
    if domain == "haggling":
        return build_single_case(config, seed)
    if domain == "haggling_multi_item":
        return build_multi_case(config, seed)
    raise ValueError(f"unsupported domain: {domain}")


def build_single_case(config: Any, seed: int) -> dict[str, Any]:
    from examples.games.haggling import simulation

    num_main = getattr(config, "NUM_MAIN_PLAYERS", 3)
    num_supporting = getattr(config, "NUM_SUPPORTING_PLAYERS", 0)
    num_games = getattr(config, "NUM_GAMES", 2)
    all_people, rng = simulation.sample_parameters(
        male_names=getattr(config, "MALE_NAMES"),
        female_names=getattr(config, "FEMALE_NAMES"),
        num_people=num_main + num_supporting,
        seed=seed,
    )
    focal_players = list(all_people[:num_main])
    supporting_players = list(all_people[num_main:])
    pairs = build_pairs(simulation, focal_players, supporting_players, rng, only_match_with_support=False)
    deal_count = num_games * len(pairs)
    buyer_rewards = [
        float(rng.randint(getattr(config, "BUYER_BASE_REWARD_MIN", 5), getattr(config, "BUYER_BASE_REWARD_MAX", 6)))
        for _ in range(deal_count)
    ]
    seller_costs = [
        float(rng.randint(getattr(config, "SELLER_BASE_REWARD_MIN", 1), getattr(config, "SELLER_BASE_REWARD_MAX", 2)))
        for _ in range(deal_count)
    ]
    deals = []
    deal_index = 0
    for game_index in range(num_games):
        for buyer, seller in pairs:
            deals.append({"game_index": game_index, "buyer": buyer, "seller": seller, "buyer_reward": buyer_rewards[deal_index], "seller_cost": seller_costs[deal_index]})
            deal_index += 1
    return {
        "domain": "haggling",
        "seed": seed,
        "people": list(all_people),
        "focal_players": focal_players,
        "supporting_players": supporting_players,
        "pairs": pairs,
        "deals": deals,
        "price_options": list(getattr(config, "PRICE_OPTIONS")),
        "location": getattr(config, "LOCATION", ""),
        "event": getattr(config, "EVENT", ""),
    }


def build_multi_case(config: Any, seed: int) -> dict[str, Any]:
    from examples.games.haggling_multi_item import simulation

    num_main = getattr(config, "NUM_MAIN_PLAYERS", 2)
    num_supporting = getattr(config, "NUM_SUPPORTING_PLAYERS", 0)
    num_games = getattr(config, "NUM_GAMES", 2)
    items = list(getattr(config, "ITEMS_FOR_SALE", ("apple", "banana", "pear")))
    prices = list(getattr(config, "PRICES", (1, 2, 3, 4, 5, 6)))
    all_people, rng = simulation.sample_parameters(
        male_names=getattr(config, "MALE_NAMES"),
        female_names=getattr(config, "FEMALE_NAMES"),
        num_people=num_main + num_supporting,
        seed=seed,
    )
    focal_players = list(all_people[:num_main])
    supporting_players = list(all_people[num_main:])
    pairs = build_pairs(simulation, focal_players, supporting_players, rng, only_match_with_support=getattr(config, "ONLY_MATCH_WITH_SUPPORT", False))
    deal_count = num_games * len(pairs)
    deals = []
    for deal_index in range(deal_count):
        buyer, seller = pairs[deal_index % len(pairs)]
        buyer_rewards = {item: float(rng.randint(getattr(config, "BUYER_BASE_REWARD_MIN", 5), getattr(config, "BUYER_BASE_REWARD_MAX", 6))) for item in items}
        seller_costs = {item: float(rng.randint(getattr(config, "SELLER_BASE_REWARD_MIN", 1), getattr(config, "SELLER_BASE_REWARD_MAX", 2))) for item in items}
        deals.append({"game_index": deal_index // max(1, len(pairs)), "buyer": buyer, "seller": seller, "buyer_rewards": buyer_rewards, "seller_costs": seller_costs})
    return {
        "domain": "haggling_multi_item",
        "seed": seed,
        "people": list(all_people),
        "focal_players": focal_players,
        "supporting_players": supporting_players,
        "pairs": pairs,
        "deals": deals,
        "items": items,
        "prices": prices,
        "price_options": list(simulation.generate_price_options(items, prices)),
        "location": getattr(config, "LOCATION", ""),
        "event": getattr(config, "EVENT", ""),
    }


def build_pairs(simulation: Any, focal_players: list[str], supporting_players: list[str], rng: Any, only_match_with_support: bool) -> list[tuple[str, str]]:
    if supporting_players and only_match_with_support:
        pairs = []
        for main_player in focal_players:
            for support_player in supporting_players:
                pairs.append((main_player, support_player) if rng.choice([True, False]) else (support_player, main_player))
        return pairs
    return simulation.create_player_pairs(list(focal_players) + list(supporting_players), rng)


def run_method(case: dict[str, Any], method: str, model_name: str | None = None) -> dict[str, Any]:
    totals = {name: 0.0 for name in case["people"]}
    deal_rows = []
    for deal in case["deals"]:
        action, info = choose_action(case, deal, method, model_name=model_name)
        scores = score_deal(case, deal, action)
        for name, score in scores.items():
            totals[name] = totals.get(name, 0.0) + float(score)
        buyer_score = float(scores.get(deal["buyer"], 0.0))
        seller_score = float(scores.get(deal["seller"], 0.0))
        deal_rows.append(
            {
                "deal": deal,
                "action": action,
                "scores": scores,
                "accepted": action["seller_action"] == "accept",
                "valid_action": action_is_valid(case, action),
                "surplus": buyer_score + seller_score,
                "min_score": min(buyer_score, seller_score),
                "nash_product": max(0.0, buyer_score) * max(0.0, seller_score),
                "info": info,
            }
        )

    focal_scores = [float(totals.get(name, 0.0)) for name in case["focal_players"]]
    return {
        "method": method,
        "seed": case["seed"],
        "scores": totals,
        "focal_players": list(case["focal_players"]),
        "focal_score_mean": mean(focal_scores),
        "focal_score_min": min(focal_scores) if focal_scores else 0.0,
        "deal_score_mean": mean(row["surplus"] for row in deal_rows),
        "deal_min_score_mean": mean(row["min_score"] for row in deal_rows),
        "nash_product_mean": mean(row["nash_product"] for row in deal_rows),
        "agreement_rate": mean(1.0 if row["accepted"] else 0.0 for row in deal_rows),
        "valid_action_rate": mean(1.0 if row["valid_action"] else 0.0 for row in deal_rows),
        "information_scope": information_scope_for_method(method),
        "deals": deal_rows,
    }


def choose_action(case: dict[str, Any], deal: dict[str, Any], method: str, model_name: str | None = None) -> tuple[dict[str, str], dict[str, Any]]:
    if case["domain"] == "haggling_multi_item":
        return choose_multi_action(case, deal, method, model_name=model_name)
    return choose_single_action(case, deal, method, model_name=model_name)


def choose_single_action(case: dict[str, Any], deal: dict[str, Any], method: str, model_name: str | None = None) -> tuple[dict[str, str], dict[str, Any]]:
    prices = [price_value(option) for option in case["price_options"]]
    buyer_reward = float(deal["buyer_reward"])
    seller_cost = float(deal["seller_cost"])
    feasible = [price for price in prices if seller_cost <= price <= buyer_reward]
    if method == "random":
        import random as _random
        rng = _random.Random(f"{case.get('seed', 0)}|{deal.get('buyer', '')}|{deal.get('seller', '')}|single")
        price = rng.choice(prices)
        accept = bool(rng.random() < 0.5)
        policy = "uniform_random_action"
    elif method == "atom_tom1_mech":
        price = min((candidate for candidate in prices if candidate >= seller_cost), default=min(prices))
        accept = price <= buyer_reward
        policy = "buyer_lowball_first_order_acceptance"
    elif method == "atom_tom2_mech":
        # Second-order ToM: anticipate that seller anticipates lowballing, bump up to median feasible
        if feasible:
            sorted_feas = sorted(feasible)
            price = sorted_feas[len(sorted_feas) // 2]
        else:
            price = min(prices, key=lambda c: abs(c - seller_cost))
        accept = bool(feasible)
        policy = "second_order_median_feasible"
    elif method == "econ_bne_mech":
        price = min(prices, key=lambda candidate: (abs(candidate - 3.0), candidate))
        accept = seller_cost <= price <= buyer_reward
        policy = "market_anchor_equilibrium"
    elif method == "llm_psrl_verbal":
        action, info = choose_llm_psrl_verbal_single(case, deal, model_name)
        return action, info
    elif method in {"hpsmg_plus_proxy", "hpsmg_proxy"}:
        buyer_posterior = infer_haggling_persona_posterior(deal, role="buyer", domain="haggling")
        seller_posterior = infer_haggling_persona_posterior(deal, role="seller", domain="haggling")
        target_share = seller_target_share(seller_posterior)
        target_price = seller_cost + target_share * max(0.0, buyer_reward - seller_cost)
        price = closest_price(prices, target_price, feasible)
        accept = bool(feasible)
        policy = "posterior_individual_fair_split_beta0" if method == "hpsmg_proxy" else "posterior_individual_fair_split"
        return make_single_action(deal, price, accept), {
            "policy": policy,
            "beta": 0.0 if method == "hpsmg_proxy" else None,
            "buyer_persona_posterior": buyer_posterior,
            "seller_persona_posterior": seller_posterior,
        }
    elif method in {"hpsmg_plus_joint_proxy", "hpsmg_joint_proxy", "oracle_joint", "oracle_focal", "hpsmg_plus_focal_proxy", "hpsmg_focal_proxy"} or method.startswith("hpsmg_plus_blend_a"):
        fw = focal_weights_for_deal(case, deal)
        # hpsmg_plus_focal_proxy: maximize focal payoff (like oracle_focal)
        m = "oracle_focal" if method in {"hpsmg_plus_focal_proxy", "hpsmg_focal_proxy"} else method
        price, accept, value = best_single_joint_action(prices, buyer_reward, seller_cost, m, fw)
        policy = {
            "hpsmg_plus_joint_proxy": "joint_nash_social_objective",
            "hpsmg_joint_proxy": "joint_nash_social_objective_beta0",
            "oracle_joint": "oracle_best_surplus",
            "oracle_focal": "oracle_focal_payoff",
            "hpsmg_plus_focal_proxy": "focal_payoff_proxy",
            "hpsmg_focal_proxy": "focal_payoff_proxy_beta0",
        }.get(method, f"blend_focal_joint_{method}")
        return make_single_action(deal, price, accept), {"policy": policy, "objective_value": value, "focal_weights": fw, "beta": 0.0 if method.startswith("hpsmg_") else None}
    else:
        raise ValueError(f"unsupported method: {method}")
    return make_single_action(deal, price, accept), {"policy": policy}


def focal_weights_for_deal(case: dict[str, Any], deal: dict[str, Any]) -> tuple[float, float]:
    fp = set(case.get("focal_players", []))
    return (1.0 if deal.get("buyer") in fp else 0.0,
            1.0 if deal.get("seller") in fp else 0.0)


def choose_multi_action(case: dict[str, Any], deal: dict[str, Any], method: str, model_name: str | None = None) -> tuple[dict[str, str], dict[str, Any]]:
    prices = [float(price) for price in case["prices"]]
    items = list(case["items"])
    buyer_rewards = deal["buyer_rewards"]
    seller_costs = deal["seller_costs"]
    if method == "random":
        import random as _random
        rng = _random.Random(f"{case.get('seed', 0)}|{deal.get('buyer', '')}|{deal.get('seller', '')}|multi")
        item = rng.choice(items)
        price = rng.choice(prices)
        accept = bool(rng.random() < 0.5)
        policy = "uniform_random_action"
    elif method == "atom_tom1_mech":
        item = items[0]
        price = min((candidate for candidate in prices if candidate >= seller_costs[item]), default=min(prices))
        accept = price <= buyer_rewards[item]
        policy = "first_item_lowball_first_order_acceptance"
    elif method == "atom_tom2_mech":
        item = max(items, key=lambda candidate: buyer_rewards[candidate] - seller_costs[candidate])
        feasible = [p for p in prices if seller_costs[item] <= p <= buyer_rewards[item]]
        if feasible:
            sorted_feas = sorted(feasible)
            price = sorted_feas[len(sorted_feas) // 2]
        else:
            price = min(prices, key=lambda c: abs(c - seller_costs[item]))
        accept = bool(feasible)
        policy = "second_order_best_item_median_feasible"
    elif method == "econ_bne_mech":
        item = max(items, key=lambda candidate: buyer_rewards[candidate] - seller_costs[candidate])
        price = min(prices, key=lambda candidate: (abs(candidate - 3.0), candidate))
        accept = seller_costs[item] <= price <= buyer_rewards[item]
        policy = "best_item_market_anchor_equilibrium"
    elif method == "llm_psrl_verbal":
        action, info = choose_llm_psrl_verbal_multi(case, deal, model_name)
        return action, info
    elif method in {"hpsmg_plus_proxy", "hpsmg_proxy"}:
        buyer_posterior = infer_haggling_persona_posterior(deal, role="buyer", domain="haggling_multi_item")
        seller_posterior = infer_haggling_persona_posterior(deal, role="seller", domain="haggling_multi_item")
        item = max(
            items,
            key=lambda candidate: persona_weighted_item_value(
                buyer_rewards[candidate],
                seller_costs[candidate],
                buyer_posterior,
                seller_posterior,
            ),
        )
        feasible = [price for price in prices if seller_costs[item] <= price <= buyer_rewards[item]]
        target_share = seller_target_share(seller_posterior)
        target_price = seller_costs[item] + target_share * max(0.0, buyer_rewards[item] - seller_costs[item])
        price = closest_price(prices, target_price, feasible)
        accept = bool(feasible)
        policy = "posterior_best_item_fair_split_beta0" if method == "hpsmg_proxy" else "posterior_best_item_fair_split"
        return make_multi_action(deal, item, price, accept), {
            "policy": policy,
            "beta": 0.0 if method == "hpsmg_proxy" else None,
            "buyer_persona_posterior": buyer_posterior,
            "seller_persona_posterior": seller_posterior,
        }
    elif method in {"hpsmg_plus_joint_proxy", "hpsmg_joint_proxy", "oracle_joint", "oracle_focal", "hpsmg_plus_focal_proxy", "hpsmg_focal_proxy"} or method.startswith("hpsmg_plus_blend_a"):
        fw = focal_weights_for_deal(case, deal)
        m = "oracle_focal" if method in {"hpsmg_plus_focal_proxy", "hpsmg_focal_proxy"} else method
        item, price, accept, value = best_multi_joint_action(items, prices, buyer_rewards, seller_costs, m, fw)
        policy = {
            "hpsmg_plus_joint_proxy": "joint_item_price_nash_social_objective",
            "hpsmg_joint_proxy": "joint_item_price_nash_social_objective_beta0",
            "oracle_joint": "oracle_best_surplus",
            "oracle_focal": "oracle_focal_payoff",
            "hpsmg_plus_focal_proxy": "focal_payoff_proxy",
            "hpsmg_focal_proxy": "focal_payoff_proxy_beta0",
        }.get(method, f"blend_focal_joint_{method}")
        return make_multi_action(deal, item, price, accept), {"policy": policy, "objective_value": value, "focal_weights": fw, "beta": 0.0 if method.startswith("hpsmg_") else None}
    else:
        raise ValueError(f"unsupported method: {method}")
    return make_multi_action(deal, item, price, accept), {"policy": policy}


def best_single_joint_action(prices: list[float], buyer_reward: float, seller_cost: float, method: str, focal_weights: tuple[float, float] = (1.0, 1.0)) -> tuple[float, bool, float]:
    best = (prices[0], False, float("-inf"))
    for price in prices:
        for accept in (False, True):
            buyer_score, seller_score = single_scores(buyer_reward, seller_cost, price, accept)
            value = bargaining_objective(buyer_score, seller_score, method, focal_weights)
            if value > best[2]:
                best = (price, accept, value)
    return best


def choose_llm_psrl_verbal_single(case: dict[str, Any], deal: dict[str, Any], model_name: str | None) -> tuple[dict[str, str], dict[str, Any]]:
    model = HPGGConcordiaLanguageModel(
        model=model_name,
        system_prompt="You are a careful bargaining coordinator using verbal posterior sampling. Return valid JSON only.",
    )
    prices = list(case["price_options"])
    prompt = json.dumps(
        {
            "task": "Sample a verbal hypothesis and choose a compact haggling action.",
            "buyer": deal["buyer"],
            "seller": deal["seller"],
            "buyer_reward": deal["buyer_reward"],
            "seller_cost": deal["seller_cost"],
            "price_options": prices,
            "instruction": "Choose one buyer_action from price_options and seller_action as accept or reject. Output JSON only.",
            "response_schema": {"buyer_action": "one price option", "seller_action": "accept or reject", "belief": "brief verbal hypothesis"},
        },
        indent=2,
    )
    try:
        reply = model.sample_text(prompt, max_tokens=700, temperature=0.0)
        parsed = _extract_json_object(reply)
        buyer_action = str(parsed.get("buyer_action", "")).strip()
        seller_action = str(parsed.get("seller_action", "")).strip().lower()
        if buyer_action not in prices or seller_action not in {"accept", "reject"}:
            raise ValueError(f"invalid action {buyer_action!r}/{seller_action!r}")
        return {
            "buyer": deal["buyer"],
            "seller": deal["seller"],
            "buyer_action": buyer_action,
            "seller_action": seller_action,
        }, {"policy": "llm_psrl_verbal_direct_haggling", "sample_ok": True, "reply_preview": reply[:1000]}
    except Exception as exc:
        price = min((price_value(option) for option in prices), key=lambda candidate: (abs(candidate - 3.0), candidate))
        accept = float(deal["seller_cost"]) <= price <= float(deal["buyer_reward"])
        return make_single_action(deal, price, accept), {"policy": "llm_psrl_verbal_fallback_market_anchor", "sample_ok": False, "error": str(exc)[:300]}


def choose_llm_psrl_verbal_multi(case: dict[str, Any], deal: dict[str, Any], model_name: str | None) -> tuple[dict[str, str], dict[str, Any]]:
    model = HPGGConcordiaLanguageModel(
        model=model_name,
        system_prompt="You are a careful multi-item bargaining coordinator using verbal posterior sampling. Return valid JSON only.",
    )
    prompt = json.dumps(
        {
            "task": "Sample a verbal hypothesis and choose a compact multi-item haggling action.",
            "buyer": deal["buyer"],
            "seller": deal["seller"],
            "buyer_rewards": deal["buyer_rewards"],
            "seller_costs": deal["seller_costs"],
            "price_options": case["price_options"],
            "instruction": "Choose one buyer_action exactly from price_options and seller_action as accept or reject. Output JSON only.",
            "response_schema": {"buyer_action": "one price option", "seller_action": "accept or reject", "belief": "brief verbal hypothesis"},
        },
        indent=2,
    )
    try:
        reply = model.sample_text(prompt, max_tokens=800, temperature=0.0)
        parsed = _extract_json_object(reply)
        buyer_action = str(parsed.get("buyer_action", "")).strip()
        seller_action = str(parsed.get("seller_action", "")).strip().lower()
        if buyer_action not in case["price_options"] or seller_action not in {"accept", "reject"}:
            raise ValueError(f"invalid action {buyer_action!r}/{seller_action!r}")
        return {
            "buyer": deal["buyer"],
            "seller": deal["seller"],
            "buyer_action": buyer_action,
            "seller_action": seller_action,
        }, {"policy": "llm_psrl_verbal_direct_multi_haggling", "sample_ok": True, "reply_preview": reply[:1000]}
    except Exception as exc:
        item = max(case["items"], key=lambda candidate: deal["buyer_rewards"][candidate] - deal["seller_costs"][candidate])
        prices = [float(price) for price in case["prices"]]
        price = min(prices, key=lambda candidate: (abs(candidate - 3.0), candidate))
        accept = deal["seller_costs"][item] <= price <= deal["buyer_rewards"][item]
        return make_multi_action(deal, item, price, accept), {"policy": "llm_psrl_verbal_fallback_multi_market_anchor", "sample_ok": False, "error": str(exc)[:300]}


def best_multi_joint_action(items: list[str], prices: list[float], buyer_rewards: dict[str, float], seller_costs: dict[str, float], method: str, focal_weights: tuple[float, float] = (1.0, 1.0)) -> tuple[str, float, bool, float]:
    best = (items[0], prices[0], False, float("-inf"))
    for item in items:
        for price in prices:
            for accept in (False, True):
                buyer_score, seller_score = single_scores(buyer_rewards[item], seller_costs[item], price, accept)
                value = bargaining_objective(buyer_score, seller_score, method, focal_weights)
                if value > best[3]:
                    best = (item, price, accept, value)
    return best


def bargaining_objective(buyer_score: float, seller_score: float, method: str, focal_weights: tuple[float, float] = (1.0, 1.0)) -> float:
    if method == "oracle_joint":
        return buyer_score + seller_score
    if method == "oracle_focal":
        wb, ws = focal_weights
        if wb + ws <= 0:
            return buyer_score + seller_score
        return wb * buyer_score + ws * seller_score
    # Blend variants: hpsmg_plus_blend_aXX where XX/100 = alpha in [0, 1].
    # alpha=0 -> pure joint (Nash-fair), alpha=1 -> pure focal payoff.
    if method.startswith("hpsmg_plus_blend_a"):
        try:
            alpha = int(method.split("hpsmg_plus_blend_a", 1)[1]) / 100.0
        except ValueError:
            alpha = 0.0
        alpha = max(0.0, min(1.0, alpha))
        wb, ws = focal_weights
        focal_term = (wb * buyer_score + ws * seller_score) if (wb + ws > 0) else (buyer_score + seller_score)
        nash = max(0.0, buyer_score) * max(0.0, seller_score)
        joint_term = buyer_score + seller_score + 0.35 * min(buyer_score, seller_score) + 0.15 * nash
        return alpha * focal_term + (1.0 - alpha) * joint_term
    nash = max(0.0, buyer_score) * max(0.0, seller_score)
    return buyer_score + seller_score + 0.35 * min(buyer_score, seller_score) + 0.15 * nash


def single_scores(buyer_reward: float, seller_cost: float, price: float, accept: bool) -> tuple[float, float]:
    if not accept:
        return 0.0, 0.0
    return buyer_reward - price, price - seller_cost


def score_deal(case: dict[str, Any], deal: dict[str, Any], action: dict[str, str]) -> dict[str, float]:
    if case["domain"] == "haggling_multi_item":
        from examples.games.haggling_multi_item import simulation
        payoff = simulation.MultiItemHagglingPayoff(deal["buyer"], deal["seller"], deal["buyer_rewards"], deal["seller_costs"])
    else:
        from examples.games.haggling import simulation
        payoff = simulation.HagglingPayoff(deal["buyer"], deal["seller"], deal["buyer_reward"], deal["seller_cost"])
    return dict(payoff.action_to_scores({deal["buyer"]: action["buyer_action"], deal["seller"]: action["seller_action"]}))


def make_single_action(deal: dict[str, Any], price: float, accept: bool) -> dict[str, str]:
    return {"buyer": deal["buyer"], "seller": deal["seller"], "buyer_action": price_label(price), "seller_action": "accept" if accept else "reject"}


def make_multi_action(deal: dict[str, Any], item: str, price: float, accept: bool) -> dict[str, str]:
    return {"buyer": deal["buyer"], "seller": deal["seller"], "buyer_action": f"{item} for {int(price)} coins", "seller_action": "accept" if accept else "reject"}


def action_is_valid(case: dict[str, Any], action: dict[str, str]) -> bool:
    return action["seller_action"] in {"accept", "reject"} and action["buyer_action"] in case["price_options"]


def price_label(price: float) -> str:
    return "1 coin" if int(price) == 1 else f"{int(price)} coins"


def price_value(label: str) -> float:
    return float(label.split()[0])


def closest_price(prices: list[float], target: float, feasible: list[float]) -> float:
    candidates = feasible or prices
    return min(candidates, key=lambda candidate: (abs(candidate - target), candidate))


def infer_haggling_persona_posterior(deal: dict[str, Any], role: str, domain: str) -> dict[str, float]:
    keys = [persona.key for persona in PERSONAS]
    log_scores = {key: math.log(1.0 / len(keys)) for key in keys}
    if domain == "haggling":
        buyer_value = float(deal["buyer_reward"])
        seller_value = float(deal["seller_cost"])
        spread = max(0.0, buyer_value - seller_value)
        spread_ratio = spread / max(1.0, buyer_value)
        if role == "buyer":
            log_scores["free_rider"] += 0.7 * spread_ratio
            log_scores["risk_averse_balancer"] += 0.4 * (1.0 - spread_ratio)
            log_scores["conditional_cooperator"] += 0.25
        else:
            log_scores["risk_averse_balancer"] += 0.5 * (1.0 - spread_ratio)
            log_scores["conditional_cooperator"] += 0.3
            log_scores["free_rider"] += 0.35 * spread_ratio
    else:
        buyer_rewards = deal["buyer_rewards"]
        seller_costs = deal["seller_costs"]
        spreads = [max(0.0, float(buyer_rewards[item]) - float(seller_costs[item])) for item in buyer_rewards]
        mean_spread = sum(spreads) / max(1, len(spreads))
        spread_ratio = mean_spread / max(1.0, max(float(value) for value in buyer_rewards.values()))
        if role == "buyer":
            log_scores["free_rider"] += 0.65 * spread_ratio
            log_scores["conditional_cooperator"] += 0.25
        else:
            log_scores["risk_averse_balancer"] += 0.45 * (1.0 - spread_ratio)
            log_scores["conditional_cooperator"] += 0.30
            log_scores["free_rider"] += 0.25 * spread_ratio

    max_log = max(log_scores.values())
    probs = {key: math.exp(value - max_log) for key, value in log_scores.items()}
    total = sum(probs.values())
    if total <= 0.0 or not math.isfinite(total):
        uniform = round(1.0 / len(keys), 4)
        return {key: uniform for key in keys}
    return {key: round(value / total, 4) for key, value in probs.items()}


def seller_target_share(seller_posterior: dict[str, float]) -> float:
    weights = {
        "altruistic_builder": 0.35,
        "conditional_cooperator": 0.45,
        "risk_averse_balancer": 0.55,
        "free_rider": 0.70,
    }
    share = sum(float(seller_posterior.get(key, 0.0)) * value for key, value in weights.items())
    return min(0.85, max(0.20, share))


def persona_weighted_item_value(
    buyer_reward: float,
    seller_cost: float,
    buyer_posterior: dict[str, float],
    seller_posterior: dict[str, float],
) -> float:
    spread = max(0.0, float(buyer_reward) - float(seller_cost))
    buyer_coop = float(buyer_posterior.get("altruistic_builder", 0.0) + buyer_posterior.get("conditional_cooperator", 0.0))
    seller_coop = float(seller_posterior.get("altruistic_builder", 0.0) + seller_posterior.get("conditional_cooperator", 0.0))
    return spread * (0.6 + 0.2 * buyer_coop + 0.2 * seller_coop)


def information_scope_for_method(method: str) -> dict[str, Any]:
    if method in {"oracle_joint", "oracle_focal"}:
        return {"mode": "privileged_upper_bound", "sees_full_case": True, "uses_known_payoff_model": True, "uses_privileged_oracle_objective": True, "comparable_as_baseline": False}
    if method == "random":
        return {"mode": "uninformed_random", "sees_full_case": False, "uses_known_payoff_model": False, "uses_privileged_oracle_objective": False, "comparable_as_baseline": True}
    if method == "llm_psrl_verbal":
        return {"mode": "centralized_verbal_posterior", "sees_full_case": True, "uses_known_payoff_model": True, "uses_privileged_oracle_objective": False, "comparable_as_baseline": True}
    return {"mode": "centralized_full_case", "sees_full_case": True, "uses_known_payoff_model": True, "uses_privileged_oracle_objective": False, "comparable_as_baseline": True}


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
                "deal_score_mean": mean(row["deal_score_mean"] for row in method_rows),
                "deal_min_score_mean": mean(row["deal_min_score_mean"] for row in method_rows),
                "nash_product_mean": mean(row["nash_product_mean"] for row in method_rows),
                "agreement_rate_mean": mean(row["agreement_rate"] for row in method_rows),
                "valid_action_rate_mean": mean(row["valid_action_rate"] for row in method_rows),
            }
        )
    summary.sort(key=lambda row: (-row["nash_product_mean"], -row["focal_score_min_mean"], -row["focal_score_mean"], row["method"]))
    return summary


def mean(values: Iterable[float]) -> float:
    values = list(values)
    return float(sum(values) / max(1, len(values)))


def write_summary_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Compact Concordia Haggling Results",
        "",
        f"Domain: `{payload['domain']}`",
        f"Config: `{payload['config']}`",
        f"Seeds: `{payload['seeds']}`",
        "",
        "| method | episodes | focal_score_mean | focal_score_min_mean | deal_score_mean | deal_min_score_mean | nash_product_mean | agreement_rate_mean | valid_action_rate_mean |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["summary"]:
        lines.append("| {method} | {episodes} | {focal_score_mean:.4f} | {focal_score_min_mean:.4f} | {deal_score_mean:.4f} | {deal_min_score_mean:.4f} | {nash_product_mean:.4f} | {agreement_rate_mean:.4f} | {valid_action_rate_mean:.4f} |".format(**row))
    lines.extend(["", "## Information Fairness Audit", "", "| method | mode | full_case | known_payoff_model | privileged_oracle_objective | comparable_baseline |", "|---|---|---|---|---|---|"])
    for method, scope in payload["information_audit"].items():
        lines.append("| {method} | {mode} | {full_case} | {payoff} | {oracle} | {comparable} |".format(method=method, mode=scope["mode"], full_case=str(scope["sees_full_case"]).lower(), payoff=str(scope["uses_known_payoff_model"]).lower(), oracle=str(scope["uses_privileged_oracle_objective"]).lower(), comparable=str(scope["comparable_as_baseline"]).lower()))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", choices=["haggling", "haggling_multi_item"], default="haggling")
    parser.add_argument("--config", default="fruitville")
    parser.add_argument("--methods", nargs="+", default=DEFAULT_METHODS)
    parser.add_argument("--model", default=None)
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--seed-offset", type=int, default=0)
    parser.add_argument("--out", default="analysis/concordia_haggling_compact.json")
    parser.add_argument("--summary-out", default="")
    args = parser.parse_args()

    ensure_concordia_examples_on_path()
    config = load_config(args.domain, args.config)
    seeds = [args.seed_offset + index for index in range(args.seeds)]
    rows: list[dict[str, Any]] = []
    for seed in seeds:
        case = build_case(args.domain, config, seed)
        for method in args.methods:
            row = run_method(case, method, model_name=args.model)
            rows.append(row)
            print(f"seed={seed} method={method} focal_mean={row['focal_score_mean']:.3f} min={row['focal_score_min']:.3f} nash={row['nash_product_mean']:.3f}", flush=True)

    payload = {
        "domain": args.domain,
        "config": args.config,
        "seeds": seeds,
        "methods": args.methods,
        "model": args.model or "",
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