"""Generate MaaSSim-style experiment figures for the PACT paper.

The figures follow the visual grammar used by MaaSSim examples: spatial demand
and vehicle maps, route traces on the road graph, and processed KPI panels.
"""

from __future__ import annotations

import ast
import csv
import json
import math
import sys
from io import BytesIO
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.collections import LineCollection
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
for path in (ROOT, SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import animate_maassim_fig5_policy_comparison as trace
import replay_maassim_llm_smoke as replay


ANALYSIS = ROOT / "analysis" / "courier_dispatch_maassim"
FIG_DIRS = [ROOT / "figs", ROOT / "arr_paper" / "figs"]
GRAPH = ROOT / "external" / "maassim" / "MaaSSim" / "data" / "Nootdorp.graphml"

POLICY_ORDER = ["llm", "llm_belief", "llm_psrl", "atom_tom1", "econ_bne", "oracle"]
PROMPT_POLICIES = ["llm_belief", "llm_psrl", "atom_tom1", "econ_bne"]
EPISODE_POLICIES = ["llm", "llm_psrl", "atom_tom1", "econ_bne"]
POLICY_LABELS = {
    "llm": "LLM-PACT",
    "llm_belief": "LLM-belief",
    "llm_psrl": "LLM-PSRL",
    "atom_tom0": "A-ToM-0",
    "atom_tom1": "A-ToM-1",
    "econ_bne": "ECON-BNE",
    "oracle": "Oracle",
    "nearest": "Nearest",
    "random": "Random",
    "pact_prior": "PACT-prior",
    "pact_shuffled": "PACT-shuffled",
    "pact": "PACT",
}
COLORS = {
    "llm": "#12345d",
    "llm_belief": "#557a95",
    "llm_psrl": "#7b5fb3",
    "atom_tom0": "#b79d5d",
    "atom_tom1": "#cc8242",
    "econ_bne": "#b64b45",
    "oracle": "#2f7d5b",
    "nearest": "#8c8c8c",
    "random": "#555555",
    "pact_prior": "#b9cce8",
    "pact_shuffled": "#d18a7a",
    "pact": "#12345d",
}
INK = "#1f2328"
MUTED = "#68707a"
ROAD = "#d9e0e8"
ORIGIN = "#2f5f9b"
DEST = "#2f7d5b"
VEH = "#343a40"
REJECT = "#c23b32"
SERVICE = "#2f7d5b"
PICKUP = "#2f5f9b"


def configure() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Inter", "Helvetica Neue", "Arial", "DejaVu Sans"],
            "font.size": 9,
            "savefig.dpi": 150,
        }
    )


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def f(row: dict[str, Any], key: str, default: float = float("nan")) -> float:
    try:
        return float(row.get(key, default))
    except Exception:
        return default


def save_figure(fig: plt.Figure, stem: str) -> None:
    for out_dir in FIG_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        png_buffer = BytesIO()
        fig.savefig(png_buffer, format="png", bbox_inches="tight", facecolor="white", edgecolor="white", transparent=False)
        png_buffer.seek(0)
        rgba = Image.open(png_buffer).convert("RGBA")
        white = Image.new("RGBA", rgba.size, "white")
        white.alpha_composite(rgba)
        white.convert("RGB").save(out_dir / f"{stem}.png")
        fig.savefig(out_dir / f"{stem}.pdf", bbox_inches="tight", facecolor="white")


def style_axis(ax: plt.Axes, *, grid: bool = True) -> None:
    if grid:
        ax.grid(axis="y", linestyle=":", linewidth=0.6, color="#d9dde3")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#d8dde6")
    ax.spines["bottom"].set_color("#d8dde6")
    ax.tick_params(colors=MUTED)


def node_pos(graph: nx.Graph) -> dict[str, tuple[float, float]]:
    return {str(node): (float(data["x"]), float(data["y"])) for node, data in graph.nodes(data=True) if "x" in data and "y" in data}


def bounds(points: list[tuple[float, float]], pad_frac: float = 0.10) -> tuple[tuple[float, float], tuple[float, float]]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    pad_x = max((max(xs) - min(xs)) * pad_frac, 1e-6)
    pad_y = max((max(ys) - min(ys)) * pad_frac, 1e-6)
    return (min(xs) - pad_x, max(xs) + pad_x), (min(ys) - pad_y, max(ys) + pad_y)


def segment_in_bounds(a: tuple[float, float], b: tuple[float, float], xlim: tuple[float, float], ylim: tuple[float, float]) -> bool:
    return not (max(a[0], b[0]) < xlim[0] or min(a[0], b[0]) > xlim[1] or max(a[1], b[1]) < ylim[0] or min(a[1], b[1]) > ylim[1])


def road_segments(graph: nx.Graph, pos: dict[str, tuple[float, float]], xlim: tuple[float, float], ylim: tuple[float, float], max_segments: int = 4500) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    segments = []
    for u, v in graph.edges():
        u_key = str(u)
        v_key = str(v)
        if u_key not in pos or v_key not in pos:
            continue
        a = pos[u_key]
        b = pos[v_key]
        if segment_in_bounds(a, b, xlim, ylim):
            segments.append((a, b))
            if len(segments) >= max_segments:
                break
    return segments


def draw_roads(ax: plt.Axes, segments: list[tuple[tuple[float, float], tuple[float, float]]], linewidth: float = 0.58, alpha: float = 0.78) -> None:
    if segments:
        ax.add_collection(LineCollection(segments, colors=ROAD, linewidths=linewidth, alpha=alpha, zorder=0, capstyle="round"))


