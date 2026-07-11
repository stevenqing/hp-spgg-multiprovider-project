# CourierDispatch-Rules x MaaSSim Integration

This folder is the new work area for connecting CourierDispatch-Rules to a real mobility-platform simulator.

> **Canonical results audit:** See [RESULTS_REVIEW.md](RESULTS_REVIEW.md) for the consolidated, source-checked review of all retained MaaSSim results. It separates primary evidence from smoke tests, identifies superseded variants, and documents the current claim boundaries. The historical notes below preserve the development sequence.

## Simulator Choice

MaaSSim is the best first target. It is explicitly a two-sided mobility-platform simulator with microscopic travellers, drivers, and a platform that matches demand and supply. The key integration hook is friendly: the platform matching logic is an external user-defined function `f_match(platform=platform)`. Driver opt-out, driver decline, and repositioning are also user-defined functions.

FleetPy is likely useful later. It has richer fleet control, ride-pooling, EV charging, routing, RL wrappers, and benchmark-scale scenarios. The cost is higher: integration requires implementing or extending a `FleetControlBase` operator and fitting into its request/vehicle-plan lifecycle.

## MaaSSim Integration Path

1. Install/clone MaaSSim in an external folder or environment.
2. Run a tiny MaaSSim default simulation unchanged.
3. Replace `f_match` with a shadow wrapper using `make_shadow_match_function` from `adapter.py`.
4. Log `MaaSSimQueueSnapshot` objects and verify driver/request IDs, wait times, fare, and event logs.
5. Map MaaSSim candidate offers to CourierDispatch-style features using `offer_to_rule_features`.
6. Run PACT/PACT+ in shadow mode while MaaSSim's default nearest-vehicle matcher still controls the platform.
7. Implement `MaaSSimDispatchAdapter.apply_assignment` to make PACT choose driver-request offers directly.
8. Evaluate recovery and platform KPIs.

## Current Smoke Result

The packaged Nootdorp config has been run in shadow mode through `scripts/run_maassim_shadow_smoke.py`.

| Metric | Value |
|---|---:|
| Queue snapshots | 45 |
| Non-empty snapshots | 20 |
| Max candidate pairs | 5 |
| Output | `analysis/courier_dispatch_maassim/shadow_queue_snapshots.jsonl` |

The smoke does not intervene in MaaSSim's default matching; it only observes queue states and candidate offers.

PACT shadow policy smoke also completed:

| Metric | Value |
|---|---:|
| Queue snapshots | 45 |
| Snapshots with shadow assignment | 20 |
| Total evaluated candidate assignments | 61 |
| Max evaluated assignments in one snapshot | 5 |
| Output | `analysis/courier_dispatch_maassim/pact_shadow_queue_snapshots.jsonl` |

The PACT shadow policy consumes MaaSSim candidate offers and logs a legal assignment, but still delegates execution to MaaSSim's default matcher.

Synthetic hidden-rule posterior smoke also completed in non-intervening shadow mode:

| Metric | Value |
|---|---:|
| Posterior update events | 21 |
| Drivers with updates | 5 |
| Mean final P(true) | 0.228 |
| Mean final rule acc | 0.733 |
| Synthetic decline rate | 0.333 |
| Actual MaaSSim decline rate | 0.048 |
| Posterior output | `analysis/courier_dispatch_maassim/synthetic_rule_posterior.csv` |

The synthetic rule tracker updates CourierDispatch posteriors from hidden-rule observations while leaving MaaSSim's default driver-decline behavior in control. Direct intervention is a later step because repeated synthetic rejections exposed fragile event handling in the old MaaSSim code.

Closed-loop controlled PACT matching with intervening synthetic hidden rules also completed with `--seed 0`:

| Metric | Value |
|---|---:|
| Queue snapshots | 79 |
| Controlled PACT assignments | 62 |
| Posterior update events | 62 |
| Mean final P(true) | 0.333 |
| Mean final rule acc | 0.826 |
| Synthetic/actual decline rate | 0.742 |
| Vehicle rides | 16 |
| Vehicle rejects | 44 |
| Mean passenger wait | 143.85 |

