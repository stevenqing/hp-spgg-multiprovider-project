"""Generate CourierDispatch live appendix figures F3/F4/A2/A3."""

from __future__ import annotations

import csv
import json
import math
import sys
import time
from collections import defaultdict
from itertools import product
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_courier_dispatch.dispatch_env import CourierDispatchEnv, RulePosterior  # noqa: E402
from llm_courier_dispatch.matching_dispatch import (  # noqa: E402
    all_assignments,
    expected_assignment_reward,
    expected_assignment_under_factored_posteriors,
    type_stress_order_pool,
)


ANALYSIS = ROOT / "analysis" / "courier_dispatch_matching"
OUT_DIRS = [ROOT / "figs", ROOT / "arr_paper" / "figs"]
MODEL_LABELS = ["GPT-5.4-mini", "DeepSeek-V3.2", "Kimi-K2.6", "Llama-Maverick"]
BETAS = [("0p0", 0.0), ("0p025", 0.025), ("0p05", 0.05), ("0p1", 0.1), ("0p2", 0.2), ("0p4", 0.4)]
INK = "#202020"
MUTED = "#555555"
PALE = "#cccccc"
BLUE = "#1b3a6f"
STEEL = "#3d6cb3"
OCHRE = "#c7773d"
GREEN = "#3d7b62"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"no rows for {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def mean(values: list[float]) -> float:
    return float(sum(values) / len(values)) if values else float("nan")


