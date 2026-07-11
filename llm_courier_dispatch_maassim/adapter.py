"""MaaSSim adapter scaffold for CourierDispatch-Rules.

The first integration target is MaaSSim's user-defined ``f_match`` platform
function. This module keeps MaaSSim optional and exposes small typed snapshots
that the existing PACT/PACT+ solver can consume after a feature mapping layer is
implemented.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Protocol


@dataclass(frozen=True)
class MaaSSimCandidateOffer:
    """A candidate driver-request pair extracted from MaaSSim queues."""

    driver_id: int
    request_id: int
    driver_position: Any
    origin: Any
    destination: Any
    wait_time: float
    travel_time: float
    fare: float
    distance: float | None = None
    time: float | None = None


@dataclass(frozen=True)
class MaaSSimDriverObservation:
    """Neutral event used for posterior updates."""

    driver_id: int
    request_id: int | None
    event: str
    offer: MaaSSimCandidateOffer | None = None


@dataclass(frozen=True)
class MaaSSimQueueSnapshot:
    """Minimal state exposed to a dispatch policy."""

    time: float
    vehicle_queue: tuple[int, ...]
    request_queue: tuple[int, ...]
    candidates: tuple[MaaSSimCandidateOffer, ...]


class MaaSSimDispatchPolicy(Protocol):
    """Policy interface used by a MaaSSim ``f_match`` wrapper."""

    def choose_assignment(self, snapshot: MaaSSimQueueSnapshot) -> dict[int, int]:
        """Return ``{driver_id: request_id}`` for a legal partial assignment."""


@dataclass(frozen=True)
class MaaSSimFeatureConfig:
    """Thresholds for mapping MaaSSim offers to CourierDispatch rule features."""

    long_trip_seconds: float = 900.0
    low_fare_per_second: float = 0.001
    surge_fare_per_second: float = 0.004


def offer_to_rule_features(offer: MaaSSimCandidateOffer, config: MaaSSimFeatureConfig = MaaSSimFeatureConfig()) -> dict[str, float | int]:
    """Map a MaaSSim candidate offer into CourierDispatch-style public features.

    ``leaves_zone`` and ``home_ward`` require zone/home annotations that MaaSSim
    does not expose in the generic queue object, so they are conservative zeros
    until a scenario-specific mapper is supplied.
    """

    fare_per_second = offer.fare / max(float(offer.travel_time), 1.0)
    return {
        "long_trip": int(float(offer.travel_time) >= config.long_trip_seconds),
        "leaves_zone": 0,
        "home_ward": 0,
        "surge": int(fare_per_second >= config.surge_fare_per_second),
        "pay": float(offer.fare),
        "after_deadline": 0,
        "congestion": 0.0,
        "menu_long_trip": 0,
        "menu_leaves_zone": 0,
        "menu_home_ward": 0,
        "menu_surge": 0,
        "menu_pay": float(offer.fare),
    }


def import_maassim() -> Any:
    """Import MaaSSim lazily so this package remains optional."""

    try:
        import MaaSSim  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on optional external repo
        raise RuntimeError("MaaSSim is not installed. Install or clone RafalKucharskiPK/MaaSSim before running this adapter.") from exc
    return MaaSSim


class MaaSSimDispatchAdapter:
    """Extracts platform queue snapshots and applies policy decisions.

    The extraction side is intentionally light. The application side will be
    implemented after a first MaaSSim smoke run confirms the exact in-memory
    shapes of ``platform.reqQ``, ``platform.vehQ``, ``sim.inData.requests``, and
    ``sim.vehicles`` in the selected scenario.
    """

    def __init__(self, feature_config: MaaSSimFeatureConfig | None = None) -> None:
        self.feature_config = feature_config or MaaSSimFeatureConfig()

    def snapshot_from_platform(self, platform: Any, max_pairs: int | None = None) -> MaaSSimQueueSnapshot:
        sim = platform.sim
        veh_ids = tuple(int(vid) for vid in list(platform.vehQ))
        req_ids = tuple(int(rid) for rid in list(platform.reqQ))
        candidates = tuple(self._candidate_pairs(platform, veh_ids, req_ids, max_pairs=max_pairs))
        return MaaSSimQueueSnapshot(float(sim.env.now), veh_ids, req_ids, candidates)

    def _candidate_pairs(self, platform: Any, veh_ids: Iterable[int], req_ids: Iterable[int], max_pairs: int | None) -> list[MaaSSimCandidateOffer]:
        sim = platform.sim
        offers: list[MaaSSimCandidateOffer] = []
        for driver_id in veh_ids:
            vehicle = sim.vehicles.loc[driver_id]
            driver_position = vehicle.pos
            for request_id in req_ids:
                request = sim.inData.requests.loc[request_id]
                origin = request.origin
                if (driver_id, request_id) in platform.tabu or (driver_position, origin) in platform.tabu:
                    continue
                wait_time = float(sim.skims.ride[origin][driver_position])
                travel_time_raw = request.ttrav
                travel_time = float(travel_time_raw.total_seconds() if hasattr(travel_time_raw, "total_seconds") else travel_time_raw)
                distance = float(getattr(request, "dist", 0.0)) if hasattr(request, "dist") else None
                fare = float(platform.platform.fare) * float(distance or 0.0) / 1000.0
                offers.append(
                    MaaSSimCandidateOffer(
                        driver_id=int(driver_id),
                        request_id=int(request_id),
                        driver_position=driver_position,
                        origin=origin,
                        destination=getattr(request, "destination", None),
                        wait_time=wait_time,
                        travel_time=travel_time,
                        fare=fare,
                        distance=distance,
                        time=float(sim.env.now),
                    )
                )
                if max_pairs is not None and len(offers) >= max_pairs:
                    return offers
        return offers

    def apply_assignment(self, platform: Any, assignment: dict[int, int]) -> None:
        sim = platform.sim
        from MaaSSim.driver import driverEvent  # type: ignore
        from MaaSSim.pool_price import pool_price_fun  # type: ignore
        from MaaSSim.traveller import travellerEvent  # type: ignore

        for driver_id, request_id in assignment.items():
            if driver_id not in platform.vehQ or request_id not in platform.reqQ:
                continue
            veh = sim.vehs[driver_id]
            request = sim.inData.requests.loc[request_id]
            request, sim = pool_price_fun(sim, veh, request, sim.params.shareability)
            simpaxes = request.sim_schedule.req_id.dropna().unique()
            if len(simpaxes) == 0:
                if request_id in platform.reqQ:
                    platform.reqQ.pop(platform.reqQ.index(request_id))
                continue
            simpax = sim.pax[simpaxes[0]]
            if simpax.veh is not None:
                if request_id in platform.reqQ:
                    platform.reqQ.pop(platform.reqQ.index(request_id))
                continue

            wait_time = float(sim.skims.ride[request.origin][veh.veh.pos])
            veh.update(event=driverEvent.RECEIVES_REQUEST)
            offer_ids = []
            for pax_id in simpaxes:
                sim.pax[pax_id].update(event=travellerEvent.RECEIVES_OFFER)
                pax_request = sim.pax[pax_id].request
                travel_time_raw = pax_request.ttrav
                travel_time = travel_time_raw if isinstance(travel_time_raw, int) else travel_time_raw.total_seconds()
                offer = {
                    "pax_id": pax_id,
                    "req_id": pax_request.name,
                    "simpaxes": simpaxes,
                    "veh_id": driver_id,
                    "status": 0,
                    "request": pax_request,
                    "wait_time": wait_time,
                    "travel_time": travel_time,
                    "fare": platform.platform.fare * sim.pax[pax_id].request.dist / 1000,
                }
                platform.offers[pax_id] = offer
                sim.pax[pax_id].offers[platform.platform.name] = offer
                offer_ids.append(pax_id)

            if veh.f_driver_decline(veh=veh):
                veh.update(event=driverEvent.REJECTS_REQUEST)
                for pax_id in offer_ids:
                    platform.offers[pax_id]["status"] = -2
                    sim.pax[pax_id].update(event=travellerEvent.IS_REJECTED_BY_VEHICLE)
                    if platform.platform.name in sim.pax[pax_id].offers:
                        sim.pax[pax_id].offers.pop(platform.platform.name)
                platform.tabu.append((driver_id, request_id))
                platform.tabu.append((veh.veh.pos, request.origin))
            else:
                for pax_id in offer_ids:
                    if not sim.pax[pax_id].got_offered.triggered:
                        sim.pax[pax_id].got_offered.succeed()
                if driver_id in platform.vehQ:
                    platform.vehQ.pop(platform.vehQ.index(driver_id))
                if request_id in platform.reqQ:
                    platform.reqQ.pop(platform.reqQ.index(request_id))
        platform.updateQs()


def make_shadow_match_function(policy: MaaSSimDispatchPolicy, adapter: MaaSSimDispatchAdapter | None = None) -> Callable[..., None]:
    """Create a MaaSSim ``f_match`` wrapper that observes but does not intervene."""

    dispatch_adapter = adapter or MaaSSimDispatchAdapter()

    def f_match(**kwargs: Any) -> None:
        platform = kwargs["platform"]
        snapshot = dispatch_adapter.snapshot_from_platform(platform)
        policy.choose_assignment(snapshot)
        from MaaSSim.decisions import f_match as default_match  # type: ignore

        default_match(platform=platform)

    return f_match


def make_controlled_match_function(policy: MaaSSimDispatchPolicy, adapter: MaaSSimDispatchAdapter | None = None) -> Callable[..., None]:
    """Create a MaaSSim ``f_match`` replacement controlled by a dispatch policy."""

    dispatch_adapter = adapter or MaaSSimDispatchAdapter()

    def f_match(**kwargs: Any) -> None:
        platform = kwargs["platform"]
        while min(len(platform.vehQ), len(platform.reqQ)) > 0:
            snapshot = dispatch_adapter.snapshot_from_platform(platform)
            assignment = policy.choose_assignment(snapshot)
            if not assignment:
                break
            before = (len(platform.vehQ), len(platform.reqQ), len(platform.tabu))
            dispatch_adapter.apply_assignment(platform, assignment)
            after = (len(platform.vehQ), len(platform.reqQ), len(platform.tabu))
            if before == after:
                break

    return f_match