This is the first real closed-loop bridge: PACT chooses MaaSSim matches, synthetic hidden rules affect actual driver declines, and posterior recovery is logged from simulator events.

## Baseline Smoke Comparison

A first controlled synthetic baseline sweep over seeds `{0,1,2,3,4}` has been run for `Nearest`, `Random`, the old proxy scorer, and the current PACT scorer.

| Policy | Seeds | P(true) | Rule acc | Mean wait | Rides | Rejects | Synthetic decline |
|---|---:|---:|---:|---:|---:|---:|---:|
| Nearest | 5 | 0.199 +/- 0.030 | 0.695 +/- 0.023 | 102.8 +/- 15.4 | 19.6 +/- 0.4 | 12.0 +/- 3.8 | 0.347 |
| Random | 5 | 0.233 +/- 0.037 | 0.731 +/- 0.021 | 136.6 +/- 5.9 | 19.8 +/- 0.2 | 13.2 +/- 3.8 | 0.370 |
| PACT-proxy | 5 | 0.204 +/- 0.034 | 0.707 +/- 0.029 | 132.3 +/- 10.3 | 19.6 +/- 0.2 | 10.0 +/- 2.6 | 0.318 |
| PACT+-proxy | 5 | 0.216 +/- 0.030 | 0.720 +/- 0.020 | 133.2 +/- 10.0 | 19.6 +/- 0.2 | 11.8 +/- 2.0 | 0.369 |
| PACT | 5 | 0.198 +/- 0.029 | 0.702 +/- 0.029 | 99.8 +/- 12.7 | 19.6 +/- 0.4 | 13.0 +/- 5.0 | 0.353 |
| PACT+ | 5 | 0.198 +/- 0.029 | 0.702 +/- 0.029 | 99.8 +/- 12.7 | 19.6 +/- 0.4 | 13.0 +/- 5.0 | 0.353 |
| Oracle | 5 | 0.200 +/- 0.029 | 0.688 +/- 0.023 | 102.8 +/- 15.4 | 19.6 +/- 0.4 | 10.2 +/- 3.9 | 0.304 |

Full table: [../analysis/courier_dispatch_maassim/maassim_controlled_synthetic_baseline_summary.md](../analysis/courier_dispatch_maassim/maassim_controlled_synthetic_baseline_summary.md)

Figure: [../figs/fig_maassim_controlled_baselines.png](../figs/fig_maassim_controlled_baselines.png)

Readout: the tuned smoke now shows why the earlier result was poor. The original PACT proxy reduces rejects but does not optimize passenger wait. The current PACT scorer uses accept probability, pickup wait, and fare; it has the lowest mean wait in this smoke. This is still not final: PACT and PACT+ can be identical when candidate sets are small.

Batch-matching smoke with `nP=40`, `nV=8`, and `batch_time=120` increases queue depth:

| Policy | Seeds | P(true) | Rule acc | Mean wait | Rides | Rejects | Synthetic decline |
|---|---:|---:|---:|---:|---:|---:|---:|
| Nearest | 5 | 0.214 +/- 0.023 | 0.742 +/- 0.007 | 167.5 +/- 6.9 | 39.0 +/- 0.4 | 24.2 +/- 3.2 | 0.433 |
| Random | 5 | 0.224 +/- 0.022 | 0.751 +/- 0.016 | 216.8 +/- 9.1 | 39.0 +/- 0.4 | 34.4 +/- 5.5 | 0.520 |
| PACT | 5 | 0.208 +/- 0.022 | 0.730 +/- 0.013 | 170.7 +/- 7.2 | 39.0 +/- 0.4 | 22.2 +/- 3.5 | 0.409 |
| PACT+ | 5 | 0.208 +/- 0.022 | 0.728 +/- 0.013 | 170.7 +/- 7.2 | 39.0 +/- 0.4 | 22.0 +/- 3.6 | 0.406 |
| Oracle | 5 | 0.198 +/- 0.020 | 0.705 +/- 0.018 | 170.2 +/- 7.4 | 39.2 +/- 0.5 | 16.8 +/- 4.0 | 0.336 |

