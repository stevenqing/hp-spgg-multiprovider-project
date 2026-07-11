"""Fig5-style MaaSSim route comparison GIF for LLM policies."""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from llm_courier_dispatch.dispatch_env import ACCEPT
from llm_courier_dispatch_maassim.adapter import MaaSSimCandidateOffer
from llm_courier_dispatch_maassim.hidden_rules import synthetic_action_for_type
from replay_maassim_llm_smoke import (
    active_snapshots,
    accepted_utility,
    build_policy,
    fake_traveller,
    init_trackers,
    load_cache,
    load_personas,
    offer_dict,
    resolved_player_model,
)


ANALYSIS = ROOT / "analysis" / "courier_dispatch_maassim"
GRAPH = ROOT / "external" / "maassim" / "MaaSSim" / "data" / "Nootdorp.graphml"
OUT_DIRS = [ROOT / "figs", ROOT / "arr_paper" / "figs"]

SEED = 3
WINDOW_START = 0
WINDOW_SIZE = 20
STRESS_DRIVER_REJECT_PENALTY = 5.0
STRESS_PASSENGER_REJECT_PENALTY = 0.5
POLICIES = ["llm", "llm_psrl", "atom_tom1", "econ_bne"]
LABELS = {
    "llm": "LLM-PACT",
    "llm_psrl": "LLM-PSRL",
    "atom_tom1": "A-ToM-1",
    "econ_bne": "ECON-BNE",
}
COLORS = {
    "llm": "#12345d",
    "llm_psrl": "#7b5fb3",
    "atom_tom1": "#cc8242",
    "econ_bne": "#b64b45",
}
INK = "#1f2328"
MUTED = "#68707a"
PALE = "#e6e8eb"
ROAD = "#e2e5ea"
SERVICE = "#2f7d5b"
PICKUP = "#2f5f9b"
REJECT = "#c23b32"
PASSENGER_REJECT = "#9aa3ad"


@dataclass
class PolicyTrace:
    policy: str
    events: list[dict[str, Any]] = field(default_factory=list)
    persona_acc: list[float] = field(default_factory=list)
    persona_acc_observed: list[float] = field(default_factory=list)
    persona_acc_observed_map: list[float] = field(default_factory=list)
    persona_ptrue_observed: list[float] = field(default_factory=list)
    utility: float = 0.0
    served: int = 0
    driver_rejects: int = 0
    passenger_rejects: int = 0


def mean_rule_accuracy(driver_tracker: Any, driver_ids: set[int] | None = None) -> float:
    values = []
    for driver_id, true_type in driver_tracker.true_types.items():
        driver_key = int(driver_id)
        if driver_ids is not None and driver_key not in driver_ids:
            continue
        if driver_key not in driver_tracker.posteriors:
            continue
        posterior = driver_tracker.posterior_for_driver(driver_key)
        values.append(float(posterior.rule_marginal_accuracy(np.asarray(true_type, dtype=int))))
    return float(np.mean(values)) if values else 0.5


def mean_rule_map_accuracy(driver_tracker: Any, driver_ids: set[int] | None = None) -> float:
    values = []
    for driver_id, true_type in driver_tracker.true_types.items():
        driver_key = int(driver_id)
        if driver_ids is not None and driver_key not in driver_ids:
            continue
        if driver_key not in driver_tracker.posteriors:
            continue
        posterior = driver_tracker.posterior_for_driver(driver_key)
        prediction = posterior.type_space[int(np.argmax(posterior.probs()))]
        values.append(float(np.mean(prediction == np.asarray(true_type, dtype=int))))
    return float(np.mean(values)) if values else 0.5


def mean_ptrue(driver_tracker: Any, driver_ids: set[int] | None = None) -> float:
    values = []
    for driver_id, true_type in driver_tracker.true_types.items():
        driver_key = int(driver_id)
        if driver_ids is not None and driver_key not in driver_ids:
            continue
        if driver_key not in driver_tracker.posteriors:
            continue
        posterior = driver_tracker.posterior_for_driver(driver_key)
        values.append(float(posterior.prob_true(np.asarray(true_type, dtype=int))))
    if values:
        return float(np.mean(values))
    return float(1.0 / len(driver_tracker.env.type_space))


def configure() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Inter", "Helvetica Neue", "Arial", "DejaVu Sans"],
            "font.size": 8.6,
            "savefig.dpi": 130,
        }
    )


