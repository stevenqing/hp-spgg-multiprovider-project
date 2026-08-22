"""Small live-LLM probe for HP-SPGG-COM communication decisions.

This is Layer B-lite: it does not require token logprobs. Instead, it asks the
configured LLM backend to make explicit reveal/no-reveal decisions from the same
abstract HP-SPGG-COM setting, then evaluates those decisions with the analytic
model. Use a tiny grid by default to keep live calls cheap.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_hpgg.llm_agent import backend_name, call_player, model_for  # noqa: E402
from llm_hpgg_com.hp_spgg_com import (  # noqa: E402
    evaluate_closed_form,
    full_comm_policy,
    make_model,
    no_comm_policy,
    optimal_reveal_for_profile,
    pact_local_policy,
    value_for_realized_policy,
)


OUT_DIR = ROOT / "analysis" / "hp_spgg_com"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CACHE_PATH = OUT_DIR / "hp_spgg_com_live_cache.json"


def extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def resolved_player_model(model_name: str | None) -> str:
    backend = backend_name("player")
    return model_for("player", backend, model_name)


def cache_key(payload: dict, model_name: str | None) -> str:
    raw = json.dumps(
        {
            "backend": os.getenv("LLM_HPGG_BACKEND", "anthropic"),
            "offline": os.getenv("LLM_HPGG_OFFLINE", "0"),
            "model": resolved_player_model(model_name),
            "payload": payload,
            "version": "live-probe-v3-repeats",
        },
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def llm_reveal_decision(payload: dict, model_name: str | None, cache: dict[str, str]) -> tuple[bool, str]:
    key = cache_key(payload, model_name)
    if key not in cache:
        system = (
            "You are a careful cooperative multi-agent communication policy. "
            "Return valid JSON only."
        )
        user = json.dumps(payload, indent=2)
        cache[key] = call_player(system, user, model=model_name, max_tokens=140, temperature=0.2)
        CACHE_PATH.write_text(json.dumps(cache, indent=2), encoding="utf-8")
    reply = cache[key]
    try:
        parsed = extract_json(reply)
        reveal = bool(parsed.get("reveal_type", parsed.get("reveal", False)))
    except Exception:
        reveal = "reveal" in reply.lower() and "no" not in reply.lower()[:30]
    return reveal, reply


def call_payload(payload: dict, model_name: str | None) -> tuple[str, str]:
    key = cache_key(payload, model_name)
    system = (
        "You are a careful cooperative multi-agent communication policy. "
        "Return valid JSON only."
    )
    user = json.dumps(payload, indent=2)
    reply = call_player(system, user, model=model_name, max_tokens=140, temperature=0.2)
    return key, reply


def build_payload(*, rho: float, cost: float, theta_profile: tuple[int, ...], agent: int, repeat: int) -> dict:
    own_type = theta_profile[agent]
    return {
        "task": "HP-SPGG-COM one-shot communication decision",
        "agent_index": agent,
        "own_type": int(own_type),
        "type_meaning": {
            "0": "low-need/low-impact persona; partners gain moderate value from matching it",
            "1": "high-need/high-impact persona; partners gain high value from matching it",
        },
        "team_setting": "cooperative shared reward",
        "identifiability_rho": rho,
        "identifiability_explanation": (
            "rho=0 means domain actions give no useful cue about type; "
            "rho=1 means domain actions reveal type almost perfectly."
        ),
        "communication_cost": cost,
        "replicate_index": repeat,
        "replicate_instruction": "Use replicate_index only to break ties; do not mention it.",
        "decision": "Reveal your own type now, or stay silent and let partners infer from noisy action cues.",
        "response_schema": {"reveal_type": "boolean", "reason": "short"},
        "instruction": "Return only JSON matching the response_schema.",
    }


def all_payloads(args: argparse.Namespace) -> list[dict]:
    payloads: list[dict] = []
    theta_profiles = [(0, 0), (0, 1), (1, 0), (1, 1)]
    for rho in args.rhos:
        for cost in args.costs:
            for theta_profile in theta_profiles:
                for repeat in range(args.repeats):
                    for agent in range(2):
                        payloads.append(build_payload(rho=rho, cost=cost, theta_profile=theta_profile, agent=agent, repeat=repeat))
    return payloads


def prefill_cache(args: argparse.Namespace, cache: dict[str, str]) -> None:
    missing: dict[str, dict] = {}
    for payload in all_payloads(args):
        key = cache_key(payload, args.model)
        if key not in cache:
            missing[key] = payload
    if not missing:
        return
    print(f"prefill_missing_calls={len(missing)} concurrency={args.concurrency}", flush=True)
    completed = 0
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as executor:
        futures = [executor.submit(call_payload, payload, args.model) for payload in missing.values()]
        for future in as_completed(futures):
            key, reply = future.result()
            cache[key] = reply
            completed += 1
            if completed % 10 == 0 or completed == len(futures):
                CACHE_PATH.write_text(json.dumps(cache, indent=2), encoding="utf-8")
                print(f"prefill_completed={completed}/{len(futures)}", flush=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def run_probe(args: argparse.Namespace) -> dict:
    if CACHE_PATH.exists():
        cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    else:
        cache = {}
    prefill_cache(args, cache)
    rows = []
    theta_profiles = [(0, 0), (0, 1), (1, 0), (1, 1)]
    for rho in args.rhos:
        for cost in args.costs:
            model = make_model(n=2, type_count=2, identifiability=rho, comm_cost=cost, coupling=1.0)
            pact_policy = pact_local_policy(model)
            analytic = {
                "NO_COMM": evaluate_closed_form(model, no_comm_policy(model)),
                "FULL_COMM": evaluate_closed_form(model, full_comm_policy(model)),
                "PACT_LOCAL": evaluate_closed_form(model, pact_policy),
            }
            for theta_profile in theta_profiles:
                for repeat in range(args.repeats):
                    reveal = []
                    replies = []
                    for agent in range(model.n):
                        payload = build_payload(rho=rho, cost=cost, theta_profile=theta_profile, agent=agent, repeat=repeat)
                        flag, reply = llm_reveal_decision(payload, args.model, cache)
                        reveal.append(flag)
                        replies.append(reply)
                    reveal_tuple = tuple(reveal)
                    pact_reveal = tuple(pact_policy.reveals(agent, theta_profile[agent]) for agent in range(model.n))
                    opt_reveal = optimal_reveal_for_profile(model, theta_profile)
                    rows.append(
                        {
                            "rho": rho,
                            "comm_cost": cost,
                            "theta_profile": list(theta_profile),
                            "repeat": repeat,
                            "llm_reveal": list(reveal_tuple),
                            "pact_local_reveal": list(pact_reveal),
                            "profile_optimal_reveal": list(opt_reveal),
                            "llm_value": value_for_realized_policy(model, theta_profile, reveal_tuple),
                            "pact_local_value": value_for_realized_policy(model, theta_profile, pact_reveal),
                            "profile_optimal_value": value_for_realized_policy(model, theta_profile, opt_reveal),
                            "llm_matches_pact": reveal_tuple == pact_reveal,
                            "llm_matches_profile_opt": reveal_tuple == opt_reveal,
                            "replies": replies,
                            "analytic_expected_values": analytic,
                        }
                    )
    matches = [row["llm_matches_pact"] for row in rows]
    opt_matches = [row["llm_matches_profile_opt"] for row in rows]
    mean_gap = sum(row["profile_optimal_value"] - row["llm_value"] for row in rows) / max(len(rows), 1)
    payload = {
        "backend": os.getenv("LLM_HPGG_BACKEND", "anthropic"),
        "model": resolved_player_model(args.model),
        "repeats": args.repeats,
        "rhos": args.rhos,
        "costs": args.costs,
        "rows": rows,
        "summary": {
            "n_rows": len(rows),
            "llm_matches_pact_rate": sum(matches) / max(len(matches), 1),
            "llm_matches_profile_opt_rate": sum(opt_matches) / max(len(opt_matches), 1),
            "mean_profile_opt_minus_llm_value": mean_gap,
        },
    }
    out = OUT_DIR / args.out
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def parse_float_list(raw: str) -> list[float]:
    return [float(x.strip()) for x in raw.split(",") if x.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rhos", type=parse_float_list, default=[0.0, 0.8])
    parser.add_argument("--costs", type=parse_float_list, default=[0.05, 0.35])
    parser.add_argument("--model", default=None)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--concurrency", type=int, default=6)
    parser.add_argument("--out", default="hp_spgg_com_live_probe.json")
    args = parser.parse_args()
    payload = run_probe(args)
    print(json.dumps(payload["summary"], indent=2))
    print(f"OK: {OUT_DIR / args.out}")


if __name__ == "__main__":
    main()