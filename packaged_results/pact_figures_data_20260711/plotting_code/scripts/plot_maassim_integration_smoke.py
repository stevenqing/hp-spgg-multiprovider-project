"""Plot MaaSSim integration smoke diagnostics."""

from __future__ import annotations

import csv
import json
import ast
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis" / "courier_dispatch_maassim"
SNAPSHOTS = ANALYSIS / "pact_controlled_synthetic_queue_snapshots.jsonl"
POSTERIOR = ANALYSIS / "controlled_synthetic_rule_posterior.csv"
RIDES = ANALYSIS / "controlled_synthetic_rides.csv"
TRIPS = ANALYSIS / "controlled_synthetic_trips.csv"
GRAPH = ROOT / "external" / "maassim" / "MaaSSim" / "data" / "Nootdorp.graphml"
OUT_DIRS = [ROOT / "figs", ROOT / "arr_paper" / "figs"]

INK = "#202020"
MUTED = "#555555"
PALE = "#cccccc"
BLUE = "#1b3a6f"
STEEL = "#3d6cb3"
OCHRE = "#c7773d"
GREEN = "#3d7b62"
RED = "#b64b45"


def read_snapshots() -> list[dict[str, object]]:
    return [json.loads(line) for line in SNAPSHOTS.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_posterior() -> list[dict[str, str]]:
    with POSTERIOR.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def configure() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Inter", "Helvetica Neue", "Arial", "DejaVu Sans"],
            "font.size": 8.8,
            "axes.titlesize": 10.4,
            "axes.titleweight": "semibold",
            "axes.titlelocation": "left",
            "axes.edgecolor": PALE,
            "axes.linewidth": 0.5,
            "savefig.dpi": 240,
        }
    )


def style(ax: plt.Axes, grid_axis: str = "y") -> None:
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(PALE)
        ax.spines[spine].set_linewidth(0.45)
    ax.tick_params(colors=MUTED)
    ax.grid(axis=grid_axis, linestyle=":", linewidth=0.55, color="#dddddd")
    ax.set_axisbelow(True)


def save(fig: plt.Figure, stem: str) -> None:
    for out_dir in OUT_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_dir / f"{stem}.png", bbox_inches="tight", facecolor="white")
        fig.savefig(out_dir / f"{stem}.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def node_pos(graph: nx.Graph) -> dict[str, tuple[float, float]]:
    return {node: (float(data["x"]), float(data["y"])) for node, data in graph.nodes(data=True) if "x" in data and "y" in data}


def draw_graph_base(ax: plt.Axes, graph: nx.Graph, pos: dict[str, tuple[float, float]], linewidth: float = 0.32) -> None:
    for u, v in graph.edges():
        if u in pos and v in pos:
            ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]], color="#e4e4e4", linewidth=linewidth, zorder=0)


def parse_paxes(raw: object) -> list[int]:
    if raw is None or (isinstance(raw, float) and np.isnan(raw)):
        return []
    try:
        value = ast.literal_eval(str(raw))
    except Exception:
        return []
    if isinstance(value, (list, tuple)):
        return [int(item) for item in value]
    return []


def read_rides() -> pd.DataFrame:
    rides = pd.read_csv(RIDES)
    rides["veh"] = rides["veh"].astype(int)
    rides["node"] = rides["pos"].dropna().astype(float).astype(int).astype(str)
    rides["pax_count"] = rides["paxes"].apply(lambda value: len(parse_paxes(value)))
    return rides.sort_values(["veh", "t"])


