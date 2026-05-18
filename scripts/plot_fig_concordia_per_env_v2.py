"""Per-environment Concordia margin plot.

Enumerates every Concordia config available locally:
- Pub Coordination (mechanistic, s>=30 only)
- Haggling single-item (s30)
- Haggling multi-item (s30)

Margin = proposed_focal - best_alternative_focal, where proposed = hpsmg_plus_joint_proxy
and "best alternative" excludes oracle_joint and any hpsmg_plus variant.

Pub Coordination uses focal_score_mean; Haggling uses focal_score_min_mean (the
discriminating worst-agent metric, since focal mean ties at the cake size).

Outputs:
- arr_paper/figs/fig_concordia_per_env_v2.{pdf,png}
"""
from __future__ import annotations
import glob, json, os
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

mpl.rcParams.update({"font.family": "serif", "font.size": 11, "pdf.fonttype": 42, "ps.fonttype": 42})

PROPOSED = "hpsmg_plus_joint_proxy"
ORACLE = "oracle_joint"


def best_alt(summary: dict, metric: str) -> tuple[str, float] | None:
    cand = [(m, float(r[metric])) for m, r in summary.items()
            if m not in {PROPOSED, ORACLE} and not m.startswith("hpsmg_plus")
            and metric in r and r[metric] is not None]
    return max(cand, key=lambda kv: kv[1]) if cand else None


def collect_rows():
    rows = []
    # Pub coordination -- mechanistic_joint runs with seeds >= 30 only
    for path in sorted(glob.glob("analysis/concordia_pub_coordination_compact_*mechanistic_joint_s*.json")):
        d = json.load(open(path, encoding="utf-8"))
        n = int(d.get("summary", [{}])[0].get("episodes", 0))
        if n < 30:
            continue
        summary = {r["method"]: r for r in d["summary"]}
        if PROPOSED not in summary:
            continue
        ba = best_alt(summary, "focal_score_mean")
        if ba is None:
            continue
        rows.append({
            "domain": "pub_coordination",
            "config": d.get("config", os.path.basename(path)),
            "episodes": n,
            "proposed": float(summary[PROPOSED]["focal_score_mean"]),
            "best_name": ba[0],
            "best_val": ba[1],
            "oracle": float(summary[ORACLE]["focal_score_mean"]) if ORACLE in summary else float("nan"),
        })
    # Haggling single + multi
    for pat in [
        "analysis/concordia_haggling_compact_*_s30.json",
        "analysis/concordia_haggling_multi_item_compact_*_s30.json",
    ]:
        for path in sorted(glob.glob(pat)):
            d = json.load(open(path, encoding="utf-8"))
            summary = {r["method"]: r for r in d["summary"]}
            if PROPOSED not in summary or "focal_score_min_mean" not in summary[PROPOSED]:
                continue
            ba = best_alt(summary, "focal_score_min_mean")
            if ba is None:
                continue
            domain = "haggling_multi" if "multi_item" in path else "haggling"
            rows.append({
                "domain": domain,
                "config": d.get("config", os.path.basename(path)),
                "episodes": int(summary[PROPOSED]["episodes"]),
                "proposed": float(summary[PROPOSED]["focal_score_min_mean"]),
                "best_name": ba[0],
                "best_val": ba[1],
                "oracle": float(summary[ORACLE]["focal_score_min_mean"]) if ORACLE in summary else float("nan"),
            })
    # dedupe: keep highest-episodes per (domain, config)
    best_per_key: dict[tuple[str, str], dict] = {}
    for r in rows:
        k = (r["domain"], r["config"])
        if k not in best_per_key or r["episodes"] > best_per_key[k]["episodes"]:
            best_per_key[k] = r
    return list(best_per_key.values())


def plot(rows, out_pdf):
    for r in rows:
        r["margin"] = r["proposed"] - r["best_val"]
        r["rel"] = r["margin"] / max(r["best_val"], 1e-6) * 100.0  # percent over best alt
    rows.sort(key=lambda r: r["margin"], reverse=True)

    DOMAIN_COLORS = {
        "pub_coordination": "#1f4e79",
        "haggling": "#c47a3b",
        "haggling_multi": "#5a8a3a",
    }
    DOMAIN_LABELS = {
        "pub_coordination": "Pub Coordination (focal mean)",
        "haggling": "Haggling single-item (focal min)",
        "haggling_multi": "Haggling multi-item (focal min)",
    }

    n = len(rows)
    fig, ax = plt.subplots(figsize=(7.6, max(3.5, 0.32 * n + 1.2)))
    y = np.arange(n)[::-1]
    margins = [r["margin"] for r in rows]
    cols = [DOMAIN_COLORS[r["domain"]] for r in rows]
    ax.barh(y, margins, color=cols, edgecolor="black", linewidth=0.5)
    for yi, r in zip(y, rows):
        sign = "+" if r["margin"] >= 0 else ""
        ax.text(r["margin"] + (0.02 if r["margin"] >= 0 else -0.02),
                yi, f"{sign}{r['margin']:.2f}",
                va="center", ha="left" if r["margin"] >= 0 else "right",
                fontsize=8.5, fontweight="bold")
    labels = [f"{r['config']}  (n={r['episodes']}, best alt={r['best_name'].replace('_mech','')})"
              for r in rows]
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.axvline(0, color="black", linewidth=0.8)

    pos = sum(1 for r in rows if r["margin"] > 1e-4)
    neg = sum(1 for r in rows if r["margin"] < -1e-4)
    tie = n - pos - neg
    ax.set_xlabel(
        f"H-PSMG$^{{+}}$ focal-score margin over best alternative baseline\n"
        f"({pos} win, {tie} tie, {neg} loss out of {n} configurations)"
    )
    ax.set_title("Concordia per-environment margins: H-PSMG$^{+}$ vs best alternative baseline",
                 fontsize=11)
    xmax = max(margins)
    xmin = min(margins)
    pad = max(0.15, (xmax - xmin) * 0.12)
    ax.set_xlim(xmin - pad, xmax + pad)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    handles = [plt.Rectangle((0, 0), 1, 1, color=DOMAIN_COLORS[d]) for d in DOMAIN_LABELS]
    ax.legend(handles, list(DOMAIN_LABELS.values()),
              loc="lower right", frameon=False, fontsize=8.5)
    fig.subplots_adjust(left=0.42, right=0.97, top=0.93, bottom=0.16)
    fig.savefig(out_pdf, bbox_inches="tight", pad_inches=0.10)
    fig.savefig(out_pdf.replace(".pdf", ".png"), dpi=200, bbox_inches="tight", pad_inches=0.10)
    plt.close(fig)
    return rows, pos, tie, neg


def main():
    rows = collect_rows()
    out_pdf = "arr_paper/figs/fig_concordia_per_env_v2.pdf"
    os.makedirs(os.path.dirname(out_pdf), exist_ok=True)
    rows, pos, tie, neg = plot(rows, out_pdf)
    print(f"[ok] {len(rows)} configs: {pos} win / {tie} tie / {neg} loss")
    for r in rows:
        print(f"  {r['domain']:18s} {r['config']:32s} margin={r['margin']:+.3f}  proposed={r['proposed']:.3f}  best={r['best_val']:.3f} ({r['best_name']})")


if __name__ == "__main__":
    main()
