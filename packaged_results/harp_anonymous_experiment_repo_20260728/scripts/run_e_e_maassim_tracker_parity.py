"""Run E-E: MaaSSim factored-versus-explicit-joint tracker parity.

The experiment uses scheme (i): for every fleet size and common environment
index it regenerates a closed-loop Nootdorp market, saves the nearest-policy
queue snapshots and analytic driver event stream, then replays both trackers on
those identical events. Tracker-specific profile samples use independent RNGs.
No LLM/provider calls are made.
"""

from __future__ import annotations

import argparse
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, replace
import hashlib
from itertools import combinations, permutations
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter_ns
from types import SimpleNamespace
from typing import Iterable

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_courier_dispatch.dispatch_env import ACCEPT, CourierDispatchEnv, state_from_dict
from llm_courier_dispatch_maassim.adapter import MaaSSimCandidateOffer, MaaSSimQueueSnapshot
from llm_courier_dispatch_maassim.hidden_rules import (
    SyntheticRuleConfig,
    SyntheticRuleTracker,
    synthetic_action_for_type,
)
from llm_courier_dispatch_maassim.personas import PassengerPersonaConfig, PassengerPersonaTracker


DEFAULT_ROOT = ROOT / "analysis" / "e_e_maassim_rq2"
GENERATOR = ROOT / "scripts" / "run_maassim_shadow_smoke.py"
FLEET_SIZES = (2, 3, 4, 6, 8)
DEFAULT_LAMBDAS = (0.0, 0.5, 1.0)
JOINT_REQUIRED = {2, 3, 4}
TYPE_COUNT = 16

SERVE_VALUE = 3.0
WAIT_WEIGHT = 0.01
TRAVEL_WEIGHT = 0.0
FARE_WEIGHT = 0.0
DRIVER_REJECT_PENALTY = 2.0
PASSENGER_REJECT_PENALTY = 0.5

CONFLICT_FAST_COUNT = 1
CONFLICT_RISKY_TRAVEL = 420.0
CONFLICT_SAFE_TRAVEL = 150.0
CONFLICT_SAFE_FARE_PER_SECOND = 0.012
CONFLICT_RISKY_FARE_PER_SECOND = 0.003

RULE_CONFIG = SyntheticRuleConfig(
    long_trip_seconds=300.0,
    far_pickup_seconds=180.0,
    surge_fare_per_second=0.006,
    home_after_seconds=2700.0,
)
PASSENGER_CONFIG = PassengerPersonaConfig(
    impatient_wait_ratio=1.0,
    price_sensitive_fare=2.75,
    delay_sensitive_total_ratio=3.0,
)


@dataclass(frozen=True)
class CellPaths:
    snapshots: Path
    driver_events: Path
    passenger_events: Path
    rides: Path
    trips: Path
    personas: Path
    summary: Path


@dataclass
class UtilityStats:
    utility: float = 0.0
    snapshots: int = 0
    assignments: int = 0
    served: int = 0
    driver_rejects: int = 0
    passenger_rejects: int = 0


@dataclass(frozen=True)
class EvidenceEvent:
    time: float
    driver_id: int
    request_id: int
    action: int
    features: dict[str, float | int]


class FactoredTracker:
    def __init__(self, driver_ids: list[int], type_space: np.ndarray):
        self.driver_ids = list(driver_ids)
        self.driver_index = {driver_id: index for index, driver_id in enumerate(driver_ids)}
        self.type_space = np.asarray(type_space, dtype=int)
        self.log_probs = np.full((len(driver_ids), len(type_space)), -math.log(len(type_space)), dtype=np.float64)
        self.update_ns: list[int] = []

    @property
    def belief_bytes(self) -> int:
        return int(self.log_probs.nbytes)

    def update(self, driver_id: int, log_likelihood: np.ndarray) -> None:
        start = perf_counter_ns()
        index = self.driver_index[int(driver_id)]
        self.log_probs[index] += log_likelihood
        self.log_probs[index] -= logsumexp(self.log_probs[index])
        self.update_ns.append(perf_counter_ns() - start)

    def marginals(self) -> np.ndarray:
        return np.exp(self.log_probs)

    def sample_profile(self, rng: np.random.Generator) -> np.ndarray:
        indices = [int(rng.choice(len(self.type_space), p=np.exp(row))) for row in self.log_probs]
        return self.type_space[np.asarray(indices, dtype=int)]


