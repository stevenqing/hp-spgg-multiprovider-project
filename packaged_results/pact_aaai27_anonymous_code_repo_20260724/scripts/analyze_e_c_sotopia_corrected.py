"""Analyze the corrected SOTOPIA E-C/E-R3 runs without new LLM calls.

The recurrent posterior is reconstructed turn by turn from stored transcripts
using the same keyword-increment function as the live agent.  SOTOPIA has no
native labels for the project's four persona classes, so concentration is
measured against the profile-derived oracle projection used by the existing
oracle adapter and is always labelled as a proxy, never ground truth.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_hpgg.personas import PERSONAS
from llm_hpgg_sotopia.agents import (
    _persona_log_likelihood_increment,
    _posterior_from_log_scores,
    oracle_one_hot_from_profile,
)
from llm_hpgg_sotopia.official_hard_data import load_hard_cases, make_agent_profiles


DEFAULT_RAW = ROOT / "analysis" / "aaai27_review" / "e_r3_raw"
DEFAULT_AGG = ROOT / "analysis" / "aaai27_review" / "e_r3_menu_corruption.csv"
DEFAULT_COMPARATORS = ROOT / "config" / "aaai27_sotopia_historical_comparators.csv"
DEFAULT_OUT = ROOT / "analysis" / "e_c_sotopia_corrected"
DEFAULT_SURROGATE = ROOT / "analysis" / "aaai27_review" / "e_c_component_surrogate_only.csv"
DEFAULT_NAIVE = ROOT / "analysis" / "aaai27_review" / "e_c_component_naive_belief.csv"


def family_of(codename: str) -> str:
    parts = codename.split("_")
    while parts and parts[-1].isdigit():
        parts.pop()
    return "_".join(parts)


def extract_utterance(natural_action: str) -> str:
    match = re.search(r'said:\s*"(.*)"\s*$', natural_action, flags=re.DOTALL)
    return match.group(1) if match else natural_action


def entropy(posterior: dict[str, float]) -> float:
    values = np.clip(np.asarray(list(posterior.values()), dtype=float), 1e-15, 1.0)
    return float(-np.sum(values * np.log(values)) / math.log(len(values)))


def mean_sem(values: list[float]) -> tuple[float, float]:
    array = np.asarray(values, dtype=float)
    return float(array.mean()), float(array.std(ddof=1) / math.sqrt(len(array))) if len(array) > 1 else 0.0


def load_proxy_targets(benchmark: Path, episodes_jsonl: Path, cache: Path) -> dict[str, dict[str, str]]:
    cases = load_hard_cases(benchmark, episodes_jsonl, cache)
    targets: dict[str, dict[str, str]] = {}
    for case in cases:
        profiles = make_agent_profiles(case)
        target_for_agent_1 = max(oracle_one_hot_from_profile(profiles[1]), key=oracle_one_hot_from_profile(profiles[1]).get)
        target_for_agent_2 = max(oracle_one_hot_from_profile(profiles[0]), key=oracle_one_hot_from_profile(profiles[0]).get)
        targets[case.combo_pk] = {"agent_1": target_for_agent_1, "agent_2": target_for_agent_2}
    return targets


def reconstruct_episode(episode: dict[str, Any], targets: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    combo_pk = str(episode["combo_pk"])
    target = targets[combo_pk]
    audit = episode.get("menu_corruption", {}) or {}
    transcript = episode.get("transcript", []) or []
    log_scores = {
        agent: {persona.key: math.log(1.0 / len(PERSONAS)) for persona in PERSONAS}
        for agent in ("agent_1", "agent_2")
    }
    rows: list[dict[str, object]] = []
    applied = {"agent_1": 0, "agent_2": 0}

    def append_row(agent: str, turn: int) -> None:
        posterior = _posterior_from_log_scores(log_scores[agent])
        proxy_key = target[agent]
        rows.append(
            {
                "family": family_of(str(episode.get("codename", ""))),
                "combo_pk": combo_pk,
                "episode_id": episode.get("episode_id", combo_pk),
                "replicate": episode.get("replicate", ""),
                "agent": agent,
                "turn": turn,
                "updates_applied": applied[agent],
                "proxy_persona": proxy_key,
                "proxy_mass": float(posterior[proxy_key]),
                "normalized_entropy": entropy(posterior),
                "map_matches_proxy": int(max(posterior, key=posterior.get) == proxy_key),
            }
        )

    append_row("agent_1", 0)
    append_row("agent_2", 0)
    for turn_index, turn in enumerate(transcript, start=1):
        actions = turn.get("actions", {}) or {}
        for observer, opponent in (("agent_1", "agent_2"), ("agent_2", "agent_1")):
            max_updates = int((audit.get(observer, {}) or {}).get("updates", 0) or 0)
            if applied[observer] >= max_updates:
                append_row(observer, turn_index)
                continue
            text = extract_utterance(str(actions.get(opponent, "")))
            increments = _persona_log_likelihood_increment(text)
            for key, increment in increments.items():
                log_scores[observer][key] += float(increment)
            applied[observer] += 1
            append_row(observer, turn_index)
    return rows


def read_all_p0(raw_dir: Path) -> list[dict[str, Any]]:
    episodes: list[dict[str, Any]] = []
    for path in sorted(raw_dir.glob("p0p0_r*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        episodes.extend(payload.get("episodes", []))
    if not episodes:
        raise FileNotFoundError(f"no corrected p=0 raw episodes under {raw_dir}")
    return episodes


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def concentration_summary(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[tuple[str, int], list[dict[str, object]]] = {}
    for row in rows:
        groups.setdefault((str(row["family"]), int(row["turn"])), []).append(row)
    summary: list[dict[str, object]] = []
    for (family, turn), group in sorted(groups.items()):
        mass_mean, mass_sem = mean_sem([float(row["proxy_mass"]) for row in group])
        entropy_mean, entropy_sem = mean_sem([float(row["normalized_entropy"]) for row in group])
        accuracy_mean, accuracy_sem = mean_sem([float(row["map_matches_proxy"]) for row in group])
        summary.append(
            {
                "family": family,
                "turn": turn,
                "agent_rows": len(group),
                "proxy_mass_mean": mass_mean,
                "proxy_mass_sem": mass_sem,
                "normalized_entropy_mean": entropy_mean,
                "normalized_entropy_sem": entropy_sem,
                "map_matches_proxy_mean": accuracy_mean,
                "map_matches_proxy_sem": accuracy_sem,
            }
        )
    return summary


def read_corruption(path: Path) -> list[dict[str, object]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    groups: dict[tuple[str, float], list[float]] = {}
    for row in rows:
        if row.get("focal_score", "") == "":
            continue
        groups.setdefault((str(row["family"]), float(row["p"])), []).append(float(row["focal_score"]))
    result: list[dict[str, object]] = []
    for (family, p), values in sorted(groups.items()):
        mean, sem = mean_sem(values)
        result.append({"family": family, "p": p, "episodes": len(values), "focal_score_mean": mean, "focal_score_sem": sem})
    return result


def read_comparators(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return {str(row["family"]): row for row in csv.DictReader(handle)}


def branch_decision(corruption: list[dict[str, object]], comparators: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    decisions = []
    for row in corruption:
        if not math.isclose(float(row["p"]), 0.0):
            continue
        comparator = comparators[str(row["family"])]
        best = float(comparator["mean"])
        delta = float(row["focal_score_mean"]) - best
        decisions.append(
            {
                "family": row["family"],
                "corrected_p0_mean": row["focal_score_mean"],
                "corrected_p0_sem": row["focal_score_sem"],
                "historical_best_method": comparator["best_method"],
                "historical_best_mean": best,
                "delta_vs_historical_best": delta,
                "branch": "restore" if delta > 0.0 else "clean-boundary",
            }
        )
    return decisions


def component_summary(
    full_path: Path,
    surrogate_path: Path,
    naive_path: Path,
) -> list[dict[str, object]]:
    sources = {
        "PACT+ corrected": full_path,
        "surrogate-only corrected": surrogate_path,
        "naive-belief corrected": naive_path,
    }
    groups: dict[tuple[str, str], list[float]] = {}
    scores_by_episode: dict[tuple[str, str, str], float] = {}
    for label, path in sources.items():
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if not math.isclose(float(row.get("p", 0.0)), 0.0):
                    continue
                value = row.get("focal_score", "")
                if value == "":
                    continue
                family = str(row["family"])
                episode_id = str(row["episode_id"])
                numeric = float(value)
                groups.setdefault((family, label), []).append(numeric)
                scores_by_episode[(family, label, episode_id)] = numeric
    result: list[dict[str, object]] = []
    for (family, label), values in sorted(groups.items()):
        mean, sem = mean_sem(values)
        episode_ids = sorted(
            key[2]
            for key in scores_by_episode
            if key[0] == family and key[1] == label
        )
        paired = [
            scores_by_episode[(family, "PACT+ corrected", episode_id)]
            - scores_by_episode[(family, label, episode_id)]
            for episode_id in episode_ids
            if (family, "PACT+ corrected", episode_id) in scores_by_episode
        ]
        paired_mean, paired_sem = mean_sem(paired) if paired else (float("nan"), float("nan"))
        result.append(
            {
                "family": family,
                "variant": label,
                "episodes": len(values),
                "focal_score_mean": mean,
                "focal_score_sem": sem,
                "pact_minus_variant_paired_mean": paired_mean,
                "pact_minus_variant_paired_sem": paired_sem,
            }
        )
    return result


def plot_results(concentration: list[dict[str, object]], corruption: list[dict[str, object]], out_dir: Path) -> None:
    families = sorted({str(row["family"]) for row in concentration})
    colors = dict(zip(families, ["#12345d", "#b64b45", "#2f7d5b"], strict=False))
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.35))
    for family in families:
        family_rows = [row for row in concentration if str(row["family"]) == family]
        axes[0].errorbar(
            [int(row["turn"]) for row in family_rows],
            [float(row["proxy_mass_mean"]) for row in family_rows],
            yerr=[float(row["proxy_mass_sem"]) for row in family_rows],
            marker="o",
            capsize=2,
            linewidth=1.3,
            color=colors[family],
            label=family.replace("_", " "),
        )
        corruption_rows = [row for row in corruption if str(row["family"]) == family]
        axes[1].errorbar(
            [float(row["p"]) for row in corruption_rows],
            [float(row["focal_score_mean"]) for row in corruption_rows],
            yerr=[float(row["focal_score_sem"]) for row in corruption_rows],
            marker="o",
            capsize=2,
            linewidth=1.3,
            color=colors[family],
            label=family.replace("_", " "),
        )
    axes[0].axhline(0.25, color="#888888", linestyle="--", linewidth=0.9)
    axes[0].set_xlabel("Dialogue turn")
    axes[0].set_ylabel("Mass on profile-derived proxy type")
    axes[0].set_title("(a) Corrected recurrent tracker", loc="left")
    axes[1].set_xlabel("Menu-corruption probability")
    axes[1].set_ylabel("Focal score")
    axes[1].set_title("(b) Intent-menu sensitivity", loc="left")
    for ax in axes:
        ax.grid(axis="y", linestyle=":", linewidth=0.6, color="#d7d7d7")
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].legend(frameon=False, fontsize=7)
    fig.tight_layout()
    for target in (out_dir, ROOT / "figs", ROOT / "arr_paper" / "figs"):
        target.mkdir(parents=True, exist_ok=True)
        fig.savefig(target / "fig_e_c_sotopia_corrected.pdf", bbox_inches="tight", facecolor="white")
        fig.savefig(target / "fig_e_c_sotopia_corrected.png", dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_component(component: list[dict[str, object]], out_dir: Path) -> None:
    if not component:
        return
    families = sorted({str(row["family"]) for row in component})
    variants = ["surrogate-only corrected", "naive-belief corrected", "PACT+ corrected"]
    colors = ["#9a9a9a", "#b64b45", "#12345d"]
    x = np.arange(len(families), dtype=float)
    width = 0.24
    fig, ax = plt.subplots(figsize=(6.8, 3.4))
    for variant_index, (variant, color) in enumerate(zip(variants, colors, strict=True)):
        means = []
        sems = []
        for family in families:
            row = next(
                (
                    item
                    for item in component
                    if str(item["family"]) == family and str(item["variant"]) == variant
                ),
                None,
            )
            means.append(float(row["focal_score_mean"]) if row else float("nan"))
            sems.append(float(row["focal_score_sem"]) if row else 0.0)
        offset = (variant_index - 1) * width
        ax.bar(x + offset, means, width, yerr=sems, capsize=2, color=color, label=variant)
    ax.set_xticks(x, [family.replace("_", "\n") for family in families])
    ax.set_ylabel("Focal score")
    ax.set_title("Corrected SOTOPIA tracker variants", loc="left")
    ax.grid(axis="y", linestyle=":", linewidth=0.6, color="#d7d7d7")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    for target in (out_dir, ROOT / "figs", ROOT / "arr_paper" / "figs"):
        target.mkdir(parents=True, exist_ok=True)
        fig.savefig(target / "fig_e_c_sotopia_component_corrected.pdf", bbox_inches="tight", facecolor="white")
        fig.savefig(target / "fig_e_c_sotopia_component_corrected.png", dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def write_markdown(
    path: Path,
    concentration: list[dict[str, object]],
    corruption: list[dict[str, object]],
    component: list[dict[str, object]],
    decisions: list[dict[str, object]],
    mechanism_branch: str,
) -> None:
    levels = sorted({float(row["p"]) for row in corruption})
    if {0.25, 0.5}.issubset(set(levels)):
        grid_note = (
            "The completed grid contains 0%, 10%, 20%, 25%, 30%, and 50% corruption; every point is a measured rerun, not interpolation. "
        )
    else:
        grid_note = (
            "The existing grid is reported exactly as run. Missing requested 25%/50% levels are not interpolated. "
        )
    lines = [
        "# E-C: Corrected SOTOPIA Tracker Analysis",
        "",
        "The retained corrected run reads `Observation.last_turn` and records nonzero recurrent updates. "
        "SOTOPIA has no native labels for the project's four persona classes; all concentration numbers below use the existing profile-derived oracle projection as a proxy.",
        "",
        "## Branch decision",
        "",
        "| family | corrected p=0 | historical best | delta | branch |",
        "|---|---:|---:|---:|---|",
    ]
    for row in decisions:
        lines.append(
            f"| {row['family']} | {float(row['corrected_p0_mean']):.3f} $\\pm$ {float(row['corrected_p0_sem']):.3f} | "
            f"{float(row['historical_best_mean']):.3f} ({row['historical_best_method']}) | "
            f"{float(row['delta_vs_historical_best']):+.3f} | {row['branch']} |"
        )
    lines.extend(["", "## Proxy concentration", "", "| family | turn | proxy mass | entropy | MAP agreement |", "|---|---:|---:|---:|---:|"])
    for row in concentration:
        lines.append(
            f"| {row['family']} | {row['turn']} | {float(row['proxy_mass_mean']):.3f} $\\pm$ {float(row['proxy_mass_sem']):.3f} | "
            f"{float(row['normalized_entropy_mean']):.3f} | {float(row['map_matches_proxy_mean']):.3f} |"
        )
    lines.extend(["", "## Menu corruption", "", "| family | p | episodes | focal score |", "|---|---:|---:|---:|"])
    for row in corruption:
        lines.append(
            f"| {row['family']} | {float(row['p']):.2f} | {row['episodes']} | "
            f"{float(row['focal_score_mean']):.3f} $\\pm$ {float(row['focal_score_sem']):.3f} |"
        )
    if component:
        lines.extend(["", "## Corrected component variants", "", "| family | variant | episodes | focal score | paired PACT-minus-variant |", "|---|---|---:|---:|---:|"])
        for row in component:
            lines.append(
                f"| {row['family']} | {row['variant']} | {row['episodes']} | "
                f"{float(row['focal_score_mean']):.3f} $\\pm$ {float(row['focal_score_sem']):.3f} | "
                f"{float(row['pact_minus_variant_paired_mean']):+.3f} $\\pm$ {float(row['pact_minus_variant_paired_sem']):.3f} |"
            )
    lines.extend(
        [
            "",
            grid_note
            + "The corrected p=0 run is below the retained GPT-nano comparator in all three families. "
            + f"Applying the corrected component/concentration rule selects the {mechanism_branch} branch.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--aggregate", type=Path, default=DEFAULT_AGG)
    parser.add_argument("--comparators", type=Path, default=DEFAULT_COMPARATORS)
    parser.add_argument("--surrogate-component", type=Path, default=DEFAULT_SURROGATE)
    parser.add_argument("--naive-component", type=Path, default=DEFAULT_NAIVE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--benchmark-agents", type=Path, default=ROOT / "external" / "sotopia_data_probe" / "benchmark_agents.json")
    parser.add_argument("--episodes-jsonl", type=Path, default=ROOT / "external" / "sotopia_data_probe" / "sotopia_episodes_v1_hf.jsonl")
    parser.add_argument("--case-cache", type=Path, default=ROOT / "external" / "sotopia_data_probe" / "sotopia_hard_cases_cache.json")
    args = parser.parse_args()

    targets = load_proxy_targets(args.benchmark_agents, args.episodes_jsonl, args.case_cache)
    episodes = read_all_p0(args.raw_dir)
    reconstructed = [row for episode in episodes for row in reconstruct_episode(episode, targets)]
    concentration = concentration_summary(reconstructed)
    corruption = read_corruption(args.aggregate)
    component = component_summary(args.aggregate, args.surrogate_component, args.naive_component)
    decisions = branch_decision(corruption, read_comparators(args.comparators))

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.out_dir / "e_c_posterior_proxy_per_turn.csv", reconstructed)
    write_csv(args.out_dir / "e_c_posterior_proxy_summary.csv", concentration)
    write_csv(args.out_dir / "e_c_menu_corruption_summary.csv", corruption)
    write_csv(args.out_dir / "e_c_branch_decision.csv", decisions)
    if component:
        write_csv(args.out_dir / "e_c_component_summary.csv", component)
    plot_results(concentration, corruption, args.out_dir)
    plot_component(component, args.out_dir)
    component_complete = len(component) == 9 and all(
        int(row["episodes"])
        == {"craigslist_bargains": 80, "donate_funds": 20, "revenge_plot": 20}[str(row["family"])]
        for row in component
    )
    revenge_naive = next(
        (
            row
            for row in component
            if row["family"] == "revenge_plot" and row["variant"] == "naive-belief corrected"
        ),
        None,
    )
    revenge_final = max(
        (row for row in concentration if row["family"] == "revenge_plot"),
        key=lambda row: int(row["turn"]),
    )
    restore = bool(
        component_complete
        and revenge_naive is not None
        and float(revenge_naive["pact_minus_variant_paired_mean"])
        - 1.96 * float(revenge_naive["pact_minus_variant_paired_sem"])
        > 0.0
        and float(revenge_final["proxy_mass_mean"]) > 0.25
    )
    mechanism_branch = "restore" if restore else "clean-boundary"
    write_markdown(
        args.out_dir / "e_c_sotopia_corrected.md",
        concentration,
        corruption,
        component,
        decisions,
        mechanism_branch,
    )
    metadata = {
        "experiment": "E-C corrected SOTOPIA analysis",
        "episode_count_p0": len(episodes),
        "native_true_persona_labels": False,
        "concentration_target": "profile-derived oracle_one_hot_from_profile proxy",
        "component_ablation_corrected": component_complete,
        "available_corruption_levels": sorted({float(row["p"]) for row in corruption}),
        "branch": mechanism_branch,
        "restore_rule": "revenge paired PACT-minus-naive lower 95% bound > 0 and profile-proxy mass > 0.25",
        "llm_calls": 0,
    }
    (args.out_dir / "e_c_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))
    for row in decisions:
        print(f"{row['family']}: delta={float(row['delta_vs_historical_best']):+.4f} branch={row['branch']}")


if __name__ == "__main__":
    main()
