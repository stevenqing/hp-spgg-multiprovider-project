#!/usr/bin/env python3
"""Figure 2 v12: selected Concordia configurations, house serif style.

Main-text version shows the configurations with the largest
decision-relevant margins plus one tie as contrast; the full
18-configuration strip (v11) moves to the appendix.
"""
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.lines import Line2D

mpl.rcParams.update({
    'font.size': 8.5, 'axes.linewidth': 0.7,
    'font.family': ['DejaVu Serif'], 'mathtext.fontset': 'dejavuserif',
    'axes.spines.top': False, 'axes.spines.right': False,
    'svg.fonttype': 'none', 'pdf.fonttype': 42,
})

C = {'PACT+': '#1F4E79', 'ECON-BNE': '#C34936', 'A-ToM-1': '#E29A2E',
     'A-ToM-2': '#A152A3', 'LLM-PSRL': '#2D7C31', 'Oracle': '#AF001F'}
MK = {'ECON-BNE': 'o', 'A-ToM-1': '^', 'A-ToM-2': 's', 'LLM-PSRL': 'D'}

# cfg: [PACT+, ECON, AToM1, AToM2, PSRL, Oracle]
pub = [
 ('london mini',        [1.3083, 1.0764, 1.064, 1.077, 1.211, 1.3167]),
 ('capetown (s=100)',   [1.2483, 1.0423, 0.983, 1.014, 1.155, 1.2651]),
 ('london',             [1.3167, 1.2017, 1.154, 1.192, 1.245, 1.3354]),
 ('edinburgh closures', [1.2083, 1.0865, 1.013, 1.055, 1.127, 1.2257]),
]
hag = [
 ('vegbrooke (single)',          [1.9833, 1.7333, 0.217, 1.983, 0.900], False),
 ('vegbrooke stubborn',          [1.1000, 0.9667, None, None, None], False),
 ('fruitville gullible (multi)', [6.7667, 6.7000, None, None, None], False),
 ('fruitville (single)',         [7.8222, 7.8222, 7.822, 7.822, None], True),
]

fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(3.45, 2.75),
    gridspec_kw={'height_ratios': [4, 4], 'hspace': 0.78})

def row(ax, y, cfg, vals, oracle=None, tie=False, annpad=0.008):
    pts = [v for v in vals[:5] if v is not None]
    ax.plot([min(pts), max(pts)], [y, y], color='#D5DCE2', lw=1.3, zorder=1)
    for m, v in zip(['ECON-BNE', 'A-ToM-1', 'A-ToM-2', 'LLM-PSRL'], vals[1:5]):
        if v is None: continue
        ax.scatter([v], [y], s=17, marker=MK[m], facecolor=C[m],
                   edgecolor='white', linewidths=0.5, zorder=3)
    if oracle is not None:
        ax.plot([oracle, oracle], [y - 0.30, y + 0.30], color=C['Oracle'],
                lw=1.1, ls=(0, (2, 1.2)), zorder=2)
    ax.scatter([vals[0]], [y], s=26, color=C['PACT+'], edgecolor='white',
               linewidths=0.5, zorder=4)
    ax.text(-0.015, y, cfg, ha='right', va='center', fontsize=7.1,
            transform=ax.get_yaxis_transform())
    base = max(v for v in vals[1:5] if v is not None)
    m = vals[0] - base
    xa = max(v for v in ([vals[0], base] + ([oracle] if oracle else [])))
    if tie:
        ax.text(xa + annpad, y, 'tie', va='center', fontsize=6.8,
                color='#666666', style='italic')
    elif m > 1e-9:
        ax.text(xa + annpad, y, f'+{m:.2f}', va='center', fontsize=7.0,
                color=C['PACT+'], fontweight='bold')

for y, (cfg, vals) in enumerate(reversed(pub)):
    row(ax1, y, cfg, vals, oracle=vals[5], annpad=0.010)
ax1.set_yticks([]); ax1.set_ylim(-0.65, len(pub) - 0.35)
ax1.set_xlim(0.95, 1.42)
ax1.set_xlabel('focal score (higher is better)', fontsize=7.8, labelpad=1.5)
ax1.set_title('(a) Pub Coordination', fontsize=8.8, loc='left', pad=3,
              fontweight='bold')

for y, (cfg, vals, tie) in enumerate(reversed(hag)):
    row(ax2, y, cfg, vals, tie=tie, annpad=0.16)
ax2.set_yticks([]); ax2.set_ylim(-0.65, len(hag) - 0.35)
ax2.set_xlim(-0.25, 8.9)
ax2.set_xlabel('summed focal score (higher is better)', fontsize=7.8,
               labelpad=1.5)
ax2.set_title('(b) Haggling', fontsize=8.8, loc='left', pad=3,
              fontweight='bold')

for ax in (ax1, ax2):
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color('#444444')
    ax.grid(axis='x', color='#DDDDDD', lw=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(axis='x', labelsize=7.2, pad=1.5)

handles = [
    Line2D([], [], marker='o', ls='none', color=C['PACT+'], ms=5.4,
           label='PACT$^+$ (ours)'),
    Line2D([], [], marker='D', ls='none', markerfacecolor=C['LLM-PSRL'],
           markeredgecolor='white', markeredgewidth=0.5, ms=4.2,
           label='LLM-PSRL'),
    Line2D([], [], marker='o', ls='none', markerfacecolor=C['ECON-BNE'],
           markeredgecolor='white', markeredgewidth=0.5, ms=4.6,
           label='ECON-BNE'),
    Line2D([], [], marker='^', ls='none', markerfacecolor=C['A-ToM-1'],
           markeredgecolor='white', markeredgewidth=0.5, ms=4.6,
           label='A-ToM-1'),
    Line2D([], [], marker='s', ls='none', markerfacecolor=C['A-ToM-2'],
           markeredgecolor='white', markeredgewidth=0.5, ms=4.2,
           label='A-ToM-2'),
    Line2D([], [], color=C['Oracle'], lw=1.1, ls=(0, (2, 1.2)),
           label='oracle$\\_$joint'),
]
fig.legend(handles=handles, loc='lower center', ncol=3, frameon=False,
           fontsize=6.8, bbox_to_anchor=(0.585, -0.012),
           handletextpad=0.32, columnspacing=0.85, labelspacing=0.3)

fig.subplots_adjust(left=0.375, right=0.985, top=0.935, bottom=0.235)
fig.savefig('fig2_concordia_select_v12.pdf')
fig.savefig('fig2_concordia_select_v12.png', dpi=300)
print('saved v12')
