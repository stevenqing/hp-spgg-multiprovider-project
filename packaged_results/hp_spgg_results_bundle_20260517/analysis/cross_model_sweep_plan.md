# HP-SPGG Cross-Model Sweep Plan

Last updated: 2026-05-17

This plan starts after the DeepSeek c19 seed-normalization run completes. Grok is excluded from the active sweep. Current CloudGPT availability is recorded in `analysis/cloudgpt_model_availability_sweep_20260517.md`.

## Scope

Active models:

| Model slug | CloudGPT model string | c19 native calibration | Native c19 status | Missing comparison layer |
| --- | --- | --- | --- | --- |
| `gpt_5_4_nano_20260317` | `gpt-5.4-nano-20260317` | `calibration_cloudgpt_multi_model_fast4_8algos_gpt_5_4_nano_20260317_c19.npy` | complete, K20, seeds=5 | prompted LLM; optional external |
| `Kimi_K2_6` | `Kimi-K2.6` | `calibration_cloudgpt_multi_model_fast4_8algos_Kimi_K2_6_c19.npy` | complete, K20, seeds=5 | prompted LLM; optional external |
| `Llama_4_Maverick_17B_128E_Instruct_FP8` | `Llama-4-Maverick-17B-128E-Instruct-FP8` | `calibration_cloudgpt_multi_model_fast4_8algos_Llama_4_Maverick_17B_128E_Instruct_FP8_c19.npy` | complete, K20, seeds=5 | prompted LLM; optional external |

Optional already-calibrated model:

| Model slug | CloudGPT model string | c19 native calibration | Native c19 status | Missing comparison layer |
| --- | --- | --- | --- | --- |
| `gpt_5_5_20260424` | `gpt-5.5-20260424` | `calibration_cloudgpt_multi_model_fast4_8algos_gpt_5_5_20260424_c19.npy` | complete, K20, seeds=5, parse-failure caveat | prompted LLM; optional external |

Dropped:

| Model | Reason |
| --- | --- |
| Grok | No formal `results/cloudgpt` outputs; only archived bad-run artifacts exist. |

## Execution Order

1. Finish DeepSeek c19 seed normalization.
   - Prompted LLM is complete at K20/seeds=5.
   - External A-ToM/ECON K20/seeds=5 is currently running.

2. Run prompted LLM baselines for the three active cross-model calibrations.
   - This is the cheapest missing comparison layer.
   - Use K20/seeds=5 for consistency with native c19 sweeps.
   - Reuse one cache per coordinator model.

3. Generate cross-model headline table.
   - Rows: native best H-PSMG+, MAP, Joint-PSRL, prompted LLM belief, prompted LLM greedy.
   - Columns: mean/std, median/IQR, bootstrap CI, welfare.

4. Decide whether to run external A-ToM/ECON on all three models.
   - Full six-algorithm external sweeps are expensive.
   - If budget is tight, run only `atom_adaptive_hedge` and `econ_bne`, but preserve seed comparability by using an explicit fixed seed map or a full six-algorithm run.

## Prompted LLM Commands

```powershell
$env:LLM_HPGG_BACKEND='cloudgpt'; $env:CLOUDGPT_USE_AZURE_CLI='1'; $env:CLOUDGPT_TIMEOUT='90'; $env:LLM_BASELINE_CALL_RETRIES='12'; $env:LLM_BASELINE_RETRY_BASE_SECONDS='10'
```

```powershell
uv run python -m llm_hpgg.run_llm_baselines --K 20 --n 3 --seeds 5 --algos llm_greedy llm_belief --calibration calibration_cloudgpt_multi_model_fast4_8algos_gpt_5_4_nano_20260317_c19.npy --out results\cloudgpt\E2_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5.npz --trace-out analysis\E2_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5_trace.json --cache logs\llm_baseline_cache_gpt_5_4_nano_20260317.json --model gpt-5.4-nano-20260317
```

```powershell
uv run python -m llm_hpgg.run_llm_baselines --K 20 --n 3 --seeds 5 --algos llm_greedy llm_belief --calibration calibration_cloudgpt_multi_model_fast4_8algos_Kimi_K2_6_c19.npy --out results\cloudgpt\E2_llm_baselines_Kimi_K2_6_c19_K20_s5.npz --trace-out analysis\E2_llm_baselines_Kimi_K2_6_c19_K20_s5_trace.json --cache logs\llm_baseline_cache_Kimi_K2_6.json --model Kimi-K2.6
```

```powershell
uv run python -m llm_hpgg.run_llm_baselines --K 20 --n 3 --seeds 5 --algos llm_greedy llm_belief --calibration calibration_cloudgpt_multi_model_fast4_8algos_Llama_4_Maverick_17B_128E_Instruct_FP8_c19.npy --out results\cloudgpt\E2_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5.npz --trace-out analysis\E2_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5_trace.json --cache logs\llm_baseline_cache_Llama_4_Maverick_17B_128E_Instruct_FP8.json --model Llama-4-Maverick-17B-128E-Instruct-FP8
```

## Caution

The exact CloudGPT model strings should be confirmed with a one-call smoke before launching the full sweep. If any model string is rejected, use the nearest confirmed deployment name from `scripts/probe_cloudgpt_models.py` output or the existing calibration logs.