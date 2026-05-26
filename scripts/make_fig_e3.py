"""
Fig 7 — E3 n-agent scaling.
Single panel: 3 curves (PACT, PACT+, Joint-PSRL) across n in {2,3,4,5}.
Llama-4-Maverick backbone, |Theta_i|=4 fixed, 10 seeds.
Storage gap annotated above x-axis. n=2 boundary shaded.
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

# E3 disk data (10 seeds, Llama, |Theta_i|=4)
n_values = [2, 3, 4, 5]
hpsmg_mean      = [0.070, 0.232, 0.108, 0.870]
hpsmg_sem       = [0.037, 0.142, 0.108, 0.588]
hpsmg_p_mean    = [2.962, 0.000, 0.000, 0.278]
hpsmg_p_sem     = [0.545, 0.000, 0.000, 0.278]
jpsrl_mean      = [0.275, 0.348, 0.216, 1.252]
jpsrl_sem       = [0.140, 0.232, 0.216, 0.648]

# Storage gap (analytic)
theta_i = 4
storage_factored = [n * theta_i for n in n_values]      # 8, 12, 16, 20
storage_joint    = [theta_i ** n for n in n_values]     # 16, 64, 256, 1024
storage_ratio    = [j/f for f, j in zip(storage_factored, storage_joint)]

# Colors
C_HPSMG      = "#3d6cb3"   # mid blue
C_HPSMG_PLUS = "#1b3a6f"   # deep navy (ours, primary)
C_JPSRL      = "#7b9fcf"   # pale blue (same family, just for contrast)

fig, ax = plt.subplots(figsize=(7.6, 4.4))

x = np.arange(len(n_values))

# Shade n=2 column as "degenerate boundary regime"
ax.axvspan(-0.4, 0.5, color="#f5f5f5", alpha=0.7, zorder=0)
ax.text(0.05, 3.65, "boundary regime  ($|\\Theta_i|^n$ small)",
        fontsize=7.5, color=MUTED, ha="center", va="top",
        style="italic", alpha=0.85)

# 3 curves
ax.errorbar(x, jpsrl_mean, yerr=jpsrl_sem,
            color=C_JPSRL, linewidth=1.6, marker="s", markersize=7,
            markerfacecolor="white", markeredgewidth=1.6,
            capsize=3, capthick=0.7, elinewidth=0.7,
            label="Joint-PSRL", zorder=3, linestyle="--")

ax.errorbar(x, hpsmg_mean, yerr=hpsmg_sem,
            color=C_HPSMG, linewidth=2.0, marker="o", markersize=7,
            markerfacecolor="white", markeredgewidth=1.8,
            capsize=3, capthick=0.7, elinewidth=0.7,
            label="PACT", zorder=4)

ax.errorbar(x, hpsmg_p_mean, yerr=hpsmg_p_sem,
            color=C_HPSMG_PLUS, linewidth=2.4, marker="D", markersize=7,
            markerfacecolor="white", markeredgewidth=1.8,
            capsize=3, capthick=0.7, elinewidth=0.7,
            label=r"PACT$^+$ (ours)", zorder=5)

# Direct labels at end of curves
ax.text(x[-1] + 0.18, jpsrl_mean[-1] + 0.05, "Joint-PSRL",
        fontsize=8.5, color=C_JPSRL, fontweight="semibold",
        va="bottom", ha="left", zorder=6)
ax.text(x[-1] + 0.18, hpsmg_mean[-1], "PACT",
        fontsize=8.5, color=C_HPSMG, fontweight="semibold",
        va="center", ha="left", zorder=6)
ax.text(x[-1] + 0.18, hpsmg_p_mean[-1] - 0.05, r"PACT$^+$",
        fontsize=8.5, color=C_HPSMG_PLUS, fontweight="semibold",
        va="top", ha="left", zorder=6)

# Storage gap annotations above x-axis labels
y_storage = -0.65
for i, (n, f, j, r) in enumerate(zip(n_values, storage_factored, storage_joint, storage_ratio)):
    if r > 10:
        ratio_str = f"{r:.0f}×"
        weight = "bold"
        col = "#a52a2a"  # highlight large ratios
    else:
        ratio_str = f"{r:.1f}×"
        weight = "normal"
        col = MUTED
    ax.text(x[i], y_storage,
            f"{f}\nvs\n{j}\n({ratio_str})",
            fontsize=7, color=col, ha="center", va="top",
            fontweight=weight, linespacing=1.2)

# Label for storage row
ax.text(-0.55, y_storage - 0.05,
        "storage:\n   $n|\\Theta_i|$\n   $|\\Theta_i|^n$\n   (ratio)",
        fontsize=7, color=MUTED, ha="left", va="top", style="italic",
        linespacing=1.2)

ax.set_xticks(x)
ax.set_xticklabels([str(n) for n in n_values])
ax.set_xlim(-0.6, len(n_values) - 1 + 1.6)
ax.set_xlabel(r"Number of agents $n$", color=MUTED, labelpad=42)
ax.set_ylabel(r"Cumulative regret at $K = 20$", color=MUTED)
ax.set_ylim(-0.4, 3.7)
ax.grid(axis="y", linestyle=":", linewidth=0.5, color="#dddddd")
ax.set_axisbelow(True)

for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color("#cccccc")

plt.tight_layout()
out_pdf = OUT_DIR / "fig_e3_n_agent_scaling_v3.pdf"
out_png = OUT_DIR / "fig_e3_n_agent_scaling_v3.png"
fig.savefig(out_pdf, bbox_inches="tight")
fig.savefig(out_png, bbox_inches="tight", dpi=180)
plt.close(fig)
print(f"OK: {out_pdf.name}")
