"""Plot E-1.3+ lower-bound sweep: regret scaling with n, K under correlated priors.

Reads analysis/e1_3_lower_bound/sweep_summary.json and produces two panels:
  (left)  log-log regret vs K for PACT and Joint-PSRL under shared_type prior,
          one line per n, with reference slope sqrt(K).
  (right) regret-vs-n at fixed K=100 under shared_type prior, with reference
          curve C * sqrt(|Theta|^{n-1}) showing the predicted lower-bound
          scaling sqrt(m^{n-1} K) / sqrt(m K) = sqrt(m^{n-1}).

Output: arr_paper/figs/fig_e1_3_lower_bound.{png,pdf}
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "analysis" / "e1_3_lower_bound" / "sweep_summary.json"
FIG_DIR = ROOT / "arr_paper" / "figs"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# default analytic abstraction: |Theta| = 4 (low/med/high/spite)
M = 4

ALGO_COLORS = {
    "hpsmg_plus":  "#1f77b4",
    "hpsmg":       "#1f77b4",
    "joint_psrl":  "#d62728",
    "map_greedy":  "#2ca02c",
}
ALGO_LABEL = {
    "hpsmg_plus":  "PACT+",
    "hpsmg":       "PACT",
    "joint_psrl":  "Joint-PSRL",
    "map_greedy":  "MAP-greedy",
}


def load_rows(backbone: str = "analytic") -> list[dict]:
    data = json.loads(SUMMARY.read_text())
    return [r for r in data["rows"] if r["backbone"] == backbone]


def pivot(rows, algo, prior, *, by="K", fixed_n=None, fixed_K=None):
    out = []
    for r in rows:
        if r["algorithm"] != algo or r["prior"] != prior:
            continue
        if fixed_n is not None and r["n"] != fixed_n:
            continue
        if fixed_K is not None and r["K"] != fixed_K:
            continue
        out.append((r[by], r["mean"], r["sem"]))
    out.sort()
    if not out:
        return np.array([]), np.array([]), np.array([])
    xs, ys, es = zip(*out)
    return np.array(xs, dtype=float), np.array(ys, dtype=float), np.array(es, dtype=float)


def plot(prior: str = "shared_type", backbone: str = "analytic") -> Path:
    rows = load_rows(backbone)
    if not rows:
        raise RuntimeError("no rows in sweep_summary.json")
    ns = sorted({r["n"] for r in rows})
    Ks = sorted({r["K"] for r in rows})

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))

    # --- LEFT: regret vs K, one line per n, for PACT and Joint-PSRL
    ax = axes[0]
    n_styles = {3: "-", 4: "--", 5: ":", 6: "-."}
    for n in ns:
        for algo in ("hpsmg", "joint_psrl"):
            xs, ys, es = pivot(rows, algo, prior, by="K", fixed_n=n)
            if xs.size == 0:
                continue
            ys = np.clip(ys, 1e-3, None)  # for log plotting
            ax.errorbar(xs, ys, yerr=es,
                        marker="o", linestyle=n_styles.get(n, "-"),
                        color=ALGO_COLORS[algo], alpha=0.85,
                        label=f"{ALGO_LABEL[algo]} (n={n})")
    # reference slopes
    Kref = np.array(Ks, dtype=float)
    sqrtK = 0.5 * np.sqrt(Kref)
    ax.plot(Kref, sqrtK, color="grey", linewidth=1.0, linestyle="-.",
            label=r"$\propto\sqrt{K}$ (PF rate)")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Episodes $K$")
    ax.set_ylabel("Final cumulative regret")
    ax.set_title(f"Regret vs $K$  ({prior}, {backbone})")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=7, loc="best", ncol=2)

    # --- RIGHT: regret vs n at largest K, plus theoretical sqrt(m^{n-1}) curve
    ax = axes[1]
    Kfix = max(Ks)
    for algo in ("hpsmg", "joint_psrl", "map_greedy"):
        xs, ys, es = pivot(rows, algo, prior, by="n", fixed_K=Kfix)
        if xs.size == 0:
            continue
        ys = np.clip(ys, 1e-3, None)
        ax.errorbar(xs, ys, yerr=es, marker="s",
                    color=ALGO_COLORS[algo],
                    label=ALGO_LABEL[algo])
    # theory curve: Joint-PSRL value at smallest n anchored, then * sqrt(m^{n-n0})
    js_xs, js_ys, _ = pivot(rows, "joint_psrl", prior, by="n", fixed_K=Kfix)
    if js_xs.size >= 1:
        n0 = js_xs[0]
        anchor = max(js_ys[0], 1e-3)
        theory = anchor * np.sqrt(M ** (js_xs - n0))
        ax.plot(js_xs, theory, color="black", linestyle="--", linewidth=1.0,
                label=fr"$\propto\sqrt{{m^{{n-{int(n0)}}}}}$  (no-PF lower bound)")
    ax.set_yscale("log")
    ax.set_xlabel("Number of partners $n$")
    ax.set_ylabel(f"Final regret (K={Kfix})")
    ax.set_title(f"Regret vs $n$  ({prior}, {backbone})")
    ax.set_xticks(sorted({int(x) for x in js_xs}) if js_xs.size else ns)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=7, loc="best")

    fig.suptitle(
        f"E-1.3+: Joint-PSRL vs PACT under {prior} prior  ({backbone} calibration)",
        fontsize=11,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    out_png = FIG_DIR / f"fig_e1_3_lower_bound_{prior}_{backbone}.png"
    out_pdf = FIG_DIR / f"fig_e1_3_lower_bound_{prior}_{backbone}.pdf"
    fig.savefig(out_png, dpi=150)
    fig.savefig(out_pdf)
    plt.close(fig)
    print(f"wrote {out_png}")
    print(f"wrote {out_pdf}")
    return out_png


def numerical_table(backbone: str = "analytic") -> str:
    """Build a small markdown table comparing observed vs predicted regret ratio
    (Joint-PSRL / PACT) as n grows.  Prediction: sqrt(|Theta|^{n-n0})."""
    rows = load_rows(backbone)
    if not rows:
        return ""
    out_lines = []
    for prior in ("shared_type", "dir_a0p1"):
        out_lines.append(f"\n### {prior} (backbone={backbone})\n")
        out_lines.append("| n | K | PACT | Joint-PSRL | observed ratio | predicted $\\sqrt{m^{n-3}}$ |")
        out_lines.append("|---|---|------|-----------|---------------|-----------------------------|")
        Ks = sorted({r["K"] for r in rows})
        ns = sorted({r["n"] for r in rows})
        for K in Ks:
            for n in ns:
                pact = next((r["mean"] for r in rows
                             if r["algorithm"] == "hpsmg" and r["prior"] == prior
                             and r["n"] == n and r["K"] == K), None)
                jp = next((r["mean"] for r in rows
                           if r["algorithm"] == "joint_psrl" and r["prior"] == prior
                           and r["n"] == n and r["K"] == K), None)
                if pact is None or jp is None:
                    continue
                ratio = jp / max(pact, 1e-6)
                pred = np.sqrt(M ** (n - 3))
                out_lines.append(f"| {n} | {K} | {pact:.3f} | {jp:.3f} | {ratio:.2f} | {pred:.2f} |")
    return "\n".join(out_lines)


def main() -> None:
    for prior in ("shared_type", "dir_a0p1"):
        plot(prior=prior, backbone="analytic")
    for backbone in ("deepseek", "llama_maverick", "kimi_k2", "gpt5_nano"):
        try:
            plot(prior="shared_type", backbone=backbone)
        except Exception as e:
            print(f"skip {backbone}: {e}")
    tables = []
    for bb in ("analytic", "deepseek", "llama_maverick", "kimi_k2", "gpt5_nano"):
        t = numerical_table(bb)
        if t:
            tables.append(t)
    if tables:
        out = ROOT / "analysis" / "e1_3_lower_bound" / "ratio_table.md"
        joined = "\n\n".join(tables)
        out.write_text(joined, encoding="utf-8")
        print(f"wrote {out}")
        print(joined)


if __name__ == "__main__":
    main()