class JointTracker:
    def __init__(self, driver_ids: list[int], type_space: np.ndarray):
        self.driver_ids = list(driver_ids)
        self.driver_index = {driver_id: index for index, driver_id in enumerate(driver_ids)}
        self.type_space = np.asarray(type_space, dtype=int)
        self.shape = (len(type_space),) * len(driver_ids)
        self.log_probs = np.full(self.shape, -math.log(len(type_space)) * len(driver_ids), dtype=np.float64)
        self.update_ns: list[int] = []

    @property
    def belief_bytes(self) -> int:
        return int(self.log_probs.nbytes)

    def update(self, driver_id: int, log_likelihood: np.ndarray) -> None:
        start = perf_counter_ns()
        axis = self.driver_index[int(driver_id)]
        broadcast_shape = [1] * len(self.driver_ids)
        broadcast_shape[axis] = len(self.type_space)
        self.log_probs += log_likelihood.reshape(broadcast_shape)
        self.log_probs -= logsumexp(self.log_probs)
        self.update_ns.append(perf_counter_ns() - start)

    def marginals(self) -> np.ndarray:
        probabilities = np.exp(self.log_probs)
        result = np.empty((len(self.driver_ids), len(self.type_space)), dtype=np.float64)
        for axis in range(len(self.driver_ids)):
            sum_axes = tuple(index for index in range(len(self.driver_ids)) if index != axis)
            marginal = probabilities.sum(axis=sum_axes) if sum_axes else probabilities
            result[axis] = marginal / float(marginal.sum())
        return result

    def sample_profile(self, rng: np.random.Generator) -> np.ndarray:
        probabilities = np.exp(self.log_probs).reshape(-1)
        probabilities /= float(probabilities.sum())
        flat_index = int(rng.choice(len(probabilities), p=probabilities))
        type_indices = np.asarray(np.unravel_index(flat_index, self.shape), dtype=int)
        return self.type_space[type_indices]


def logsumexp(values: np.ndarray) -> float:
    maximum = float(np.max(values))
    return maximum + math.log(float(np.exp(values - maximum).sum()))


def mean(values: Iterable[float]) -> float:
    data = list(values)
    return float(np.mean(data)) if data else float("nan")


def sem(values: Iterable[float]) -> float:
    data = np.asarray(list(values), dtype=float)
    return float(data.std(ddof=1) / math.sqrt(len(data))) if len(data) > 1 else 0.0


def t95(n: int) -> float:
    # Two-sided Student-t 97.5% quantiles, df=1..30. Required cells use n=10.
    table = {
        1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
        6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
        11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131,
        16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086,
        21: 2.080, 22: 2.074, 23: 2.069, 24: 2.064, 25: 2.060,
        26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045, 30: 2.042,
    }
    return table.get(max(1, n - 1), 1.96)


def parse_ints(raw: str) -> list[int]:
    values = sorted({int(item.strip()) for item in raw.split(",") if item.strip()})
    if not values or any(value < 1 for value in values):
        raise ValueError("fleet sizes must be positive")
    return values


def parse_floats(raw: str) -> list[float]:
    values = sorted({float(item.strip()) for item in raw.split(",") if item.strip()})
    if not values or any(value < 0.0 or value > 1.0 for value in values):
        raise ValueError("lambda values must lie in [0,1]")
    return values


def cell_paths(root: Path, n: int, seed: int) -> CellPaths:
    cell = root / "subfleets" / f"n{n}" / f"nearest_n{n}_s{seed}"
    return CellPaths(
        snapshots=cell.with_name(cell.name + "_queue_snapshots.jsonl"),
        driver_events=cell.with_name(cell.name + "_driver_events.csv"),
        passenger_events=cell.with_name(cell.name + "_passenger_events.csv"),
        rides=cell.with_name(cell.name + "_rides.csv"),
        trips=cell.with_name(cell.name + "_trips.csv"),
        personas=cell.with_name(cell.name + "_personas.json"),
        summary=cell.with_name(cell.name + "_summary.json"),
    )


def valid_generated_cell(paths: CellPaths, n: int) -> bool:
    required = (paths.snapshots, paths.driver_events, paths.personas, paths.summary)
    if not all(path.is_file() and path.stat().st_size > 0 for path in required):
        return False
    try:
        summary = json.loads(paths.summary.read_text(encoding="utf-8"))
        personas = json.loads(paths.personas.read_text(encoding="utf-8"))
        driver_types = ((personas.get("driver_personas") or {}).get("driver_types") or {})
        return (
            int(summary.get("snapshots", 0)) > 0
            and int((summary.get("posterior_summary") or {}).get("events", 0)) > 0
            and int((summary.get("maassim_overrides") or {}).get("n_vehicles", -1)) == n
            and len(driver_types) == n
        )
    except (OSError, ValueError, TypeError):
        return False


def generation_command(args: argparse.Namespace, n: int, seed: int, paths: CellPaths) -> list[str]:
    def rel(path: Path) -> str:
        return str(path.relative_to(ROOT))

    return [
        str(args.maassim_python), str(GENERATOR),
        "--seed", str(seed),
        "--config", str(ROOT / "external" / "maassim" / "MaaSSim" / "data" / "config.json"),
        "--root-path", str(ROOT / "external" / "maassim" / "MaaSSim"),
        "--n-passengers", "40", "--n-vehicles", str(n), "--batch-time", "120",
        "--policy", "nearest", "--control-match",
        "--synthetic-rules", "--intervene-driver-rules",
        "--passenger-personas", "--persona-assignment", "random",
        "--passenger-price-sensitive-fare", "2.75",
        "--passenger-impatient-wait-ratio", "1.0",
        "--passenger-delay-sensitive-total-ratio", "3.0",
        "--long-trip-seconds", "300", "--far-pickup-seconds", "180",
        "--surge-fare-per-second", "0.006", "--home-after-seconds", "2700",
        "--kpi-wait-weight", str(WAIT_WEIGHT),
        "--kpi-reject-penalty", str(DRIVER_REJECT_PENALTY),
        "--kpi-fare-weight", str(FARE_WEIGHT),
        "--out", rel(paths.snapshots),
        "--posterior-out", rel(paths.driver_events),
        "--passenger-posterior-out", rel(paths.passenger_events),
        "--rides-out", rel(paths.rides), "--trips-out", rel(paths.trips),
        "--persona-out", rel(paths.personas), "--summary-out", rel(paths.summary),
    ]