def draw_line(ax: plt.Axes, points: list[tuple[float, float]], color: str, linewidth: float, alpha: float, linestyle: str = "-", zorder: int = 3) -> None:
    if len(points) < 2:
        return
    xs, ys = zip(*points, strict=True)
    ax.plot(xs, ys, color=color, linewidth=linewidth, alpha=alpha, linestyle=linestyle, solid_capstyle="round", zorder=zorder)


def heatmap(ax: plt.Axes, matrix: np.ndarray, xlabels: list[object], ylabels: list[object], *, title: str, cbar_label: str, cmap: str = "viridis") -> None:
    masked = np.ma.masked_invalid(matrix)
    image = ax.imshow(masked, origin="lower", aspect="auto", cmap=cmap)
    ax.set_title(title, loc="left", fontweight="semibold", color=INK)
    ax.set_xticks(np.arange(len(xlabels)))
    ax.set_yticks(np.arange(len(ylabels)))
    ax.set_xticklabels([str(label) for label in xlabels])
    ax.set_yticklabels([str(label) for label in ylabels])
    ax.tick_params(colors=MUTED, labelsize=8.2)
    for spine in ax.spines.values():
        spine.set_color("#d8dde6")
    cbar = plt.colorbar(image, ax=ax, fraction=0.046, pad=0.035)
    cbar.set_label(cbar_label, color=MUTED)
    cbar.ax.tick_params(colors=MUTED, labelsize=8.0)


def matrix_from_groups(rows: list[dict[str, Any]], xkey: str, ykey: str, value_key: str) -> tuple[np.ndarray, list[object], list[object]]:
    xlabels = sorted({row[xkey] for row in rows})
    ylabels = sorted({row[ykey] for row in rows})
    matrix = np.full((len(ylabels), len(xlabels)), np.nan, dtype=float)
    for yi, ylabel in enumerate(ylabels):
        for xi, xlabel in enumerate(xlabels):
            values = [float(row[value_key]) for row in rows if row[xkey] == xlabel and row[ykey] == ylabel and not math.isnan(float(row[value_key]))]
            if values:
                matrix[yi, xi] = float(np.mean(values))
    return matrix, xlabels, ylabels


def all_snapshot_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for seed in range(10):
        path = ANALYSIS / f"nearest_persona_v2_main_s{seed}_queue_snapshots.jsonl"
        if not path.exists():
            continue
        for snapshot in load_snapshots(path):
            candidates = list(snapshot.get("candidates", []))
            if not candidates:
                continue
            wait_values = [float(offer.get("wait_time", 0.0)) for offer in candidates]
            request_ids = {int(offer.get("request_id")) for offer in candidates}
            driver_ids = {int(offer.get("driver_id")) for offer in candidates}
            rows.append(
                {
                    "seed": seed,
                    "request_queue": len(snapshot.get("request_queue", [])),
                    "vehicle_queue": len(snapshot.get("vehicle_queue", [])),
                    "requests_with_offers": len(request_ids),
                    "drivers_with_offers": len(driver_ids),
                    "candidate_count": len(candidates),
                    "best_pickup_wait": float(min(wait_values)),
                    "mean_pickup_wait": float(np.mean(wait_values)),
                    "offers_per_request": float(len(candidates) / max(1, len(request_ids))),
                    "idle_vehicle_pressure": float(max(0, len(snapshot.get("vehicle_queue", [])) - len(snapshot.get("request_queue", [])))),
                }
            )
    return rows


def plot_readme_fig2_service_surface() -> None:
    rows = all_snapshot_rows()
    capped_rows = []
    for row in rows:
        demand = min(int(row["request_queue"]), 8)
        supply = min(int(row["vehicle_queue"]), 8)
        if demand <= 0 or supply <= 0:
            continue
        capped_rows.append({**row, "demand": demand, "supply": supply})
    wait_matrix, supply_labels, demand_labels = matrix_from_groups(capped_rows, "supply", "demand", "best_pickup_wait")
    menu_matrix, _, _ = matrix_from_groups(capped_rows, "supply", "demand", "offers_per_request")
    pressure_matrix, _, _ = matrix_from_groups(capped_rows, "supply", "demand", "idle_vehicle_pressure")

    fig, axes = plt.subplots(1, 3, figsize=(12.1, 3.65), facecolor="white")
    fig.suptitle("README Fig. 2 analogue: service performance across demand and supply", x=0.02, y=1.05, ha="left", fontsize=15.5, fontweight="semibold", color=INK)
    fig.text(0.02, 0.965, "Common MaaSSim queue states binned by queued requests and idle vehicles; lower pickup wait is better for travellers", ha="left", fontsize=9.2, color=MUTED)
    heatmap(axes[0], wait_matrix, supply_labels, demand_labels, title="Traveller pickup wait", cbar_label="seconds", cmap="YlGnBu_r")
    heatmap(axes[1], menu_matrix, supply_labels, demand_labels, title="Legal offers per request", cbar_label="offers", cmap="BuGn")
    heatmap(axes[2], pressure_matrix, supply_labels, demand_labels, title="Driver idle pressure", cbar_label="idle vehicles", cmap="Oranges")
    for ax in axes:
        ax.set_xlabel("idle vehicles in queue")
        ax.set_ylabel("queued requests")
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    save_figure(fig, "fig_maassim_readme_fig2_service_surface")
    plt.close(fig)


