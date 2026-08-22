#!/usr/bin/env python3
"""Figure 4: selected Concordia configs with the shared paper method set.

Panel (a) uses the legacy joint oracle reference; panel (b) uses the exact
focal oracle. The four displayed LLM systems, their order, colors, and markers
match main-paper Figures 2 and 6.
"""
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.lines import Line2D

SCRIPT_PATH = Path(__file__).resolve()
ROOT = SCRIPT_PATH.parents[2] if SCRIPT_PATH.parent.name == "figs" else SCRIPT_PATH.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from paper_comparison_methods import (  # noqa: E402
    METHOD_COLORS,
    METHOD_LABELS,
    METHOD_MARKERS,
    ORACLE_COLOR,
    ORACLE_LABEL,
    ORACLE_LINESTYLE,
)

mpl.rcParams.update({
    'font.size': 8.5, 'axes.linewidth': 0.7,
    'font.family': ['DejaVu Serif'], 'mathtext.fontset': 'dejavuserif',
    'axes.spines.top': False, 'axes.spines.right': False,
    'svg.fonttype': 'none', 'pdf.fonttype': 42,
})

LOCAL_METHODS = (
    ("econ_bne", 1),
    ("atom_tom1", 2),
    ("llm_psrl", 4),
)

pub = [
 ('london mini',        [1.3083, 1.0764, 1.064, 1.077, 1.211, 1.3167]),
 ('capetown (s=100)',   [1.2483, 1.0423, 0.983, 1.014, 1.155, 1.2651]),
 ('london',             [1.3167, 1.2017, 1.154, 1.192, 1.245, 1.3354]),
 ('edinburgh closures', [1.2083, 1.0865, 1.013, 1.055, 1.127, 1.2257]),
]
# [PACT+, ECON, AToM1, AToM2, PSRL, true oracle_focal]
hag = [
 ('vegbrooke (single)', [1.9833, 1.7333, 0.217, 1.983, 0.900, 1.9833], False),
 ('vegbrooke stubborn', [1.1000, 0.9667, None, None, None, 9.2667], False),
 ('fruitville gullible (multi)',
                        [6.7667, 6.7000, None, None, None, 14.600], False),
 ('fruitville (single)',[7.8222, 7.8222, 7.822, 7.822, None, 7.8222], True),
]

fig = plt.figure(figsize=(3.45, 2.75))
gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], hspace=0.80,
                      width_ratios=[0.34, 0.66], wspace=0.06)
ax1 = fig.add_subplot(gs[0, :])
axL = fig.add_subplot(gs[1, 0])
axR = fig.add_subplot(gs[1, 1], sharey=axL)

def draw(ax, y, vals, oracle=None, ocolor=ORACLE_COLOR, tie=False, label=None,
         annpad=0.01, annotate=True):
    pts = [vals[0], *[vals[index] for _, index in LOCAL_METHODS if vals[index] is not None]]
    if max(pts) > min(pts):
        ax.plot([min(pts), max(pts)], [y, y], color='#D5DCE2', lw=1.3,
                zorder=1)
    for method, index in LOCAL_METHODS:
        value = vals[index]
        if value is None:
            continue
        ax.scatter([value], [y], s=17, marker=METHOD_MARKERS[method], facecolor=METHOD_COLORS[method],
                   edgecolor='white', linewidths=0.5, zorder=3)
    if oracle is not None:
        ax.plot([oracle, oracle], [y - 0.30, y + 0.30], color=ocolor,
                lw=1.1, ls=ORACLE_LINESTYLE, zorder=2)
    ax.scatter([vals[0]], [y], s=26, color=METHOD_COLORS['pact_family'], edgecolor='white',
               linewidths=0.5, zorder=4)
    if label is not None:
        ax.text(-0.02, y, label, ha='right', va='center', fontsize=7.1,
                transform=ax.get_yaxis_transform())
    if not annotate:
        return
    base = max(vals[index] for _, index in LOCAL_METHODS if vals[index] is not None)
    m = vals[0] - base
    xa = max(vals[0], base)
    if tie:
        ax.text(xa + annpad, y, 'tie', va='center', fontsize=6.8,
                color='#666666', style='italic')
    elif m > 1e-9:
        ax.text(xa + annpad, y, f'+{m:.2f}', va='center', fontsize=7.0,
            color=METHOD_COLORS['pact_family'], fontweight='bold')

