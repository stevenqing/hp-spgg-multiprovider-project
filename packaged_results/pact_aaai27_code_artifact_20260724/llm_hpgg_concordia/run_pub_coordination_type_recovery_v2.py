"""Pub-Coordination type-recovery benchmark v2.

Unlike v1 (which leaked `person_preferences` to every method), v2 enforces a
strict information boundary: each method only sees the *masked observation*

    obs = {
        people, focal_players, venues, closed_venues,
        relationship_statements, relational_matrix,
        history: [{round, joint_action}, ...],
    }

and must output a per-player posterior over the hidden favourite venue.

Each episode runs ``rounds`` ticks. Per tick we sample a noisy joint action
from the ground-truth preferences (each player picks their favourite with
probability ``1 - epsilon`` else uniform over open venues), append it to the
history, and ask every method to emit a posterior. Metrics are computed
per round and aggregated.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from pathlib import Path
from typing import Any, Callable

from .cloudgpt_model import HPGGConcordiaLanguageModel
from .run_pub_coordination_compact import (
    build_case,
    ensure_concordia_examples_on_path,
    infer_pub_persona_posterior,
    load_config,
    persona_weighted_venue_score,
)


# --------------------------------------------------------------------------- #
# Observation construction
# --------------------------------------------------------------------------- #


def make_observation(case: dict[str, Any], history: list[dict[str, Any]]) -> dict[str, Any]:
    """Return a *masked* observation: case fields minus ``person_preferences``."""
    return {
        "people": list(case["people"]),
        "focal_players": list(case["focal_players"]),
        "venues": list(case["venues"]),
        "closed_venues": list(case["closed_venues"]),
        "relationship_statements": dict(case["relationship_statements"]),
        "relational_matrix": dict(case["relational_matrix"]),
        "history": list(history),
    }


def sample_round_joint_action(
    case: dict[str, Any], epsilon: float, rng: random.Random
) -> dict[str, str]:
    open_venues = [v for v in case["venues"] if v not in case["closed_venues"]] or case["venues"]
    joint: dict[str, str] = {}
    for player in case["people"]:
        favourite = case["person_preferences"][player]
        if favourite in case["closed_venues"] or rng.random() < epsilon:
            joint[player] = rng.choice(open_venues)
        else:
            joint[player] = favourite
    return joint


# --------------------------------------------------------------------------- #
# Posterior helpers
# --------------------------------------------------------------------------- #


def _smooth(p: dict[str, float], venues: list[str], eps: float = 1e-3) -> dict[str, float]:
    out = {v: p.get(v, 0.0) for v in venues}
    for v in venues:
        out[v] = (1.0 - eps) * out[v] + eps * (1.0 / len(venues))
    s = sum(out.values())
    return {v: out[v] / s for v in venues}


def _softmax(scores: dict[str, float], temperature: float = 1.0) -> dict[str, float]:
    if not scores:
        return {}
    logits = {k: v / max(temperature, 1e-6) for k, v in scores.items()}
    m = max(logits.values())
    exps = {k: math.exp(v - m) for k, v in logits.items()}
    total = sum(exps.values()) or 1.0
    return {k: v / total for k, v in exps.items()}


def visit_count_posterior(
    obs: dict[str, Any], player: str, *, alpha: float = 1.0
) -> dict[str, float]:
    """Dirichlet posterior over venues from observed joint actions of ``player``."""
    venues = obs["venues"]
    counts = {v: alpha for v in venues}  # Laplace prior
    for entry in obs["history"]:
        venue = entry["joint_action"].get(player)
        if venue in counts:
            counts[venue] += 1.0
    total = sum(counts.values()) or 1.0
    return {v: counts[v] / total for v in venues}


def persona_prior_posterior(
    obs: dict[str, Any], case_ref: dict[str, Any], player: str
) -> dict[str, float]:
    """Persona-only prior over venues (no observation update). Uses statements
    + relational matrix via ``infer_pub_persona_posterior`` then maps to
    venues via ``persona_weighted_venue_score``.

    ``case_ref`` is a stand-in case dict providing fields the persona scorer
    needs that are *also* in the masked observation (statements, matrix,
    venues, closed_venues, people, relational matrix). It must NOT include
    ``person_preferences``.
    """
    venues = obs["venues"]
    posterior = infer_pub_persona_posterior(case_ref, player)
    scores = {
        venue: _persona_to_venue_score(case_ref, player, venue, posterior)
        for venue in venues
    }
    return _softmax(scores, temperature=0.5)


def _persona_to_venue_score(
    case_ref: dict[str, Any], player: str, venue: str, posterior: dict[str, float]
) -> float:
    """Like ``persona_weighted_venue_score`` but only uses information present
    in the masked observation (i.e. no ``person_preferences``)."""
    if venue in case_ref["closed_venues"]:
        return -1.0
    matrix = case_ref["relational_matrix"][player]
    max_social = sum(matrix.values()) - matrix.get(player, 0.0)
    # We can no longer compute private_match (needs ground-truth preferences)
    # nor social_alignment (needs others' preferences). Best signal we have:
    # personas weighted toward venues by their type's preference profile, plus
    # social mass directed at the venue via co-attendance history.
    score = 0.0
    for persona_key, prob in posterior.items():
        pref_weight, social_weight, risk_weight = _persona_venue_weights(persona_key)
        # We treat the persona's archetype as preferring "popular" venues
        # under the social weight; private preferences are unknown.
        score += prob * (pref_weight + social_weight * 0.5 - risk_weight * 0.1)
    return score


def _persona_venue_weights(persona_key: str) -> tuple[float, float, float]:
    if persona_key == "altruistic_builder":
        return 0.35, 0.65, 0.05
    if persona_key == "conditional_cooperator":
        return 0.45, 0.50, 0.10
    if persona_key == "risk_averse_balancer":
        return 0.55, 0.30, 0.30
    return 0.80, 0.15, 0.05


# --------------------------------------------------------------------------- #
# Methods
# --------------------------------------------------------------------------- #


def method_uniform(obs: dict[str, Any], case: dict[str, Any]) -> dict[str, dict[str, float]]:
    venues = obs["venues"]
    return {p: {v: 1.0 / len(venues) for v in venues} for p in obs["people"]}


def method_bayes_count(obs: dict[str, Any], case: dict[str, Any]) -> dict[str, dict[str, float]]:
    return {p: _smooth(visit_count_posterior(obs, p), obs["venues"]) for p in obs["people"]}


def method_persona_prior(obs: dict[str, Any], case: dict[str, Any]) -> dict[str, dict[str, float]]:
    case_ref = {**obs}  # safe: no person_preferences
    return {p: _smooth(persona_prior_posterior(obs, case_ref, p), obs["venues"]) for p in obs["people"]}


def method_hpsmg_plus_proxy(obs: dict[str, Any], case: dict[str, Any]) -> dict[str, dict[str, float]]:
    """μ(venue) ∝ visit_count_posterior(venue) × persona_prior(venue)."""
    venues = obs["venues"]
    case_ref = {**obs}
    out: dict[str, dict[str, float]] = {}
    for player in obs["people"]:
        prior = persona_prior_posterior(obs, case_ref, player)
        likelihood = visit_count_posterior(obs, player)
        combined = {v: prior[v] * likelihood[v] for v in venues}
        s = sum(combined.values()) or 1.0
        out[player] = _smooth({v: combined[v] / s for v in venues}, venues)
    return out


def method_hpsmg_plus_joint_proxy(
    obs: dict[str, Any], case: dict[str, Any]
) -> dict[str, dict[str, float]]:
    """Joint variant: weight each player's posterior by alignment with the
    most-popular venue per round (encodes weak coordination prior)."""
    venues = obs["venues"]
    case_ref = {**obs}
    # Tally global popularity per venue across history
    popularity = {v: 1.0 for v in venues}
    for entry in obs["history"]:
        for venue in entry["joint_action"].values():
            if venue in popularity:
                popularity[venue] += 1.0
    pop_total = sum(popularity.values()) or 1.0
    pop_norm = {v: popularity[v] / pop_total for v in venues}

    out: dict[str, dict[str, float]] = {}
    for player in obs["people"]:
        prior = persona_prior_posterior(obs, case_ref, player)
        likelihood = visit_count_posterior(obs, player)
        combined = {v: prior[v] * likelihood[v] * (0.5 + 0.5 * pop_norm[v]) for v in venues}
        s = sum(combined.values()) or 1.0
        out[player] = _smooth({v: combined[v] / s for v in venues}, venues)
    return out


def method_atom_tom1(obs: dict[str, Any], case: dict[str, Any]) -> dict[str, dict[str, float]]:
    """k=1 ToM: for each player, build posterior from own visit counts AND
    from the predicted favourites of co-attended others (weighted by
    relational matrix)."""
    venues = obs["venues"]
    own_post = {p: visit_count_posterior(obs, p) for p in obs["people"]}
    out: dict[str, dict[str, float]] = {}
    for player in obs["people"]:
        matrix = obs["relational_matrix"][player]
        max_social = sum(matrix.values()) - matrix.get(player, 0.0)
        social_signal = {v: 0.0 for v in venues}
        if max_social > 0:
            for other in obs["people"]:
                if other == player:
                    continue
                weight = matrix.get(other, 0.0) / max_social
                for v in venues:
                    social_signal[v] += weight * own_post[other][v]
        combined = {v: 0.7 * own_post[player][v] + 0.3 * social_signal[v] for v in venues}
        s = sum(combined.values()) or 1.0
        out[player] = _smooth({v: combined[v] / s for v in venues}, venues)
    return out


def method_econ_bne(obs: dict[str, Any], case: dict[str, Any]) -> dict[str, dict[str, float]]:
    """Iterated best-response: alternate updating each player's posterior
    given others' posteriors. Converges to a fixed point (BNE)."""
    venues = obs["venues"]
    posteriors = {p: visit_count_posterior(obs, p) for p in obs["people"]}
    for _ in range(4):
        new_posteriors: dict[str, dict[str, float]] = {}
        for player in obs["people"]:
            matrix = obs["relational_matrix"][player]
            max_social = sum(matrix.values()) - matrix.get(player, 0.0) or 1.0
            social_score = {v: 0.0 for v in venues}
            for other in obs["people"]:
                if other == player:
                    continue
                w = matrix.get(other, 0.0) / max_social
                for v in venues:
                    social_score[v] += w * posteriors[other][v]
            own = visit_count_posterior(obs, player)
            combined = {v: own[v] * (0.5 + 0.5 * social_score[v]) for v in venues}
            s = sum(combined.values()) or 1.0
            new_posteriors[player] = {v: combined[v] / s for v in venues}
        posteriors = new_posteriors
    return {p: _smooth(posteriors[p], venues) for p in obs["people"]}


