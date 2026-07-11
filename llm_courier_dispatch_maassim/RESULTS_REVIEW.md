# MaaSSim Results Review

Audit date: 2026-07-11

This document is the canonical review of the MaaSSim integration results currently retained in the repository. It separates closed-loop simulation, fixed-state replay, mechanism ablations, LLM-assisted dispatch, early smoke tests, and presentation-only artifacts.

## 1. Scope and source-of-truth policy

The current workspace contains:

- 70 MaaSSim result files under `analysis/courier_dispatch_maassim/`:
  - 20 CSV files;
  - 11 JSON files;
  - 10 JSONL files;
  - 29 Markdown files;
- 72 MaaSSim figures under `arr_paper/figs/`:
  - 35 PDF files;
  - 36 PNG files;
  - 1 GIF animation.

When numbers disagree across documents, this review uses the following precedence:

1. aggregate CSV;
2. generated experiment Markdown;
3. integration README prose;
4. historical smoke notes.

The CloudGPT cache is not an experimental result and is excluded from evidence claims.

## 2. Executive assessment

### 2.1 What the retained results support

1. **The MaaSSim bridge works end to end.** The adapter can observe queues, control matching, apply synthetic hidden driver rules, update posteriors, and export simulator KPIs.
2. **Learned driver-specific beliefs have measurable value on fixed states.** In the persona-mechanism replay, PACT reaches utility `27.61`, versus `11.11` with a uniform prior and `6.87` when learned posteriors are attached to the wrong drivers.
3. **Correct identity attachment is essential.** PACT exceeds the shuffled-posterior variant by `20.73` utility.
4. **The legal-assignment LLM interface is reliable.** The final normal and stress runs have parse rate `1.000`, repair rate `0.000`, and fallback rate `0.000` for the reported LLM methods.
5. **Persona-aware score assistance matters more as rejection mistakes become costly.** The LLM-PACT hybrid's utility advantage over the best pure prompt baseline grows from `+1.47` in the normal replay to `+4.60` under rejection-cost stress and `+39.69` in the extreme conflict-offer stress test.

### 2.2 What the retained results do not support

1. **The closed-loop Persona v2 table does not show PACT beating Nearest.** Nearest has lower mean wait (`121.4` versus `127.6` seconds), while PACT, PACT+, and Oracle are operationally identical in that configuration.
2. **The current MaaSSim runs do not establish a PACT+ advantage.** PACT and PACT+ are identical or nearly identical in all primary MaaSSim tables.
3. **The LLM-PACT hybrid is not a pure prompt baseline.** It receives PACT-style assignment scores and must be described as an assisted or hybrid method.
4. **The LLM comparisons are not statistically conclusive.** They use five seeds and have large seed-level SEM; no paired significance test can be reconstructed from the retained aggregate-only LLM tables.
5. **Passenger type recovery is weak.** Passenger rule accuracy is about `0.531`, close to the uninformative `0.5` baseline, because most passengers are observed only once.
6. **The conflict-offer result is an extreme stress test, not a normal-operation estimate.** Several baselines have strongly negative utility.
7. **MaaSSim backbone generalization is untested.** The retained LLM replay results use only `gpt-5.4-mini-20260317`.

## 3. Evidence hierarchy

| Tier | Experiment | Scale | Role in the evidence |
|---|---|---:|---|
| A | Persona-mechanism replay | 10 seeds | Strongest mechanism evidence |
| A | Common-state replay | 10 seeds | Controls state-distribution confounding |
| A- | Persona v2 closed loop | 10 seeds, 40 passengers, 8 vehicles | Main ecological integration run, but policy-degenerate |
| B+ | LLM normal replay | 5 seeds x 20 active snapshots | Main normal LLM comparison |
| B+ | LLM rejection-stress replay | 5 seeds x 20 active snapshots | Main stress comparison |
| B | Three-scenario suite | 5 seeds x 20 active snapshots | Robustness trend; conflict case is extreme |
| C | Nearest-optimality diagnostic | 10 seeds | One-step wait diagnostic |
| C | Controlled synthetic baseline | 5 seeds | Integration smoke |
| C | Batch controlled synthetic | 5 seeds | Queue-depth smoke |
| C | KPI calibration grid | 18 settings x 5 seeds | Tuning diagnostic |
| D | LLM s1/s2 runs | 1-2 seeds | Prompt and parser development |
| Historical | Shadow and single-seed bridge smokes | 1 seed | README-only integration history |