def sem(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = mean(values)
    return float(math.sqrt(sum((value - avg) ** 2 for value in values) / (len(values) - 1)) / math.sqrt(len(values)))


def style(ax: plt.Axes) -> None:
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(PALE)
        ax.spines[spine].set_linewidth(0.45)
    ax.tick_params(colors=MUTED, which="both")
    ax.grid(axis="y", linestyle=":", linewidth=0.55, color="#dddddd")
    ax.set_axisbelow(True)


def aggregate_by(rows: list[dict[str, str]], key_field: str, value_field: str) -> tuple[list[float], list[float], list[float]]:
    grouped: dict[float, list[float]] = defaultdict(list)
    for row in rows:
        grouped[float(row[key_field])].append(float(row[value_field]))
    xs = sorted(grouped)
    return xs, [mean(grouped[x]) for x in xs], [sem(grouped[x]) for x in xs]


def aggregate_a3_h8_beta_sweep() -> None:
    rows: list[dict[str, object]] = []
    for tag, beta in BETAS:
        path = ANALYSIS / f"courier_matching_structured_live_expected_pact_beta_{tag}_s5h8_allmodels_rows.csv"
        source_rows = read_csv(path)
        by_model: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in source_rows:
            if row["method"] == "live_pact_plus" and int(row["round"]) == 7:
                by_model[row["model"]].append(row)
        for model, final_rows in sorted(by_model.items()):
            label = next((row.get("model_label", "") for row in final_rows if row.get("model_label")), model)
            rows.append(
                {
                    "horizon": 8,
                    "beta": beta,
                    "model": model,
                    "model_label": label,
                    "exploration_cost": mean([float(row["cumulative_exploration_cost"]) for row in final_rows]),
                    "exploration_cost_sem": sem([float(row["cumulative_exploration_cost"]) for row in final_rows]),
                    "ptrue": mean([float(row["mean_true_tuple_posterior"]) for row in final_rows]),
                    "ptrue_sem": sem([float(row["mean_true_tuple_posterior"]) for row in final_rows]),
                    "regret": mean([float(row["cumulative_regret"]) for row in final_rows]),
                    "regret_sem": sem([float(row["cumulative_regret"]) for row in final_rows]),
                }
            )
    write_csv(ANALYSIS / "courier_matching_live_A3_beta_exploration_h8_sweep_summary.csv", rows)
    (ANALYSIS / "courier_matching_live_A3_beta_exploration_h8_sweep_summary.json").write_text(
        json.dumps({"backend": "cloudgpt", "horizon": 8, "rows": rows}, indent=2), encoding="utf-8"
    )


def explicit_joint_product_value(env: CourierDispatchEnv, orders, assignment, posteriors: list[RulePosterior]) -> float:
    posterior_probs = [posterior.probs() for posterior in posteriors]
    value = 0.0
    for profile in product(range(len(env.type_space)), repeat=env.n_agents):
        weight = 1.0
        for driver, type_index in enumerate(profile):
            weight *= float(posterior_probs[driver][type_index])
        if weight <= 0.0:
            continue
        types = np.asarray([env.type_space[type_index] for type_index in profile], dtype=int)
        value += weight * expected_assignment_reward(env, orders, assignment, types)
    return float(value)


def random_posterior(env: CourierDispatchEnv, rng: np.random.Generator) -> RulePosterior:
    posterior = RulePosterior(env.type_space)
    posterior.log_probs = rng.normal(loc=0.0, scale=1.15, size=len(env.type_space))
    posterior.log_probs -= float(np.max(posterior.log_probs))
    return posterior


def generate_a2_factored_vs_joint() -> None:
    rng = np.random.default_rng(20260417)
    replicate_counts = {2: 8, 3: 6, 4: 3}
    rows: list[dict[str, object]] = []
    for n_agents, replicate_count in replicate_counts.items():
        for replicate in range(replicate_count):
            seed = 30_000 + 100 * n_agents + replicate
            env = CourierDispatchEnv(n_agents=n_agents, rule_count=4, horizon=1, seed=seed)
            env.reset(seed)
            orders = type_stress_order_pool(env, n_agents + 1)
            assignments = all_assignments(n_agents, len(orders))
            assignment = assignments[int(rng.integers(0, len(assignments)))]
            posteriors = [random_posterior(env, rng) for _ in range(n_agents)]

            start = time.perf_counter()
            factored = expected_assignment_under_factored_posteriors(
                env,
                orders,
                assignment,
                posteriors,
                rng,
                samples=4,
                max_exact_profiles=10_000_000,
            )
            factored_sec = time.perf_counter() - start

            start = time.perf_counter()
            exact = explicit_joint_product_value(env, orders, assignment, posteriors)
            exact_sec = time.perf_counter() - start

            rows.append(
                {
                    "n_agents": n_agents,
                    "replicate": replicate,
                    "joint_type_states": len(env.type_space) ** n_agents,
                    "factored_value": factored,
                    "exact_joint_value": exact,
                    "abs_error": abs(factored - exact),
                    "factored_sec": factored_sec,
                    "exact_sec": exact_sec,
                    "speedup": exact_sec / factored_sec if factored_sec > 0 else float("nan"),
                    "exact_skipped": "no",
                }
            )
    write_csv(ANALYSIS / "courier_matching_A2_factored_vs_joint_error.csv", rows)
    (ANALYSIS / "courier_matching_A2_factored_vs_joint_error.json").write_text(
        json.dumps({"rows": rows}, indent=2), encoding="utf-8"
    )


def plot_f3() -> None:
    rows = read_csv(ANALYSIS / "courier_matching_live_F3_couple_lambda_summary.csv")
    fig, axes = plt.subplots(1, 3, figsize=(10.4, 3.0), sharex=True)
    metrics = [("ptrue", "P(true tuple)", BLUE), ("rule_acc", "Rule-marginal acc.", GREEN), ("nll_true", "NLL(true)", OCHRE)]
    for ax, (field, ylabel, color) in zip(axes, metrics, strict=True):
        xs, ys, es = aggregate_by(rows, "lambda", field)
        ax.errorbar(xs, ys, yerr=es, color=color, marker="o", markersize=5.4, markerfacecolor="white", markeredgewidth=1.2, linewidth=1.8, capsize=2.5)
        ax.set_xlabel("Couple lambda")
        ax.set_ylabel(ylabel)
        style(ax)
    fig.suptitle("F3. CloudGPT live coupling stress", x=0.02, y=1.02, ha="left", fontsize=12, fontweight="semibold", color=INK)
    fig.tight_layout()
    save(fig, "fig_courier_matching_F3_couple_lambda")


def plot_f4() -> None:
    rows = read_csv(ANALYSIS / "courier_matching_live_F4_per_round_posterior_summary.csv")
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0), sharex=True)
    labels = {"live_pact": "PACT", "live_pact_plus": "PACT+"}
    colors = {"live_pact": STEEL, "live_pact_plus": OCHRE}
    for method in ["live_pact", "live_pact_plus"]:
        subset = [row for row in rows if row["method"] == method]
        for ax, field, ylabel in [(axes[0], "ptrue", "P(true tuple)"), (axes[1], "rule_acc", "Rule-marginal acc.")]:
            xs, ys, es = aggregate_by(subset, "round", field)
            ax.errorbar(xs, ys, yerr=es, color=colors[method], marker="o", markersize=4.8, markerfacecolor="white", markeredgewidth=1.1, linewidth=1.7, capsize=2.3, label=labels[method])
            ax.set_xlabel("Round")
            ax.set_ylabel(ylabel)
            style(ax)
    axes[0].legend(frameon=False, loc="best")
    fig.suptitle("F4. Per-round posterior recovery", x=0.02, y=1.02, ha="left", fontsize=12, fontweight="semibold", color=INK)
    fig.tight_layout()
    save(fig, "fig_courier_matching_F4_per_round_posterior")