def method_oracle(obs: dict[str, Any], case: dict[str, Any]) -> dict[str, dict[str, float]]:
    venues = obs["venues"]
    return {
        p: _smooth({case["person_preferences"][p]: 1.0}, venues)
        for p in obs["people"]
    }


def method_map_greedy(obs: dict[str, Any], case: dict[str, Any]) -> dict[str, dict[str, float]]:
    """Collapse the visit-count posterior to a delta on the MAP venue."""
    venues = obs["venues"]
    out: dict[str, dict[str, float]] = {}
    for player in obs["people"]:
        post = visit_count_posterior(obs, player)
        best = max(venues, key=lambda v: post[v])
        out[player] = _smooth({best: 1.0}, venues)
    return out


def method_atom_tom2(obs: dict[str, Any], case: dict[str, Any]) -> dict[str, dict[str, float]]:
    """k=2 ToM: each player models others by FIRST running k=1 ToM from each
    other's perspective, then aggregates those second-order beliefs via the
    relational matrix. This makes the inference recursive: my belief about
    player j's type is shaped by what j would infer about k, weighted by j's
    closeness to k.
    """
    venues = obs["venues"]
    # Step 1: compute ToM-1 posteriors for every player (these are what each
    # player would believe about themselves under k=1 reasoning).
    tom1 = method_atom_tom1(obs, case)
    # Step 2: for each focal player, build a second-order signal by averaging
    # ToM-1 posteriors of co-attended others, weighted by the focal player's
    # relational matrix (i.e. how much focal trusts each other's model).
    out: dict[str, dict[str, float]] = {}
    own_post = {p: visit_count_posterior(obs, p) for p in obs["people"]}
    for player in obs["people"]:
        matrix = obs["relational_matrix"][player]
        max_social = sum(matrix.values()) - matrix.get(player, 0.0)
        second_order = {v: 0.0 for v in venues}
        if max_social > 0:
            for other in obs["people"]:
                if other == player:
                    continue
                weight = matrix.get(other, 0.0) / max_social
                for v in venues:
                    second_order[v] += weight * tom1[other][v]
        # Mix own observations, ToM-1 own posterior, and second-order signal
        combined = {
            v: 0.5 * own_post[player][v]
            + 0.3 * tom1[player][v]
            + 0.2 * second_order[v]
            for v in venues
        }
        s = sum(combined.values()) or 1.0
        out[player] = _smooth({v: combined[v] / s for v in venues}, venues)
    return out