Batch table: [../analysis/courier_dispatch_maassim/maassim_batch_controlled_synthetic_baseline_summary.md](../analysis/courier_dispatch_maassim/maassim_batch_controlled_synthetic_baseline_summary.md)

Batch figure: [../figs/fig_maassim_batch_controlled_baselines.png](../figs/fig_maassim_batch_controlled_baselines.png)

Readout: batch mode confirms the policy is behaviorally meaningful. PACT reduces rejects relative to nearest/random, and Oracle reduces rejects further. Mean wait still slightly favors nearest, so the next calibration target is the score trade-off between pickup wait and rejection risk.

KPI calibration sweep over `wait_weight`, `reject_penalty`, and `fare_weight`:

| Best target | Setting | Value |
|---|---|---:|
| Lowest mean wait | `wait_weight=0.12`, `reject_penalty=0.0`, `fare_weight=0.0` | 167.6 |
| Fewest rejects | `wait_weight=0.04`, `reject_penalty=0.25`, `fare_weight=0.5` | 23.0 |

Calibration table: [../analysis/courier_dispatch_maassim/maassim_kpi_calibration_sweep.md](../analysis/courier_dispatch_maassim/maassim_kpi_calibration_sweep.md)

Calibration heatmap: [../figs/fig_maassim_kpi_calibration_sweep.png](../figs/fig_maassim_kpi_calibration_sweep.png)

Calibration readout: wait-first tuning can essentially match nearest on wait, but does not clearly beat it. Reject-aware tuning reduces rejects modestly. This suggests the current Nootdorp/batch substrate is near nearest-optimal for wait; the next meaningful improvement is either richer queue depth, future-aware simulator value, or a hidden-rule setup where reject avoidance has larger downstream value.

## Persona v2: Driver and Passenger Personas

Persona v2 activates both sides of the MaaSSim market:

| Persona side | Hidden bits | Main role in evaluation |
|---|---|---|
| Driver | `avoid_long`, `zone_loyal`, `home_pull`, `surge_sensitive` | Repeated type inference and assignment value |
| Passenger | `impatient`, `price_sensitive`, `delay_sensitive`, `pooling_averse` | Demand heterogeneity and local passenger utility |

The current Persona v2 main run uses `nP=40`, `nV=8`, `batch_time=120`, random factored driver/passenger personas, active driver rules, active passenger personas, and seeds `{0,1,2,3,4,5,6,7,8,9}`.

| Policy | Seeds | Driver P(true) | Driver rule acc | Mean wait | Rides | Rejects | Driver decline | Passenger rule acc | Passenger reject |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nearest | 10 | 0.257 +/- 0.046 | 0.732 +/- 0.025 | 121.4 +/- 4.6 | 30.3 +/- 1.2 | 18.9 +/- 3.4 | 0.368 | 0.532 +/- 0.003 | 0.233 |
| Random | 10 | 0.321 +/- 0.054 | 0.778 +/- 0.020 | 145.9 +/- 6.0 | 25.3 +/- 0.9 | 26.3 +/- 3.2 | 0.449 | 0.551 +/- 0.002 | 0.354 |
| PACT | 10 | 0.268 +/- 0.040 | 0.739 +/- 0.022 | 127.6 +/- 7.0 | 29.8 +/- 1.1 | 18.5 +/- 2.8 | 0.382 | 0.531 +/- 0.002 | 0.230 |
| PACT+ | 10 | 0.268 +/- 0.040 | 0.739 +/- 0.022 | 127.6 +/- 7.0 | 29.8 +/- 1.1 | 18.5 +/- 2.8 | 0.382 | 0.531 +/- 0.002 | 0.230 |
| Oracle | 10 | 0.268 +/- 0.040 | 0.739 +/- 0.022 | 127.6 +/- 7.0 | 29.8 +/- 1.1 | 18.5 +/- 2.8 | 0.382 | 0.531 +/- 0.002 | 0.230 |

