# PACT AAAI-27 评审响应实验执行报告

版本 2026-07-14。对应 review 的 logprob/likelihood 鲁棒性、projection 敏感性、persona 库误设与 planner 敏感性问题。

## Executive status

| experiment | status source |
|---|---|
| E-R1 | `e_r1_noise_analytic_mixed.csv` (actual outcome-likelihood interface; token-logprob path unavailable) |
| E-R2 | `e_r2_loo_analytic_mixed.csv`, `e_r2_expansion_analytic_mixed.csv` |
| E-R3 | `e_r3_menu_corruption.csv` + per-cell raw checkpoints |
| E-R4 | `e_r4_planner_concordia.csv` |
| E-R0 | `e_r0_maassim_per_seed.csv` cache-first/live-fill reconstruction (not recovered original rows) |

## Deadline matrix

| item | spec deadline | execution status |
|---|---|---|
| E-R1 data | 2026-07-22 | completed 2026-07-14 on the actual outcome-likelihood interface; requested token-logprob route blocked by absent data/API |
| E-R2 data | 2026-07-24 | PACT-family LOO/expansion completed 2026-07-14; prompt-baseline comparison explicitly blocked |
| E-R3 data | 2026-07-25 | checkpointed live run; final status below |
| E-R4 Concordia | 2026-07-25 | completed 2026-07-14 |
| E-R0 | same window | cache-first/live-fill checkpointed run; final status below |
| full text | 2026-07-28 | data/report artifact prepared for integration |
| supplement | 2026-07-31 | raw checkpoints and full CSVs retained |

## Infrastructure audit

- No retained `.npy`/`.npz` headline calibration tensor, posterior history, or raw token log-score cache was found in the workspace or 56 local ZIP archives.
- The ManagedProvider wrapper does not request or expose token logprobs/top-k logprobs. Azure authentication and a GPT-5.4-nano text call were verified on 2026-07-14.
- Official SOTOPIA data were restored from public `cmu-lti/sotopia` (`benchmark_agents.json`, `sotopia_episodes_v1_hf.jsonl`), and a Python 3.12 SOTOPIA 0.1.5 environment was rebuilt.
- SOTOPIA input SHA-256 (canonical `config/aaai27_sotopia_input_manifest.csv`): `benchmark_agents.json` `341cc03ec8e02a890beedb2d20f85e8a134d9f2a62a9198054965c2651c55f13`; `sotopia_episodes_v1_hf.jsonl` `3a282406c85f5d3c2b6a955c15e758573ef1b7d2a219d50cde29a9b7976611b7`; reconstructed 70-case cache `17b08ac995a8c3d8e126ff8525c358743f75550d32622982175a230575e2e482`. The 180 MB public JSONL is referenced by URL/hash rather than duplicated in the reviewer ZIP.
- Concordia upstream was restored and compact analytic payoff imports were verified.
- The original MaaSSim scenario-suite per-seed rows were deleted. The aggregate detail CSV, queue snapshots, persona maps, and a locally augmented direct-dispatch replay cache remain, allowing a provenance-labelled per-seed reconstruction and aggregate cross-check.
- Critical SOTOPIA audit finding: the pre-spec adapter read partner evidence from the agent inbox, but SOTOPIA 0.1.5 delivers it in `Observation.last_turn`; published-style runs therefore recorded zero numeric posterior updates. The update path was corrected before E-R3, and every eligible update/corruption event is now audited in raw output.

## E-R1 Likelihood-channel noise robustness (HP-SPGG)

**Status:** completed offline outcome-likelihood replay; 15,000 rows, 500 paired seeds, zero LLM calls.

**Infrastructure decision.** The cleaned workspace and all local ZIPs contain no headline c19 calibration tensors, posterior-history NPZs, or per-(episode, step, agent, candidate) token log-scores. The ManagedProvider wrapper returns text only and does not request `logprobs`. Therefore the spec's four-backbone token-logprob replay and one-backbone token-logprob rerun are not executable from the retained infrastructure. This delivered experiment perturbs the actual reported Gaussian outcome-likelihood interface on the analytic mixed-backend HP-SPGG surface; it must not be described as a token-logprob result.

