"""People-and-cars MaaSSim-style GIF comparing LLM-PACT to prompt baselines."""

from __future__ import annotations

import math
import sys
from io import BytesIO
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib import patches, transforms
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
for path in (ROOT, SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import animate_maassim_fig5_policy_comparison as trace
import replay_maassim_llm_smoke as replay


OUT_DIRS = [ROOT / "figs", ROOT / "arr_paper" / "figs"]
SCENARIO = "conflict_offer"
SEED = 1
WINDOW_START = 0
WINDOW_SIZE = 20
OUT_STEM = "fig_maassim_conflict_people_cars_llm_pact_vs_prompts"
POLICIES = ["llm", "llm_psrl", "atom_tom1", "econ_bne"]
COLORS = {"llm": "#12345d", "llm_psrl": "#7b5fb3", "atom_tom1": "#cc8242", "econ_bne": "#b64b45"}

INK = "#1f2328"
MUTED = "#68707a"
ROAD = "#dfe5ed"
SERVICE = "#2f7d5b"
PICKUP = "#2f5f9b"
REJECT = "#c23b32"
PERSON = "#1b5c9d"
DEST = "#2f7d5b"
PASSENGER_QUIET = "#a7b0ba"
ROAD_VISIBLE = "#d9e0e8"


def configure() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Inter", "Helvetica Neue", "Arial", "DejaVu Sans"],
            "font.size": 10,
            "savefig.dpi": 130,
        }
    )


def lerp(a: tuple[float, float], b: tuple[float, float], t: float) -> tuple[float, float]:
    t = float(np.clip(t, 0.0, 1.0))
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def path_point(points: list[tuple[float, float]], t: float) -> tuple[float, float] | None:
    if not points:
        return None
    if len(points) == 1:
        return points[0]
    return lerp(points[0], points[-1], t)


