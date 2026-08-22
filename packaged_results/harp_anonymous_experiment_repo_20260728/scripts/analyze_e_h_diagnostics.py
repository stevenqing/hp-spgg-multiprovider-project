"""Analyze E-H-D diagnostics from existing E-H NPZ traces and gate metadata."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = ROOT / "analysis" / "e_h_maassim_grouped_prior"
T95_20 = 2.093
ARMS = ("oracle", "joint", "harp", "harp_s")


def estimate(values: list[float]) -> dict[str, float | int]:
    data = np.asarray(values, dtype=float)
    mean = float(data.mean())
    sem = float(data.std(ddof=1) / math.sqrt(len(data))) if len(data) > 1 else 0.0
    return {
        "n": len(data),
        "mean": mean,
        "sem": sem,
        "ci95_low": mean - T95_20 * sem,
        "ci95_high": mean + T95_20 * sem,
    }


def increments(cumulative: list[float]) -> list[float]:
    values = np.asarray(cumulative, dtype=float)
    return np.diff(np.concatenate(([0.0], values))).tolist()


def fmt(item: dict[str, float | int], digits: int = 3) -> str:
    return f"{float(item['mean']):.{digits}f} +/- {float(item['sem']):.{digits}f}"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_traces(path: Path) -> dict[str, list[dict[str, list[float]]] | list[list[float]]]:
    payload = np.load(path, allow_pickle=False)
    names = (
        "assigned_type_hit_traces",
        "marginal_true_mass_traces",
        "true_profile_mass_traces",
        "regret_traces",
    )
    result: dict[str, list] = {
        name: [json.loads(str(value)) for value in payload[name].tolist()]
        for name in names
    }
    result["joint_shared_weight_pre"] = [json.loads(str(value)) for value in payload["joint_shared_weight_pre"].tolist()]
    result["joint_shared_weight_post"] = [json.loads(str(value)) for value in payload["joint_shared_weight_post"].tolist()]
    return result


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_DIR)
    args = parser.parse_args()
    root = args.root.resolve()
    metadata = json.loads((root / "e_h_maassim_grouped_prior_metadata.json").read_text(encoding="utf-8"))
    sample_payload = np.load(root / "e_h_rho0p0_g4_n8_m2_s20.npz", allow_pickle=False)
    round_count = int(sample_payload["K"])
    per_round = metadata["gates"]["decision_relevance"]["native_lambda0"]["per_round"]
    sensitive = {(int(row["seed"]), int(row["round"])): int(row["distinct_oracle_assignments"]) > 1 for row in per_round}

    output: dict[str, object] = {
        "experiment": "E-H-D belief and sensitive-round diagnostics",
        "source": "existing repaired E-H minimal NPZ traces",
        "sensitive_definition": "distinct_oracle_assignments > 1 from the preregistered full-persona decision-relevance gate",
        "sensitive_rounds": sum(sensitive.values()),
        "total_rounds": len(sensitive),
        "K": round_count,
        "belief_accuracy": {},
        "sensitive_regret": {},
        "round_regret_increment": {},
        "joint_shared_weight": {},
    }
    csv_rows: list[dict[str, object]] = []

    for rho in (0.0, 1.0):
        path = root / f"e_h_rho{str(rho).replace('.', 'p')}_g4_n8_m2_s20.npz"
        traces = load_traces(path)
        rho_key = f"rho{rho:g}"
        belief_output: dict[str, object] = {}
        for arm in ARMS:
            arm_output: dict[str, object] = {}
            for metric in ("assigned_type_hit_traces", "marginal_true_mass_traces", "true_profile_mass_traces"):
                per_seed_all = []
                per_seed_sensitive = []
                arm_traces = traces[metric]
                for seed, trace_by_arm in enumerate(arm_traces):
                    values = [float(value) for value in trace_by_arm[arm]]
                    per_seed_all.append(float(np.mean(values)))
                    selected = [value for round_index, value in enumerate(values) if sensitive[(seed, round_index)]]
                    per_seed_sensitive.append(float(np.mean(selected)) if selected else float("nan"))
                sensitive_values = [value for value in per_seed_sensitive if math.isfinite(value)]
                arm_output[metric.removesuffix("_traces")] = {
                    "all_rounds": estimate(per_seed_all),
                    "sensitive_rounds": estimate(sensitive_values),
                    "final_round": estimate([
                        float(trace_by_arm[arm][-1]) for trace_by_arm in arm_traces
                    ]),
                }
                for subset, values in (
                    ("all", per_seed_all),
                    ("sensitive", sensitive_values),
                    ("final", [float(trace_by_arm[arm][-1]) for trace_by_arm in arm_traces]),
                ):
                    item = estimate(values)
                    csv_rows.append({
                        "section": "belief_accuracy", "rho": rho, "arm": arm,
                        "metric": metric.removesuffix("_traces"), "subset": subset,
                        **item,
                    })
            belief_output[arm] = arm_output
        output["belief_accuracy"][rho_key] = belief_output

        regret_traces = traces["regret_traces"]
        subset_output: dict[str, object] = {}
        for target in ("harp", "harp_s"):
            target_output = {}
            for subset_name, desired in (("sensitive", True), ("nonsensitive", False)):
                seed_gaps = []
                for seed, by_arm in enumerate(regret_traces):
                    target_inc = increments([float(value) for value in by_arm[target]])
                    joint_inc = increments([float(value) for value in by_arm["joint"]])
                    seed_gaps.append(float(sum(
                        target_inc[round_index] - joint_inc[round_index]
                        for round_index in range(len(target_inc))
                        if sensitive[(seed, round_index)] == desired
                    )))
                item = estimate(seed_gaps)
                target_output[subset_name] = item
                csv_rows.append({
                    "section": "paired_regret_subset", "rho": rho, "arm": target,
                    "metric": "regret_increment_minus_joint", "subset": subset_name,
                    **item,
                })
            subset_output[f"{target}_minus_joint"] = target_output
        output["sensitive_regret"][rho_key] = subset_output

        round_output: dict[str, object] = {}
        for arm in ARMS:
            arm_rounds = {}
            for round_index in range(round_count):
                values = [increments([float(value) for value in by_arm[arm]])[round_index] for by_arm in regret_traces]
                item = estimate(values)
                arm_rounds[str(round_index + 1)] = item
                csv_rows.append({
                    "section": "round_regret_increment", "rho": rho, "arm": arm,
                    "metric": "regret_increment", "subset": f"round_{round_index + 1}",
                    **item,
                })
            round_output[arm] = arm_rounds
        output["round_regret_increment"][rho_key] = round_output

        weight_output = {"pre": {}, "post": {}}
        for timing, trace_name in (("pre", "joint_shared_weight_pre"), ("post", "joint_shared_weight_post")):
            for round_index in range(round_count):
                values = [float(trace[round_index]) for trace in traces[trace_name]]
                item = estimate(values)
                weight_output[timing][str(round_index + 1)] = item
                csv_rows.append({
                    "section": "joint_shared_weight", "rho": rho, "arm": "joint",
                    "metric": f"shared_weight_{timing}", "subset": f"round_{round_index + 1}",
                    **item,
                })
        output["joint_shared_weight"][rho_key] = weight_output

    json_path = root / "e_h_diagnostics.json"
    json_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    csv_path = root / "e_h_diagnostics.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(csv_rows[0].keys()))
        writer.writeheader()
        writer.writerows(csv_rows)

    lines = [
        "# E-H-D diagnostics",
        "",
        f"Sensitive rounds: {output['sensitive_rounds']}/{output['total_rounds']}.",
        "",
        "## 1. Belief accuracy",
        "",
        "| rho | arm | assigned hit (all) | assigned hit (final) | assigned hit (sensitive) | marginal true mass (final) | marginal true mass (sensitive) | true-profile mass (sensitive) |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for rho_key, rho in (("rho0", 0), ("rho1", 1)):
        for arm in ARMS:
            item = output["belief_accuracy"][rho_key][arm]
            lines.append(
                f"| {rho} | {arm} | {fmt(item['assigned_type_hit']['all_rounds'])} | "
                f"{fmt(item['assigned_type_hit']['final_round'])} | "
                f"{fmt(item['assigned_type_hit']['sensitive_rounds'])} | "
                f"{fmt(item['marginal_true_mass']['final_round'])} | "
                f"{fmt(item['marginal_true_mass']['sensitive_rounds'])} | "
                f"{fmt(item['true_profile_mass']['sensitive_rounds'], 6)} |"
            )
    lines.extend([
        "",
        "## 2. Sensitive versus non-sensitive paired regret increments",
        "",
        "| rho | contrast | subset | mean +/- SEM | 95% CI |",
        "|---:|---|---|---:|---:|",
    ])
    for rho_key, rho in (("rho0", 0), ("rho1", 1)):
        for contrast, values in output["sensitive_regret"][rho_key].items():
            for subset in ("sensitive", "nonsensitive"):
                item = values[subset]
                lines.append(
                    f"| {rho} | {contrast} | {subset} | {fmt(item)} | "
                    f"[{float(item['ci95_low']):+.3f}, {float(item['ci95_high']):+.3f}] |"
                )
    lines.extend([
        "",
        "## 3. Mean regret increment by round",
        "",
        "| rho | arm | " + " | ".join(f"round {round_index}" for round_index in range(1, round_count + 1)) + " |",
        "|---:|---|" + "---:|" * round_count,
    ])
    for rho_key, rho in (("rho0", 0), ("rho1", 1)):
        for arm in ARMS:
            items = output["round_regret_increment"][rho_key][arm]
            lines.append(
                f"| {rho} | {arm} | " + " | ".join(fmt(items[str(round_index)]) for round_index in range(1, round_count + 1)) + " |"
            )
    lines.extend([
        "",
        "## 4. Joint shared-component weight trajectory",
        "",
        "| rho | timing | " + " | ".join(f"round {round_index}" for round_index in range(1, round_count + 1)) + " |",
        "|---:|---|" + "---:|" * round_count,
    ])
    for rho_key, rho in (("rho0", 0), ("rho1", 1)):
        for timing in ("pre", "post"):
            items = output["joint_shared_weight"][rho_key][timing]
            lines.append(
                f"| {rho} | {timing} | " + " | ".join(fmt(items[str(round_index)]) for round_index in range(1, round_count + 1)) + " |"
            )
    lines.extend(["", "This report is descriptive only and does not choose the next experiment."])
    md_path = root / "e_h_diagnostics.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest_path = root / "e_h_diagnostics_sha256.json"
    artifacts = []
    for path in (json_path, csv_path, md_path):
        artifacts.append({"path": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)})
    manifest_path.write_text(json.dumps({"schema_version": "1.0", "artifacts": artifacts}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "json": str(json_path), "csv": str(csv_path)}, indent=2))


if __name__ == "__main__":
    main()
