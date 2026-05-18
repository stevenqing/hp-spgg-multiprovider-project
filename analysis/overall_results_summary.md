# HP-SPGG Overall Results Summary

Last updated: 2026-05-17

This file is the current single-page index for the HP-SPGG experiment state. It consolidates the proposed method results, tabular baselines, lightweight LLM baselines, external A-ToM/ECON-style LLM baselines, cross-provider sanity checks, and Phase 2 Concordia/SOTOPIA integration status.

For a file-level manifest of raw `.npz` outputs, summaries, tables, figures, verification scripts, and in-progress cross-model artifacts, see `analysis/results_index.md`.

## Executive Takeaway

On the current strongest CloudGPT/DeepSeek-V3.2 calibration (`c19`, `K=20`), the proposed HP-SPGG native method `hpsmg_plus` is the strongest non-oracle method observed so far.

| Method group | Method | K | Seeds | Final cumulative regret mean | Mean per-round regret | Mean welfare | Source |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Upper bound | `oracle` | 20 | 5 | 0.0000 | 0.0000 | 2.9500 | `results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz` |
| Proposed | `hpsmg_plus` | 20 | 5 | **0.4000** | **0.0200** | 2.7600 | `results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz` |
| Native baseline | `map_greedy` | 20 | 5 | 0.7120 | 0.0356 | 2.7144 | `results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz` |
| Proposed ablation | `hpsmg` | 20 | 5 | 0.8280 | 0.0414 | 2.8526 | `results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz` |
| Bayesian baseline | `joint_psrl` | 20 | 5 | 0.8320 | 0.0416 | 2.8384 | `results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz` |
| Prompted LLM baseline | `llm_belief` | 20 | 5 | 3.0740 | 0.1537 | 2.7363 | `results/cloudgpt/E2_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz` |
| External LLM baseline | `econ_bne` | 20 | 5 | 3.9900 | 0.1995 | 2.6105 | `results/cloudgpt/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz` |
| External LLM baseline | `atom_adaptive_hedge` | 20 | 5 | 4.7900 | 0.2395 | 2.6605 | `results/cloudgpt/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz` |
| Prompted LLM baseline | `llm_greedy` | 20 | 5 | 14.0200 | 0.7010 | 2.1590 | `results/cloudgpt/E2_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz` |

Important comparison note: the native HP-SPGG, prompted LLM, and external A-ToM/ECON baselines now all use `K=20`, `seeds=5`, and the same DeepSeek-V3.2 `c19` calibration.

## Current Best HP-SPGG Native Run

Calibration: `calibration_cloudgpt_multi_model_fast4_8algos_DeepSeek_V3_2_c19.npy`

Summary: `analysis/calibration_cloudgpt_multi_model_fast4_8algos_DeepSeek_V3_2_c19_summary.md`

Best `hpsmg_plus` file: `results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0.npz`

The beta sweep shows `hpsmg_plus` is stable across low-to-moderate beta values and degrades slightly at larger beta.

| beta | oracle | hpsmg_plus | hpsmg | joint_psrl | map_greedy | psrl_notype | iql | random |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.0 | 0.000 | **0.400** | 0.828 | 0.832 | 0.712 | 13.912 | 28.342 | 28.266 |
| 0.05 | 0.000 | **0.400** | 0.828 | 0.832 | 0.712 | 13.912 | 28.342 | 28.266 |
| 0.1 | 0.000 | **0.400** | 0.828 | 0.832 | 0.712 | 13.912 | 28.342 | 28.266 |
| 0.25 | 0.000 | **0.400** | 0.828 | 0.832 | 0.712 | 13.912 | 28.342 | 28.266 |
| 0.5 | 0.000 | **0.400** | 0.828 | 0.832 | 0.712 | 13.912 | 28.342 | 28.266 |
| 0.75 | 0.000 | **0.400** | 0.828 | 0.832 | 0.712 | 13.912 | 28.342 | 28.266 |
| 1.0 | 0.000 | 0.530 | 0.828 | 0.832 | 0.712 | 13.912 | 28.342 | 28.266 |
| 1.5 | 0.000 | 0.630 | 0.828 | 0.832 | 0.712 | 13.912 | 28.342 | 28.266 |

