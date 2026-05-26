"""Generate fig10_concordia_main_v7 (grouped bars) for ARR paper.

Replaces v3. Key differences vs v3:
- Plots the dashed oracle as `oracle_focal` on both Pub Coordination and
    Haggling axes. Legacy Pub Coordination result files store this row under
    `oracle_joint`, but the recorded policy is `best_focal_mean`, so the visual
    label should be focal.
- Adds Random and A-ToM-2 (mech) baselines on both panels.

Source data (read from analysis/, preferring latest tagged runs):
- Pub Coordination: concordia_pub_coordination_compact_*mechanistic_joint*_v2.json
                    falls back to *mechanistic_joint_s*.json
- Haggling:         concordia_haggling_compact_*_s30_v3.json
                    concordia_haggling_multi_item_compact_*_s30_v3.json
                    (falls back to v2, then *_s30.json)

Output: figs/fig10_concordia_main_v7.{pdf,png} and arr_paper{,_overleaf}/figs/
"""
from __future__ import annotations

import glob
import json
import os
import shutil
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

mpl.rcParams.update({
    "font.family": "serif",
    "font.size": 14,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
FIGS = ROOT / "figs"
FIGS.mkdir(exist_ok=True)

# Methods to plot (in render order)
PUB_METHODS = ["random", "atom_tom1_mech", "atom_tom2_mech", "econ_bne_mech",
               "llm_psrl_verbal", "hpsmg_plus_joint_proxy", "oracle_focal"]
# Haggling: pair our joint-proxy variant (the headline method, same as on the
# Pub Coordination panel) with `oracle_focal`. oracle_focal is the *true*
# upper bound on focal_score_mean, and joint_proxy is <= oracle_focal on
# every Haggling config (strictly less on 5/9, tied at the joint-Pareto
# optimum on the rest). This gives the proper visual: ours sits inside the
# dashed oracle ring on most axes.
HAG_METHODS = ["random", "atom_tom1_mech", "atom_tom2_mech", "econ_bne_mech",
               "llm_psrl_verbal", "hpsmg_plus_joint_proxy", "oracle_focal"]

# Per-method style. Oracle is dashed; ours is bold blue with fill; others thin.
STYLE = {
    "random":               {"color": "#6a9a3a", "lw": 1.3, "ls": (0, (1, 1.5)), "label": "Random",          "alpha": 0.9, "fill": False},
    "atom_tom1_mech":       {"color": "#e39a2f", "lw": 1.2, "ls": "-",         "label": "A-ToM-1 (mech)",  "alpha": 0.92, "fill": False},
    "atom_tom2_mech":       {"color": "#a253a4", "lw": 1.2, "ls": "-",         "label": "A-ToM-2 (mech)",  "alpha": 0.92, "fill": False},
    "econ_bne_mech":        {"color": "#c34a36", "lw": 1.2, "ls": "-",         "label": "ECON-BNE (mech)", "alpha": 0.92, "fill": False},
    "llm_psrl_verbal":      {"color": "#2e7d32", "lw": 1.8, "ls": "-",         "label": "LLM-PSRL-verbal", "alpha": 0.95, "fill": False},
    "hpsmg_plus_joint_proxy": {"color": "#1f4e79", "lw": 2.6, "ls": "-",       "label": "PACT$^+$ (joint proxy, ours)", "alpha": 1.0, "fill": True},
    "hpsmg_plus_focal_proxy": {"color": "#1f4e79", "lw": 2.6, "ls": "-",       "label": "PACT$^+$ (focal proxy, ours)", "alpha": 1.0, "fill": True},
    "oracle_joint":         {"color": "#8b8b8b", "lw": 1.5, "ls": (0, (6, 3)), "label": "Oracle (joint)",  "alpha": 0.95, "fill": False},
    "oracle_focal":         {"color": "#2f2f2f", "lw": 1.9, "ls": (0, (2, 2)), "label": "Oracle (focal)",  "alpha": 0.98, "fill": False},
}

# -----------------------------------------------------------------------------
# Data collection
# -----------------------------------------------------------------------------

def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def best_run_for(pattern_v2: str, pattern_v1: str) -> dict[str, dict]:
    """Returns {config_label: summary_dict_by_method}. Prefers v2 files."""
    out: dict[str, dict] = {}
    seen: set[str] = set()
    for pat in (pattern_v2, pattern_v1):
        for path in sorted(glob.glob(pat)):
            d = load_json(path)
            cfg = d.get("config", os.path.basename(path))
            key = cfg
            if key in seen:
                continue
            summary = {r["method"]: r for r in d["summary"]}
            n = max((int(r.get("episodes", 0)) for r in d["summary"]), default=0)
            out[key] = {"summary": summary, "episodes": n, "path": path}
            seen.add(key)
    return out


def collect_pub() -> list[tuple[str, dict]]:
    runs = best_run_for(
        str(ANALYSIS / "concordia_pub_coordination_compact_*mechanistic_joint_v2.json"),
        str(ANALYSIS / "concordia_pub_coordination_compact_*mechanistic_joint_s*.json"),
    )
    # Build axis labels in a stable order: capetown s100, capetown s30, edinburgh*, london*, london_mini
    order = [
        ("capetown_s100", "capetown\n(s=100)"),
        ("capetown_s30",  "capetown\n(s=30)"),
        ("edinburgh_s30", "edinburgh\n(s=30)"),
        ("edinburgh_closures_s30", "edinburgh\nclosures"),
        ("edinburgh_tough_friendship_s30", "edinburgh\ntough fr."),
        ("london_s30",    "london\n(s=30)"),
        ("london_closures_s30", "london\nclosures"),
        ("london_mini_s30", "london mini\n(s=30)"),
    ]
    items: list[tuple[str, dict]] = []
    for key, label in order:
        # match keys that contain the prefix (configs may vary in tag)
        match = None
        for k, v in runs.items():
            tag = v["path"].replace("\\", "/").split("/")[-1]
            if key in tag:
                match = v
                break
        if match is not None:
            summary = dict(match["summary"])
            maybe_add_verbal_summary(summary, "pub", key)
            items.append((label, summary))
    return items


def collect_hag() -> list[tuple[str, dict]]:
    runs_single = best_run_for(
        str(ANALYSIS / "concordia_haggling_compact_*_s30_v3.json"),
        str(ANALYSIS / "concordia_haggling_compact_*_s30_v2.json"),
    )
    if not runs_single:
        runs_single = best_run_for(
            str(ANALYSIS / "concordia_haggling_compact_*_s30.json"),
            str(ANALYSIS / "concordia_haggling_compact_*_s30.json"),
        )
    runs_multi = best_run_for(
        str(ANALYSIS / "concordia_haggling_multi_item_compact_*_s30_v3.json"),
        str(ANALYSIS / "concordia_haggling_multi_item_compact_*_s30_v2.json"),
    )
    if not runs_multi:
        runs_multi = best_run_for(
            str(ANALYSIS / "concordia_haggling_multi_item_compact_*_s30.json"),
            str(ANALYSIS / "concordia_haggling_multi_item_compact_*_s30.json"),
        )
    order_single = [
        ("fruitville", "fruitville\n(single)"),
        ("fruitville_gullible", "fruitville\ngullible\n(single)"),
        ("vegbrooke", "vegbrooke\n(single)"),
        ("vegbrooke_stubborn", "vegbrooke\nstubborn"),
        ("vegbrooke_strange_game", "vegbrooke\nstrange"),
    ]
    order_multi = [
        ("fruitville_multi", "fruitville\nmulti"),
        ("fruitville_gullible", "fruitville\ngullible (multi)"),
        ("vegbrooke", "vegbrooke\n(multi)"),
        ("cumulative_score", "cumulative\nscore (multi)"),
    ]
    items: list[tuple[str, dict]] = []
    for key, label in order_single:
        if key in runs_single:
            summary = dict(runs_single[key]["summary"])
            maybe_add_verbal_summary(summary, "haggling", key)
            items.append((label, summary))
    for key, label in order_multi:
        if key in runs_multi:
            summary = dict(runs_multi[key]["summary"])
            maybe_add_verbal_summary(summary, "haggling_multi_item", key)
            items.append((label, summary))
    return items


def maybe_add_verbal_summary(summary: dict, domain: str, config_key: str) -> None:
    pattern = ANALYSIS / "llm_psrl_verbal" / f"concordia_full_{domain}_{config_key}_*_llmpsrl.json"
    values = []
    for path in sorted(glob.glob(str(pattern))):
        data = load_json(path)
        for row in data.get("summary", []):
            if row.get("method") == "llm_psrl_verbal" and row.get("focal_score_mean") is not None:
                values.append(float(row["focal_score_mean"]))
    if values:
        summary["llm_psrl_verbal"] = {
            "method": "llm_psrl_verbal",
            "episodes": len(values),
            "focal_score_mean": float(np.mean(values)),
        }


# -----------------------------------------------------------------------------
# Plot
# -----------------------------------------------------------------------------

def per_axis_norm(values: list[float]) -> list[float]:
    """Min-max normalise to [0, 1] across non-NaN entries."""
    vals = [v for v in values if v is not None and not np.isnan(v)]
    if not vals:
        return [0.0] * len(values)
    lo, hi = min(vals), max(vals)
    if hi <= lo:  # all methods tied on this axis -> draw everyone on outer ring
        return [1.0 if (v is not None and not np.isnan(v)) else 0.0 for v in values]
    span = hi - lo
    return [((v - lo) / span) if (v is not None and not np.isnan(v)) else 0.0 for v in values]


def gather_metric(axes_data: list[tuple[str, dict]], methods: list[str], metric: str) -> tuple[list[str], np.ndarray]:
    """Returns axis labels and a (num_methods, num_axes) matrix of normalised values."""
    labels = [lbl for lbl, _ in axes_data]
    raw = np.full((len(methods), len(axes_data)), np.nan)
    for j, (_, summ) in enumerate(axes_data):
        for i, m in enumerate(methods):
            row = summ.get(m)
            if row is None and m == "oracle_focal":
                # Pub Coordination legacy files use the method name
                # `oracle_joint`, but the policy is `best_focal_mean`.
                row = summ.get("oracle_joint")
            if row is None:
                continue
            v = row.get(metric)
            if v is None:
                continue
            raw[i, j] = float(v)
    # Normalise per axis (column)
    norm = np.zeros_like(raw)
    for j in range(raw.shape[1]):
        col = raw[:, j].tolist()
        norm[:, j] = per_axis_norm(col)
    return labels, norm


def bar_panel(ax, labels, methods, norm, title, tick_fs=10):
    x = np.arange(len(labels))
    bar_methods = [method for method in methods if method != "oracle_focal"]
    width = min(0.12, 0.82 / max(1, len(bar_methods)))
    offsets = (np.arange(len(bar_methods)) - (len(bar_methods) - 1) / 2) * width
    for bar_index, method in enumerate(bar_methods):
        i = methods.index(method)
        st = STYLE[method]
        edgecolor = "#1f1f1f" if method == "hpsmg_plus_joint_proxy" else "white"
        linewidth = 0.8 if method == "hpsmg_plus_joint_proxy" else 0.35
        ax.bar(
            x + offsets[bar_index],
            norm[i],
            width=width,
            color=st["color"],
            alpha=0.92,
            edgecolor=edgecolor,
            linewidth=linewidth,
            label=st["label"],
            zorder=3 if method == "hpsmg_plus_joint_proxy" else 2,
        )
    oracle_style = STYLE["oracle_focal"]
    ax.axhline(
        1.0,
        color=oracle_style["color"],
        linewidth=2.0,
        linestyle=oracle_style["ls"],
        alpha=oracle_style["alpha"],
        label=oracle_style["label"],
        zorder=4,
    )
    ax.set_title(title, fontsize=16, pad=10, fontweight="semibold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=tick_fs, rotation=35, ha="right")
    ax.set_ylim(0, 1.08)
    ax.set_yticks([0.0, 0.25, 0.5, 0.75, 1.0])
    ax.set_ylabel("Per-config normalized focal score", fontsize=11)
    ax.grid(axis="y", color="#d6d6d6", linestyle=":", linewidth=0.8, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def main():
    pub = collect_pub()
    hag = collect_hag()
    if not pub or not hag:
        raise SystemExit(f"missing data: pub={len(pub)} hag={len(hag)}")

    pub_labels, pub_norm = gather_metric(pub, PUB_METHODS, "focal_score_mean")
    # Haggling: use focal payoff with `oracle_focal` as the true upper bound
    # of that metric. This recovers a visible gradient (random < atom_tom1 <
    # joint-coalition baselines < focal-greedy oracle), mirroring the Pub
    # Coordination panel.
    hag_labels, hag_norm = gather_metric(hag, HAG_METHODS, "focal_score_mean")

    fig, axes = plt.subplots(1, 2, figsize=(15.4, 6.4))
    bar_panel(axes[0], pub_labels, PUB_METHODS, pub_norm, "Pub Coordination", tick_fs=9.4)
    bar_panel(axes[1], hag_labels, HAG_METHODS, hag_norm, "Haggling", tick_fs=9.2)

    # Combined legend
    handles_pub, _ = axes[0].get_legend_handles_labels()
    handles_hag, _ = axes[1].get_legend_handles_labels()
    # Deduplicate by label
    seen = set()
    legend_handles = []
    legend_labels = []
    for h in handles_pub + handles_hag:
        lbl = h.get_label()
        if lbl in seen:
            continue
        seen.add(lbl)
        legend_handles.append(h)
        legend_labels.append(lbl)
    fig.legend(legend_handles, legend_labels, loc="lower center", ncol=4,
               bbox_to_anchor=(0.5, -0.02), fontsize=11.4, frameon=False,
               columnspacing=1.5, handletextpad=0.7)

    fig.tight_layout(rect=(0, 0.12, 1, 1))
    out_pdf = FIGS / "fig10_concordia_main_v7.pdf"
    out_png = FIGS / "fig10_concordia_main_v7.png"
    fig.savefig(out_pdf, bbox_inches="tight")
    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    for target_dir in (ROOT / "arr_paper" / "figs", ROOT / "arr_paper_overleaf" / "figs"):
        if target_dir.exists():
            shutil.copy2(out_pdf, target_dir / out_pdf.name)
            shutil.copy2(out_png, target_dir / out_png.name)
    print(f"wrote {out_pdf}")
    print(f"wrote {out_png}")


if __name__ == "__main__":
    main()