## 4. Experimental substrate

### 4.1 MaaSSim setting

The retained main runs use the Nootdorp MaaSSim scenario. The larger closed-loop settings use:

- `nP=40` passengers;
- `nV=8` vehicles;
- `batch_time=120` seconds;
- independently sampled driver and passenger personas;
- synthetic driver accept/reject rules applied inside MaaSSim;
- passenger accept/reject decisions based on passenger personas.

### 4.2 Hidden types

Driver rules:

- `avoid_long`;
- `zone_loyal`;
- `home_pull`;
- `surge_sensitive` / `surge_only`.

Passenger rules:

- `impatient`;
- `price_sensitive`;
- `delay_sensitive`;
- `pooling_averse`.

### 4.3 Metrics

- exact posterior mass on the true driver tuple, `P(true)`;
- driver rule-marginal accuracy;
- passenger rule-marginal accuracy;
- mean passenger wait;
- served rides;
- driver and passenger rejects;
- driver acceptance rate;
- realized utility;
- immediate wait-oracle match rate and extra pickup wait.

The mechanism and LLM replay utility uses service value, pickup-wait cost, driver-reject penalty, and passenger-reject penalty. The normal replay uses driver-reject penalty `2.0`; rejection stress uses `5.0`.

## 5. Integration and controlled synthetic results

### 5.1 Historical shadow and single-seed bridge smokes

The integration README records the following early milestones:

- 45 queue snapshots, including 20 non-empty snapshots;
- shadow PACT assignments on 20 snapshots;
- non-intervening synthetic rule tracking with final mean `P(true)=0.228` and rule accuracy `0.733`;
- a first controlled single-seed run with 62 assignments, final mean `P(true)=0.333`, rule accuracy `0.826`, 16 rides, 44 rejects, and mean wait `143.85` seconds.

These values validate the integration path, but the original raw files are no longer retained in the cleaned workspace. They are **historical integration records**, not independently re-auditable primary evidence.

### 5.2 Five-seed controlled synthetic comparison

Source: [maassim_controlled_synthetic_baseline_summary.csv](../analysis/courier_dispatch_maassim/maassim_controlled_synthetic_baseline_summary.csv)

| Policy | P(true) | Rule acc. | Mean wait | Rides | Rejects |
|---|---:|---:|---:|---:|---:|
| Nearest | 0.199 +/- 0.030 | 0.695 +/- 0.023 | 102.8 +/- 15.4 | 19.6 | 12.0 |
| Random | 0.233 +/- 0.037 | 0.731 +/- 0.021 | 136.6 +/- 5.9 | 19.8 | 13.2 |
| PACT-proxy | 0.204 +/- 0.034 | 0.707 +/- 0.029 | 132.3 +/- 10.3 | 19.6 | 10.0 |
| PACT+-proxy | 0.216 +/- 0.030 | 0.720 +/- 0.020 | 133.2 +/- 10.0 | 19.6 | 11.8 |
| PACT-KPI | 0.198 +/- 0.029 | 0.702 +/- 0.029 | 99.8 +/- 12.7 | 19.6 | 13.0 |
| PACT+-KPI | 0.198 +/- 0.029 | 0.702 +/- 0.029 | 99.8 +/- 12.7 | 19.6 | 13.0 |
| Oracle-KPI | 0.200 +/- 0.029 | 0.688 +/- 0.023 | 102.8 +/- 15.4 | 19.6 | 10.2 |

Interpretation:

- the current KPI scorer has the lowest mean wait in this small smoke;
- all uncertainty intervals are broad;
- PACT and PACT+ collapse to the same result;
- the proxy scorer reduces rejects but has substantially worse wait.