# --- LLM methods ----------------------------------------------------------- #


def _extract_json_object(reply: str) -> dict[str, Any]:
    import re as _re
    match = _re.search(r"\{.*\}", reply, flags=_re.S)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except Exception:
        return {}


def _normalise_venue_distribution(raw: Any, venues: list[str]) -> dict[str, float]:
    out: dict[str, float] = {v: 0.0 for v in venues}
    if not isinstance(raw, dict):
        return {v: 1.0 / len(venues) for v in venues}
    for k, val in raw.items():
        if k not in out:
            continue
        try:
            out[k] = max(0.0, float(val))
        except (TypeError, ValueError):
            out[k] = 0.0
    total = sum(out.values())
    if total <= 0.0:
        return {v: 1.0 / len(venues) for v in venues}
    return {v: out[v] / total for v in venues}


def _history_block(obs: dict[str, Any]) -> str:
    if not obs["history"]:
        return "No prior observations.\n"
    lines = []
    for entry in obs["history"]:
        line = f"Round {entry['round']}: " + ", ".join(
            f"{p}->{v}" for p, v in entry["joint_action"].items()
        )
        lines.append(line)
    return "\n".join(lines) + "\n"


def method_centralized_planner_llm(
    obs: dict[str, Any], case: dict[str, Any], *, model_name: str | None = None
) -> dict[str, dict[str, float]]:
    venues = obs["venues"]
    people = obs["people"]
    statements_block = "\n".join(
        f"- {p}: {' '.join(obs['relationship_statements'].get(p, []))}"
        for p in people
    )
    closed = ", ".join(obs["closed_venues"]) or "none"
    history_block = _history_block(obs)
    prompt = (
        "You observe a group going to pubs over multiple nights. Each person has "
        "a private favourite pub. Use the social relationship statements AND the "
        "observed joint actions so far to estimate each person's favourite. "
        "Return JSON only.\n\n"
        f"Venues: {venues}\nClosed: {closed}\n\n"
        f"Relationships:\n{statements_block}\n\n"
        f"Observed joint actions per round:\n{history_block}\n"
        'Return: {"posteriors": {"<player>": {"<venue>": <prob>, ...}, ...}}\n'
        "Each player's distribution must sum to 1."
    )
    model = HPGGConcordiaLanguageModel(
        model=model_name,
        system_prompt=(
            "You infer hidden venue preferences from social text and observed "
            "behaviour. Output a calibrated probability distribution per player. "
            "Return valid JSON only."
        ),
    )
    reply = model.sample_text(prompt, max_tokens=700, temperature=0.0)
    parsed = _extract_json_object(reply).get("posteriors", {})
    return {
        p: _smooth(_normalise_venue_distribution(parsed.get(p, {}), venues), venues)
        for p in people
    }


