"""LLM direct-dispatch smoke for MaaSSim common-state replay."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import sys
import uuid
from dataclasses import dataclass, replace
from itertools import combinations, permutations
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
for path in (ROOT, SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from llm_hpgg.llm_agent import backend_name, call_player, model_for

from llm_courier_dispatch.dispatch_env import ACCEPT, RULES
from llm_courier_dispatch_maassim.adapter import MaaSSimCandidateOffer, MaaSSimQueueSnapshot
from llm_courier_dispatch_maassim.hidden_rules import SyntheticRuleTracker, posterior_accept_probability, synthetic_action_for_type, synthetic_features
from llm_courier_dispatch_maassim.policies import MaaSSimRandomPolicy
from replay_maassim_pact_persona_mechanism import (
    ANALYSIS,
    FIG_DIRS,
    DRIVER_REJECT_PENALTY,
    LABELS as MECHANISM_LABELS,
    PASSENGER_REJECT_PENALTY,
    PACTReplayPolicy,
    accepted_utility,
    fake_traveller,
    init_trackers,
    load_personas,
    load_snapshots,
    mean,
    offer_dict,
    sem,
    wait_oracle,
)


CACHE_PATH = ANALYSIS / "maassim_llm_replay_cache.json"
METHOD_VERSION = "maassim-llm-direct-v7-scenarios"
SCENARIO = "normal"
CONFLICT_FAST_COUNT = 1
CONFLICT_RISKY_TRAVEL = 420.0
CONFLICT_SAFE_TRAVEL = 150.0
CONFLICT_SAFE_FARE_PER_SECOND = 0.012
CONFLICT_RISKY_FARE_PER_SECOND = 0.003
DEFAULT_POLICIES = ["nearest", "random", "pact", "llm", "oracle"]
LLM_POLICIES = {"llm", "llm_belief", "llm_psrl", "atom_tom0", "atom_tom1", "atom_adaptive_hedge", "econ_bne"}
LABELS = {
    **MECHANISM_LABELS,
    "llm": "LLM-PACT",
    "llm_belief": "LLM-belief",
    "llm_psrl": "LLM-PSRL",
    "atom_tom0": "A-ToM-0",
    "atom_tom1": "A-ToM-1",
    "atom_adaptive_hedge": "A-ToM-Hedge",
    "econ_bne": "ECON-BNE",
}
COLORS = {
    "nearest": "#8c8c8c",
    "random": "#555555",
    "pact": "#12345d",
    "llm": "#8a5fbf",
    "llm_belief": "#e08e45",
    "llm_psrl": "#7f5aa2",
    "atom_tom0": "#d4a04a",
    "atom_tom1": "#cc8242",
    "atom_adaptive_hedge": "#b8723d",
    "econ_bne": "#c0463f",
    "oracle": "#3d7b62",
}

BASELINE_INSTRUCTIONS = {
    "llm": "Use the provided assignment-level persona-aware scores as decision support. Prefer high estimated_utility; break ties by fewer expected driver rejects and then lower total_wait.",
    "llm_belief": "Infer likely driver constraints from the provided belief marginals and current public features, then choose the robust legal assignment. Do not use assignment-level estimated_utility unless it is explicitly provided.",
    "llm_psrl": "Use posterior-sampling-style verbal reasoning: rely on the sampled driver persona hypotheses as a plausible world model, then choose the legal assignment that is robust under that sampled hypothesis. Do not use assignment-level estimated_utility unless it is explicitly provided.",
    "atom_tom0": "Use zero-order theory of mind: predict driver responses from the current public candidate features only, without using history or numeric belief updates.",
    "atom_tom1": "Use first-order theory of mind: infer stable driver response patterns from public history, then choose strategically under those inferred patterns. Do not use hidden rule names as privileged truth.",
    "atom_adaptive_hedge": "Hedge between zero-order and first-order theory of mind: use public history only when it clearly improves robustness; otherwise prefer robust current features.",
    "econ_bne": "Use an economic best-response / Bayes-Nash-style heuristic: treat drivers as rational responders with private constraints and choose a stable assignment that likely avoids rejections.",
}


@dataclass
class SmokeStats:
    policy: str
    seed: int
    snapshots: int = 0
    assignments: int = 0
    served: int = 0
    driver_rejects: int = 0
    passenger_rejects: int = 0
    total_wait: float = 0.0
    realized_utility: float = 0.0
    exact_wait_oracle_matches: int = 0
    extra_wait: float = 0.0
    llm_calls: int = 0
    cache_hits: int = 0
    parse_successes: int = 0
    fallbacks: int = 0
    repair_calls: int = 0


class NearestPolicy:
    def choose_assignment(self, snapshot: MaaSSimQueueSnapshot) -> dict[int, int]:
        assignment: dict[int, int] = {}
        used_drivers: set[int] = set()
        used_requests: set[int] = set()
        for offer in sorted(snapshot.candidates, key=lambda item: (item.wait_time, item.driver_id, item.request_id)):
            if offer.driver_id in used_drivers or offer.request_id in used_requests:
                continue
            assignment[int(offer.driver_id)] = int(offer.request_id)
            used_drivers.add(int(offer.driver_id))
            used_requests.add(int(offer.request_id))
        return assignment


@dataclass
class MaaSSimLLMPolicy:
    tracker: SyntheticRuleTracker
    model: str
    cache: dict[str, str]
    baseline: str = "llm"
    max_tokens: int = 700
    temperature: float = 0.0
    prompt_variant: str = "scored"
    calls: int = 0
    cache_hits: int = 0
    parse_successes: int = 0
    fallbacks: int = 0
    repair_calls: int = 0

    def _rng_for_snapshot(self, snapshot: MaaSSimQueueSnapshot) -> np.random.Generator:
        seed_material = f"{self.baseline}|{snapshot.time}|{','.join(str(v) for v in snapshot.vehicle_queue)}|{','.join(str(v) for v in snapshot.request_queue)}"
        digest = hashlib.sha256(seed_material.encode("utf-8")).hexdigest()
        return np.random.default_rng(int(digest[:16], 16) % (2**32))

    def choose_assignment(self, snapshot: MaaSSimQueueSnapshot) -> dict[int, int]:
        payload = self._payload(snapshot)
        reply, cache_hit = self._call(payload)
        self.calls += 1
        self.cache_hits += int(cache_hit)
        parsed = parse_assignment(reply, snapshot)
        if not parsed.legal:
            repair_reply, _ = self._repair_call(payload, reply, parsed.reason)
            self.repair_calls += 1
            parsed = parse_assignment(repair_reply, snapshot)
        self.parse_successes += int(parsed.legal)
        if not parsed.legal:
            self.fallbacks += 1
        return fill_assignment(parsed.assignment, snapshot)

    def _call(self, payload: dict[str, object]) -> tuple[str, bool]:
        key = cache_key(self.model, payload)
        if key in self.cache:
            return self.cache[key], True
        system = (
            "You are a JSON API for a ride-hailing dispatch benchmark. "
            "You must choose exactly one row from legal_assignments. "
            "Do not invent or combine candidate IDs yourself. "
            f"Baseline policy instruction: {BASELINE_INSTRUCTIONS[self.baseline]} "
            "Return exactly one compact JSON object and no other text. "
            "Required schema: {\"assignment_id\": integer}. "
            "assignment_id must be one of the listed legal_assignments assignment_id values."
        )
        reply = call_player(system, json.dumps(payload, indent=2), model=self.model, max_tokens=self.max_tokens, temperature=self.temperature)
        self.cache[key] = reply
        save_cache(self.cache)
        return reply, False

    def _repair_call(self, payload: dict[str, object], bad_reply: str, reason: str) -> tuple[str, bool]:
        repair_payload = {
            "original_task": payload,
            "invalid_reply": bad_reply,
            "validation_error": reason,
            "required_output": "Return JSON only: {\"assignment_id\": integer}.",
        }
        key = cache_key(f"repair::{self.model}", repair_payload)
        if key in self.cache:
            return self.cache[key], True
        system = (
            "Repair an invalid dispatch API response. Return JSON only. "
            "Choose exactly one row from original_task.legal_assignments. "
            "Required schema: {\"assignment_id\": integer}."
        )
        reply = call_player(system, json.dumps(repair_payload, indent=2), model=self.model, max_tokens=300, temperature=0.0)
        self.cache[key] = reply
        save_cache(self.cache)
        return reply, False

    def _payload(self, snapshot: MaaSSimQueueSnapshot) -> dict[str, object]:
        candidates = []
        for idx, offer in enumerate(snapshot.candidates):
            features = synthetic_features(offer, self.tracker.config)
            candidates.append(
                {
                    "candidate_id": idx,
                    "driver_id": int(offer.driver_id),
                    "request_id": int(offer.request_id),
                    "wait_time": round(float(offer.wait_time), 3),
                    "travel_time": round(float(offer.travel_time), 3),
                    "fare": round(float(offer.fare), 3),
                    "persona_relevant_features": {
                        "long_trip": int(features["long_trip"]),
                        "far_pickup_or_leaves_zone": int(features["leaves_zone"]),
                        "home_ward": int(features["home_ward"]),
                        "surge": int(features["surge"]),
                        "after_deadline": int(features["after_deadline"]),
                    },
                }
            )
        drivers = []
        include_numeric_beliefs = self.baseline in {"llm", "llm_belief"}
        if include_numeric_beliefs:
            for driver_id in sorted({offer.driver_id for offer in snapshot.candidates}):
                marginals = self.tracker.posterior_for_driver(int(driver_id)).rule_marginals()
                drivers.append({"driver_id": int(driver_id), **{f"p_{name}": round(float(marginals[name]), 3) for name in RULES}})
        include_scores = self.baseline == "llm" and self.prompt_variant == "scored"
        legal_assignments = legal_assignment_options(snapshot, self.tracker if include_scores else None)
        sampled_hypotheses = sampled_persona_hypotheses(snapshot, self.tracker, self._rng_for_snapshot(snapshot)) if self.baseline == "llm_psrl" else []
        return {
            "time": round(float(snapshot.time), 3),
            "scenario": SCENARIO,
            "baseline": self.baseline,
            "prompt_variant": self.prompt_variant,
            "baseline_instruction": BASELINE_INSTRUCTIONS[self.baseline],
            "required_output": {
                "json_only": True,
                "schema": {"assignment_id": "integer"},
                "hard_rule": "assignment_id must be one of legal_assignments[].assignment_id",
            },
            "objective": {
                "primary": "maximize realized service utility under hidden driver personas",
                "serve_value": 3.0,
                "driver_reject_penalty": DRIVER_REJECT_PENALTY,
                "passenger_reject_penalty": PASSENGER_REJECT_PENALTY,
                "wait_penalty_per_second": 0.01,
                "assignment_scoring_note": "When legal_assignments include estimated_utility, prefer the largest value; it already combines service value, wait penalty, and learned driver rejection risk.",
                "assignment_count": min(len(set(offer.driver_id for offer in snapshot.candidates)), len(set(offer.request_id for offer in snapshot.candidates))),
            },
            "rule_semantics": {
                "avoid_long": "may reject long_trip offers",
                "zone_loyal": "may reject far-pickup/leaves-zone offers",
                "home_pull": "may reposition after deadline unless offer goes home_ward",
                "surge_only": "may reject non-surge offers",
            },
            "driver_persona_beliefs": drivers,
            "sampled_driver_persona_hypotheses": sampled_hypotheses,
            "public_history": public_history_payload(self.tracker) if self.baseline in {"llm_belief", "atom_tom1", "atom_adaptive_hedge", "econ_bne"} else [],
            "candidates": candidates,
            "legal_assignments": legal_assignments,
        }


@dataclass
class ParsedAssignment:
    assignment: dict[int, int]
    legal: bool
    reason: str = "ok"


def offer_risk_summary(offer: MaaSSimCandidateOffer, tracker: SyntheticRuleTracker) -> dict[str, object]:
    features = synthetic_features(offer, tracker.config)
    marginals = tracker.posterior_for_driver(int(offer.driver_id)).rule_marginals()
    risks = {
        "avoid_long": float(marginals["avoid_long"]) if int(features["long_trip"]) else 0.0,
        "zone_loyal": float(marginals["zone_loyal"]) if int(features["leaves_zone"]) else 0.0,
        "home_pull": float(marginals["home_pull"]) if int(features["after_deadline"]) and not int(features["home_ward"]) else 0.0,
        "surge_only": float(marginals["surge_only"]) if not int(features["surge"]) else 0.0,
    }
    top_rule, top_risk = max(risks.items(), key=lambda item: item[1])
    accept_prob = posterior_accept_probability(tracker.posterior_for_driver(int(offer.driver_id)), offer, tracker.config)
    return {
        "accept_prob": round(float(accept_prob), 3),
        "reject_prob": round(float(1.0 - accept_prob), 3),
        "top_reject_risk": top_rule if top_risk > 0 else "none",
        "top_reject_risk_prob": round(float(top_risk), 3),
    }


def public_history_payload(tracker: SyntheticRuleTracker, max_events: int = 12) -> list[dict[str, object]]:
    rows = tracker.rows[-max_events:]
    history = []
    for row in rows:
        history.append(
            {
                "time": round(float(row.get("time", 0.0) or 0.0), 3),
                "driver_id": int(row["driver_id"]),
                "request_id": int(row["request_id"]),
                "public_action": "accept" if int(row["action_code"]) == ACCEPT else "reject_or_reposition",
                "actual_declined": bool(row.get("actual_declined", False)),
                "long_trip": int(row["long_trip"]),
                "far_pickup_or_leaves_zone": int(row["leaves_zone"]),
                "home_ward": int(row["home_ward"]),
                "surge": int(row["surge"]),
                "wait_time": round(float(row["wait_time"]), 3),
                "travel_time": round(float(row["travel_time"]), 3),
                "fare": round(float(row["fare"]), 3),
            }
        )
    return history


def sampled_persona_hypotheses(snapshot: MaaSSimQueueSnapshot, tracker: SyntheticRuleTracker, rng: np.random.Generator) -> list[dict[str, object]]:
    hypotheses = []
    for driver_id in sorted({int(offer.driver_id) for offer in snapshot.candidates}):
        posterior = tracker.posterior_for_driver(driver_id)
        sampled = posterior.sample(rng)
        active_rules = [name for name, value in zip(RULES, sampled, strict=True) if int(value)]
        hypotheses.append(
            {
                "driver_id": driver_id,
                "sampled_active_constraints": active_rules or ["none"],
                "interpretation": {
                    "avoid_long": "may reject long_trip offers",
                    "zone_loyal": "may reject far-pickup/leaves-zone offers",
                    "home_pull": "may reposition after deadline unless offer goes home_ward",
                    "surge_only": "may reject non-surge offers",
                },
            }
        )
    return hypotheses


def legal_assignment_options(snapshot: MaaSSimQueueSnapshot, tracker: SyntheticRuleTracker | None = None) -> list[dict[str, object]]:
    offers = list(snapshot.candidates)
    if not offers:
        return []
    drivers = sorted({int(offer.driver_id) for offer in offers})
    requests = sorted({int(offer.request_id) for offer in offers})
    offer_by_pair = {(int(offer.driver_id), int(offer.request_id)): (idx, offer) for idx, offer in enumerate(offers)}
    match_count = min(len(drivers), len(requests))
    rows = []
    for driver_subset in combinations(range(len(drivers)), match_count):
        for request_perm in permutations(requests, match_count):
            pairs = []
            candidate_ids = []
            total_wait = 0.0
            total_travel = 0.0
            total_fare = 0.0
            expected_accepts = 0.0
            expected_driver_rejects = 0.0
            estimated_utility = 0.0
            risk_summaries = []
            legal = True
            for driver_idx, request_id in zip(driver_subset, request_perm, strict=True):
                driver_id = drivers[driver_idx]
                item = offer_by_pair.get((driver_id, request_id))
                if item is None:
                    legal = False
                    break
                candidate_id, offer = item
                candidate_ids.append(int(candidate_id))
                pairs.append({"driver_id": int(driver_id), "request_id": int(request_id), "candidate_id": int(candidate_id)})
                total_wait += float(offer.wait_time)
                total_travel += float(offer.travel_time)
                total_fare += float(offer.fare)
                if tracker is not None:
                    risk = offer_risk_summary(offer, tracker)
                    accept_prob = float(risk["accept_prob"])
                    expected_accepts += accept_prob
                    expected_driver_rejects += 1.0 - accept_prob
                    estimated_utility += accept_prob * accepted_utility(offer) - DRIVER_REJECT_PENALTY * (1.0 - accept_prob)
                    risk_summaries.append({"candidate_id": int(candidate_id), **risk})
            if legal:
                row = {
                    "candidate_ids": candidate_ids,
                    "pairs": pairs,
                    "total_wait": round(total_wait, 3),
                    "total_travel": round(total_travel, 3),
                    "total_fare": round(total_fare, 3),
                }
                if tracker is not None:
                    row.update(
                        {
                            "estimated_utility": round(float(estimated_utility), 3),
                            "expected_accepts": round(float(expected_accepts), 3),
                            "expected_driver_rejects": round(float(expected_driver_rejects), 3),
                            "risk_summaries": risk_summaries,
                        }
                    )
                rows.append(row)
    rows.sort(key=lambda row: (float(row["total_wait"]), tuple(int(value) for value in row["candidate_ids"])))
    for assignment_id, row in enumerate(rows):
        row["assignment_id"] = assignment_id
    if tracker is not None:
        ranked_ids = sorted(range(len(rows)), key=lambda idx: float(rows[idx].get("estimated_utility", float("-inf"))), reverse=True)
        for rank, row_idx in enumerate(ranked_ids, start=1):
            rows[row_idx]["estimated_utility_rank"] = rank
            rows[row_idx]["recommended_by_score"] = rank == 1
    return rows


def conflict_transform_snapshot(snapshot: MaaSSimQueueSnapshot) -> MaaSSimQueueSnapshot:
    risky_pairs: set[tuple[int, int]] = set()
    by_request: dict[int, list[MaaSSimCandidateOffer]] = {}
    for offer in snapshot.candidates:
        by_request.setdefault(int(offer.request_id), []).append(offer)
    for offers in by_request.values():
        for offer in sorted(offers, key=lambda item: (item.wait_time, item.driver_id))[:CONFLICT_FAST_COUNT]:
            risky_pairs.add((int(offer.driver_id), int(offer.request_id)))
    transformed = []
    for offer in snapshot.candidates:
        if (int(offer.driver_id), int(offer.request_id)) in risky_pairs:
            travel_time = max(float(offer.travel_time), CONFLICT_RISKY_TRAVEL)
            fare = min(float(offer.fare), travel_time * CONFLICT_RISKY_FARE_PER_SECOND)
        else:
            travel_time = min(float(offer.travel_time), CONFLICT_SAFE_TRAVEL)
            fare = max(float(offer.fare), travel_time * CONFLICT_SAFE_FARE_PER_SECOND)
        transformed.append(replace(offer, travel_time=travel_time, fare=fare))
    return MaaSSimQueueSnapshot(
        time=snapshot.time,
        vehicle_queue=snapshot.vehicle_queue,
        request_queue=snapshot.request_queue,
        candidates=tuple(transformed),
    )


def apply_scenario(snapshot: MaaSSimQueueSnapshot) -> MaaSSimQueueSnapshot:
    if SCENARIO == "normal":
        return snapshot
    if SCENARIO == "conflict_offer":
        return conflict_transform_snapshot(snapshot)
    raise ValueError(f"unknown scenario: {SCENARIO}")


def resolved_player_model(model_name: str | None) -> str:
    backend = backend_name("player")
    return model_for("player", backend, model_name)


def load_cache() -> dict[str, str]:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def save_cache(cache: dict[str, str]) -> None:
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    tmp_path = CACHE_PATH.with_suffix(f"{CACHE_PATH.suffix}.{uuid.uuid4().hex}.tmp")
    tmp_path.write_text(json.dumps(cache, indent=2), encoding="utf-8")
    tmp_path.replace(CACHE_PATH)


def cache_key(model: str, payload: dict[str, object]) -> str:
    raw = json.dumps(
        {
            "version": METHOD_VERSION,
            "backend": os.getenv("LLM_HPGG_BACKEND", "anthropic"),
            "offline": os.getenv("LLM_HPGG_OFFLINE", "0"),
            "model": model,
            "payload": payload,
        },
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def extract_json(text: str) -> dict[str, object]:
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if not match:
            return {}
        try:
            parsed = json.loads(match.group(0))
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}

def parse_assignment(reply: str, snapshot: MaaSSimQueueSnapshot) -> ParsedAssignment:
    parsed = extract_json(reply)
    offers = list(snapshot.candidates)
    if not parsed:
        return ParsedAssignment({}, False, "reply did not contain a JSON object")
    by_pair = {(int(offer.driver_id), int(offer.request_id)): offer for offer in offers}
    assignment: dict[int, int] = {}
    used_drivers: set[int] = set()
    used_requests: set[int] = set()
    invalid_reasons: list[str] = []

    if "assignment_id" in parsed:
        options = legal_assignment_options(snapshot)
        try:
            assignment_id = int(parsed["assignment_id"])
            selected = options[assignment_id]
        except Exception:
            return ParsedAssignment({}, False, f"assignment_id {parsed.get('assignment_id')!r} is not in legal_assignments")
        expected_candidate_ids = [int(value) for value in selected["candidate_ids"]]
        for candidate_id in expected_candidate_ids:
            offer = offers[candidate_id]
            assignment[int(offer.driver_id)] = int(offer.request_id)
        return ParsedAssignment(assignment, True, "ok")

    candidate_ids = parsed.get("candidate_ids") or parsed.get("candidates") or parsed.get("selected_candidate_ids")
    if isinstance(candidate_ids, list):
        for raw_idx in candidate_ids:
            try:
                candidate_id = int(raw_idx)
                offer = offers[candidate_id]
            except Exception:
                invalid_reasons.append(f"candidate_id {raw_idx!r} is not valid")
                continue
            driver_id = int(offer.driver_id)
            request_id = int(offer.request_id)
            if driver_id in used_drivers:
                invalid_reasons.append(f"driver_id {driver_id} is repeated")
                continue
            if request_id in used_requests:
                invalid_reasons.append(f"request_id {request_id} is repeated")
                continue
            assignment[driver_id] = request_id
            used_drivers.add(driver_id)
            used_requests.add(request_id)

    raw_assignment = parsed.get("assignment") or parsed.get("assignments")
    if not assignment and isinstance(raw_assignment, list):
        for item in raw_assignment:
            if not isinstance(item, dict):
                continue
            try:
                driver_id = int(item.get("driver_id"))
                request_id = int(item.get("request_id"))
            except Exception:
                invalid_reasons.append("assignment item missing integer driver_id/request_id")
                continue
            if (driver_id, request_id) not in by_pair:
                invalid_reasons.append(f"pair ({driver_id}, {request_id}) is not a candidate")
                continue
            if driver_id in used_drivers:
                invalid_reasons.append(f"driver_id {driver_id} is repeated")
                continue
            if request_id in used_requests:
                invalid_reasons.append(f"request_id {request_id} is repeated")
                continue
            assignment[driver_id] = request_id
            used_drivers.add(driver_id)
            used_requests.add(request_id)

    target = min(len({offer.driver_id for offer in offers}), len({offer.request_id for offer in offers}))
    if len(assignment) != target:
        invalid_reasons.append(f"expected {target} non-conflicting assignments, got {len(assignment)}")
    if not assignment:
        invalid_reasons.append("no usable candidate_ids or assignment list found")
    return ParsedAssignment(assignment, len(assignment) == target, "; ".join(invalid_reasons) if invalid_reasons else "ok")


def fill_assignment(assignment: dict[int, int], snapshot: MaaSSimQueueSnapshot) -> dict[int, int]:
    target = min(len({offer.driver_id for offer in snapshot.candidates}), len({offer.request_id for offer in snapshot.candidates}))
    if len(assignment) >= target:
        return assignment
    used_drivers = set(assignment)
    used_requests = set(assignment.values())
    repaired = dict(assignment)
    for offer in sorted(snapshot.candidates, key=lambda item: (item.wait_time, item.driver_id, item.request_id)):
        driver_id = int(offer.driver_id)
        request_id = int(offer.request_id)
        if driver_id in used_drivers or request_id in used_requests:
            continue
        repaired[driver_id] = request_id
        used_drivers.add(driver_id)
        used_requests.add(request_id)
        if len(repaired) >= target:
            break
    return repaired


def parse_csv(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def policy_label(policy: str, prompt_variant: str) -> str:
    if policy == "llm":
        return "LLM-PACT" if prompt_variant == "scored" else "LLM-basic"
    return LABELS[policy]


def build_policy(policy_name: str, seed: int, tracker: SyntheticRuleTracker, model: str, cache: dict[str, str], max_tokens: int, temperature: float, prompt_variant: str) -> Any:
    if policy_name == "nearest":
        return NearestPolicy()
    if policy_name == "random":
        return MaaSSimRandomPolicy(rng_seed=seed)
    if policy_name == "pact":
        return PACTReplayPolicy(tracker, reject_penalty=DRIVER_REJECT_PENALTY)
    if policy_name == "oracle":
        return PACTReplayPolicy(tracker, oracle=True, reject_penalty=DRIVER_REJECT_PENALTY)
    if policy_name in LLM_POLICIES:
        return MaaSSimLLMPolicy(tracker=tracker, model=model, cache=cache, baseline=policy_name, max_tokens=max_tokens, temperature=temperature, prompt_variant=prompt_variant)
    raise ValueError(policy_name)


def active_snapshots(seed: int, max_snapshots: int | None) -> list[MaaSSimQueueSnapshot]:
    snapshots = [apply_scenario(snapshot) for snapshot in load_snapshots(seed) if snapshot.candidates]
    if max_snapshots is not None:
        return snapshots[: int(max_snapshots)]
    return snapshots


def evaluate_policy_seed(policy_name: str, seed: int, model: str, cache: dict[str, str], max_snapshots: int | None, max_tokens: int, temperature: float, prompt_variant: str) -> SmokeStats:
    personas = load_personas(seed)
    snapshots = active_snapshots(seed, max_snapshots)
    driver_tracker, passenger_tracker = init_trackers(seed, personas)
    policy = build_policy(policy_name, seed, driver_tracker, model, cache, max_tokens, temperature, prompt_variant)
    stats = SmokeStats(policy=policy_name, seed=seed)
    for snapshot in snapshots:
        oracle_assignment = wait_oracle(snapshot)
        assignment = policy.choose_assignment(snapshot)
        if not assignment:
            continue
        stats.snapshots += 1
        if assignment == oracle_assignment:
            stats.exact_wait_oracle_matches += 1
        offer_by_pair = {(offer.driver_id, offer.request_id): offer for offer in snapshot.candidates}
        oracle_wait = sum(offer_by_pair[(driver_id, request_id)].wait_time for driver_id, request_id in oracle_assignment.items())
        policy_wait = sum(offer_by_pair[(driver_id, request_id)].wait_time for driver_id, request_id in assignment.items() if (driver_id, request_id) in offer_by_pair)
        stats.extra_wait += policy_wait - oracle_wait
        for driver_id, request_id in assignment.items():
            offer = offer_by_pair.get((driver_id, request_id))
            if offer is None:
                continue
            stats.assignments += 1
            action, reason = synthetic_action_for_type(driver_tracker.type_for_driver(driver_id), offer, driver_tracker.config)
            driver_reject = action != ACCEPT
            driver_tracker._update_posterior(offer, action, reason, driver_reject, driver_reject)
            if driver_reject:
                stats.driver_rejects += 1
                stats.realized_utility -= DRIVER_REJECT_PENALTY
                continue
            traveller = fake_traveller(request_id, offer)
            offer_payload = offer_dict(offer)
            passenger_reject, passenger_reason = passenger_tracker.reject_for_type(passenger_tracker.type_for_passenger(request_id), traveller, offer_payload)
            passenger_tracker._update_posterior(request_id, traveller, offer_payload, passenger_reject, passenger_reason)
            if passenger_reject:
                stats.passenger_rejects += 1
                stats.realized_utility -= PASSENGER_REJECT_PENALTY
                continue
            stats.served += 1
            stats.total_wait += float(offer.wait_time)
            stats.realized_utility += accepted_utility(offer)
    if isinstance(policy, MaaSSimLLMPolicy):
        stats.llm_calls = policy.calls
        stats.cache_hits = policy.cache_hits
        stats.parse_successes = policy.parse_successes
        stats.fallbacks = policy.fallbacks
        stats.repair_calls = policy.repair_calls
    return stats


def aggregate(stats: list[SmokeStats], policies: list[str], prompt_variant: str) -> list[dict[str, object]]:
    rows = []
    for policy in policies:
        group = [stat for stat in stats if stat.policy == policy]
        if not group:
            continue
        row: dict[str, object] = {"policy": policy, "label": policy_label(policy, prompt_variant), "seeds": len(group)}
        metrics = {
            "snapshots": [stat.snapshots for stat in group],
            "assignments": [stat.assignments for stat in group],
            "served": [stat.served for stat in group],
            "driver_rejects": [stat.driver_rejects for stat in group],
            "passenger_rejects": [stat.passenger_rejects for stat in group],
            "driver_accept_rate": [(stat.assignments - stat.driver_rejects) / max(stat.assignments, 1) for stat in group],
            "realized_utility": [stat.realized_utility for stat in group],
            "extra_wait_per_snapshot": [stat.extra_wait / max(stat.snapshots, 1) for stat in group],
            "oracle_match_rate": [stat.exact_wait_oracle_matches / max(stat.snapshots, 1) for stat in group],
            "llm_parse_rate": [stat.parse_successes / max(stat.llm_calls, 1) if stat.policy in LLM_POLICIES else float("nan") for stat in group],
            "llm_fallback_rate": [stat.fallbacks / max(stat.llm_calls, 1) if stat.policy in LLM_POLICIES else float("nan") for stat in group],
            "llm_repair_rate": [stat.repair_calls / max(stat.llm_calls, 1) if stat.policy in LLM_POLICIES else float("nan") for stat in group],
            "llm_cache_rate": [stat.cache_hits / max(stat.llm_calls, 1) if stat.policy in LLM_POLICIES else float("nan") for stat in group],
        }
        for key, values in metrics.items():
            numeric = [float(value) for value in values]
            valid = [value for value in numeric if not math.isnan(value)]
            row[key] = mean(valid) if valid else float("nan")
            row[f"{key}_sem"] = sem(valid) if valid else 0.0
        rows.append(row)
    return rows


def fmt(value: object, digits: int = 2) -> str:
    numeric = float(value)
    if math.isnan(numeric):
        return "n/a"
    return f"{numeric:.{digits}f}"


def write_outputs(summary: list[dict[str, object]], out_prefix: str, model: str, seeds: int, max_snapshots: int | None, prompt_variant: str) -> None:
    csv_path = ANALYSIS / f"{out_prefix}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        writer.writerows(summary)
    lines = [
        "# MaaSSim LLM Common-State Smoke",
        "",
        f"Model: `{model}`. Prompt variant: `{prompt_variant}`. Seeds: `{seeds}`. Max active snapshots per seed: `{max_snapshots if max_snapshots is not None else 'all'}`.",
        f"Scenario: `{SCENARIO}`.",
        f"Utility penalties: driver_reject_penalty=`{DRIVER_REJECT_PENALTY}`, passenger_reject_penalty=`{PASSENGER_REJECT_PENALTY}`.",
        "",
        "LLM-family policies see a legal one-to-one assignment menu plus method-specific public, belief, history, or score context, then return JSON with `assignment_id` and copied `candidate_ids`.",
        "",
        "| Policy | Utility | Served | Driver rejects | Driver accept | Extra wait/snapshot | Oracle-match | LLM parse | LLM repair | LLM fallback |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(
            "| {label} | {utility} +/- {utility_sem} | {served} | {drej} | {accept} | {extra} | {match} | {parse} | {repair} | {fallback} |".format(
                label=row["label"],
                utility=fmt(row["realized_utility"]),
                utility_sem=fmt(row["realized_utility_sem"]),
                served=fmt(row["served"], 1),
                drej=fmt(row["driver_rejects"], 1),
                accept=fmt(row["driver_accept_rate"], 3),
                extra=fmt(row["extra_wait_per_snapshot"]),
                match=fmt(row["oracle_match_rate"], 3),
                parse=fmt(row["llm_parse_rate"], 3),
                repair=fmt(row["llm_repair_rate"], 3),
                fallback=fmt(row["llm_fallback_rate"], 3),
            )
        )
    (ANALYSIS / f"{out_prefix}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    plot_summary(summary, out_prefix)


def plot_summary(summary: list[dict[str, object]], out_prefix: str) -> None:
    labels = [str(row["label"]) for row in summary]
    colors = [COLORS[str(row["policy"])] for row in summary]
    x = np.arange(len(summary))
    fig, axes = plt.subplots(1, 3, figsize=(10.8, 3.2))
    specs = [("realized_utility", "Utility"), ("served", "Served"), ("driver_rejects", "Driver rejects")]
    for axis, (metric, ylabel) in zip(axes, specs, strict=True):
        values = [float(row[metric]) for row in summary]
        errors = [float(row.get(f"{metric}_sem", 0.0)) for row in summary]
        axis.bar(x, values, yerr=errors, color=colors, edgecolor="white", linewidth=0.8, capsize=2.5)
        axis.set_xticks(x)
        axis.set_xticklabels(labels, rotation=25, ha="right")
        axis.set_ylabel(ylabel)
        axis.grid(axis="y", linestyle=":", linewidth=0.55, color="#dddddd")
        for spine in ("top", "right"):
            axis.spines[spine].set_visible(False)
    fig.suptitle("MaaSSim LLM common-state smoke", x=0.02, y=1.02, ha="left", fontsize=12, fontweight="semibold")
    fig.tight_layout()
    for out_dir in FIG_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_dir / f"fig_{out_prefix}.png", bbox_inches="tight", facecolor="white")
        fig.savefig(out_dir / f"fig_{out_prefix}.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    global DRIVER_REJECT_PENALTY, PASSENGER_REJECT_PENALTY, SCENARIO, CONFLICT_FAST_COUNT
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=1)
    parser.add_argument("--max-snapshots", type=int, default=12)
    parser.add_argument("--model", default=None)
    parser.add_argument("--max-tokens", type=int, default=700)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--prompt-variant", choices=["basic", "scored"], default="scored")
    parser.add_argument("--policies", default=",".join(DEFAULT_POLICIES))
    parser.add_argument("--scenario", choices=["normal", "conflict_offer"], default="normal")
    parser.add_argument("--conflict-fast-count", type=int, default=CONFLICT_FAST_COUNT)
    parser.add_argument("--driver-reject-penalty", type=float, default=DRIVER_REJECT_PENALTY)
    parser.add_argument("--passenger-reject-penalty", type=float, default=PASSENGER_REJECT_PENALTY)
    parser.add_argument("--out-prefix", default="maassim_llm_replay_smoke")
    args = parser.parse_args()

    SCENARIO = args.scenario
    CONFLICT_FAST_COUNT = int(args.conflict_fast_count)
    DRIVER_REJECT_PENALTY = float(args.driver_reject_penalty)
    PASSENGER_REJECT_PENALTY = float(args.passenger_reject_penalty)

    model = resolved_player_model(args.model)
    cache = load_cache()
    policies = parse_csv(args.policies)
    stats = []
    for policy in policies:
        for seed in range(args.seeds):
            print(f"=== MaaSSim LLM replay policy={policy} seed={seed} variant={args.prompt_variant} ===", flush=True)
            stats.append(evaluate_policy_seed(policy, seed, model, cache, args.max_snapshots, args.max_tokens, args.temperature, args.prompt_variant))
    summary = aggregate(stats, policies, args.prompt_variant)
    write_outputs(summary, args.out_prefix, model, args.seeds, args.max_snapshots, args.prompt_variant)
    print(
        json.dumps(
            {
                "rows": len(stats),
                "summary_rows": len(summary),
                "model": model,
                "scenario": SCENARIO,
                "prompt_variant": args.prompt_variant,
                "driver_reject_penalty": DRIVER_REJECT_PENALTY,
                "passenger_reject_penalty": PASSENGER_REJECT_PENALTY,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()