def plot_overview(snapshots: list[dict[str, object]], posterior_rows: list[dict[str, str]]) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(10.2, 6.2))
    snap_idx = np.arange(len(snapshots))
    times = np.asarray([float(row.get("time", 0.0)) / 60.0 for row in snapshots], dtype=float)
    veh_q = np.asarray([len(row.get("vehicle_queue", [])) for row in snapshots], dtype=float)
    req_q = np.asarray([len(row.get("request_queue", [])) for row in snapshots], dtype=float)
    candidates = np.asarray([int(row.get("candidate_count", 0)) for row in snapshots], dtype=float)
    assigned = np.asarray([1 if row.get("shadow_assignment") else 0 for row in snapshots], dtype=float)
    evaluated = np.asarray([int(row.get("policy_diagnostics", {}).get("evaluated_assignments", 0)) for row in snapshots], dtype=float)

    ax = axes[0, 0]
    ax.plot(times, veh_q, color=BLUE, linewidth=1.6, label="idle drivers")
    ax.plot(times, req_q, color=OCHRE, linewidth=1.6, label="waiting requests")
    ax.plot(times, candidates, color=GREEN, linewidth=1.6, label="candidate pairs")
    ax.set_title("MaaSSim queue state")
    ax.set_xlabel("Simulation time (min)")
    ax.set_ylabel("Count")
    ax.legend(frameon=False, loc="best")
    style(ax)

    ax = axes[0, 1]
    ax.bar(times, evaluated, width=0.65, color="#d9e4f4", edgecolor="white", linewidth=0.4, label="evaluated")
    ax.scatter(times[assigned > 0], evaluated[assigned > 0], s=18, color=RED, label="assigned", zorder=3)
    ax.set_title("PACT controlled matching")
    ax.set_xlabel("Simulation time (min)")
    ax.set_ylabel("Assignments evaluated")
    ax.legend(frameon=False, loc="best")
    style(ax)

    ax = axes[1, 0]
    by_driver: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in posterior_rows:
        by_driver[row["driver_id"]].append(row)
    colors = [BLUE, STEEL, OCHRE, GREEN, RED]
    for color, driver_id in zip(colors, sorted(by_driver, key=lambda item: int(item)), strict=False):
        rows = by_driver[driver_id]
        xs = [float(row["time"]) / 60.0 for row in rows]
        ys = [float(row["ptrue"]) for row in rows]
        ax.plot(xs, ys, marker="o", markersize=3.2, linewidth=1.35, color=color, label=f"driver {driver_id}")
    ax.set_title("Posterior P(true) trajectory")
    ax.set_xlabel("Simulation time (min)")
    ax.set_ylabel("P(true tuple)")
    ax.set_ylim(-0.02, 1.04)
    ax.legend(frameon=False, ncol=2, loc="best")
    style(ax)

    ax = axes[1, 1]
    final_rows = {row["driver_id"]: row for row in posterior_rows}
    driver_ids = sorted(final_rows, key=lambda item: int(item))
    x = np.arange(len(driver_ids))
    width = 0.36
    ptrue = [float(final_rows[driver_id]["ptrue"]) for driver_id in driver_ids]
    rule_acc = [float(final_rows[driver_id]["rule_acc"]) for driver_id in driver_ids]
    ax.bar(x - width / 2, ptrue, width=width, color=BLUE, label="P(true)")
    ax.bar(x + width / 2, rule_acc, width=width, color=OCHRE, label="rule acc")
    ax.set_xticks(x)
    ax.set_xticklabels([f"D{driver_id}" for driver_id in driver_ids])
    ax.set_ylim(0, 1.05)
    ax.set_title("Final recovery by driver")
    ax.set_xlabel("Driver")
    ax.set_ylabel("Score")
    ax.legend(frameon=False, loc="best")
    style(ax)

    fig.suptitle("MaaSSim controlled PACT smoke", x=0.02, y=1.01, ha="left", fontsize=12.5, fontweight="semibold", color=INK)
    fig.tight_layout()
    save(fig, "fig_maassim_controlled_smoke_overview")


def plot_map(snapshots: list[dict[str, object]]) -> None:
    if not GRAPH.exists():
        return
    graph = nx.read_graphml(GRAPH)
    pos = node_pos(graph)
    if not pos:
        return
    driver_nodes: set[str] = set()
    origin_nodes: set[str] = set()
    dest_nodes: set[str] = set()
    for snapshot in snapshots:
        for candidate in snapshot.get("candidates", []):
            driver_nodes.add(str(candidate.get("driver_position")))
            origin_nodes.add(str(candidate.get("origin")))
            dest_nodes.add(str(candidate.get("destination")))
    driver_nodes &= set(pos)
    origin_nodes &= set(pos)
    dest_nodes &= set(pos)

    fig, ax = plt.subplots(figsize=(6.2, 6.2))
    draw_graph_base(ax, graph, pos, linewidth=0.35)
    if origin_nodes:
        xy = np.asarray([pos[node] for node in origin_nodes])
        ax.scatter(xy[:, 0], xy[:, 1], s=28, color=BLUE, label="origins", alpha=0.85, zorder=3)
    if dest_nodes:
        xy = np.asarray([pos[node] for node in dest_nodes])
        ax.scatter(xy[:, 0], xy[:, 1], s=28, color=OCHRE, label="destinations", alpha=0.85, zorder=3)
    if driver_nodes:
        xy = np.asarray([pos[node] for node in driver_nodes])
        ax.scatter(xy[:, 0], xy[:, 1], s=36, color=GREEN, marker="^", label="driver positions", alpha=0.9, zorder=4)
    ax.set_title("MaaSSim Nootdorp smoke events")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.legend(frameon=False, loc="best")
    ax.set_aspect("equal", adjustable="box")
    style(ax, grid_axis="both")
    fig.tight_layout()
    save(fig, "fig_maassim_controlled_smoke_map")