The requested five-seed grid was expanded to 500 paired seeds because reference regret is near zero. Environment/policy randomness is shared across perturbation levels, while likelihood-noise randomness uses a separate reproducible stream so the intervention cannot change the policy RNG sequence.

| variant | perturbation | level | regret K=20 | exact-type mass K=20 |
|---|---|---:|---:|---:|
| pact | additive_log_noise | 0.0 | 0.0117 $\pm$ 0.0016 | 0.9951 |
| pact | additive_log_noise | 0.1 | 0.0121 $\pm$ 0.0017 | 0.9941 |
| pact | additive_log_noise | 0.25 | 0.0121 $\pm$ 0.0018 | 0.9876 |
| pact | additive_log_noise | 0.5 | 0.0167 $\pm$ 0.0032 | 0.9554 |
| pact | additive_log_noise | 1.0 | 0.0214 $\pm$ 0.0039 | 0.8606 |
| pact | additive_log_noise | 2.0 | 0.0318 $\pm$ 0.0055 | 0.7200 |
| pact | temperature | 0.5 | 0.0081 $\pm$ 0.0013 | 0.9998 |
| pact | temperature | 0.7 | 0.0100 $\pm$ 0.0014 | 0.9991 |
| pact | temperature | 1.0 | 0.0117 $\pm$ 0.0016 | 0.9951 |
| pact | temperature | 1.5 | 0.0139 $\pm$ 0.0018 | 0.9800 |
| pact | temperature | 2.0 | 0.0174 $\pm$ 0.0021 | 0.9580 |
| pact | top_k | 1 | 0.0055 $\pm$ 0.0011 | 1.0000 |
| pact | top_k | 3 | 0.0118 $\pm$ 0.0016 | 0.9951 |
| pact | top_k | 5 | 0.0117 $\pm$ 0.0016 | 0.9951 |
| pact | top_k | full | 0.0117 $\pm$ 0.0016 | 0.9951 |
| pact_plus | additive_log_noise | 0.0 | 0.0017 $\pm$ 0.0003 | 0.9953 |
| pact_plus | additive_log_noise | 0.1 | 0.0016 $\pm$ 0.0003 | 0.9943 |
| pact_plus | additive_log_noise | 0.25 | 0.0017 $\pm$ 0.0003 | 0.9877 |
| pact_plus | additive_log_noise | 0.5 | 0.0021 $\pm$ 0.0004 | 0.9549 |
| pact_plus | additive_log_noise | 1.0 | 0.0060 $\pm$ 0.0013 | 0.8602 |
| pact_plus | additive_log_noise | 2.0 | 0.0175 $\pm$ 0.0040 | 0.7211 |
| pact_plus | temperature | 0.5 | 0.0016 $\pm$ 0.0003 | 0.9999 |
| pact_plus | temperature | 0.7 | 0.0019 $\pm$ 0.0003 | 0.9992 |
| pact_plus | temperature | 1.0 | 0.0017 $\pm$ 0.0003 | 0.9953 |
| pact_plus | temperature | 1.5 | 0.0019 $\pm$ 0.0004 | 0.9803 |
| pact_plus | temperature | 2.0 | 0.0024 $\pm$ 0.0005 | 0.9583 |
| pact_plus | top_k | 1 | 0.0019 $\pm$ 0.0004 | 1.0000 |
| pact_plus | top_k | 3 | 0.0017 $\pm$ 0.0003 | 0.9953 |
| pact_plus | top_k | 5 | 0.0017 $\pm$ 0.0003 | 0.9953 |
| pact_plus | top_k | full | 0.0017 $\pm$ 0.0003 | 0.9953 |

### Regret-doubling threshold $\sigma^*$

- **pact:** reference regret 0.01175; $\sigma^*=2$ using the monotone regret envelope.
- **pact_plus:** reference regret 0.00166; $\sigma^*=1$ using the monotone regret envelope.
- The HP-SPGG library has four candidates, so requested top-$5$ truncation is exactly the same operation as `full`; only top-$1$ and top-$3$ are nontrivial truncations.
- PACT+ reference regret is near zero, so its doubling threshold is ratio-unstable; the absolute regret curve and posterior mass should be reported alongside $\sigma^*$.

## E-R2 Persona-library misspecification (HP-SPGG)