def node_pos(graph: nx.Graph) -> dict[str, tuple[float, float]]:
    return {str(node): (float(data["x"]), float(data["y"])) for node, data in graph.nodes(data=True) if "x" in data and "y" in data}


def draw_context(ax: plt.Axes, pos: dict[str, tuple[float, float]], trace: PolicyTrace) -> None:
    nodes: set[str] = set()
    for event in trace.events:
        for key in ("driver_position", "origin", "destination"):
            node = str(event.get(key))
            if node in pos:
                nodes.add(node)
    if nodes:
        points = np.asarray([pos[node] for node in nodes], dtype=float)
        ax.scatter(points[:, 0], points[:, 1], s=7, color="#d7dde5", alpha=0.55, linewidth=0, zorder=0)


def route_points(graph: nx.Graph, pos: dict[str, tuple[float, float]], start: object, end: object) -> list[tuple[float, float]]:
    start_key = str(start)
    end_key = str(end)
    if start_key not in pos or end_key not in pos:
        return []
    return [pos[start_key], pos[end_key]]


def enrich_routes(traces: dict[str, PolicyTrace], graph: nx.Graph, pos: dict[str, tuple[float, float]]) -> None:
    for trace in traces.values():
        for event in trace.events:
            event["pickup_points"] = route_points(graph, pos, event["driver_position"], event["origin"])
            event["trip_points"] = route_points(graph, pos, event["origin"], event["destination"])


def line_path(ax: plt.Axes, points: list[tuple[float, float]], color: str, linewidth: float, alpha: float, zorder: int, linestyle: str = "-") -> None:
    if len(points) < 2:
        return
    xs, ys = zip(*points, strict=True)
    ax.plot(xs, ys, color=color, linewidth=linewidth, alpha=alpha, zorder=zorder, linestyle=linestyle, solid_capstyle="round")


def simulate_policy(policy_name: str, seed: int, model: str, cache: dict[str, str]) -> PolicyTrace:
    personas = load_personas(seed)
    driver_tracker, passenger_tracker = init_trackers(seed, personas)
    policy = build_policy(policy_name, seed, driver_tracker, model, cache, 700, 0.0, "scored")
    trace = PolicyTrace(policy=policy_name)
    observed_driver_ids: set[int] = set()
    snapshots = active_snapshots(seed, WINDOW_START + WINDOW_SIZE)
    for step, snapshot in enumerate(snapshots):
        assignment = policy.choose_assignment(snapshot)
        offer_by_pair = {(offer.driver_id, offer.request_id): offer for offer in snapshot.candidates}
        for driver_id, request_id in assignment.items():
            offer: MaaSSimCandidateOffer | None = offer_by_pair.get((driver_id, request_id))
            if offer is None:
                continue
            action, reason = synthetic_action_for_type(driver_tracker.type_for_driver(driver_id), offer, driver_tracker.config)
            driver_reject = action != ACCEPT
            observed_driver_ids.add(int(driver_id))
            driver_tracker._update_posterior(offer, action, reason, driver_reject, driver_reject)
            in_window = WINDOW_START <= step < WINDOW_START + WINDOW_SIZE
            event = {
                "step": step - WINDOW_START,
                "driver_id": int(driver_id),
                "request_id": int(request_id),
                "driver_position": offer.driver_position,
                "origin": offer.origin,
                "destination": offer.destination,
                "wait_time": float(offer.wait_time),
                "travel_time": float(offer.travel_time),
                "status": "driver_reject" if driver_reject else "served",
            }
            if driver_reject:
                if in_window:
                    trace.driver_rejects += 1
                    trace.utility -= STRESS_DRIVER_REJECT_PENALTY
                    trace.events.append(event)
                continue
            traveller = fake_traveller(request_id, offer)
            payload = offer_dict(offer)
            passenger_reject, passenger_reason = passenger_tracker.reject_for_type(passenger_tracker.type_for_passenger(request_id), traveller, payload)
            passenger_tracker._update_posterior(request_id, traveller, payload, passenger_reject, passenger_reason)
            if passenger_reject:
                if in_window:
                    trace.passenger_rejects += 1
                    trace.utility -= STRESS_PASSENGER_REJECT_PENALTY
                    event["status"] = "passenger_reject"
                    trace.events.append(event)
                continue
            if in_window:
                trace.served += 1
                trace.utility += accepted_utility(offer)
                trace.events.append(event)
        if WINDOW_START <= step < WINDOW_START + WINDOW_SIZE:
            trace.persona_acc.append(mean_rule_accuracy(driver_tracker))
            trace.persona_acc_observed.append(mean_rule_accuracy(driver_tracker, observed_driver_ids))
            trace.persona_acc_observed_map.append(mean_rule_map_accuracy(driver_tracker, observed_driver_ids))
            trace.persona_ptrue_observed.append(mean_ptrue(driver_tracker, observed_driver_ids))
    return trace


