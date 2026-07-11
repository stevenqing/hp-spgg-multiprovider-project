"""Run a MaaSSim shadow-matching smoke with CourierDispatch adapter logging.

This script does not change MaaSSim's default matching outcome. It wraps
MaaSSim's platform ``f_match`` function, records queue snapshots for the future
PACT adapter, then delegates to MaaSSim's default matcher.
"""

from __future__ import annotations

import argparse
import json
import logging
import random
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

from llm_courier_dispatch_maassim.adapter import MaaSSimQueueSnapshot, make_controlled_match_function, make_shadow_match_function
from llm_courier_dispatch_maassim.hidden_rules import SyntheticRuleConfig, SyntheticRuleTracker
from llm_courier_dispatch_maassim.personas import PassengerPersonaConfig, PassengerPersonaTracker
from llm_courier_dispatch_maassim.policies import MaaSSimKpiPolicy, MaaSSimNearestPolicy, MaaSSimPactShadowPolicy, MaaSSimRandomPolicy


ROOT = Path(__file__).resolve().parents[1]


class JsonlShadowPolicy:
    def __init__(self, path: Path, policy_name: str = "snapshot", dispatch_policy: Any | None = None) -> None:
        self.path = path
        self.count = 0
        self.policy_name = policy_name
        self.policy = dispatch_policy
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("", encoding="utf-8")

    def choose_assignment(self, snapshot: MaaSSimQueueSnapshot) -> dict[int, int]:
        assignment = self.policy.choose_assignment(snapshot) if self.policy is not None else {}
        record = asdict(snapshot)
        record["candidate_count"] = len(snapshot.candidates)
        record["policy"] = self.policy_name
        record["shadow_assignment"] = assignment
        if self.policy is not None:
            record["policy_diagnostics"] = self.policy.last_diagnostics
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, default=str) + "\n")
        self.count += 1
        return assignment


def import_maassim_modules() -> tuple[Any, Any]:
    try:
        from MaaSSim import simulators  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "MaaSSim is not installed in this environment. Clone/install https://github.com/RafalKucharskiPK/MaaSSim "
            "and rerun this script."
        ) from exc
    return simulators, logging


def build_maassim_inputs(args: argparse.Namespace) -> dict[str, object]:
    if args.batch_time is None and args.n_passengers is None and args.n_vehicles is None:
        kwargs: dict[str, object] = {"config": args.config}
        if args.root_path:
            kwargs["root_path"] = args.root_path
        return kwargs

    from MaaSSim.data_structures import structures  # type: ignore
    from MaaSSim.utils import empty_series, get_config, initialize_df  # type: ignore

    params = get_config(args.config, root_path=args.root_path)
    if args.n_passengers is not None:
        params.nP = int(args.n_passengers)
    if args.n_vehicles is not None:
        params.nV = int(args.n_vehicles)
    in_data = structures.copy()
    if args.batch_time is not None:
        in_data.platforms = initialize_df(in_data.platforms)
        in_data.platforms.loc[0] = empty_series(in_data.platforms)
        in_data.platforms.fare = [1]
        in_data.platforms.batch_time = [int(args.batch_time)]
    return {"params": params, "inData": in_data}


def summarize_maassim_result(sim: Any) -> dict[str, object]:
    if sim is None or not getattr(sim, "run_ids", None):
        return {}
    run_id = sim.run_ids[-1]
    result = sim.res[run_id]
    summary: dict[str, object] = {"run_id": run_id}
    pax_exp = getattr(result, "pax_exp", None)
    veh_exp = getattr(result, "veh_exp", None)
    if pax_exp is not None:
        summary["pax_count"] = int(getattr(pax_exp, "shape", [0])[0])
        for column in ["WAIT", "TRAVEL", "LOS", "OPENS_APP", "ARRIVES_AT_DEST", "PREFERS_OTHER_SERVICE", "LOSES_PATIENCE"]:
            if column in pax_exp.columns:
                summary[f"pax_{column.lower()}_sum"] = float(pax_exp[column].sum())
                summary[f"pax_{column.lower()}_mean"] = float(pax_exp[column].mean())
    if veh_exp is not None:
        summary["veh_count"] = int(getattr(veh_exp, "shape", [0])[0])
        for column in ["nRIDES", "nREJECTS", "nREJECTED", "REVENUE", "IDLE", "TRAVEL", "CRUISE"]:
            if column in veh_exp.columns:
                summary[f"veh_{column.lower()}_sum"] = float(veh_exp[column].sum())
                summary[f"veh_{column.lower()}_mean"] = float(veh_exp[column].mean())
    return summary


