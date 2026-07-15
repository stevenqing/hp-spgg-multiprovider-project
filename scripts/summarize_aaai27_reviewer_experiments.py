"""Summarize PACT AAAI-27 reviewer experiments into one Markdown report."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
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


def sotopia_historical_comparators() -> dict[str, float]:
    path = ROOT / "config" / "aaai27_sotopia_historical_comparators.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    values = {row["family"]: f(row["mean"]) for row in rows}
    expected = {"craigslist_bargains", "donate_funds", "revenge_plot"}
    if set(values) != expected or len(rows) != len(expected):
        raise ValueError(f"invalid SOTOPIA comparator grid in {path}: {sorted(values)}")
    return values


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
            "The requested five-seed grid was expanded to 500 paired seeds because reference regret is near zero. Environment/policy randomness is shared across perturbation levels, while likelihood-noise randomness uses a separate reproducible stream so the intervention cannot change the policy RNG sequence.",
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
        base = mean(
            f(row["cumulative_regret_k20"])
            for row in grouped[(variant, "additive_log_noise", "0.0")]
        )
        running = 0.0
        critical: float | None = None
        for sigma in (0.0, 0.1, 0.25, 0.5, 1.0, 2.0):
            value = mean(f(row["cumulative_regret_k20"]) for row in grouped[(variant, "additive_log_noise", str(sigma))])
            running = max(running, value)
            if sigma > 0 and base > 0 and running >= 2 * base and critical is None:
                critical = sigma
        if base <= 1e-12:
            threshold_clause = "$\\sigma^*$ is undefined because reference regret is zero; report the absolute curve"
        elif critical is None:
            threshold_clause = "$\\sigma^*>2.0$ (not reached on the tested grid)"
        else:
            threshold_clause = f"$\\sigma^*={critical:g}$ using the monotone regret envelope"
        lines.append(f"- **{variant}:** reference regret {fmt(base, 5)}; {threshold_clause}.")
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
    lines.extend(
        [
            "",
            "The in-library regret floor is nearly zero, so relative degradation ratios are unstable. Small negative degradation means that the finite-seed LOO replay happened to incur slightly less regret; it is not evidence that excluding a true persona is generally beneficial.",
        ]
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
    expected_family_counts = {
        (p, family): count
        for p in ("0.0", "0.1", "0.2", "0.3")
        for family, count in (("craigslist_bargains", 80), ("donate_funds", 20), ("revenge_plot", 20))
    }
    observed_family_counts = Counter((row["p"], row["family"]) for row in rows)
    grid_complete = len(rows) == expected and observed_family_counts == Counter(expected_family_counts)
    lines.append(
        f"**Status:** {len(rows)}/{expected} episode rows checkpointed"
        f"{' (complete grid).' if grid_complete else ' (partial grid; thresholds withheld).'}"
    )
    lines.append(
        "Planned design per p: 30 official target cases repeated four times (120 episodes): 20 craigslist cases (80 episodes), five donate cases (20), and five revenge cases (20). Replicates are independent provider generations, not deterministic resampling of a stored trajectory."
    )
    lines.append(
        "Displayed score SEMs are descriptive episode-row SEMs. Confirmatory uncertainty should cluster or bootstrap by `combo_pk` because each official case contributes four generations; the episode-level CSV retains both case and replicate identifiers."
    )
    lines.append(
        "The spec-mandated legacy column `focal_score` equals the arithmetic mean of `episode.overall.agent_1` and `episode.overall.agent_2` in symmetric SOTOPIA self-play; it is not an agent-1-only focal reward. Historical comparators use the same formula."
    )
    failures = sum(int(row.get("generation_failures", 0) or 0) for row in rows)
    calls = sum(int(row.get("generation_calls", 0) or 0) for row in rows)
    events = sum(int(row.get("corruption_events", 0) or 0) for row in rows)
    updates = sum(int(row.get("corruption_updates", 0) or 0) for row in rows)
    lines.append(
        f"Caught provider-call generation fallbacks: {failures}/{calls}; triggered permutation events: {events}/{updates} eligible updates. "
        "The experiment uses the corrected Observation.last_turn update path; the pre-spec adapter's inbox path produced zero posterior updates and is documented below. This counter catches provider exceptions only. The stored schema does not separately count malformed/invalid/missing action fields that the action parser defaults, or missing/non-numeric evaluator dimensions that score normalization maps to zero; hence zero provider fallbacks is not a zero-schema-default guarantee."
    )
    lines.append(
        "`corruption_events` counts seeded permutation triggers. If an utterance yields tied keyword increments (especially an all-zero vector), permuting indices can leave the numeric vector unchanged; the recorded rate is therefore a trigger rate, not an effective-vector-change rate."
    )
    lines.append(
        "Release cleaning retained already-clean checkpoints, discarded every accepted episode with a caught provider-call fallback, and reran the affected case under up to five provider attempts per call and five whole-episode attempts at concurrency 2--4. The legacy checkpoint schema did not retain discarded attempts or transient failure history, so final zero counts describe accepted episodes rather than provider reliability; retry settings are documented from the execution log, not recovered from each raw record. The final validator checks all 16 raw cells as well as the aggregate CSV."
    )
    lines.append(
        "After completion, all 16 cells were migrated to checkpoint schema v2 only after legacy episode metadata matched the intended model, evaluator, strategy, corruption level/seed, and target IDs. Each raw file now carries an immutable run signature with turns and SHA-256 input hashes; this migration does not recreate the discarded legacy attempt history."
    )
    lines.append(
        "Case and replicate IDs are paired across p, but the CloudGPT chat endpoint exposes no sampling-seed control; LLM generations are therefore not pathwise coupled. Paired tests reduce case-composition variance but still include provider-generation and judge variance, so E-R3 is a sensitivity bound rather than a pure causal projection ablation."
    )
    lines.append(
        "The corruption RNG is SHA-256-derived from the same (base seed, case, agent, replicate) tuple at every p. It is fully reproducible, but the same stream supplies both trigger draws and conditional permutation shuffles, so masks are not guaranteed to be nested across p. LLM generation/judge randomness is also uncoupled. The best-alternative comparator is a retained historical GPT-nano aggregate, not a contemporaneous rerun under the same judge draws; p* below is therefore an operational threshold against that retained reference, not a strictly causal crossover estimate."
    )
    lines.append(
        "Comparator provenance: `config/aaai27_sotopia_historical_comparators.csv`, derived from the GPT-5.4-nano per-codename table in `analysis/sotopia_tuned_all70_full_report.md`. Craigslist aggregates its four five-episode codenames before selecting the best among A-ToM-1, ECON-BNE, llm-belief, and llm-greedy; donate and revenge each have one five-episode codename. LLM-PSRL was later recovered only as a cross-backbone family aggregate in `packaged_results/sotopia_font13_recovered_aggregates.json`, so it cannot be included in a GPT-nano-only comparator. The original episode JSONs listed by that report are no longer retained."
    )
    lines.append(
        "The positive family margins quoted for the original figure average all four backbones, whereas this corruption suite follows the spec's one-backbone GPT-nano design. The GPT-specific operational p* is therefore a different estimand and must not be substituted for the cross-backbone historical margin."
    )
    grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
    by_episode: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    for row in rows:
        grouped[(row["family"], row["p"])].append(f(row["focal_score"]))
        by_episode[(row["family"], row["p"])][row["episode_id"]] = f(row["focal_score"])
    historical_best = sotopia_historical_comparators()
    lines.extend(
        [
            "",
            "| p | episodes | eligible updates | permutation triggers | trigger rate | generation calls | provider-exception fallbacks |",
            "|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for p in sorted({row["p"] for row in rows}, key=float):
        level_rows = [row for row in rows if row["p"] == p]
        level_updates = sum(int(row.get("corruption_updates", 0) or 0) for row in level_rows)
        level_events = sum(int(row.get("corruption_events", 0) or 0) for row in level_rows)
        level_calls = sum(int(row.get("generation_calls", 0) or 0) for row in level_rows)
        level_failures = sum(int(row.get("generation_failures", 0) or 0) for row in level_rows)
        lines.append(
            f"| {p} | {len(level_rows)} | {level_updates} | {level_events} | "
            f"{fmt(level_events / max(level_updates, 1), 4)} | {level_calls} | {level_failures} |"
        )
    lines.extend(
        [
            "",
            "| family | p | episodes | focal score | paired delta vs p=0 | delta vs historical four-baseline best |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for (family, p), values in sorted(grouped.items(), key=lambda item: (item[0][0], float(item[0][1]))):
        current = mean(values)
        baseline = by_episode.get((family, "0.0"), by_episode.get((family, "0"), {}))
        paired = [score - baseline[episode_id] for episode_id, score in by_episode[(family, p)].items() if episode_id in baseline]
        paired_text = f"{fmt(mean(paired), 4)} $\\pm$ {fmt(sem(paired), 4)}" if paired else "--"
        lines.append(
            f"| {family} | {p} | {len(values)} | {fmt(current, 4)} $\\pm$ {fmt(sem(values), 4)} | "
            f"{paired_text} | "
            f"{fmt(current - historical_best[family], 4)} |"
        )
    lines.extend(["", "### Advantage-disappearance threshold $p^*$", ""])
    for family in sorted(historical_best):
        available = sorted(
            ((float(p), mean(values)) for (candidate_family, p), values in grouped.items() if candidate_family == family),
            key=lambda item: item[0],
        )
        threshold = next((p for p, score in available if score <= historical_best[family]), None) if grid_complete else None
        if not grid_complete:
            threshold_clause = "$p^*$ pending an incomplete p grid"
        elif threshold is None:
            threshold_clause = "$p^*>0.3$ (not reached)"
        else:
            threshold_clause = f"$p^*={threshold:g}$"
        lines.append(
            f"- **{family}:** historical GPT-5.4-nano four-baseline-best mean {historical_best[family]:.4f}; {threshold_clause}."
        )
    p0_advantages = {
        family: mean(grouped.get((family, "0.0"), grouped.get((family, "0"), []))) - reference
        for family, reference in historical_best.items()
    }
    if grid_complete and p0_advantages and all(value <= 0.0 for value in p0_advantages.values()):
        lines.append(
            "- The corrected GPT-nano $p=0$ run has no positive margin against the retained four-baseline comparator in any selected family. Thus the spec's conditional 'advantage disappearance' test is not activated: $p^*=0$ is bookkeeping for an absent initial advantage, not evidence that $p=0.1$ corruption caused a crossover. Interpret the within-run paired deltas instead."
        )
        lines.append(
            "- Across the tested grid, family-level paired mean changes are non-monotone and of the same order as their descriptive SEMs. Together with uncoupled provider/judge randomness, this supports no monotone causal dose-response claim for menu corruption."
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
    lines.append(
        f"**Status:** {len(rows)}/{expected} unique (scenario, variant, seed) rows. Replay decision cache hit rate during this run: "
        f"{hits}/{calls} ({hits / max(calls, 1):.3f}); live-filled decisions: {calls - hits}. "
        f"Current cache keys after live-fill: {current_cache_keys}. The pre-spec package intentionally excluded filenames containing `cache`, and no historical cache copy was found in the pre-experiment audit of 56 retained ZIPs."
    )
    lines.append("")
    lines.append(
        "**Provenance:** the original scenario-suite per-seed CSVs were deleted during cleanup. These rows are a deterministic state/persona replay with the current v7 assignment-ID runner, reusing matching cached decisions and live-filling missing current-schema keys. They are suitable for new paired analyses but are not byte-for-byte recovery of the deleted original run; compare aggregate means before replacing published SEMs."
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

    retained_path = ROOT / "analysis" / "courier_dispatch_maassim" / "maassim_llm_scenario_suite_detail.csv"
    retained: list[dict[str, str]] = []
    if retained_path.exists():
        with retained_path.open(newline="", encoding="utf-8") as handle:
            retained = list(csv.DictReader(handle))
    reconstructed = {
        key: {
            "utility": mean([f(row["utility"]) for row in values]),
            "rejects": mean([f(row["rejects"]) for row in values]),
            "served": mean([f(row["served"]) for row in values]),
        }
        for key, values in grouped.items()
    }
    comparisons: list[dict[str, Any]] = []
    for old in retained:
        key = (old["scenario_id"], old["policy"])
        if key not in reconstructed:
            continue
        new = reconstructed[key]
        comparisons.append(
            {
                "scenario": key[0],
                "variant": key[1],
                "old_utility": f(old["utility"]),
                "new_utility": new["utility"],
                "delta": new["utility"] - f(old["utility"]),
                "old_rejects": f(old["driver_rejects"]),
                "new_rejects": new["rejects"],
                "old_served": f(old["served"]),
                "new_served": new["served"],
            }
        )
    if comparisons:
        exact = sum(
            abs(row["delta"]) < 1e-9
            and abs(row["new_rejects"] - row["old_rejects"]) < 1e-9
            and abs(row["new_served"] - row["old_served"]) < 1e-9
            for row in comparisons
        )
        max_delta = max(abs(row["delta"]) for row in comparisons)
        lines.extend(
            [
                "",
                f"### Retained aggregate cross-check ({exact}/{len(comparisons)} exact cells; max |utility delta|={fmt(max_delta, 3)})",
                "",
                "Only non-exact scenario-policy cells are listed. Exact matching of an aggregate does not prove recovery of the original seed ordering; non-exact cells confirm that live-fill cannot be represented as original raw data.",
                "",
                "| scenario | variant | retained utility | reconstructed utility | delta | retained/reconstructed rejects | retained/reconstructed served |",
                "|---|---|---:|---:|---:|---:|---:|",
            ]
        )
        for row in comparisons:
            if (
                abs(row["delta"]) < 1e-9
                and abs(row["new_rejects"] - row["old_rejects"]) < 1e-9
                and abs(row["new_served"] - row["old_served"]) < 1e-9
            ):
                continue
            lines.append(
                f"| {row['scenario']} | {row['variant']} | {fmt(row['old_utility'], 3)} | {fmt(row['new_utility'], 3)} | "
                f"{fmt(row['delta'], 3)} | {fmt(row['old_rejects'], 1)} / {fmt(row['new_rejects'], 1)} | "
                f"{fmt(row['old_served'], 1)} / {fmt(row['new_served'], 1)} |"
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
    raw_hash_manifest = "\n".join(
        f"{path.relative_to(ROOT).as_posix()} {file_sha(path)}" for path in raw_files
    )
    raw_set_hash = hashlib.sha256(raw_hash_manifest.encode("utf-8")).hexdigest()
    lines.append(
        f"| `analysis/aaai27_review/e_r3_raw/*.json` | {raw_episodes} checkpointed episodes in {len(raw_files)} files | raw-set manifest `{raw_set_hash}`; per-file hashes in package manifest |"
    )


def main() -> None:
    input_manifest_path = ROOT / "config" / "aaai27_sotopia_input_manifest.csv"
    with input_manifest_path.open(newline="", encoding="utf-8") as handle:
        input_manifest = {row["name"]: row for row in csv.DictReader(handle)}
    expected_inputs = {"benchmark_agents.json", "sotopia_episodes_v1_hf.jsonl", "sotopia_hard_cases_cache.json"}
    if set(input_manifest) != expected_inputs:
        raise ValueError(f"invalid SOTOPIA input manifest: {sorted(input_manifest)}")
    benchmark_hash = input_manifest["benchmark_agents.json"]["sha256"]
    episodes_hash = input_manifest["sotopia_episodes_v1_hf.jsonl"]["sha256"]
    hard_cache_hash = input_manifest["sotopia_hard_cases_cache.json"]["sha256"]
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
        "| E-R0 | `e_r0_maassim_per_seed.csv` cache-first/live-fill reconstruction (not recovered original rows) |",
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
        f"- SOTOPIA input SHA-256 (canonical `config/aaai27_sotopia_input_manifest.csv`): `benchmark_agents.json` `{benchmark_hash}`; `sotopia_episodes_v1_hf.jsonl` `{episodes_hash}`; reconstructed 70-case cache `{hard_cache_hash}`. The 180 MB public JSONL is referenced by URL/hash rather than duplicated in the reviewer ZIP.",
        "- Concordia upstream was restored and compact analytic payoff imports were verified.",
        "- The original MaaSSim scenario-suite per-seed rows were deleted. The aggregate detail CSV, queue snapshots, persona maps, and a locally augmented direct-dispatch replay cache remain, allowing a provenance-labelled per-seed reconstruction and aggregate cross-check.",
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
            "5. E-R0 is a cache-first/live-fill reconstruction for new paired analyses, not recovery of deleted original rows. Cache-hit counts and the retained-aggregate cross-check expose the provenance; these rows must not silently replace published original-run SEMs.",
        ]
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"saved={OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
