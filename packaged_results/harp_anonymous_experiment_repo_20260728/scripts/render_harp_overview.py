"""Draw the HARP system overview from first principles with Matplotlib."""

from __future__ import annotations

from pathlib import Path
import textwrap

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "arr_paper" / "figs"
BLUE = "#0d47a1"
PALE = "#f4f8ff"
GREEN = "#2e7d32"
PURPLE = "#6a3fb5"
ORANGE = "#e58a1f"
INK = "#20242a"


def box(axis, x, y, width, height, *, edge=BLUE, face="white", radius=0.012, linewidth=1.2):
    patch = FancyBboxPatch((x, y), width, height, boxstyle=f"round,pad=0.008,rounding_size={radius}",
                           facecolor=face, edgecolor=edge, linewidth=linewidth)
    axis.add_patch(patch)
    return patch


def arrow(axis, start, end, color=BLUE):
    axis.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=13, linewidth=1.25, color=color))


def robot(axis, x, y, color):
    box(axis, x - 0.018, y - 0.014, 0.036, 0.028, edge=color, face="#f8fbff", radius=0.006, linewidth=1.5)
    axis.add_patch(Circle((x - 0.007, y), 0.003, color=color))
    axis.add_patch(Circle((x + 0.007, y), 0.003, color=color))
    axis.plot([x - 0.010, x + 0.010], [y - 0.007, y - 0.007], color=color, linewidth=1.0)
    axis.plot([x, x], [y + 0.014, y + 0.022], color=color, linewidth=1.2)
    axis.add_patch(Circle((x, y + 0.024), 0.0025, color=color))


def coordinator(axis):
    box(axis, 0.025, 0.53, 0.22, 0.42, edge="#497dcc", face=PALE)
    axis.text(0.135, 0.92, "Coordinator", ha="center", fontsize=15, fontweight="bold", color=BLUE)
    axis.add_patch(Circle((0.135, 0.82), 0.040, facecolor="#f2c7a0", edgecolor=INK, linewidth=1.2))
    axis.add_patch(Rectangle((0.085, 0.68), 0.10, 0.10, facecolor="#3977b8", edgecolor=INK, linewidth=1.0))
    axis.add_patch(Rectangle((0.125, 0.68), 0.09, 0.055, facecolor="#68737d", edgecolor=INK, linewidth=1.0))
    axis.text(0.135, 0.625, "Observes public state and actions", ha="center", fontsize=9)
    axis.text(0.135, 0.585, "Does not observe hidden personas", ha="center", fontsize=9)
    axis.text(0.135, 0.545, "Learns beliefs and plans jointly", ha="center", fontsize=9, fontweight="bold")


def environment(axis):
    box(axis, 0.285, 0.53, 0.69, 0.42, edge="#466a99", face="#fbfdff")
    axis.text(0.63, 0.925, "Public environment and hidden personas", ha="center", fontsize=15, fontweight="bold")
    agents = [(0.40, BLUE, "Agent 1", "Altruistic builder"), (0.63, GREEN, "Agent 2", "Free rider"), (0.86, PURPLE, "Agent $n$", "Strategic hedger")]
    for x, color, name, persona in agents:
        robot(axis, x, 0.84, color)
        axis.text(x, 0.88, name, ha="center", fontsize=10, fontweight="bold", color=color)
        box(axis, x - 0.085, 0.66, 0.17, 0.13, edge=color, face="white", radius=0.008)
        axis.text(x, 0.755, "Private persona", ha="center", fontsize=8, color=color, fontweight="bold")
        axis.text(x, 0.715, persona, ha="center", fontsize=9, fontweight="bold")
        axis.text(x, 0.675, "emits action $a_t^i$", ha="center", fontsize=8)
        arrow(axis, (x, 0.655), (x, 0.625), color)
    axis.text(0.515, 0.84, "$\\cdots$", fontsize=20)
    axis.text(0.745, 0.84, "$\\cdots$", fontsize=20)
    box(axis, 0.34, 0.565, 0.58, 0.035, edge="#466a99", face="#f8f8f8", radius=0.004)
    axis.text(0.63, 0.582, "Joint transition and team reward are observed by the coordinator", ha="center", va="center", fontsize=9)
    arrow(axis, (0.245, 0.77), (0.285, 0.77))
    arrow(axis, (0.285, 0.70), (0.245, 0.70))
    axis.text(0.265, 0.79, "state", ha="center", fontsize=7)
    axis.text(0.265, 0.66, "actions / reward", ha="center", fontsize=7)