def build_policy(
    policy_name: str,
    beta: float,
    seed: int,
    posterior_source: Any | None = None,
    *,
    kpi_wait_weight: float = 0.01,
    kpi_travel_weight: float = 0.0,
    kpi_fare_weight: float = 1.0,
    kpi_reject_penalty: float = 2.0,
) -> Any | None:
    if policy_name == "snapshot":
        return None
    if policy_name == "nearest":
        return MaaSSimNearestPolicy()
    if policy_name == "random":
        return MaaSSimRandomPolicy(rng_seed=seed)
    if policy_name == "pact_proxy":
        return MaaSSimPactShadowPolicy(beta=0.0, rng_seed=seed, posterior_source=posterior_source)
    if policy_name == "pact_plus_proxy":
        return MaaSSimPactShadowPolicy(beta=beta, rng_seed=seed, posterior_source=posterior_source)
    if policy_name in {"pact", "pact_kpi"}:
        return MaaSSimKpiPolicy(
            posterior_source=posterior_source,
            wait_weight=kpi_wait_weight,
            travel_weight=kpi_travel_weight,
            fare_weight=kpi_fare_weight,
            reject_penalty=kpi_reject_penalty,
        )
    if policy_name in {"pact_plus", "pact_plus_kpi"}:
        return MaaSSimKpiPolicy(
            posterior_source=posterior_source,
            wait_weight=kpi_wait_weight,
            travel_weight=kpi_travel_weight,
            fare_weight=kpi_fare_weight,
            reject_penalty=kpi_reject_penalty + beta,
        )
    if policy_name in {"oracle", "oracle_kpi"}:
        return MaaSSimKpiPolicy(
            posterior_source=posterior_source,
            oracle=True,
            wait_weight=kpi_wait_weight,
            travel_weight=kpi_travel_weight,
            fare_weight=kpi_fare_weight,
            reject_penalty=kpi_reject_penalty,
        )
    raise ValueError(f"unknown policy: {policy_name}")


