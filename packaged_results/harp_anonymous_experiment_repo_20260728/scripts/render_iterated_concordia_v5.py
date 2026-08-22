"""Iterated Concordia v3: cross-geometry external-validity panels.
(a) per-configuration paired parity forest (HARP - Joint-PSRL at K=20, t95).
(b) update value (PSRL-NoType - HARP+ at K=20, paired) against each
configuration's selection-time persona decision value."""
from pathlib import Path
import re
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

mpl.rcParams.update({
    "font.family": "serif", "font.serif": ["DejaVu Serif"], "font.size": 7,
    "axes.linewidth": 0.7, "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "pdf.fonttype": 42, "ps.fonttype": 42,
})
NAVY_D="#1B3A6F"; NAVY_M="#3D6CB3"; AMBER="#D4A04A"; GRAY="#8A8A8A"
T95 = 2.7764
ROOT = Path(__file__).resolve().parents[1]

txt = (ROOT / "analysis" / "e_b_iterated_concordia" / "e_b_iterated_concordia_rq2_rq3_all_data.md").read_text(
    encoding="utf-8", errors="replace"
)
rows = re.findall(r"^\|\s*([a-z_0-9]+)\s*\|\s*([\w/ _-]+)\s*\|\s*(10\d\d)\s*\|\s*(\d+)\s*\|\s*(-?\d+\.?\d*(?:e-?\d+)?)\s*\|\s*$", txt, re.M)
D = {}
for m, cfg, s, k, r in rows:
    D[(m, cfg.strip(), int(s), int(k))] = float(r)

cfg_meta = [  # (config key, short label, family, decision value)
    ("pub/london",                          "london",        "pub", 0.00845),
    ("pub/london_mini",                     "london-mini",   "pub", 0.00736),
    ("haggling/fruitville",                 "fruitville",    "hag", 0.0589),
    ("haggling/vegbrooke",                  "vegbrooke",     "hag", 0.04937),
    ("haggling_multi_item/fruitville_multi","fruitville-m",  "hag", 0.05266),
    ("haggling_multi_item/vegbrooke",       "vegbrooke-m",   "hag", 0.053),
]
seeds = range(1000, 1005)

def paired(c, m1, m2):
    v = np.array([D[(m1,c,s,20)] - D[(m2,c,s,20)] for s in seeds])
    return v.mean(), v.std(ddof=1)/np.sqrt(5)

parity = {c: paired(c, "pact", "joint_psrl_uniform") for c,_,_,_ in cfg_meta}
update = {c: paired(c, "psrl_notype", "pact_plus") for c,_,_,_ in cfg_meta}
pooled = np.array([np.mean([D[("pact",c,s,20)] - D[("joint_psrl_uniform",c,s,20)]
                            for c,_,_,_ in cfg_meta]) for s in seeds])
pm, ps = pooled.mean(), pooled.std(ddof=1)/np.sqrt(5)
assert abs(pm - (-0.016807856201604826)) < 1e-9
for c,_,_,_ in cfg_meta:  # every geometry's t95 must cover zero
    m, se = parity[c]
    assert (m - T95*se) < 0 < (m + T95*se), c
print("integrity ok; pooled %.4f±%.4f" % (pm, ps))

fig, (a, b) = plt.subplots(1, 2, figsize=(3.4, 1.44))
fig.subplots_adjust(wspace=0.62, left=0.215, right=0.985, top=0.86, bottom=0.285)

# ---- (a) forest of per-geometry paired parity + pooled
order = cfg_meta + [None]  # None = pooled row
ylabels = []
for i, item in enumerate(order):
    y = len(order) - 1 - i
    if item is None:
        a.errorbar([pm],[y], xerr=[[T95*ps],[T95*ps]], fmt="D", ms=3.2, lw=0.9,
                   capsize=1.6, color=NAVY_D)
        ylabels.append("pooled")
    else:
        c, lab, fam, _ = item
        m, se = parity[c]
        col = AMBER if fam == "pub" else NAVY_M
        a.errorbar([m],[y], xerr=[[T95*se],[T95*se]], fmt="o", ms=2.8, lw=0.9,
                   capsize=1.6, color=col)
        ylabels.append(lab)
a.axvline(0, color="black", lw=0.7)
a.set_yticks(range(len(order))); a.set_yticklabels(ylabels[::-1], fontsize=5.4)
a.set_ylim(-0.6, len(order)-0.4)
a.set_xlim(-0.55, 0.55); a.set_xticks([-0.4, 0, 0.4])
a.set_xlabel("HARP $-$ Joint-PSRL regret", labelpad=1)
a.set_title("(a) RQ2: parity per geometry", fontsize=7)

# ---- (b) update value by configuration
b.axhline(0, color=GRAY, lw=0.7, ls="--")
bar_x = np.arange(len(cfg_meta))
bar_values = [update[c][0] for c,_,_,_ in cfg_meta]
bar_sems = [update[c][1] for c,_,_,_ in cfg_meta]
bar_colors = [AMBER if fam == "pub" else NAVY_M for _,_,fam,_ in cfg_meta]
b.bar(bar_x,bar_values,0.68,yerr=bar_sems,color=bar_colors,edgecolor="black",lw=0.5,
      capsize=1.7,error_kw=dict(lw=0.7),zorder=3)
b.axvline(1.5,color="0.82",lw=0.6,zorder=0)
b.set_xlim(-0.6,len(cfg_meta)-0.4); b.set_ylim(-0.45,2.6)
b.set_xticks(bar_x)
b.set_xticklabels(["London","London\nmini","Fruit.","Veg.","Fruit.\nmulti","Veg.\nmulti"],
                  rotation=42,ha="right",fontsize=4.7)
b.set_ylabel("update value (regret)", labelpad=1)
b.bar([],[],color=AMBER,edgecolor="black",lw=0.5,label="pub")
b.bar([],[],color=NAVY_M,edgecolor="black",lw=0.5,label="haggling")
b.legend(fontsize=5.2,loc="upper left",ncol=2,handletextpad=0.2,borderaxespad=0.1,
         columnspacing=0.6)
b.set_title("(b) RQ3: update value", fontsize=7)

fig.savefig(ROOT / "arr_paper" / "figs" / "fig_e_b_iterated_concordia_v5.pdf")
print("done")
