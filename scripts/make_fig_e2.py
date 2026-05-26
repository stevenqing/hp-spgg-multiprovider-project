"""
Fig 6 — E2 type space size scaling.
2-curve line plot: PACT vs PACT+ across |Theta_i| = {2..6}.
Llama-4-Maverick backbone, 10 seeds.
"""
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parents[1] / "arr_paper" / "figs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "Inter",
    "font.sans-serif": ["Inter", "Helvetica Neue", "Arial", "DejaVu Sans"],
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

# E2 disk data (10 seeds, Llama-4-Maverick)
theta_values = [2, 3, 4, 5, 6]
hpsmg_mean    = [0.198, 0.632, 0.232, 0.910, 1.280]
hpsmg_sem     = [0.135, 0.494, 0.142, 0.110, 0.272]
hpsmg_p_mean  = [0.062, 0.000, 0.000, 0.772, 0.200]
hpsmg_p_sem   = [0.062, 0.000, 0.000, 0.322, 0.082]

# Colors (v3 system)
C_HPSMG      = "#3d6cb3"   # mid blue
C_HPSMG_PLUS = "#1b3a6f"   # deep navy

fig, ax = plt.subplots(figsize=(7.2, 4.2))

x = np.arange(len(theta_values))

# Shaded separation band (gap between two curves)
ax.fill_between(x, hpsmg_p_mean, hpsmg_mean,
                color="#e6efff", alpha=0.6, zorder=1,
                label="separation (bonus benefit)")

# PACT (vanilla)
ax.errorbar(x, hpsmg_mean, yerr=hpsmg_sem,
            color=C_HPSMG, linewidth=2.0, marker="o", markersize=7,
            markerfacecolor="white", markeredgewidth=1.8,
            capsize=3.5, capthick=0.8, elinewidth=0.8,
            label="PACT", zorder=3)

# PACT+ (ours)
ax.errorbar(x, hpsmg_p_mean, yerr=hpsmg_p_sem,
            color=C_HPSMG_PLUS, linewidth=2.4, marker="D", markersize=7,
            markerfacecolor="white", markeredgewidth=1.8,
            capsize=3.5, capthick=0.8, elinewidth=0.8,
            label=r"PACT$^+$ (ours)", zorder=4)

# Inline labels at end of curves
ax.text(x[-1] + 0.15, hpsmg_mean[-1], "PACT",
        fontsize=9, color=C_HPSMG, fontweight="semibold",
        va="center", ha="left")
ax.text(x[-1] + 0.15, hpsmg_p_mean[-1] - 0.05, r"PACT$^+$ (ours)",
        fontsize=9, color=C_HPSMG_PLUS, fontweight="semibold",
        va="top", ha="left")

# Inline separation values at top
for i, t in enumerate(theta_values):
    sep = hpsmg_mean[i] - hpsmg_p_mean[i]
    ax.text(x[i], hpsmg_mean[i] + hpsmg_sem[i] + 0.10,
            f"+{sep:.2f}",
            fontsize=7.5, color=MUTED, ha="center", va="bottom",
            style="italic")

ax.set_xticks(x)
ax.set_xticklabels([str(t) for t in theta_values])
ax.set_xlim(-0.4, len(theta_values) - 1 + 1.9)
ax.set_xlabel(r"Type-space size $|\Theta_i|$ (persona count)", color=MUTED)
ax.set_ylabel(r"Cumulative regret at $K = 20$", color=MUTED)
ax.set_ylim(-0.15, 1.85)
ax.grid(axis="y", linestyle=":", linewidth=0.5, color="#dddddd")
ax.set_axisbelow(True)

for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color("#cccccc")

plt.tight_layout()
out_pdf = OUT_DIR / "fig_e2_type_scaling_v3.pdf"
out_png = OUT_DIR / "fig_e2_type_scaling_v3.png"
fig.savefig(out_pdf, bbox_inches="tight")
fig.savefig(out_png, bbox_inches="tight", dpi=180)
plt.close(fig)
print(f"OK: {out_pdf.name}")
