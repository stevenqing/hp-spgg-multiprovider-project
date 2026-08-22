"""Summarize MaaSSim controlled synthetic baseline runs."""

from __future__ import annotations

import csv
import json
import math
import argparse
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis" / "courier_dispatch_maassim"
FIGS = [ROOT / "figs", ROOT / "arr_paper" / "figs"]
POLICIES = ["nearest", "random", "pact", "pact_plus", "oracle", "pact_kpi", "pact_plus_kpi", "oracle_kpi"]
LABELS = {
    "nearest": "Nearest",
    "random": "Random",
    "pact": "PACT",
    "pact_plus": "PACT+",
    "oracle": "Oracle",
    "pact_kpi": "PACT",
    "pact_plus_kpi": "PACT+",
    "oracle_kpi": "Oracle",
}
COLORS = {
    "nearest": "#8c8c8c",
    "random": "#555555",
    "pact": "#3d6cb3",
    "pact_plus": "#1b3a6f",
    "oracle": "#c7773d",
    "pact_kpi": "#3d6cb3",
    "pact_plus_kpi": "#1b3a6f",
    "oracle_kpi": "#c7773d",
}
METRICS = [
    ("mean_final_ptrue", "P(true)", "posterior_summary"),
    ("mean_final_rule_acc", "Rule acc", "posterior_summary"),
    ("pax_wait_mean", "Mean wait", "maassim_summary"),
    ("veh_nrides_sum", "Rides", "maassim_summary"),
    ("veh_nrejects_sum", "Rejects", "maassim_summary"),
]


def mean(values: list[float]) -> float:
    return float(sum(values) / len(values)) if values else float("nan")


