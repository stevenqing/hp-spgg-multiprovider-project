"""Diagnose why the preregistered HP-SPGG burn-in scaling relation is unsupported."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_hpgg.analytic_scaling import (  # noqa: E402
    AnalyticPlanner,
    squared_hellinger_gaussians,
)


DATA = ROOT / "analysis" / "hp_spgg_analytic_scaling"
MANIFEST = DATA / "manifest_scaling.json"
FIT = DATA / "scaling_burn_in_fit.json"
JSON_OUT = DATA / "burn_in_support_diagnostic.json"
MD_OUT = DATA / "burn_in_support_diagnostic.md"
SEEDS = tuple(range(1000, 1010))


def load_npz(sweep: str, n: int, m: int, seed: int) -> dict[str, np.ndarray]:
    path = DATA / "npz" / sweep / f"n{n:02d}_m{m:02d}" / f"pact_seed{seed}.npz"
    with np.load(path, allow_pickle=False) as payload:
        return {key: np.array(payload[key], copy=True) for key in payload.files}


def action_rho(planner: AnalyticPlanner, action_index: int) -> float:
    digits = planner.grid.profile_digits(action_index)
    total = int(digits.sum())
    best = math.inf
    for agent in range(planner.n):
        means = planner.lookup[:, int(digits[agent]), total]
        distances = squared_hellinger_gaussians(means[:, None], means[None, :])
        distances[np.tril_indices(planner.m)] = np.inf
        best = min(best, float(np.min(distances)))
    return best


def cell_diagnostic(
    *,
    manifest: dict[str, object],
    sweep: str,
    n: int,
    m: int,
) -> dict[str, object]:
    parameters = np.asarray(manifest["type_libraries"][str(m)]["parameters"], dtype=float)
    planner = AnalyticPlanner(n, parameters, beta=float(manifest["beta"]))
    payloads = [load_npz(sweep, n, m, seed) for seed in SEEDS]
    passages = np.asarray([float(payload["burn_in_all_agents"]) for payload in payloads])
    finite = passages[np.isfinite(passages)]
    actions = np.concatenate([payload["action_indices"] for payload in payloads])
    counts = Counter(int(value) for value in actions)
    visited = sorted(counts)
    modal_action, modal_count = counts.most_common(1)[0]
    true_types = np.concatenate([payload["true_types"] for payload in payloads])
    per_agent_passages = np.concatenate([payload["burn_in_per_agent"] for payload in payloads])
    by_type: dict[int, list[float]] = defaultdict(list)
    for type_index, passage in zip(true_types, per_agent_passages, strict=True):
        by_type[int(type_index)].append(float(passage))
    return {
        "sweep": sweep,
        "n": n,
        "m": m,
        "x_preregistered": (n + 1.0) * math.log(m),
        "all_agent_median": float(np.median(finite)) if len(finite) >= 5 else math.nan,
        "all_agent_mean_observed": float(np.mean(finite)) if len(finite) else math.nan,
        "censored_seeds": int(len(passages) - len(finite)),
        "passages": passages.tolist(),
        "unique_actions": len(visited),
        "modal_action_index": modal_action,
        "modal_action_share": modal_count / len(actions),
        "visited_action_rho_min": min(action_rho(planner, action) for action in visited),
        "modal_action_rho": action_rho(planner, modal_action),
        "global_rho_hat": float(manifest["cells"][f"n{n}_m{m}"]["rho_hat"]),
        "per_type": {
            str(type_index): {
                "observations": len(values),
                "median": float(np.nanmedian(values)) if np.isfinite(values).any() else math.nan,
                "censored": int(np.isnan(values).sum()),
                "unique_passages": sorted({value for value in values if math.isfinite(value)}),
            }
            for type_index, values in sorted(by_type.items())
        },
    }


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    fit = json.loads(FIT.read_text(encoding="utf-8"))
    s1 = [cell_diagnostic(manifest=manifest, sweep="s1_population_m4", n=n, m=4) for n in range(2, 11)]
    s2 = [cell_diagnostic(manifest=manifest, sweep="s2_library_n3", n=3, m=m) for m in (4, 8, 16)]

    proposition = {
        "paper_statement": "per-agent expected cumulative reward-channel regret is O(H + rho^{-1} log(m/pi_min))",
        "proof_switching_term": "the displayed proof sets C=m*pi_min^{-1/2}, hence log(C)",
        "uniform_prior_log_term": "statement: 2 log(m); proof switching point: 1.5 log(m); both are O(log m)",
        "population_dependence": "none in the proposition; an all-agent union bound adds log(n), not n log(m)",
        "measured_quantity": "median first episode at which every agent posterior true-type mass exceeds 0.9",
        "mismatch": "the measured all-agent threshold maximum is neither the proposition's per-agent expected regret nor an equality case of its upper bound",
    }
    causes = [
        {
            "cause": "theory-target mismatch",
            "detail": "Proposition prop:tid-collapse bounds per-agent expected cumulative reward-channel regret. It does not predict that an all-agent posterior first-passage median equals (n+1) log(m)/(rho H).",
        },
        {
            "cause": "wrong population functional form",
            "detail": "For independent agent channels, controlling all agents by a union bound contributes log(n). A linear n factor is not present in the current proof, and thm:any-coupling is not a label in the current paper source.",
        },
        {
            "cause": "deterministic analytic observations",
            "detail": "The runner observes the calibrated reward mean exactly and only evaluates a Gaussian likelihood around it; it does not sample y from the Gaussian q_theta used in the Hellinger contraction proof. Conditional hitting times therefore become almost deterministic by true type.",
        },
        {
            "cause": "no horizon scaling dimension",
            "detail": "The analytic runner has one action/reward observation per episode and records H=1. It cannot test inverse-H dependence because H is neither greater than one nor swept.",
        },
        {
            "cause": "S1 action/channel degeneracy",
            "detail": "PACT visits only the all-contribution action in every S1 episode. At m=4, types 0/1 cross 0.9 at episode 8 and types 2/3 at episode 3. From n=2 onward, the median maximum is already the slow-type value 8 and cannot reveal further n growth.",
        },
        {
            "cause": "rho_hat is a worst-case unvisited margin",
            "detail": "The global reachable-grid rho_hat can be orders of magnitude smaller than the margin on actions actually visited. It is valid for a conservative uniform bound but not an empirical equality predictor.",
        },
        {
            "cause": "rho varies with m but the OLS x-axis omits it",
            "detail": "m=8 and m=16 use different rho_hat values, while Fig B regresses only on (n+1) log(m). There is no single slope that can be compared with 1/(rho_hat H) across libraries.",
        },
        {
            "cause": "informative censoring and pseudo-replication",
            "detail": "The m=16 point is 9/10 censored at K=50 and excluded from OLS, biasing the complete-case slope downward. Nine flat S1 points from one m=4 channel dominate the pooled fit.",
        },
        {
            "cause": "median saturation and low seed resolution",
            "detail": "The all-agent median is discrete and saturates once more than half of profiles contain any slow type; ten seeds cannot resolve the much weaker max-order/log(n) effect.",
        },
    ]
    recommendation = {
        "disposition": "retain the current result as a preregistered null; do not tune it into support",
        "valid_follow_up": [
            "Test per-agent posterior error or log-odds contraction, the quantity directly controlled by prop:tid-collapse.",
            "Sample stochastic outcomes from q_theta instead of always observing the channel mean.",
            "Use realized cumulative information sum_h D_H^2(q_true,q_competitor) on visited actions, or hold rho fixed across libraries.",
            "If measuring all-agent first passage, use a predictor with log(n), not linear n, and analyze right censoring with survival/AFT methods.",
            "Sweep a genuine multi-turn H if inverse-H behavior is a target; the completed runner has H=1 only.",
            "Increase K for m=16 and increase seeds before estimating a population-order effect; preregister this as a new experiment rather than altering the completed run.",
        ],
    }
    diagnostic = {
        "status": "diagnosed",
        "claim_b_supported": False,
        "current_fit": fit,
        "proposition": proposition,
        "causes": causes,
        "s1": s1,
        "s2": s2,
        "recommendation": recommendation,
    }
    JSON_OUT.write_text(json.dumps(diagnostic, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Why Claim (b) Is Unsupported",
        "",
        "This diagnostic is derived from the completed scaling NPZs and the current proof of Proposition `prop:tid-collapse`. It does not rerun or retune the experiment.",
        "",
        "## Bottom line",
        "",
        "The null is not primarily evidence against Proposition `prop:tid-collapse`. The experiment regressed a different statistic against a predictor that is not the proposition's formula, under a deterministic-mean DGP that does not instantiate the stochastic Gaussian outcome channel used by the Hellinger proof.",
        "",
        f"The preregistered uncensored PACT fit is slope `{fit['slope']}`, R-squared `{fit['r_squared']}`, with `{fit['observations']}` observations; it does not support the proposed pooled relation.",
        "",
        "## Theory mismatch",
        "",
        "The current proposition is per-agent and states an upper bound on expected cumulative reward-channel regret:",
        "",
        "`O(H + rho^{-1} log(m / pi_min))`.",
        "",
        "The displayed proof uses `C=m*pi_min^{-1/2}` at its switching point. For a uniform prior, the proposition statement gives `2 log(m)` and that proof step gives `1.5 log(m)`; both are only order-level `O(log m)` statements. Neither contains a linear `n` term. Requiring simultaneous control over all agents would introduce `log(n)` through a union bound, not `(n+1) log(m)`. The measured median all-agent first passage is also not the proposition's expected regret quantity. The label `thm:any-coupling` is absent from the current paper source.",
        "",
        "## Data diagnosis",
        "",
        "### S1 population sweep",
        "",
        "| n | median all-agent burn-in | mean observed | censored | unique PACT actions | modal share | global rho_hat | visited-action rho |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in s1:
        lines.append(
            f"| {row['n']} | {row['all_agent_median']} | {row['all_agent_mean_observed']} | {row['censored_seeds']} | "
            f"{row['unique_actions']} | {row['modal_action_share']:.3f} | {row['global_rho_hat']:.9g} | {row['visited_action_rho_min']:.9g} |"
        )
    lines.extend(
        [
            "",
            "PACT chooses the all-contribution action in all 4,500 S1 decisions. Under this deterministic channel, original types 0/1 cross 0.9 at episode 8 and types 2/3 at episode 3. The probability that an n-agent profile includes at least one slow type is `1-(1/2)^n`, already 0.75 at n=2, so the median maximum is 8 for every n. This is median saturation, not a failed posterior update.",
            "",
            "### S2 library sweep",
            "",
            "| m | median all-agent burn-in | censored | unique PACT actions | modal share | global rho_hat | visited-action rho |",
            "|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in s2:
        lines.append(
            f"| {row['m']} | {row['all_agent_median']} | {row['censored_seeds']} | {row['unique_actions']} | "
            f"{row['modal_action_share']:.3f} | {row['global_rho_hat']:.9g} | {row['visited_action_rho_min']:.9g} |"
        )
    lines.extend(["", "## Why the OLS slope turns negative", ""])
    lines.extend(
        [
            "1. Nine S1 points move right with n but all remain at burn-in 8.",
            "2. The only uncensored library-growth point, m=8, is 45 at the same x-value as the S1 n=5 point at 8.",
            "3. The informative m=16 point lies at the right but is 9/10 censored and excluded from OLS.",
            "4. Pooling these as independent complete cases yields a small negative slope and near-zero R-squared; this is a weighting/censoring artifact, not a contraction-rate estimate.",
            "",
            "## Causes",
            "",
        ]
    )
    for index, cause in enumerate(causes, start=1):
        lines.append(f"{index}. **{cause['cause']}.** {cause['detail']}")
    lines.extend(["", "## Recommended disposition and follow-up", "", "Keep the current run as a preregistered null. Do not change seeds, K, rho spacing, threshold, or OLS inclusion to manufacture support.", ""])
    for item in recommendation["valid_follow_up"]:
        lines.append(f"- {item}")
    lines.extend(["", "The follow-up would be a new, separately preregistered experiment. Claim (a)—exact factored/joint parity and the n=7/n=8 feasibility wall—remains unaffected."])
    MD_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "json": JSON_OUT.relative_to(ROOT).as_posix(), "report": MD_OUT.relative_to(ROOT).as_posix()}, indent=2))


if __name__ == "__main__":
    main()