This is an integration/tuning result, not a main performance claim.

### 5.3 Five-seed batch comparison

Source: [maassim_batch_controlled_synthetic_baseline_summary.csv](../analysis/courier_dispatch_maassim/maassim_batch_controlled_synthetic_baseline_summary.csv)

| Policy | P(true) | Rule acc. | Mean wait | Rides | Rejects |
|---|---:|---:|---:|---:|---:|
| Nearest | 0.214 +/- 0.023 | 0.742 +/- 0.007 | 167.5 +/- 6.9 | 39.0 | 24.2 |
| Random | 0.224 +/- 0.022 | 0.751 +/- 0.016 | 216.8 +/- 9.1 | 39.0 | 34.4 |
| PACT | 0.208 +/- 0.022 | 0.730 +/- 0.013 | 170.7 +/- 7.2 | 39.0 | 22.2 |
| PACT+ | 0.208 +/- 0.022 | 0.728 +/- 0.013 | 170.7 +/- 7.2 | 39.0 | 22.0 |
| Oracle | 0.198 +/- 0.020 | 0.705 +/- 0.018 | 170.2 +/- 7.4 | 39.2 | 16.8 |

Interpretation:

- Nearest is about `3.2` seconds better on mean wait than PACT;
- PACT reduces rejects by `2.0` versus Nearest;
- Oracle reduces rejects further but does not minimize wait;
- random assignments provide slightly higher posterior recovery while producing much worse operational KPIs, showing that recovery alone is not the objective.

### 5.4 KPI calibration grid

Source: [maassim_kpi_calibration_sweep.csv](../analysis/courier_dispatch_maassim/maassim_kpi_calibration_sweep.csv)

The grid covers 18 settings:

- wait weight in `{0.04, 0.08, 0.12}`;
- reject penalty in `{0.0, 0.25, 0.5}`;
- fare weight in `{0.0, 0.5}`;
- five seeds per setting.

Best observed settings:

| Target | Setting | Result |
|---|---|---:|
| Lowest mean wait | wait `0.12`, reject `0.0`, fare `0.0` | 167.6 +/- 7.2 s |
| Fewest rejects | wait `0.04`, reject `0.25`, fare `0.5` | 23.0 +/- 2.6 |
| Highest rule accuracy | several fare-weight `0.5` cells | approximately 0.737 |

The grid is a tuning diagnostic. It does not establish a globally optimal parameter choice.

## 6. Persona v2 closed-loop results

Source: [maassim_persona_v2_main_summary.csv](../analysis/courier_dispatch_maassim/maassim_persona_v2_main_summary.csv)

Configuration: 10 seeds, 40 passengers, 8 vehicles, 120-second batches, independently sampled driver and passenger personas.

| Policy | Driver P(true) | Driver rule acc. | Mean wait | Rides | Driver rejects | Passenger rule acc. | Passenger reject rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| Nearest | 0.257 +/- 0.046 | 0.732 +/- 0.025 | 121.4 +/- 4.6 | 30.3 | 18.9 | 0.532 +/- 0.003 | 0.233 |
| Random | 0.321 +/- 0.054 | 0.778 +/- 0.020 | 145.9 +/- 6.0 | 25.3 | 26.3 | 0.551 +/- 0.002 | 0.354 |
| PACT | 0.268 +/- 0.040 | 0.739 +/- 0.022 | 127.6 +/- 7.0 | 29.8 | 18.5 | 0.531 +/- 0.002 | 0.230 |
| PACT+ | 0.268 +/- 0.040 | 0.739 +/- 0.022 | 127.6 +/- 7.0 | 29.8 | 18.5 | 0.531 +/- 0.002 | 0.230 |
| Oracle | 0.268 +/- 0.040 | 0.739 +/- 0.022 | 127.6 +/- 7.0 | 29.8 | 18.5 | 0.531 +/- 0.002 | 0.230 |

Critical readout:

- Nearest has lower wait than PACT by `6.2` seconds and serves `0.5` more rides on average.
- PACT has only `0.4` fewer driver rejects than Nearest.
- PACT and Oracle rows are exactly identical across all retained columns.
- PACT+ differs from PACT only at negligible posterior-update precision; its operational metrics are identical.
- This table validates the two-sided simulation, but it **does not discriminate PACT, PACT+, and Oracle**.
- Random explores more varied assignments and therefore recovers driver rules more accurately, but has substantially worse wait, service, and rejection outcomes.
- Passenger `P(true)` is about `0.079`, only modestly above the 16-type uniform prior `0.0625`; passenger inference should not be a headline result.

The five-seed [Persona v2 baseline subset](../analysis/courier_dispatch_maassim/maassim_persona_v2_baseline_summary.csv) shows the same qualitative pattern and is treated as confirmatory only.

## 7. Immediate-wait diagnostics and common-state replay

### 7.1 Nearest-optimality diagnostic

Source: [maassim_nearest_optimality_summary.csv](../analysis/courier_dispatch_maassim/maassim_nearest_optimality_summary.csv)

This diagnostic evaluates each policy on snapshots from its own closed-loop trajectory.

| Policy | Exact wait-oracle match | Extra wait / snapshot |
|---|---:|---:|
| Nearest | 0.906 | 3.060 +/- 1.709 |
| Random | 0.257 | 115.739 +/- 5.440 |
| PACT | 0.994 | 0.000 +/- 0.000 |
| PACT+ | 0.990 | 0.000 +/- 0.000 |
| Oracle | 0.994 | 0.000 +/- 0.000 |

Because policies induce different state trajectories, this table cannot isolate policy quality by itself.

### 7.2 Common-state replay

Source: [maassim_common_state_replay_summary.csv](../analysis/courier_dispatch_maassim/maassim_common_state_replay_summary.csv)

All methods are evaluated on the same Nearest-generated queue snapshots and the same persona maps.

| Policy | Wait-oracle match | Extra wait / snapshot | Served | Driver rejects | Passenger rejects |
|---|---:|---:|---:|---:|---:|
| Wait-oracle | 1.000 | 0.000 | 29.4 | 25.4 | 9.3 |
| Nearest | 0.906 | 3.060 +/- 1.709 | 30.4 | 26.0 | 9.2 |
| Random | 0.231 | 108.861 +/- 6.486 | 20.4 | 30.6 | 14.6 |
| PACT | 0.991 | 0.000 | 29.6 | 25.3 | 9.2 |
| PACT+ | 0.988 | 0.003 +/- 0.003 | 29.7 | 25.2 | 9.2 |
| Oracle | 0.991 | 0.000 | 29.6 | 25.3 | 9.2 |

Interpretation:

- on fixed states, PACT is effectively immediate-wait optimal;
- Nearest is close but not exact, paying `3.06` seconds extra per active snapshot;
- the closed-loop wait difference therefore comes from state-distribution feedback, not a one-step assignment error by PACT;
- this replay is wait-focused and still does not distinguish PACT from Oracle on persona-aware utility.

## 8. Persona-mechanism replay

Source: [maassim_pact_persona_mechanism_summary.csv](../analysis/courier_dispatch_maassim/maassim_pact_persona_mechanism_summary.csv)

This is the strongest retained mechanism experiment. Queue states and persona maps are fixed; only the driver-belief source changes.

| Variant | Belief source | Utility | Served | Driver rejects | Accept rate | Extra wait / snapshot | Policy rule acc. |
|---|---|---:|---:|---:|---:|---:|---:|
| Nearest | none | 11.03 +/- 10.88 | 30.4 | 26.0 | 0.634 | 3.06 | n/a |
| Random | none | -33.94 +/- 11.62 | 20.4 | 30.6 | 0.563 | 108.86 | n/a |
| PACT-prior | uniform | 11.11 +/- 10.74 | 29.8 | 25.1 | 0.635 | 0.45 | 0.500 |
| PACT-shuffled | learned, wrong driver | 6.87 +/- 9.55 | 29.0 | 26.5 | 0.609 | 17.56 | 0.521 |
| PACT | learned, correct driver | 27.61 +/- 11.65 | 33.3 | 18.5 | 0.740 | 16.25 | 0.720 |
| Oracle | true persona | 38.92 +/- 11.17 | 34.7 | 13.2 | 0.822 | 26.84 | 1.000 |