def method_chat_agent_llm(
    obs: dict[str, Any], case: dict[str, Any], *, model_name: str | None = None
) -> dict[str, dict[str, float]]:
    venues = obs["venues"]
    people = obs["people"]
    closed = ", ".join(obs["closed_venues"]) or "none"
    model = HPGGConcordiaLanguageModel(
        model=model_name,
        system_prompt=(
            "You infer one person's hidden favourite pub from social text and "
            "behavioural history. Return valid JSON only."
        ),
    )
    out: dict[str, dict[str, float]] = {}
    for player in people:
        own_history = "\n".join(
            f"Round {entry['round']}: {player} -> {entry['joint_action'].get(player, '?')}"
            for entry in obs["history"]
        ) or "No prior observations."
        own_statements = " ".join(obs["relationship_statements"].get(player, []))
        prompt = (
            f"Person: {player}\nVenues: {venues}\nClosed: {closed}\n"
            f"Social context: {own_statements}\n"
            f"Behavioural history:\n{own_history}\n\n"
            'Return JSON: {"posterior": {"<venue>": <prob>, ...}}. Sum to 1.'
        )
        reply = model.sample_text(prompt, max_tokens=200, temperature=0.0)
        parsed = _extract_json_object(reply).get("posterior", {})
        out[player] = _smooth(_normalise_venue_distribution(parsed, venues), venues)
    return out


# --------------------------------------------------------------------------- #
# Registry + metrics
# --------------------------------------------------------------------------- #


