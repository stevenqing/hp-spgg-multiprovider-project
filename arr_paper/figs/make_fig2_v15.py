#!/usr/bin/env python3
"""Figure 5: selected Concordia configurations as vertical grouped bars.

Panel (a) uses the legacy joint oracle reference; panel (b) uses the exact
focal oracle. The four displayed LLM systems and their colors match the shared
main-paper palette used in Figures 2 and 4(a).
"""
from pathlib import Path
import json
import sys

import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

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

DATA_PATH = ROOT / 'arr_paper' / 'data' / 'figure5_bar_data.json'
DATA = json.loads(DATA_PATH.read_text(encoding='utf-8'))['configurations']
PUB_KEYS = (
    'pub/london_mini_s30',
    'pub/capetown_s100',
    'pub/london_s30',
    'pub/edinburgh_closures_s30',
)
HAGGLING_KEYS = (
    'haggling/vegbrooke',
    'haggling/vegbrooke_stubborn',
    'haggling_multi_item/fruitville_gullible',
    'haggling/fruitville',
)
REQUESTED_PLOT_METHODS = ('pact_family', 'llm_psrl', 'atom_tom1', 'econ_bne', 'moa', 'puppeteer')
PLOT_METHODS = tuple(
    method for method in REQUESTED_PLOT_METHODS
    if all(method in cell['methods'] for cell in DATA.values())
)
BAR_WIDTH = 0.12
OFFSETS = [(index - (len(PLOT_METHODS) - 1) / 2) * BAR_WIDTH for index in range(len(PLOT_METHODS))]

fig = plt.figure(figsize=(3.45, 3.55))
outer = fig.add_gridspec(2, 1, height_ratios=[1.0, 1.65], hspace=0.50)
ax1 = fig.add_subplot(outer[0])
hag_grid = outer[1].subgridspec(3, 1, height_ratios=[0.42, 0.82, 1.0], hspace=0.0)
ax_high = fig.add_subplot(hag_grid[0])
ax_mid = fig.add_subplot(hag_grid[1], sharex=ax_high)
ax_low = fig.add_subplot(hag_grid[2], sharex=ax_high)


def draw_bars(axes, keys):
    x = list(range(len(keys)))
    for offset, method in zip(OFFSETS, PLOT_METHODS):
        positions = [group + offset for group in x]
        values = [DATA[key]['methods'][method]['mean'] for key in keys]
        errors = [DATA[key]['methods'][method]['sem'] for key in keys]
        for axis in axes:
            axis.bar(
                positions,
                values,
                yerr=errors,
                width=BAR_WIDTH,
                color=METHOD_COLORS[method],
                edgecolor='#0a243f' if method == 'pact_family' else 'white',
                linewidth=0.65 if method == 'pact_family' else 0.4,
                capsize=1.8,
                error_kw={'ecolor': '#30343a', 'elinewidth': 0.65, 'capthick': 0.65},
                zorder=3,
            )
    for group, key in enumerate(keys):
        oracle = DATA[key]['methods']['oracle']['mean']
        for axis in axes:
            axis.hlines(oracle, group - 0.38, group + 0.38, color=ORACLE_COLOR,
                        linewidth=1.0, linestyle=ORACLE_LINESTYLE, alpha=0.85,
                        zorder=2)
    return x


pub_x = draw_bars((ax1,), PUB_KEYS)
ax1.set_xticks(pub_x, ['London\nmini', 'Cape Town\n($s{=}100$)', 'London',
                       'Edinburgh\nclosures'])
ax1.set_ylim(0.50, 1.39)
ax1.set_yticks([0.6, 0.8, 1.0, 1.2, 1.3])
ax1.set_ylabel('Focal score')
ax1.set_title('(a) Pub Coordination', fontsize=8.8, loc='left', pad=3,
              fontweight='bold')

hag_x = draw_bars((ax_high, ax_mid, ax_low), HAGGLING_KEYS)
ax_low.set_xticks(hag_x, ['Vegbrooke\n(single)', 'Vegbrooke\nstubborn',
                          'Fruitville gullible\n(multi)', 'Fruitville\n(single)'])
ax_low.set_ylim(-0.8, 2.35)
ax_mid.set_ylim(5.25, 8.25)
ax_high.set_ylim(8.8, 15.5)
ax_low.axhline(0, color='#777777', linewidth=0.6, zorder=2)
ax_high.tick_params(axis='x', bottom=False, labelbottom=False)
ax_mid.tick_params(axis='x', bottom=False, labelbottom=False)
ax_high.set_title('(b) Haggling', fontsize=8.8, loc='left', pad=3,
                  fontweight='bold')
fig.text(0.025, 0.38, 'Summed focal score', rotation=90, va='center',
         ha='center', fontsize=8.0)

d = 0.7
break_style = dict(marker=[(-1, -d), (1, d)], markersize=5, linestyle='none',
                   color='#444444', mec='#444444', mew=0.8, clip_on=False)
ax1.plot([0, 1], [0, 0], transform=ax1.transAxes, **break_style)
ax_high.plot([0, 1], [0, 0], transform=ax_high.transAxes, **break_style)
ax_mid.plot([0, 1], [1, 1], transform=ax_mid.transAxes, **break_style)
ax_mid.plot([0, 1], [0, 0], transform=ax_mid.transAxes, **break_style)
ax_low.plot([0, 1], [1, 1], transform=ax_low.transAxes, **break_style)
ax_high.spines['bottom'].set_visible(False)
ax_mid.spines['top'].set_visible(False)
ax_mid.spines['bottom'].set_visible(False)
ax_low.spines['top'].set_visible(False)

for axis in (ax1, ax_high, ax_mid, ax_low):
    axis.spines['left'].set_color('#444444')
    axis.spines['bottom'].set_color('#444444')
    axis.grid(axis='y', color='#DDDDDD', lw=0.5, linestyle=':', zorder=0)
    axis.set_axisbelow(True)
    axis.tick_params(axis='both', labelsize=6.3, pad=1.5)
    axis.set_xlim(-0.52, 3.52)

handles = [
    Patch(facecolor=METHOD_COLORS[method], edgecolor='none', label=METHOD_LABELS[method])
    for method in PLOT_METHODS
]
handles.append(Line2D([], [], color=ORACLE_COLOR, lw=1.05,
                      ls=ORACLE_LINESTYLE, label=ORACLE_LABEL))
fig.legend(handles=handles, loc='lower center', ncol=4, frameon=False,
           fontsize=5.8, bbox_to_anchor=(0.53, 0.005),
           handlelength=1.4, handletextpad=0.35, columnspacing=0.7,
           labelspacing=0.3)

fig.subplots_adjust(left=0.145, right=0.99, top=0.94, bottom=0.19)
output_dir = ROOT / 'arr_paper' / 'figs'
output_dir.mkdir(parents=True, exist_ok=True)
fig.savefig(output_dir / 'fig2_concordia_select_v15.pdf')
fig.savefig(output_dir / 'fig2_concordia_select_v15.png', dpi=300)
print('saved v15')
