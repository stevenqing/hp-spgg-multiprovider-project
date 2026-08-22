"""
Fig 5 — E1 posterior concentration rate per LLM backbone.
Single-panel design: K_conc^0.9 bar chart with regime classification + bonus benefit
overlay. Matches v3 design system.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parents[1] / "arr_paper" / "figs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Design system (matches v3)
plt.rcParams.update({
    "font.family": "Inter",
    "font.sans-serif": ["Inter", "Helvetica Neue", "Arial", "DejaVu Sans"],
    "font.weight": "regular",
    "font.size": 9,
    "axes.titlesize": 11,
    "axes.titleweight": "semibold",
    "axes.labelsize": 9,
    "axes.linewidth": 0.4,
    "axes.edgecolor": "#cccccc",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "xtick.color": "#444444",
    "ytick.color": "#444444",
    "xtick.major.size": 0,
    "ytick.major.size": 0,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
})

INK = "#202020"
MUTED = "#555555"
LIGHTER = "#888888"

# E1 disk data
backbones = ["DeepSeek-V3.2", "GPT-5.4-nano", "Kimi-K2.6", "Llama-4-Maverick"]
k_conc = [4.4, 6.6, 12.0, 14.0]  # mean K_conc^0.9 per backbone

# Bonus benefit = PACT (β=0) regret - PACT+ (β=0.25) regret
# DeepSeek: 0.828 - 0.400 = +0.428
# GPT: 0.644 - 0.912 = -0.268
# Kimi: 0.632 - 0.704 = -0.072
# Llama: 0.732 - 0.312 = +0.420
bonus_benefit = [+0.428, -0.268, -0.072, +0.420]

# Regime classification per backbone (matches β-sweep narrative)
# - extreme self-decay: GPT, Kimi (bonus has no work AND mildly harmful)
# - self-decay edge: DeepSeek (small K_conc, but bonus produces gentle benefit)
# - burn-in jump: Llama (large K_conc, dramatic benefit)
regime_color = {
    "DeepSeek-V3.2":     "#1b3a6f",   # self-decay edge — deep navy
    "GPT-5.4-nano":      "#c0463f",   # extreme self-decay — red
    "Kimi-K2.6":         "#2c7a5e",   # extreme self-decay — green
    "Llama-4-Maverick":  "#b8723d",   # burn-in jump — burnt orange
}

# Single panel: K_conc on x-axis, bonus benefit on y-axis, scatter with colored markers
fig, ax = plt.subplots(figsize=(7.2, 4.6))

# Background bands for regime regions
# Self-decay edge: K_conc < 6 — pale blue
# Boundary / extreme self-decay: K_conc 6-13 — pale gray
# Burn-in jump: K_conc > 13 — pale orange
ax.axvspan(0, 6, color="#f0f4fa", alpha=0.6, zorder=0)
ax.axvspan(6, 13, color="#f5f5f5", alpha=0.6, zorder=0)
ax.axvspan(13, 18, color="#fdf0e6", alpha=0.6, zorder=0)

# Region labels at top
ax.text(3.0, 0.55, "self-decay edge\n(small $K_{\\mathrm{conc}}$)",
        fontsize=8, color="#5a73a3", ha="center", va="top",
        fontweight="semibold", alpha=0.85)
ax.text(9.5, 0.55, "boundary regime\n(bonus over-explores)",
        fontsize=8, color="#666666", ha="center", va="top",
        fontweight="semibold", alpha=0.85)
ax.text(15.5, 0.55, "burn-in jump\n(bonus drives escape)",
        fontsize=8, color="#a06030", ha="center", va="top",
        fontweight="semibold", alpha=0.85)

# Horizontal zero-benefit reference line
ax.axhline(y=0, color="#cccccc", linewidth=0.8, linestyle="-", zorder=1)

# Marker for each backbone (size scaled with |benefit| to highlight Llama + DeepSeek)
markers = {
    "DeepSeek-V3.2":     "o",
    "GPT-5.4-nano":      "s",
    "Kimi-K2.6":         "D",
    "Llama-4-Maverick":  "^",
}

for i, bb in enumerate(backbones):
    c = regime_color[bb]
    mk = markers[bb]
    x = k_conc[i]
    y = bonus_benefit[i]
    ax.scatter(x, y, s=160, color=c, marker=mk,
               edgecolor="white", linewidth=1.8, zorder=4)
    # Inline label next to each point
    if bb == "Llama-4-Maverick":
        ax.text(x - 0.4, y - 0.04, bb, fontsize=8.5, color=c,
                fontweight="semibold", va="top", ha="right", zorder=5)
    elif bb == "DeepSeek-V3.2":
        ax.text(x + 0.4, y + 0.02, bb, fontsize=8.5, color=c,
                fontweight="semibold", va="bottom", ha="left", zorder=5)
    elif bb == "GPT-5.4-nano":
        ax.text(x + 0.4, y, bb, fontsize=8.5, color=c,
                fontweight="semibold", va="center", ha="left", zorder=5)
    elif bb == "Kimi-K2.6":
        ax.text(x + 0.4, y + 0.02, bb, fontsize=8.5, color=c,
                fontweight="semibold", va="bottom", ha="left", zorder=5)

ax.set_xlabel(r"Mean concentration time $K_{\mathrm{conc}}^{0.9}$ "
              r"(episodes until $\mu_k^{\Theta,i}(\theta_i^\star) \geq 0.9$)",
              color=MUTED)
ax.set_ylabel(r"Bonus benefit  $\mathrm{Reg}(\text{PACT}) - \mathrm{Reg}(\text{PACT}^+)$",
              color=MUTED)
ax.set_xlim(0, 17.5)
ax.set_ylim(-0.55, 0.65)
ax.grid(axis="y", linestyle=":", linewidth=0.5, color="#dddddd")
ax.set_axisbelow(True)

# Style spines
for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color("#cccccc")

# Subtle annotation arrows for benefit interpretation
ax.annotate("",
            xy=(17.0, 0.55), xytext=(17.0, 0.05),
            arrowprops=dict(arrowstyle="->", color=LIGHTER, lw=0.8))
ax.text(17.0, 0.30, "  bonus helps", fontsize=7.5, color=LIGHTER,
        rotation=90, va="center", ha="left", style="italic")
ax.annotate("",
            xy=(17.0, -0.50), xytext=(17.0, -0.05),
            arrowprops=dict(arrowstyle="->", color=LIGHTER, lw=0.8))
ax.text(17.0, -0.30, "  bonus hurts", fontsize=7.5, color=LIGHTER,
        rotation=90, va="center", ha="left", style="italic")

plt.tight_layout()
out_pdf = OUT_DIR / "fig_e1_posterior_concentration_v3.pdf"
out_png = OUT_DIR / "fig_e1_posterior_concentration_v3.png"
fig.savefig(out_pdf, bbox_inches="tight")
fig.savefig(out_png, bbox_inches="tight", dpi=180)
plt.close(fig)
print(f"OK: {out_pdf.name}")
