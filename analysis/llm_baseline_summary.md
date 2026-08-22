# HP-SPGG Baseline Suite Summary

Last updated: 2026-05-17 15:48

## Algorithm families now included

### Type-aware Bayesian / posterior methods

| Method | Role | Current implementation |
| --- | --- | --- |
| `hpsmg_plus` | Proposed method with type-discrimination bonus | `llm_hpgg/coordinator.py` |
| `hpsmg` | Proposed method without bonus | `llm_hpgg/coordinator.py` |
| `joint_psrl` | Explicit joint posterior PSRL baseline | `llm_hpgg/coordinator.py` |
| `map_greedy` | MAP-type greedy baseline | `llm_hpgg/coordinator.py` |

### Type-agnostic / standard baselines

| Method | Role | Current implementation |
| --- | --- | --- |
| `psrl_notype` | Samples hidden type uniformly each round, no type posterior update | `llm_hpgg/coordinator.py` |
| `iql_independent_actions` | Canonical independent-action IQL baseline | `llm_hpgg/run_experiment.py` |
| `iql` / `joint_profile_iql` | Joint-profile Q-learning ablation retained for comparison with earlier runs | `llm_hpgg/run_experiment.py` |
| `random` | Uniform random action profile | `llm_hpgg/coordinator.py` |
| `oracle` | Knows the true hidden type profile | `llm_hpgg/coordinator.py` |

### LLM-based coordinator baselines

| Method | Role | Current implementation |
| --- | --- | --- |
| `llm_greedy` | Direct LLM coordinator chooses a joint contribution profile from public history | `llm_hpgg/run_llm_baselines.py` |
| `llm_belief` | LLM coordinator first infers likely hidden personas from history, then chooses action | `llm_hpgg/run_llm_baselines.py` |

These two LLM-based methods are intended as lightweight, executable analogues of belief / ToM-style LLM coordination baselines. They are not full ECON or A-ToM reproductions, but they directly test whether a prompted LLM coordinator can replace the closed-form Bayesian posterior.

## Completed LLM-based baseline run

Calibration: `calibration_cloudgpt_multi_model_fast4_8algos_DeepSeek_V3_2_c19.npy`

Coordinator model: `DeepSeek-V3.2` through CloudGPT

Setting: `K=20`, `seeds=5`

Output: `results/cloudgpt/E2_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz`

Trace: `analysis/E2_llm_baselines_DeepSeek_V3_2_c19_K20_s5_trace.json`

Cache: `logs/llm_baseline_cache_DeepSeek_V3_2.json`

Headline stats and curve: `analysis/E2_native_vs_llm_baselines_stats.md`, `tables/E2_native_vs_llm_baselines.tex`, `figs/E2_native_vs_llm_baselines_main.pdf`

| Method | Final cumulative regret mean |
| --- | ---: |
| `llm_belief` | 3.074 |
| `llm_greedy` | 14.020 |

Earlier 3-seed run retained for traceability: `results/cloudgpt/E2_llm_baselines_DeepSeek_V3_2_c19_K20_s3.npz`.

## Same-setting tabular comparison

Calibration: `calibration_cloudgpt_multi_model_fast4_8algos_DeepSeek_V3_2_c19.npy`

Setting: `K=20`, `seeds=3`, `beta=1.0`

Output: `results/cloudgpt/E2_tabular_compare_DeepSeek_V3_2_c19_K20_s3_beta1.npz`

| Method | Final cumulative regret mean |
| --- | ---: |
| `oracle` | 0.000 |
| `joint_psrl` | 0.860 |
| `hpsmg` | 0.877 |
| `hpsmg_plus` | 0.883 |
| `map_greedy` | 0.943 |
| `llm_belief` | 3.074 |
| `llm_greedy` | 14.020 |
| `psrl_notype` | 14.100 |
| `iql` | 29.267 |
| `random` | 30.580 |

## Current interpretation

The 5-seed LLM belief baseline is meaningfully better than the previously run type-agnostic baselines (`psrl_notype`, old joint-profile `iql`, `random`), which is a useful reviewer-facing comparison against LLM belief / ToM-style methods. It is still substantially worse than the closed-form Bayesian type-aware methods, supporting the claim that explicit posterior structure matters. The canonical `iql_independent_actions` baseline has now been added and should be included in the next full rerun.

The next stronger version would implement more formal ECON / A-ToM-style baselines, but the current `llm_belief` run already gives an executable LLM-based comparison point inside HP-SPGG.