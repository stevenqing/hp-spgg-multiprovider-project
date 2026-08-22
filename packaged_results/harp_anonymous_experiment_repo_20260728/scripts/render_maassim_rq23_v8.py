"""Single-column 2x2 MaaSSim RQ2/RQ3 figure. Top row RQ2, bottom row RQ3.
Panel (a) has a ready slot for lambda=0.5 once E-E is extended."""
from pathlib import Path
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

mpl.rcParams.update({
    "font.family": "serif", "font.serif": ["DejaVu Serif"], "font.size": 7,
    "axes.linewidth": 0.7, "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "pdf.fonttype": 42, "ps.fonttype": 42,
})
NAVY_D="#1B3A6F"; NAVY_M="#3D6CB3"; NAVY_L="#7B9FCF"; AMBER="#D4A04A"
RED="#A52A2A"; GRAY="#8A8A8A"
ROOT = Path(__file__).resolve().parents[1]

fig, axes = plt.subplots(2, 2, figsize=(3.4, 2.85))
(a, b), (c, d) = axes
fig.subplots_adjust(wspace=0.56, hspace=0.68, left=0.135, right=0.985, top=0.94, bottom=0.115)

# ---------- (a) RQ2 paired utility gap ----------
cells = {(2,0.0):( 1.849, 0.192,3.506),(2,1.0):( 0.114,-2.870,3.098),
         (3,0.0):( 1.331,-0.708,3.370),(3,1.0):(-1.589,-5.126,1.948),
         (4,0.0):(-1.375,-3.901,1.151),(4,1.0):(-0.372,-4.081,3.337)}
# TODO: extend E-E and add lambda=0.5 cells here, e.g. (2,0.5):(mean,lo,hi)
lam_style = {0.0:("o","white",-0.18,r"$\lambda{=}0$"),
             0.5:("s","#9FB3D1",0.0,r"$\lambda{=}0.5$"),
             1.0:("o",NAVY_D,0.18,r"$\lambda{=}1$")}
a.axhline(0, color="black", lw=0.7)
for lam,(mk,fc,off,lab) in lam_style.items():
    pts=[(n,cells[(n,lam)]) for n in (2,3,4) if (n,lam) in cells]
    if not pts: continue
    xs=[n+off for n,_ in pts]; ys=[v[0] for _,v in pts]
    lo=[v[0]-v[1] for _,v in pts]; hi=[v[2]-v[0] for _,v in pts]
    a.errorbar(xs,ys,yerr=[lo,hi],fmt=mk,ms=3.2,lw=0.9,capsize=1.8,
               color=NAVY_D,mfc=fc,mew=0.8,label=lab)
a.set_xticks([2,3,4]); a.set_xlim(1.5,4.5); a.set_ylim(-5.8,7.2)
a.set_xlabel("fleet size $n$", labelpad=1)
a.set_ylabel("joint $-$ factored utility", labelpad=1)
a.legend(fontsize=5.6, loc="upper center", ncol=3, handletextpad=0.15,
         borderaxespad=0.05, columnspacing=0.7, handlelength=1.0)
a.set_title("(a) RQ2: paired gap (95% CI)", fontsize=7)

# ---------- (b) RQ2 update cost ----------
ns_f=[2,3,4,6,8]; t_f=[7.55,7.39,7.76,6.89,7.11]
ns_j=[2,3,4];     t_j=[10.22,28.70,496.95]
b.axvspan(4.6, 8.7, color="0.93", zorder=0)
b.plot(ns_f,t_f,"o-",ms=2.8,lw=1.0,color=NAVY_D,label="factored $16n$")
b.plot(ns_j,t_j,"s-",ms=2.8,lw=1.0,color=NAVY_L,label="joint $16^{n}$")
b.set_yscale("log"); b.set_xticks(ns_f); b.set_xlim(1.5,8.7); b.set_ylim(3.5,2000)
b.set_ylabel(r"update time ($\mu$s/event)", labelpad=1)
b.set_xlabel("fleet size $n$", labelpad=1)
b.legend(fontsize=5.6, loc="upper right", bbox_to_anchor=(1.0, 1.0),
         handletextpad=0.2, borderaxespad=0.0, labelspacing=0.25, handlelength=1.0)
b.set_title("(b) RQ2: update cost", fontsize=7)

# ---------- (c) RQ3 belief accuracy vs utility ----------
c.axhline(38.92, color=RED, lw=0.8, ls="--")
c.text(0.455, 41.0, "oracle (true personas)", fontsize=5.6, color=RED)
pts = [  # label, policy-side rule acc, acc SEM, utility, utility SEM, color
    ("Prior",    0.500, 0.000, 11.11, 10.74, NAVY_L),
    ("Shuffled", 0.521, 0.018,  6.87,  9.55, AMBER),
    ("HARP",     0.720, 0.023, 27.61, 11.65, NAVY_D),
]
for lab,x,xs_,y,ys_,col in pts:
    c.errorbar([x],[y],xerr=[xs_],yerr=[ys_],fmt="o",ms=3.8,lw=0.8,capsize=1.6,
               color=col, alpha=0.9, elinewidth=0.7)
c.errorbar([1.0],[38.92],yerr=[11.17],fmt="o",ms=3.8,lw=0.8,capsize=1.6,
           color=RED, alpha=0.9, elinewidth=0.7)
c.annotate("Prior",(0.500,11.11),xytext=(3,-10),textcoords="offset points",fontsize=5.8,color=NAVY_L)
c.annotate("Shuffled",(0.521,6.87),xytext=(4,-11),textcoords="offset points",fontsize=5.8,color=AMBER)
c.annotate("HARP",(0.720,27.61),xytext=(-4,6),textcoords="offset points",ha="right",fontsize=5.8,color=NAVY_D)
c.set_xlim(0.44,1.06); c.set_ylim(-8,55)
c.set_xlabel("policy-side belief accuracy", labelpad=1)
c.set_ylabel("realized utility", labelpad=1)
c.set_title("(c) RQ3: belief acc. vs utility", fontsize=7)

# ---------- (d) RQ3 event-type attribution ----------
x = np.array([0, 1]); w = 0.32
rej = [0.0379, 0.0310]; rej_s = [0.0036, None]
acc_ = [0.0221, 0.0200]; acc_s = [0.0026, None]
d.bar(x - w/2, rej, w, color=NAVY_D, edgecolor="black", lw=0.6, label="reject",
      yerr=[s if s else 0 for s in rej_s], capsize=1.8, error_kw=dict(lw=0.7))
d.bar(x + w/2, acc_, w, color=NAVY_L, edgecolor="black", lw=0.6, label="accept",
      yerr=[s if s else 0 for s in acc_s], capsize=1.8, error_kw=dict(lw=0.7))
d.set_xticks(x); d.set_xticklabels(["rule\naccuracy", "exact-type\nmass"], fontsize=6)
d.set_ylim(0, 0.050)
d.set_ylabel("posterior gain / event", labelpad=1)
d.legend(fontsize=6, loc="upper center", ncol=2, handletextpad=0.25,
         borderaxespad=0.1, columnspacing=0.9)
d.set_title("(d) RQ3: which events update", fontsize=7)

fig.savefig(ROOT / "arr_paper" / "figs" / "fig_maassim_rq23_v8.pdf")
print("done")