def plot_vehicle_trace() -> None:
    if not GRAPH.exists() or not RIDES.exists():
        return
    graph = nx.read_graphml(GRAPH)
    pos = node_pos(graph)
    rides = read_rides()
    eventful = rides.groupby("veh").size().sort_values(ascending=False)
    if eventful.empty:
        return
    vehicle_id = int(eventful.index[0])
    track = rides[rides["veh"] == vehicle_id].copy().sort_values("t")
    fig, ax = plt.subplots(figsize=(6.8, 6.8))
    draw_graph_base(ax, graph, pos, linewidth=0.32)
    colors = {0: "#777777", 1: BLUE, 2: GREEN}
    labels_seen: set[str] = set()
    previous_node = None
    for _, row in track.iterrows():
        node = str(row["node"])
        if node not in pos:
            continue
        if previous_node is not None and previous_node in pos and previous_node != node:
            try:
                route = nx.shortest_path(graph, previous_node, node, weight="length")
            except Exception:
                route = [previous_node, node]
            pax_count = int(min(2, row["pax_count"]))
            label = "empty/reposition" if pax_count == 0 else "with passenger"
            route_xy = [pos[str(route_node)] for route_node in route if str(route_node) in pos]
            if len(route_xy) >= 2:
                xs, ys = zip(*route_xy, strict=True)
                ax.plot(
                    xs,
                    ys,
                    color=colors[pax_count],
                    linewidth=1.2 + 1.1 * pax_count,
                    alpha=0.80,
                    label=label if label not in labels_seen else None,
                    zorder=2 + pax_count,
                )
                labels_seen.add(label)
        previous_node = node
    points = np.asarray([pos[str(node)] for node in track["node"] if str(node) in pos])
    if len(points):
        ax.scatter(points[:, 0], points[:, 1], s=18, color=OCHRE, edgecolor="white", linewidth=0.4, label="events", zorder=5)
        ax.scatter(points[0, 0], points[0, 1], s=58, color=GREEN, marker="^", edgecolor="white", linewidth=0.6, label="start", zorder=6)
        ax.scatter(points[-1, 0], points[-1, 1], s=58, color=RED, marker="s", edgecolor="white", linewidth=0.6, label="end", zorder=6)
    ax.set_title(f"MaaSSim Fig5-style trace: vehicle {vehicle_id}")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect("equal", adjustable="box")
    ax.legend(frameon=False, loc="best")
    style(ax, grid_axis="both")
    fig.tight_layout()
    save(fig, "fig_maassim_controlled_vehicle_trace")


def make_animation() -> None:
    if not GRAPH.exists() or not RIDES.exists():
        return
    graph = nx.read_graphml(GRAPH)
    pos = node_pos(graph)
    rides = read_rides()
    if rides.empty:
        return
    frames_dir = ANALYSIS / "animation_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    for frame_path in frames_dir.glob("frame_*.png"):
        frame_path.unlink()
    times = np.linspace(float(rides["t"].min()), float(rides["t"].max()), num=36)
    vehicles = sorted(rides["veh"].unique())
    frame_paths: list[Path] = []
    for frame_idx, current_time in enumerate(times):
        fig, ax = plt.subplots(figsize=(5.8, 5.8))
        draw_graph_base(ax, graph, pos, linewidth=0.28)
        active_points = []
        active_colors = []
        active_labels = []
        for vehicle_id in vehicles:
            hist = rides[(rides["veh"] == vehicle_id) & (rides["t"] <= current_time)]
            if hist.empty:
                continue
            row = hist.iloc[-1]
            node = str(row["node"])
            if node not in pos:
                continue
            active_points.append(pos[node])
            active_colors.append(BLUE if int(row["pax_count"]) > 0 else GREEN)
            active_labels.append(str(vehicle_id))
        if active_points:
            xy = np.asarray(active_points)
            ax.scatter(xy[:, 0], xy[:, 1], s=50, color=active_colors, marker="^", edgecolor="white", linewidth=0.5, zorder=5)
            for (x, y), label in zip(active_points, active_labels, strict=True):
                ax.text(x, y, label, fontsize=7, color=INK, ha="center", va="bottom", zorder=6)
        ax.set_title(f"MaaSSim controlled smoke t={current_time / 60:.1f} min")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_aspect("equal", adjustable="box")
        style(ax, grid_axis="both")
        fig.tight_layout()
        frame_path = frames_dir / f"frame_{frame_idx:03d}.png"
        fig.savefig(frame_path, bbox_inches="tight", facecolor="white", dpi=130)
        plt.close(fig)
        frame_paths.append(frame_path)
    images = [Image.open(path).convert("P", palette=Image.Palette.ADAPTIVE) for path in frame_paths]
    gif_path = ROOT / "figs" / "fig_maassim_controlled_smoke_animation.gif"
    gif_path.parent.mkdir(parents=True, exist_ok=True)
    if images:
        images[0].save(gif_path, save_all=True, append_images=images[1:], duration=180, loop=0)
        arr_gif = ROOT / "arr_paper" / "figs" / gif_path.name
        arr_gif.parent.mkdir(parents=True, exist_ok=True)
        images[0].save(arr_gif, save_all=True, append_images=images[1:], duration=180, loop=0)


def main() -> None:
    configure()
    snapshots = read_snapshots()
    posterior_rows = read_posterior()
    plot_overview(snapshots, posterior_rows)
    plot_map(snapshots)
    plot_vehicle_trace()
    make_animation()
    print("OK: figs/fig_maassim_controlled_smoke_overview.png")
    if GRAPH.exists():
        print("OK: figs/fig_maassim_controlled_smoke_map.png")
        print("OK: figs/fig_maassim_controlled_vehicle_trace.png")
        print("OK: figs/fig_maassim_controlled_smoke_animation.gif")


if __name__ == "__main__":
    main()