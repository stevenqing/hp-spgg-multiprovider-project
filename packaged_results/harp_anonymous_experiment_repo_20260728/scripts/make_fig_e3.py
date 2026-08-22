"""Figure 3 upper panel: regret and persona-storage scaling by agent count."""
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FuncFormatter
import numpy as np
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parents[1] / "arr_paper" / "figs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif"],
    "font.size": 7,
    "axes.labelsize": 7,
    "axes.linewidth": 0.7,
    "axes.edgecolor": "#777777",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.labelsize": 6.5,
    "ytick.labelsize": 6.5,
    "xtick.color": "#444444",
    "ytick.color": "#444444",
    "legend.frameon": False,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.dpi": 200,
})

INK = "#202020"
MUTED = "#555555"
GRID = "#d9d9d9"

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

fig = plt.figure(figsize=(3.4, 2.45))
grid = fig.add_gridspec(2, 1, height_ratios=(3.0, 1.15), hspace=0.08)
ax = fig.add_subplot(grid[0])
storage_ax = fig.add_subplot(grid[1], sharex=ax)
fig.subplots_adjust(left=0.19, right=0.985, top=0.94, bottom=0.17)

x = np.asarray(n_values)
for axis in (ax, storage_ax):
    axis.axvspan(1.65, 2.35, color="#f1f1f1", zorder=0)
    axis.set_xlim(1.55, 5.25)
    axis.grid(axis="y", linestyle=":", linewidth=0.55, color=GRID)
    axis.set_axisbelow(True)

ax.errorbar(x, jpsrl_mean, yerr=jpsrl_sem,
            color=C_JPSRL, linewidth=1.6, marker="s", markersize=7,
            markerfacecolor="white", markeredgewidth=1.6,
            capsize=2.5, capthick=0.7, elinewidth=0.7,
            label="Joint-PSRL", zorder=3, linestyle="--")

ax.errorbar(x, hpsmg_mean, yerr=hpsmg_sem,
            color=C_HPSMG, linewidth=1.8, marker="o", markersize=5,
            markerfacecolor="white", markeredgewidth=1.4,
            capsize=2.5, capthick=0.7, elinewidth=0.7,
            label="HARP", zorder=4)

ax.errorbar(x, hpsmg_p_mean, yerr=hpsmg_p_sem,
            color=C_HPSMG_PLUS, linewidth=2.0, marker="D", markersize=5,
            markerfacecolor="white", markeredgewidth=1.4,
            capsize=2.5, capthick=0.7, elinewidth=0.7,
            label=r"HARP$^+$", zorder=5)

ax.set_ylim(-0.08, 3.72)
ax.set_ylabel("Cumulative regret\nat $K{=}20$")
ax.tick_params(axis="x", labelbottom=False, bottom=False)
handles, labels = ax.get_legend_handles_labels()
order = (2, 1, 0)
ax.legend([handles[index] for index in order], [labels[index] for index in order],
          loc="upper right", ncol=1, fontsize=6.1, handlelength=2.2,
          borderaxespad=0.3, labelspacing=0.25)

storage_ax.set_yscale("log")
storage_ax.plot(x, storage_joint, color="#a94442", linewidth=1.25,
                marker="s", markersize=3.8, label=r"Joint $|\Theta_i|^n$", zorder=3)
storage_ax.plot(x, storage_factored, color="#555555", linewidth=1.25,
                marker="o", markersize=3.8, label=r"Factored $n|\Theta_i|$", zorder=4)
storage_ax.set_ylim(6, 5000)
storage_ax.yaxis.set_major_locator(FixedLocator([10, 100, 1000]))
storage_ax.yaxis.set_major_formatter(FuncFormatter(
    lambda value, _: "1k" if value == 1000 else f"{int(value)}"
))
storage_ax.set_ylabel("Stored\nstates", labelpad=4)
storage_ax.set_xticks(x)
storage_ax.set_xlabel(r"Number of agents $n$", labelpad=2)
storage_ax.legend(loc="upper left", ncol=2, fontsize=5.4, handlelength=1.7,
                  columnspacing=0.9, borderaxespad=0.25)
for n, joint, ratio in zip(x, storage_joint, storage_ratio):
    ratio_label = f"{ratio:.1f}x" if ratio < 10 else f"{ratio:.0f}x"
    storage_ax.annotate(ratio_label, (n, joint), xytext=(0, 5),
                        textcoords="offset points", ha="center", va="bottom",
                        fontsize=5.6, color="#8f302f", fontweight="bold")

out_pdf = OUT_DIR / "fig_e3_n_agent_scaling_v3.pdf"
out_png = OUT_DIR / "fig_e3_n_agent_scaling_v3.png"
fig.savefig(out_pdf)
fig.savefig(out_png, dpi=220)
plt.close(fig)
print(f"OK: {out_pdf.name}")