def plot_readme_fig3_platform_strategy() -> None:
    rows = read_csv_rows(ANALYSIS / "maassim_kpi_calibration_sweep.csv")
    selected = [row for row in rows if abs(float(row["fare_weight"]) - 0.5) < 1e-9]
    for row in selected:
        row["wait_weight_f"] = float(row["wait_weight"])
        row["reject_penalty_f"] = float(row["reject_penalty"])
        row["utility_proxy"] = float(row["rides"]) * 3.0 - 0.01 * float(row["mean_wait"]) - float(row["reject_penalty"]) * float(row["rejects"])
    wait_matrix, penalties, weights = matrix_from_groups(selected, "reject_penalty_f", "wait_weight_f", "mean_wait")
    ride_matrix, _, _ = matrix_from_groups(selected, "reject_penalty_f", "wait_weight_f", "rides")
    reject_matrix, _, _ = matrix_from_groups(selected, "reject_penalty_f", "wait_weight_f", "rejects")
    utility_matrix, _, _ = matrix_from_groups(selected, "reject_penalty_f", "wait_weight_f", "utility_proxy")
    fig, axes = plt.subplots(2, 2, figsize=(9.8, 7.2), facecolor="white")
    fig.suptitle("README Fig. 3 analogue: platform dispatch strategy search", x=0.02, y=0.99, ha="left", fontsize=15.5, fontweight="semibold", color=INK)
    fig.text(0.02, 0.948, "PACT objective sweep with fare_weight=0.5; axes are dispatch objective weights", ha="left", fontsize=9.2, color=MUTED)
    panels = [
        (wait_matrix, "Passenger wait", "seconds", "YlGnBu_r"),
        (ride_matrix, "Completed rides", "rides", "BuGn"),
        (reject_matrix, "Driver rejects", "rejects", "OrRd"),
        (utility_matrix, "Utility proxy", "score", "PuBuGn"),
    ]
    for ax, (matrix, title, label, cmap) in zip(axes.flatten(), panels, strict=True):
        heatmap(ax, matrix, penalties, weights, title=title, cbar_label=label, cmap=cmap)
        ax.set_xlabel("driver reject penalty")
        ax.set_ylabel("wait weight")
    fig.tight_layout(rect=[0, 0, 1, 0.91])
    save_figure(fig, "fig_maassim_readme_fig3_platform_strategy")
    plt.close(fig)


def posterior_learning_rows() -> list[dict[str, float]]:
    rows = []
    for seed in range(10):
        path = ANALYSIS / f"pact_kpi_persona_v2_main_s{seed}_driver_posterior.csv"
        if not path.exists():
            continue
        for idx, row in enumerate(read_csv_rows(path)):
            rows.append(
                {
                    "seed": float(seed),
                    "event": float(idx),
                    "time_min": f(row, "time") / 60.0,
                    "ptrue": f(row, "ptrue"),
                    "rule_acc": f(row, "rule_acc"),
                    "declined": 1.0 if str(row.get("actual_declined", "False")).lower() == "true" else 0.0,
                    "wait_time": f(row, "wait_time"),
                }
            )
    return rows