**Status:** PACT-family offline outcome-likelihood LOO completed (40 rows). Prompt-baseline LOO was not run because retained A-ToM/LLM-belief trajectories are absent and those baselines do not share PACT's discrete tracker library; 40 explicit not-run rows are retained rather than fabricated.

| excluded persona | variant | LOO regret | in-library regret | degradation | final entropy | modal proxy type |
|---|---|---:|---:|---:|---:|---|
| altruistic_builder | pact | 0.0000 | 0.0000 | 0.0000 | 0.0000 | conditional_cooperator / conditional_cooperator / conditional_cooperator |
| altruistic_builder | pact_plus | 0.0000 | 0.0000 | 0.0000 | 0.0000 | conditional_cooperator / conditional_cooperator / conditional_cooperator |
| conditional_cooperator | pact | 0.0000 | 0.0000 | 0.0000 | 0.0155 | altruistic_builder / altruistic_builder / altruistic_builder |
| conditional_cooperator | pact_plus | 0.0000 | 0.0000 | 0.0000 | 0.0155 | altruistic_builder / altruistic_builder / altruistic_builder |
| free_rider | pact | 0.0000 | 0.0037 | -0.0037 | 0.0000 | risk_averse_balancer / risk_averse_balancer / risk_averse_balancer |
| free_rider | pact_plus | 0.0000 | 0.0031 | -0.0031 | 0.0000 | risk_averse_balancer / risk_averse_balancer / risk_averse_balancer |
| risk_averse_balancer | pact | 0.0000 | 0.0000 | 0.0000 | 0.0033 | conditional_cooperator / free_rider / conditional_cooperator |
| risk_averse_balancer | pact_plus | 0.0000 | 0.0000 | 0.0000 | 0.0033 | conditional_cooperator / free_rider / conditional_cooperator |

The in-library regret floor is nearly zero, so relative degradation ratios are unstable. Small negative degradation means that the finite-seed LOO replay happened to incur slightly less regret; it is not evidence that excluding a true persona is generally beneficial.

### Library expansion

| distractors | variant | regret K=20 | exact-type mass | final entropy |
|---:|---|---:|---:|---:|
| 0 | pact | 0.0135 | 0.9961 | 0.0209 |
| 0 | pact_plus | 0.0000 | 0.9961 | 0.0209 |
| 2 | pact | 0.0000 | 0.8950 | 0.2787 |
| 2 | pact_plus | 0.0000 | 0.8950 | 0.2787 |
| 4 | pact | 0.0149 | 0.8384 | 0.3977 |
| 4 | pact_plus | 0.0000 | 0.8354 | 0.3981 |

**Convex-mixture decision:** not used as a prompt-level persona experiment. The current HP-SPGG player behavior is generated from fixed reward templates rather than a continuously mixed persona prompt. The earlier analytic reward-mixture diagnostic is therefore not promoted as satisfying the reviewer's prompt-level convex-mixture request.

## E-R3 SOTOPIA intent-menu corruption

