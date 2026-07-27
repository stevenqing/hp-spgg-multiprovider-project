"""Consolidate every retained MaaSSim RQ2/RQ3 result into one Markdown file."""

from __future__ import annotations

import csv
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
E_E = ROOT / "analysis" / "e_e_maassim_rq2"
E_F = ROOT / "analysis" / "e_f_maassim_bonus"
MAASSIM = ROOT / "analysis" / "courier_dispatch_maassim"
OUT = ROOT / "analysis" / "maassim_rq2_rq3_all_data.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def escape(value: object) -> str:
    if value is None:
        return ""
    text = str(value)
    if text.lower() == "nan":
        return "NA"
    return text.replace("|", "\\|").replace("\n", " ")


def table(rows: Iterable[dict[str, object] | dict[str, str]], columns: list[tuple[str, str]]) -> list[str]:
    data = list(rows)
    lines = [
        "| " + " | ".join(label for _, label in columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    for row in data:
        lines.append("| " + " | ".join(escape(row.get(key, "")) for key, _ in columns) + " |")
    if not data:
        lines.append("| " + " | ".join("(none)" for _ in columns) + " |")
    return lines


def numeric_summary(values: list[float]) -> tuple[float, float]:
    data = np.asarray(values, dtype=float)
    mean = float(data.mean())
    sem = float(data.std(ddof=1) / math.sqrt(len(data))) if len(data) > 1 else 0.0
    return mean, sem


def fmt(value: float, digits: int = 6) -> str:
    if not math.isfinite(value):
        return "NA"
    return f"{value:.{digits}g}"


def driver_events() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[Path]]:
    raw: list[dict[str, object]] = []
    concentration: dict[int, dict[str, list[float]]] = defaultdict(lambda: {"ptrue": [], "rule_acc": []})
    gains: dict[str, list[float]] = {"reject": [], "accept": []}
    sources: list[Path] = []
    for seed in range(10):
        path = MAASSIM / f"pact_kpi_persona_v2_main_s{seed}_driver_posterior.csv"
        sources.append(path)
        previous_accuracy: dict[int, float] = {}
        observation_count: dict[int, int] = defaultdict(int)
        for event_index, row in enumerate(read_csv(path), start=1):
            driver_id = int(row["driver_id"])
            observation_count[driver_id] += 1
            observation = observation_count[driver_id]
            rule_acc = float(row["rule_acc"])
            ptrue = float(row["ptrue"])
            gain = rule_acc - previous_accuracy.get(driver_id, 0.5)
            previous_accuracy[driver_id] = rule_acc
            event_type = "reject" if row["actual_declined"].lower() == "true" else "accept"
            gains[event_type].append(gain)
            concentration[observation]["ptrue"].append(ptrue)
            concentration[observation]["rule_acc"].append(rule_acc)
            raw.append(
                {
                    "seed": seed,
                    "event_index": event_index,
                    "driver_observation": observation,
                    **row,
                    "event_type": event_type,
                    "rule_acc_gain": repr(gain),
                }
            )
    concentration_rows: list[dict[str, object]] = []
    for observation in sorted(concentration):
        p_mean, p_sem = numeric_summary(concentration[observation]["ptrue"])
        a_mean, a_sem = numeric_summary(concentration[observation]["rule_acc"])
        concentration_rows.append(
            {
                "observation": observation,
                "rows": len(concentration[observation]["ptrue"]),
                "ptrue_mean": fmt(p_mean, 9),
                "ptrue_sem": fmt(p_sem, 9),
                "rule_acc_mean": fmt(a_mean, 9),
                "rule_acc_sem": fmt(a_sem, 9),
            }
        )
    gain_rows: list[dict[str, object]] = []
    for event_type in ("reject", "accept"):
        mean, sem = numeric_summary(gains[event_type])
        gain_rows.append(
            {
                "event_type": event_type,
                "events": len(gains[event_type]),
                "mean_rule_acc_gain": fmt(mean, 9),
                "sem_rule_acc_gain": fmt(sem, 9),
            }
        )
    return raw, concentration_rows, gain_rows, sources


def main() -> None:
    ee_raw = read_csv(E_E / "e_e_maassim_tracker_parity.csv")
    ee_summary = read_csv(E_E / "e_e_maassim_tracker_parity_summary.csv")
    ee_gaps = read_csv(E_E / "e_e_maassim_tracker_parity_gaps.csv")
    ee_meta = json.loads((E_E / "e_e_maassim_tracker_parity_metadata.json").read_text(encoding="utf-8"))
    ef_raw = read_csv(E_F / "e_f_maassim_bonus_per_seed.csv")
    ef_summary = read_csv(E_F / "e_f_maassim_bonus_summary.csv")
    ef_meta = json.loads((E_F / "e_f_maassim_bonus_metadata.json").read_text(encoding="utf-8"))
    mechanism = read_csv(MAASSIM / "maassim_pact_persona_mechanism_summary.csv")
    closed_loop = read_csv(MAASSIM / "maassim_persona_v2_main_summary.csv")
    common_state = read_csv(MAASSIM / "maassim_common_state_replay_summary.csv")
    events, concentration, event_gains, event_sources = driver_events()
    ef_changed = sum(int(row["assignment_changes_vs_pact"]) for row in ef_raw if row["tracker"] == "pact_plus")
    ef_compared = sum(int(row["compared_snapshots"]) for row in ef_raw if row["tracker"] == "pact_plus")

    lines = [
        "# MaaSSim RQ2 / RQ3 — Consolidated Data",
        "",
        "Generated from retained repository artifacts on 2026-07-24. This file collects the complete paper-facing MaaSSim RQ2/RQ3 numeric evidence in one place. It does not include the RQ1 LLM conflict-sweep rows. No values below are interpolated.",
        "",
        "## Scope and evidence map",
        "",
        "| Research question / axis | Experiment or control | Data included here |",
        "|---|---|---|",
        "| RQ2 exactness/storage | E-E factored vs explicit joint | protocol, 24 aggregate rows, 9 paired-gap rows, all 240 tracker/environment rows |",
        "| RQ3 identity attachment | learned vs prior vs shuffled vs oracle | complete 6-row mechanism summary, all retained columns |",
        "| RQ3 closed-form update | posterior concentration and reject/accept decomposition | all 667 retained driver events plus derived concentration and event-gain tables |",
        "| RQ3 centralized dispatch | centralized vs independent prompting | paper-reported Concordia carrier only; original per-seed JSONs are not retained |",
        "| RQ3 beta bonus | E-F PACT vs frozen-beta PACT+ | 2 aggregate rows, paired interval, all 20 tracker/environment rows |",
        "",
        "Terminology: E-E is environment-matched through common environment indices and uses independent tracker sampling RNG streams.",
        "",
        "## RQ2 — E-E factored vs explicit-joint tracker parity",
        "",
        "### Protocol",
        "",
        f"- Source scheme: {ee_meta['source_scheme']}.",
        f"- Fleet sizes: {ee_meta['fleet_sizes']}; lambdas: {ee_meta['lambdas']}; environment indices: {ee_meta['common_environment_indices']}.",
        f"- Likelihood: {ee_meta['likelihood']}.",
        f"- Evidence: {ee_meta['evidence_stream']}.",
        f"- Sampling: {ee_meta['sampling']}.",
        f"- Planner: {ee_meta['planner']}.",
        f"- Utility: `{json.dumps(ee_meta['utility'], sort_keys=True)}`.",
        f"- Joint n=8 status: {ee_meta['joint_n8']}.",
        "",
        "### Paired utility gaps and posterior identity (all 9 required cells)",
        "",
    ]
    lines.extend(
        table(
            ee_gaps,
            [
                ("n", "n"), ("lambda", "lambda"), ("seeds", "environments"),
                ("joint_minus_factored_mean", "joint-factored mean"),
                ("joint_minus_factored_sem", "SEM"), ("ci95_low", "95% low"),
                ("ci95_high", "95% high"), ("ci_covers_zero", "covers zero"),
                ("max_tv", "max marginal TV"), ("factored_entries", "factored entries"),
                ("joint_entries", "joint entries"), ("storage_ratio", "ratio"),
            ],
        )
    )
    lines.extend(["", "### Tracker aggregates (all 24 rows)", ""])
    lines.extend(
        table(
            ee_summary,
            [
                ("n", "n"), ("lambda", "lambda"), ("tracker", "tracker"), ("seeds", "envs"),
                ("utility_mean", "utility mean"), ("utility_sem", "utility SEM"), ("max_tv", "max TV"),
                ("mean_update_us", "mean update us"), ("p95_update_us", "p95 update us"),
                ("peak_mem_bytes", "peak bytes"), ("belief_entries", "belief entries"),
                ("joint_entries", "joint entries"), ("factored_entries", "factored entries"),
                ("storage_ratio", "storage ratio"), ("events_mean", "events mean"),
            ],
        )
    )
    lines.extend(["", "### Complete tracker/environment rows (all 240 rows)", ""])
    lines.extend(table(ee_raw, [(key, key) for key in ee_raw[0].keys()]))

    lines.extend(
        [
            "",
            "## RQ3 axis 1 — identity attachment / belief source",
            "",
            "### Operational outcomes (complete mechanism-summary columns, part 1)",
            "",
        ]
    )
    lines.extend(
        table(
            mechanism,
            [
                ("variant", "variant"), ("label", "label"), ("belief_source", "belief source"), ("seeds", "seeds"),
                ("snapshots", "snapshots"), ("snapshots_sem", "snapshots SEM"),
                ("assignments", "assignments"), ("assignments_sem", "assignments SEM"),
                ("served", "served"), ("served_sem", "served SEM"),
                ("driver_rejects", "driver rejects"), ("driver_rejects_sem", "driver rejects SEM"),
                ("passenger_rejects", "passenger rejects"), ("passenger_rejects_sem", "passenger rejects SEM"),
                ("driver_accept_rate", "driver accept"), ("driver_accept_rate_sem", "accept SEM"),
                ("served_rate", "served rate"), ("served_rate_sem", "served-rate SEM"),
                ("realized_utility", "utility"), ("realized_utility_sem", "utility SEM"),
            ],
        )
    )
    lines.extend(["", "### Wait, oracle, and belief metrics (complete mechanism-summary columns, part 2)", ""])
    lines.extend(
        table(
            mechanism,
            [
                ("variant", "variant"), ("mean_wait_served", "mean wait served"),
                ("mean_wait_served_sem", "wait SEM"), ("extra_wait_per_snapshot", "extra wait/snapshot"),
                ("extra_wait_per_snapshot_sem", "extra-wait SEM"), ("oracle_match_rate", "oracle match"),
                ("oracle_match_rate_sem", "oracle-match SEM"), ("driver_ptrue", "driver P(true)"),
                ("driver_ptrue_sem", "driver P(true) SEM"), ("driver_rule_acc", "driver rule acc"),
                ("driver_rule_acc_sem", "driver rule SEM"), ("policy_ptrue", "policy P(true)"),
                ("policy_ptrue_sem", "policy P(true) SEM"), ("policy_rule_acc", "policy rule acc"),
                ("policy_rule_acc_sem", "policy rule SEM"), ("passenger_ptrue", "passenger P(true)"),
                ("passenger_ptrue_sem", "passenger P(true) SEM"),
                ("passenger_rule_acc", "passenger rule acc"),
                ("passenger_rule_acc_sem", "passenger rule SEM"),
            ],
        )
    )

    lines.extend(["", "### Supporting closed-loop Persona-v2 summary (all rows)", ""])
    lines.extend(table(closed_loop, [(key, key) for key in closed_loop[0].keys()]))
    lines.extend(["", "### Supporting common-state policy summary (all rows)", ""])
    lines.extend(table(common_state, [(key, key) for key in common_state[0].keys()]))

    lines.extend(["", "## RQ3 axis 2 — closed-form update", "", "### Concentration by within-driver observation count", ""])
    lines.extend(
        table(
            concentration,
            [
                ("observation", "observation"), ("rows", "driver rows"),
                ("ptrue_mean", "P(true) mean"), ("ptrue_sem", "P(true) SEM"),
                ("rule_acc_mean", "rule accuracy mean"), ("rule_acc_sem", "rule accuracy SEM"),
            ],
        )
    )
    lines.extend(["", "### Event-type information gain", ""])
    lines.extend(table(event_gains, [("event_type", "event type"), ("events", "events"), ("mean_rule_acc_gain", "mean rule-accuracy gain"), ("sem_rule_acc_gain", "SEM")]))
    lines.extend(["", "### Complete retained driver posterior event rows (all 667 rows)", ""])
    event_columns = [
        ("seed", "seed"), ("event_index", "event"), ("driver_observation", "driver obs"),
        ("time", "time"), ("driver_id", "driver"), ("request_id", "request"),
        ("action_code", "action"), ("synthetic_declined", "synthetic declined"),
        ("actual_declined", "actual declined"), ("intervened", "intervened"),
        ("event_type", "event type"), ("reason", "reason"),
        ("true_type", "true type"), ("ptrue", "P(true)"), ("rule_acc", "rule acc"),
        ("rule_acc_gain", "rule-acc gain"), ("long_trip", "long"), ("leaves_zone", "leaves zone"),
        ("home_ward", "homeward"), ("surge", "surge"), ("pay", "pay"),
        ("wait_time", "wait"), ("travel_time", "travel"), ("fare", "fare"),
    ]
    lines.extend(table(events, event_columns))

    lines.extend(
        [
            "",
            "## RQ3 axis 3 — centralized dispatch carrier",
            "",
            "This axis is carried by the Concordia centralized-versus-independent-prompting ablation, not by a MaaSSim run. The original four per-backbone L3 JSON files are no longer retained, so this section records only the paper-facing aggregate and does not fabricate raw rows.",
            "",
            "| Metric | Centralized cluster | Independent/decentralized cluster | Reported contrast |",
            "|---|---|---|---|",
            "| Cumulative focal regret at K=5 | 0.60–0.75 | 1.90–2.00 | 3–4x slope ratio |",
            "| Focal payoff | reference cluster | 0.2–0.3 lower | separation on every backbone |",
            "| Coordination | reference cluster | 0.2–0.4 lower | separation on every backbone |",
            "| Social welfare | reference cluster | 1–2 units lower | all five players included |",
            "",
            "## RQ3 axis 4 — E-F frozen beta bonus",
            "",
            f"- Beta: {ef_meta['beta']} ({ef_meta['beta_selection']}).",
            f"- Bonus: {ef_meta['bonus']}.",
            f"- Paired gap: `{json.dumps(ef_meta['paired_gap'], sort_keys=True)}`.",
            f"- Observed assignment changes: {ef_changed}/{ef_compared} assignments.",
            "",
            "### Tracker aggregates (all 2 rows)",
            "",
        ]
    )
    lines.extend(table(ef_summary, [(key, key) for key in ef_summary[0].keys()]))
    lines.extend(["", "### Complete tracker/environment rows (all 20 rows)", ""])
    lines.extend(table(ef_raw, [(key, key) for key in ef_raw[0].keys()]))

    source_paths = [
        E_E / "e_e_maassim_tracker_parity.csv",
        E_E / "e_e_maassim_tracker_parity_summary.csv",
        E_E / "e_e_maassim_tracker_parity_gaps.csv",
        E_E / "e_e_maassim_tracker_parity_metadata.json",
        E_F / "e_f_maassim_bonus_per_seed.csv",
        E_F / "e_f_maassim_bonus_summary.csv",
        E_F / "e_f_maassim_bonus_metadata.json",
        MAASSIM / "maassim_pact_persona_mechanism_summary.csv",
        MAASSIM / "maassim_persona_v2_main_summary.csv",
        MAASSIM / "maassim_common_state_replay_summary.csv",
        *event_sources,
    ]
    lines.extend(["", "## Source integrity", ""])
    integrity = [
        {"path": rel(path), "bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in source_paths
    ]
    lines.extend(table(integrity, [("path", "source"), ("bytes", "bytes"), ("sha256", "SHA-256")]))
    lines.extend(
        [
            "",
            "## Coverage checks",
            "",
            f"- E-E raw rows: {len(ee_raw)}; aggregates: {len(ee_summary)}; paired cells: {len(ee_gaps)}.",
            f"- RQ3 mechanism rows: {len(mechanism)}; closed-loop rows: {len(closed_loop)}; common-state rows: {len(common_state)}.",
            f"- Retained driver posterior events: {len(events)} ({event_gains[0]['events']} rejects, {event_gains[1]['events']} accepts).",
            f"- E-F raw rows: {len(ef_raw)}; aggregates: {len(ef_summary)}.",
            "- Temporary generator smoke outputs are excluded.",
            "- RQ1 LLM conflict-continuum data are intentionally outside this RQ2/RQ3-only document.",
        ]
    )
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "ok",
                "output": rel(OUT),
                "bytes": OUT.stat().st_size,
                "lines": len(lines),
                "ee_rows": len(ee_raw),
                "driver_events": len(events),
                "ef_rows": len(ef_raw),
                "source_files": len(source_paths),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
