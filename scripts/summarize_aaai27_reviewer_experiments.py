"""Summarize PACT AAAI-27 reviewer experiments into one Markdown report."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis" / "aaai27_review"
OUTPUT = DATA / "PACT_AAAI27_REVIEWER_EXPERIMENTS.md"


def read_csv(name: str) -> list[dict[str, str]]:
    path = DATA / name
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def f(value: str | float | int) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def mean(values: Iterable[float]) -> float:
    valid = [value for value in values if math.isfinite(value)]
    return statistics.mean(valid) if valid else float("nan")


def sem(values: Iterable[float]) -> float:
    valid = [value for value in values if math.isfinite(value)]
    return statistics.stdev(valid) / math.sqrt(len(valid)) if len(valid) > 1 else 0.0


def fmt(value: float, digits: int = 3) -> str:
    return "--" if not math.isfinite(value) else f"{value:.{digits}f}"


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add_e_r1(lines: list[str]) -> None:
    rows = read_csv("e_r1_noise_analytic_mixed.csv")
    lines.extend(["", "## E-R1 Likelihood-channel noise robustness (HP-SPGG)", ""])
    if not rows:
        lines.append("**Status:** not completed.")
        return
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["variant"], row["perturbation_type"], row["level"])].append(row)
    seeds = len({row["seed"] for row in rows})
    lines.extend(
        [
            f"**Status:** completed offline outcome-likelihood replay; {len(rows):,} rows, {seeds} paired seeds, zero LLM calls.",
            "",
            "**Infrastructure decision.** The cleaned workspace and all local ZIPs contain no headline c19 calibration tensors, posterior-history NPZs, or per-(episode, step, agent, candidate) token log-scores. The CloudGPT wrapper returns text only and does not request `logprobs`. Therefore the spec's four-backbone token-logprob replay and one-backbone token-logprob rerun are not executable from the retained infrastructure. This delivered experiment perturbs the actual reported Gaussian outcome-likelihood interface on the analytic mixed-backend HP-SPGG surface; it must not be described as a token-logprob result.",
            "",
            "| variant | perturbation | level | regret K=20 | exact-type mass K=20 |",
            "|---|---|---:|---:|---:|",
        ]
    )
    perturbation_order = ["additive_log_noise", "temperature", "top_k"]
    for variant in ("pact", "pact_plus"):
        for perturbation in perturbation_order:
            keys = [key for key in grouped if key[0] == variant and key[1] == perturbation]
            def level_key(key: tuple[str, str, str]) -> tuple[int, float]:
                if key[2] == "full":
                    return (1, float("inf"))
                return (0, float(key[2]))
            for key in sorted(keys, key=level_key):
                values = grouped[key]
                regret = [f(row["cumulative_regret_k20"]) for row in values]
                mass = [f(row["exact_type_mass_k20"]) for row in values]
                lines.append(
                    f"| {variant} | {perturbation} | {key[2]} | "
                    f"{fmt(mean(regret), 4)} $\\pm$ {fmt(sem(regret), 4)} | {fmt(mean(mass), 4)} |"
                )
    lines.extend(["", "### Regret-doubling threshold $\\sigma^*$", ""])
    for variant in ("pact", "pact_plus"):
        base = mean(f(row["cumulative_regret_k20"]) for row in grouped[(variant, "additive_log_noise", "0.0")])
        running = 0.0
        critical: float | None = None
        for sigma in (0.0, 0.1, 0.25, 0.5, 1.0, 2.0):
            value = mean(f(row["cumulative_regret_k20"]) for row in grouped[(variant, "additive_log_noise", str(sigma))])
            running = max(running, value)
            if sigma > 0 and base > 0 and running >= 2 * base and critical is None:
                critical = sigma
        if base <= 1e-12:
            text = "undefined because reference regret is zero; report the absolute curve"
        elif critical is None:
            text = ">$2.0$ (not reached on the tested grid)"
        else:
            text = f"{critical:g} using the monotone regret envelope"
        lines.append(f"- **{variant}:** reference regret {fmt(base, 5)}; $\\sigma^*={text}$. ")
    lines.append("- The HP-SPGG library has four candidates, so requested top-$5$ truncation is exactly the same operation as `full`; only top-$1$ and top-$3$ are nontrivial truncations.")
    lines.append("- PACT+ reference regret is near zero, so its doubling threshold is ratio-unstable; the absolute regret curve and posterior mass should be reported alongside $\\sigma^*$.")


def add_e_r2(lines: list[str]) -> None:
    loo = read_csv("e_r2_loo_analytic_mixed.csv")
    expansion = read_csv("e_r2_expansion_analytic_mixed.csv")
    lines.extend(["", "## E-R2 Persona-library misspecification (HP-SPGG)", ""])
    if not loo:
        lines.append("**Status:** not completed.")
        return
    lines.extend(
        [
            f"**Status:** PACT-family offline outcome-likelihood LOO completed ({sum(row['status'].startswith('completed') for row in loo)} rows). Prompt-baseline LOO was not run because retained A-ToM/LLM-belief trajectories are absent and those baselines do not share PACT's discrete tracker library; {sum(row['status'].startswith('not_run') for row in loo)} explicit not-run rows are retained rather than fabricated.",
            "",
            "| excluded persona | variant | LOO regret | in-library regret | degradation | final entropy | modal proxy type |",
            "|---|---|---:|---:|---:|---:|---|",
        ]
    )
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in loo:
        if row["status"].startswith("completed"):
            grouped[(row["excluded_persona"], row["variant"])].append(row)
    for key, values in sorted(grouped.items()):
        modes = Counter(row["argmax_persona"] for row in values)
        modal = modes.most_common(1)[0][0].replace("|", " / ")
        lines.append(
            f"| {key[0]} | {key[1]} | {fmt(mean(f(r['cumulative_regret_k20']) for r in values), 4)} | "
            f"{fmt(mean(f(r['in_library_reference_regret_k20']) for r in values), 4)} | "
            f"{fmt(mean(f(r['regret_degradation']) for r in values), 4)} | "
            f"{fmt(mean(f(r['final_entropy']) for r in values), 4)} | {modal} |"
        )
    if expansion:
        lines.extend(
            [
                "",
                "### Library expansion",
                "",
                "| distractors | variant | regret K=20 | exact-type mass | final entropy |",
                "|---:|---|---:|---:|---:|",
            ]
        )
        grouped_exp: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
        for row in expansion:
            grouped_exp[(row["distractor_count"], row["variant"])].append(row)
        for key, values in sorted(grouped_exp.items(), key=lambda item: (int(item[0][0]), item[0][1])):
            lines.append(
                f"| {key[0]} | {key[1]} | {fmt(mean(f(r['cumulative_regret_k20']) for r in values), 4)} | "
                f"{fmt(mean(f(r['exact_type_mass_k20']) for r in values), 4)} | "
                f"{fmt(mean(f(r['final_entropy']) for r in values), 4)} |"
            )
    lines.extend(
        [
            "",
            "**Convex-mixture decision:** not used as a prompt-level persona experiment. The current HP-SPGG player behavior is generated from fixed reward templates rather than a continuously mixed persona prompt. The earlier analytic reward-mixture diagnostic is therefore not promoted as satisfying the reviewer's prompt-level convex-mixture request.",
        ]
    )


def add_e_r3(lines: list[str]) -> None:
    rows = read_csv("e_r3_menu_corruption.csv")
    lines.extend(["", "## E-R3 SOTOPIA intent-menu corruption", ""])
    expected = 4 * 4 * 30
    if not rows:
        lines.append(f"**Status:** live suite running or not started; 0/{expected} episode rows available.")
        return
    lines.append(f"**Status:** {len(rows)}/{expected} episode rows checkpointed.")
    failures = sum(int(row.get("generation_failures", 0) or 0) for row in rows)
    calls = sum(int(row.get("generation_calls", 0) or 0) for row in rows)
    events = sum(int(row.get("corruption_events", 0) or 0) for row in rows)
    updates = sum(int(row.get("corruption_updates", 0) or 0) for row in rows)
    lines.append(
        f"Generation failures: {failures}/{calls}; realised corruption events: {events}/{updates} eligible updates. "
        "The experiment uses the corrected Observation.last_turn update path; the pre-spec adapter's inbox path produced zero posterior updates and is documented below."
    )
    grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in rows:
        grouped[(row["family"], row["p"])].append(f(row["focal_score"]))
    historical_best = {
        "craigslist_bargains": 2.7605,
        "revenge_plot": 3.2000,
        "donate_funds": 3.3860,
    }
    lines.extend(
        [
            "",
            "| family | p | episodes | focal score | delta vs p=0 | delta vs historical best baseline |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for (family, p), values in sorted(grouped.items(), key=lambda item: (item[0][0], float(item[0][1]))):
        reference = mean(grouped.get((family, "0.0"), grouped.get((family, "0"), [])))
        current = mean(values)
        lines.append(
            f"| {family} | {p} | {len(values)} | {fmt(current, 4)} $\\pm$ {fmt(sem(values), 4)} | "
            f"{fmt(current - reference, 4) if math.isfinite(reference) else '--'} | "
            f"{fmt(current - historical_best[family], 4)} |"
        )
    lines.extend(["", "### Advantage-disappearance threshold $p^*$", ""])
    for family in sorted(historical_best):
        available = sorted(
            ((float(p), mean(values)) for (candidate_family, p), values in grouped.items() if candidate_family == family),
            key=lambda item: item[0],
        )
        threshold = next((p for p, score in available if score <= historical_best[family]), None)
        if threshold is None and len(available) == 4:
            text = ">$0.3$ (not reached)"
        elif threshold is None:
            text = "pending incomplete p grid"
        else:
            text = f"{threshold:g}"
        lines.append(
            f"- **{family}:** historical GPT-5.4-nano best-alternative mean {historical_best[family]:.4f}; $p^*={text}$."
        )
    lines.extend(
        [
            "",
            "**Projection-accuracy boundary:** per-family projection accuracy remains non-identifiable because SOTOPIA has no native labels for the project's four keyword classes. E-R3 measures intervention sensitivity, not projection accuracy.",
        ]
    )


def add_e_r4(lines: list[str]) -> None:
    rows = read_csv("e_r4_planner_concordia.csv")
    lines.extend(["", "## E-R4 Planner sensitivity (compact Concordia)", ""])
    if not rows:
        lines.append("**Status:** not completed.")
        return
    by_config: dict[tuple[str, str], dict[str, dict[str, str]]] = defaultdict(dict)
    for row in rows:
        by_config[(row["substrate"], row["config"])][row["solver"]] = row
    lines.extend(
        [
            f"**Status:** completed; {len(by_config)} configurations, {len(rows)} aggregate rows, zero LLM calls.",
            "",
            "| solver | configs | mean focal gap vs exact | worst gap | exact ties | mean wall-time ms |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for solver in ("exact_enumeration", "greedy_br_1pass", "iterated_br_3pass"):
        gaps: list[float] = []
        wall: list[float] = []
        for data in by_config.values():
            exact = f(data["exact_enumeration"]["focal_payoff"])
            gaps.append(f(data[solver]["focal_payoff"]) - exact)
            wall.append(f(data[solver]["walltime_ms"]))
        lines.append(
            f"| {solver} | {len(gaps)} | {fmt(mean(gaps), 4)} | {fmt(min(gaps), 4)} | "
            f"{sum(abs(gap) < 1e-12 for gap in gaps)} | {fmt(mean(wall), 4)} |"
        )
    lines.extend(["", "### By substrate", "", "| substrate | solver | configs | mean focal gap | worst gap |", "|---|---|---:|---:|---:|"])
    substrates = sorted({key[0] for key in by_config})
    for substrate in substrates:
        configs = [data for (candidate_substrate, _), data in by_config.items() if candidate_substrate == substrate]
        for solver in ("greedy_br_1pass", "iterated_br_3pass"):
            gaps = [
                f(data[solver]["focal_payoff"]) - f(data["exact_enumeration"]["focal_payoff"])
                for data in configs
            ]
            lines.append(
                f"| {substrate} | {solver} | {len(configs)} | {fmt(mean(gaps), 4)} | {fmt(min(gaps), 4)} |"
            )
    lines.extend(
        [
            "",
            "**Definition:** one-pass BR updates each agent once in deterministic order against the current joint action; three-pass BR repeats that sweep three times. Pub agents optimise own analytic pub payoff. In haggling, buyer and seller optimise their own payoff sequentially. Exact enumeration maximises the reported focal objective. Tracker/case information is fixed before solver timing.",
            "",
            "**HP-SPGG n=5 half:** not run. The spec marks it contingent on remaining budget after E-R1--E-R3; the active budget was assigned to the 480-episode E-R3 live suite and E-R0 cache/live reconstruction. The complete zero-call Concordia half is delivered.",
        ]
    )


def add_e_r0(lines: list[str]) -> None:
    rows = read_csv("e_r0_maassim_per_seed.csv")
    lines.extend(["", "## E-R0 MaaSSim per-seed paired rows", ""])
    expected = (8 + 9 + 9) * 5
    if not rows:
        lines.append(f"**Status:** cache replay running or unavailable; 0/{expected} rows available.")
        return
    llm_rows = [row for row in rows if int(row.get("llm_calls", 0) or 0) > 0]
    calls = sum(int(row["llm_calls"]) for row in llm_rows)
    hits = sum(int(row["cache_hits"]) for row in llm_rows)
    current_cache_path = ROOT / "analysis" / "courier_dispatch_maassim" / "maassim_llm_replay_cache.json"
    current_cache_keys = 0
    if current_cache_path.exists():
        current_cache_keys = len(json.loads(current_cache_path.read_text(encoding="utf-8")))
    historical_cache_keys: int | None = None
    bundle = ROOT / "packaged_results" / "pact_figures_data_20260711.zip"
    if bundle.exists():
        try:
            with zipfile.ZipFile(bundle) as archive:
                member = "pact_figures_data_20260711/data/analysis/courier_dispatch_maassim/maassim_llm_replay_cache.json"
                historical_cache_keys = len(json.loads(archive.read(member)))
        except (KeyError, zipfile.BadZipFile, json.JSONDecodeError):
            historical_cache_keys = None
    lines.append(
        f"**Status:** {len(rows)}/{expected} unique (scenario, variant, seed) rows. Replay decision cache hit rate during this run: "
        f"{hits}/{calls} ({hits / max(calls, 1):.3f}); live-filled decisions: {calls - hits}. "
        f"Current cache keys: {current_cache_keys}; pre-spec bundle cache keys: "
        f"{historical_cache_keys if historical_cache_keys is not None else 'unavailable'}."
    )
    lines.extend(
        [
            "",
            "| scenario | variant | utility | rejects | wait |",
            "|---|---|---:|---:|---:|",
        ]
    )
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["scenario"], row["variant"])].append(row)
    for key, values in sorted(grouped.items()):
        utility = [f(row["utility"]) for row in values]
        rejects = [f(row["rejects"]) for row in values]
        wait = [f(row["wait"]) for row in values]
        lines.append(
            f"| {key[0]} | {key[1]} | {fmt(mean(utility), 3)} $\\pm$ {fmt(sem(utility), 3)} | "
            f"{fmt(mean(rejects), 3)} $\\pm$ {fmt(sem(rejects), 3)} | "
            f"{fmt(mean(wait), 3)} $\\pm$ {fmt(sem(wait), 3)} |"
        )


def add_delivery(lines: list[str]) -> None:
    lines.extend(["", "## Deliverables and integrity", "", "| file | rows/bytes | SHA-256 |", "|---|---:|---|"])
    names = [
        "e_r1_noise_analytic_mixed.csv",
        "e_r2_loo_analytic_mixed.csv",
        "e_r2_expansion_analytic_mixed.csv",
        "e_r3_menu_corruption.csv",
        "e_r4_planner_concordia.csv",
        "e_r0_maassim_per_seed.csv",
    ]
    for name in names:
        path = DATA / name
        if path.exists():
            rows = max(0, len(path.read_text(encoding="utf-8").splitlines()) - 1)
            lines.append(f"| `{path.relative_to(ROOT).as_posix()}` | {rows} rows | `{file_sha(path)}` |")
        else:
            lines.append(f"| `{path.relative_to(ROOT).as_posix()}` | missing/running | -- |")
    raw_files = sorted((DATA / "e_r3_raw").glob("*.json")) if (DATA / "e_r3_raw").exists() else []
    raw_episodes = 0
    for path in raw_files:
        try:
            raw_episodes += len(json.loads(path.read_text(encoding="utf-8")).get("episodes", []))
        except json.JSONDecodeError:
            pass
    lines.append(f"| `analysis/aaai27_review/e_r3_raw/*.json` | {raw_episodes} checkpointed episodes in {len(raw_files)} files | per-file hashes available from package manifest |")


def main() -> None:
    lines = [
        "# PACT AAAI-27 评审响应实验执行报告",
        "",
        "版本 2026-07-14。对应 review 的 logprob/likelihood 鲁棒性、projection 敏感性、persona 库误设与 planner 敏感性问题。",
        "",
        "## Executive status",
        "",
        "| experiment | status source |",
        "|---|---|",
        "| E-R1 | `e_r1_noise_analytic_mixed.csv` (actual outcome-likelihood interface; token-logprob path unavailable) |",
        "| E-R2 | `e_r2_loo_analytic_mixed.csv`, `e_r2_expansion_analytic_mixed.csv` |",
        "| E-R3 | `e_r3_menu_corruption.csv` + per-cell raw checkpoints |",
        "| E-R4 | `e_r4_planner_concordia.csv` |",
        "| E-R0 | `e_r0_maassim_per_seed.csv` reconstructed from replay cache |",
        "",
        "## Deadline matrix",
        "",
        "| item | spec deadline | execution status |",
        "|---|---|---|",
        "| E-R1 data | 2026-07-22 | completed 2026-07-14 on the actual outcome-likelihood interface; requested token-logprob route blocked by absent data/API |",
        "| E-R2 data | 2026-07-24 | PACT-family LOO/expansion completed 2026-07-14; prompt-baseline comparison explicitly blocked |",
        "| E-R3 data | 2026-07-25 | checkpointed live run; final status below |",
        "| E-R4 Concordia | 2026-07-25 | completed 2026-07-14 |",
        "| E-R0 | same window | cache-first/live-fill checkpointed run; final status below |",
        "| full text | 2026-07-28 | data/report artifact prepared for integration |",
        "| supplement | 2026-07-31 | raw checkpoints and full CSVs retained |",
        "",
        "## Infrastructure audit",
        "",
        "- No retained `.npy`/`.npz` headline calibration tensor, posterior history, or raw token log-score cache was found in the workspace or 56 local ZIP archives.",
        "- The CloudGPT wrapper does not request or expose token logprobs/top-k logprobs. Azure authentication and a GPT-5.4-nano text call were verified on 2026-07-14.",
        "- Official SOTOPIA data were restored from public `cmu-lti/sotopia` (`benchmark_agents.json`, `sotopia_episodes_v1_hf.jsonl`), and a Python 3.12 SOTOPIA 0.1.5 environment was rebuilt.",
        "- Concordia upstream was restored and compact analytic payoff imports were verified.",
        "- MaaSSim scenario aggregate source CSVs were deleted, but queue snapshots, persona maps, and the direct-dispatch replay cache remain, allowing deterministic per-seed reconstruction.",
        "- Critical SOTOPIA audit finding: the pre-spec adapter read partner evidence from the agent inbox, but SOTOPIA 0.1.5 delivers it in `Observation.last_turn`; published-style runs therefore recorded zero numeric posterior updates. The update path was corrected before E-R3, and every eligible update/corruption event is now audited in raw output.",
    ]
    add_e_r1(lines)
    add_e_r2(lines)
    add_e_r3(lines)
    add_e_r4(lines)
    add_e_r0(lines)
    lines.extend(
        [
            "",
            "## Optional conflict-p2 completion",
            "",
            "**Status:** not run. This was explicitly optional rebuttal ammunition; resources were prioritised to the required E-R3 live corruption grid and E-R0 per-seed reconstruction.",
        ]
    )
    add_delivery(lines)
    lines.extend(
        [
            "",
            "## Claim-safe conclusions",
            "",
            "1. E-R1 is evidence about the reported Gaussian outcome-likelihood implementation, not token-logprob robustness; the requested token-logprob claim remains untested because the interface and raw data do not exist.",
            "2. E-R2 quantifies PACT-family discrete-library misspecification only. A-ToM/LLM-belief comparative degradation is unavailable without new live trajectories and a shared discrete-library definition.",
            "3. E-R3 is the first valid recurrent-surrogate sensitivity run after fixing the zero-update adapter bug. It bounds intervention sensitivity but cannot provide projection accuracy.",
            "4. E-R4 cleanly separates tracker from planner under analytic payoffs; agent-wise BR can converge to a low-focal equilibrium even when exact focal enumeration is cheap.",
            "5. E-R0 rows are reconstructed from the retained cache and support paired SEM; the CSV records cache-hit counts so any live cache misses are visible.",
        ]
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"saved={OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
