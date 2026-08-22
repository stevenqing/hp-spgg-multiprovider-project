"""Render Figure 7 v9 with independent- and grouped-prior regret reductions."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np


mpl.rcParams.update({
    "font.family": "serif", "font.serif": ["DejaVu Serif"], "font.size": 7,
    "axes.linewidth": 0.7, "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "pdf.fonttype": 42, "ps.fonttype": 42,
})
NAVY_D="#1B3A6F"; NAVY_M="#3D6CB3"; NAVY_L="#7B9FCF"; AMBER="#D4A04A"
RED="#A52A2A"; GRAY="#8A8A8A"
ROOT = Path(__file__).resolve().parents[1]
T95 = {10: 2.262157163, 40: 2.02269092}
EXPECTED_GAPS = {
    (2, 0.0): 1.848999999999999,
    (2, 1.0): 0.11399999999999952,
    (3, 0.0): 1.3310000000000013,
    (3, 1.0): -1.5889999999999993,
    (4, 0.0): -1.3749999999999996,
    (4, 1.0): -0.37199999999999916,
}


def estimate_percent(gaps: np.ndarray, harp_regrets: np.ndarray) -> tuple[float, float, float]:
    denominator = float(np.mean(harp_regrets))
    if denominator <= 0.0:
        raise AssertionError(f"nonpositive mean HARP regret: {denominator}")
    mean = float(np.mean(gaps))
    sem = float(np.std(gaps, ddof=1) / np.sqrt(len(gaps)))
    half_width = T95[len(gaps)] * sem
    return tuple(100.0 * value / denominator for value in (mean, mean - half_width, mean + half_width))


def load_independent_cells() -> tuple[
    dict[tuple[int, float], tuple[float, float, float]],
    tuple[float, float, float],
]:
    path = ROOT / "analysis" / "maassim_rq2_rq3_all_data.md"
    lines = path.read_text(encoding="utf-8").splitlines()
    heading = lines.index("### Complete tracker/environment rows (all 240 rows)")
    header = [value.strip() for value in lines[heading + 2].strip("|").split("|")]
    rows = []
    for line in lines[heading + 4:]:
        if not line.startswith("|"):
            break
        values = [value.strip() for value in line.strip("|").split("|")]
        if len(values) == len(header):
            rows.append(dict(zip(header, values)))
    result = {}
    pooled_gaps_by_seed = {seed: [] for seed in range(10)}
    pooled_harp_regrets = []
    for key, expected_gap in EXPECTED_GAPS.items():
        n, strength = key
        selected = [
            row for row in rows
            if int(row["n"]) == n and float(row["lambda"]) == strength
        ]
        by_seed: dict[int, dict[str, dict[str, str]]] = {}
        for row in selected:
            by_seed.setdefault(int(row["seed"]), {})[row["tracker"]] = row
        if sorted(by_seed) != list(range(10)):
            raise AssertionError(f"independent cell {key} does not contain seeds 0--9")
        gaps = []
        harp_regrets = []
        for seed in range(10):
            factored = by_seed[seed]["factored"]
            joint = by_seed[seed]["joint"]
            gap = float(joint["utility"]) - float(factored["utility"])
            harp_regret = float(factored["oracle_utility"]) - float(factored["utility"])
            gaps.append(gap)
            harp_regrets.append(harp_regret)
            pooled_gaps_by_seed[seed].append(gap)
            pooled_harp_regrets.append(harp_regret)
        if abs(float(np.mean(gaps)) - expected_gap) > 1e-9:
            raise AssertionError(
                f"tab:maassim-parity mismatch at {key}: {np.mean(gaps)} != {expected_gap}"
            )
        result[key] = estimate_percent(np.asarray(gaps), np.asarray(harp_regrets))
    pooled_seed_gaps = np.asarray([
        np.mean(pooled_gaps_by_seed[seed]) for seed in range(10)
    ])
    pooled = estimate_percent(pooled_seed_gaps, np.asarray(pooled_harp_regrets))
    return result, pooled


def decoded_traces(payload: np.lib.npyio.NpzFile, name: str) -> list[dict[str, object]]:
    return [json.loads(str(value)) for value in payload[name].tolist()]


def assert_crn(payload: np.lib.npyio.NpzFile, left: str, right: str, label: str) -> None:
    for field in ("action_traces", "utility_traces", "regret_traces"):
        traces = decoded_traces(payload, field)
        mismatches = sum(
            left_value != right_value
            for trace in traces
            for left_value, right_value in zip(trace[left], trace[right])
        )
        if mismatches:
            raise AssertionError(f"{label} {field} has {mismatches} mismatches")


def load_grouped_cells() -> dict[int, tuple[float, float, float]]:
    root = (
        ROOT / "analysis" / "e_h_maassim_grouped_prior"
        / "k20_softmax_crn_confirm_seed20_59"
    )
    result = {}
    for group_size in (2, 4):
        rho0 = np.load(root / f"e_h_rho0p0_g{group_size}_n8_m2_s40.npz", allow_pickle=False)
        rho1 = np.load(root / f"e_h_rho1p0_g{group_size}_n8_m2_s40.npz", allow_pickle=False)
        assert_crn(rho0, "joint", "harp", f"rho=0,g={group_size}")
        assert_crn(rho1, "joint", "harp_s", f"rho=1,g={group_size}")
        rows = {
            (int(seed), str(arm)): float(regret)
            for seed, arm, regret in zip(rho1["seeds"], rho1["arms"], rho1["cum_regret"])
        }
        seeds = sorted({seed for seed, _ in rows})
        if seeds != list(range(20, 60)):
            raise AssertionError(f"grouped cell g={group_size} does not contain seeds 20--59")
        gaps = np.asarray([rows[(seed, "harp")] - rows[(seed, "joint")] for seed in seeds])
        harp_regrets = np.asarray([rows[(seed, "harp")] for seed in seeds])
        result[group_size] = estimate_percent(gaps, harp_regrets)
    return result


independent, independent_pooled = load_independent_cells()
grouped = load_grouped_cells()
fig, axes = plt.subplots(2, 2, figsize=(3.4, 2.85))
(a, b), (c, d) = axes
fig.subplots_adjust(wspace=0.56, hspace=0.68, left=0.135, right=0.985, top=0.94, bottom=0.115)

# ---------- (a) RQ2 relative regret reduction ----------
forest = [independent_pooled, grouped[2], grouped[4]]
y_positions = np.asarray([2.0, 1.0, 0.0])
means = np.asarray([value[0] for value in forest])
low = np.asarray([value[1] for value in forest])
high = np.asarray([value[2] for value in forest])
xerr = np.vstack((means - low, high - means))
a.axhspan(-0.45, 1.45, color="#EEF2F8", zorder=0)
a.axvline(0, color=GRAY, lw=0.7, ls="--", zorder=1)
a.errorbar(means, y_positions, xerr=xerr, fmt="none", color=NAVY_D,
        lw=1.0, capsize=2.0, capthick=1.0, zorder=2)
a.plot(means, y_positions, linestyle="none", marker="s", ms=6.0,
    mfc="white", mec=NAVY_L, mew=1.6, zorder=3)
a.plot(means, y_positions, linestyle="none", marker="o", ms=2.4,
    mfc=NAVY_D, mec=NAVY_D, mew=0.0, zorder=4)
a.set_yticks(y_positions)
a.set_yticklabels(["indep.", r"$g{=}2$", r"$g{=}4$"], fontsize=5.4)
a.set_xticks([-40, -20, 0, 20])
a.set_xlim(-45, 32)
a.set_ylim(-0.55, 3.35)
a.set_xlabel("regret reduction (%)", fontsize=5.8, labelpad=1)
a.tick_params(axis="x", labelsize=5.4, pad=1)
a.tick_params(axis="y", labelsize=5.4, pad=1)
a.text(-42.0, 0.50, "grouped prior", fontsize=4.8, color=GRAY,
    ha="left", va="center")
a.plot([-31.0], [2.78], linestyle="none", marker="s", ms=6.0,
    mfc="white", mec=NAVY_L, mew=1.6, clip_on=False, zorder=3)
a.plot([-31.0], [2.78], linestyle="none", marker="o", ms=2.4,
    mfc=NAVY_D, mec=NAVY_D, mew=0.0, clip_on=False, zorder=4)
a.text(-27.5, 2.78, r"joint $=$ HARP$^{+}$", fontsize=5.0,
    ha="left", va="center")
a.set_title("(a) RQ2: value of joint prior", fontsize=7, pad=2)

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
d.set_title("(d) RQ3: update signal", fontsize=7)

output = ROOT / "arr_paper" / "figs" / "fig_maassim_rq23_v10.pdf"
fig.savefig(output)
print(json.dumps({
    "status": "ok",
    "output": str(output.relative_to(ROOT)),
    "independent_pooled_percent": independent_pooled,
    "independent_percent": {f"n{n}_lambda{strength:g}": values for (n, strength), values in independent.items()},
    "grouped_percent": {f"g{group_size}": values for group_size, values in grouped.items()},
}, indent=2))