def binned_mean(rows: list[dict[str, float]], key: str, value: str, bins: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    centers = (bins[:-1] + bins[1:]) / 2.0
    means = np.full(len(centers), np.nan)
    sems = np.zeros(len(centers))
    for idx, (lo, hi) in enumerate(zip(bins[:-1], bins[1:], strict=True)):
        values = [row[value] for row in rows if lo <= row[key] < hi and not math.isnan(row[value])]
        if values:
            means[idx] = float(np.mean(values))
            sems[idx] = float(np.std(values, ddof=1) / math.sqrt(len(values))) if len(values) > 1 else 0.0
    return centers, means, sems


def plot_readme_fig4_driver_learning() -> None:
    rows = posterior_learning_rows()
    bins = np.linspace(0.0, max(row["time_min"] for row in rows) + 1e-6, 11)
    fig, axes = plt.subplots(1, 3, figsize=(11.2, 3.55), facecolor="white")
    fig.suptitle("README Fig. 4 analogue: driver-persona learning dynamics", x=0.02, y=1.05, ha="left", fontsize=15.5, fontweight="semibold", color=INK)
    fig.text(0.02, 0.965, "PACT updates hidden driver-persona beliefs from accept/reject events within MaaSSim episodes", ha="left", fontsize=9.2, color=MUTED)
    specs = [
        ("ptrue", "Exact persona posterior", "P(true persona)", COLORS["llm"]),
        ("rule_acc", "Rule marginal accuracy", "accuracy", COLORS["oracle"]),
        ("declined", "Observed decline rate", "decline rate", REJECT),
    ]
    for ax, (value, title, ylabel, color) in zip(axes, specs, strict=True):
        centers, means, sems = binned_mean(rows, "time_min", value, bins)
        ax.plot(centers, means, color=color, linewidth=2.0)
        ax.fill_between(centers, means - sems, means + sems, color=color, alpha=0.16, linewidth=0)
        ax.set_title(title, loc="left", fontweight="semibold", color=INK)
        ax.set_xlabel("simulation minute")
        ax.set_ylabel(ylabel)
        style_axis(ax)
    axes[0].axhline(1.0 / 16.0, color="#9aa3ad", linestyle="--", linewidth=0.9)
    axes[1].axhline(0.5, color="#9aa3ad", linestyle="--", linewidth=0.9)
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    save_figure(fig, "fig_maassim_readme_fig4_driver_learning")
    plt.close(fig)


def parse_paxes(raw: str) -> list[int]:
    try:
        value = ast.literal_eval(raw)
    except Exception:
        return []
    if isinstance(value, list):
        return [int(item) for item in value]
    return []


def vehicle_trace_rows(policy_prefix: str, seed: int = 0) -> tuple[int, list[dict[str, Any]]]:
    rows = read_csv_rows(ANALYSIS / f"{policy_prefix}_persona_v2_main_s{seed}_rides.csv")
    by_vehicle: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        vehicle = int(float(row["veh"]))
        by_vehicle.setdefault(vehicle, []).append(row)
    vehicle_id = max(by_vehicle, key=lambda veh_id: len({str(row["pos"]) for row in by_vehicle[veh_id]}) + len(by_vehicle[veh_id]) * 0.01)
    return vehicle_id, by_vehicle[vehicle_id]


def draw_vehicle_trace(ax: plt.Axes, graph: nx.Graph, pos: dict[str, tuple[float, float]], policy_prefix: str, title: str) -> None:
    vehicle_id, rows = vehicle_trace_rows(policy_prefix)
    points = [pos[str(int(float(row["pos"])))] for row in rows if str(int(float(row["pos"]))) in pos]
    if not points:
        return
    xlim, ylim = bounds(points, pad_frac=0.18)
    draw_roads(ax, road_segments(graph, pos, xlim, ylim, max_segments=2400), linewidth=0.48, alpha=0.70)
    prev_point: tuple[float, float] | None = None
    prev_loaded = False
    for row in rows:
        node = str(int(float(row["pos"])))
        if node not in pos:
            continue
        point = pos[node]
        loaded = bool(parse_paxes(str(row.get("paxes", "[]"))))
        if prev_point is not None and point != prev_point:
            color = SERVICE if prev_loaded else "#20242a"
            linewidth = 2.2 if prev_loaded else 1.35
            draw_line(ax, [prev_point, point], color, linewidth, 0.82, zorder=3)
        marker_color = REJECT if "REJECT" in str(row.get("event", "")) else (SERVICE if loaded else PICKUP)
        ax.scatter(point[0], point[1], s=20, color=marker_color, edgecolor="white", linewidth=0.45, zorder=4)
        prev_point = point
        prev_loaded = loaded
    ax.set_title(f"{title}: vehicle {vehicle_id}", loc="left", fontweight="semibold", color=INK)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def driver_event_utility(events: list[dict[str, Any]]) -> float:
    total = 0.0
    for event in events:
        delta, _, _ = event_increment(event)
        total += delta
    return float(total)


def choose_contrast_driver(left: trace.PolicyTrace, right: trace.PolicyTrace) -> int:
    drivers = {int(event["driver_id"]) for event in left.events + right.events}
    best_driver = sorted(drivers)[0]
    best_score = float("-inf")
    for driver_id in drivers:
        left_events = [event for event in left.events if int(event["driver_id"]) == driver_id]
        right_events = [event for event in right.events if int(event["driver_id"]) == driver_id]
        score = abs(driver_event_utility(left_events) - driver_event_utility(right_events)) + 0.5 * abs(len(left_events) - len(right_events))
        if score > best_score:
            best_score = score
            best_driver = driver_id
    return best_driver


def draw_policy_driver_trace(ax: plt.Axes, graph: nx.Graph, pos: dict[str, tuple[float, float]], policy_trace: trace.PolicyTrace, driver_id: int, title: str) -> None:
    events = [event for event in policy_trace.events if int(event["driver_id"]) == driver_id]
    points = []
    for event in events:
        for key in ("driver_position", "origin", "destination"):
            node = str(event.get(key))
            if node in pos:
                points.append(pos[node])
    if not points:
        ax.set_title(title, loc="left", fontweight="semibold", color=INK)
        ax.set_xticks([])
        ax.set_yticks([])
        return
    xlim, ylim = bounds(points, pad_frac=0.22)
    draw_roads(ax, road_segments(graph, pos, xlim, ylim, max_segments=2600), linewidth=0.48, alpha=0.70)
    for event in events:
        pickup = event.get("pickup_points", [])
        trip = event.get("trip_points", [])
        if event["status"] == "served":
            draw_line(ax, pickup, "#20242a", 1.35, 0.68, linestyle="--", zorder=2)
            draw_line(ax, trip, SERVICE, 2.15, 0.86, zorder=3)
            if trip:
                ax.scatter(trip[0][0], trip[0][1], s=26, color=PICKUP, edgecolor="white", linewidth=0.45, zorder=4)
                ax.scatter(trip[-1][0], trip[-1][1], s=30, marker="^", color=SERVICE, edgecolor="white", linewidth=0.45, zorder=4)
        elif event["status"] == "driver_reject":
            draw_line(ax, pickup, REJECT, 1.45, 0.82, linestyle="--", zorder=3)
            if pickup:
                ax.scatter(pickup[-1][0], pickup[-1][1], marker="x", s=38, color=REJECT, linewidth=1.6, zorder=5)
    served = sum(1 for event in events if event["status"] == "served")
    rejects = sum(1 for event in events if event["status"] == "driver_reject")
    utility = driver_event_utility(events)
    ax.set_title(f"{title}: driver {driver_id}   utility {utility:.1f}   served {served}   rejects {rejects}", loc="left", fontweight="semibold", color=COLORS.get(policy_trace.policy, INK))
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def plot_readme_fig5_vehicle_trace(graph: nx.Graph, pos: dict[str, tuple[float, float]]) -> None:
    configure_conflict_episode()
    model = trace.resolved_player_model(None)
    cache = trace.load_cache()
    traces = {policy: trace.simulate_policy(policy, trace.SEED, model, cache) for policy in ("llm", "econ_bne")}
    trace.enrich_routes(traces, graph, pos)
    driver_id = choose_contrast_driver(traces["llm"], traces["econ_bne"])
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.8), facecolor="white")
    fig.suptitle("README Fig. 5 analogue: single-vehicle MaaSSim ride traces", x=0.02, y=1.03, ha="left", fontsize=15.5, fontweight="semibold", color=INK)
    fig.text(0.02, 0.947, "Conflict-offer replay for the same driver; black dashed pickup movement, green service, red rejected offer", ha="left", fontsize=9.2, color=MUTED)
    draw_policy_driver_trace(axes[0], graph, pos, traces["llm"], driver_id, "LLM-PACT")
    draw_policy_driver_trace(axes[1], graph, pos, traces["econ_bne"], driver_id, "ECON-BNE")
    save_figure(fig, "fig_maassim_readme_fig5_vehicle_trace")
    plt.close(fig)