Derived results:

- PACT minus PACT-prior: `+16.50` utility;
- PACT minus PACT-shuffled: `+20.73` utility;
- PACT minus Nearest: `+16.58` utility;
- remaining Oracle headroom: `11.31` utility;
- prior-to-Oracle gap closed by PACT: `59.3%`.

Interpretation:

- learned beliefs are useful only when attached to the correct driver;
- the gain is not free: PACT accepts `16.25` seconds of extra pickup wait per snapshot to reduce rejections and serve more passengers;
- this table supports a persona-mechanism claim, not a pure wait-minimization claim.

## 9. LLM replay development sequence

All retained LLM MaaSSim experiments use `gpt-5.4-mini-20260317` on fixed common states.

| Stage | Scale | Key result | Status |
|---|---:|---|---|
| Direct candidate-ID prompt | 1 seed x 8 snapshots | utility 12.33, parse 0.875, fallback 0.125 | Superseded parser smoke |
| Legal assignment menu | 2 seeds x 12 snapshots | parse 1.000, fallback 0.000 | Interface validation |
| Basic versus scored menu | 2 seeds x 12 snapshots | scored 8.52 vs basic 8.29 utility | Small diagnostic |
| A-ToM/ECON menu | 2 seeds x 12 snapshots | all parse 1.000; utilities around 8.2-8.5 | Small diagnostic |
| Normal core | 5 seeds x 20 snapshots | LLM-PACT 31.29; best pure prompt 29.81 | Main normal replay |
| Rejection stress | 5 seeds x 20 snapshots | LLM-PACT 18.37; best pure prompt 13.77 | Main stress replay |
| Conflict-offer stress | 5 seeds x 20 snapshots | LLM-PACT 8.79; best pure prompt -30.90 | Extreme stress replay |

The intermediate [maassim_llm_atom_stress_s5_m20.md](../analysis/courier_dispatch_maassim/maassim_llm_atom_stress_s5_m20.md) used an earlier prompt version with parse `0.990`. It is superseded by the final prompt-stress table with parse `1.000`.

## 10. Normal LLM replay

Sources:

- [maassim_llm_atom_core_s5_m20.md](../analysis/courier_dispatch_maassim/maassim_llm_atom_core_s5_m20.md)
- [maassim_llm_scenario_suite_detail.csv](../analysis/courier_dispatch_maassim/maassim_llm_scenario_suite_detail.csv)

Configuration: five seeds, first 20 active snapshots per seed, driver-reject penalty `2.0`.

| Policy | Utility | Served | Driver rejects | Accept rate | Extra wait / snapshot | Parse |
|---|---:|---:|---:|---:|---:|---:|
| Nearest | 28.90 +/- 8.34 | 19.6 | 5.4 | 0.822 | 1.66 | n/a |
| Random | -0.72 +/- 4.17 | 13.6 | 8.8 | 0.716 | 120.77 | n/a |
| PACT | 31.29 +/- 7.76 | 20.2 | 4.2 | 0.862 | 2.19 | n/a |
| LLM-PACT hybrid | 31.29 +/- 7.76 | 20.2 | 4.2 | 0.862 | 2.19 | 1.000 |
| LLM-belief | 28.27 +/- 7.47 | 19.4 | 5.2 | 0.829 | 3.50 | 1.000 |
| LLM-PSRL | 29.81 +/- 7.80 | 19.8 | 4.8 | 0.841 | 3.22 | 1.000 |
| A-ToM-0 | 29.02 +/- 7.99 | 19.6 | 5.4 | 0.822 | 0.26 | 1.000 |
| A-ToM-1 | 28.97 +/- 8.01 | 19.6 | 5.4 | 0.822 | 0.20-1.31 across retained prompt variants | 1.000 |
| ECON-BNE | 28.81-28.88 +/- about 8.0 | 19.6 | 5.4 | 0.822 | 1.05-1.28 | 1.000 |
| Oracle | 37.64 +/- 6.01 | 20.6 | 0.4 | 0.989 | 18.48 | n/a |

