from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path

import numpy as np

ROOT = Path("results/cloudgpt")
OUT = Path("analysis/all_numeric_results.md")

BETAS = ["beta0", "beta0p05", "beta0p1", "beta0p25", "beta0p5", "beta0p75", "beta1", "beta1p5"]
NATIVE_MODELS = {
    "DeepSeek-V3.2": "DeepSeek_V3_2",
    "gpt-5.4-nano": "gpt_5_4_nano_20260317",
    "Kimi-K2.6": "Kimi_K2_6",
    "Llama-4-Maverick": "Llama_4_Maverick_17B_128E_Instruct_FP8",
}
PROMPTED_MODELS = {
    "DeepSeek-V3.2": "DeepSeek_V3_2",
    "gpt-5.4-nano": "gpt_5_4_nano_20260317",
    "Kimi-K2.6": "Kimi_K2_6",
    "Llama-4-Maverick": "Llama_4_Maverick_17B_128E_Instruct_FP8",
}
EXTERNAL_SHARD_MODELS = {
    "gpt-5.4-nano": "gpt_5_4_nano_20260317",
    "Kimi-K2.6": "Kimi_K2_6",
    "Llama-4-Maverick": "Llama_4_Maverick_17B_128E_Instruct_FP8",
}
EXTERNAL_ALGORITHMS = [
    "atom_tom0",
    "atom_tom1",
    "atom_tom2",
    "atom_adaptive_ftl",
    "atom_adaptive_hedge",
    "econ_bne",
]
SOTOPIA_VANILLA_BASELINES = ["hpsmg_plus", "llm_belief", "llm_greedy", "atom_tom1", "econ_bne"]
SOTOPIA_TUNED_BASELINES = [f"{baseline}_sotopia_tuned" for baseline in SOTOPIA_VANILLA_BASELINES]
SOTOPIA_BASELINES = SOTOPIA_VANILLA_BASELINES + SOTOPIA_TUNED_BASELINES
SOTOPIA_MODEL_SLUGS = {
    "DeepSeek-V3.2": "DeepSeek_V3_2",
    "gpt-5.4-nano": "gpt_5_4_nano_20260317",
    "Kimi-K2.6": "Kimi_K2_6",
    "Llama-4-Maverick": "Llama_4_Maverick_17B_128E_Instruct_FP8",
}
SOTOPIA_DIMENSIONS = [
    "believability",
    "relationship",
    "knowledge",
    "secret",
    "social_rules",
    "financial_and_material_benefits",
    "goal",
]


def fmt(value: float) -> str:
    if np.isnan(value):
        return "NA"
    return f"{value:.4f}"


def npz_rows(path: Path) -> list[dict[str, object]]:
    data = np.load(path, allow_pickle=True)
    algorithms = [str(value) for value in data["algorithms"]]
    cumulative = np.asarray(data["cumulative_regret"], dtype=float)
    regrets = np.asarray(data["regrets"], dtype=float)
    welfare = np.asarray(data["welfare"], dtype=float)
    rows: list[dict[str, object]] = []
    for index, algorithm in enumerate(algorithms):
        final = cumulative[index, :, -1]
        welfare_values = welfare[index]
        rows.append(
            {
                "algorithm": algorithm,
                "final_mean": float(final.mean()),
                "final_std": float(final.std(ddof=0)),
                "final_median": float(np.median(final)),
                "final_q25": float(np.quantile(final, 0.25)),
                "final_q75": float(np.quantile(final, 0.75)),
                "per_round_mean": float(regrets[index].mean()),
                "welfare_mean": float(welfare_values.mean()),
                "welfare_std": float(welfare_values.std(ddof=0)),
            }
        )
    return rows


