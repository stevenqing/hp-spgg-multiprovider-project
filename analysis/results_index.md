# HP-SPGG Results Index

Last updated: 2026-05-17

This is the single entry point for experiment outputs, summaries, tables, figures, and status notes. The headline metric is final cumulative regret; lower is better. Oracle is an upper bound and should not be counted as a competing baseline.

## Executive Result

The current headline result is on CloudGPT `DeepSeek-V3.2`, calibration `c19`, `K=20`, `seeds=5`:

| Role | Method | Final cumulative regret mean | Std | Mean welfare | Source |
|---|---|---:|---:|---:|---|
| Upper bound | `oracle` | 0.0000 | 0.0000 | 2.9500 | `results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz` |
| Proposed headline | `hpsmg_plus` | 0.4000 | 0.8000 | 2.7600 | `results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz` |
| Closest native baseline | `map_greedy` | 0.7120 | 0.4663 | 2.7144 | `results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz` |
| Best prompted LLM baseline | `llm_belief` | 3.0740 | 2.2308 | 2.7363 | `results/cloudgpt/E2_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz` |
| Best external LLM baseline | `econ_bne` | 3.9900 | 3.4136 | 2.6105 | `results/cloudgpt/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz` |

Main interpretation: the proposed posterior method is currently the strongest non-oracle method on the normalized headline setting. The broader proposed family should be reported with both `hpsmg` and `hpsmg_plus` as an ablation pair for cross-model robustness.

## Main Human-Readable Summaries

| File | Purpose |
|---|---|
| `analysis/overall_results_summary.md` | Current single-page narrative summary across native, LLM, external baselines, cross-provider checks, and next steps. |
| `analysis/all_numeric_results.md` | Numeric-only consolidated Markdown containing the current headline, native beta sweep, prompted LLM, external LLM, shard, guardrail, Concordia, and SOTOPIA tables. |
| `analysis/proposed_vs_baselines_guardrail_20260517.md` | Guardrail for the paper claim: when `hpsmg_plus` beats all baselines, and where the `hpsmg` ablation is stronger. |
| `analysis/model_performance_available_20260517.md` | Cross-model LLM performance analysis using currently completed results; Kimi external is partial until all shards finish. |
| `analysis/scientific_integrity_audit_20260517.md` | Audit note quarantining current gpt-5.5 artifacts and explaining Pub Coordination proxy collapse. |
| `analysis/concordia_validation_notes_20260517.md` | Concordia validation status, live CloudGPT smoke results, setup fix, and next experiment path. |
| `analysis/E2_native_vs_llm_baselines_stats.md` | Paper-ready headline statistics table with CI/IQR for native, prompted LLM, and external LLM baselines on DeepSeek c19. |
| `analysis/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5_summary.md` | External A-ToM/ECON summary for DeepSeek c19, K20/s5. |
| `analysis/cross_model_full_sweep_run_20260517.md` | Run log for the current cross-model prompted/external sweep. |

## Paper-Ready Tables And Figures

| Artifact | Purpose |
|---|---|
| `tables/E2_native_vs_llm_baselines.tex` | Main LaTeX table comparing native methods, prompted LLM, and external LLM baselines. |
| `figs/E2_native_vs_llm_baselines_main.pdf` | Main E2 regret curve figure. |
| `tables/E2_native_vs_llm_baselines_preview_s3.tex` | Earlier 3-seed preview table. |
| `figs/E2_native_vs_llm_baselines_preview_s3.pdf` | Earlier 3-seed preview figure. |
| `tables/E2_sanity_regret.tex` | Initial sanity table. |
| `figs/E2_sanity.pdf` | Initial sanity figure. |

## Raw Result Files: Headline DeepSeek c19

| Layer | File |
|---|---|
| Native/proposed beta 0.25 | `results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz` |
| Native/proposed beta 0.0 | `results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0.npz` |
| Prompted LLM K20/s5 | `results/cloudgpt/E2_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz` |
| Prompted LLM trace | `analysis/E2_llm_baselines_DeepSeek_V3_2_c19_K20_s5_trace.json` |
| External LLM K20/s5 | `results/cloudgpt/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz` |
| External LLM trace | `analysis/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5_trace.json` |

## Raw Result Files: Cross-Model Prompted LLM