METHOD_REGISTRY: dict[str, Callable[..., dict[str, dict[str, float]]]] = {
    # Canonical (paper-aligned) names
    "random": method_uniform,
    "map_greedy": method_map_greedy,
    "hpsmg": method_bayes_count,
    "hpsmg_plus": method_hpsmg_plus_proxy,
    "joint_psrl": method_hpsmg_plus_joint_proxy,
    "atom_tom1": method_atom_tom1,
    "atom_tom2": method_atom_tom2,
    "econ_bne": method_econ_bne,
    "llm_belief": method_centralized_planner_llm,
    "chat_agent_llm": method_chat_agent_llm,
    "oracle": method_oracle,
    # Legacy aliases (kept for backwards compatibility with v2 smoke runs)
    "uniform": method_uniform,
    "bayes_count": method_bayes_count,
    "persona_prior": method_persona_prior,
    "hpsmg_plus_proxy": method_hpsmg_plus_proxy,
    "hpsmg_plus_joint_proxy": method_hpsmg_plus_joint_proxy,
    "centralized_planner_llm": method_centralized_planner_llm,
}

LLM_METHODS = {"llm_belief", "centralized_planner_llm", "chat_agent_llm"}

DEFAULT_METHODS = [
    "random",
    "map_greedy",
    "hpsmg",
    "hpsmg_plus",
    "joint_psrl",
    "atom_tom1",
    "atom_tom2",
    "econ_bne",
    "llm_belief",
    "chat_agent_llm",
    "oracle",
]


def type_recovery_metrics(
    case: dict[str, Any], venue_posterior: dict[str, dict[str, float]]
) -> dict[str, float]:
    truths = case["person_preferences"]
    venues = list(case["venues"])
    nll = 0.0
    brier = 0.0
    top1 = 0
    n = 0
    for player in case["people"]:
        true_venue = truths[player]
        p = venue_posterior.get(player) or {v: 1.0 / len(venues) for v in venues}
        prob_true = max(p.get(true_venue, 0.0), 1e-9)
        nll += -math.log(prob_true)
        brier += sum((p.get(v, 0.0) - (1.0 if v == true_venue else 0.0)) ** 2 for v in venues)
        argmax = max(venues, key=lambda v: p.get(v, 0.0))
        if argmax == true_venue:
            top1 += 1
        n += 1
    n = max(1, n)
    return {
        "top1_accuracy": top1 / n,
        "nll": nll / n,
        "brier": brier / n,
        "uniform_baseline_nll": math.log(len(venues)),
    }


# --------------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------------- #


def run_episode(
    case: dict[str, Any],
    methods: list[str],
    rounds: int,
    epsilon: float,
    model_name: str | None,
    rng: random.Random,
) -> list[dict[str, Any]]:
    history: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    for r in range(1, rounds + 1):
        joint = sample_round_joint_action(case, epsilon, rng)
        history.append({"round": r, "joint_action": joint})
        obs = make_observation(case, history)
        for method in methods:
            fn = METHOD_REGISTRY[method]
            t0 = time.time()
            try:
                if method in LLM_METHODS:
                    posterior = fn(obs, case, model_name=model_name)
                else:
                    posterior = fn(obs, case)
            except Exception as exc:
                print(f"  [WARN {method} round={r} FAILED]: {exc!r}", flush=True)
                posterior = {p: {v: 1.0 / len(case["venues"]) for v in case["venues"]} for p in case["people"]}
            elapsed = time.time() - t0
            metrics = type_recovery_metrics(case, posterior)
            rows.append(
                {
                    "method": method,
                    "seed": case["seed"],
                    "round": r,
                    **metrics,
                    "elapsed_sec": elapsed,
                }
            )
            print(
                f"  [seed={case['seed']} r={r:02d} {method:<25s}] "
                f"top1={metrics['top1_accuracy']:.2f} nll={metrics['nll']:.3f} "
                f"brier={metrics['brier']:.3f} ({elapsed:.1f}s)",
                flush=True,
            )
    return rows


def mean(values: Any) -> float:
    vals = list(values)
    return float(sum(vals) / max(1, len(vals)))