Interpretation:

- the hybrid exactly matches the PACT outcome in this replay;
- its advantage over the best pure prompt method, LLM-PSRL, is `+1.47` utility;
- SEM is much larger than the gap, so this is directional, not a significance claim;
- perfect parse behavior validates the action interface, not policy optimality.

## 11. Rejection-cost stress replay

Source: [maassim_llm_prompt_stress_s5_m20.md](../analysis/courier_dispatch_maassim/maassim_llm_prompt_stress_s5_m20.md)

Configuration: five seeds, 20 active snapshots, driver-reject penalty `5.0`, passenger-reject penalty `0.5`.

| Policy | Utility | Served | Driver rejects | Accept rate | Extra wait / snapshot | Parse |
|---|---:|---:|---:|---:|---:|---:|
| Nearest | 12.70 +/- 11.83 | 19.6 | 5.4 | 0.822 | 1.66 | n/a |
| Random | -27.12 +/- 7.54 | 13.6 | 8.8 | 0.716 | 120.77 | n/a |
| LLM-PACT hybrid | 18.37 +/- 10.12 | 20.2 | 4.2 | 0.862 | 5.97 | 1.000 |
| LLM-belief | 13.47 +/- 9.94 | 19.4 | 5.0 | 0.835 | 3.06 | 1.000 |
| LLM-PSRL | 13.77 +/- 11.14 | 19.6 | 5.0 | 0.835 | 6.69 | 1.000 |
| A-ToM-0 | 12.67 +/- 11.34 | 19.6 | 5.4 | 0.822 | 1.46 | 1.000 |
| A-ToM-1 | 12.77 +/- 11.46 | 19.6 | 5.4 | 0.822 | 0.62 | 1.000 |
| ECON-BNE | 12.48 +/- 11.47 | 19.6 | 5.4 | 0.822 | 1.76 | 1.000 |
| Oracle | 36.44 +/- 5.09 | 20.6 | 0.4 | 0.989 | 18.48 | n/a |

The hybrid exceeds the best pure prompt baseline by `+4.60` utility and avoids `0.8` driver rejects on average. Large SEM still prevents a strong significance claim.

## 12. Three-scenario suite

Sources:

- [maassim_llm_scenario_suite_summary.csv](../analysis/courier_dispatch_maassim/maassim_llm_scenario_suite_summary.csv)
- [maassim_llm_scenario_suite_detail.csv](../analysis/courier_dispatch_maassim/maassim_llm_scenario_suite_detail.csv)

| Scenario | Reject penalty | LLM-PACT utility | Best pure prompt | Best prompt utility | Utility gap | Reject gap | Oracle utility |
|---|---:|---:|---|---:|---:|---:|---:|
| Normal | 2.0 | 31.29 +/- 7.76 | LLM-PSRL | 29.81 +/- 7.80 | +1.47 | 0.6 | 37.64 |
| Rejection stress | 5.0 | 18.37 +/- 10.12 | LLM-PSRL | 13.77 +/- 11.14 | +4.60 | 0.8 | 36.44 |
| Conflict offer | 5.0 | 8.79 +/- 4.84 | LLM-belief | -30.90 +/- 4.20 | +39.69 | 7.6 | 22.44 |

### 12.1 Conflict-offer detail