Persona v2 readout: adding passenger personas makes the substrate more realistic but also harder. Passenger personas reduce served rides because some riders reject offers. Driver persona recovery remains meaningful because drivers appear repeatedly. Passenger posterior recovery is weak because MaaSSim passengers are mostly one-shot; repeated-rider scenarios are needed before passenger type inference can be a primary metric. In the current main run, nearest remains the strongest wait-time heuristic, while PACT is close on wait and clearly better than random.

Assumption mapping:

| Assumption | MaaSSim Persona v2 status |
|---|---|
| Type inference | Good for drivers; limited for one-shot passengers |
| Reward locality | Driver decisions depend on own persona and own offer; passenger choices depend on own persona and own offer |
| Factored prior | Supported by `--persona-assignment random`, which samples driver/passenger types independently and saves the realized persona JSON |

Random factored-persona smoke completed with `--persona-assignment random`:

| Metric | Value |
|---|---:|
| Driver personas | 8 |
| Passenger personas | 40 |
| Mean wait | 121.35 |
| Rides | 27 |
| Driver rejects | 18 |
| Passenger rejections | 13 |
| Driver final P(true) | 0.316 |
| Driver final rule acc | 0.770 |
| Passenger final rule acc | 0.539 |

Persona config: [../analysis/courier_dispatch_maassim/persona_v2_random_smoke_personas.json](../analysis/courier_dispatch_maassim/persona_v2_random_smoke_personas.json)

Summary: [../analysis/courier_dispatch_maassim/persona_v2_random_smoke_summary.json](../analysis/courier_dispatch_maassim/persona_v2_random_smoke_summary.json)

Persona v2 main table: [../analysis/courier_dispatch_maassim/maassim_persona_v2_main_summary.md](../analysis/courier_dispatch_maassim/maassim_persona_v2_main_summary.md)

Persona v2 main figure: [../figs/fig_maassim_persona_v2_main.png](../figs/fig_maassim_persona_v2_main.png)

Nearest-optimality diagnostic:

| Policy | Exact-match rate to immediate wait oracle | Extra wait / snapshot |
|---|---:|---:|
| Nearest | 0.906 | 3.06 +/- 1.71 |
| Random | 0.257 | 115.74 +/- 5.44 |
| PACT | 0.994 | 0.00 +/- 0.00 |
| PACT+ | 0.990 | 0.00 +/- 0.00 |
| Oracle | 0.994 | 0.00 +/- 0.00 |

Diagnostic table: [../analysis/courier_dispatch_maassim/maassim_nearest_optimality_diagnostic.md](../analysis/courier_dispatch_maassim/maassim_nearest_optimality_diagnostic.md)

Readout: nearest is very close to immediate pickup-wait optimal on its own trajectory, but PACT is also immediate-wait optimal on its own trajectory. The remaining performance difference is therefore dynamic: earlier assignments change future vehicle positions, passenger rejections, and queue composition. A true optimality claim needs common exogenous replay or simulator branching, not only per-snapshot oracle checks.

Common-state replay fixes the exogenous queue snapshots to the nearest Persona v2 main trajectory and evaluates every policy on the same saved persona maps. This removes closed-loop trajectory drift and tests the immediate assignment decision directly.

| Policy | Oracle-match | Extra wait / snapshot | Served | Driver rejects | Passenger rejects |
|---|---:|---:|---:|---:|---:|
| Wait-oracle | 1.000 | 0.00 +/- 0.00 | 29.4 | 25.4 | 9.3 |
| Nearest | 0.906 | 3.06 +/- 1.71 | 30.4 | 26.0 | 9.2 |
| Random | 0.231 | 108.86 +/- 6.49 | 20.4 | 30.6 | 14.6 |
| PACT | 0.991 | 0.00 +/- 0.00 | 29.6 | 25.3 | 9.2 |
| PACT+ | 0.988 | 0.00 +/- 0.00 | 29.7 | 25.2 | 9.2 |
| Oracle | 0.991 | 0.00 +/- 0.00 | 29.6 | 25.3 | 9.2 |