def generate_subfleets(args: argparse.Namespace, fleet_sizes: list[int]) -> None:
    jobs: list[tuple[int, int, CellPaths, list[str]]] = []
    for n in fleet_sizes:
        for seed in range(args.seeds):
            paths = cell_paths(args.root, n, seed)
            if not args.force_generate and valid_generated_cell(paths, n):
                continue
            paths.snapshots.parent.mkdir(parents=True, exist_ok=True)
            jobs.append((n, seed, paths, generation_command(args, n, seed, paths)))
    if not jobs:
        print("All closed-loop sub-fleet artifacts already exist.")
        return

    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join((str(ROOT / "external" / "maassim"), str(ROOT)))
    environment["MPLBACKEND"] = "Agg"

    def run(job: tuple[int, int, CellPaths, list[str]]) -> tuple[int, int]:
        n, seed, _, command = job
        result = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"n={n} seed={seed} generation failed:\n{result.stdout}\n{result.stderr}")
        return n, seed

    failures: list[str] = []
    with ThreadPoolExecutor(max_workers=max(1, args.generate_workers)) as executor:
        futures = {executor.submit(run, job): (job[0], job[1]) for job in jobs}
        for future in as_completed(futures):
            n, seed = futures[future]
            try:
                future.result()
                print(f"generated n={n} seed={seed}", flush=True)
            except Exception as exc:  # noqa: BLE001 - aggregate all subprocess failures
                failures.append(str(exc))
    if failures:
        raise RuntimeError("Sub-fleet generation failures:\n" + "\n".join(failures))
    for n, seed, paths, _ in jobs:
        if not valid_generated_cell(paths, n):
            raise AssertionError(f"generated cell failed validation: n={n} seed={seed}")


def tuple_from_bits(bits: str) -> tuple[int, int, int, int]:
    values = tuple(int(char) for char in bits)
    if len(values) != 4:
        raise ValueError(bits)
    return values  # type: ignore[return-value]


def load_cell(paths: CellPaths, seed: int, n: int) -> tuple[list[tuple[MaaSSimQueueSnapshot, list[tuple[int, int]]]], SyntheticRuleTracker, PassengerPersonaTracker, list[dict[str, str]]]:
    personas = json.loads(paths.personas.read_text(encoding="utf-8"))
    driver_tracker = SyntheticRuleTracker(
        paths.driver_events,
        intervene=True,
        seed=seed,
        assignment_mode="random",
        config=RULE_CONFIG,
    )
    passenger_tracker = PassengerPersonaTracker(
        paths.passenger_events,
        seed=seed,
        assignment_mode="random",
        config=PASSENGER_CONFIG,
    )
    driver_types = ((personas.get("driver_personas") or {}).get("driver_types") or {})
    passenger_types = ((personas.get("passenger_personas") or {}).get("passenger_types") or {})
    driver_tracker.true_types = {int(key): tuple_from_bits(value) for key, value in driver_types.items()}
    passenger_tracker.true_types = {int(key): tuple_from_bits(value) for key, value in passenger_types.items()}
    if len(driver_tracker.true_types) != n:
        raise AssertionError(f"n={n} seed={seed}: persona map has {len(driver_tracker.true_types)} drivers")

    snapshots: list[tuple[MaaSSimQueueSnapshot, list[tuple[int, int]]]] = []
    for line in paths.snapshots.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        snapshot = MaaSSimQueueSnapshot(
            time=float(raw.get("time", 0.0)),
            vehicle_queue=tuple(int(value) for value in raw.get("vehicle_queue", [])),
            request_queue=tuple(int(value) for value in raw.get("request_queue", [])),
            candidates=tuple(MaaSSimCandidateOffer(**candidate) for candidate in raw.get("candidates", [])),
        )
        source_assignment = [(int(driver), int(request)) for driver, request in (raw.get("shadow_assignment") or {}).items()]
        snapshots.append((snapshot, source_assignment))
    with paths.driver_events.open(newline="", encoding="utf-8") as handle:
        event_rows = list(csv.DictReader(handle))
    return snapshots, driver_tracker, passenger_tracker, event_rows