| Policy | Utility | Served | Driver rejects | Accept rate |
|---|---:|---:|---:|---:|
| Nearest | -108.48 +/- 9.62 | 6.8 | 24.2 | 0.230 |
| Random | -59.15 +/- 9.61 | 8.8 | 13.2 | 0.577 |
| LLM-PACT hybrid | 8.79 +/- 4.84 | 16.4 | 3.2 | 0.896 |
| LLM-belief | -30.90 +/- 4.20 | 13.6 | 10.8 | 0.654 |
| LLM-PSRL | -32.93 +/- 7.23 | 13.6 | 11.2 | 0.643 |
| A-ToM-0 | -49.21 +/- 4.71 | 11.6 | 13.8 | 0.560 |
| A-ToM-1 | -42.43 +/- 3.21 | 12.6 | 12.8 | 0.594 |
| ECON-BNE | -46.82 +/- 8.02 | 11.8 | 13.4 | 0.575 |
| Oracle | 22.44 +/- 4.72 | 18.6 | 1.4 | 0.956 |

The conflict environment intentionally makes low-wait offers persona-risky. The hybrid chooses much higher-wait assignments to avoid rejections. The large positive gap is therefore a valid stress response but should not be presented as expected normal-operation performance.

## 13. Cross-result interpretation

### 13.1 Recovery and utility are different objectives

Random matching often has the highest driver posterior recovery because it creates diverse observations, but it performs poorly on wait, service, and utility. Posterior recovery is a mechanism diagnostic, not a sufficient operational objective.

### 13.2 Wait-optimality and persona utility are different objectives

PACT is essentially immediate-wait-optimal in the wait-focused common-state replay. In the persona-mechanism replay it willingly accepts more pickup wait to reduce driver rejections and increase service. These results are compatible because the objectives differ.

### 13.3 Closed-loop comparisons remain distribution-sensitive

The same one-step policy can induce different future vehicle positions and queue composition. Closed-loop mean wait therefore cannot be interpreted solely from the current assignment rule. A definitive dynamic comparison requires simulator branching or common exogenous arrivals with policy-specific state evolution.

### 13.4 PACT+ remains unresolved

The retained MaaSSim candidate sets and bonus settings do not create a meaningful PACT/PACT+ separation. No MaaSSim claim should rely on PACT+ outperforming PACT.

## 14. Recommended claims

### Supported wording

- The adapter closes the loop between PACT matching, hidden synthetic driver rules, posterior updates, and MaaSSim KPIs.
- On fixed MaaSSim states, learned driver-specific beliefs improve realized utility relative to a uniform prior and shuffled-driver controls.
- Correctly attaching a recovered belief to the corresponding driver is necessary for the observed gain.
- A constrained legal-assignment menu yields reliable structured LLM output.
- The LLM-PACT hybrid becomes more useful when hidden-persona mistakes carry larger rejection costs.

### Wording to avoid

- PACT significantly outperforms Nearest in the Persona v2 closed-loop main run.
- PACT+ outperforms PACT in MaaSSim.
- The Persona v2 Oracle result validates optimality; it is identical to PACT under that configuration.
- LLM-PACT is a pure prompt baseline.
- The conflict-offer utility gap represents normal ride-hailing operations.
- MaaSSim results generalize across LLM backbones or real human driver personas.

## 15. Limitations and missing analyses

1. Synthetic hidden personas, not learned real-world driver types.
2. Only one MaaSSim road-network scenario.
3. One LLM backbone in retained MaaSSim LLM results.
4. Five LLM seeds and no retained per-seed outcome table for formal paired testing.
5. Weak passenger inference due to one-shot riders.
6. No fairness breakdown by driver or passenger persona.
7. No long-horizon fleet-level welfare or revenue analysis.
8. No meaningful PACT+ separation.
9. No dynamic counterfactual branching from identical simulator states.
10. Early shadow-smoke raw artifacts were removed during cleanup.

## 16. Canonical artifacts

### 16.1 Aggregate result tables