Replay table: [../analysis/courier_dispatch_maassim/maassim_common_state_replay_summary.md](../analysis/courier_dispatch_maassim/maassim_common_state_replay_summary.md)

Replay figure: [../figs/fig_maassim_common_state_replay.png](../figs/fig_maassim_common_state_replay.png)

Replay readout: nearest is not exactly optimal on the fixed candidate states; it pays about `3.06` seconds extra pickup wait per active snapshot relative to the immediate wait oracle. PACT, PACT+, and Oracle are effectively wait-oracle on this replay. The observed gap in the closed-loop Persona v2 main table is therefore a state-distribution effect, not a one-step matching error by PACT.

PACT persona-mechanism replay uses the same common states but changes only the driver-persona belief source inside PACT.

| Variant | Belief source | Utility | Served | Driver rejects | Driver accept | Policy rule acc |
|---|---|---:|---:|---:|---:|---:|
| PACT-prior | uniform prior | 11.11 +/- 10.74 | 29.8 | 25.1 | 0.635 | 0.500 |
| PACT-shuffled | learned posterior, shuffled across drivers | 6.87 +/- 9.55 | 29.0 | 26.5 | 0.609 | 0.521 |
| PACT | learned posterior | 27.61 +/- 11.65 | 33.3 | 18.5 | 0.740 | 0.720 |
| Oracle | true hidden persona | 38.92 +/- 11.17 | 34.7 | 13.2 | 0.822 | 1.000 |

Mechanism table: [../analysis/courier_dispatch_maassim/maassim_pact_persona_mechanism_summary.md](../analysis/courier_dispatch_maassim/maassim_pact_persona_mechanism_summary.md)

Mechanism figure: [../figs/fig_maassim_pact_persona_mechanism.png](../figs/fig_maassim_pact_persona_mechanism.png)

Mechanism readout: PACT improves utility over PACT-prior by `16.50` and closes `59.3%` of the prior-to-oracle utility gap. Shuffling learned posteriors across drivers destroys the gain, which supports the mechanism claim that PACT's improvement comes from using recovered persona beliefs attached to the correct driver.

LLM direct-dispatch smoke is now connected through CloudGPT. All LLM-family baselines see a legal one-to-one assignment menu and return JSON with `assignment_id` plus copied `candidate_ids`. The assisted `LLM+PACT-score` policy additionally receives assignment-level PACT-style expected accepts, expected driver rejects, estimated utility, and risk summaries; it is not a pure prompt baseline.

Persona-stress LLM prompt baseline comparison (`driver_reject_penalty=5.0`, `5` seeds, `20` active snapshots per seed):

| Policy | Utility | Served | Driver rejects | Driver accept | Extra wait/snapshot | LLM parse | LLM repair | LLM fallback |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Nearest | 12.70 +/- 11.83 | 19.6 | 5.4 | 0.822 | 1.66 | n/a | n/a | n/a |
| Random | -27.12 +/- 7.54 | 13.6 | 8.8 | 0.716 | 120.77 | n/a | n/a | n/a |
| LLM-PACT | 18.37 +/- 10.12 | 20.2 | 4.2 | 0.862 | 5.97 | 1.000 | 0.000 | 0.000 |
| LLM-belief | 13.47 +/- 9.94 | 19.4 | 5.0 | 0.835 | 3.06 | 1.000 | 0.000 | 0.000 |
| LLM-PSRL | 13.77 +/- 11.14 | 19.6 | 5.0 | 0.835 | 6.69 | 1.000 | 0.000 | 0.000 |
| A-ToM-0 | 12.67 +/- 11.34 | 19.6 | 5.4 | 0.822 | 1.46 | 1.000 | 0.000 | 0.000 |
| A-ToM-1 | 12.77 +/- 11.46 | 19.6 | 5.4 | 0.822 | 0.62 | 1.000 | 0.000 | 0.000 |
| ECON-BNE | 12.48 +/- 11.47 | 19.6 | 5.4 | 0.822 | 1.76 | 1.000 | 0.000 | 0.000 |
| Oracle | 36.44 +/- 5.09 | 20.6 | 0.4 | 0.989 | 18.48 | n/a | n/a | n/a |