Representative native ranking at `beta=0.25`, `K=20`, `seeds=5`:

| Rank | Algorithm | Final cumulative regret mean | Std | Mean per-round regret | Mean welfare |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | `oracle` | 0.0000 | 0.0000 | 0.0000 | 2.9500 |
| 2 | `hpsmg_plus` | 0.4000 | 0.8000 | 0.0200 | 2.7600 |
| 3 | `map_greedy` | 0.7120 | 0.4663 | 0.0356 | 2.7144 |
| 4 | `hpsmg` | 0.8280 | 0.5414 | 0.0414 | 2.8526 |
| 5 | `joint_psrl` | 0.8320 | 0.0796 | 0.0416 | 2.8384 |
| 6 | `psrl_notype` | 13.9120 | 7.3737 | 0.6956 | 2.1744 |
| 7 | `random` | 28.2660 | 5.1241 | 1.4133 | 1.4767 |
| 8 | `iql` | 28.3420 | 16.9136 | 1.4171 | 1.3969 |

## External A-ToM/ECON-Style LLM Baselines

Completed run: `results/cloudgpt/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz`

Trace: `analysis/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5_trace.json`

Summary: `analysis/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5_summary.md`

Setting: CloudGPT backend, `DeepSeek-V3.2`, `K=20`, `seeds=5`, `econ_rounds=3`.

| Rank | Algorithm | Final cumulative regret mean | Std | Mean per-round regret | Mean welfare |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | `econ_bne` | 3.9900 | 3.4136 | 0.1995 | 2.6105 |
| 2 | `atom_adaptive_hedge` | 4.7900 | 4.5089 | 0.2395 | 2.6605 |
| 3 | `atom_tom0` | 6.0000 | 7.4565 | 0.3000 | 2.5900 |
| 4 | `atom_tom2` | 13.4020 | 10.3200 | 0.6701 | 2.2139 |
| 5 | `atom_adaptive_ftl` | 14.9440 | 1.4313 | 0.7472 | 2.0968 |
| 6 | `atom_tom1` | 16.6760 | 8.2004 | 0.8338 | 2.0182 |

Interpretation: the stronger LLM social-reasoning baselines are much better than random and type-agnostic baselines, but still substantially worse than the HP-SPGG native posterior methods. The current best external LLM method has roughly 10.0x higher cumulative regret than `hpsmg_plus` on the headline c19 setting.

## Lightweight Prompted LLM Baselines

Implementation: `llm_hpgg/run_llm_baselines.py`

Summary: `analysis/llm_baseline_summary.md`

Headline stats and curve: `analysis/E2_native_vs_llm_baselines_stats.md`, `tables/E2_native_vs_llm_baselines.tex`, `figs/E2_native_vs_llm_baselines_main.pdf`

The lightweight baselines test whether a directly prompted LLM coordinator can replace the explicit HP-SPGG posterior.

| Run | Method | K | Seeds | Final cumulative regret mean | Std | Mean welfare | Result file |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Main 5-seed | `llm_belief` | 20 | 5 | 3.0740 | 2.2308 | 2.7363 | `results/cloudgpt/E2_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz` |
| Main 5-seed | `llm_greedy` | 20 | 5 | 14.0200 | 14.6643 | 2.1590 | `results/cloudgpt/E2_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz` |
| Earlier 3-seed | `llm_belief` | 20 | 3 | 4.3567 | 1.9985 | 2.6155 | `results/cloudgpt/E2_llm_baselines_DeepSeek_V3_2_c19_K20_s3.npz` |
| Earlier 3-seed | `llm_greedy` | 20 | 3 | 10.0000 | 7.2572 | 2.3000 | `results/cloudgpt/E2_llm_baselines_DeepSeek_V3_2_c19_K20_s3.npz` |
| Earlier small run | `llm_belief` | 10 | 2 | 2.3300 | 1.3500 | 2.6170 | `results/cloudgpt/E2_llm_baselines_DeepSeek_V3_2_c19_K10_s2.npz` |
| Earlier small run | `llm_greedy` | 10 | 2 | 4.2500 | 4.2500 | 2.4500 | `results/cloudgpt/E2_llm_baselines_DeepSeek_V3_2_c19_K10_s2.npz` |