def table(headers: list[str], rows: list[list[object]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def add_result_table(lines: list[str], title: str, headers: list[str], rows: list[list[object]]) -> None:
    lines.append(f"## {title}")
    lines.append("")
    if rows:
        lines.append(table(headers, rows))
    else:
        lines.append("No rows available.")
    lines.append("")


def sotopia_path(slug: str, baseline: str) -> Path:
    if baseline.endswith("_sotopia_tuned"):
        base_baseline = baseline.removesuffix("_sotopia_tuned")
        return Path("analysis") / f"sotopia_hard_official_{slug}_{base_baseline}_sotopia_tuned_all70.json"
    return Path("analysis") / f"sotopia_hard_official_{slug}_{baseline}_all70.json"


def add_e1_e4_llm_tables(lines: list[str]) -> None:
    e1_path = Path("analysis/E1_posterior_concentration_llm_summary.json")
    if e1_path.exists():
        payload = json.loads(e1_path.read_text(encoding="utf-8"))
        rows = []
        for row in payload.get("summary", []):
            rows.append(
                [
                    row.get("backbone", ""),
                    row.get("seeds", ""),
                    row.get("K", ""),
                    fmt(float(row.get("mean_concentration_time_censored", np.nan))),
                    fmt(float(row.get("final_true_mass_mean", np.nan))),
                    ",".join("null" if value is None else str(value) for value in row.get("seed_concentration_times", [])),
                    row.get("input", ""),
                ]
            )
        add_result_table(lines, "E1 LLM Posterior Concentration", ["backbone", "seeds", "K", "mean_concentration_time", "final_true_mass_mean", "seed_times", "source"], rows)

    e2_path = Path("analysis/E2_type_scaling_llm_summary.json")
    if e2_path.exists():
        payload = json.loads(e2_path.read_text(encoding="utf-8"))
        rows = [
            [
                row.get("type_count", ""),
                row.get("algorithm", ""),
                fmt(float(row.get("mean_final_cumulative_regret", np.nan))),
                fmt(float(row.get("sem", np.nan))),
                row.get("seeds", ""),
                row.get("input", ""),
            ]
            for row in payload.get("rows", [])
        ]
        add_result_table(lines, "E2 LLM Type-Count Scaling", ["type_count", "algorithm", "mean_final_cumulative_regret", "sem", "seeds", "source"], rows)

    e2_s10_path = Path("analysis/E2_type_scaling_llm_s10_summary.json")
    if e2_s10_path.exists():
        payload = json.loads(e2_s10_path.read_text(encoding="utf-8"))
        rows = [
            [
                row.get("type_count", ""),
                row.get("algorithm", ""),
                fmt(float(row.get("mean_final_cumulative_regret", np.nan))),
                fmt(float(row.get("sem", np.nan))),
                row.get("seeds", ""),
                row.get("input", ""),
            ]
            for row in payload.get("rows", [])
        ]
        add_result_table(lines, "E2 LLM Type-Count Scaling 10-Seed Confirmation", ["type_count", "algorithm", "mean_final_cumulative_regret", "sem", "seeds", "source"], rows)

    e3_path = Path("analysis/E3_n_agent_scaling_llm_summary.json")
    if e3_path.exists():
        payload = json.loads(e3_path.read_text(encoding="utf-8"))
        rows = [
            [
                row.get("n", ""),
                row.get("algorithm", ""),
                row.get("storage_entries", ""),
                fmt(float(row.get("mean_final_cumulative_regret", np.nan))),
                fmt(float(row.get("sem", np.nan))),
                row.get("seeds", ""),
                row.get("input", ""),
            ]
            for row in payload.get("rows", [])
        ]
        add_result_table(lines, "E3 LLM N-Agent Scaling", ["n", "algorithm", "storage_entries", "mean_final_cumulative_regret", "sem", "seeds", "source"], rows)

    e3_s10_path = Path("analysis/E3_n_agent_scaling_llm_s10_summary.json")
    if e3_s10_path.exists():
        payload = json.loads(e3_s10_path.read_text(encoding="utf-8"))
        rows = [
            [
                row.get("n", ""),
                row.get("algorithm", ""),
                row.get("storage_entries", ""),
                fmt(float(row.get("mean_final_cumulative_regret", np.nan))),
                fmt(float(row.get("sem", np.nan))),
                row.get("seeds", ""),
                row.get("input", ""),
            ]
            for row in payload.get("rows", [])
        ]
        add_result_table(lines, "E3 LLM N-Agent Scaling 10-Seed Confirmation", ["n", "algorithm", "storage_entries", "mean_final_cumulative_regret", "sem", "seeds", "source"], rows)

    e4_path = Path("analysis/E4_prior_recovery_llm_summary.json")
    if e4_path.exists():
        payload = json.loads(e4_path.read_text(encoding="utf-8"))
        rows = [
            [
                row.get("prior_mode", ""),
                row.get("algorithm", ""),
                fmt(float(row.get("mean_final_cumulative_regret", np.nan))),
                fmt(float(row.get("sem_final", np.nan))),
                row.get("seeds", ""),
                row.get("K", ""),
                row.get("input", ""),
            ]
            for row in payload.get("rows", [])
        ]
        add_result_table(lines, "E4 LLM Prior Recovery", ["prior_mode", "algorithm", "mean_final_cumulative_regret", "sem", "seeds", "K", "source"], rows)


def main() -> None:
    lines: list[str] = []
    lines.append("# All Numeric Results")
    lines.append("")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("This file intentionally stores numeric results only, with minimal labels. HP-SPGG metric: final cumulative regret; lower is better. Concordia metric: focal score; higher is better. SOTOPIA metric: evaluator score; higher is better. Oracle is an upper bound.")
    lines.append("")

    headline_rows: list[list[object]] = []
    headline_sources = [
        ("Native", "DeepSeek-V3.2", ROOT / "E2_DeepSeek_V3_2_c19_beta0p25.npz"),
        ("Prompted LLM", "DeepSeek-V3.2", ROOT / "E2_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz"),
        ("External LLM", "DeepSeek-V3.2", ROOT / "E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz"),
    ]
    for group, model, path in headline_sources:
        if not path.exists():
            continue
        for row in npz_rows(path):
            headline_rows.append(
                [
                    group,
                    model,
                    row["algorithm"],
                    fmt(row["final_mean"]),
                    fmt(row["final_std"]),
                    fmt(row["final_median"]),
                    f"[{fmt(row['final_q25'])}, {fmt(row['final_q75'])}]",
                    fmt(row["per_round_mean"]),
                    fmt(row["welfare_mean"]),
                    fmt(row["welfare_std"]),
                    path.as_posix(),
                ]
            )
    headline_rows.sort(key=lambda values: float(values[3]))
    add_result_table(
        lines,
        "Headline DeepSeek c19 K20 s5: Native + Prompted + External",
        ["group", "model", "algorithm", "final_mean", "final_std", "median", "iqr", "per_round", "welfare_mean", "welfare_std", "source"],
        headline_rows,
    )

    native_rows: list[list[object]] = []
    for model, slug in NATIVE_MODELS.items():
        for beta in BETAS:
            path = ROOT / f"E2_{slug}_c19_{beta}.npz"
            if not path.exists():
                continue
            for row in npz_rows(path):
                native_rows.append(
                    [
                        model,
                        beta,
                        row["algorithm"],
                        fmt(row["final_mean"]),
                        fmt(row["final_std"]),
                        fmt(row["final_median"]),
                        f"[{fmt(row['final_q25'])}, {fmt(row['final_q75'])}]",
                        fmt(row["per_round_mean"]),
                        fmt(row["welfare_mean"]),
                        fmt(row["welfare_std"]),
                        path.as_posix(),
                    ]
                )
    add_result_table(
        lines,
        "Native c19 Beta Sweeps",
        ["model", "beta", "algorithm", "final_mean", "final_std", "median", "iqr", "per_round", "welfare_mean", "welfare_std", "source"],
        native_rows,
    )

    prompted_rows: list[list[object]] = []
    for model, slug in PROMPTED_MODELS.items():
        path = ROOT / f"E2_llm_baselines_{slug}_c19_K20_s5.npz"
        if not path.exists():
            continue
        for row in npz_rows(path):
            prompted_rows.append(
                [
                    model,
                    row["algorithm"],
                    fmt(row["final_mean"]),
                    fmt(row["final_std"]),
                    fmt(row["final_median"]),
                    f"[{fmt(row['final_q25'])}, {fmt(row['final_q75'])}]",
                    fmt(row["per_round_mean"]),
                    fmt(row["welfare_mean"]),
                    fmt(row["welfare_std"]),
                    path.as_posix(),
                ]
            )
    add_result_table(
        lines,
        "Prompted LLM c19 K20 s5",
        ["model", "algorithm", "final_mean", "final_std", "median", "iqr", "per_round", "welfare_mean", "welfare_std", "source"],
        prompted_rows,
    )

    external_merged_rows: list[list[object]] = []
    for path in sorted(ROOT.glob("E2_external_llm_baselines_*_c19_K20_s5.npz")):
        if "smoke" in path.name:
            continue
        model = path.name.removeprefix("E2_external_llm_baselines_").removesuffix("_c19_K20_s5.npz")
        for row in npz_rows(path):
            external_merged_rows.append(
                [
                    model,
                    row["algorithm"],
                    fmt(row["final_mean"]),
                    fmt(row["final_std"]),
                    fmt(row["final_median"]),
                    f"[{fmt(row['final_q25'])}, {fmt(row['final_q75'])}]",
                    fmt(row["per_round_mean"]),
                    fmt(row["welfare_mean"]),
                    fmt(row["welfare_std"]),
                    path.as_posix(),
                ]
            )
    add_result_table(
        lines,
        "External LLM Merged c19 K20 s5",
        ["model_slug", "algorithm", "final_mean", "final_std", "median", "iqr", "per_round", "welfare_mean", "welfare_std", "source"],
        external_merged_rows,
    )

    external_shard_rows: list[list[object]] = []
    for model, slug in EXTERNAL_SHARD_MODELS.items():
        for algorithm in EXTERNAL_ALGORITHMS:
            path = ROOT / "shards" / f"E2_external_{slug}_c19_K20_s5_{algorithm}.npz"
            if not path.exists():
                continue
            rows = npz_rows(path)
            selected = next((candidate for candidate in rows if candidate["algorithm"] == algorithm), rows[0])
            external_shard_rows.append(
                [
                    model,
                    algorithm,
                    fmt(selected["final_mean"]),
                    fmt(selected["final_std"]),
                    fmt(selected["final_median"]),
                    f"[{fmt(selected['final_q25'])}, {fmt(selected['final_q75'])}]",
                    fmt(selected["per_round_mean"]),
                    fmt(selected["welfare_mean"]),
                    fmt(selected["welfare_std"]),
                    path.as_posix(),
                ]
            )
    add_result_table(
        lines,
        "External LLM Solo Shards c19 K20 s5",
        ["model", "algorithm", "final_mean", "final_std", "median", "iqr", "per_round", "welfare_mean", "welfare_std", "source"],
        external_shard_rows,
    )

    guardrail_rows: list[list[object]] = []
    for model, slug in PROMPTED_MODELS.items():
        native_path = ROOT / f"E2_{slug}_c19_beta0p25.npz"
        if not native_path.exists():
            continue
        native = npz_rows(native_path)
        proposed = next(row for row in native if row["algorithm"] == "hpsmg_plus")
        candidates = [row for row in native if row["algorithm"] not in {"oracle", "hpsmg_plus"}]
        prompted_path = ROOT / f"E2_llm_baselines_{slug}_c19_K20_s5.npz"
        if prompted_path.exists():
            candidates.extend(npz_rows(prompted_path))
        merged_external = ROOT / f"E2_external_llm_baselines_{slug}_c19_K20_s5.npz"
        if merged_external.exists():
            candidates.extend(npz_rows(merged_external))
        else:
            for algorithm in EXTERNAL_ALGORITHMS:
                shard = ROOT / "shards" / f"E2_external_{slug}_c19_K20_s5_{algorithm}.npz"
                if shard.exists():
                    candidates.extend(row for row in npz_rows(shard) if row["algorithm"] == algorithm)
        best_baseline = min(candidates, key=lambda row: row["final_mean"])
        margin = best_baseline["final_mean"] - proposed["final_mean"]
        guardrail_rows.append(
            [
                model,
                fmt(proposed["final_mean"]),
                fmt(proposed["final_std"]),
                best_baseline["algorithm"],
                fmt(best_baseline["final_mean"]),
                fmt(best_baseline["final_std"]),
                fmt(margin),
                "PASS" if margin > 0 else "VIOLATION",
            ]
        )
    add_result_table(
        lines,
        "Fixed Beta0p25 hpsmg_plus vs Best Available Non-Oracle Baseline",
        ["model", "hpsmg_plus_mean", "hpsmg_plus_std", "best_baseline", "best_baseline_mean", "best_baseline_std", "margin", "status"],
        guardrail_rows,
    )

    add_e1_e4_llm_tables(lines)

    concordia_rows: list[list[object]] = []
    for path in sorted(Path("analysis").glob("concordia_pub_coordination_compact_*.json")):
        if "offline" in path.name or "s2" in path.name or "seed2_4" in path.name:
            continue
        if not ("mechanistic_joint" in path.name or "live_s5" in path.name):
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for row in payload.get("summary", []):
            concordia_rows.append(
                [
                    payload.get("config", ""),
                    payload.get("model", ""),
                    row["method"],
                    row["episodes"],
                    fmt(float(row["focal_score_mean"])),
                    fmt(float(row["focal_score_min_mean"])),
                    fmt(float(row["coordination_rate_mean"])),
                    fmt(float(row["valid_action_rate_mean"])),
                    path.as_posix(),
                ]
            )
    add_result_table(
        lines,
        "Concordia Compact Pub Coordination Live s5",
        ["config", "model", "method", "episodes", "focal_score_mean", "focal_score_min_mean", "coordination_rate_mean", "valid_action_rate_mean", "source"],
        concordia_rows,
    )

    haggling_rows: list[list[object]] = []
    haggling_patterns = [
        "concordia_haggling_compact_*_s*.json",
        "concordia_haggling_multi_item_compact_*_s*.json",
    ]
    for pattern in haggling_patterns:
        for path in sorted(Path("analysis").glob(pattern)):
            if "smoke" in path.name:
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            for row in payload.get("summary", []):
                haggling_rows.append(
                    [
                        payload.get("domain", payload.get("game", "")),
                        payload.get("config", ""),
                        row["method"],
                        row["episodes"],
                        fmt(float(row["focal_score_mean"])),
                        fmt(float(row["focal_score_min_mean"])),
                        fmt(float(row["deal_score_mean"])),
                        fmt(float(row["deal_min_score_mean"])),
                        fmt(float(row["agreement_rate_mean"])),
                        fmt(float(row["nash_product_mean"])),
                        fmt(float(row["valid_action_rate_mean"])),
                        path.as_posix(),
                    ]
                )
    add_result_table(
        lines,
        "Concordia Compact Haggling",
        ["domain", "config", "method", "episodes", "focal_score_mean", "focal_score_min_mean", "deal_score_mean", "deal_min_score_mean", "agreement_rate_mean", "nash_product_mean", "valid_action_rate_mean", "source"],
        haggling_rows,
    )

    sotopia_rows: list[list[object]] = []
    sotopia_vanilla_rows: list[list[object]] = []
    sotopia_tuned_rows: list[list[object]] = []
    sotopia_dimension_rows: list[list[object]] = []
    for model, slug in SOTOPIA_MODEL_SLUGS.items():
        for baseline in SOTOPIA_BASELINES:
            path = sotopia_path(slug, baseline)
            if not path.exists():
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            case_count = payload.get("case_count", len(payload.get("episodes", [])))
            target_case_count = payload.get("target_case_count", 70)
            if payload.get("complete", False) is not True or case_count != target_case_count:
                continue
            summary = payload.get("summary", {})
            agent_1 = summary.get("agent_1", {})
            agent_2 = summary.get("agent_2", {})
            result_row = [
                model,
                baseline,
                case_count,
                target_case_count,
                payload.get("complete", False),
                fmt(float(summary.get("mean_overall", np.nan))),
                fmt(float(agent_1.get("overall_score", np.nan))),
                fmt(float(agent_2.get("overall_score", np.nan))),
                path.as_posix(),
            ]
            sotopia_rows.append(result_row)
            if baseline in SOTOPIA_VANILLA_BASELINES:
                sotopia_vanilla_rows.append(result_row)
            elif baseline in SOTOPIA_TUNED_BASELINES:
                sotopia_tuned_rows.append(result_row)
            for dimension in SOTOPIA_DIMENSIONS:
                agent_1_score = float(agent_1.get(dimension, np.nan))
                agent_2_score = float(agent_2.get(dimension, np.nan))
                sotopia_dimension_rows.append(
                    [
                        model,
                        baseline,
                        dimension,
                        fmt(agent_1_score),
                        fmt(agent_2_score),
                        fmt((agent_1_score + agent_2_score) / 2.0),
                    ]
                )
    sotopia_rows.sort(key=lambda row: (str(row[0]), -(float(row[5]) if row[5] != "NA" else float("-inf"))))
    sotopia_vanilla_rows.sort(key=lambda row: (str(row[0]), -(float(row[5]) if row[5] != "NA" else float("-inf"))))
    sotopia_tuned_rows.sort(key=lambda row: (str(row[0]), -(float(row[5]) if row[5] != "NA" else float("-inf"))))
    add_result_table(
        lines,
        "SOTOPIA-Hard Vanilla Fair all70",
        ["model", "baseline", "cases", "target_cases", "complete", "mean_overall", "agent_1_overall", "agent_2_overall", "source"],
        sotopia_vanilla_rows,
    )
    add_result_table(
        lines,
        "SOTOPIA-Hard Tuned All-Baseline Fair all70 Complete Rows",
        ["model", "baseline", "cases", "target_cases", "complete", "mean_overall", "agent_1_overall", "agent_2_overall", "source"],
        sotopia_tuned_rows,
    )
    add_result_table(
        lines,
        "SOTOPIA-Hard Official Reconstruction all70 Combined",
        ["model", "baseline", "cases", "target_cases", "complete", "mean_overall", "agent_1_overall", "agent_2_overall", "source"],
        sotopia_rows,
    )
    add_result_table(
        lines,
        "SOTOPIA-Hard Official Reconstruction Dimension Means",
        ["model", "baseline", "dimension", "agent_1", "agent_2", "mean_agents"],
        sotopia_dimension_rows,
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT.as_posix())


if __name__ == "__main__":
    main()