Stress LLM prompt baseline table: [../analysis/courier_dispatch_maassim/maassim_llm_prompt_stress_s5_m20.md](../analysis/courier_dispatch_maassim/maassim_llm_prompt_stress_s5_m20.md)

Stress LLM prompt baseline figure: [../figs/fig_maassim_llm_prompt_stress_s5_m20.png](../figs/fig_maassim_llm_prompt_stress_s5_m20.png)

Prompt comparison: [../analysis/courier_dispatch_maassim/maassim_llm_prompt_variant_comparison.md](../analysis/courier_dispatch_maassim/maassim_llm_prompt_variant_comparison.md)

A-ToM / ECON-BNE comparison: [../analysis/courier_dispatch_maassim/maassim_llm_atom_baseline_comparison.md](../analysis/courier_dispatch_maassim/maassim_llm_atom_baseline_comparison.md)

Persona-stress comparison: [../analysis/courier_dispatch_maassim/maassim_llm_prompt_stress_comparison.md](../analysis/courier_dispatch_maassim/maassim_llm_prompt_stress_comparison.md)

Scenario-suite table: [../analysis/courier_dispatch_maassim/maassim_llm_scenario_suite_summary.md](../analysis/courier_dispatch_maassim/maassim_llm_scenario_suite_summary.md)

Scenario-suite figure: [../figs/fig_maassim_llm_scenario_suite.png](../figs/fig_maassim_llm_scenario_suite.png)

Animated comparison GIF: [../figs/fig_maassim_llm_prompt_stress_comparison.gif](../figs/fig_maassim_llm_prompt_stress_comparison.gif)

Fig5-style policy trace GIF: [../figs/fig_maassim_fig5_policy_trace_comparison.gif](../figs/fig_maassim_fig5_policy_trace_comparison.gif)

Conflict-offer people-and-cars replay GIF: [../figs/fig_maassim_conflict_people_cars_llm_pact_vs_prompts.gif](../figs/fig_maassim_conflict_people_cars_llm_pact_vs_prompts.gif)

Full smaller A-ToM smoke table: [../analysis/courier_dispatch_maassim/maassim_llm_atom_baselines_s2_m12.md](../analysis/courier_dispatch_maassim/maassim_llm_atom_baselines_s2_m12.md)

LLM readout: the legal-assignment menu prompt reaches `1.000` parse rate with `0.000` repair and fallback rates across LLM-PACT, LLM-belief, LLM-PSRL, A-ToM, and ECON-BNE. Under persona stress, LLM-PACT is higher than every pure LLM prompt baseline: `18.37` vs `13.77` for LLM-PSRL, `13.47` for LLM-belief, and `12.48-12.77` for A-ToM/ECON-BNE. This is the fair LLM-vs-LLM comparison; PACT itself remains a mechanism/reference policy.

Scenario-suite readout: the LLM-PACT advantage grows as the environment makes persona mistakes more consequential. The utility gap over the best pure prompt baseline is `+1.47` in the normal replay, `+4.60` under reject-cost stress, and `+39.69` under conflict-offer stress, where low-wait offers are made persona-risky.

## Visualizations

Two smoke visualizations are generated from the controlled synthetic run:

| Figure | Description |
|---|---|
| [../figs/fig_maassim_controlled_smoke_overview.png](../figs/fig_maassim_controlled_smoke_overview.png) | Queue dynamics, PACT assignment activity, posterior P(true) trajectories, and final recovery by driver |
| [../figs/fig_maassim_controlled_smoke_map.png](../figs/fig_maassim_controlled_smoke_map.png) | Nootdorp graph with observed driver positions, request origins, and destinations from the smoke |
| [../figs/fig_maassim_controlled_vehicle_trace.png](../figs/fig_maassim_controlled_vehicle_trace.png) | Fig5-style trace for the most eventful vehicle, with empty/reposition vs passenger-carrying route segments |
| [../figs/fig_maassim_controlled_smoke_animation.gif](../figs/fig_maassim_controlled_smoke_animation.gif) | Lightweight animated replay of vehicle positions through the smoke run |
| [../figs/fig_maassim_controlled_baselines.png](../figs/fig_maassim_controlled_baselines.png) | First baseline comparison over seeds `{0,1,2,3,4}` |
| [../figs/fig_maassim_batch_controlled_baselines.png](../figs/fig_maassim_batch_controlled_baselines.png) | Batch-matching baseline comparison with larger queues |
| [../figs/fig_maassim_kpi_calibration_sweep.png](../figs/fig_maassim_kpi_calibration_sweep.png) | KPI wait/reject calibration heatmap |
| [../figs/fig_maassim_common_state_replay.png](../figs/fig_maassim_common_state_replay.png) | Common-state replay comparison against the immediate wait oracle |
| [../figs/fig_maassim_pact_persona_mechanism.png](../figs/fig_maassim_pact_persona_mechanism.png) | PACT prior/shuffled/learned/oracle persona-mechanism replay |
| [../figs/fig_maassim_llm_replay_smoke_s2_m12.png](../figs/fig_maassim_llm_replay_smoke_s2_m12.png) | CloudGPT LLM direct-dispatch common-state smoke |
| [../figs/fig_maassim_llm_replay_scored_s2_m12.png](../figs/fig_maassim_llm_replay_scored_s2_m12.png) | CloudGPT LLM scored-menu common-state smoke |
| [../figs/fig_maassim_llm_atom_baselines_s2_m12.png](../figs/fig_maassim_llm_atom_baselines_s2_m12.png) | CloudGPT LLM-scored vs A-ToM and ECON-BNE common-state smoke |
| [../figs/fig_maassim_llm_atom_core_s5_m20.png](../figs/fig_maassim_llm_atom_core_s5_m20.png) | Scaled CloudGPT LLM+PACT-score vs A-ToM and ECON-BNE core comparison |
| [../figs/fig_maassim_llm_prompt_stress_s5_m20.png](../figs/fig_maassim_llm_prompt_stress_s5_m20.png) | Persona-stress LLM-PACT vs LLM-belief, LLM-PSRL, A-ToM, and ECON-BNE comparison |
| [../figs/fig_maassim_llm_scenario_suite.png](../figs/fig_maassim_llm_scenario_suite.png) | Scenario suite showing LLM-PACT gap growth from normal to reject-stress to conflict-offer environments |
| [../figs/fig_maassim_llm_prompt_stress_comparison.gif](../figs/fig_maassim_llm_prompt_stress_comparison.gif) | Animated persona-stress LLM-PACT vs prompt-baseline comparison for README/GitHub presentation |
| [../figs/fig_maassim_fig5_policy_trace_comparison.gif](../figs/fig_maassim_fig5_policy_trace_comparison.gif) | Focused Fig5-style route trace window where LLM-PACT has fewer rejected pickup attempts than LLM-PSRL, A-ToM-1, and ECON-BNE |
| [../figs/fig_maassim_conflict_people_cars_llm_pact_vs_prompts.gif](../figs/fig_maassim_conflict_people_cars_llm_pact_vs_prompts.gif) | Conflict-offer full-episode people-and-cars replay in the MaaSSim README style: LLM-PACT vs LLM-PSRL, A-ToM-1, and ECON-BNE |

They are also copied to `arr_paper/figs/`.

## Current Performance Caveat

