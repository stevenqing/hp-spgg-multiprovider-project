"""Run the zero-provider E-G HP-SPGG analytic component knock-out ladder."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from llm_hpgg.coordinator import (
    CoordinatorState,
    expected_profile_scores,
    oracle_profile,
    posterior_expected_profile_scores,
    update_posterior,
)
from llm_hpgg.environment import (
    build_reward_tensor,
    load_calibration,
    rewards_for_types,
    save_calibration,
    welfare_for_types,
)


OUT_DIR = ROOT / "analysis" / "e_g_hp_spgg_component_ladder"
CALIBRATION = OUT_DIR / "calibration_analytic_n3.npy"
LONG_OUT = OUT_DIR / "e_g_hp_spgg_component_ladder_long.csv"
SUMMARY_OUT = OUT_DIR / "e_g_hp_spgg_component_ladder_summary.csv"
METADATA_OUT = OUT_DIR / "e_g_hp_spgg_component_ladder_metadata.json"
NPZ_OUT = OUT_DIR / "e_g_hp_spgg_component_ladder.npz"
REPORT_OUT = OUT_DIR / "e_g_hp_spgg_component_ladder.md"

N = 3
TYPE_COUNT = 4
K = 20
BETA = 0.25
SIGMA = 0.08
SEEDS = tuple(range(10))
T95_DF9 = 2.2621571627409915
VARIANTS = ("full", "minus_bonus", "minus_update", "minus_identity", "minus_dispatch")
LABELS = {
    "full": "Full PACT+",
    "minus_bonus": "- bonus",
    "minus_update": "- update",
    "minus_identity": "- identity",
    "minus_dispatch": "- dispatch",
}
DERANGEMENTS = {
    0: np.asarray([1, 2, 0], dtype=int),
    1: np.asarray([2, 0, 1], dtype=int),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mean_sem(values: np.ndarray) -> tuple[float, float]:
    return float(values.mean()), float(values.std(ddof=1) / math.sqrt(len(values)))


def ensure_calibration(force: bool = False) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if force or not CALIBRATION.exists():
        bundle = build_reward_tensor(n=N, backend="mixed", samples=3, seed=0, trap=False)
        save_calibration(bundle, CALIBRATION)
    loaded = load_calibration(CALIBRATION)
    reward_tensor = np.asarray(loaded["reward_tensor"], dtype=float)
    action_profiles = np.asarray(loaded["action_profiles"], dtype=float)
    if reward_tensor.shape != (N, TYPE_COUNT, 125) or action_profiles.shape != (125, N):
        raise AssertionError(
            f"unexpected analytic calibration shapes: rewards={reward_tensor.shape}, actions={action_profiles.shape}"
        )


def attached_state(state: CoordinatorState, derangement: np.ndarray) -> CoordinatorState:
    """Planning-only view that attaches each decision slot to another slot's posterior."""
    return CoordinatorState(
        posterior=state.posterior[derangement].copy(),
        joint_type_profiles=state.joint_type_profiles,
        joint_posterior=state.joint_posterior,
        reward_tensor=state.reward_tensor,
        action_profiles=state.action_profiles,
        beta=state.beta,
    )


def action_lookup(action_profiles: np.ndarray) -> tuple[np.ndarray, dict[tuple[float, ...], int]]:
    values = np.asarray(sorted({float(value) for value in action_profiles.ravel()}), dtype=float)
    lookup = {tuple(float(value) for value in profile): index for index, profile in enumerate(action_profiles)}
    return values, lookup