# ---- (a) Pub ----
for y, (cfg, vals) in enumerate(reversed(pub)):
    draw(ax1, y, vals, oracle=vals[5], ocolor=ORACLE_COLOR, label=cfg,
         annpad=0.010)
ax1.set_yticks([]); ax1.set_ylim(-0.65, len(pub) - 0.35)
ax1.set_xlim(0.95, 1.42)
ax1.set_xlabel('focal score (higher is better)', fontsize=7.8, labelpad=1.5)
ax1.set_title('(a) Pub Coordination', fontsize=8.8, loc='left', pad=3,
              fontweight='bold')

# ---- (b) Haggling, broken axis ----
XL = (-0.25, 3.30)
XR = (5.90, 15.30)
def seg(v):
    return axL if v < 3.0 else axR
for y, (cfg, vals, tie) in enumerate(reversed(hag)):
    ax = seg(vals[0])
    draw(ax, y, vals, oracle=None, tie=tie, label=None, annpad=0.20,
         annotate=True)
    o = vals[5]
    seg(o).plot([o, o], [y - 0.30, y + 0.30], color=ORACLE_COLOR, lw=1.1,
                ls=ORACLE_LINESTYLE, zorder=2)
    axL.text(-0.02, y, cfg, ha='right', va='center', fontsize=7.1,
             transform=axL.get_yaxis_transform())
axL.set_yticks([]); axL.set_ylim(-0.65, len(hag) - 0.35)
axL.set_xlim(*XL); axR.set_xlim(*XR)
axL.set_xticks([0, 1, 2, 3]); axR.set_xticks([6, 8, 10, 12, 14])
axR.tick_params(axis='y', left=False, labelleft=False)
axL.set_title('(b) Haggling', fontsize=8.8, loc='left', pad=3,
              fontweight='bold')
fig.text(0.635, 0.118, 'summed focal score (higher is better)',
         ha='center', fontsize=7.8)
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
    Line2D([], [], marker=METHOD_MARKERS['pact_family'], ls='none', color=METHOD_COLORS['pact_family'], ms=5.4,
        label=METHOD_LABELS['pact_family']),
    Line2D([], [], marker=METHOD_MARKERS['llm_psrl'], ls='none', markerfacecolor=METHOD_COLORS['llm_psrl'],
           markeredgecolor='white', markeredgewidth=0.5, ms=4.2,
        label=METHOD_LABELS['llm_psrl']),
    Line2D([], [], marker=METHOD_MARKERS['atom_tom1'], ls='none', markerfacecolor=METHOD_COLORS['atom_tom1'],
           markeredgecolor='white', markeredgewidth=0.5, ms=4.6,
        label=METHOD_LABELS['atom_tom1']),
    Line2D([], [], marker=METHOD_MARKERS['econ_bne'], ls='none', markerfacecolor=METHOD_COLORS['econ_bne'],
           markeredgecolor='white', markeredgewidth=0.5, ms=4.6,
        label=METHOD_LABELS['econ_bne']),
    Line2D([], [], color=ORACLE_COLOR, lw=1.1, ls=ORACLE_LINESTYLE,
        label=ORACLE_LABEL),
]
fig.legend(handles=handles, loc='lower center', ncol=3, frameon=False,
        fontsize=6.3, bbox_to_anchor=(0.575, -0.010),
           handletextpad=0.3, columnspacing=0.65, labelspacing=0.3)

fig.subplots_adjust(left=0.375, right=0.985, top=0.935, bottom=0.235)
output_dir = ROOT / 'arr_paper' / 'figs'
output_dir.mkdir(parents=True, exist_ok=True)
fig.savefig(output_dir / 'fig2_concordia_select_v15.pdf')
fig.savefig(output_dir / 'fig2_concordia_select_v15.png', dpi=300)
print('saved v15')