def pipeline(axis):
    axis.text(0.50, 0.485, "HARP Pipeline: inference outside the prompt, planning inside the loop", ha="center",
              fontsize=15, fontweight="bold", color=BLUE)
    steps = [
        ("1", "Persona priors", "Maintain one numeric posterior per agent."),
        ("2", "Sample profile", "Sample each persona independently from its posterior."),
        ("3", "Plan and execute", "Optimize a joint action under the sampled profile."),
        ("4", "Score outcomes", "Evaluate each observation under every persona."),
        ("5", "Bayesian update", "Update each posterior in closed form; repeat."),
    ]
    start = 0.035
    gap = 0.012
    width = (0.93 - 4 * gap) / 5
    for index, (number, title, body) in enumerate(steps):
        x = start + index * (width + gap)
        box(axis, x, 0.07, width, 0.36, edge="#8bb7ef", face="#fbfdff", radius=0.008)
        axis.add_patch(Circle((x + 0.025, 0.395), 0.014, facecolor=BLUE, edgecolor="none"))
        axis.text(x + 0.025, 0.395, number, color="white", ha="center", va="center", fontsize=9, fontweight="bold")
        axis.text(x + 0.048, 0.395, title, ha="left", va="center", fontsize=10, fontweight="bold", color=BLUE)
        axis.text(x + width / 2, 0.33, textwrap.fill(body, width=24), ha="center", va="top", fontsize=6.8, linespacing=1.25)
        if index == 0:
            for row in range(4):
                axis.text(x + 0.035, 0.245 - row * 0.04, f"$\\theta_{row + 1}$", fontsize=8)
                axis.add_patch(Rectangle((x + 0.075, 0.245 - row * 0.04), width * (0.45 - row * 0.05), 0.012, facecolor="#4d86cc", alpha=0.85))
        elif index == 1:
            for offset, color in ((0.04, BLUE), (0.09, GREEN), (0.14, PURPLE)):
                axis.add_patch(Circle((x + offset, 0.20), 0.016, facecolor="white", edgecolor=color, linewidth=1.4))
                robot(axis, x + offset, 0.13, color)
        elif index == 2:
            box(axis, x + 0.035, 0.18, width - 0.07, 0.075, edge=ORANGE, face="#fff8e8", radius=0.006)
            axis.text(x + width / 2, 0.218, "central planner $\\mathcal{P}$", ha="center", va="center", fontsize=9, fontweight="bold")
        elif index == 3:
            axis.text(x + width / 2, 0.23, "$q_\\phi(o_i \\mid x_i, \\theta_i)$", ha="center", fontsize=12)
            axis.text(x + width / 2, 0.16, "persona-conditioned likelihood", ha="center", fontsize=8)
        else:
            axis.text(x + width / 2, 0.245, "$\\mu_{k+1}^{i}(\\theta) \\propto \\mu_k^{i}(\\theta) q_\\theta(o)$", ha="center", fontsize=10)
            axis.text(x + width / 2, 0.16, "$O(n|\\Theta_i|)$ storage", ha="center", fontsize=9, color=BLUE, fontweight="bold")
        if index < len(steps) - 1:
            arrow(axis, (x + width + 0.002, 0.25), (x + width + gap - 0.002, 0.25))


def main() -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "pdf.fonttype": 42, "ps.fonttype": 42})
    fig, axis = plt.subplots(figsize=(15.0, 8.2))
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.axis("off")
    coordinator(axis)
    environment(axis)
    pipeline(axis)
    fig.tight_layout(pad=0.15)
    fig.savefig(OUT / "main.pdf", bbox_inches="tight", facecolor="white")
    fig.savefig(OUT / "main.png", dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("redrew HARP overview")


if __name__ == "__main__":
    main()
