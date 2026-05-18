"""Per-family SOTOPIA-Hard margins.

Enumerates all 11 scenario families. For each family, computes H-PSMG+ mean
focal-score across all backbones vs the best alternative baseline (max over
A-ToM-1, ECON-BNE, llm_belief, llm_greedy), and plots a horizontal bar chart
sorted by margin. Wins are green, losses red, ties grey.

Output: arr_paper/figs/fig_sotopia_per_family_v1.{pdf,png}
"""
from __future__ import annotations
import json, glob, os
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

mpl.rcParams.update({"font.family": "serif", "font.size": 11, "pdf.fonttype": 42, "ps.fonttype": 42})

BASES = ["hpsmg_plus", "atom_tom1", "econ_bne", "llm_belief", "llm_greedy"]
BASELINE_LABEL = {
    "atom_tom1": "A-ToM-1",
    "econ_bne": "ECON-BNE",
    "llm_belief": "llm\\_belief",
    "llm_greedy": "llm\\_greedy",
}

# Families ordered by closeness to HT-MG-BC preconditions: multi-turn
# negotiation with hidden agent type (PF/TID approximately satisfied).
IN_SCOPE = {"revenge_plot", "craigslist_bargains", "donate_funds"}


def fam(code: str) -> str:
    parts = code.split("_")
    while parts and parts[-1].isdigit():
        parts.pop()
    return "_".join(parts) if parts else code


def load_buckets():
    buckets: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for p in sorted(glob.glob("analysis/sotopia_hard_official_*_sotopia_tuned_all70.json")):
        name = os.path.basename(p).replace("sotopia_hard_official_", "").replace("_sotopia_tuned_all70.json", "")
        bl = None
        for b in BASES:
            if name.endswith("_" + b):
                bl = b
                model = name[: -(len(b) + 1)]
                break
        if bl is None:
            continue
        d = json.load(open(p, encoding="utf-8"))
        for ep in d.get("episodes", []):
            code = ep.get("codename") or "?"
            ov = ep.get("overall") or {}
            vals = [v for v in ov.values() if isinstance(v, (int, float))]
            if not vals:
                continue
            buckets[(model, fam(code), bl)].append(sum(vals) / len(vals))
    return buckets


def compute_rows(buckets):
    models = sorted({m for (m, _, _) in buckets})
    families = sorted({f for (_, f, _) in buckets})
    rows = []
    for f in families:
        # per-baseline mean of per-model means
        per_method = {}
        episode_count = 0
        for b in BASES:
            scores = []
            for m in models:
                xs = buckets.get((m, f, b))
                if xs:
                    scores.append(sum(xs) / len(xs))
                    if b == "hpsmg_plus":
                        episode_count += len(xs)
            per_method[b] = sum(scores) / len(scores) if scores else None
        if per_method["hpsmg_plus"] is None:
            continue
        alts = [(b, v) for b, v in per_method.items() if b != "hpsmg_plus" and v is not None]
        if not alts:
            continue
        best_name, best_val = max(alts, key=lambda kv: kv[1])
        rows.append({
            "family": f,
            "episodes": episode_count,
            "hpsmg": per_method["hpsmg_plus"],
            "best_val": best_val,
            "best_name": best_name,
            "margin": per_method["hpsmg_plus"] - best_val,
        })
    rows.sort(key=lambda r: r["margin"], reverse=True)
    return rows


def plot(rows, out_pdf):
    n = len(rows)
    fig, ax = plt.subplots(figsize=(7.4, max(3.0, 0.34 * n + 1.2)))
    y = np.arange(n)[::-1]
    margins = [r["margin"] for r in rows]
    cols = []
    for r in rows:
        if r["margin"] > 0.005:
            cols.append("#3e8a4e")  # green = win
        elif r["margin"] < -0.005:
            cols.append("#b14848")  # red = loss
        else:
            cols.append("#9a9a9a")  # grey = tie
    edges = ["black" if r["family"] in IN_SCOPE else "none" for r in rows]
    widths = [1.4 if r["family"] in IN_SCOPE else 0.0 for r in rows]
    ax.barh(y, margins, color=cols, edgecolor=edges, linewidth=widths)
    for yi, r in zip(y, rows):
        sign = "+" if r["margin"] >= 0 else ""
        ax.text(r["margin"] + (0.012 if r["margin"] >= 0 else -0.012),
                yi, f"{sign}{r['margin']:.3f}",
                va="center", ha="left" if r["margin"] >= 0 else "right",
                fontsize=8.5, fontweight="bold")
    labels = []
    for r in rows:
        marker = "$\\star$ " if r["family"] in IN_SCOPE else "   "
        labels.append(f"{marker}{r['family'].replace('_',' ')}  (n={r['episodes']})")
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.axvline(0, color="black", linewidth=0.8)

    wins = sum(1 for r in rows if r["margin"] > 0.005)
    losses = sum(1 for r in rows if r["margin"] < -0.005)
    ties = n - wins - losses
    worst = min(margins)
    ax.set_xlabel(
        f"H-PSMG$^{{+}}$ focal-score margin over best alternative baseline\n"
        f"({wins} win / {ties} tie / {losses} loss of {n} families; max loss = {worst:+.2f})"
    )
    ax.set_title("SOTOPIA-Hard per-family margins ($\\star$ = HT-MG-BC-lite preconditions hold)",
                 fontsize=11)
    xmax = max(margins)
    xmin = min(margins)
    pad = max(0.05, (xmax - xmin) * 0.13)
    ax.set_xlim(xmin - pad, xmax + pad)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    handles = [
        plt.Rectangle((0, 0), 1, 1, color="#3e8a4e"),
        plt.Rectangle((0, 0), 1, 1, color="#9a9a9a"),
        plt.Rectangle((0, 0), 1, 1, color="#b14848"),
    ]
    ax.legend(handles, ["H-PSMG$^{+}$ wins", "tie", "H-PSMG$^{+}$ loses"],
              loc="lower right", frameon=False, fontsize=8.5)
    fig.subplots_adjust(left=0.34, right=0.97, top=0.92, bottom=0.18)
    fig.savefig(out_pdf, bbox_inches="tight", pad_inches=0.10)
    fig.savefig(out_pdf.replace(".pdf", ".png"), dpi=200, bbox_inches="tight", pad_inches=0.10)
    plt.close(fig)


def main():
    buckets = load_buckets()
    rows = compute_rows(buckets)
    out_pdf = "arr_paper/figs/fig_sotopia_per_family_v1.pdf"
    os.makedirs(os.path.dirname(out_pdf), exist_ok=True)
    plot(rows, out_pdf)
    for r in rows:
        scope = "in-scope" if r["family"] in IN_SCOPE else "out-of-scope"
        print(f"  {r['family']:25s} n={r['episodes']:4d}  H-PSMG+={r['hpsmg']:.3f}  "
              f"best_alt={r['best_val']:.3f} ({r['best_name']:<10s})  margin={r['margin']:+.3f}  [{scope}]")
    print(f"[ok] wrote {out_pdf}")


if __name__ == "__main__":
    main()