def conflict_transform(snapshot: MaaSSimQueueSnapshot, strength: float) -> MaaSSimQueueSnapshot:
    strength = min(1.0, max(0.0, float(strength)))
    if strength == 0.0:
        return snapshot
    risky_pairs: set[tuple[int, int]] = set()
    by_request: dict[int, list[MaaSSimCandidateOffer]] = {}
    for offer in snapshot.candidates:
        by_request.setdefault(int(offer.request_id), []).append(offer)
    for offers in by_request.values():
        ordered = sorted(offers, key=lambda item: (item.wait_time, item.driver_id, item.request_id))
        for offer in ordered[:CONFLICT_FAST_COUNT]:
            risky_pairs.add((int(offer.driver_id), int(offer.request_id)))
    transformed: list[MaaSSimCandidateOffer] = []
    for offer in snapshot.candidates:
        if (int(offer.driver_id), int(offer.request_id)) in risky_pairs:
            target_travel = max(float(offer.travel_time), CONFLICT_RISKY_TRAVEL)
            target_fare = min(float(offer.fare), target_travel * CONFLICT_RISKY_FARE_PER_SECOND)
        else:
            target_travel = min(float(offer.travel_time), CONFLICT_SAFE_TRAVEL)
            target_fare = max(float(offer.fare), target_travel * CONFLICT_SAFE_FARE_PER_SECOND)
        transformed.append(
            replace(
                offer,
                travel_time=float(offer.travel_time) + strength * (target_travel - float(offer.travel_time)),
                fare=float(offer.fare) + strength * (target_fare - float(offer.fare)),
            )
        )
    return MaaSSimQueueSnapshot(snapshot.time, snapshot.vehicle_queue, snapshot.request_queue, tuple(transformed))


def legal_assignments(snapshot: MaaSSimQueueSnapshot) -> list[tuple[tuple[int, int], ...]]:
    offers = list(snapshot.candidates)
    if not offers:
        return []
    drivers = sorted({int(offer.driver_id) for offer in offers})
    requests = sorted({int(offer.request_id) for offer in offers})
    available = {(int(offer.driver_id), int(offer.request_id)) for offer in offers}
    match_count = min(len(drivers), len(requests))
    assignments: list[tuple[tuple[int, int], ...]] = []
    for driver_subset in combinations(drivers, match_count):
        for request_perm in permutations(requests, match_count):
            pairs = tuple(zip(driver_subset, request_perm, strict=True))
            if all(pair in available for pair in pairs):
                assignments.append(pairs)
    return sorted(assignments)


def planner_score(
    assignment: tuple[tuple[int, int], ...],
    offer_by_pair: dict[tuple[int, int], MaaSSimCandidateOffer],
    sampled_types: np.ndarray,
    driver_index: dict[int, int],
) -> float:
    score = 0.0
    for driver_id, request_id in assignment:
        offer = offer_by_pair[(driver_id, request_id)]
        theta = tuple(int(value) for value in sampled_types[driver_index[driver_id]])
        action, _ = synthetic_action_for_type(theta, offer, RULE_CONFIG)
        if action == ACCEPT:
            score += (
                SERVE_VALUE
                + FARE_WEIGHT * float(offer.fare)
                - WAIT_WEIGHT * float(offer.wait_time)
                - TRAVEL_WEIGHT * float(offer.travel_time)
            )
        else:
            score -= DRIVER_REJECT_PENALTY
    return float(score)


def choose_assignment(
    snapshot: MaaSSimQueueSnapshot,
    sampled_types: np.ndarray,
    driver_index: dict[int, int],
) -> tuple[tuple[int, int], ...]:
    assignments = legal_assignments(snapshot)
    if not assignments:
        return ()
    offer_by_pair = {(int(offer.driver_id), int(offer.request_id)): offer for offer in snapshot.candidates}
    best = assignments[0]
    best_score = planner_score(best, offer_by_pair, sampled_types, driver_index)
    for assignment in assignments[1:]:
        score = planner_score(assignment, offer_by_pair, sampled_types, driver_index)
        if score > best_score + 1e-12:
            best, best_score = assignment, score
        elif abs(score - best_score) <= 1e-12 and assignment < best:
            best = assignment
    return best


def fake_traveller(passenger_id: int, offer: MaaSSimCandidateOffer) -> SimpleNamespace:
    return SimpleNamespace(
        id=int(passenger_id),
        request=SimpleNamespace(ttrav=float(offer.travel_time)),
        sim=SimpleNamespace(env=SimpleNamespace(now=float(offer.time or 0.0))),
    )