- [Controlled synthetic baseline](../analysis/courier_dispatch_maassim/maassim_controlled_synthetic_baseline_summary.csv)
- [Batch controlled synthetic baseline](../analysis/courier_dispatch_maassim/maassim_batch_controlled_synthetic_baseline_summary.csv)
- [KPI calibration sweep](../analysis/courier_dispatch_maassim/maassim_kpi_calibration_sweep.csv)
- [Persona v2 main](../analysis/courier_dispatch_maassim/maassim_persona_v2_main_summary.csv)
- [Persona v2 five-seed subset](../analysis/courier_dispatch_maassim/maassim_persona_v2_baseline_summary.csv)
- [Nearest-optimality diagnostic](../analysis/courier_dispatch_maassim/maassim_nearest_optimality_summary.csv)
- [Common-state replay](../analysis/courier_dispatch_maassim/maassim_common_state_replay_summary.csv)
- [Persona-mechanism replay](../analysis/courier_dispatch_maassim/maassim_pact_persona_mechanism_summary.csv)
- [LLM scenario suite summary](../analysis/courier_dispatch_maassim/maassim_llm_scenario_suite_summary.csv)
- [LLM scenario suite detail](../analysis/courier_dispatch_maassim/maassim_llm_scenario_suite_detail.csv)

### 16.2 Raw retained replay assets

- `nearest_persona_v2_main_s{0..9}_personas.json`: realized persona maps;
- `nearest_persona_v2_main_s{0..9}_queue_snapshots.jsonl`: fixed replay states;
- `pact_kpi_persona_v2_main_s{0..9}_driver_posterior.csv`: driver posterior trajectories.

### 16.3 Key figures

- [Persona v2 closed loop](../arr_paper/figs/fig_maassim_persona_v2_main.pdf)
- [Common-state replay](../arr_paper/figs/fig_maassim_common_state_replay.pdf)
- [Persona-mechanism ablation](../arr_paper/figs/fig_maassim_pact_persona_mechanism.pdf)
- [LLM normal core](../arr_paper/figs/fig_maassim_llm_atom_core_s5_m20.pdf)
- [LLM rejection stress](../arr_paper/figs/fig_maassim_llm_prompt_stress_s5_m20.pdf)
- [Three-scenario suite](../arr_paper/figs/fig_maassim_llm_scenario_suite.pdf)
- [Scenario dashboard](../arr_paper/figs/fig_maassim_experiment_scenario_dashboard.pdf)
- [Conflict episode dynamics](../arr_paper/figs/fig_maassim_experiment_conflict_episode_dynamics.pdf)
- [Conflict people-and-cars animation](../arr_paper/figs/fig_maassim_conflict_people_cars_llm_pact_vs_prompts.gif)

### 16.4 Main producer scripts

- [MaaSSim controlled runner](../scripts/run_maassim_shadow_smoke.py)
- [Persona v2 orchestrator](../scripts/run_maassim_persona_v2_baselines.py)
- [Common-state replay](../scripts/replay_maassim_common_states.py)
- [Persona-mechanism replay](../scripts/replay_maassim_pact_persona_mechanism.py)
- [LLM replay](../scripts/replay_maassim_llm_smoke.py)
- [Nearest-optimality diagnostic](../scripts/diagnose_maassim_nearest_optimality.py)
- [Scenario summarizer](../scripts/summarize_maassim_scenario_suite.py)
- [Experiment figure generator](../scripts/plot_maassim_experiment_figures.py)

## 17. Recommended next experiments

1. Export per-seed LLM outcome tables and run paired bootstrap/permutation tests.
2. Repeat the LLM scenario suite with at least three backbones.
3. Create repeated-rider demand to make passenger type learning identifiable.
4. Add driver-persona and passenger-persona fairness slices.
5. Build a branching/common-random-number closed-loop evaluator.
6. Construct larger candidate pools where PACT+ exploration changes assignments.
7. Evaluate multi-hour fleet welfare, driver idle time, platform revenue, and rejection externalities.

## 18. Bottom line

The MaaSSim integration is technically successful and the retained fixed-state mechanism ablation gives credible evidence that learned, correctly attached driver beliefs improve dispatch utility. The closed-loop Persona v2 main table is primarily an integration result because PACT, PACT+, and Oracle collapse to the same operational outcome. The LLM replay shows reliable structured action generation and a growing advantage for the assisted LLM-PACT hybrid under stronger persona stress, but the normal-run gap is small relative to uncertainty and the conflict case is deliberately extreme.