All are `K=20`, `seeds=5`, calibration `c19`.

| Model | File |
|---|---|
| DeepSeek-V3.2 | `results/cloudgpt/E2_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz` |
| gpt-5.4-nano | `results/cloudgpt/E2_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5.npz` |
| Kimi-K2.6 | `results/cloudgpt/E2_llm_baselines_Kimi_K2_6_c19_K20_s5.npz` |
| Llama-4-Maverick | `results/cloudgpt/E2_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5.npz` |

## Raw Result Files: Cross-Model Native Sweeps

These contain native algorithms including `oracle`, `hpsmg_plus`, `hpsmg`, `joint_psrl`, `map_greedy`, `psrl_notype`, `iql`, and `random`.

Paper-facing cross-model native sweeps currently exclude gpt-5.5. The existing gpt-5.5 artifacts are quarantined in `analysis/scientific_integrity_audit_20260517.md` because the native calibration-dependent outputs are identical to gpt-5.4-nano across all checked betas.

| Model | Representative beta 0.25 file | Summary |
|---|---|---|
| DeepSeek-V3.2 | `results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz` | `analysis/calibration_cloudgpt_multi_model_fast4_8algos_DeepSeek_V3_2_c19_summary.md` |
| gpt-5.4-nano | `results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p25.npz` | `analysis/calibration_cloudgpt_multi_model_fast4_8algos_gpt_5_4_nano_20260317_c19_summary.md` |
| Kimi-K2.6 | `results/cloudgpt/E2_Kimi_K2_6_c19_beta0p25.npz` | `analysis/calibration_cloudgpt_multi_model_fast4_8algos_Kimi_K2_6_c19_summary.md` |
| Llama-4-Maverick | `results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p25.npz` | `analysis/calibration_cloudgpt_multi_model_fast4_8algos_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_summary.md` |

## Raw Result Files: Cross-Model External LLM

Completed or currently available solo shards are under `results/cloudgpt/shards/` with matching traces under `analysis/shards/`.

| Model | Status | Files |
|---|---|---|
| gpt-5.4-nano | complete 6/6 shards | `results/cloudgpt/shards/E2_external_gpt_5_4_nano_20260317_c19_K20_s5_*.npz` |
| Llama-4-Maverick | complete 6/6 shards | `results/cloudgpt/shards/E2_external_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5_*.npz` |
| Kimi-K2.6 | partial; 1/6 shard complete at last documented checkpoint | `results/cloudgpt/shards/E2_external_Kimi_K2_6_c19_K20_s5_*.npz` |

When all Kimi shards finish, the postprocess watcher should produce merged outputs in `results/cloudgpt/` and summaries in `analysis/`.

Expected merged external outputs:

| Model | Expected merged file |
|---|---|
| gpt-5.4-nano | `results/cloudgpt/E2_external_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5.npz` |
| Kimi-K2.6 | `results/cloudgpt/E2_external_llm_baselines_Kimi_K2_6_c19_K20_s5.npz` |
| Llama-4-Maverick | `results/cloudgpt/E2_external_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5.npz` |

## Repro And Verification Scripts

| Script | Purpose |
|---|---|
| `scripts/summarize_available_model_performance.py` | Print currently available model performance table using final cumulative regret. |
| `scripts/generate_all_numeric_results_md.py` | Regenerate `analysis/all_numeric_results.md`. |
| `scripts/check_proposed_vs_baselines.py` | Strict check: fixed beta 0.25 `hpsmg_plus` vs all available non-oracle baselines. |
| `scripts/check_proposed_beta_sweep_vs_baselines.py` | Check best available `hpsmg_plus` beta vs all available non-oracle baselines. |
| `scripts/merge_external_llm_shards.py` | Merge solo external shards into a full model-level external `.npz`. |
| `scripts/summarize_external_llm_baselines.py` | Summarize a merged external LLM `.npz` into Markdown. |
| `scripts/postprocess_cross_model_full_sweep.ps1` | Watch for cross-model runs to complete, then merge and summarize. |
| `scripts/setup_phase2_external_envs.ps1` | Recreate Concordia/SOTOPIA isolated environments, including CloudGPT dependencies for both external benchmark venvs. |

## Concordia Validation Artifacts