The early controlled smokes use the structured PACT policy and synthetic hidden driver rules inside MaaSSim. The new LLM direct-dispatch smoke is connected separately through common-state replay. The legal-assignment menu prompt now gives stable JSON output across LLM-PACT and pure prompt baselines. LLM-PACT is assisted by PACT-style assignment scores; pure prompt baselines are LLM-belief, LLM-PSRL, A-ToM-0, A-ToM-1, and ECON-BNE. The persona-stress run is a stronger LLM-vs-LLM diagnostic, but still not a final closed-loop MaaSSim significance claim.

To reproduce from the repo root:

```powershell
$env:PYTHONPATH="$PWD\external\maassim;$PWD"
uv run python scripts/run_maassim_shadow_smoke.py --config external\maassim\MaaSSim\data\config.json --root-path external\maassim\MaaSSim --out analysis\courier_dispatch_maassim\shadow_queue_snapshots.jsonl
uv run python scripts/run_maassim_shadow_smoke.py --config external\maassim\MaaSSim\data\config.json --root-path external\maassim\MaaSSim --policy pact --beta 0.25 --out analysis\courier_dispatch_maassim\pact_shadow_queue_snapshots.jsonl
uv run python scripts/run_maassim_shadow_smoke.py --config external\maassim\MaaSSim\data\config.json --root-path external\maassim\MaaSSim --policy pact --beta 0.25 --synthetic-rules --out analysis\courier_dispatch_maassim\pact_synthetic_shadow_queue_snapshots.jsonl --posterior-out analysis\courier_dispatch_maassim\synthetic_rule_posterior.csv
uv run python scripts/run_maassim_shadow_smoke.py --seed 0 --config external\maassim\MaaSSim\data\config.json --root-path external\maassim\MaaSSim --policy pact --beta 0.25 --control-match --synthetic-rules --intervene-driver-rules --out analysis\courier_dispatch_maassim\pact_controlled_synthetic_queue_snapshots.jsonl --posterior-out analysis\courier_dispatch_maassim\controlled_synthetic_rule_posterior.csv
uv run python scripts/plot_maassim_integration_smoke.py
uv run python scripts/summarize_maassim_baselines.py
uv run python scripts/run_maassim_shadow_smoke.py --seed 0 --config external\maassim\MaaSSim\data\config.json --root-path external\maassim\MaaSSim --n-passengers 40 --n-vehicles 8 --batch-time 120 --policy pact --control-match --synthetic-rules --intervene-driver-rules --passenger-personas --persona-assignment random --out analysis\courier_dispatch_maassim\persona_v2_random_smoke_queue_snapshots.jsonl --posterior-out analysis\courier_dispatch_maassim\persona_v2_random_smoke_driver_posterior.csv --passenger-posterior-out analysis\courier_dispatch_maassim\persona_v2_random_smoke_passenger_posterior.csv --persona-out analysis\courier_dispatch_maassim\persona_v2_random_smoke_personas.json --summary-out analysis\courier_dispatch_maassim\persona_v2_random_smoke_summary.json
```

Required lightweight packages in the current uv environment are `dotmap`, `simpy`, `osmnx`, `exmas==0.9.99`, `scipy`, and `scikit-learn`.

## First Metrics

Shadow mode should report:

- number of queue snapshots observed
- driver event counts: request received, accepted, rejected, repositioned, opted out
- posterior concentration if hidden synthetic driver rules are injected
- compatibility of MaaSSim offers with the four CourierDispatch rule features

Closed-loop mode should add:

- wait time
- served requests
- driver idle time
- rejected offers
- total platform fare/revenue proxy
- regret only if we can construct a counterfactual oracle over the same queued pairs

## Design Decision

Do not replace CourierDispatch-Rules v1. Keep it as the controlled analytic benchmark and use MaaSSim as a new substrate. The right abstraction is:

```text
simulator substrate -> adapter snapshot -> PACT posterior/value layer -> assignment -> simulator substrate
```

The current analytic environment remains valuable because it exposes true hidden rules and exact oracle regret. MaaSSim adds ecological validity: real queues, space-time travel, two-sided accept/reject, and driver repositioning.
