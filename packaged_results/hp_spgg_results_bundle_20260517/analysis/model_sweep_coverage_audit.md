# HP-SPGG Model Sweep Coverage Audit

Last updated: 2026-05-17

This audit records which model/calibration experiments already exist and what is still missing before the next sweep. Grok is intentionally excluded from the active sweep: there are no formal Grok result files under `results/cloudgpt`, and the only Grok evidence found is in an archived bad-run folder.

## Active Model Set

| Model slug | Native c19 beta sweep | K | Seeds | c coverage found | c19 best hpsmg_plus | Best beta | Lightweight LLM c19 | External A-ToM/ECON c19 | Status |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| `DeepSeek_V3_2` | complete | 20 | 5 | c1-c19 | 0.400 | 0.0 | K20, seeds=3 | K20, seeds=3 | seed mismatch needs fixing first |
| `gpt_5_4_nano_20260317` | complete | 20 | 5 | c1-c29 | 0.898 | 1.0 | missing | missing | native done; LLM baselines missing |
| `Kimi_K2_6` | complete | 20 | 5 | c1-c21 | 0.704 | 0.25 | missing | missing | native done; LLM baselines missing |
| `Llama_4_Maverick_17B_128E_Instruct_FP8` | complete | 20 | 5 | c1-c23 | 0.312 | 0.25 | missing | missing | native done; LLM baselines missing |
| `gpt_5_5_20260424` | complete but parse failures in report | 20 | 5 | c1-c55 | 0.898 | 1.0 | missing | missing | optional; not in requested sweep |

## Explicitly Dropped

| Model | Reason |
| --- | --- |
| Grok | No formal `results/cloudgpt` outputs. Only archived bad-run records exist under `logs/bad_multimodel_before_fix_20260517_094413`, so it should not be used in the current sweep. |

## Immediate Missing Experiments

1. Fix seed mismatch on the DeepSeek c19 headline comparison.
   - Rerun prompted LLM baselines with `seeds=5`.
   - Rerun external A-ToM/ECON baselines with `seeds=5`.
   - Keep the full six external algorithms for the 5-seed rerun so each algorithm keeps the same `algo_index` seed family as the existing 3-seed run.

2. Add statistics and curves after the 5-seed outputs exist.
   - Mean/std, median/IQR, and bootstrap confidence intervals.
   - Regret curves for native, prompted LLM, and external LLM baselines.

3. Cross-model sweep after the DeepSeek headline is normalized.
   - Native c19 already exists for gpt-5.4-nano, Kimi, and Llama.
   - Missing cross-model comparison layer is prompted LLM and, if budget allows, external A-ToM/ECON on the same c19 calibration for each model.

## Candidate Commands

DeepSeek prompted LLM 5-seed rerun:

```powershell
$env:LLM_HPGG_BACKEND='cloudgpt'; $env:CLOUDGPT_USE_AZURE_CLI='1'; $env:CLOUDGPT_TIMEOUT='90'; uv run python -m llm_hpgg.run_llm_baselines --K 20 --n 3 --seeds 5 --algos llm_greedy llm_belief --calibration calibration_cloudgpt_multi_model_fast4_8algos_DeepSeek_V3_2_c19.npy --out results\cloudgpt\E2_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz --trace-out analysis\E2_llm_baselines_DeepSeek_V3_2_c19_K20_s5_trace.json --cache logs\llm_baseline_cache_DeepSeek_V3_2.json --model DeepSeek-V3.2
```

DeepSeek external A-ToM/ECON 5-seed rerun:

```powershell
$env:LLM_HPGG_BACKEND='cloudgpt'; $env:CLOUDGPT_USE_AZURE_CLI='1'; $env:CLOUDGPT_TIMEOUT='90'; $env:EXTERNAL_LLM_CALL_RETRIES='12'; $env:EXTERNAL_LLM_RETRY_BASE_SECONDS='10'; uv run python -m llm_hpgg.run_external_llm_baselines --K 20 --n 3 --seeds 5 --algos atom_tom0 atom_tom1 atom_tom2 atom_adaptive_ftl atom_adaptive_hedge econ_bne --calibration calibration_cloudgpt_multi_model_fast4_8algos_DeepSeek_V3_2_c19.npy --out results\cloudgpt\E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz --trace-out analysis\E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5_trace.json --cache logs\external_llm_baseline_cache_DeepSeek_V3_2.json --model DeepSeek-V3.2 --econ-rounds 3
```