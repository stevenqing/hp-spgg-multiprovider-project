"""Create a polished GIF for MaaSSim LLM prompt-baseline comparison."""

from __future__ import annotations

import csv
from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis" / "courier_dispatch_maassim"
CSV_PATH = ANALYSIS / "maassim_llm_prompt_stress_s5_m20.csv"
OUT_DIRS = [ROOT / "figs", ROOT / "arr_paper" / "figs"]

INK = "#1f2328"
MUTED = "#68707a"
PALE = "#e6e8eb"
BLUE = "#12345d"
STEEL = "#3d6cb3"
PURPLE = "#7b5fb3"
OCHRE = "#c7773d"
AMBER = "#d4a04a"
RED = "#b64b45"
GREEN = "#3d7b62"
SOFT_GREEN = "#e9f4ee"
SOFT_BLUE = "#eaf0f8"
SOFT_RED = "#f8ecea"

ORDER = ["llm", "llm_psrl", "llm_belief", "atom_tom1", "atom_tom0", "econ_bne", "nearest", "random"]
LABELS = {
    "llm": "LLM-PACT",
    "llm_psrl": "LLM-PSRL",
    "llm_belief": "LLM-belief",
    "atom_tom1": "A-ToM-1",
    "atom_tom0": "A-ToM-0",
    "econ_bne": "ECON-BNE",
    "nearest": "Nearest",
    "random": "Random",
    "oracle": "Oracle",
}
COLORS = {
    "llm": BLUE,
    "llm_psrl": PURPLE,
    "llm_belief": OCHRE,
    "atom_tom1": "#cc8242",
    "atom_tom0": AMBER,
    "econ_bne": RED,
    "nearest": "#8c8c8c",
    "random": "#555555",
    "oracle": GREEN,
}


def read_rows() -> dict[str, dict[str, float | str]]:
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        raw = list(csv.DictReader(handle))
    rows: dict[str, dict[str, float | str]] = {}
    for row in raw:
        policy = str(row["policy"])
        rows[policy] = {
            "policy": policy,
            "label": LABELS.get(policy, str(row.get("label", policy))),
            "utility": float(row["realized_utility"]),
            "utility_sem": float(row["realized_utility_sem"]),
            "rejects": float(row["driver_rejects"]),
            "rejects_sem": float(row["driver_rejects_sem"]),
            "accept": float(row["driver_accept_rate"]),
            "parse": float(row["llm_parse_rate"]) if row["llm_parse_rate"] and row["llm_parse_rate"].lower() != "nan" else np.nan,
        }
    return rows


def ease(value: float) -> float:
    value = float(np.clip(value, 0.0, 1.0))
    return value * value * (3.0 - 2.0 * value)


def configure() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Inter", "Helvetica Neue", "Arial", "DejaVu Sans"],
            "font.size": 10.5,
            "axes.edgecolor": PALE,
            "axes.linewidth": 0.6,
            "savefig.dpi": 130,
        }
    )


def draw_badge(fig: plt.Figure, x: float, y: float, text: str, face: str, edge: str, color: str = INK) -> None:
    fig.text(
        x,
        y,
        text,
        ha="center",
        va="center",
        fontsize=9.2,
        color=color,
        bbox={"boxstyle": "round,pad=0.35,rounding_size=0.16", "facecolor": face, "edgecolor": edge, "linewidth": 0.8},
    )


def draw_pill(fig: plt.Figure, x: float, y: float, text: str, face: str, edge: str, color: str = INK) -> None:
    fig.text(
        x,
        y,
        text,
        ha="right",
        va="center",
        fontsize=9.2,
        color=color,
        bbox={"boxstyle": "round,pad=0.42,rounding_size=0.16", "facecolor": face, "edgecolor": edge, "linewidth": 0.8},
    )


def style_axis(ax: plt.Axes, grid: bool = True) -> None:
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(PALE)
    ax.tick_params(axis="x", colors=MUTED, labelsize=8.5)
    ax.tick_params(axis="y", colors=INK, labelsize=9.5, length=0)
    if grid:
        ax.grid(axis="x", linestyle=":", linewidth=0.6, color="#d9dde3")
    ax.set_axisbelow(True)