Interpretation: `llm_belief` is the best lightweight prompted LLM baseline and beats simple type-agnostic baselines, but it remains far behind explicit posterior methods.

## Cross-Provider Sanity Checks

Existing LaTeX tables:

- `tables/E2_sanity_regret.tex`
- `tables/E3_cross_provider_regret.tex`
- `tables/E4_burn_in.tex`

Current cross-provider table indicates that native type-aware methods remain low-regret across provider calibrations, while random remains high-regret.

| Provider | hpsmg_plus | hpsmg | joint_psrl | map_greedy | random | oracle |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| anthropic | 0.019 +/- 0.012 | 0.006 +/- 0.006 | 0.035 +/- 0.032 | 0.000 +/- 0.000 | 14.461 +/- 3.516 | 0.000 +/- 0.000 |
| cloudgpt | 0.012 +/- 0.007 | 0.007 +/- 0.007 | 0.046 +/- 0.031 | 0.000 +/- 0.000 | 14.588 +/- 3.499 | 0.000 +/- 0.000 |
| google | 0.010 +/- 0.006 | 0.006 +/- 0.006 | 0.044 +/- 0.031 | 0.000 +/- 0.000 | 14.560 +/- 3.503 | 0.000 +/- 0.000 |
| openai | 0.005 +/- 0.005 | 0.004 +/- 0.004 | 0.033 +/- 0.033 | 0.000 +/- 0.000 | 14.448 +/- 3.500 | 0.000 +/- 0.000 |
| qwen3 | 0.020 +/- 0.013 | 0.014 +/- 0.014 | 0.082 +/- 0.031 | 0.004 +/- 0.002 | 14.725 +/- 3.476 | 0.000 +/- 0.000 |

Note: these cross-provider values are from the existing table artifacts and may use a different scale/normalization than the c19 DeepSeek headline run. Treat them as provider robustness checks, not a replacement for the main K=20 c19 comparison.

## Phase 2 Concordia/SOTOPIA Status

## Concordia Compact Cross-Task Validation

The compact Concordia Pub Coordination validation now covers all 7 non-test configs available in the local Concordia checkout at 30 seeds, plus a 100-seed Cape Town run. These runs use the fair mechanism table: A-ToM, ECON, HPSMG ablations, and the proposed joint proxy all receive the same full sampled case and known payoff model; `oracle_joint` is reported only as a privileged upper bound.

| Config | Episodes | Proposed focal score | Best non-oracle baseline | Margin | Oracle gap | Source |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| london_mini | 30 | 1.3083 | 1.0764 | 0.2319 | 0.0083 | `analysis/concordia_pub_coordination_compact_london_mini_mechanistic_joint_s30.json` |
| capetown | 100 | 1.2483 | 1.0423 | 0.2061 | 0.0168 | `analysis/concordia_pub_coordination_compact_capetown_mechanistic_joint_s100.json` |
| capetown | 30 | 1.2472 | 1.0439 | 0.2033 | 0.0287 | `analysis/concordia_pub_coordination_compact_capetown_mechanistic_joint_s30.json` |
| edinburgh_closures | 30 | 1.2083 | 1.0865 | 0.1218 | 0.0174 | `analysis/concordia_pub_coordination_compact_edinburgh_closures_mechanistic_joint_s30.json` |
| london | 30 | 1.3167 | 1.2017 | 0.1150 | 0.0188 | `analysis/concordia_pub_coordination_compact_london_mechanistic_joint_s30.json` |

