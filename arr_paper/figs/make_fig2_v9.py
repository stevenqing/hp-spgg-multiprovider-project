#!/usr/bin/env python3
"""Figure 2 redesign: Concordia results as a two-panel dumbbell plot.

Panel (a) Pub Coordination: per-episode focal score. Best in-prompt
baseline -> PACT+ dumbbell, oracle_joint as a vertical tick per row.
Panel (b) Haggling: Nash product. Baseline -> PACT+ dumbbell, margin
annotated. Rows sorted by margin within each panel.
Colours match the paper's existing figure palette.
"""
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

mpl.rcParams.update({
    'font.size': 8.0, 'axes.linewidth': 0.8,
    'font.family': ['DejaVu Sans', 'Helvetica', 'Arial', 'sans-serif'],
    'axes.spines.top': False, 'axes.spines.right': False,
    'svg.fonttype': 'none', 'pdf.fonttype': 42,
})

C_PACT = '#1F4E79'      # paper blue for PACT+
C_BASE = '#C24A36'      # paper red-brown (ECON-BNE family)
C_BASE2 = '#E39A2F'     # paper orange (A-ToM-1)
C_ORACLE = '#2F2F2F'
C_LINE = '#B9C4CE'

# --- Pub Coordination (focal score) ---------------------------------------
# config, s, pact, baseline_name, baseline, oracle
pub = [
    ('london mini', 30, 1.3083, 'E', 1.0764, 1.3167),
    ('capetown', 100, 1.2483, 'E', 1.0423, 1.2651),
    ('capetown', 30, 1.2472, 'E', 1.0439, 1.2759),
    ('london mini', 5, 1.3000, 'A', 1.1083, 1.3000),
    ('edinburgh closures', 30, 1.2083, 'E', 1.0865, 1.2257),
    ('london', 30, 1.3167, 'E', 1.2017, 1.3354),
    ('london closures', 30, 1.2667, 'E', 1.2349, 1.2750),
    ('edinburgh', 30, 1.2700, 'A', 1.2700, 1.2700),
    ('edinburgh tough fr.', 30, 1.2533, 'A', 1.2533, 1.2533),
]
pub.sort(key=lambda r: r[2] - r[4])  # ascending margin, largest at top after invert

# --- Haggling (Nash product) ----------------------------------------------
hag = [
    ('vegbrooke (multi)', 5.1000, 4.7833),
    ('fruitville gullible (multi)', 5.0889, 4.7778),
    ('fruitville', 3.8222, 3.5611),
    ('fruitville (multi)', 4.8000, 4.5500),
    ('vegbrooke stubborn', 0.1667, 0.1000),
    ('vegbrooke', 0.2694, 0.2139),
    ('fruitville gullible', 6.0000, 6.0000),
    ('vegbrooke strange', 0.0000, 0.0000),
    ('cumulative score (multi)', 4.0000, 4.0000),
]
hag.sort(key=lambda r: r[1] - r[2])

fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(3.45, 3.9),
    gridspec_kw={'height_ratios': [1, 1], 'hspace': 0.52})

# ---- panel (a) -----------------------------------------------------------
ys = np.arange(len(pub))
for y, (cfg, s, pact, bname, base, orc) in zip(ys, pub):
    tie = abs(pact - base) < 1e-9
    if not tie:
        ax1.plot([base, pact], [y, y], color=C_LINE, lw=1.4, zorder=1)
        col = C_BASE if bname == 'E' else C_BASE2
        ax1.scatter([base], [y], s=16, color=col, zorder=3,
                    marker='o', facecolor='white', linewidths=1.2)
    ax1.plot([orc, orc], [y - 0.34, y + 0.34], color=C_ORACLE, lw=1.1,
             ls=(0, (2, 1.2)), zorder=2)
    ax1.scatter([pact], [y], s=20, color=C_PACT, zorder=4)
    lab = f'{cfg}' + (f' (s={s})' if s != 30 else '')
    ax1.text(-0.012, y, lab, ha='right', va='center', fontsize=7.0,
             transform=ax1.get_yaxis_transform())
    m = pact - base
    if m > 1e-9:
        ax1.text(max(pact, orc) + 0.010, y, f'+{m:.2f}', va='center',
                 fontsize=6.3, color=C_PACT)
ax1.set_yticks([])
ax1.set_ylim(-0.7, len(pub) - 0.3)
ax1.set_xlim(1.00, 1.42)
ax1.set_xlabel('focal score (per episode)', fontsize=7.5, labelpad=1.5)
ax1.set_title('(a) Pub Coordination', fontsize=8.5, loc='left', pad=3)
ax1.tick_params(axis='x', labelsize=7)
ax1.spines['left'].set_visible(False)

# ---- panel (b) -----------------------------------------------------------
ys = np.arange(len(hag))
for y, (cfg, pact, base) in zip(ys, hag):
    tie = abs(pact - base) < 1e-9
    if not tie:
        ax2.plot([base, pact], [y, y], color=C_LINE, lw=1.4, zorder=1)
        ax2.scatter([base], [y], s=16, color=C_BASE, zorder=3,
                    marker='o', facecolor='white', linewidths=1.2)
    ax2.scatter([pact], [y], s=20, color=C_PACT, zorder=4)
    ax2.text(-0.012, y, cfg, ha='right', va='center', fontsize=7.0,
             transform=ax2.get_yaxis_transform())
    m = pact - base
    if m > 1e-9:
        ax2.text(pact + 0.10, y, f'+{m:.2f}', va='center', fontsize=6.3,
                 color=C_PACT)
ax2.set_yticks([])
ax2.set_ylim(-0.7, len(hag) - 0.3)
ax2.set_xlim(-0.15, 7.0)
ax2.set_xlabel('Nash product', fontsize=7.5, labelpad=1.5)
ax2.set_title('(b) Haggling', fontsize=8.5, loc='left', pad=3)
ax2.tick_params(axis='x', labelsize=7)
ax2.spines['left'].set_visible(False)

# ---- legend --------------------------------------------------------------
from matplotlib.lines import Line2D
handles = [
    Line2D([], [], marker='o', ls='none', color=C_PACT, ms=5,
           label='PACT$^+$ (ours)'),
    Line2D([], [], marker='o', ls='none', markerfacecolor='white',
           markeredgecolor=C_BASE, markeredgewidth=1.2, ms=5,
           label='ECON-BNE'),
    Line2D([], [], marker='o', ls='none', markerfacecolor='white',
           markeredgecolor=C_BASE2, markeredgewidth=1.2, ms=5,
           label='A-ToM-1'),
    Line2D([], [], color=C_ORACLE, lw=1.1, ls=(0, (2, 1.2)),
           label='oracle$\\_$joint'),
]
fig.legend(handles=handles, loc='lower center', ncol=4, frameon=False,
           fontsize=6.8, bbox_to_anchor=(0.56, -0.005),
           handletextpad=0.35, columnspacing=0.9)

fig.subplots_adjust(left=0.36, right=0.985, top=0.94, bottom=0.135)
fig.savefig('fig2_concordia_dumbbell_v9.pdf')
fig.savefig('fig2_concordia_dumbbell_v9.png', dpi=300)
print('done')