def plot_scenario_dashboard() -> None:
    rows = read_csv_rows(ANALYSIS / "maassim_llm_scenario_suite_detail.csv")
    scenarios = ["Normal", "Reject-stress", "Conflict-offer"]
    by_key = {(row["scenario"], row["policy"]): row for row in rows}
    x = np.arange(len(scenarios))
    width = 0.12
    fig, axes = plt.subplots(2, 2, figsize=(11.0, 7.0), facecolor="white")
    fig.suptitle("MaaSSim LLM policy experiment suite", x=0.02, y=0.99, ha="left", fontsize=16, fontweight="semibold", color=INK)
    fig.text(0.02, 0.946, "Common MaaSSim queue states; identical legal assignments; hidden driver personas", ha="left", fontsize=9.8, color=MUTED)

    for idx, policy in enumerate(POLICY_ORDER):
        offset = (idx - (len(POLICY_ORDER) - 1) / 2) * width
        values = [f(by_key[(scenario, policy)], "utility") for scenario in scenarios]
        sems = [f(by_key[(scenario, policy)], "utility_sem", 0.0) for scenario in scenarios]
        axes[0, 0].bar(x + offset, values, width=width, color=COLORS[policy], edgecolor="white", linewidth=0.5, label=POLICY_LABELS[policy])
        axes[0, 0].errorbar(x + offset, values, yerr=sems, fmt="none", ecolor="#5f6873", elinewidth=0.7, capsize=1.5, alpha=0.7)
        rejects = [f(by_key[(scenario, policy)], "driver_rejects") for scenario in scenarios]
        axes[0, 1].bar(x + offset, rejects, width=width, color=COLORS[policy], edgecolor="white", linewidth=0.5)

    axes[0, 0].axhline(0, color="#aab2bd", linewidth=0.8)
    axes[0, 0].set_title("Realized utility", loc="left", fontweight="semibold", color=INK)
    axes[0, 0].set_ylabel("utility")
    axes[0, 0].legend(ncol=3, frameon=False, fontsize=8, loc="upper left")
    axes[0, 1].set_title("Driver rejects", loc="left", fontweight="semibold", color=INK)
    axes[0, 1].set_ylabel("reject count")

    gap = []
    reject_gap = []
    oracle_headroom = []
    for scenario in scenarios:
        llm = by_key[(scenario, "llm")]
        best_prompt = max(PROMPT_POLICIES, key=lambda policy: f(by_key[(scenario, policy)], "utility"))
        best = by_key[(scenario, best_prompt)]
        oracle = by_key[(scenario, "oracle")]
        gap.append(f(llm, "utility") - f(best, "utility"))
        reject_gap.append(f(best, "driver_rejects") - f(llm, "driver_rejects"))
        oracle_headroom.append(f(oracle, "utility") - f(llm, "utility"))
    axes[1, 0].bar(x - 0.17, gap, width=0.32, color=COLORS["llm"], edgecolor="white", label="LLM-PACT minus best prompt")
    axes[1, 0].bar(x + 0.17, oracle_headroom, width=0.32, color=COLORS["oracle"], edgecolor="white", label="Oracle headroom")
    axes[1, 0].set_title("Gap decomposition", loc="left", fontweight="semibold", color=INK)
    axes[1, 0].set_ylabel("utility")
    axes[1, 0].legend(frameon=False, fontsize=8, loc="upper left")
    axes[1, 1].bar(x, reject_gap, color="#2f7d5b", edgecolor="white")
    axes[1, 1].set_title("Fewer rejects than best prompt", loc="left", fontweight="semibold", color=INK)
    axes[1, 1].set_ylabel("driver rejects avoided")

    for ax in axes.flatten():
        ax.set_xticks(x)
        ax.set_xticklabels(scenarios, rotation=13, ha="right")
        style_axis(ax)
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    save_figure(fig, "fig_maassim_experiment_scenario_dashboard")
    plt.close(fig)