def angle_between(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.atan2(b[1] - a[1], b[0] - a[0])


def draw_car(ax: plt.Axes, xy: tuple[float, float], angle: float, color: str, scale: float, alpha: float = 1.0) -> None:
    x, y = xy
    width = scale * 1.85
    height = scale * 0.95
    trans = transforms.Affine2D().rotate_around(x, y, angle) + ax.transData
    body = patches.FancyBboxPatch(
        (x - width / 2, y - height / 2),
        width,
        height,
        boxstyle=f"round,pad=0,rounding_size={height * 0.22}",
        facecolor=color,
        edgecolor="white",
        linewidth=0.75,
        alpha=alpha,
        zorder=8,
        transform=trans,
    )
    ax.add_patch(body)
    windshield = patches.FancyBboxPatch(
        (x + width * 0.04, y - height * 0.24),
        width * 0.34,
        height * 0.48,
        boxstyle=f"round,pad=0,rounding_size={height * 0.10}",
        facecolor="white",
        edgecolor="none",
        alpha=0.72 * alpha,
        zorder=9,
        transform=trans,
    )
    ax.add_patch(windshield)
    wheel_offset_x = width * 0.28
    wheel_offset_y = height * 0.48
    for sx in (-wheel_offset_x, wheel_offset_x):
        for sy in (-wheel_offset_y, wheel_offset_y):
            wx = x + math.cos(angle) * sx - math.sin(angle) * sy
            wy = y + math.sin(angle) * sx + math.cos(angle) * sy
            ax.add_patch(patches.Circle((wx, wy), radius=scale * 0.13, facecolor="#202020", edgecolor="none", alpha=0.9 * alpha, zorder=7))


def draw_person(ax: plt.Axes, xy: tuple[float, float], scale: float, color: str = PERSON, alpha: float = 1.0, zorder: int = 7) -> None:
    x, y = xy
    ax.add_patch(patches.Circle((x, y), radius=scale * 0.72, facecolor="white", edgecolor=color, linewidth=0.7, alpha=0.78 * alpha, zorder=zorder - 1))
    ax.add_patch(patches.Circle((x, y + scale * 0.36), radius=scale * 0.20, facecolor=color, edgecolor="white", linewidth=0.65, alpha=alpha, zorder=zorder))
    ax.plot([x, x], [y + scale * 0.17, y - scale * 0.30], color=color, linewidth=1.65, alpha=alpha, zorder=zorder)
    ax.plot([x - scale * 0.26, x + scale * 0.26], [y, y], color=color, linewidth=1.45, alpha=alpha, zorder=zorder)
    ax.plot([x, x - scale * 0.24], [y - scale * 0.30, y - scale * 0.60], color=color, linewidth=1.35, alpha=alpha, zorder=zorder)
    ax.plot([x, x + scale * 0.24], [y - scale * 0.30, y - scale * 0.60], color=color, linewidth=1.35, alpha=alpha, zorder=zorder)


def draw_flag(ax: plt.Axes, xy: tuple[float, float], scale: float, color: str = DEST, alpha: float = 1.0) -> None:
    x, y = xy
    ax.plot([x, x], [y - scale * 0.4, y + scale * 0.55], color=color, linewidth=1.3, alpha=alpha, zorder=6)
    tri = patches.Polygon([(x, y + scale * 0.55), (x + scale * 0.62, y + scale * 0.38), (x, y + scale * 0.20)], closed=True, facecolor=color, edgecolor="white", linewidth=0.4, alpha=alpha, zorder=6)
    ax.add_patch(tri)


def draw_x(ax: plt.Axes, xy: tuple[float, float], scale: float, color: str = REJECT, alpha: float = 1.0) -> None:
    x, y = xy
    ax.plot([x - scale * 0.42, x + scale * 0.42], [y - scale * 0.42, y + scale * 0.42], color=color, linewidth=2.0, alpha=alpha, zorder=10)
    ax.plot([x - scale * 0.42, x + scale * 0.42], [y + scale * 0.42, y - scale * 0.42], color=color, linewidth=2.0, alpha=alpha, zorder=10)


def draw_path(ax: plt.Axes, points: list[tuple[float, float]], color: str, scale: float, alpha: float, linestyle: str = "-", zorder: int = 3) -> None:
    if len(points) < 2:
        return
    xs, ys = zip(*points, strict=True)
    ax.plot(xs, ys, color=color, linewidth=max(1.3, scale * 1400), alpha=alpha, linestyle=linestyle, solid_capstyle="round", zorder=zorder)


def used_bounds(traces: dict[str, trace.PolicyTrace], pos: dict[str, tuple[float, float]]) -> tuple[tuple[float, float], tuple[float, float], float]:
    points = []
    for tr in traces.values():
        for event in tr.events:
            for key in ("driver_position", "origin", "destination"):
                node = str(event.get(key))
                if node in pos:
                    points.append(pos[node])
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    pad_x = (max(xs) - min(xs)) * 0.10
    pad_y = (max(ys) - min(ys)) * 0.14
    span = max(max(xs) - min(xs), max(ys) - min(ys))
    return (min(xs) - pad_x, max(xs) + pad_x), (min(ys) - pad_y, max(ys) + pad_y), span


def segment_in_bounds(a: tuple[float, float], b: tuple[float, float], xlim: tuple[float, float], ylim: tuple[float, float]) -> bool:
    min_x, max_x = min(a[0], b[0]), max(a[0], b[0])
    min_y, max_y = min(a[1], b[1]), max(a[1], b[1])
    return not (max_x < xlim[0] or min_x > xlim[1] or max_y < ylim[0] or min_y > ylim[1])


def used_nodes(traces: dict[str, trace.PolicyTrace], pos: dict[str, tuple[float, float]]) -> set[str]:
    nodes: set[str] = set()
    for tr in traces.values():
        for event in tr.events:
            for key in ("driver_position", "origin", "destination"):
                node = str(event.get(key))
                if node in pos:
                    nodes.add(node)
    return nodes


def visible_road_segments(graph: nx.Graph, pos: dict[str, tuple[float, float]], xlim: tuple[float, float], ylim: tuple[float, float], nodes_of_interest: set[str]) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    interest_points = np.asarray([pos[node] for node in nodes_of_interest], dtype=float) if nodes_of_interest else np.empty((0, 2))
    span = max(xlim[1] - xlim[0], ylim[1] - ylim[0])
    max_dist = span * 0.18
    segments = []
    for u, v in graph.edges():
        u_key = str(u)
        v_key = str(v)
        if u_key not in pos or v_key not in pos:
            continue
        a = pos[u_key]
        b = pos[v_key]
        if segment_in_bounds(a, b, xlim, ylim):
            if len(interest_points):
                mid = np.asarray([(a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0])
                if float(np.min(np.linalg.norm(interest_points - mid, axis=1))) > max_dist:
                    continue
            segments.append((a, b))
    return segments


def draw_road_network(ax: plt.Axes, road_segments: list[tuple[tuple[float, float], tuple[float, float]]]) -> None:
    if not road_segments:
        return
    collection = LineCollection(road_segments, colors=ROAD_VISIBLE, linewidths=0.62, alpha=0.78, zorder=0, capstyle="round")
    ax.add_collection(collection)


def draw_context(ax: plt.Axes, road_segments: list[tuple[tuple[float, float], tuple[float, float]]], tr: trace.PolicyTrace, pos: dict[str, tuple[float, float]], scale: float) -> None:
    draw_road_network(ax, road_segments)
    nodes = used_nodes({tr.policy: tr}, pos)
    pts = np.asarray([pos[node] for node in nodes], dtype=float)
    if len(pts):
        ax.scatter(pts[:, 0], pts[:, 1], s=18, color="#cfd7e2", edgecolor="white", linewidth=0.3, alpha=0.7, zorder=1)
    for event in tr.events:
        origin = str(event.get("origin"))
        destination = str(event.get("destination"))
        if origin in pos:
            draw_person(ax, pos[origin], scale * 0.92, alpha=0.58, zorder=2)
        if destination in pos:
            draw_flag(ax, pos[destination], scale * 0.78, alpha=0.30)


def draw_panel(ax: plt.Axes, road_segments: list[tuple[tuple[float, float], tuple[float, float]]], tr: trace.PolicyTrace, pos: dict[str, tuple[float, float]], step_float: float, xlim: tuple[float, float], ylim: tuple[float, float], scale: float) -> None:
    current_step = int(np.floor(step_float))
    sub = float(step_float - current_step)
    draw_context(ax, road_segments, tr, pos, scale)
    visible = [event for event in tr.events if int(event["step"]) <= current_step]
    for event in visible:
        age = current_step - int(event["step"])
        alpha = max(0.18, 0.95 - 0.065 * age)
        pickup_points = event.get("pickup_points", [])
        trip_points = event.get("trip_points", [])
        if event["status"] == "served":
            draw_path(ax, pickup_points, PICKUP, scale, alpha * 0.42, linestyle="--", zorder=2)
            draw_path(ax, trip_points, SERVICE, scale, alpha, zorder=3)
        elif event["status"] == "driver_reject":
            draw_path(ax, pickup_points, REJECT, scale, alpha, linestyle="--", zorder=4)
            if pickup_points:
                draw_x(ax, pickup_points[-1], scale * 1.05, alpha=alpha)
        else:
            node = str(event.get("origin"))
            if node in pos:
                ax.scatter(pos[node][0], pos[node][1], s=24, color=PASSENGER_QUIET, alpha=0.25, linewidth=0, zorder=2)
    active = [event for event in tr.events if int(event["step"]) == current_step]
    for event in active:
        pickup_points = event.get("pickup_points", [])
        trip_points = event.get("trip_points", [])
        if event["status"] == "served" and pickup_points and trip_points:
            if sub < 0.44:
                car_xy = path_point(pickup_points, sub / 0.44)
                car_angle = angle_between(pickup_points[0], pickup_points[-1])
                person_node = str(event.get("origin"))
                if person_node in pos:
                    draw_person(ax, pos[person_node], scale * 1.38, alpha=1.0)
            else:
                car_xy = path_point(trip_points, (sub - 0.44) / 0.56)
                car_angle = angle_between(trip_points[0], trip_points[-1])
            if car_xy is not None:
                draw_car(ax, car_xy, car_angle, COLORS[tr.policy], scale * 1.25, alpha=1.0)
        elif event["status"] == "driver_reject" and pickup_points:
            car_xy = path_point(pickup_points, min(sub / 0.75, 1.0))
            car_angle = angle_between(pickup_points[0], pickup_points[-1])
            if car_xy is not None:
                draw_car(ax, car_xy, car_angle, COLORS[tr.policy], scale * 1.20, alpha=0.92)
            if sub > 0.72:
                draw_x(ax, pickup_points[-1], scale * 1.25, alpha=1.0)
    served = sum(1 for event in visible if event["status"] == "served")
    driver_rejects = sum(1 for event in visible if event["status"] == "driver_reject")
    utility = 0.0
    for event in visible:
        if event["status"] == "driver_reject":
            utility -= trace.STRESS_DRIVER_REJECT_PENALTY
        elif event["status"] == "passenger_reject":
            utility -= trace.STRESS_PASSENGER_REJECT_PENALTY
        else:
            utility += 3.0 - 0.01 * float(event["wait_time"])
    ax.set_title(trace.LABELS[tr.policy], loc="left", fontsize=14, fontweight="semibold", color=COLORS[tr.policy])
    ax.text(0.02, 0.94, f"utility {utility:4.1f}   served {served}   driver rejects {driver_rejects}", transform=ax.transAxes, ha="left", va="top", fontsize=9.4, color=INK, bbox={"boxstyle": "round,pad=0.32", "facecolor": "white", "edgecolor": "#d8dde6", "linewidth": 0.65, "alpha": 0.94})
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def make_frame(road_segments: list[tuple[tuple[float, float], tuple[float, float]]], traces: dict[str, trace.PolicyTrace], pos: dict[str, tuple[float, float]], xlim: tuple[float, float], ylim: tuple[float, float], scale: float, frame_idx: int, frame_count: int) -> Image.Image:
    progress = frame_idx / max(frame_count - 1, 1)
    step_float = progress * (trace.WINDOW_SIZE - 1)
    fig, axes = plt.subplots(2, 2, figsize=(11.2, 7.15), facecolor="white")
    fig.patch.set_facecolor("white")
    fig.subplots_adjust(left=0.035, right=0.975, top=0.82, bottom=0.095, wspace=0.05, hspace=0.16)
    fig.text(0.04, 0.94, "MaaSSim conflict-offer replay", fontsize=18, fontweight="semibold", color=INK, ha="left")
    fig.text(0.04, 0.892, f"Full episode seed={trace.SEED}; road network, people, cars, same requests", fontsize=10.2, color=MUTED, ha="left")
    fig.text(0.975, 0.936, "car = active driver", ha="right", va="center", fontsize=9.2, color=INK, bbox={"boxstyle": "round,pad=0.34", "facecolor": "#eef3fb", "edgecolor": "#c9d8ee", "linewidth": 0.7})
    fig.text(0.975, 0.888, "person = waiting passenger", ha="right", va="center", fontsize=9.2, color=PERSON, bbox={"boxstyle": "round,pad=0.34", "facecolor": "#edf6ff", "edgecolor": "#c9d8ee", "linewidth": 0.7})
    fig.text(0.975, 0.840, "red X = driver reject", ha="right", va="center", fontsize=9.2, color=REJECT, bbox={"boxstyle": "round,pad=0.34", "facecolor": "#f8ecea", "edgecolor": "#efc7c0", "linewidth": 0.7})
    for ax, policy in zip(axes.flatten(), POLICIES, strict=True):
        draw_panel(ax, road_segments, traces[policy], pos, step_float, xlim, ylim, scale)
    if frame_idx >= frame_count - 1:
        prompt_policies = ["llm_psrl", "atom_tom1", "econ_bne"]
        best_prompt = max(prompt_policies, key=lambda policy: traces[policy].utility)
        delta = traces["llm"].utility - traces[best_prompt].utility
        fig.text(
            0.04,
            0.045,
            f"Full episode result: LLM-PACT has {traces['llm'].driver_rejects} driver rejects; best pure prompt baseline ({trace.LABELS[best_prompt]}) has {traces[best_prompt].driver_rejects}. Utility gap: +{delta:.2f}.",
            fontsize=10.8,
            color=INK,
            ha="left",
        )
    else:
        fig.text(0.04, 0.045, "The same passengers and requests unfold under two LLM policies.", fontsize=10.0, color=MUTED, ha="left")
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
        gif_path = out_dir / f"{OUT_STEM}.gif"
        png_path = out_dir / f"{OUT_STEM}.png"
        frames[-1].save(png_path)
        paletted = [frame.convert("P", palette=Image.Palette.ADAPTIVE) for frame in frames]
        paletted[0].save(gif_path, save_all=True, append_images=paletted[1:], duration=120, loop=0, optimize=False)


def main() -> None:
    configure()
    trace.SEED = SEED
    trace.WINDOW_START = WINDOW_START
    trace.WINDOW_SIZE = WINDOW_SIZE
    graph = nx.read_graphml(trace.GRAPH)
    pos = trace.node_pos(graph)
    replay = __import__("replay_maassim_llm_smoke")
    replay.SCENARIO = SCENARIO
    replay.DRIVER_REJECT_PENALTY = trace.STRESS_DRIVER_REJECT_PENALTY
    replay.PASSENGER_REJECT_PENALTY = trace.STRESS_PASSENGER_REJECT_PENALTY
    model = trace.resolved_player_model(None)
    cache = trace.load_cache()
    traces = {}
    for policy in POLICIES:
        print(f"simulate {policy}", flush=True)
        traces[policy] = trace.simulate_policy(policy, trace.SEED, model, cache)
    trace.enrich_routes(traces, graph, pos)
    xlim, ylim, span = used_bounds(traces, pos)
    scale = span * 0.018
    road_segments = visible_road_segments(graph, pos, xlim, ylim, used_nodes(traces, pos))
    frame_count = 20
    frames = []
    for idx in range(frame_count):
        if idx % 5 == 0:
            print(f"frame {idx}/{frame_count}", flush=True)
        frames.append(make_frame(road_segments, traces, pos, xlim, ylim, scale, idx, frame_count))
    frames.extend([frames[-1].copy() for _ in range(12)])
    write_outputs(frames)
    print(f"OK: figs/{OUT_STEM}.gif")


if __name__ == "__main__":
    main()