def summarize(rows: list[dict[str, Any]], rounds: int) -> dict[str, Any]:
    """Return both a final-round summary and a per-round convergence table."""
    by_method: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_method.setdefault(row["method"], []).append(row)

    final_summary = []
    convergence: dict[str, list[dict[str, float]]] = {}
    for method, method_rows in by_method.items():
        last_round_rows = [r for r in method_rows if r["round"] == rounds]
        final_summary.append(
            {
                "method": method,
                "episodes": len(last_round_rows),
                "top1_accuracy_mean": mean(r["top1_accuracy"] for r in last_round_rows),
                "nll_mean": mean(r["nll"] for r in last_round_rows),
                "brier_mean": mean(r["brier"] for r in last_round_rows),
                "uniform_baseline_nll": last_round_rows[0]["uniform_baseline_nll"] if last_round_rows else 0.0,
            }
        )
        # Per-round means
        convergence[method] = []
        for r in range(1, rounds + 1):
            round_rows = [row for row in method_rows if row["round"] == r]
            if not round_rows:
                continue
            convergence[method].append(
                {
                    "round": r,
                    "top1_accuracy": mean(row["top1_accuracy"] for row in round_rows),
                    "nll": mean(row["nll"] for row in round_rows),
                    "brier": mean(row["brier"] for row in round_rows),
                }
            )
    final_summary.sort(key=lambda r: (-r["top1_accuracy_mean"], r["nll_mean"], r["method"]))
    return {"final": final_summary, "convergence": convergence}


def write_summary_md(path: Path, payload: dict[str, Any]) -> None:
    rounds = payload["rounds"]
    lines = [
        "# Pub-Coordination Type Recovery (v2 — masked observation)",
        "",
        f"Config: `{payload['config']}`  Model: `{payload['model']}`  Seeds: `{payload['seeds']}`  Rounds: `{rounds}`  Epsilon: `{payload['epsilon']}`",
        "",
        "Hidden type per player = favourite venue. Methods see only "
        "relationship statements, relational matrix, venues, closed venues, "
        "and the observed joint actions so far.",
        "",
        f"## Final-round (round={rounds}) metrics",
        "",
        "| method | episodes | top1 | NLL | Brier | uniform NLL |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in payload["summary"]["final"]:
        lines.append(
            "| {method} | {episodes} | {top1_accuracy_mean:.4f} | {nll_mean:.4f} | {brier_mean:.4f} | {uniform_baseline_nll:.4f} |".format(
                **row
            )
        )
    lines.extend(["", "## Per-round convergence (top1 accuracy)", "", "| method | " + " | ".join(f"r{r}" for r in range(1, rounds + 1)) + " |", "|---|" + "---:|" * rounds])
    for method, conv in payload["summary"]["convergence"].items():
        by_round = {row["round"]: row["top1_accuracy"] for row in conv}
        cells = " | ".join(f"{by_round.get(r, 0.0):.3f}" for r in range(1, rounds + 1))
        lines.append(f"| {method} | {cells} |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="london_mini")
    parser.add_argument("--model")
    parser.add_argument("--methods", nargs="+", default=DEFAULT_METHODS, choices=list(METHOD_REGISTRY))
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--seed-offset", type=int, default=0)
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--epsilon", type=float, default=0.1, help="Action noise: prob of picking a uniformly random open venue instead of favourite.")
    parser.add_argument("--out", default="analysis/pub_coordination_type_recovery_v2.json")
    parser.add_argument("--summary-out", default="analysis/pub_coordination_type_recovery_v2.md")
    args = parser.parse_args()

    ensure_concordia_examples_on_path()
    config = load_config(args.config)
    seeds = [args.seed_offset + i for i in range(args.seeds)]

    rows: list[dict[str, Any]] = []
    t0 = time.time()
    for seed in seeds:
        case = build_case(config, seed)
        rng = random.Random(seed * 7919 + 1)
        print(f"=== seed={seed} venues={case['venues']} people={case['people']} ===", flush=True)
        episode_rows = run_episode(case, args.methods, args.rounds, args.epsilon, args.model, rng)
        rows.extend(episode_rows)

    payload = {
        "config": args.config,
        "model": args.model or "",
        "seeds": seeds,
        "methods": args.methods,
        "rounds": args.rounds,
        "epsilon": args.epsilon,
        "summary": summarize(rows, args.rounds),
        "episodes": rows,
        "total_elapsed_sec": time.time() - t0,
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if args.summary_out:
        write_summary_md(Path(args.summary_out), payload)
    print(f"wrote {out_path}")
    if args.summary_out:
        print(f"wrote {args.summary_out}")
    print(f"\n=== final-round summary ===")
    for row in payload["summary"]["final"]:
        print(
            f"  {row['method']:<28s} top1={row['top1_accuracy_mean']:.3f}  "
            f"nll={row['nll_mean']:.3f}  brier={row['brier_mean']:.3f}"
        )


if __name__ == "__main__":
    main()