def evaluate_assignment(
    assignment: tuple[tuple[int, int], ...],
    snapshot: MaaSSimQueueSnapshot,
    driver_tracker: SyntheticRuleTracker,
    passenger_tracker: PassengerPersonaTracker,
    stats: UtilityStats,
) -> None:
    if not assignment:
        return
    offer_by_pair = {(int(offer.driver_id), int(offer.request_id)): offer for offer in snapshot.candidates}
    stats.snapshots += 1
    for driver_id, request_id in assignment:
        offer = offer_by_pair[(driver_id, request_id)]
        stats.assignments += 1
        action, _ = synthetic_action_for_type(driver_tracker.type_for_driver(driver_id), offer, RULE_CONFIG)
        if action != ACCEPT:
            stats.driver_rejects += 1
            stats.utility -= DRIVER_REJECT_PENALTY
            continue
        traveller = fake_traveller(request_id, offer)
        offer_payload = {
            "req_id": request_id,
            "wait_time": offer.wait_time,
            "travel_time": offer.travel_time,
            "fare": offer.fare,
            "simpaxes": [request_id],
        }
        passenger_type = passenger_tracker.type_for_passenger(request_id)
        rejected, _ = passenger_tracker.reject_for_type(passenger_type, traveller, offer_payload)
        if rejected:
            stats.passenger_rejects += 1
            stats.utility -= PASSENGER_REJECT_PENALTY
            continue
        stats.served += 1
        stats.utility += (
            SERVE_VALUE
            + FARE_WEIGHT * float(offer.fare)
            - WAIT_WEIGHT * float(offer.wait_time)
            - TRAVEL_WEIGHT * float(offer.travel_time)
        )


def likelihood_vector(env: CourierDispatchEnv, features: dict[str, float | int], action: int) -> np.ndarray:
    state = state_from_dict(features)
    accepted = int(action) == ACCEPT
    values = []
    for theta in env.type_space:
        accept_probability = env.likelihood(ACCEPT, state, theta)
        likelihood = accept_probability if accepted else 1.0 - accept_probability
        values.append(max(likelihood, 1e-12))
    values = np.asarray(values, dtype=np.float64)
    return np.log(values)


def load_evidence_events(
    snapshots: list[tuple[MaaSSimQueueSnapshot, list[tuple[int, int]]]],
    saved: list[dict[str, str]],
) -> list[EvidenceEvent]:
    expected_pairs: list[tuple[float, int, int]] = []
    for snapshot, source_assignment in snapshots:
        for driver_id, request_id in source_assignment:
            expected_pairs.append((float(snapshot.time), driver_id, request_id))
    observed_pairs = [
        (float(row["time"]), int(row["driver_id"]), int(row["request_id"]))
        for row in saved
    ]
    if observed_pairs != expected_pairs:
        for index, (left, right) in enumerate(zip(observed_pairs, expected_pairs)):
            if left != right:
                raise AssertionError(f"saved/snapshot event mismatch at {index}: {left} != {right}")
        raise AssertionError(f"saved/snapshot event counts differ: {len(observed_pairs)} != {len(expected_pairs)}")
    events: list[EvidenceEvent] = []
    for row in saved:
        events.append(
            EvidenceEvent(
                time=float(row["time"]),
                driver_id=int(row["driver_id"]),
                request_id=int(row["request_id"]),
                action=int(row["action_code"]),
                features={
                    "long_trip": int(row["long_trip"]),
                    "leaves_zone": int(row["leaves_zone"]),
                    "home_ward": int(row["home_ward"]),
                    "surge": int(row["surge"]),
                    "pay": float(row["pay"]),
                    "after_deadline": int(float(row["time"]) >= RULE_CONFIG.home_after_seconds),
                    "congestion": 0.0,
                },
            )
        )
    return events


def update_summary(values_ns: list[int]) -> tuple[float, float]:
    if not values_ns:
        return 0.0, 0.0
    microseconds = np.asarray(values_ns, dtype=float) / 1000.0
    return float(microseconds.mean()), float(np.percentile(microseconds, 95))