**Status:** 480/480 episode rows checkpointed (complete grid).
Planned design per p: 30 official target cases repeated four times (120 episodes): 20 craigslist cases (80 episodes), five donate cases (20), and five revenge cases (20). Replicates are independent provider generations, not deterministic resampling of a stored trajectory.
Displayed score SEMs are descriptive episode-row SEMs. Confirmatory uncertainty should cluster or bootstrap by `combo_pk` because each official case contributes four generations; the episode-level CSV retains both case and replicate identifiers.
The spec-mandated legacy column `focal_score` equals the arithmetic mean of `episode.overall.agent_1` and `episode.overall.agent_2` in symmetric SOTOPIA self-play; it is not an agent-1-only focal reward. Historical comparators use the same formula.
Caught provider-call generation fallbacks: 0/2880; triggered permutation events: 384/2399 eligible updates. The experiment uses the corrected Observation.last_turn update path; the pre-spec adapter's inbox path produced zero posterior updates and is documented below. This counter catches provider exceptions only. The stored schema does not separately count malformed/invalid/missing action fields that the action parser defaults, or missing/non-numeric evaluator dimensions that score normalization maps to zero; hence zero provider fallbacks is not a zero-schema-default guarantee.
`corruption_events` counts seeded permutation triggers. If an utterance yields tied keyword increments (especially an all-zero vector), permuting indices can leave the numeric vector unchanged; the recorded rate is therefore a trigger rate, not an effective-vector-change rate.
Release cleaning retained already-clean checkpoints, discarded every accepted episode with a caught provider-call fallback, and reran the affected case under up to five provider attempts per call and five whole-episode attempts at concurrency 2--4. The legacy checkpoint schema did not retain discarded attempts or transient failure history, so final zero counts describe accepted episodes rather than provider reliability; retry settings are documented from the execution log, not recovered from each raw record. The final validator checks all 16 raw cells as well as the aggregate CSV.
After completion, all 16 cells were migrated to checkpoint schema v2 only after legacy episode metadata matched the intended model, evaluator, strategy, corruption level/seed, and target IDs. Each raw file now carries an immutable run signature with turns and SHA-256 input hashes; this migration does not recreate the discarded legacy attempt history.
Case and replicate IDs are paired across p, but the ManagedProvider chat endpoint exposes no sampling-seed control; LLM generations are therefore not pathwise coupled. Paired tests reduce case-composition variance but still include provider-generation and judge variance, so E-R3 is a sensitivity bound rather than a pure causal projection ablation.
The corruption RNG is SHA-256-derived from the same (base seed, case, agent, replicate) tuple at every p. It is fully reproducible, but the same stream supplies both trigger draws and conditional permutation shuffles, so masks are not guaranteed to be nested across p. LLM generation/judge randomness is also uncoupled. The best-alternative comparator is a retained historical GPT-nano aggregate, not a contemporaneous rerun under the same judge draws; p* below is therefore an operational threshold against that retained reference, not a strictly causal crossover estimate.
Comparator provenance: `config/aaai27_sotopia_historical_comparators.csv`, derived from the GPT-5.4-nano per-codename table in `analysis/sotopia_tuned_all70_full_report.md`. Craigslist aggregates its four five-episode codenames before selecting the best among A-ToM-1, ECON-BNE, llm-belief, and llm-greedy; donate and revenge each have one five-episode codename. LLM-PSRL was later recovered only as a cross-backbone family aggregate in `packaged_results/sotopia_font13_recovered_aggregates.json`, so it cannot be included in a GPT-nano-only comparator. The original episode JSONs listed by that report are no longer retained.
The positive family margins quoted for the original figure average all four backbones, whereas this corruption suite follows the spec's one-backbone GPT-nano design. The GPT-specific operational p* is therefore a different estimand and must not be substituted for the cross-backbone historical margin.

| p | episodes | eligible updates | permutation triggers | trigger rate | generation calls | provider-exception fallbacks |
|---:|---:|---:|---:|---:|---:|---:|
| 0.0 | 120 | 600 | 0 | 0.0000 | 720 | 0 |
| 0.1 | 120 | 600 | 73 | 0.1217 | 720 | 0 |
| 0.2 | 120 | 599 | 121 | 0.2020 | 720 | 0 |
| 0.3 | 120 | 600 | 190 | 0.3167 | 720 | 0 |

| family | p | episodes | focal score | paired delta vs p=0 | delta vs historical four-baseline best |
|---|---:|---:|---:|---:|---:|
| craigslist_bargains | 0.0 | 80 | 2.6652 $\pm$ 0.0739 | 0.0000 $\pm$ 0.0000 | -0.0953 |
| craigslist_bargains | 0.1 | 80 | 2.6580 $\pm$ 0.0755 | -0.0071 $\pm$ 0.1018 | -0.1025 |
| craigslist_bargains | 0.2 | 80 | 2.6027 $\pm$ 0.0722 | -0.0625 $\pm$ 0.0905 | -0.1578 |
| craigslist_bargains | 0.3 | 80 | 2.6420 $\pm$ 0.0758 | -0.0232 $\pm$ 0.0886 | -0.1185 |
| donate_funds | 0.0 | 20 | 3.2286 $\pm$ 0.1208 | 0.0000 $\pm$ 0.0000 | -0.1574 |
| donate_funds | 0.1 | 20 | 3.3571 $\pm$ 0.1370 | 0.1286 $\pm$ 0.1835 | -0.0289 |
| donate_funds | 0.2 | 20 | 3.1179 $\pm$ 0.1695 | -0.1107 $\pm$ 0.1916 | -0.2681 |
| donate_funds | 0.3 | 20 | 3.4607 $\pm$ 0.1143 | 0.2321 $\pm$ 0.1562 | 0.0747 |
| revenge_plot | 0.0 | 20 | 2.7429 $\pm$ 0.1024 | 0.0000 $\pm$ 0.0000 | -0.4571 |
| revenge_plot | 0.1 | 20 | 2.8643 $\pm$ 0.1261 | 0.1214 $\pm$ 0.1578 | -0.3357 |
| revenge_plot | 0.2 | 20 | 2.6750 $\pm$ 0.1205 | -0.0679 $\pm$ 0.1184 | -0.5250 |
| revenge_plot | 0.3 | 20 | 2.7786 $\pm$ 0.0731 | 0.0357 $\pm$ 0.1151 | -0.4214 |

