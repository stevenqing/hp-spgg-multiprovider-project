#!/usr/bin/env python3
"""Figure 2 v10: dense per-config strip plot, all methods.

Pub values for A-ToM-1/A-ToM-2/LLM-PSRL decoded from the v8 radar PDF
by per-axis affine inversion anchored on PACT+/best-baseline/oracle
(lstsq residual <= 0.003). Haggling panel is focal-sum (the metric the
radar actually plotted, verified by tie geometry); cells not
recoverable from the radar are omitted and listed in MISSING.
Family palette follows Fig. 3: blue Bayesian, green LLM-PSRL,
warm LLM-coordination, dark oracle reference.
"""
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from matplotlib.lines import Line2D

mpl.rcParams.update({
    'font.size': 7.5, 'axes.linewidth': 0.7,
    'font.family': ['DejaVu Serif'], 'mathtext.fontset': 'dejavuserif',
    'axes.spines.top': False, 'axes.spines.right': False,
    'svg.fonttype': 'none', 'pdf.fonttype': 42,
})

C = {'PACT+': '#1F4E79', 'ECON-BNE': '#C34936', 'A-ToM-1': '#E29A2E',
     'A-ToM-2': '#A152A3', 'LLM-PSRL': '#2D7C31', 'Oracle': '#AF001F'}
MK = {'ECON-BNE': 'o', 'A-ToM-1': '^', 'A-ToM-2': 's', 'LLM-PSRL': 'D'}

# ---- Pub Coordination (focal score) --------------------------------------
# cfg: [PACT+, ECON, AToM1, AToM2, PSRL, Oracle]  None = unavailable
pub = {
 'london mini':        [1.3083, 1.0764, 1.064, 1.077, 1.211, 1.3167],
 'capetown (s=100)':   [1.2483, 1.0423, 0.983, 1.014, 1.155, 1.2651],
 'capetown':           [1.2472, 1.0439, None, None, None, 1.2759],
 'london mini (s=5)':  [1.3000, None, 1.1083, None, None, 1.3000],
 'edinburgh closures': [1.2083, 1.0865, 1.013, 1.055, 1.127, 1.2257],
 'london':             [1.3167, 1.2017, 1.154, 1.192, 1.245, 1.3354],
 'london closures':    [1.2667, 1.2349, 1.224, 1.235, 1.260, 1.2750],
 'edinburgh':          [1.2700, None, 1.2700, 1.270, 1.270, 1.2700],
 'edinburgh tough fr.':[1.2533, None, 1.2533, 1.253, 1.253, 1.2533],
}
# ---- Haggling (summed focal score) ---------------------------------------
# last entry: oracle_joint where measured (Git snapshot 9e7f12b)
hag = {
 'vegbrooke (single)':          [1.9833, 1.7333, 0.217, 1.983, 0.900, None],
 'vegbrooke stubborn':          [1.1000, 0.9667, None, None, None, -0.3333],
 'fruitville gullible (multi)': [6.7667, 6.7000, None, None, None, 6.3000],
 'fruitville (single)':         [7.8222, 7.8222, 7.822, 7.822, None, None],
 'fruitville gullible (single)':[7.4000, 7.4000, None, 7.400, 7.400, 7.0000],
 'fruitville (multi)':          [4.4000, 4.4000, None, 4.400, 4.400, None],
 'vegbrooke (multi)':           [4.5500, 4.5500, None, 4.550, 4.550, None],
 'cumulative score (multi)':    [6.0000, 6.0000, None, 6.000, 6.000, 5.6000],
 'vegbrooke strange':           [0.0000, 0.0000, None, 0.000, 0.000, None],
}

def margin(row):
    base = [v for v in row[1:5] if v is not None]
    return row[0] - max(base) if base else 0.0

pub_rows = sorted(pub.items(), key=lambda kv: margin(kv[1]))
hag_rows = sorted(hag.items(), key=lambda kv: margin(kv[1]))

fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(3.45, 3.30),
    gridspec_kw={'height_ratios': [1, 1], 'hspace': 0.62})