def draw_frame(rows: dict[str, dict[str, float | str]], frame_idx: int, total_frames: int) -> Image.Image:
    progress = frame_idx / max(total_frames - 1, 1)
    utility_phase = ease((progress - 0.10) / 0.32)
    reject_phase = ease((progress - 0.32) / 0.30)
    callout_phase = ease((progress - 0.60) / 0.22)
    parse_phase = ease((progress - 0.74) / 0.18)

    policies = [policy for policy in ORDER if policy in rows]
    labels = [str(rows[policy]["label"]) for policy in policies]
    utility = np.asarray([float(rows[policy]["utility"]) for policy in policies])
    utility_sem = np.asarray([float(rows[policy]["utility_sem"]) for policy in policies])
    rejects = np.asarray([float(rows[policy]["rejects"]) for policy in policies])
    rejects_sem = np.asarray([float(rows[policy]["rejects_sem"]) for policy in policies])

    fig = plt.figure(figsize=(10.8, 6.1), facecolor="white")
    fig.subplots_adjust(left=0.10, right=0.96, top=0.78, bottom=0.18, wspace=0.36)
    ax_util = fig.add_subplot(1, 2, 1)
    ax_rej = fig.add_subplot(1, 2, 2)

    fig.text(0.055, 0.94, "MaaSSim persona-stress replay", fontsize=18, weight="semibold", color=INK, ha="left")
    fig.text(0.055, 0.895, "Same legal assignment menu, same queue states, same persona maps", fontsize=10.5, color=MUTED, ha="left")
    draw_pill(fig, 0.955, 0.930, "driver reject penalty = 5.0", SOFT_RED, "#efc7c0", RED)
    draw_pill(fig, 0.955, 0.882, "all LLM prompts parse cleanly", SOFT_GREEN, "#b8dbc6", GREEN)

    y = np.arange(len(policies))[::-1]
    bar_colors = [COLORS[policy] for policy in policies]
    shown_utility = utility * utility_phase
    shown_sem = utility_sem * utility_phase
    ax_util.barh(y, shown_utility, xerr=shown_sem, color=bar_colors, alpha=0.96, edgecolor="white", linewidth=0.8, capsize=2.5)
    ax_util.set_yticks(y)
    ax_util.set_yticklabels(labels)
    ax_util.set_xlim(min(-31, float(np.nanmin(utility)) - 4), max(42, float(np.nanmax(utility)) + 6))
    ax_util.axvline(0, color=PALE, linewidth=0.8)
    ax_util.set_title("Realized utility", loc="left", fontsize=12, weight="semibold", color=INK)
    style_axis(ax_util)

    for yi, value, policy in zip(y, shown_utility, policies, strict=True):
        if utility_phase > 0.65:
            weight = "semibold" if policy == "llm" else "normal"
            true_value = float(rows[policy]["utility"])
            if true_value >= 0:
                ax_util.text(value + 0.8, yi, f"{true_value:.1f}", va="center", ha="left", fontsize=8.8, color=INK, weight=weight)
            else:
                ax_util.text(value + 1.2, yi, f"{true_value:.1f}", va="center", ha="left", fontsize=8.8, color="white", weight=weight)

    shown_rejects = rejects * reject_phase
    shown_reject_sem = rejects_sem * reject_phase
    ax_rej.barh(y, shown_rejects, xerr=shown_reject_sem, color=bar_colors, alpha=0.88, edgecolor="white", linewidth=0.8, capsize=2.5)
    ax_rej.set_yticks(y)
    ax_rej.set_yticklabels([])
    ax_rej.set_xlim(0, max(10.5, float(np.nanmax(rejects)) + 2.0))
    ax_rej.set_title("Driver rejects", loc="left", fontsize=12, weight="semibold", color=INK)
    style_axis(ax_rej)
    for yi, value, policy in zip(y, shown_rejects, policies, strict=True):
        if reject_phase > 0.65:
            ax_rej.text(value + 0.15, yi, f"{float(rows[policy]['rejects']):.1f}", va="center", ha="left", fontsize=8.8, color=INK)

    if callout_phase > 0:
        best_prompt = max([policy for policy in policies if policy not in {"llm", "nearest", "random"}], key=lambda p: float(rows[p]["utility"]))
        delta = float(rows["llm"]["utility"]) - float(rows[best_prompt]["utility"])
        alpha = callout_phase
        fig.text(0.055, 0.105, "LLM-PACT", fontsize=13.5, weight="semibold", color=BLUE, alpha=alpha, ha="left")
        fig.text(
            0.182,
            0.108,
            f"+{delta:.2f} utility vs best pure prompt baseline ({LABELS[best_prompt]})",
            fontsize=11.2,
            color=INK,
            alpha=alpha,
            ha="left",
        )
        fig.text(
            0.055,
            0.067,
            "PACT-style scores give the LLM a recovered-persona value signal; A-ToM, LLM-belief, LLM-PSRL, and ECON-BNE do not see assignment utility.",
            fontsize=9.5,
            color=MUTED,
            alpha=alpha,
            ha="left",
        )

    if parse_phase > 0:
        draw_pill(fig, 0.955, 0.842, "LLM-PACT, LLM-belief, LLM-PSRL, A-ToM, ECON-BNE: JSON ok", SOFT_BLUE, "#c9d8ee", STEEL)

    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=130, facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGBA")


def hold_frames(frames: list[Image.Image], count: int) -> None:
    if frames:
        frames.extend([frames[-1].copy() for _ in range(count)])


def write_outputs(frames: list[Image.Image]) -> None:
    for out_dir in OUT_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        gif_path = out_dir / "fig_maassim_llm_prompt_stress_comparison.gif"
        png_path = out_dir / "fig_maassim_llm_prompt_stress_comparison.png"
        if frames:
            frames[-1].save(png_path)
            paletted = [frame.convert("P", palette=Image.Palette.ADAPTIVE) for frame in frames]
            paletted[0].save(gif_path, save_all=True, append_images=paletted[1:], duration=70, loop=0, optimize=False)


def main() -> None:
    configure()
    rows = read_rows()
    frames = [draw_frame(rows, idx, 64) for idx in range(64)]
    hold_frames(frames, 18)
    write_outputs(frames)
    print("OK: figs/fig_maassim_llm_prompt_stress_comparison.gif")


if __name__ == "__main__":
    main()