### Advantage-disappearance threshold $p^*$

- **craigslist_bargains:** historical GPT-5.4-nano four-baseline-best mean 2.7605; $p^*=0$.
- **donate_funds:** historical GPT-5.4-nano four-baseline-best mean 3.3860; $p^*=0$.
- **revenge_plot:** historical GPT-5.4-nano four-baseline-best mean 3.2000; $p^*=0$.
- The corrected GPT-nano $p=0$ run has no positive margin against the retained four-baseline comparator in any selected family. Thus the spec's conditional 'advantage disappearance' test is not activated: $p^*=0$ is bookkeeping for an absent initial advantage, not evidence that $p=0.1$ corruption caused a crossover. Interpret the within-run paired deltas instead.
- Across the tested grid, family-level paired mean changes are non-monotone and of the same order as their descriptive SEMs. Together with uncoupled provider/judge randomness, this supports no monotone causal dose-response claim for menu corruption.

**Projection-accuracy boundary:** per-family projection accuracy remains non-identifiable because SOTOPIA has no native labels for the project's four keyword classes. E-R3 measures intervention sensitivity, not projection accuracy.

## E-R4 Planner sensitivity (compact Concordia)

**Status:** completed; 18 configurations, 54 aggregate rows, zero LLM calls.

| solver | configs | mean focal gap vs exact | worst gap | exact ties | mean wall-time ms |
|---|---:|---:|---:|---:|---:|
| exact_enumeration | 18 | 0.0000 | 0.0000 | 18 | 9.5872 |
| greedy_br_1pass | 18 | -3.7849 | -14.6000 | 4 | 0.1150 |
| iterated_br_3pass | 18 | -3.7849 | -14.6000 | 4 | 0.3133 |

### By substrate

| substrate | solver | configs | mean focal gap | worst gap |
|---|---|---:|---:|---:|
| haggling | greedy_br_1pass | 5 | -6.4944 | -13.4000 |
| haggling | iterated_br_3pass | 5 | -6.4944 | -13.4000 |
| haggling_multi_item | greedy_br_1pass | 4 | -8.8875 | -14.6000 |
| haggling_multi_item | iterated_br_3pass | 4 | -8.8875 | -14.6000 |
| pub_coordination | greedy_br_1pass | 9 | -0.0118 | -0.0259 |
| pub_coordination | iterated_br_3pass | 9 | -0.0118 | -0.0259 |

**Definition:** one-pass BR updates each agent once in deterministic order against the current joint action; three-pass BR repeats that sweep three times. Pub agents optimise own analytic pub payoff. In haggling, buyer and seller optimise their own payoff sequentially. Exact enumeration maximises the reported focal objective. Tracker/case information is fixed before solver timing.

**HP-SPGG n=5 half:** not run. The spec marks it contingent on remaining budget after E-R1--E-R3; the active budget was assigned to the 480-episode E-R3 live suite and E-R0 cache/live reconstruction. The complete zero-call Concordia half is delivered.

## E-R0 MaaSSim per-seed paired rows

**Status:** 130/130 unique (scenario, variant, seed) rows. Replay decision cache hit rate during this run: 1323/1700 (0.778); live-filled decisions: 377. Current cache keys after live-fill: 3846. The pre-spec package intentionally excluded filenames containing `cache`, and no historical cache copy was found in the pre-experiment audit of 56 retained ZIPs.