def plot_a2() -> None:
    rows = read_csv(ANALYSIS / "courier_matching_A2_factored_vs_joint_error.csv")
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.0))
    rng = np.random.default_rng(99)
    for n_agents in sorted({int(row["n_agents"]) for row in rows}):
        subset = [row for row in rows if int(row["n_agents"]) == n_agents]
        x_jitter = rng.uniform(-0.06, 0.06, size=len(subset))
        axes[0].scatter(
            np.full(len(subset), n_agents) + x_jitter,
            [max(float(row["abs_error"]), 1e-16) for row in subset],
            s=22,
            color=BLUE,
            alpha=0.70,
            edgecolor="white",
            linewidth=0.35,
        )
    axes[0].set_yscale("log")
    axes[0].set_xlabel("Drivers n")
    axes[0].set_ylabel("Abs. value error")
    axes[0].set_xticks([2, 3, 4])
    style(axes[0])

    grouped: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[int(row["n_agents"])].append(row)
    xs = sorted(grouped)
    factored = [mean([float(row["factored_sec"]) for row in grouped[x]]) for x in xs]
    exact = [mean([float(row["exact_sec"]) for row in grouped[x]]) for x in xs]
    axes[1].plot(xs, factored, color=STEEL, marker="o", markerfacecolor="white", linewidth=1.8, label="Factored exact")
    axes[1].plot(xs, exact, color=OCHRE, marker="s", markerfacecolor="white", linewidth=1.8, label="Explicit joint")
    axes[1].set_yscale("log")
    axes[1].set_xlabel("Drivers n")
    axes[1].set_ylabel("Seconds per value")
    axes[1].set_xticks([2, 3, 4])
    axes[1].legend(frameon=False, loc="best")
    style(axes[1])
    fig.suptitle("A2. Factored exact value matches joint enumeration", x=0.02, y=1.02, ha="left", fontsize=12, fontweight="semibold", color=INK)
    fig.tight_layout()
    save(fig, "fig_courier_matching_A2_factored_vs_joint")


def plot_a3() -> None:
    rows = read_csv(ANALYSIS / "courier_matching_live_A3_beta_exploration_h8_sweep_summary.csv")
    fig, axes = plt.subplots(1, 3, figsize=(10.2, 3.0), sharex=True)
    metrics = [("exploration_cost", "Exploration cost", BLUE), ("ptrue", "Final P(true)", GREEN), ("regret", "Final regret", OCHRE)]
    for ax, (field, ylabel, color) in zip(axes, metrics, strict=True):
        xs, ys, es = aggregate_by(rows, "beta", field)
        ax.errorbar(xs, ys, yerr=es, color=color, marker="o", markersize=5.4, markerfacecolor="white", markeredgewidth=1.2, linewidth=1.8, capsize=2.5)
        ax.set_xlabel("PACT+ beta")
        ax.set_ylabel(ylabel)
        ax.set_xticks([0.0, 0.1, 0.2, 0.4])
        style(ax)
    fig.suptitle("A3. CloudGPT live beta trade-off", x=0.02, y=1.02, ha="left", fontsize=12, fontweight="semibold", color=INK)
    fig.tight_layout()
    save(fig, "fig_courier_matching_A3_beta_exploration")


def save(fig: plt.Figure, stem: str) -> None:
    for out_dir in OUT_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_dir / f"{stem}.png", bbox_inches="tight", facecolor="white")
        fig.savefig(out_dir / f"{stem}.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Inter", "Helvetica Neue", "Arial", "DejaVu Sans"],
            "font.size": 8.8,
            "axes.titlesize": 10.5,
            "axes.titleweight": "semibold",
            "axes.titlelocation": "left",
            "savefig.dpi": 240,
        }
    )
    aggregate_a3_h8_beta_sweep()
    generate_a2_factored_vs_joint()
    plot_f3()
    plot_f4()
    plot_a2()
    plot_a3()
    print("OK: F3/F4/A2/A3 figures written to figs/ and arr_paper/figs/")


if __name__ == "__main__":
    main()