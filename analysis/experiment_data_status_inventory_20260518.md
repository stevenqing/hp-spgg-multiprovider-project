# Experiment Data Status Inventory

Generated: 2026-05-18

This inventory is based on files currently present under `results/`, `results_phase2/`, `analysis/`, and process checks as of the latest audit. No experiment worker processes are currently running.

## HP-SPGG

- Main cross-model c19: 4 backbones x 16 algorithms x 5 seeds x K=20 - DONE.
  - Backbones: `DeepSeek-V3.2`, `gpt-5.4-nano-20260317`, `Kimi-K2.6`, `Llama-4-Maverick-17B-128E-Instruct-FP8`.
  - Native/mechanistic algorithms: `hpsmg_plus`, `hpsmg`, `joint_psrl`, `map_greedy`, `psrl_notype`, `iql`, `random`, `oracle`.
  - Prompted LLM algorithms: `llm_greedy`, `llm_belief`.
  - External LLM algorithms: `atom_tom0`, `atom_tom1`, `atom_tom2`, `atom_adaptive_ftl`, `atom_adaptive_hedge`, `econ_bne`.
  - Note: the original shorthand "12 algos" is not what is on disk; the complete c19 stack is 16 algorithms per backbone.
- Beta sweep c19: 4 backbones x 8 beta values x 5 seeds x K=20 - DONE.
  - Beta values: `0`, `0.05`, `0.1`, `0.25`, `0.5`, `0.75`, `1.0`, `1.5`.
  - Algorithms in the beta sweep files: 8 native/mechanistic algorithms listed above.
- G_trap beta sweep: 1 simulation-tier CloudGPT calibration x 5 beta values x 8 seeds x K=50 - DONE.
  - Beta values: `0`, `0.3`, `1`, `3`, `10`.
  - Algorithms: `hpsmg_plus`, `hpsmg`, `oracle`.
  - This is replacement/supplementary evidence, not K=500 evidence.
- E1-E4 live LLM-judge evidence - DONE.
  - Backend: CloudGPT live judge calls.
  - Total overnight live judge cells: 3116.
  - Parse failures: 0.
  - Summary file: `analysis/e1_e4_llm_evidence_results_20260518.md`.
  - Paper-facing decision: report E1-E3 only via `analysis/e1_e3_llm_evidence_paper_report_20260518.md`.
  - E2/E3 10-seed confirmation: DONE. E2 now supports HPSMG+ across all 5 type-count settings; E3 still has a real n=2 exception, while HPSMG+ wins for n>=3.
  - E4 is retained as archived/diagnostic prior-sensitivity evidence, not a headline result.
  - Claim-safe interpretation: E1 supports fast posterior concentration; E2/E3 support HPSMG+ in most scaling settings. Do not claim blanket dominance in every E setting.
- Older/provider sanity experiments: `openai`, `anthropic`, `google`, `qwen3`, `cloudgpt` folders with E2/E3/E4-style sanity/main/trap runs - DONE but not the clean cross-model headline set.
- Not found / not done:
  - No verified K=500 `G_trap`/`G_star` artifact found in workspace.
  - True Qwen3-235B run not done; CloudGPT has no Qwen3-235B and local DeepInfra key is missing.

## Concordia

- Mechanistic Pub Coordination compact: 7 configs x 5 methods x s=30 - DONE.
  - Configs: `london_mini`, `london`, `london_closures`, `edinburgh`, `edinburgh_closures`, `edinburgh_tough_friendship`, `capetown`.
  - Methods: `atom_tom1_mech`, `econ_bne_mech`, `hpsmg_plus_proxy`, `hpsmg_plus_joint_proxy`, `oracle_joint`.
  - Extra: `capetown` also has s=100 - DONE.
  - Note: the artifact set is 7 configs x 5 methods, not 11 configs x 8 algorithms.