**Provenance:** the original scenario-suite per-seed CSVs were deleted during cleanup. These rows are a deterministic state/persona replay with the current v7 assignment-ID runner, reusing matching cached decisions and live-filling missing current-schema keys. They are suitable for new paired analyses but are not byte-for-byte recovery of the deleted original run; compare aggregate means before replacing published SEMs.

| scenario | variant | utility | rejects | wait |
|---|---|---:|---:|---:|
| conflict_p5 | atom_tom0 | -49.212 $\pm$ 4.715 | 13.800 $\pm$ 0.663 | 104.173 $\pm$ 6.992 |
| conflict_p5 | atom_tom1 | -42.432 $\pm$ 3.214 | 12.800 $\pm$ 0.583 | 104.682 $\pm$ 4.908 |
| conflict_p5 | econ_bne | -46.824 $\pm$ 8.021 | 13.400 $\pm$ 1.249 | 104.255 $\pm$ 5.746 |
| conflict_p5 | llm | 8.786 $\pm$ 4.845 | 3.200 $\pm$ 0.583 | 113.199 $\pm$ 8.536 |
| conflict_p5 | llm_belief | -30.900 $\pm$ 4.200 | 10.800 $\pm$ 0.374 | 104.499 $\pm$ 4.600 |
| conflict_p5 | llm_psrl | -32.934 $\pm$ 7.234 | 11.200 $\pm$ 1.114 | 105.639 $\pm$ 4.691 |
| conflict_p5 | nearest | -108.484 $\pm$ 9.625 | 24.200 $\pm$ 1.393 | 119.293 $\pm$ 20.680 |
| conflict_p5 | oracle | 22.440 $\pm$ 4.719 | 1.400 $\pm$ 0.510 | 113.220 $\pm$ 10.391 |
| conflict_p5 | random | -59.146 $\pm$ 9.614 | 13.200 $\pm$ 1.772 | 180.047 $\pm$ 19.275 |
| normal_p2 | atom_tom1 | 28.972 $\pm$ 8.007 | 5.400 $\pm$ 1.208 | 82.684 $\pm$ 10.335 |
| normal_p2 | econ_bne | 28.810 $\pm$ 7.970 | 5.400 $\pm$ 1.208 | 83.450 $\pm$ 10.712 |
| normal_p2 | llm | 31.286 $\pm$ 7.763 | 4.200 $\pm$ 0.800 | 88.616 $\pm$ 13.657 |
| normal_p2 | llm_belief | 28.268 $\pm$ 7.472 | 5.200 $\pm$ 1.114 | 85.019 $\pm$ 10.801 |
| normal_p2 | llm_psrl | 29.814 $\pm$ 7.797 | 4.800 $\pm$ 1.158 | 85.327 $\pm$ 10.335 |
| normal_p2 | nearest | 28.900 $\pm$ 8.345 | 5.400 $\pm$ 1.208 | 82.728 $\pm$ 10.117 |
| normal_p2 | oracle | 37.644 $\pm$ 6.010 | 0.400 $\pm$ 0.400 | 90.106 $\pm$ 14.314 |
| normal_p2 | random | -0.716 $\pm$ 4.167 | 8.800 $\pm$ 1.241 | 144.662 $\pm$ 12.091 |
| stress_p5 | atom_tom0 | 12.818 $\pm$ 11.442 | 5.400 $\pm$ 1.208 | 82.408 $\pm$ 10.332 |
| stress_p5 | atom_tom1 | 12.804 $\pm$ 11.442 | 5.400 $\pm$ 1.208 | 82.484 $\pm$ 10.340 |
| stress_p5 | econ_bne | 12.222 $\pm$ 11.246 | 5.400 $\pm$ 1.208 | 85.215 $\pm$ 10.057 |
| stress_p5 | llm | 18.366 $\pm$ 10.117 | 4.200 $\pm$ 0.800 | 90.522 $\pm$ 14.992 |
| stress_p5 | llm_belief | 13.616 $\pm$ 11.119 | 5.200 $\pm$ 1.114 | 85.651 $\pm$ 11.050 |
| stress_p5 | llm_psrl | 13.502 $\pm$ 11.119 | 5.000 $\pm$ 1.225 | 87.891 $\pm$ 9.194 |
| stress_p5 | nearest | 12.700 $\pm$ 11.829 | 5.400 $\pm$ 1.208 | 82.728 $\pm$ 10.117 |
| stress_p5 | oracle | 36.444 $\pm$ 5.094 | 0.400 $\pm$ 0.400 | 90.106 $\pm$ 14.314 |
| stress_p5 | random | -27.116 $\pm$ 7.543 | 8.800 $\pm$ 1.241 | 144.662 $\pm$ 12.091 |