The expanded sweep is summarized in `analysis/concordia_compact_margin_summary.md`. `edinburgh` and `edinburgh_tough_friendship` function as easy-control tasks where all non-oracle mechanisms tie, so they should be reported as coverage rather than separation evidence.

Live compact prompt checks now also cover GPT-5.4 Nano and Llama-4 Maverick on the same `london_mini` seeds `[0, 1, 2, 3, 4]`, with the same split artifact structure used for DeepSeek (`s2`, `s3_seed2_4`, combined `s5`) and matching `puppet --max-steps 5` official smokes. `hpsmg_plus_joint_proxy` reaches 1.3000 focal score on both, matching the oracle compact focal mean. The best GPT prompt baseline is `econ_bne` at 1.1250; the Llama prompt baselines tie at 0.8250. Sources: `analysis/concordia_pub_coordination_compact_gpt_5_4_nano_20260317_live_s5.json` and `analysis/concordia_pub_coordination_compact_Llama_4_Maverick_17B_128E_Instruct_FP8_live_s5.json`.

## Concordia Compact Haggling Validation

The compact Concordia validation now also covers 9 official bargaining configs at 30 seeds: 5 single-item Haggling configs and 4 Multi-Item Haggling configs. These use the same fair mechanism setting: A-ToM, ECON, HPSMG ablations, and the proposed joint proxy all receive the same sampled case and the same known official payoff model. For bargaining tasks, the primary margin is Nash product, with focal-min score as the fairness tie-breaker.

| Domain | Config | Episodes | Proposed Nash | Best non-oracle baseline | Baseline Nash | Nash margin | Min-score margin | Source |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | --- |
| haggling_multi_item | vegbrooke | 30 | 5.1000 | econ_bne_mech | 4.7833 | 0.3167 | 0.6333 | `analysis/concordia_haggling_multi_item_compact_vegbrooke_s30.json` |
| haggling_multi_item | fruitville_gullible | 30 | 5.0889 | econ_bne_mech | 4.7778 | 0.3111 | 0.0667 | `analysis/concordia_haggling_multi_item_compact_fruitville_gullible_s30.json` |
| haggling | fruitville | 30 | 3.8222 | econ_bne_mech | 3.5611 | 0.2611 | 0.6667 | `analysis/concordia_haggling_compact_fruitville_s30.json` |
| haggling_multi_item | fruitville_multi | 30 | 4.8000 | econ_bne_mech | 4.5500 | 0.2500 | 0.5000 | `analysis/concordia_haggling_multi_item_compact_fruitville_multi_s30.json` |
| haggling | vegbrooke_stubborn | 30 | 0.1667 | econ_bne_mech | 0.1000 | 0.0667 | 0.1333 | `analysis/concordia_haggling_compact_vegbrooke_stubborn_s30.json` |

The haggling sweep is summarized in `analysis/concordia_haggling_margin_summary.md`. `fruitville_gullible`, `vegbrooke_strange_game`, and `cumulative_score` are useful coverage/control tasks where the proposed method ties the strongest baseline under the compact metric.

Notes: `analysis/phase2_concordia_sotopia_environment_notes.md`

Concordia source: `external/concordia`

SOTOPIA source: `external/sotopia`

Setup script: `scripts/setup_phase2_external_envs.ps1`

Smoke script: `scripts/smoke_phase2_adapters.ps1`

Validated adapters and smoke outputs:

| Environment | Artifact | Status |
| --- | --- | --- |
| Concordia adapter sweep | `analysis/concordia_baseline_choice_sweep_offline.json` | offline adapter smoke passed |
| Concordia official `pub_coordination` | `analysis/concordia_pub_coordination_official_smoke.json` | official simulation smoke passed with puppet config |
| SOTOPIA adapter sweep | `analysis/sotopia_baseline_action_sweep_offline.json` | offline action sweep passed |
| SOTOPIA official local episode | `analysis/sotopia_official_episode_smoke.json` | local `ParallelSotopiaEnv` smoke passed |

