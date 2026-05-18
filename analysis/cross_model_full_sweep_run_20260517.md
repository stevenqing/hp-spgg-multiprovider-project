# Cross-Model Full Sweep Run

Last updated: 2026-05-17

Goal: repeat the full DeepSeek comparison layer for the three active cross-model targets:

1. `gpt-5.4-nano-20260317`
2. `Kimi-K2.6`
3. `Llama-4-Maverick-17B-128E-Instruct-FP8`

Grok is excluded.

## Started Runs

Prompted LLM baselines, K20/seeds=5:

| Model | Result target | Trace target | Cache |
| --- | --- | --- | --- |
| `gpt-5.4-nano-20260317` | `results/cloudgpt/E2_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5.npz` | `analysis/E2_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5_trace.json` | `logs/llm_baseline_cache_gpt_5_4_nano_20260317.json` |
| `Kimi-K2.6` | `results/cloudgpt/E2_llm_baselines_Kimi_K2_6_c19_K20_s5.npz` | `analysis/E2_llm_baselines_Kimi_K2_6_c19_K20_s5_trace.json` | `logs/llm_baseline_cache_Kimi_K2_6.json` |
| `Llama-4-Maverick-17B-128E-Instruct-FP8` | `results/cloudgpt/E2_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5.npz` | `analysis/E2_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5_trace.json` | `logs/llm_baseline_cache_Llama_4_Maverick_17B_128E_Instruct_FP8.json` |

External A-ToM/ECON baselines, K20/seeds=5, started as three shards per model:

| Model | Shards |
| --- | --- |
| `gpt-5.4-nano-20260317` | `atom01`, `atom2_ftl`, `hedge_econ` |
| `Kimi-K2.6` | `atom01`, `atom2_ftl`, `hedge_econ` |
| `Llama-4-Maverick-17B-128E-Instruct-FP8` | `atom01`, `atom2_ftl`, `hedge_econ` |

The external merge step will use `scripts/merge_external_llm_shards.py` with no base result after all shards finish.

## Fastest-Run Strategy

- Prompted LLM layer runs all three models in parallel.
- External layer runs 9 model/algorithm-family shards in parallel.
- If a `hedge_econ` shard becomes the tail, split it into `atom_adaptive_hedge` and per-seed `econ_bne` shards, as done for the DeepSeek run.
- Each shard has an independent cache to avoid concurrent writes to the same JSON file.

## Acceleration Restart

The initial 9 external shards showed CloudGPT 429 retries while each process still executed two algorithms sequentially. To shorten the critical path, the 9 external terminals were stopped after their immediate-save caches had accumulated progress. Their cache files were copied into independent per-algorithm cache snapshots, and the external layer was restarted as 18 single-algorithm shards with `EXTERNAL_LLM_RETRY_BASE_SECONDS=2`.

Runner: `scripts/run_cross_model_external_solo_shards.ps1`

New external shard layout: 3 models x 6 algorithms = 18 shards.

Algorithms: `atom_tom0`, `atom_tom1`, `atom_tom2`, `atom_adaptive_ftl`, `atom_adaptive_hedge`, `econ_bne`.

The final merge should use these 18 shard outputs rather than the superseded 9 family-shard targets.

## Initial Monitor Snapshot

At launch monitor, prompted cache entries were:

| Cache | Entries |
| --- | ---: |
| `logs/llm_baseline_cache_gpt_5_4_nano_20260317.json` | 46 |
| `logs/llm_baseline_cache_Kimi_K2_6.json` | 16 |
| `logs/llm_baseline_cache_Llama_4_Maverick_17B_128E_Instruct_FP8.json` | 64 |

External completed shards: `0/9` at first check.