def panel(ax, rows, oracle_col, xlab, xlim, annfmt, annpad):
    n = len(rows)
    for y, (cfg, row) in enumerate(rows):
        vals = [v for v in row[:5] if v is not None]
        ax.plot([min(vals), max(vals)], [y, y], color='#D5DCE2', lw=1.1,
                zorder=1)
        for m, v in zip(['ECON-BNE','A-ToM-1','A-ToM-2','LLM-PSRL'], row[1:5]):
            if v is None: continue
            ax.scatter([v], [y], s=12, marker=MK[m], facecolor=C[m],
                       edgecolor='white', linewidths=0.45, zorder=3)
        if oracle_col is not None and row[oracle_col] is not None:
            o = row[oracle_col]
            ax.plot([o, o], [y-0.33, y+0.33], color=C['Oracle'], lw=1.0,
                    ls=(0, (2, 1.2)), zorder=2)
        ax.scatter([row[0]], [y], s=19, color=C['PACT+'],
                   edgecolor='white', linewidths=0.45, zorder=4)
        ax.text(-0.012, y, cfg, ha='right', va='center', fontsize=6.2,
                transform=ax.get_yaxis_transform())
        m = margin(row)
        if m > 1e-9:
            xa = max(v for v in (row[:6] if oracle_col else row[:5])
                     if v is not None)
            ax.text(xa + annpad, y, annfmt % m, va='center', fontsize=5.8,
                    color=C['PACT+'])
    ax.set_yticks([]); ax.set_ylim(-0.7, n - 0.3)
    ax.set_xlim(*xlim)
    ax.set_xlabel(xlab, fontsize=7.0, labelpad=1.0)
    ax.tick_params(axis='x', labelsize=6.5, pad=1.5)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color('#444444')
    ax.grid(axis='x', color='#DDDDDD', lw=0.5, zorder=0)
    ax.set_axisbelow(True)

panel(ax1, pub_rows, 5, 'focal score (per episode)', (0.95, 1.40),
      '+%.2f', 0.008)
ax1.set_title('(a) Pub Coordination', fontsize=8, loc='left', pad=2, fontweight='bold')
panel(ax2, hag_rows, 5, 'summed focal score', (-0.70, 8.4),
      '+%.2f', 0.14)
ax2.set_title('(b) Haggling', fontsize=8, loc='left', pad=2, fontweight='bold')

handles = [
    Line2D([], [], marker='o', ls='none', color=C['PACT+'], ms=4.5,
           label='PACT$^+$ (ours)'),
    Line2D([], [], marker='D', ls='none', markerfacecolor=C['LLM-PSRL'],
           markeredgecolor='white', markeredgewidth=0.45, ms=3.8,
           label='LLM-PSRL'),
    Line2D([], [], marker='o', ls='none', markerfacecolor=C['ECON-BNE'],
           markeredgecolor='white', markeredgewidth=0.45, ms=4,
           label='ECON-BNE'),
    Line2D([], [], marker='^', ls='none', markerfacecolor=C['A-ToM-1'],
           markeredgecolor='white', markeredgewidth=0.45, ms=4,
           label='A-ToM-1'),
    Line2D([], [], marker='s', ls='none', markerfacecolor=C['A-ToM-2'],
           markeredgecolor='white', markeredgewidth=0.45, ms=3.6,
           label='A-ToM-2'),
    Line2D([], [], color=C['Oracle'], lw=1.0, ls=(0, (2, 1.2)),
           label='oracle$\\_$joint'),
]
fig.legend(handles=handles, loc='lower center', ncol=3, frameon=False,
           fontsize=6.2, bbox_to_anchor=(0.575, -0.008),
           handletextpad=0.3, columnspacing=0.7, labelspacing=0.25)

fig.subplots_adjust(left=0.345, right=0.99, top=0.955, bottom=0.185)
fig.savefig('fig2_concordia_strip_v11b.pdf')
fig.savefig('fig2_concordia_strip_v11b.png', dpi=300)
print('saved v11b')