def load_snapshots(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
        if limit is not None and len(rows) >= limit:
            break
    return rows


def plot_demand_supply_overview(graph: nx.Graph, pos: dict[str, tuple[float, float]]) -> None:
    snapshots = load_snapshots(ANALYSIS / "nearest_persona_v2_main_s0_queue_snapshots.jsonl", limit=36)
    request_seen: dict[int, dict[str, Any]] = {}
    vehicle_nodes: set[str] = set()
    timeline = []
    for snapshot in snapshots:
        candidates = list(snapshot.get("candidates", []))
        timeline.append(
            {
                "time": float(snapshot.get("time", 0.0)),
                "candidate_count": len(candidates),
                "request_queue": len(snapshot.get("request_queue", [])),
                "vehicle_queue": len(snapshot.get("vehicle_queue", [])),
            }
        )
        for offer in candidates:
            vehicle_nodes.add(str(offer.get("driver_position")))
            request_id = int(offer.get("request_id"))
            request_seen.setdefault(request_id, offer)
    origin_nodes = [str(row["origin"]) for row in request_seen.values() if str(row.get("origin")) in pos]
    dest_nodes = [str(row["destination"]) for row in request_seen.values() if str(row.get("destination")) in pos]
    vehicle_nodes = {node for node in vehicle_nodes if node in pos}
    points = [pos[node] for node in origin_nodes + dest_nodes + list(vehicle_nodes)]
    xlim, ylim = bounds(points, pad_frac=0.12)
    segments = road_segments(graph, pos, xlim, ylim)
    travel_min = [float(row["travel_time"]) / 60.0 for row in request_seen.values()]
    fares = [float(row["fare"]) for row in request_seen.values()]
    times = [row["time"] / 60.0 for row in timeline]

    fig = plt.figure(figsize=(11.0, 6.4), facecolor="white")
    gs = fig.add_gridspec(2, 3, width_ratios=[1.55, 1.0, 1.0], left=0.055, right=0.98, top=0.86, bottom=0.10, hspace=0.36, wspace=0.28)
    fig.text(0.055, 0.955, "MaaSSim demand and supply snapshot", fontsize=16, fontweight="semibold", color=INK, ha="left")
    fig.text(0.055, 0.918, "Nootdorp graph; first seed queue snapshots; origins, destinations, and idle vehicles", fontsize=9.8, color=MUTED, ha="left")
    ax_map = fig.add_subplot(gs[:, 0])
    draw_roads(ax_map, segments)
    if origin_nodes:
        pts = np.asarray([pos[node] for node in origin_nodes], dtype=float)
        ax_map.scatter(pts[:, 0], pts[:, 1], s=28, color=ORIGIN, edgecolor="white", linewidth=0.45, alpha=0.88, label="origins", zorder=3)
    if dest_nodes:
        pts = np.asarray([pos[node] for node in dest_nodes], dtype=float)
        ax_map.scatter(pts[:, 0], pts[:, 1], s=28, marker="^", color=DEST, edgecolor="white", linewidth=0.45, alpha=0.88, label="destinations", zorder=3)
    if vehicle_nodes:
        pts = np.asarray([pos[node] for node in vehicle_nodes], dtype=float)
        ax_map.scatter(pts[:, 0], pts[:, 1], s=18, marker="s", color=VEH, edgecolor="white", linewidth=0.35, alpha=0.74, label="vehicles", zorder=2)
    ax_map.set_xlim(*xlim)
    ax_map.set_ylim(*ylim)
    ax_map.set_aspect("equal", adjustable="box")
    ax_map.set_xticks([])
    ax_map.set_yticks([])
    for spine in ax_map.spines.values():
        spine.set_visible(False)
    ax_map.legend(frameon=False, loc="lower left", fontsize=8)
    ax_map.set_title("Spatial market state", loc="left", fontweight="semibold", color=INK)

    ax_travel = fig.add_subplot(gs[0, 1])
    ax_travel.hist(travel_min, bins=10, color=ORIGIN, edgecolor="white", alpha=0.88)
    ax_travel.set_title("Trip travel times", loc="left", fontweight="semibold", color=INK)
    ax_travel.set_xlabel("minutes")
    ax_travel.set_ylabel("requests")
    style_axis(ax_travel)

    ax_fare = fig.add_subplot(gs[0, 2])
    ax_fare.hist(fares, bins=10, color=DEST, edgecolor="white", alpha=0.88)
    ax_fare.set_title("Fare distribution", loc="left", fontweight="semibold", color=INK)
    ax_fare.set_xlabel("fare")
    style_axis(ax_fare)

    ax_queue = fig.add_subplot(gs[1, 1:])
    ax_queue.plot(times, [row["candidate_count"] for row in timeline], color=COLORS["llm"], linewidth=2.0, label="candidate offers")
    ax_queue.plot(times, [row["request_queue"] for row in timeline], color=ORIGIN, linewidth=1.8, label="queued requests")
    ax_queue.plot(times, [row["vehicle_queue"] for row in timeline], color=VEH, linewidth=1.8, label="queued vehicles")
    ax_queue.set_title("Queue and legal-action menu size", loc="left", fontweight="semibold", color=INK)
    ax_queue.set_xlabel("simulation minute")
    ax_queue.set_ylabel("count")
    ax_queue.legend(frameon=False, ncol=3, fontsize=8, loc="upper right")
    style_axis(ax_queue)
    save_figure(fig, "fig_maassim_experiment_demand_supply")
    plt.close(fig)


def configure_conflict_episode() -> None:
    trace.SEED = 1
    trace.WINDOW_START = 0
    trace.WINDOW_SIZE = 20
    replay.SCENARIO = "conflict_offer"
    replay.DRIVER_REJECT_PENALTY = trace.STRESS_DRIVER_REJECT_PENALTY
    replay.PASSENGER_REJECT_PENALTY = trace.STRESS_PASSENGER_REJECT_PENALTY


def event_increment(event: dict[str, Any]) -> tuple[float, int, int]:
    status = str(event.get("status"))
    if status == "served":
        return 3.0 - 0.01 * float(event.get("wait_time", 0.0)), 1, 0
    if status == "driver_reject":
        return -trace.STRESS_DRIVER_REJECT_PENALTY, 0, 1
    return -trace.STRESS_PASSENGER_REJECT_PENALTY, 0, 0


def series_for_trace(policy_trace: trace.PolicyTrace) -> dict[str, list[float]]:
    utility = []
    served = []
    rejects = []
    cum_utility = 0.0
    cum_served = 0
    cum_rejects = 0
    for step in range(trace.WINDOW_SIZE):
        for event in policy_trace.events:
            if int(event["step"]) != step:
                continue
            delta, served_inc, reject_inc = event_increment(event)
            cum_utility += delta
            cum_served += served_inc
            cum_rejects += reject_inc
        utility.append(cum_utility)
        served.append(float(cum_served))
        rejects.append(float(cum_rejects))
    return {"utility": utility, "served": served, "rejects": rejects}


def trace_bounds(traces: dict[str, trace.PolicyTrace], pos: dict[str, tuple[float, float]]) -> tuple[tuple[float, float], tuple[float, float]]:
    points = []
    for policy_trace in traces.values():
        for event in policy_trace.events:
            for key in ("driver_position", "origin", "destination"):
                node = str(event.get(key))
                if node in pos:
                    points.append(pos[node])
    return bounds(points, pad_frac=0.12)


def draw_trace_panel(ax: plt.Axes, segments: list[tuple[tuple[float, float], tuple[float, float]]], policy_trace: trace.PolicyTrace, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
    draw_roads(ax, segments, linewidth=0.45, alpha=0.60)
    for event in policy_trace.events:
        pickup = event.get("pickup_points", [])
        trip = event.get("trip_points", [])
        if event["status"] == "served":
            draw_line(ax, pickup, PICKUP, 0.8, 0.42, linestyle="--", zorder=2)
            draw_line(ax, trip, SERVICE, 1.25, 0.86, zorder=3)
        elif event["status"] == "driver_reject":
            draw_line(ax, pickup, REJECT, 1.05, 0.82, linestyle="--", zorder=3)
            if pickup:
                ax.scatter(pickup[-1][0], pickup[-1][1], marker="x", s=24, color=REJECT, linewidth=1.3, zorder=5)
    ax.set_title(
        f"{trace.LABELS[policy_trace.policy]}   utility {policy_trace.utility:.1f}   served {policy_trace.served}   rejects {policy_trace.driver_rejects}",
        loc="left",
        fontsize=9.4,
        fontweight="semibold",
        color=COLORS.get(policy_trace.policy, INK),
    )
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def plot_conflict_episode_dynamics(graph: nx.Graph, pos: dict[str, tuple[float, float]]) -> None:
    configure_conflict_episode()
    model = trace.resolved_player_model(None)
    cache = trace.load_cache()
    traces = {policy: trace.simulate_policy(policy, trace.SEED, model, cache) for policy in EPISODE_POLICIES}
    trace.enrich_routes(traces, graph, pos)
    xlim, ylim = trace_bounds(traces, pos)
    segments = road_segments(graph, pos, xlim, ylim, max_segments=3200)
    steps = np.arange(trace.WINDOW_SIZE)
    series = {policy: series_for_trace(policy_trace) for policy, policy_trace in traces.items()}

    fig = plt.figure(figsize=(12.2, 8.0), facecolor="white")
    gs = fig.add_gridspec(3, 3, width_ratios=[1.0, 1.0, 1.05], left=0.045, right=0.985, top=0.88, bottom=0.075, hspace=0.24, wspace=0.16)
    fig.text(0.045, 0.958, "Conflict-offer MaaSSim episode dynamics", fontsize=16, fontweight="semibold", color=INK, ha="left")
    fig.text(0.045, 0.922, "Full episode route traces and cumulative outcomes under the same passengers and legal menus", fontsize=9.8, color=MUTED, ha="left")
    map_slots = [gs[0, 0], gs[0, 1], gs[1, 0], gs[1, 1]]
    for slot, policy in zip(map_slots, EPISODE_POLICIES, strict=True):
        draw_trace_panel(fig.add_subplot(slot), segments, traces[policy], xlim, ylim)

    timeline_axes = [fig.add_subplot(gs[idx, 2]) for idx in range(3)]
    for policy in EPISODE_POLICIES:
        color = COLORS[policy]
        label = trace.LABELS[policy]
        timeline_axes[0].plot(steps, series[policy]["utility"], color=color, linewidth=2.0, label=label)
        timeline_axes[1].plot(steps, series[policy]["served"], color=color, linewidth=2.0)
        timeline_axes[2].plot(steps, series[policy]["rejects"], color=color, linewidth=2.0)
    titles = ["Cumulative utility", "Served passengers", "Driver rejects"]
    ylabels = ["utility", "served", "rejects"]
    for ax, title, ylabel in zip(timeline_axes, titles, ylabels, strict=True):
        ax.set_title(title, loc="left", fontweight="semibold", color=INK)
        ax.set_xlabel("decision step")
        ax.set_ylabel(ylabel)
        style_axis(ax)
    timeline_axes[0].legend(frameon=False, fontsize=8, loc="upper left")
    save_figure(fig, "fig_maassim_experiment_conflict_episode_dynamics")
    plt.close(fig)


def plot_persona_mechanism() -> None:
    rows = [row for row in read_csv_rows(ANALYSIS / "maassim_pact_persona_mechanism_summary.csv") if row["variant"] in {"pact_prior", "pact_shuffled", "pact", "oracle"}]
    x = np.arange(len(rows))
    labels = [POLICY_LABELS[row["variant"]] for row in rows]
    colors = [COLORS[row["variant"]] for row in rows]
    fig, axes = plt.subplots(1, 3, figsize=(11.2, 3.35), facecolor="white")
    fig.suptitle("MaaSSim persona mechanism ablation", x=0.02, y=1.04, ha="left", fontsize=15, fontweight="semibold", color=INK)
    panels = [
        ("realized_utility", "realized_utility_sem", "Realized utility", "utility"),
        ("driver_rejects", "driver_rejects_sem", "Driver rejects", "reject count"),
        ("policy_rule_acc", "policy_rule_acc_sem", "Policy belief accuracy", "rule marginal accuracy"),
    ]
    for ax, (value_key, sem_key, title, ylabel) in zip(axes, panels, strict=True):
        values = [f(row, value_key) for row in rows]
        sems = [f(row, sem_key, 0.0) for row in rows]
        ax.bar(x, values, color=colors, edgecolor="white", linewidth=0.7)
        ax.errorbar(x, values, yerr=sems, fmt="none", ecolor="#5f6873", elinewidth=0.8, capsize=2)
        ax.set_title(title, loc="left", fontweight="semibold", color=INK)
        ax.set_ylabel(ylabel)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=18, ha="right")
        style_axis(ax)
    fig.tight_layout()
    save_figure(fig, "fig_maassim_experiment_persona_mechanism")
    plt.close(fig)


def write_index() -> None:
    lines = [
        "# MaaSSim Experiment Figures",
        "",
        "Generated by `uv run python scripts/plot_maassim_experiment_figures.py`.",
        "",
        "The primary set mirrors the four overview figures in the MaaSSim GitHub README: Fig. 2 demand/supply service performance, Fig. 3 platform strategy search, Fig. 4 driver learning/adaptation, and Fig. 5 single-vehicle ride trace.",
        "",
        "## README Figure Analogues",
        "",
        "| README reference | Files | Local analogue |",
        "|---|---|---|",
        "| Fig. 2 service performance for demand/supply levels | `fig_maassim_readme_fig2_service_surface.{png,pdf}` | Common-state queue surface: queued requests x idle vehicles, with traveller pickup wait, legal offers per request, and driver idle pressure. |",
        "| Fig. 3 platform competition/strategy search | `fig_maassim_readme_fig3_platform_strategy.{png,pdf}` | PACT dispatch-objective sweep over wait weight and reject penalty, showing passenger wait, rides, rejects, and a utility proxy. |",
        "| Fig. 4 driver reinforced learning/adaptation | `fig_maassim_readme_fig4_driver_learning.{png,pdf}` | Hidden driver-persona belief adaptation over MaaSSim time, including exact posterior, marginal rule accuracy, and observed decline rate. |",
        "| Fig. 5 single-vehicle ride trace | `fig_maassim_readme_fig5_vehicle_trace.{png,pdf}` | MaaSSim route trace for one vehicle under Nearest and PACT replay; black means empty travel, green means carrying a passenger, red marks rejects. |",
        "",
        "## Additional PACT-Focused Figures",
        "",
        "| Figure | Files | Purpose |",
        "|---|---|---|",
        "| Scenario dashboard | `fig_maassim_experiment_scenario_dashboard.{png,pdf}` | Normal, reject-stress, and conflict-offer KPI comparison for LLM-PACT versus prompt baselines and Oracle. |",
        "| Demand/supply overview | `fig_maassim_experiment_demand_supply.{png,pdf}` | MaaSSim-style road-network market snapshot with origins, destinations, vehicles, trip-time/fare distributions, and legal-action menu size. |",
        "| Conflict episode dynamics | `fig_maassim_experiment_conflict_episode_dynamics.{png,pdf}` | Route traces plus cumulative utility/served/reject curves for LLM-PACT, LLM-PSRL, A-ToM-1, and ECON-BNE under the conflict-offer scenario. |",
        "| Persona mechanism | `fig_maassim_experiment_persona_mechanism.{png,pdf}` | Shows that learned driver-persona beliefs, not just the assignment solver, account for PACT's gain. |",
    ]
    (ANALYSIS / "maassim_experiment_figures_index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    configure()
    graph = nx.read_graphml(GRAPH)
    pos = node_pos(graph)
    plot_readme_fig2_service_surface()
    plot_readme_fig3_platform_strategy()
    plot_readme_fig4_driver_learning()
    plot_readme_fig5_vehicle_trace(graph, pos)
    plot_scenario_dashboard()
    plot_demand_supply_overview(graph, pos)
    plot_conflict_episode_dynamics(graph, pos)
    plot_persona_mechanism()
    write_index()
    print("OK: analysis/courier_dispatch_maassim/maassim_experiment_figures_index.md")


if __name__ == "__main__":
    main()