| Artifact | Status |
|---|---|
| `analysis/concordia_baseline_choice_sweep_offline.json` | offline adapter sweep passed |
| `analysis/concordia_pub_coordination_official_smoke.json` | offline official puppet smoke passed |
| `analysis/concordia_baseline_choice_sweep_DeepSeek_V3_2_live.json` | live CloudGPT adapter sweep passed |
| `analysis/concordia_baseline_choice_sweep_gpt_5_4_nano_20260317_live.json` | live CloudGPT adapter sweep passed for GPT-5.4 Nano |
| `analysis/concordia_baseline_choice_sweep_Llama_4_Maverick_17B_128E_Instruct_FP8_live.json` | live CloudGPT adapter sweep passed for Llama-4 Maverick |
| `analysis/concordia_pub_coordination_puppet_DeepSeek_V3_2_live_max5.json` | official live loop/serialization smoke passed; max steps too low for final joint action |
| `analysis/concordia_pub_coordination_puppet_gpt_5_4_nano_20260317_live_max5.json` | official live loop/serialization smoke passed for GPT-5.4 Nano; max steps too low for final joint action |
| `analysis/concordia_pub_coordination_puppet_Llama_4_Maverick_17B_128E_Instruct_FP8_live_max5.json` | official live loop/serialization smoke passed for Llama-4 Maverick; max steps too low for final joint action |
| `analysis/concordia_pub_coordination_compact_DeepSeek_V3_2_live_s2.md` | compact DeepSeek live numeric table passed; seeds 0-1 |
| `analysis/concordia_pub_coordination_compact_DeepSeek_V3_2_live_s5.md` | compact DeepSeek live numeric table passed; seeds 0-4 |
| `analysis/concordia_pub_coordination_compact_gpt_5_4_nano_20260317_live_s2.md` | compact GPT-5.4 Nano live numeric table passed; seeds 0-1 |
| `analysis/concordia_pub_coordination_compact_gpt_5_4_nano_20260317_live_s3_seed2_4.md` | compact GPT-5.4 Nano live numeric table passed; seeds 2-4 |
| `analysis/concordia_pub_coordination_compact_gpt_5_4_nano_20260317_live_s5.md` | compact GPT-5.4 Nano live numeric table passed; seeds 0-4 |
| `analysis/concordia_pub_coordination_compact_Llama_4_Maverick_17B_128E_Instruct_FP8_live_s2.md` | compact Llama-4 Maverick live numeric table passed; seeds 0-1 |
| `analysis/concordia_pub_coordination_compact_Llama_4_Maverick_17B_128E_Instruct_FP8_live_s3_seed2_4.md` | compact Llama-4 Maverick live numeric table passed; seeds 2-4 |
| `analysis/concordia_pub_coordination_compact_Llama_4_Maverick_17B_128E_Instruct_FP8_live_s5.md` | compact Llama-4 Maverick live numeric table passed; seeds 0-4 |
| `analysis/concordia_pub_coordination_compact_mechanistic_joint_s5.md` | preferred compact Concordia mechanism table; joint proxy vs mechanism baselines |
| `analysis/concordia_pub_coordination_compact_london_mini_mechanistic_joint_s30.md` | compact Concordia London Mini s30 mechanism table |
| `analysis/concordia_pub_coordination_compact_london_mechanistic_joint_s30.md` | compact Concordia London s30 mechanism table |
| `analysis/concordia_pub_coordination_compact_london_closures_mechanistic_joint_s30.md` | compact Concordia London Closures s30 mechanism table |
| `analysis/concordia_pub_coordination_compact_edinburgh_mechanistic_joint_s30.md` | compact Concordia Edinburgh s30 mechanism table; easy-control task |
| `analysis/concordia_pub_coordination_compact_edinburgh_closures_mechanistic_joint_s30.md` | compact Concordia Edinburgh Closures s30 mechanism table |
| `analysis/concordia_pub_coordination_compact_edinburgh_tough_friendship_mechanistic_joint_s30.md` | compact Concordia Edinburgh Tough Friendship s30 mechanism table; easy-control task |
| `analysis/concordia_pub_coordination_compact_capetown_mechanistic_joint_s30.md` | compact Concordia Cape Town s30 mechanism table |
| `analysis/concordia_pub_coordination_compact_capetown_mechanistic_joint_s100.md` | strongest compact Concordia result; Cape Town s100 margin over A-ToM/ECON |
| `analysis/concordia_compact_margin_summary.md` | cross-task compact Concordia margin summary |
| `analysis/concordia_haggling_compact_fruitville_s30.md` | compact Concordia single-item haggling Fruitville s30 table |
| `analysis/concordia_haggling_compact_fruitville_gullible_s30.md` | compact Concordia single-item haggling Fruitville Gullible s30 table; tie/control task |
| `analysis/concordia_haggling_compact_vegbrooke_s30.md` | compact Concordia single-item haggling Vegbrooke s30 table |
| `analysis/concordia_haggling_compact_vegbrooke_strange_game_s30.md` | compact Concordia single-item haggling Vegbrooke Strange Game s30 table; tie/control task |
| `analysis/concordia_haggling_compact_vegbrooke_stubborn_s30.md` | compact Concordia single-item haggling Vegbrooke Stubborn s30 table |
| `analysis/concordia_haggling_multi_item_compact_fruitville_multi_s30.md` | compact Concordia multi-item haggling Fruitville Multi s30 table |
| `analysis/concordia_haggling_multi_item_compact_fruitville_gullible_s30.md` | compact Concordia multi-item haggling Fruitville Gullible s30 table |
| `analysis/concordia_haggling_multi_item_compact_vegbrooke_s30.md` | compact Concordia multi-item haggling Vegbrooke s30 table |
| `analysis/concordia_haggling_multi_item_compact_cumulative_score_s30.md` | compact Concordia multi-item haggling Cumulative Score s30 table; tie/control task |
| `analysis/concordia_haggling_margin_summary.md` | cross-task compact Concordia haggling margin summary |
| `analysis/concordia_compact_action_diagnostics.md` | explains why prompt-only Concordia baselines have identical scores/actions |
| `analysis/concordia_validation_notes_20260517.md` | current Concordia validation plan and command log |