### Retained aggregate cross-check (21/26 exact cells; max |utility delta|=0.264)

Only non-exact scenario-policy cells are listed. Exact matching of an aggregate does not prove recovery of the original seed ordering; non-exact cells confirm that live-fill cannot be represented as original raw data.

| scenario | variant | retained utility | reconstructed utility | delta | retained/reconstructed rejects | retained/reconstructed served |
|---|---|---:|---:|---:|---:|---:|
| stress_p5 | llm_belief | 13.470 | 13.616 | 0.146 | 5.0 / 5.2 | 19.4 / 19.8 |
| stress_p5 | llm_psrl | 13.766 | 13.502 | -0.264 | 5.0 / 5.0 | 19.6 / 19.6 |
| stress_p5 | atom_tom0 | 12.674 | 12.818 | 0.144 | 5.4 / 5.4 | 19.6 / 19.6 |
| stress_p5 | atom_tom1 | 12.768 | 12.804 | 0.036 | 5.4 / 5.4 | 19.6 / 19.6 |
| stress_p5 | econ_bne | 12.482 | 12.222 | -0.260 | 5.4 / 5.4 | 19.6 / 19.6 |

## Optional conflict-p2 completion

**Status:** not run. This was explicitly optional rebuttal ammunition; resources were prioritised to the required E-R3 live corruption grid and E-R0 per-seed reconstruction.

## Deliverables and integrity

| file | rows/bytes | SHA-256 |
|---|---:|---|
| `analysis/aaai27_review/e_r1_noise_analytic_mixed.csv` | 15000 rows | `9f61cbd582eba2a693a1e3341f91d8e02aa0cf8b5132eb14f25fcf67f72da5a6` |
| `analysis/aaai27_review/e_r2_loo_analytic_mixed.csv` | 80 rows | `999be7e3c265be69293e26a82a21cd990440de4f871dae73eb0f1801ca841ba0` |
| `analysis/aaai27_review/e_r2_expansion_analytic_mixed.csv` | 30 rows | `f1a8801dd3c93bfea08856d2b3bf4a9b8e4eb078aacd0bc041a047d582725e61` |
| `analysis/aaai27_review/e_r3_menu_corruption.csv` | 480 rows | `d176b44fb994353276bd736817715e8b91b097ec9e89ea102a306ea5e546b24d` |
| `analysis/aaai27_review/e_r4_planner_concordia.csv` | 54 rows | `052e6c0b3a06d88855f7824d4afc629074b8e0d8409911a386039932f5883aa0` |
| `analysis/aaai27_review/e_r0_maassim_per_seed.csv` | 130 rows | `8ea5b8f19b313f9f991646f3d7febe27830e26923aeaf244b6a304e082a88017` |
| `analysis/aaai27_review/e_r3_raw/*.json` | 480 checkpointed episodes in 16 files | raw-set manifest `f06d7f5c66cc6a12de2c1dabd4a2fea9c63e2aeaec8a2a33d18e33aae002458c`; per-file hashes in package manifest |

## Claim-safe conclusions

1. E-R1 is evidence about the reported Gaussian outcome-likelihood implementation, not token-logprob robustness; the requested token-logprob claim remains untested because the interface and raw data do not exist.
2. E-R2 quantifies PACT-family discrete-library misspecification only. A-ToM/LLM-belief comparative degradation is unavailable without new live trajectories and a shared discrete-library definition.
3. E-R3 is the first valid recurrent-surrogate sensitivity run after fixing the zero-update adapter bug. It bounds intervention sensitivity but cannot provide projection accuracy.
4. E-R4 cleanly separates tracker from planner under analytic payoffs; agent-wise BR can converge to a low-focal equilibrium even when exact focal enumeration is cheap.
5. E-R0 is a cache-first/live-fill reconstruction for new paired analyses, not recovery of deleted original rows. Cache-hit counts and the retained-aggregate cross-check expose the provenance; these rows must not silently replace published original-run SEMs.