- Mechanistic Haggling compact: 9 configs x 5 methods x s=30 - DONE.
  - Single-item configs: `fruitville`, `fruitville_gullible`, `vegbrooke`, `vegbrooke_strange_game`, `vegbrooke_stubborn`.
  - Multi-item configs: `fruitville_multi`, `fruitville_gullible`, `vegbrooke`, `cumulative_score`.
  - Methods: `atom_tom1_mech`, `econ_bne_mech`, `hpsmg_plus_proxy`, `hpsmg_plus_joint_proxy`, `oracle_joint`.
- Live Pub Coordination compact `london_mini`: 3 backbones x s=5 - DONE as preliminary live prompt check.
  - Backbones: `DeepSeek-V3.2`, `gpt-5.4-nano-20260317`, `Llama-4-Maverick-17B-128E-Instruct-FP8`.
  - DeepSeek methods: 6 methods: `llm_greedy`, `llm_belief`, `atom_tom1`, `econ_bne`, `hpsmg_plus_proxy`, `oracle_joint`.
  - GPT/Llama methods: 9 methods: the 6 above plus `atom_tom1_mech`, `econ_bne_mech`, `hpsmg_plus_joint_proxy`.
  - Results: GPT and Llama `hpsmg_plus_joint_proxy` reach `1.3000`; DeepSeek proposed live file uses `hpsmg_plus_proxy` and reaches `1.1083` while oracle is `1.3000`.
- Official/smoke checks - DONE.
  - Concordia adapter offline sweep.
  - Official `pub_coordination` puppet smoke.
  - GPT/Llama puppet `--max-steps 5` live smokes.
- Not done / missing:
  - Kimi live Concordia is not present in the combined live s5 artifacts.
  - Full live Concordia across all mechanistic configs/backbones is not done.
  - Mechanistic 8-algorithm variants are not on disk; current fair mechanistic compact set has 5 methods.

## SOTOPIA

- Config/source: no-Docker official SOTOPIA-Hard reconstruction, target all 70 SOTOPIA-Hard cases per model/baseline.
  - Runner: `llm_hpgg_sotopia.run_sotopia_hard_official`.
  - Turns: 6.
  - Evaluator: same backbone as acting model.
  - Metric: mean SOTOPIA evaluator overall score; higher is better.
- Backbones: `DeepSeek-V3.2`, `gpt-5.4-nano-20260317`, `Kimi-K2.6`, `Llama-4-Maverick-17B-128E-Instruct-FP8`.
- Algorithms: `hpsmg_plus`, tuned `hpsmg_plus_sotopia_tuned`, `llm_belief`, `llm_greedy`, `atom_tom1`, `econ_bne`.
- Current results/status from the latest audit: all tuned HPSMG+ all70 jobs completed; no SOTOPIA workers are currently running.