def sem(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = mean(values)
    return float(math.sqrt(sum((value - avg) ** 2 for value in values) / (len(values) - 1)) / math.sqrt(len(values)))


def load_rows(prefix: str) -> list[dict[str, object]]:
    rows = []
    for policy in POLICIES:
        for path in sorted(ANALYSIS.glob(f"{policy}_{prefix}_s*_summary.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            rows.append(payload)
    return rows


def value(payload: dict[str, object], metric: str, section: str) -> float:
    block = payload.get(section, {}) or {}
    if not isinstance(block, dict):
        return float("nan")
    return float(block.get(metric, float("nan")))


def summarize(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_policy[str(row["policy"])].append(row)
    summary = []
    for policy in POLICIES:
        group = by_policy[policy]
        if not group:
            continue
        out: dict[str, object] = {"policy": policy, "label": LABELS[policy], "seeds": len(group)}
        for metric, _, section in METRICS:
            vals = [value(row, metric, section) for row in group]
            out[metric] = mean(vals)
            out[f"{metric}_sem"] = sem(vals)
        out["synthetic_decline_rate"] = mean([value(row, "synthetic_decline_rate", "posterior_summary") for row in group])
        out["actual_decline_rate"] = mean([value(row, "actual_decline_rate", "posterior_summary") for row in group])
        out["passenger_mean_final_ptrue"] = mean([value(row, "mean_final_ptrue", "passenger_posterior_summary") for row in group])
        out["passenger_mean_final_ptrue_sem"] = sem([value(row, "mean_final_ptrue", "passenger_posterior_summary") for row in group])
        out["passenger_mean_final_rule_acc"] = mean([value(row, "mean_final_rule_acc", "passenger_posterior_summary") for row in group])
        out["passenger_mean_final_rule_acc_sem"] = sem([value(row, "mean_final_rule_acc", "passenger_posterior_summary") for row in group])
        out["passenger_rejection_rate"] = mean([value(row, "rejection_rate", "passenger_posterior_summary") for row in group])
        summary.append(out)
    return summary


def write_csv(summary: list[dict[str, object]], out_prefix: str) -> None:
    path = ANALYSIS / f"{out_prefix}.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        writer.writerows(summary)
    (ANALYSIS / f"{out_prefix}.json").write_text(json.dumps({"rows": summary}, indent=2), encoding="utf-8")


def write_md(summary: list[dict[str, object]], out_prefix: str, fig_stem: str) -> None:
    has_passenger = any(not math.isnan(float(row.get("passenger_mean_final_rule_acc", float("nan")))) for row in summary)
    seed_count = max(int(row.get("seeds", 0)) for row in summary) if summary else 0
    seed_text = "{" + ",".join(str(i) for i in range(seed_count)) + "}" if seed_count else "{}"
    lines = [
        "# MaaSSim Controlled Synthetic Baseline Comparison",
        "",
        f"Controlled MaaSSim matching with synthetic hidden driver rules, seed set `{seed_text}`.",
        "",
        "| Policy | Seeds | Driver P(true) | Driver rule acc | Mean wait | Rides | Rejects | Synthetic decline |" + (" Passenger rule acc | Passenger reject |" if has_passenger else ""),
        "|---|---:|---:|---:|---:|---:|---:|---:|" + ("---:|---:|" if has_passenger else ""),
    ]
    for row in summary:
        base = "| {label} | {seeds} | {p:.3f} +/- {psem:.3f} | {acc:.3f} +/- {accsem:.3f} | {wait:.1f} +/- {waitsem:.1f} | {rides:.1f} +/- {ridessem:.1f} | {rej:.1f} +/- {rejsem:.1f} | {decl:.3f} |".format(
            label=row["label"],
            seeds=row["seeds"],
            p=float(row["mean_final_ptrue"]),
            psem=float(row["mean_final_ptrue_sem"]),
            acc=float(row["mean_final_rule_acc"]),
            accsem=float(row["mean_final_rule_acc_sem"]),
            wait=float(row["pax_wait_mean"]),
            waitsem=float(row["pax_wait_mean_sem"]),
            rides=float(row["veh_nrides_sum"]),
            ridessem=float(row["veh_nrides_sum_sem"]),
            rej=float(row["veh_nrejects_sum"]),
            rejsem=float(row["veh_nrejects_sum_sem"]),
            decl=float(row["synthetic_decline_rate"]),
        )
        if has_passenger:
            base += " {pax_acc:.3f} +/- {pax_acc_sem:.3f} | {pax_rej:.3f} |".format(
                pax_acc=float(row.get("passenger_mean_final_rule_acc", float("nan"))),
                pax_acc_sem=float(row.get("passenger_mean_final_rule_acc_sem", 0.0)),
                pax_rej=float(row.get("passenger_rejection_rate", float("nan"))),
            )
        lines.append(base)
    lines.extend(
        [
            "",
            "Readout: this is still a smoke-scale integration table, not a tuned MaaSSim result. PACT and PACT+ can be identical when the small candidate sets do not make the exploration bonus change the selected assignment.",
            "",
            f"![MaaSSim baseline comparison](../../figs/{fig_stem}.png)",
        ]
    )
    (ANALYSIS / f"{out_prefix}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def plot(summary: list[dict[str, object]], fig_stem: str) -> None:
    plt.rcParams.update({"font.size": 8.8, "savefig.dpi": 240})
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.2))
    plot_specs = [
        ("mean_final_rule_acc", "Rule acc"),
        ("pax_wait_mean", "Mean wait"),
        ("veh_nrejects_sum", "Rejects"),
    ]
    x = list(range(len(summary)))
    for ax, (metric, ylabel) in zip(axes, plot_specs, strict=True):
        vals = [float(row[metric]) for row in summary]
        errs = [float(row[f"{metric}_sem"]) for row in summary]
        ax.bar(x, vals, yerr=errs, color=[COLORS[str(row["policy"])] for row in summary], edgecolor="white", linewidth=0.8, capsize=2.5)
        ax.set_xticks(x)
        ax.set_xticklabels([str(row["label"]) for row in summary], rotation=25, ha="right")
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", linestyle=":", linewidth=0.55, color="#dddddd")
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
    fig.suptitle("MaaSSim controlled synthetic baseline smoke", x=0.02, y=1.02, ha="left", fontsize=12, fontweight="semibold")
    fig.tight_layout()
    for out_dir in FIGS:
        out_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_dir / f"{fig_stem}.png", bbox_inches="tight", facecolor="white")
        fig.savefig(out_dir / f"{fig_stem}.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix", default="controlled_synthetic")
    parser.add_argument("--out-prefix", default="maassim_controlled_synthetic_baseline_summary")
    parser.add_argument("--fig-stem", default="fig_maassim_controlled_baselines")
    args = parser.parse_args()
    rows = load_rows(args.prefix)
    summary = summarize(rows)
    write_csv(summary, args.out_prefix)
    write_md(summary, args.out_prefix, args.fig_stem)
    plot(summary, args.fig_stem)
    print(json.dumps({"runs": len(rows), "summary_rows": len(summary), "csv": str((ANALYSIS / f"{args.out_prefix}.csv").relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()