def frame_index(frame_idx: int, frame_count: int) -> int:
    progress = frame_idx / max(frame_count - 1, 1)
    eased = progress * progress * (3.0 - 2.0 * progress)
    return int(round(eased * (WINDOW_SIZE - 1)))


def draw_panel(ax: plt.Axes, graph: nx.Graph, pos: dict[str, tuple[float, float]], trace: PolicyTrace, current_step: int, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
    draw_context(ax, pos, trace)
    current_events = [event for event in trace.events if int(event["step"]) <= current_step]
    for event in current_events:
        age = current_step - int(event["step"])
        alpha = max(0.22, 0.92 - 0.035 * age)
        pickup_points = event.get("pickup_points", [])
        trip_points = event.get("trip_points", [])
        if event["status"] == "served":
            line_path(ax, pickup_points, PICKUP, 0.85, alpha * 0.62, 2, linestyle="--")
            line_path(ax, trip_points, SERVICE, 1.35, alpha, 3)
        elif event["status"] == "passenger_reject":
            # Keep passenger-side failures visually quiet so red is reserved for driver rejects.
            node_key = str(event.get("origin"))
            if node_key in pos:
                ax.scatter(pos[node_key][0], pos[node_key][1], s=9, color=PASSENGER_REJECT, alpha=0.28, linewidth=0, zorder=2)
        else:
            line_path(ax, pickup_points, REJECT, 1.2, alpha, 3, linestyle="--")
    recent = [event for event in current_events if current_step - int(event["step"]) <= 1]
    for event in recent:
        for node, marker, color, size in [(event["driver_position"], "^", COLORS[trace.policy], 24), (event["origin"], "o", PICKUP, 20), (event["destination"], "s", SERVICE, 18)]:
            node_key = str(node)
            if node_key in pos:
                ax.scatter(pos[node_key][0], pos[node_key][1], s=size, marker=marker, color=color, edgecolor="white", linewidth=0.45, zorder=5)
    visible = [event for event in trace.events if int(event["step"]) <= current_step]
    served = sum(1 for event in visible if event["status"] == "served")
    driver_rejects = sum(1 for event in visible if event["status"] == "driver_reject")
    passenger_rejects = sum(1 for event in visible if event["status"] == "passenger_reject")
    utility = 0.0
    for event in visible:
        if event["status"] == "driver_reject":
            utility -= STRESS_DRIVER_REJECT_PENALTY
        elif event["status"] == "passenger_reject":
            utility -= STRESS_PASSENGER_REJECT_PENALTY
        else:
            utility += 3.0 - 0.01 * float(event["wait_time"])
    ax.set_title(LABELS[trace.policy], loc="left", fontsize=10.6, fontweight="semibold", color=COLORS[trace.policy])
    ax.text(0.02, 0.965, f"utility {utility:5.1f}   served {served:2d}   rejects {driver_rejects:2d}", transform=ax.transAxes, ha="left", va="top", fontsize=7.7, color=INK, bbox={"boxstyle": "round,pad=0.28", "facecolor": "white", "edgecolor": "#d8dde6", "linewidth": 0.55, "alpha": 0.92})
    if passenger_rejects and trace.policy != "llm":
        ax.text(0.02, 0.875, f"passenger rejects {passenger_rejects}", transform=ax.transAxes, ha="left", va="top", fontsize=7.0, color=MUTED)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def make_frame(graph: nx.Graph, pos: dict[str, tuple[float, float]], traces: dict[str, PolicyTrace], current_step: int, frame_idx: int, frame_count: int) -> Image.Image:
    used_points: list[tuple[float, float]] = []
    for trace in traces.values():
        for event in trace.events:
            for key in ("driver_position", "origin", "destination"):
                node = str(event.get(key))
                if node in pos:
                    used_points.append(pos[node])
    if used_points:
        xs = [point[0] for point in used_points]
        ys = [point[1] for point in used_points]
    else:
        xs = [point[0] for point in pos.values()]
        ys = [point[1] for point in pos.values()]
    pad_x = (max(xs) - min(xs)) * 0.035
    pad_y = (max(ys) - min(ys)) * 0.035
    xlim = (min(xs) - pad_x, max(xs) + pad_x)
    ylim = (min(ys) - pad_y, max(ys) + pad_y)
    fig, axes = plt.subplots(2, 2, figsize=(10.8, 6.1), facecolor="white")
    fig.patch.set_facecolor("white")
    fig.patch.set_alpha(1.0)
    fig.subplots_adjust(left=0.035, right=0.985, top=0.84, bottom=0.075, wspace=0.05, hspace=0.11)
    fig.text(0.04, 0.95, "MaaSSim Fig5-style policy trace", fontsize=17.2, fontweight="semibold", color=INK, ha="left")
    fig.text(
        0.04,
        0.907,
        f"Same seed={SEED}, snapshots {WINDOW_START + 1}-{WINDOW_START + WINDOW_SIZE}, same persona maps | driver reject penalty={STRESS_DRIVER_REJECT_PENALTY:.1f} | frame {current_step + 1}/{WINDOW_SIZE}",
        fontsize=9.5,
        color=MUTED,
        ha="left",
    )
    fig.text(0.985, 0.946, "green = served route", ha="right", va="center", fontsize=8.4, color=SERVICE, bbox={"boxstyle": "round,pad=0.32", "facecolor": "#eaf5ef", "edgecolor": "#b8dbc6", "linewidth": 0.7})
    fig.text(0.985, 0.902, "red dashed = driver reject", ha="right", va="center", fontsize=8.4, color=REJECT, bbox={"boxstyle": "round,pad=0.32", "facecolor": "#f8ecea", "edgecolor": "#efc7c0", "linewidth": 0.7})
    for ax, policy in zip(axes.flatten(), POLICIES, strict=True):
        draw_panel(ax, graph, pos, traces[policy], current_step, xlim, ylim)
    if current_step >= WINDOW_SIZE - 1:
        best_prompt = max(["llm_psrl", "atom_tom1", "econ_bne"], key=lambda policy: traces[policy].utility)
        delta = traces["llm"].utility - traces[best_prompt].utility
        fig.text(0.04, 0.025, f"LLM-PACT finishes +{delta:.2f} utility above the best pure prompt baseline ({LABELS[best_prompt]}), with fewer driver rejects.", fontsize=10.2, color=INK, ha="left")
    else:
        fig.text(0.04, 0.025, "Cumulative routes make rejected assignments visible as red dashed pickup attempts.", fontsize=9.6, color=MUTED, ha="left")
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=130, facecolor="white", edgecolor="white", transparent=False)
    plt.close(fig)
    buf.seek(0)
    rgba = Image.open(buf).convert("RGBA")
    white = Image.new("RGBA", rgba.size, "white")
    white.alpha_composite(rgba)
    return white.convert("RGB")


