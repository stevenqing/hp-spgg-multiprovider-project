#!/usr/bin/env python3
"""Figure 2 v14: selected configs, broken Haggling axis, oracle_joint ticks
in both panels. Haggling oracle_joint values recovered from Git snapshot
9e7f12b compact JSONs (beta_obj=0 endpoints, per-episode focal sum; one
focal player per episode so focal sum equals focal_score_mean):
gullible single 7.0, stubborn -0.333333, cumulative 5.6, gullible multi 6.3.
No oracle value exists for vegbrooke (single)."""
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

pub = [
 ('london mini',        [1.3083, 1.0764, 1.064, 1.077, 1.211, 1.3167]),
 ('capetown (s=100)',   [1.2483, 1.0423, 0.983, 1.014, 1.155, 1.2651]),
 ('london',             [1.3167, 1.2017, 1.154, 1.192, 1.245, 1.3354]),
 ('edinburgh closures', [1.2083, 1.0865, 1.013, 1.055, 1.127, 1.2257]),
]
# [PACT+, ECON, AToM1, AToM2, PSRL, oracle_joint]
hag = [
 ('vegbrooke (single)',          [1.9833, 1.7333, 0.217, 1.983, 0.900, None], False),
 ('vegbrooke stubborn',          [1.1000, 0.9667, None, None, None, -0.3333], False),
 ('fruitville gullible (multi)', [6.7667, 6.7000, None, None, None, 6.3000], False),
 ('fruitville gullible (single)',[7.4000, 7.4000, None, 7.400, 7.400, 7.0000], True),
]

fig = plt.figure(figsize=(3.45, 2.75))
gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], hspace=0.80,
                      width_ratios=[0.52, 0.48], wspace=0.06)
ax1 = fig.add_subplot(gs[0, :])
axL = fig.add_subplot(gs[1, 0])
axR = fig.add_subplot(gs[1, 1], sharey=axL)

def draw(ax, y, vals, oracle=None, tie=False, label=None, annpad=0.01,
         annotate=True):
    pts = [v for v in vals[:5] if v is not None]
    if max(pts) > min(pts):
        ax.plot([min(pts), max(pts)], [y, y], color='#D5DCE2', lw=1.3,
                zorder=1)
    for m, v in zip(['ECON-BNE', 'A-ToM-1', 'A-ToM-2', 'LLM-PSRL'],
                    vals[1:5]):
        if v is None: continue
        ax.scatter([v], [y], s=17, marker=MK[m], facecolor=C[m],
                   edgecolor='white', linewidths=0.5, zorder=3)
    if oracle is not None:
        ax.plot([oracle, oracle], [y - 0.30, y + 0.30], color=C['Oracle'],
                lw=1.1, ls=(0, (2, 1.2)), zorder=2)
    ax.scatter([vals[0]], [y], s=26, color=C['PACT+'], edgecolor='white',
               linewidths=0.5, zorder=4)
    if label is not None:
        ax.text(-0.02, y, label, ha='right', va='center', fontsize=7.1,
                transform=ax.get_yaxis_transform())
    if not annotate:
        return
    base = max(v for v in vals[1:5] if v is not None)
    m = vals[0] - base
    xa = max(v for v in ([vals[0], base] + ([oracle] if oracle else [])))
    if tie:
        ax.text(xa + annpad, y, 'tie', va='center', fontsize=6.8,
                color='#666666', style='italic')
    elif m > 1e-9:
        ax.text(xa + annpad, y, f'+{m:.2f}', va='center', fontsize=7.0,
                color=C['PACT+'], fontweight='bold')

# ---- (a) Pub ----
for y, (cfg, vals) in enumerate(reversed(pub)):
    draw(ax1, y, vals, oracle=vals[5], label=cfg, annpad=0.010)
ax1.set_yticks([]); ax1.set_ylim(-0.65, len(pub) - 0.35)
ax1.set_xlim(0.95, 1.42)
ax1.set_xlabel('focal score (higher is better)', fontsize=7.8, labelpad=1.5)
ax1.set_title('(a) Pub Coordination', fontsize=8.8, loc='left', pad=3,
              fontweight='bold')

# ---- (b) Haggling, broken axis ----
XL = (-0.62, 2.45)   # left segment
XR = (5.95, 8.60)    # right segment
for y, (cfg, vals, tie) in enumerate(reversed(hag)):
    onleft = vals[0] < 3.0
    ax = axL if onleft else axR
    draw(ax, y, vals, oracle=vals[5], tie=tie, label=None, annpad=0.07,
         annotate=True)
    axL.text(-0.02, y, cfg, ha='right', va='center', fontsize=7.1,
             transform=axL.get_yaxis_transform())
axL.set_yticks([]); axL.set_ylim(-0.65, len(hag) - 0.35)
axL.set_xlim(*XL); axR.set_xlim(*XR)
axR.tick_params(axis='y', left=False, labelleft=False)
axL.set_title('(b) Haggling', fontsize=8.8, loc='left', pad=3,
              fontweight='bold')
fig.text(0.635, 0.118, 'summed focal score (higher is better)',
         ha='center', fontsize=7.8)
# break marks
d = 0.9
kw = dict(marker=[(-1, -d), (1, d)], markersize=5, linestyle='none',
          color='#444444', mec='#444444', mew=0.8, clip_on=False)
axL.plot([1], [0], transform=axL.transAxes, **kw)
axR.plot([0], [0], transform=axR.transAxes, **kw)
axL.spines['right'].set_visible(False)
axR.spines['left'].set_visible(False)

for ax in (ax1, axL, axR):
    if ax is not axR:
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
           fontsize=6.8, bbox_to_anchor=(0.595, -0.012),
           handletextpad=0.32, columnspacing=0.85, labelspacing=0.3)

fig.subplots_adjust(left=0.375, right=0.985, top=0.935, bottom=0.235)
fig.savefig('fig2_concordia_select_v14.pdf')
fig.savefig('fig2_concordia_select_v14.png', dpi=300)
print('saved v14')