def export_maassim_run_tables(sim: Any, rides_out: Path, trips_out: Path) -> dict[str, object]:
    if sim is None or not getattr(sim, "run_ids", None):
        return {"rides_rows": 0, "trips_rows": 0}
    run_id = sim.run_ids[-1]
    run = sim.runs[run_id]
    rides_out.parent.mkdir(parents=True, exist_ok=True)
    trips_out.parent.mkdir(parents=True, exist_ok=True)
    run.rides.to_csv(rides_out, index=False)
    run.trips.to_csv(trips_out, index=False)
    return {"rides_rows": int(run.rides.shape[0]), "trips_rows": int(run.trips.shape[0]), "rides_out": str(rides_out.relative_to(ROOT)), "trips_out": str(trips_out.relative_to(ROOT))}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="glance.json", help="MaaSSim config path or package config name")
    parser.add_argument("--root-path", default=None, help="Root path for relative MaaSSim data paths")
    parser.add_argument("--n-passengers", type=int, default=None)
    parser.add_argument("--n-vehicles", type=int, default=None)
    parser.add_argument("--batch-time", type=int, default=None, help="If set, use MaaSSim batch matching every N seconds")
    parser.add_argument("--out", default="analysis/courier_dispatch_maassim/shadow_queue_snapshots.jsonl")
    parser.add_argument(
        "--policy",
        choices=["snapshot", "nearest", "random", "pact", "pact_plus", "oracle", "pact_proxy", "pact_plus_proxy", "pact_kpi", "pact_plus_kpi", "oracle_kpi"],
        default="snapshot",
    )
    parser.add_argument("--beta", type=float, default=0.25)
    parser.add_argument("--control-match", action="store_true", help="Use policy-controlled MaaSSim matching instead of delegating to default f_match")
    parser.add_argument("--synthetic-rules", action="store_true", help="Inject synthetic hidden driver rules through f_driver_decline")
    parser.add_argument("--intervene-driver-rules", action="store_true", help="Let synthetic rules control actual MaaSSim driver decline decisions")
    parser.add_argument("--posterior-out", default="analysis/courier_dispatch_maassim/synthetic_rule_posterior.csv")
    parser.add_argument("--passenger-personas", action="store_true")
    parser.add_argument("--passenger-posterior-out", default="analysis/courier_dispatch_maassim/passenger_persona_posterior.csv")
    parser.add_argument("--passenger-impatient-wait-ratio", type=float, default=0.85)
    parser.add_argument("--passenger-price-sensitive-fare", type=float, default=2.25)
    parser.add_argument("--passenger-delay-sensitive-total-ratio", type=float, default=2.25)
    parser.add_argument("--persona-assignment", choices=["cycle", "random"], default="cycle")
    parser.add_argument("--persona-out", default="analysis/courier_dispatch_maassim/persona_config.json")
    parser.add_argument("--rides-out", default="analysis/courier_dispatch_maassim/controlled_synthetic_rides.csv")
    parser.add_argument("--trips-out", default="analysis/courier_dispatch_maassim/controlled_synthetic_trips.csv")
    parser.add_argument("--summary-out", default=None)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--long-trip-seconds", type=float, default=300.0)
    parser.add_argument("--far-pickup-seconds", type=float, default=180.0)
    parser.add_argument("--surge-fare-per-second", type=float, default=0.006)
    parser.add_argument("--home-after-seconds", type=float, default=2700.0)
    parser.add_argument("--kpi-wait-weight", type=float, default=0.01)
    parser.add_argument("--kpi-travel-weight", type=float, default=0.0)
    parser.add_argument("--kpi-fare-weight", type=float, default=1.0)
    parser.add_argument("--kpi-reject-penalty", type=float, default=2.0)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    simulators, logging_module = import_maassim_modules()
    if args.check_only:
        print(json.dumps({"maassim_available": True}))
        return

    out_path = ROOT / args.out
    random.seed(args.seed)
    np.random.seed(args.seed)
    rule_config = SyntheticRuleConfig(
        long_trip_seconds=args.long_trip_seconds,
        far_pickup_seconds=args.far_pickup_seconds,
        surge_fare_per_second=args.surge_fare_per_second,
        home_after_seconds=args.home_after_seconds,
    )
    tracker = SyntheticRuleTracker(
        ROOT / args.posterior_out,
        intervene=args.intervene_driver_rules,
        seed=args.seed,
        assignment_mode=args.persona_assignment,
        config=rule_config,
    ) if args.synthetic_rules else None
    passenger_tracker = (
        PassengerPersonaTracker(
            ROOT / args.passenger_posterior_out,
            config=PassengerPersonaConfig(
                impatient_wait_ratio=args.passenger_impatient_wait_ratio,
                price_sensitive_fare=args.passenger_price_sensitive_fare,
                delay_sensitive_total_ratio=args.passenger_delay_sensitive_total_ratio,
            ),
            seed=args.seed,
            assignment_mode=args.persona_assignment,
        )
        if args.passenger_personas
        else None
    )
    dispatch_policy = build_policy(
        args.policy,
        args.beta,
        args.seed,
        posterior_source=tracker,
        kpi_wait_weight=args.kpi_wait_weight,
        kpi_travel_weight=args.kpi_travel_weight,
        kpi_fare_weight=args.kpi_fare_weight,
        kpi_reject_penalty=args.kpi_reject_penalty,
    )
    policy = JsonlShadowPolicy(out_path, policy_name=args.policy, dispatch_policy=dispatch_policy)
    match_function = make_controlled_match_function(policy) if args.control_match else make_shadow_match_function(policy)
    kwargs: dict[str, object] = build_maassim_inputs(args)
    kwargs.update({"f_match": match_function, "logger_level": logging_module.WARNING})
    if args.batch_time is not None:
        kwargs["event_based"] = False
    if tracker is not None:
        kwargs["f_driver_decline"] = tracker.decline_function
    if passenger_tracker is not None:
        kwargs["f_trav_mode"] = passenger_tracker.mode_choice_function
    if args.root_path:
        kwargs["root_path"] = args.root_path
    sim = None
    try:
        sim = simulators.simulate(**kwargs)
    finally:
        if tracker is not None:
            tracker.write_csv()
        if passenger_tracker is not None:
            passenger_tracker.write_csv()
    posterior_summary: dict[str, object] | None = None
    if tracker is not None:
        posterior_summary = tracker.summary()
    passenger_summary: dict[str, object] | None = None
    if passenger_tracker is not None:
        passenger_summary = passenger_tracker.summary()
    persona_payload = {
        "seed": args.seed,
        "persona_assignment": args.persona_assignment,
        "driver_personas": tracker.persona_payload() if tracker is not None else None,
        "passenger_personas": passenger_tracker.persona_payload() if passenger_tracker is not None else None,
    }
    persona_out = ROOT / args.persona_out
    persona_out.parent.mkdir(parents=True, exist_ok=True)
    persona_out.write_text(json.dumps(persona_payload, indent=2), encoding="utf-8")
    exported = export_maassim_run_tables(sim, ROOT / args.rides_out, ROOT / args.trips_out)
    payload = {
        "seed": args.seed,
        "snapshots": policy.count,
        "policy": args.policy,
        "beta": args.beta,
        "control_match": args.control_match,
        "synthetic_rules": args.synthetic_rules,
        "intervene_driver_rules": args.intervene_driver_rules,
        "passenger_personas": args.passenger_personas,
        "persona_assignment": args.persona_assignment,
        "synthetic_rule_config": {
            "long_trip_seconds": args.long_trip_seconds,
            "far_pickup_seconds": args.far_pickup_seconds,
            "surge_fare_per_second": args.surge_fare_per_second,
            "home_after_seconds": args.home_after_seconds,
        },
        "kpi_policy_config": {
            "wait_weight": args.kpi_wait_weight,
            "travel_weight": args.kpi_travel_weight,
            "fare_weight": args.kpi_fare_weight,
            "reject_penalty": args.kpi_reject_penalty,
        },
        "maassim_overrides": {
            "n_passengers": args.n_passengers,
            "n_vehicles": args.n_vehicles,
            "batch_time": args.batch_time,
        },
        "out": str(out_path.relative_to(ROOT)),
        "runs": len(getattr(sim, "runs", [])) if sim is not None else 0,
        "maassim_summary": summarize_maassim_result(sim),
        "exported": exported,
        "posterior_out": str((ROOT / args.posterior_out).relative_to(ROOT)) if tracker is not None else None,
        "posterior_summary": posterior_summary,
        "passenger_posterior_out": str((ROOT / args.passenger_posterior_out).relative_to(ROOT)) if passenger_tracker is not None else None,
        "passenger_posterior_summary": passenger_summary,
        "persona_out": str(persona_out.relative_to(ROOT)),
    }
    summary_out = ROOT / (args.summary_out or str(Path(args.out).with_suffix(".summary.json")))
    summary_out.parent.mkdir(parents=True, exist_ok=True)
    summary_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