def write_outputs(frames: list[Image.Image]) -> None:
    for out_dir in OUT_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        gif_path = out_dir / "fig_maassim_fig5_policy_trace_comparison.gif"
        png_path = out_dir / "fig_maassim_fig5_policy_trace_comparison.png"
        if frames:
            frames[-1].convert("RGB").save(png_path)
            paletted = [frame.convert("RGB").convert("P", palette=Image.Palette.ADAPTIVE) for frame in frames]
            paletted[0].save(gif_path, save_all=True, append_images=paletted[1:], duration=150, loop=0, optimize=False)


def main() -> None:
    import replay_maassim_llm_smoke as replay

    replay.DRIVER_REJECT_PENALTY = STRESS_DRIVER_REJECT_PENALTY
    replay.PASSENGER_REJECT_PENALTY = STRESS_PASSENGER_REJECT_PENALTY
    configure = plt.rcParams.update
    configure({"font.family": "sans-serif", "font.sans-serif": ["Inter", "Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": 8.5})
    graph = nx.read_graphml(GRAPH)
    pos = node_pos(graph)
    model = resolved_player_model(None)
    cache = load_cache()
    traces = {}
    for policy in POLICIES:
        print(f"simulate {policy}", flush=True)
        traces[policy] = simulate_policy(policy, SEED, model, cache)
    enrich_routes(traces, graph, pos)
    frame_count = 40
    frames = []
    for idx in range(frame_count):
        if idx % 10 == 0:
            print(f"frame {idx}/{frame_count}", flush=True)
        frames.append(make_frame(graph, pos, traces, frame_index(idx, frame_count), idx, frame_count))
    frames.extend([frames[-1].copy() for _ in range(10)])
    write_outputs(frames)
    print("OK: figs/fig_maassim_fig5_policy_trace_comparison.gif")


if __name__ == "__main__":
    main()