def sample_profile(posterior: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    return np.asarray(
        [rng.choice(posterior.shape[1], p=posterior[player]) for player in range(posterior.shape[0])],
        dtype=int,
    )


def decentralized_action(
    local_states: list[CoordinatorState],
    rng: np.random.Generator,
    action_profiles: np.ndarray,
    beta: float,
) -> int:
    """Independent profile samples and own-utility best responses under common public beliefs.

    Each actor samples a full type profile from its own copy of the public-history
    posterior. Under reward locality, only that sample's own-type component enters
    the actor's own reward. Other agents' simultaneous actions are integrated out
    uniformly, matching the existing finite decentralized HP-SPGG semantics. The
    local uncertainty bonus retains the own-agent disagreement term; the global
    joint-action-spread term is unavailable once no joint action is selected.
    """
    action_values, lookup = action_lookup(action_profiles)
    chosen_values = np.zeros(len(local_states), dtype=float)
    for actor, state in enumerate(local_states):
        sampled_types = sample_profile(state.posterior, rng)
        sampled_own_type = int(sampled_types[actor])
        scores = np.full(len(action_values), -np.inf, dtype=float)
        for action_index, action_value in enumerate(action_values):
            profile_indices = np.where(np.isclose(action_profiles[:, actor], action_value))[0]
            own_rewards = state.reward_tensor[actor, sampled_own_type, profile_indices]
            base = float(np.mean(own_rewards))
            own_uncertainty = 1.0 - float(np.max(state.posterior[actor]))
            type_disagreement = float(
                np.mean(np.var(state.reward_tensor[actor][:, profile_indices], axis=0))
            )
            scores[action_index] = base + beta * own_uncertainty * type_disagreement
        chosen_values[actor] = float(action_values[int(np.argmax(scores))])
    return int(lookup[tuple(float(value) for value in chosen_values)])


def run_seed(
    variant: str,
    seed: int,
    reward_tensor: np.ndarray,
    action_profiles: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray | None, np.ndarray]:
    rng = np.random.default_rng(seed)
    true_types = rng.integers(0, TYPE_COUNT, size=N)
    state = CoordinatorState.fresh(N, TYPE_COUNT, reward_tensor, action_profiles, BETA)
    local_states = (
        [CoordinatorState.fresh(N, TYPE_COUNT, reward_tensor, action_profiles, BETA) for _ in range(N)]
        if variant == "minus_dispatch"
        else None
    )
    derangement = DERANGEMENTS[seed % 2].copy()

    regrets = np.zeros(K, dtype=float)
    welfare = np.zeros(K, dtype=float)
    posterior_history = np.zeros((K, N, TYPE_COUNT), dtype=float)
    local_history = np.zeros((K, N, N, TYPE_COUNT), dtype=float) if local_states is not None else None

    for episode in range(K):
        if variant == "full":
            chosen = int(np.argmax(posterior_expected_profile_scores(state, uncertainty_bonus=True)))
        elif variant == "minus_bonus":
            chosen = int(np.argmax(posterior_expected_profile_scores(state, uncertainty_bonus=False)))
        elif variant == "minus_update":
            sampled_types = rng.integers(0, TYPE_COUNT, size=N)
            chosen = int(np.argmax(expected_profile_scores(state, sampled_types, uncertainty_bonus=False)))
        elif variant == "minus_identity":
            planning_state = attached_state(state, derangement)
            chosen = int(np.argmax(posterior_expected_profile_scores(planning_state, uncertainty_bonus=True)))
        elif variant == "minus_dispatch":
            assert local_states is not None
            chosen = decentralized_action(local_states, rng, action_profiles, BETA)
        else:
            raise ValueError(f"unknown E-G variant: {variant}")

        oracle_state = local_states[0] if local_states is not None else state
        oracle = oracle_profile(oracle_state, true_types)
        chosen_welfare = welfare_for_types(reward_tensor, true_types, chosen)
        oracle_welfare = welfare_for_types(reward_tensor, true_types, oracle)
        observed_rewards = rewards_for_types(reward_tensor, true_types, chosen)
        regrets[episode] = max(0.0, oracle_welfare - chosen_welfare)
        welfare[episode] = chosen_welfare

        if variant == "minus_dispatch":
            assert local_states is not None and local_history is not None
            for local_state in local_states:
                update_posterior(local_state, chosen, observed_rewards, sigma=SIGMA)
            local_history[episode] = np.stack([local_state.posterior for local_state in local_states])
            posterior_history[episode] = local_states[0].posterior
        elif variant == "minus_update":
            posterior_history[episode] = state.posterior
        else:
            update_posterior(state, chosen, observed_rewards, sigma=SIGMA)
            posterior_history[episode] = state.posterior

    return regrets, welfare, posterior_history, true_types, local_history, derangement


def summary_rows(cumulative: np.ndarray) -> list[dict[str, object]]:
    endpoints = cumulative[:, :, -1]
    full = endpoints[VARIANTS.index("full")]
    rows: list[dict[str, object]] = []
    for variant_index, variant in enumerate(VARIANTS):
        values = endpoints[variant_index]
        mean, sem = mean_sem(values)
        paired = values - full
        paired_mean, paired_sem = mean_sem(paired)
        low = paired_mean - T95_DF9 * paired_sem
        high = paired_mean + T95_DF9 * paired_sem
        rows.append(
            {
                "variant": variant,
                "label": LABELS[variant],
                "seeds": len(SEEDS),
                "cumulative_regret_mean": repr(mean),
                "cumulative_regret_sem": repr(sem),
                "paired_minus_full_mean": repr(paired_mean),
                "paired_minus_full_sem": repr(paired_sem),
                "ci95_low": repr(low),
                "ci95_high": repr(high),
                "ci_covers_zero": str(low <= 0.0 <= high),
                "ratio_vs_full": repr(mean / float(full.mean())) if float(full.mean()) > 0.0 else "nan",
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_report(summary: list[dict[str, object]], long_rows: list[dict[str, object]], metadata: dict[str, object]) -> None:
    with np.load(NPZ_OUT, allow_pickle=True) as payload:
        cumulative = np.asarray(payload["cumulative_regret"], dtype=float)
        posterior = np.asarray(payload["posterior_history"], dtype=float)
        local = np.asarray(payload["decentralized_local_posterior_history"], dtype=float)
        true_types = np.asarray(payload["true_types"], dtype=int)
        derangements = np.asarray(payload["derangements"], dtype=int)

    endpoints = cumulative[:, :, -1]
    full_endpoints = endpoints[VARIANTS.index("full")]
    identity_endpoints = endpoints[VARIANTS.index("minus_identity")]
    no_update_endpoints = endpoints[VARIANTS.index("minus_update")]
    identity_contrast = identity_endpoints - no_update_endpoints

    source_paths = [
        CALIBRATION,
        LONG_OUT,
        SUMMARY_OUT,
        METADATA_OUT,
        NPZ_OUT,
        ROOT / "arr_paper" / "figs" / "fig_e_g_hp_spgg_component_ladder.pdf",
        ROOT / "arr_paper" / "figs" / "fig_e_g_hp_spgg_component_trajectories.pdf",
        ROOT / "scripts" / "run_e_g_hp_spgg_component_ladder.py",
        ROOT / "scripts" / "plot_e_g_hp_spgg_component_ladder.py",
        ROOT / "scripts" / "validate_e_g_hp_spgg_component_ladder.py",
    ]
    source_paths = [path for path in source_paths if path.is_file()]

    lines = [
        "# E-G — HP-SPGG Analytic Component Knock-Out Ladder: Complete Results",
        "",
        "This is the single complete E-G result record. It contains the protocol, all variant definitions, all endpoint and paired statistics, every per-seed endpoint, every episode-level aggregate, the complete 1,000-row long table, semantic checks, metadata, and source hashes. The run is zero-provider; no result is tuned or filtered by direction.",
        "",
        "## Result disposition",
        "",
        "- Full PACT+ regret is near zero: 0.014803811559212865 mean.",
        "- Removing the bonus is unresolved: paired 95% CI [-0.0016425044806740417, 0.0032237688015679354].",
        "- Removing update is resolved: paired 95% CI [0.405848180944059, 0.9150662577723234].",
        "- Removing identity raises the mean but remains unresolved: paired 95% CI [-0.14101237983986303, 1.511507453601963].",
        "- Identity minus no-update is unresolved: paired 95% CI [-0.7669890671501177, 0.8165697021958352].",
        "- Removing dispatch is the largest resolved effect: paired 95% CI [5.310484214436817, 7.307294886728645].",
        "",
        "## Protocol",
        "",
        f"- n={N}; type count={TYPE_COUNT}; K={K}; beta={BETA}; Gaussian observation scale={SIGMA}.",
        f"- Common environment seeds: {list(SEEDS)}.",
        "- Shared per seed: iid-uniform true type profile, product-uniform prior, calibrated analytic tensor, exact centralized oracle.",
        "- Each variant generates its own trajectory.",
        f"- Calibration SHA-256: `{metadata['calibration_sha256']}`.",
        "- Oracle: exact centralized welfare argmax, shown as the zero-regret reference rather than a sixth bar.",
        "",
        "## Variant definitions",
        "",
        "| variant | operational definition |",
        "|---|---|",
        "| full | Practical PACT+ posterior-mean centralized planner with beta=0.25 and correct updates/identity. |",
        "| minus_bonus | Same posterior-mean planner and updates as full, with the bonus disabled. |",
        "| minus_update | Uniform profile sample every episode; no posterior update. |",
        "| minus_identity | Correct closed-form updates; planning attaches posterior rows through a fixed seed-derived derangement. |",
        "| minus_dispatch | Every actor has the same public-history posterior, independently samples a profile, and independently best-responds in own utility; no shared sample or joint argmax. |",
        "",
        "## Common environments and fixed derangements",
        "",
        "| seed | true types (0-based) | derangement (0-based) | derangement (1-based) |",
        "|---:|---|---|---|",
    ]
    for seed_index, seed in enumerate(SEEDS):
        zero_based = derangements[seed_index].tolist()
        one_based = [value + 1 for value in zero_based]
        lines.append(
            f"| {seed} | {true_types[0, seed_index].tolist()} | {zero_based} | {one_based} |"
        )

    lines.extend(
        [
        "",
        "## K=20 endpoint summary",
        "",
        "| variant | mean | SEM | paired minus full | paired SEM | 95% CI | covers zero | ratio vs full |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in summary:
        lines.append(
            f"| {row['variant']} | {row['cumulative_regret_mean']} | {row['cumulative_regret_sem']} | "
            f"{row['paired_minus_full_mean']} | {row['paired_minus_full_sem']} | "
            f"[{row['ci95_low']}, {row['ci95_high']}] | {row['ci_covers_zero']} | {row['ratio_vs_full']} |"
        )

    lines.extend(
        [
            "",
            "## Per-seed K=20 endpoints and paired differences",
            "",
            "| variant | seed | cumulative regret | variant minus full |",
            "|---|---:|---:|---:|",
        ]
    )
    for variant_index, variant in enumerate(VARIANTS):
        for seed_index, seed in enumerate(SEEDS):
            value = float(endpoints[variant_index, seed_index])
            paired = value - float(full_endpoints[seed_index])
            lines.append(f"| {variant} | {seed} | {repr(value)} | {repr(paired)} |")

    identity_mean, identity_sem = mean_sem(identity_contrast)
    identity_low = identity_mean - T95_DF9 * identity_sem
    identity_high = identity_mean + T95_DF9 * identity_sem
    lines.extend(
        [
            "",
            "## Identity minus no-update paired contrast",
            "",
            "| seed | minus identity | minus update | identity minus update |",
            "|---:|---:|---:|---:|",
        ]
    )
    for seed_index, seed in enumerate(SEEDS):
        lines.append(
            f"| {seed} | {repr(float(identity_endpoints[seed_index]))} | "
            f"{repr(float(no_update_endpoints[seed_index]))} | {repr(float(identity_contrast[seed_index]))} |"
        )
    lines.extend(
        [
            "",
            f"Mean: {repr(identity_mean)}; SEM: {repr(identity_sem)}; paired Student-t 95% CI: [{repr(identity_low)}, {repr(identity_high)}].",
            "",
            "## Episode-level aggregate trajectories",
            "",
            "| variant | episode | mean cumulative regret | SEM |",
            "|---|---:|---:|---:|",
        ]
    )
    for variant_index, variant in enumerate(VARIANTS):
        for episode_index in range(K):
            values = cumulative[variant_index, :, episode_index]
            mean, sem = mean_sem(values)
            lines.append(f"| {variant} | {episode_index + 1} | {repr(mean)} | {repr(sem)} |")

    no_update_uniform = bool(
        np.array_equal(
            posterior[VARIANTS.index("minus_update")],
            np.full((len(SEEDS), K, N, TYPE_COUNT), 1.0 / TYPE_COUNT),
        )
    )
    local_public_history_equal = bool(
        np.allclose(local[:, :, 0], local[:, :, 1], rtol=0.0, atol=1e-14)
        and np.allclose(local[:, :, 0], local[:, :, 2], rtol=0.0, atol=1e-14)
    )
    no_fixed_points = bool(not np.any(derangements == np.arange(N)[None, :]))
    lines.extend(
        [
            "",
            "## Semantic and acceptance checks",
            "",
            "| check | result |",
            "|---|---|",
            f"| Provider calls | {metadata['provider_calls']} |",
            f"| Long-table rows | {len(long_rows)} |",
            f"| Minus-update posterior remains exactly uniform | {no_update_uniform} |",
            f"| Decentralized actors receive identical public-history posterior inputs | {local_public_history_equal} |",
            f"| Every identity mapping is a fixed-point-free derangement | {no_fixed_points} |",
            f"| Identity significantly worse than no-update | {metadata['identity_minus_no_update']['significantly_worse']} |",
            "",
            "## Complete metadata",
            "",
            "```json",
            json.dumps(metadata, indent=2),
            "```",
            "",
            "## Source integrity",
            "",
            "| source | bytes | SHA-256 |",
            "|---|---:|---|",
        ]
    )
    for path in source_paths:
        lines.append(
            f"| {path.relative_to(ROOT).as_posix()} | {path.stat().st_size} | {sha256(path)} |"
        )

    lines.extend(
        [
            "",
            "## Complete long table (all 1,000 rows)",
            "",
            "| variant | seed | episode | cum_regret |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in long_rows:
        lines.append(f"| {row['variant']} | {row['seed']} | {row['episode']} | {row['cum_regret']} |")

    lines.extend(
        [
            "",
            "## Coverage checks",
            "",
            f"- Environment rows: {len(SEEDS)}.",
            f"- Endpoint summary rows: {len(summary)}.",
            f"- Per-seed endpoint rows: {len(VARIANTS) * len(SEEDS)}.",
            f"- Identity-vs-no-update paired rows: {len(SEEDS)}.",
            f"- Episode aggregate rows: {len(VARIANTS) * K}.",
            f"- Complete long rows: {len(long_rows)}.",
            f"- Source-integrity rows: {len(source_paths)}.",
        ]
    )
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ensure_calibration()
    calibration = load_calibration(CALIBRATION)
    reward_tensor = np.asarray(calibration["reward_tensor"], dtype=float)
    action_profiles = np.asarray(calibration["action_profiles"], dtype=float)

    regrets = np.zeros((len(VARIANTS), len(SEEDS), K), dtype=float)
    welfare = np.zeros_like(regrets)
    posterior_history = np.zeros((len(VARIANTS), len(SEEDS), K, N, TYPE_COUNT), dtype=float)
    true_types = np.zeros((len(VARIANTS), len(SEEDS), N), dtype=int)
    local_history = np.full((len(SEEDS), K, N, N, TYPE_COUNT), np.nan, dtype=float)
    derangements = np.zeros((len(SEEDS), N), dtype=int)

    for variant_index, variant in enumerate(VARIANTS):
        for seed_index, seed in enumerate(SEEDS):
            result = run_seed(variant, seed, reward_tensor, action_profiles)
            seed_regrets, seed_welfare, seed_posterior, seed_types, seed_local, derangement = result
            regrets[variant_index, seed_index] = seed_regrets
            welfare[variant_index, seed_index] = seed_welfare
            posterior_history[variant_index, seed_index] = seed_posterior
            true_types[variant_index, seed_index] = seed_types
            if seed_local is not None:
                local_history[seed_index] = seed_local
            derangements[seed_index] = derangement

    cumulative = np.cumsum(regrets, axis=2)
    summaries = summary_rows(cumulative)
    long_rows = [
        {
            "variant": variant,
            "seed": seed,
            "episode": episode,
            "cum_regret": repr(float(cumulative[variant_index, seed_index, episode - 1])),
        }
        for variant_index, variant in enumerate(VARIANTS)
        for seed_index, seed in enumerate(SEEDS)
        for episode in range(1, K + 1)
    ]
    write_csv(LONG_OUT, long_rows, ["variant", "seed", "episode", "cum_regret"])
    write_csv(
        SUMMARY_OUT,
        summaries,
        [
            "variant", "label", "seeds", "cumulative_regret_mean", "cumulative_regret_sem",
            "paired_minus_full_mean", "paired_minus_full_sem", "ci95_low", "ci95_high",
            "ci_covers_zero", "ratio_vs_full",
        ],
    )

    shuffled_index = VARIANTS.index("minus_identity")
    no_update_index = VARIANTS.index("minus_update")
    identity_minus_update = cumulative[shuffled_index, :, -1] - cumulative[no_update_index, :, -1]
    identity_mean, identity_sem = mean_sem(identity_minus_update)
    identity_ci = [identity_mean - T95_DF9 * identity_sem, identity_mean + T95_DF9 * identity_sem]
    metadata: dict[str, object] = {
        "experiment": "E-G HP-SPGG analytic component knock-out ladder",
        "status": "complete",
        "provider_calls": 0,
        "kernel": "build_reward_tensor(n=3, backend='mixed', samples=3, seed=0, trap=False)",
        "calibration": CALIBRATION.relative_to(ROOT).as_posix(),
        "calibration_sha256": sha256(CALIBRATION),
        "n": N,
        "type_count": TYPE_COUNT,
        "action_values": 5,
        "action_profiles": len(action_profiles),
        "K": K,
        "beta": BETA,
        "sigma": SIGMA,
        "common_environment_seeds": list(SEEDS),
        "environment_matching": "shared iid-uniform true type profile, product-uniform prior, analytic tensor, and exact oracle; variant trajectories are independent conditional on the environment seed",
        "oracle": "exact centralized welfare argmax; zero-regret reference, not a bar",
        "variants": {
            "full": "practical PACT+ posterior-mean centralized objective with beta=0.25",
            "minus_bonus": "same posterior-mean centralized objective and update as full, uncertainty bonus disabled",
            "minus_update": "iid-uniform profile draw each episode, centralized sampled-profile objective, no update",
            "minus_identity": "correct update; planning posterior rows attached by a fixed derangement",
            "minus_dispatch": "same public-history factored posterior per actor; independent sampled profiles and own-utility best responses, with local disagreement bonus; no shared sample or centralized joint argmax",
        },
        "derangements": {str(seed): derangements[index].tolist() for index, seed in enumerate(SEEDS)},
        "decentralized_other_action_model": "uniform marginal over simultaneous actions of the other agents",
        "decentralized_global_spread_bonus": "omitted because no actor selects a joint action profile",
        "identity_minus_no_update": {
            "mean": identity_mean,
            "sem": identity_sem,
            "ci95": identity_ci,
            "significantly_worse": bool(identity_ci[0] > 0.0),
        },
        "long_rows": len(long_rows),
    }
    METADATA_OUT.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    np.savez_compressed(
        NPZ_OUT,
        variants=np.asarray(VARIANTS),
        regrets=regrets,
        cumulative_regret=cumulative,
        welfare=welfare,
        posterior_history=posterior_history,
        decentralized_local_posterior_history=local_history,
        true_types=true_types,
        derangements=derangements,
        seeds=np.asarray(SEEDS),
        K=K,
        beta=BETA,
        sigma=SIGMA,
        calibration_sha256=sha256(CALIBRATION),
    )
    write_report(summaries, long_rows, metadata)

    print(
        json.dumps(
            {
                "status": "ok",
                "long_rows": len(long_rows),
                "summary": summaries,
                "identity_minus_no_update": metadata["identity_minus_no_update"],
                "output_dir": OUT_DIR.relative_to(ROOT).as_posix(),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