Next Phase 2 tasks are live CloudGPT smokes, real SOTOPIA episode selection, and SOTOPIA-Eval scoring.

## Artifact Index

### Headline result artifacts

- Proposed/native beta sweep summary: `analysis/calibration_cloudgpt_multi_model_fast4_8algos_DeepSeek_V3_2_c19_summary.md`
- Best native result files: `results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0.npz`, `results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz`
- External LLM baseline summary: `analysis/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5_summary.md`
- External LLM baseline result: `results/cloudgpt/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz`
- External LLM baseline trace: `analysis/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5_trace.json`
- Lightweight LLM baseline result: `results/cloudgpt/E2_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz`
- Lightweight LLM baseline trace: `analysis/E2_llm_baselines_DeepSeek_V3_2_c19_K20_s5_trace.json`

### Existing tables

- `tables/E2_sanity_regret.tex`
- `tables/E3_cross_provider_regret.tex`
- `tables/E4_burn_in.tex`

### Key implementation files

- Native coordinator and posterior methods: `llm_hpgg/coordinator.py`
- Native experiment runner: `llm_hpgg/run_experiment.py`
- Lightweight LLM baselines: `llm_hpgg/run_llm_baselines.py`
- External A-ToM/ECON baselines: `llm_hpgg/run_external_llm_baselines.py`
- External baseline summarizer: `scripts/summarize_external_llm_baselines.py`
- Concordia adapter: `llm_hpgg_concordia/cloudgpt_model.py`
- Concordia official runner: `llm_hpgg_concordia/run_pub_coordination.py`
- SOTOPIA agent adapter: `llm_hpgg_sotopia/agents.py`
- SOTOPIA official smoke runner: `llm_hpgg_sotopia/run_episode_smoke.py`

## Recommended Next Steps

Detailed integration memo: `analysis/results_integration_memo.md`

Model coverage audit: `analysis/model_sweep_coverage_audit.md`

Cross-model sweep plan: `analysis/cross_model_sweep_plan.md`

1. Sweep requested models after the DeepSeek headline is normalized. Native c19 sweeps already exist for `gpt_5_4_nano_20260317`, `Kimi_K2_6`, and `Llama_4_Maverick_17B_128E_Instruct_FP8`; missing work is the prompted LLM and external LLM comparison layer. Grok is dropped from this sweep.
2. Generate any remaining paper-ready curves not covered by the headline table: `figs/E2_native_cluster_curves.pdf`.
5. Frame the MAP result carefully: on informative HP-SPGG cells, type-aware methods cluster together; do not claim H-PSMG always beats MAP in HP-SPGG.
6. Run live CloudGPT Concordia after the seed/stat/model sweep, prioritizing `pub_coordination` and then a collective-action/labor-style task if available. Defer full SOTOPIA-Hard scoring until Concordia is complete.
7. Update the main research plan and paper empirical section with the completed A-ToM/ECON run and this integrated result summary.
8. Optional camera-ready polish: implement RNG coupling for H-PSMG and Joint-PSRL if the paper wants to claim bit-identical trajectories under matched randomness.

Note: `section_9_7_draft.tex` was mentioned in the integration notes, but it is not currently present in the workspace.

## Current Claim Draft

In the hidden-persona sequential public goods game, explicit posterior structure is much more sample-efficient than directly prompted LLM coordination. On the current DeepSeek-V3.2 `c19` setting with `K=20` and `seeds=5`, `hpsmg_plus` reaches a final cumulative regret of 0.400 over 20 rounds, while the best external LLM social-reasoning baseline (`econ_bne`) reaches 3.990 and `atom_adaptive_hedge` reaches 4.790. This supports the central claim that HP-SPGG benefits from modeling hidden persona uncertainty explicitly rather than relying only on generic LLM theory-of-mind or deliberative coordination prompts.