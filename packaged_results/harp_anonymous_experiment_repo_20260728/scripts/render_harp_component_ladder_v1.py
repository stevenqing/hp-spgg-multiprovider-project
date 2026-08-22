"""E-G component knock-out ladder, Figure-6(c) bar grammar, log scale."""
from pathlib import Path
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

mpl.rcParams.update({
    "font.family": "serif", "font.serif": ["DejaVu Serif"], "font.size": 7,
    "axes.linewidth": 0.7, "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "pdf.fonttype": 42, "ps.fonttype": 42,
})
NAVY_D="#1B3A6F"; NAVY_M="#3D6CB3"; NAVY_L="#7B9FCF"; AMBER="#D4A04A"; MRED="#B64B45"
ROOT = Path(__file__).resolve().parents[1]

labels = ["full", r"$-$bonus", r"$-$update", r"$-$identity", r"$-$dispatch"]
means  = [0.014803811559212865, 0.015594443719659812, 0.6752610309174041,
          0.7000513484402628, 6.3236933621419436]
sems   = [0.006791947784878735, 0.007457581701212897, 0.11361913890079703,
          0.36842392466042223, 0.43850572649299185]
cols   = [NAVY_D, NAVY_M, NAVY_L, AMBER, MRED]

fig, ax = plt.subplots(figsize=(3.4, 1.38))
fig.subplots_adjust(left=0.19, right=0.985, top=0.97, bottom=0.16)
x = np.arange(5)
ax.bar(x, means, 0.62, color=cols, edgecolor="black", lw=0.6,
       yerr=sems, capsize=2.2, error_kw=dict(lw=0.8))
ax.set_yscale("log")
ax.set_ylim(0.004, 14)
ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=6.6)
ax.set_ylabel("cumulative regret at $K{=}20$", labelpad=1)
fig.savefig(ROOT / "arr_paper" / "figs" / "fig_e_g_ladder_v1.pdf")
print("done")