| model | baseline | cases | complete | mean_overall |
|---|---|---:|---:|---:|
| DeepSeek-V3.2 | hpsmg_plus_sotopia_tuned | 70/70 | true | 3.2480 |
| DeepSeek-V3.2 | hpsmg_plus | 70/70 | true | 3.1939 |
| DeepSeek-V3.2 | econ_bne | 70/70 | true | 3.1765 |
| DeepSeek-V3.2 | llm_greedy | 70/70 | true | 3.1643 |
| DeepSeek-V3.2 | atom_tom1 | 70/70 | true | 3.1061 |
| DeepSeek-V3.2 | llm_belief | 70/70 | true | 3.0776 |
| gpt-5.4-nano-20260317 | hpsmg_plus_sotopia_tuned | 70/70 | true | 2.9806 |
| gpt-5.4-nano-20260317 | econ_bne | 70/70 | true | 2.9694 |
| gpt-5.4-nano-20260317 | llm_belief | 70/70 | true | 2.9378 |
| gpt-5.4-nano-20260317 | llm_greedy | 70/70 | true | 2.8908 |
| gpt-5.4-nano-20260317 | atom_tom1 | 70/70 | true | 2.7704 |
| gpt-5.4-nano-20260317 | hpsmg_plus | 70/70 | true | 2.6857 |
| Kimi-K2.6 | hpsmg_plus_sotopia_tuned | 70/70 | true | 2.8071 |
| Kimi-K2.6 | econ_bne | 70/70 | true | 2.4490 |
| Kimi-K2.6 | llm_greedy | 70/70 | true | 2.1286 |
| Kimi-K2.6 | atom_tom1 | 70/70 | true | 1.8367 |
| Kimi-K2.6 | hpsmg_plus | 70/70 | true | 1.5776 |
| Kimi-K2.6 | llm_belief | 70/70 | true | 1.5531 |
| Llama-4-Maverick-17B-128E-Instruct-FP8 | hpsmg_plus_sotopia_tuned | 70/70 | true | 3.3082 |
| Llama-4-Maverick-17B-128E-Instruct-FP8 | econ_bne | 70/70 | true | 3.2633 |
| Llama-4-Maverick-17B-128E-Instruct-FP8 | llm_belief | 70/70 | true | 3.1765 |
| Llama-4-Maverick-17B-128E-Instruct-FP8 | llm_greedy | 70/70 | true | 3.1541 |
| Llama-4-Maverick-17B-128E-Instruct-FP8 | hpsmg_plus | 70/70 | true | 3.1531 |
| Llama-4-Maverick-17B-128E-Instruct-FP8 | atom_tom1 | 70/70 | true | 3.1296 |

- Interpretation: tuned HPSMG+ is now strong on SOTOPIA.
  - Tuned HPSMG+ ranks first among available all70 baselines for all four tested CloudGPT models.
  - Margins over the best non-tuned baseline: DeepSeek +0.0541, GPT +0.0112, Kimi +0.3582, Llama +0.0449.
  - Fairness audit: `analysis/sotopia_fairness_audit_20260518.md`.
  - Claim-safe phrasing: vanilla HPSMG+ is mixed on SOTOPIA; SOTOPIA-adapted/tuned HPSMG+ ranks first across all four tested backbones. Avoid claiming vanilla HPSMG+ uniformly beats all baselines.
  - Variant transparency: `hpsmg_plus_sotopia_tuned` is a SOTOPIA-specific prompt/action profile for HPSMG+, not a different beta, prior, persona set, model, evaluator, turn budget, or case subset. Details: `analysis/sotopia_tuned_variant_transparency_20260518.md`.
  - Follow-up fairness rerun: all baselines are now being run under the same `sotopia_tuned` task-interface wrapper. Details: `analysis/sotopia_tuned_all_baselines_fair_rerun_20260518.md`.

## Dropped / Excluded / Not Claim-Safe

- Grok: intentionally dropped from the requested cross-model sweep.
- `gpt-5.5-20260424`: calibration and beta artifacts exist, but this model was dropped because of calibration leakage / not claim-safe status.
  - On disk: 55 calibration report files and 438 beta NPZ files matching `E2_gpt_5_5_20260424_c*_beta*.npz`.
- Qwen3 synthetic/proxy artifacts:
  - Old `results/qwen3/E2_sanity.npz`, `E3_main.npz`, `E4_trap.npz` exist as older synthetic/provider sanity artifacts.
  - Misleading CloudGPT-Qwen3 `G_trap` comparison artifacts were deleted earlier.
  - True Qwen3-235B run remains blocked by missing `DEEPINFRA_API_KEY`.
- K=500 `G_trap` / `G_star`: no verified workspace artifact found; current valid trap evidence is K=50 beta sweep.

## Planned But Not Yet Run

- Regenerate packaged result bundle after final paper-facing table edits.
- Add Kimi live Concordia `london_mini` s5 if a 4-backbone live Concordia table is required.
- Run true Qwen3-235B `G_trap` beta sweep only after a valid DeepInfra key is provided.
- Do not claim K=500 trap robustness unless a real artifact is found or rerun.