## SOTOPIA Validation Artifacts

| Artifact | Status |
|---|---|
| `analysis/sotopia_baseline_action_sweep_offline.json` | offline adapter action sweep passed |
| `analysis/sotopia_official_episode_smoke.json` | official local `ParallelSotopiaEnv` smoke passed |
| `analysis/sotopia_baseline_action_sweep_recheck.json` | offline adapter action sweep rechecked after deterministic offline handling |
| `analysis/sotopia_official_episode_smoke_recheck.json` | official local episode smoke rechecked after deterministic offline handling |
| `analysis/sotopia_official_episode_smoke_DeepSeek_V3_2_live_t1.json` | live CloudGPT DeepSeek one-turn SOTOPIA smoke passed |
| `external/sotopia_data_probe/benchmark_agents.json` | official public SOTOPIA-Hard combo metadata: 70 combos, 14 unique hard envs |
| `external/sotopia_data_probe/sotopia_hard_cases_cache.json` | reconstructed official-hard profiles/scenarios from HuggingFace episode JSONL |
| `analysis/sotopia_hard_official_offline_smoke.json` | reconstructed official SOTOPIA-Hard runner passed offline smoke |
| `analysis/sotopia_hard_official_offline_all70_check.json` | all 70 reconstructed official SOTOPIA-Hard combos passed offline enumeration |
| `analysis/sotopia_hard_official_DeepSeek_V3_2_live_smoke.json` | reconstructed official SOTOPIA-Hard runner passed live DeepSeek smoke, one combo, two turns |
| `analysis/sotopia_hard_official_hpsmg_plus_offline_smoke.json` | fair SOTOPIA adapter smoke passed for proposed `hpsmg_plus` mode |
| `analysis/sotopia_hard_official_DeepSeek_V3_2_hpsmg_plus_live_smoke.json` | live CloudGPT SOTOPIA smoke passed for proposed `hpsmg_plus` mode, one combo, two turns |
| `analysis/sotopia_hard_official_DeepSeek_V3_2_summary.md` | completed all-70 SOTOPIA-Hard DeepSeek proposed/baseline summary with overall and dimension means |
| `analysis/sotopia_hard_official_all_models_summary.md` | all available SOTOPIA-Hard all-70 proposed/baseline summaries across DeepSeek, GPT, Kimi, and Llama |
| `analysis/sotopia_hard_official_DeepSeek_V3_2_hpsmg_plus_all70.json` | completed full reconstructed official SOTOPIA-Hard live run for proposed `hpsmg_plus`; 70/70, `complete=true` |
| `analysis/sotopia_hard_official_DeepSeek_V3_2_llm_belief_all70.json` | completed full reconstructed official SOTOPIA-Hard live run for DeepSeek `llm_belief`; 70/70, `complete=true` |
| `analysis/sotopia_hard_official_DeepSeek_V3_2_llm_greedy_all70.json` | completed full reconstructed official SOTOPIA-Hard live run for DeepSeek `llm_greedy`; 70/70, `complete=true` |
| `analysis/sotopia_hard_official_DeepSeek_V3_2_atom_tom1_all70.json` | completed full reconstructed official SOTOPIA-Hard live run for DeepSeek `atom_tom1`; 70/70, `complete=true` |
| `analysis/sotopia_hard_official_DeepSeek_V3_2_econ_bne_all70.json` | completed full reconstructed official SOTOPIA-Hard live run for DeepSeek `econ_bne`; 70/70, `complete=true` |
| `logs/sotopia_hard_official_DeepSeek_V3_2_*_all70_stdout.log` | stdout logs for detached full SOTOPIA-Hard live runs |
| `logs/sotopia_hard_official_DeepSeek_V3_2_*_all70_stderr.log` | stderr logs for detached full SOTOPIA-Hard live runs |
| `scripts/monitor_sotopia_hard_runs.ps1` | detached monitor for all four SOTOPIA-Hard all-70 baseline checkpoints |
| `logs/sotopia_hard_official_monitor.log` | combined progress monitor log for all four SOTOPIA-Hard all-70 baseline runs |
| `logs/sotopia_hard_official_hpsmg_plus_monitor.log` | progress monitor log for proposed `hpsmg_plus` SOTOPIA-Hard all-70 run |
| `logs/sotopia_hard_official_all_models_monitor.log` | combined progress monitor for GPT/Kimi/Llama SOTOPIA-Hard all-70 sweeps |
| `logs/sotopia_hard_official_model_queue.log` | low-concurrency queue log for GPT/Kimi/Llama SOTOPIA-Hard all-70 sweeps |
| `scripts/summarize_sotopia_hard_results.py` | regenerate `analysis/sotopia_hard_official_all_models_summary.md` from all available all-70 JSONs |
| `scripts/launch_sotopia_hard_model_runs.ps1` | direct launcher for GPT/Kimi/Llama SOTOPIA-Hard all-70 sweeps; superseded by queue when rate-limited |
| `scripts/run_sotopia_hard_model_queue.ps1` | recommended low-concurrency checkpoint/resume queue for GPT/Kimi/Llama SOTOPIA-Hard all-70 sweeps |
| `scripts/monitor_sotopia_hard_all_models.ps1` | detached combined monitor for GPT/Kimi/Llama SOTOPIA-Hard all-70 sweeps |
| `analysis/phase2_concordia_sotopia_environment_notes.md` | SOTOPIA setup notes; official Redis/Docker path unavailable locally, no-Docker reconstructed hard path implemented |

Recommended commands:

```powershell
uv run python scripts\summarize_available_model_performance.py
uv run python scripts\generate_all_numeric_results_md.py
uv run python scripts\check_proposed_vs_baselines.py
uv run python scripts\check_proposed_beta_sweep_vs_baselines.py
```

## Claim Discipline

Use this wording for the current evidence:

- Safe headline claim: on the normalized DeepSeek c19 K20/s5 setting, `hpsmg_plus` is the best non-oracle method and substantially outperforms prompted LLM and external A-ToM/ECON baselines.
- Safe cross-model claim: the HP-SPGG posterior family (`hpsmg`, `hpsmg_plus`) remains the central method family; the exploration bonus is beneficial on the headline DeepSeek and Llama settings but is not uniformly better than the posterior-only ablation on every model.
- Avoid: claiming `hpsmg_plus` beats every baseline on every model until a validation-selected variant or new held-out results support that exact statement.