def run_cell(
    *,
    root: Path,
    n: int,
    seed: int,
    strength: float,
    run_joint: bool,
) -> list[dict[str, object]]:
    paths = cell_paths(root, n, seed)
    snapshots, true_driver_source, true_passenger_source, saved_events = load_cell(paths, seed, n)
    driver_ids = sorted(true_driver_source.true_types)
    type_env = CourierDispatchEnv(n_agents=1, rule_count=4, horizon=1, seed=seed)
    factored = FactoredTracker(driver_ids, type_env.type_space)
    joint = JointTracker(driver_ids, type_env.type_space) if run_joint else None
    factored_rng = np.random.default_rng(110_000 + 10_000 * n + 100 * int(round(strength * 10)) + seed)
    joint_rng = np.random.default_rng(220_000 + 10_000 * n + 100 * int(round(strength * 10)) + seed)
    factored_stats = UtilityStats()
    joint_stats = UtilityStats()
    oracle_stats = UtilityStats()
    driver_index = {driver_id: index for index, driver_id in enumerate(driver_ids)}
    true_profile = np.asarray([true_driver_source.type_for_driver(driver_id) for driver_id in driver_ids], dtype=int)
    max_tv = 0.0

    evidence_events = load_evidence_events(snapshots, saved_events)
    event_cursor = 0
    for base_snapshot, source_assignment in snapshots:
        snapshot = conflict_transform(base_snapshot, strength)
        factored_assignment = choose_assignment(snapshot, factored.sample_profile(factored_rng), driver_index)
        evaluate_assignment(factored_assignment, snapshot, true_driver_source, true_passenger_source, factored_stats)
        if joint is not None:
            joint_assignment = choose_assignment(snapshot, joint.sample_profile(joint_rng), driver_index)
            evaluate_assignment(joint_assignment, snapshot, true_driver_source, true_passenger_source, joint_stats)
        oracle_assignment = choose_assignment(snapshot, true_profile, driver_index)
        evaluate_assignment(oracle_assignment, snapshot, true_driver_source, true_passenger_source, oracle_stats)

        # Multiple snapshots can share one batch timestamp after a rejection.
        # Consume exactly this snapshot's stored source-policy assignment, not
        # all events with the same timestamp.
        for expected_driver, expected_request in source_assignment:
            if event_cursor >= len(evidence_events):
                raise AssertionError("source assignment exceeds saved event stream")
            event = evidence_events[event_cursor]
            if (
                event.time != float(base_snapshot.time)
                or event.driver_id != expected_driver
                or event.request_id != expected_request
            ):
                raise AssertionError(
                    "snapshot/event alignment failed: "
                    f"snapshot={(base_snapshot.time, expected_driver, expected_request)} "
                    f"event={(event.time, event.driver_id, event.request_id)}"
                )
            log_likelihood = likelihood_vector(type_env, event.features, event.action)
            factored.update(event.driver_id, log_likelihood)
            if joint is not None:
                joint.update(event.driver_id, log_likelihood)
                factored_marginals = factored.marginals()
                joint_marginals = joint.marginals()
                tv = float(np.max(0.5 * np.sum(np.abs(factored_marginals - joint_marginals), axis=1)))
                max_tv = max(max_tv, tv)
            event_cursor += 1

    if event_cursor != len(evidence_events):
        raise AssertionError(f"not all evidence events were consumed: {event_cursor}/{len(evidence_events)}")

    joint_entries = TYPE_COUNT**n
    factored_entries = n * TYPE_COUNT
    common = {
        "seed": seed,
        "n": n,
        "lambda": strength,
        "events": len(evidence_events),
        "joint_entries": joint_entries,
        "factored_entries": factored_entries,
        "storage_ratio": joint_entries / factored_entries,
        "oracle_utility": oracle_stats.utility,
        "source_scheme": "closed-loop regeneration by fleet size",
        "environment_index": seed,
        "evidence_stream": "nearest-policy saved assignment events; identical order across trackers",
        "driver_reject_penalty": DRIVER_REJECT_PENALTY,
    }
    factored_mean_us, factored_p95_us = update_summary(factored.update_ns)
    rows: list[dict[str, object]] = [
        {
            **common,
            "tracker": "factored",
            "utility": factored_stats.utility,
            "max_tv": max_tv if joint is not None else float("nan"),
            "update_wallclock_s": sum(factored.update_ns) / 1e9,
            "wallclock": sum(factored.update_ns) / 1e9,
            "mean_update_us": factored_mean_us,
            "p95_update_us": factored_p95_us,
            "peak_mem_bytes": factored.belief_bytes,
            "peak_mem": factored.belief_bytes,
            "belief_entries": factored_entries,
            "snapshots": factored_stats.snapshots,
            "assignments": factored_stats.assignments,
            "served": factored_stats.served,
            "driver_rejects": factored_stats.driver_rejects,
            "passenger_rejects": factored_stats.passenger_rejects,
            "sampling_rng_seed": 110_000 + 10_000 * n + 100 * int(round(strength * 10)) + seed,
        }
    ]
    if joint is not None:
        joint_mean_us, joint_p95_us = update_summary(joint.update_ns)
        rows.append(
            {
                **common,
                "tracker": "joint",
                "utility": joint_stats.utility,
                "max_tv": max_tv,
                "update_wallclock_s": sum(joint.update_ns) / 1e9,
                "wallclock": sum(joint.update_ns) / 1e9,
                "mean_update_us": joint_mean_us,
                "p95_update_us": joint_p95_us,
                "peak_mem_bytes": joint.belief_bytes,
                "peak_mem": joint.belief_bytes,
                "belief_entries": joint_entries,
                "snapshots": joint_stats.snapshots,
                "assignments": joint_stats.assignments,
                "served": joint_stats.served,
                "driver_rejects": joint_stats.driver_rejects,
                "passenger_rejects": joint_stats.passenger_rejects,
                "sampling_rng_seed": 220_000 + 10_000 * n + 100 * int(round(strength * 10)) + seed,
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"no rows for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def aggregate_rows(rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    tracker_summary: list[dict[str, object]] = []
    groups: dict[tuple[int, float, str], list[dict[str, object]]] = {}
    for row in rows:
        groups.setdefault((int(row["n"]), float(row["lambda"]), str(row["tracker"])), []).append(row)
    for (n, strength, tracker), group in sorted(groups.items()):
        utilities = [float(row["utility"]) for row in group]
        tracker_summary.append(
            {
                "n": n,
                "lambda": strength,
                "tracker": tracker,
                "seeds": len(group),
                "utility_mean": mean(utilities),
                "utility_sem": sem(utilities),
                "max_tv": max((float(row["max_tv"]) for row in group if math.isfinite(float(row["max_tv"]))), default=float("nan")),
                "mean_update_us": mean(float(row["mean_update_us"]) for row in group),
                "p95_update_us": mean(float(row["p95_update_us"]) for row in group),
                "peak_mem_bytes": max(int(row["peak_mem_bytes"]) for row in group),
                "belief_entries": int(group[0]["belief_entries"]),
                "joint_entries": int(group[0]["joint_entries"]),
                "factored_entries": int(group[0]["factored_entries"]),
                "storage_ratio": float(group[0]["storage_ratio"]),
                "events_mean": mean(float(row["events"]) for row in group),
            }
        )

    gaps: list[dict[str, object]] = []
    for n in sorted({int(row["n"]) for row in rows}):
        for strength in sorted({float(row["lambda"]) for row in rows if int(row["n"]) == n}):
            factored = {int(row["seed"]): float(row["utility"]) for row in rows if int(row["n"]) == n and float(row["lambda"]) == strength and row["tracker"] == "factored"}
            joint = {int(row["seed"]): float(row["utility"]) for row in rows if int(row["n"]) == n and float(row["lambda"]) == strength and row["tracker"] == "joint"}
            common_seeds = sorted(set(factored) & set(joint))
            if not common_seeds:
                continue
            values = [joint[seed] - factored[seed] for seed in common_seeds]
            gap_mean = mean(values)
            gap_sem = sem(values)
            half_width = t95(len(values)) * gap_sem
            paired_rows = [row for row in rows if int(row["n"]) == n and float(row["lambda"]) == strength and row["tracker"] == "joint"]
            gaps.append(
                {
                    "n": n,
                    "lambda": strength,
                    "seeds": len(values),
                    "joint_minus_factored_mean": gap_mean,
                    "joint_minus_factored_sem": gap_sem,
                    "ci95_low": gap_mean - half_width,
                    "ci95_high": gap_mean + half_width,
                    "ci_covers_zero": gap_mean - half_width <= 0.0 <= gap_mean + half_width,
                    "max_tv": max(float(row["max_tv"]) for row in paired_rows),
                    "joint_entries": TYPE_COUNT**n,
                    "factored_entries": TYPE_COUNT * n,
                    "storage_ratio": TYPE_COUNT**n / (TYPE_COUNT * n),
                }
            )
    return tracker_summary, gaps


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_report(root: Path, rows: list[dict[str, object]], summary: list[dict[str, object]], gaps: list[dict[str, object]], metadata: dict[str, object]) -> None:
    lines = [
        "# E-E MaaSSim Factored-vs-Explicit-Joint Tracker Parity",
        "",
        "Scheme (i) is used: each fleet size is regenerated as a self-consistent closed-loop Nootdorp market. Both trackers consume the identical saved nearest-policy evidence stream in the identical order. Their profile-sampling RNGs are independent.",
        "",
        "| n | lambda | factored utility | joint utility | joint - factored (95% CI) | max marginal TV | storage |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    lookup = {(int(row["n"]), float(row["lambda"]), str(row["tracker"])): row for row in summary}
    for n in sorted({int(row["n"]) for row in rows}):
        for strength in sorted({float(row["lambda"]) for row in rows if int(row["n"]) == n}):
            factored = lookup[(n, strength, "factored")]
            joint = lookup.get((n, strength, "joint"))
            gap = next((row for row in gaps if int(row["n"]) == n and float(row["lambda"]) == strength), None)
            joint_text = "not run" if joint is None else f"{float(joint['utility_mean']):.3f} +/- {float(joint['utility_sem']):.3f}"
            gap_text = "n/a" if gap is None else f"{float(gap['joint_minus_factored_mean']):+.3f} [{float(gap['ci95_low']):+.3f}, {float(gap['ci95_high']):+.3f}]"
            tv_text = "n/a" if gap is None else f"{float(gap['max_tv']):.2e}"
            lines.append(
                f"| {n} | {strength:g} | {float(factored['utility_mean']):.3f} +/- {float(factored['utility_sem']):.3f} | {joint_text} | {gap_text} | {tv_text} | {TYPE_COUNT*n:,} vs {TYPE_COUNT**n:,} |"
            )
    lines.extend(
        [
            "",
            "`peak_mem_bytes` is the exact maximum persistent float64 belief-array allocation, not process RSS. `mean_update_us` and `p95_update_us` time only the Bayesian update and normalization; marginalization for the TV diagnostic is excluded.",
            "",
            f"Joint n=6 run: {'included' if metadata['include_n6_joint'] else 'not run (optional)'}; joint n=8: not run by design (theoretical float64 table is {TYPE_COUNT**8 * 8:,} bytes).",
        ]
    )
    (root / "e_e_maassim_tracker_parity.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_experiment(args: argparse.Namespace, fleet_sizes: list[int], lambdas: list[float]) -> None:
    rows: list[dict[str, object]] = []
    for n in fleet_sizes:
        run_joint = n in JOINT_REQUIRED or (n == 6 and args.include_n6_joint)
        if n == 8:
            run_joint = False
        for strength in lambdas:
            for seed in range(args.seeds):
                print(f"replay n={n} lambda={strength:g} seed={seed} joint={run_joint}", flush=True)
                rows.extend(run_cell(root=args.root, n=n, seed=seed, strength=strength, run_joint=run_joint))
    summary, gaps = aggregate_rows(rows)
    write_csv(args.root / "e_e_maassim_tracker_parity.csv", rows)
    write_csv(args.root / "e_e_maassim_tracker_parity_summary.csv", summary)
    gap_path = args.root / "e_e_maassim_tracker_parity_gaps.csv"
    if gaps:
        write_csv(gap_path, gaps)
    else:
        gap_path.write_text(
            "n,lambda,seeds,joint_minus_factored_mean,joint_minus_factored_sem,"
            "ci95_low,ci95_high,ci_covers_zero,max_tv,joint_entries,factored_entries,storage_ratio\n",
            encoding="utf-8",
        )
    artifacts = []
    for n in fleet_sizes:
        for seed in range(args.seeds):
            paths = cell_paths(args.root, n, seed)
            for path in (paths.snapshots, paths.driver_events, paths.personas, paths.summary):
                artifacts.append({"path": str(path.relative_to(ROOT)).replace("\\", "/"), "bytes": path.stat().st_size, "sha256": sha256(path)})
    metadata = {
        "experiment": "E-E MaaSSim factored-vs-explicit-joint tracker parity",
        "status": "complete",
        "source_scheme": "scheme i: closed-loop regeneration by fleet size",
        "fleet_sizes": fleet_sizes,
        "lambdas": lambdas,
        "seeds": args.seeds,
        "common_environment_indices": list(range(args.seeds)),
        "environment_matching": "common environment indices within each n; tracker sampling RNG streams are independent",
        "provider_calls": 0,
        "n_passengers": 40,
        "batch_time_seconds": 120,
        "type_count_per_driver": TYPE_COUNT,
        "joint_required_through_n": 4,
        "include_n6_joint": bool(args.include_n6_joint),
        "joint_n8": "not run; theoretical 16^8 float64 table is infeasible for the experiment budget",
        "evidence_stream": "saved nearest-policy assignment events from each regenerated closed-loop cell",
        "likelihood": "per-driver binary accept/reject analytic likelihood; identical stream/order for both trackers",
        "sampling": "independent deterministic RNG streams for factored and joint profile draws",
        "planner": "identical exhaustive maximum-cardinality assignment objective with lexicographic tie-breaking",
        "utility": {
            "serve_value": SERVE_VALUE,
            "pickup_wait_per_second": WAIT_WEIGHT,
            "travel_weight": TRAVEL_WEIGHT,
            "fare_weight": FARE_WEIGHT,
            "driver_reject_penalty": DRIVER_REJECT_PENALTY,
            "passenger_reject_penalty": PASSENGER_REJECT_PENALTY,
        },
        "lambda_scope": "offer payoff geometry only; evidence stream and likelihood are unchanged",
        "peak_mem_definition": "exact maximum persistent float64 belief-array bytes",
        "update_timing_definition": "Bayesian log update plus normalization; excludes TV marginal diagnostic and planner",
        "artifacts": artifacts,
    }
    (args.root / "e_e_maassim_tracker_parity_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    write_report(args.root, rows, summary, gaps, metadata)
    print(json.dumps({"rows": len(rows), "summary_rows": len(summary), "gap_rows": len(gaps), "status": "complete"}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("generate", "run", "all"), default="all")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--fleet-sizes", default=",".join(str(value) for value in FLEET_SIZES))
    parser.add_argument("--lambdas", default=",".join(str(value) for value in DEFAULT_LAMBDAS))
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--include-n6-joint", action="store_true")
    parser.add_argument("--generate-workers", type=int, default=2)
    parser.add_argument("--force-generate", action="store_true")
    parser.add_argument(
        "--maassim-python",
        type=Path,
        default=(
            ROOT / ".venvs" / "maassim-py311" / "Scripts" / "python.exe"
            if os.name == "nt"
            else ROOT / ".venvs" / "maassim-py311" / "bin" / "python"
        ),
    )
    args = parser.parse_args()
    args.root = args.root.resolve()
    fleet_sizes = parse_ints(args.fleet_sizes)
    lambdas = parse_floats(args.lambdas)
    if args.seeds < 2:
        raise ValueError("at least two common environment indices are required")
    if args.stage in {"generate", "all"}:
        if not args.maassim_python.is_file():
            raise FileNotFoundError(f"MaaSSim Python runtime not found: {args.maassim_python}")
        generate_subfleets(args, fleet_sizes)
    if args.stage in {"run", "all"}:
        for n in fleet_sizes:
            for seed in range(args.seeds):
                paths = cell_paths(args.root, n, seed)
                if not valid_generated_cell(paths, n):
                    raise FileNotFoundError(f"missing/invalid generated cell: n={n} seed={seed}")
        run_experiment(args, fleet_sizes, lambdas)


if __name__ == "__main__":
    main()
