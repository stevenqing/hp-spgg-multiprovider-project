# E5 Cross-Model Per-Episode Cumulative Regret Data

Date: 2026-05-18

## Files

- Seed-level long CSV: `tables/E5_cross_model_cumulative_regret_seed_level.csv`
- Mean/SEM summary CSV: `tables/E5_cross_model_cumulative_regret_summary.csv`

## Schema

- `episode_k`: 1..20
- `instant_regret`: one-step regret at episode k
- `cumulative_regret`: cumulative regret through episode k
- `cumulative_regret_mean`: mean over seeds
- `cumulative_regret_sem`: standard error over seeds

## Loaded NPZ Sources

| Model | Family | Algorithms | cumulative_regret shape | Source |
| --- | --- | ---: | --- | --- |
| DeepSeek-V3.2 | Native | 8 | (8, 5, 20) | `results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz` |
| DeepSeek-V3.2 | Prompted LLM | 2 | (2, 5, 20) | `results/cloudgpt/E2_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz` |
| DeepSeek-V3.2 | External LLM | 6 | (6, 5, 20) | `results/cloudgpt/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz` |
| gpt-5.4-nano | Native | 8 | (8, 5, 20) | `results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p25.npz` |
| gpt-5.4-nano | Prompted LLM | 2 | (2, 5, 20) | `results/cloudgpt/E2_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5.npz` |
| gpt-5.4-nano | External LLM | 6 | (6, 5, 20) | `results/cloudgpt/E2_external_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5.npz` |
| Kimi-K2.6 | Native | 8 | (8, 5, 20) | `results/cloudgpt/E2_Kimi_K2_6_c19_beta0p25.npz` |
| Kimi-K2.6 | Prompted LLM | 2 | (2, 5, 20) | `results/cloudgpt/E2_llm_baselines_Kimi_K2_6_c19_K20_s5.npz` |
| Kimi-K2.6 | External LLM | 6 | (6, 5, 20) | `results/cloudgpt/E2_external_llm_baselines_Kimi_K2_6_c19_K20_s5.npz` |
| Llama-4-Maverick | Native | 8 | (8, 5, 20) | `results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p25.npz` |
| Llama-4-Maverick | Prompted LLM | 2 | (2, 5, 20) | `results/cloudgpt/E2_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5.npz` |
| Llama-4-Maverick | External LLM | 6 | (6, 5, 20) | `results/cloudgpt/E2_external_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5.npz` |

## Final K=20 Means

| Model | Family | Algorithm | Final cumulative regret mean | SEM | Source |
| --- | --- | --- | ---: | ---: | --- |
| DeepSeek-V3.2 | Native | hpsmg_plus | 0.4000 | 0.4000 | `results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz` |
| DeepSeek-V3.2 | Native | hpsmg | 0.8280 | 0.2707 | `results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz` |
| DeepSeek-V3.2 | Native | joint_psrl | 0.8320 | 0.0398 | `results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz` |
| DeepSeek-V3.2 | Native | map_greedy | 0.7120 | 0.2331 | `results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz` |
| DeepSeek-V3.2 | Native | psrl_notype | 13.9120 | 3.6868 | `results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz` |
| DeepSeek-V3.2 | Native | iql | 28.3420 | 8.4568 | `results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz` |
| DeepSeek-V3.2 | Native | random | 28.2660 | 2.5621 | `results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz` |
| DeepSeek-V3.2 | Native | oracle | 0.0000 | 0.0000 | `results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz` |
| DeepSeek-V3.2 | Prompted LLM | llm_greedy | 14.0200 | 7.3321 | `results/cloudgpt/E2_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz` |
| DeepSeek-V3.2 | Prompted LLM | llm_belief | 3.0740 | 1.1154 | `results/cloudgpt/E2_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz` |
| DeepSeek-V3.2 | External LLM | atom_tom0 | 6.0000 | 3.7283 | `results/cloudgpt/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz` |
| DeepSeek-V3.2 | External LLM | atom_tom1 | 16.6760 | 4.1002 | `results/cloudgpt/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz` |
| DeepSeek-V3.2 | External LLM | atom_tom2 | 13.4020 | 5.1600 | `results/cloudgpt/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz` |
| DeepSeek-V3.2 | External LLM | atom_adaptive_ftl | 14.9440 | 0.7156 | `results/cloudgpt/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz` |
| DeepSeek-V3.2 | External LLM | atom_adaptive_hedge | 4.7900 | 2.2544 | `results/cloudgpt/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz` |
| DeepSeek-V3.2 | External LLM | econ_bne | 3.9900 | 1.7068 | `results/cloudgpt/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz` |
| gpt-5.4-nano | Native | hpsmg_plus | 0.9120 | 0.1460 | `results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p25.npz` |
| gpt-5.4-nano | Native | hpsmg | 0.6440 | 0.3155 | `results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p25.npz` |
| gpt-5.4-nano | Native | joint_psrl | 1.4920 | 0.1709 | `results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p25.npz` |
| gpt-5.4-nano | Native | map_greedy | 0.8540 | 0.2104 | `results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p25.npz` |
| gpt-5.4-nano | Native | psrl_notype | 17.7200 | 0.8385 | `results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p25.npz` |
| gpt-5.4-nano | Native | iql | 24.7918 | 5.8641 | `results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p25.npz` |
| gpt-5.4-nano | Native | random | 26.4584 | 0.9070 | `results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p25.npz` |
| gpt-5.4-nano | Native | oracle | 0.0000 | 0.0000 | `results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p25.npz` |
| gpt-5.4-nano | Prompted LLM | llm_greedy | 17.4060 | 8.9094 | `results/cloudgpt/E2_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5.npz` |
| gpt-5.4-nano | Prompted LLM | llm_belief | 7.1967 | 1.7374 | `results/cloudgpt/E2_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5.npz` |
| gpt-5.4-nano | External LLM | atom_tom0 | 4.0800 | 2.4703 | `results/cloudgpt/E2_external_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5.npz` |
| gpt-5.4-nano | External LLM | atom_tom1 | 13.4726 | 3.2948 | `results/cloudgpt/E2_external_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5.npz` |
| gpt-5.4-nano | External LLM | atom_tom2 | 10.2000 | 4.4127 | `results/cloudgpt/E2_external_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5.npz` |
| gpt-5.4-nano | External LLM | atom_adaptive_ftl | 14.8895 | 1.4227 | `results/cloudgpt/E2_external_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5.npz` |
| gpt-5.4-nano | External LLM | atom_adaptive_hedge | 7.6530 | 2.4791 | `results/cloudgpt/E2_external_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5.npz` |
| gpt-5.4-nano | External LLM | econ_bne | 14.8800 | 1.3764 | `results/cloudgpt/E2_external_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5.npz` |
| Kimi-K2.6 | Native | hpsmg_plus | 0.7040 | 0.2176 | `results/cloudgpt/E2_Kimi_K2_6_c19_beta0p25.npz` |
| Kimi-K2.6 | Native | hpsmg | 0.6320 | 0.3045 | `results/cloudgpt/E2_Kimi_K2_6_c19_beta0p25.npz` |
| Kimi-K2.6 | Native | joint_psrl | 1.6500 | 0.2019 | `results/cloudgpt/E2_Kimi_K2_6_c19_beta0p25.npz` |
| Kimi-K2.6 | Native | map_greedy | 0.7620 | 0.1956 | `results/cloudgpt/E2_Kimi_K2_6_c19_beta0p25.npz` |
| Kimi-K2.6 | Native | psrl_notype | 19.5060 | 1.3051 | `results/cloudgpt/E2_Kimi_K2_6_c19_beta0p25.npz` |
| Kimi-K2.6 | Native | iql | 20.1180 | 9.2633 | `results/cloudgpt/E2_Kimi_K2_6_c19_beta0p25.npz` |
| Kimi-K2.6 | Native | random | 26.5400 | 2.2569 | `results/cloudgpt/E2_Kimi_K2_6_c19_beta0p25.npz` |
| Kimi-K2.6 | Native | oracle | 0.0000 | 0.0000 | `results/cloudgpt/E2_Kimi_K2_6_c19_beta0p25.npz` |
| Kimi-K2.6 | Prompted LLM | llm_greedy | 18.2700 | 3.8239 | `results/cloudgpt/E2_llm_baselines_Kimi_K2_6_c19_K20_s5.npz` |
| Kimi-K2.6 | Prompted LLM | llm_belief | 11.7840 | 1.6668 | `results/cloudgpt/E2_llm_baselines_Kimi_K2_6_c19_K20_s5.npz` |
| Kimi-K2.6 | External LLM | atom_tom0 | 10.6720 | 3.1780 | `results/cloudgpt/E2_external_llm_baselines_Kimi_K2_6_c19_K20_s5.npz` |
| Kimi-K2.6 | External LLM | atom_tom1 | 14.0480 | 3.4621 | `results/cloudgpt/E2_external_llm_baselines_Kimi_K2_6_c19_K20_s5.npz` |
| Kimi-K2.6 | External LLM | atom_tom2 | 10.5840 | 4.1093 | `results/cloudgpt/E2_external_llm_baselines_Kimi_K2_6_c19_K20_s5.npz` |
| Kimi-K2.6 | External LLM | atom_adaptive_ftl | 14.2800 | 1.3874 | `results/cloudgpt/E2_external_llm_baselines_Kimi_K2_6_c19_K20_s5.npz` |
| Kimi-K2.6 | External LLM | atom_adaptive_hedge | 7.4840 | 2.0478 | `results/cloudgpt/E2_external_llm_baselines_Kimi_K2_6_c19_K20_s5.npz` |
| Kimi-K2.6 | External LLM | econ_bne | 10.4880 | 3.0160 | `results/cloudgpt/E2_external_llm_baselines_Kimi_K2_6_c19_K20_s5.npz` |
| Llama-4-Maverick | Native | hpsmg_plus | 0.3120 | 0.3120 | `results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p25.npz` |
| Llama-4-Maverick | Native | hpsmg | 0.7320 | 0.3043 | `results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p25.npz` |
| Llama-4-Maverick | Native | joint_psrl | 1.1940 | 0.1735 | `results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p25.npz` |
| Llama-4-Maverick | Native | map_greedy | 0.9740 | 0.2194 | `results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p25.npz` |
| Llama-4-Maverick | Native | psrl_notype | 10.6540 | 2.1783 | `results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p25.npz` |
| Llama-4-Maverick | Native | iql | 27.5260 | 8.1696 | `results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p25.npz` |
| Llama-4-Maverick | Native | random | 24.3418 | 2.1617 | `results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p25.npz` |
| Llama-4-Maverick | Native | oracle | 0.0000 | 0.0000 | `results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p25.npz` |
| Llama-4-Maverick | Prompted LLM | llm_greedy | 5.9600 | 4.2902 | `results/cloudgpt/E2_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5.npz` |
| Llama-4-Maverick | Prompted LLM | llm_belief | 10.3560 | 1.9097 | `results/cloudgpt/E2_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5.npz` |
| Llama-4-Maverick | External LLM | atom_tom0 | 7.2400 | 3.8943 | `results/cloudgpt/E2_external_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5.npz` |
| Llama-4-Maverick | External LLM | atom_tom1 | 15.7100 | 3.9660 | `results/cloudgpt/E2_external_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5.npz` |
| Llama-4-Maverick | External LLM | atom_tom2 | 11.8660 | 4.6625 | `results/cloudgpt/E2_external_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5.npz` |
| Llama-4-Maverick | External LLM | atom_adaptive_ftl | 13.9220 | 1.3285 | `results/cloudgpt/E2_external_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5.npz` |
| Llama-4-Maverick | External LLM | atom_adaptive_hedge | 7.0060 | 2.2916 | `results/cloudgpt/E2_external_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5.npz` |
| Llama-4-Maverick | External LLM | econ_bne | 3.3820 | 2.2669 | `results/cloudgpt/E2_external_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5.npz` |

## Focus Curves: Mean Cumulative Regret k=1..20

### DeepSeek-V3.2

| Family | Algorithm | k1 | k2 | k3 | k4 | k5 | k6 | k7 | k8 | k9 | k10 | k11 | k12 | k13 | k14 | k15 | k16 | k17 | k18 | k19 | k20 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| External LLM | atom_tom1 | 1.202 | 1.880 | 2.652 | 3.524 | 4.346 | 5.168 | 5.990 | 6.812 | 7.634 | 8.456 | 9.278 | 10.100 | 10.922 | 11.744 | 12.566 | 13.388 | 14.210 | 15.032 | 15.854 | 16.676 |
| External LLM | econ_bne | 0.170 | 0.400 | 0.898 | 1.068 | 1.340 | 1.610 | 1.780 | 1.950 | 2.120 | 2.290 | 2.460 | 2.630 | 2.800 | 2.970 | 3.140 | 3.310 | 3.480 | 3.650 | 3.820 | 3.990 |
| Native | hpsmg | 0.364 | 0.488 | 0.488 | 0.488 | 0.598 | 0.612 | 0.612 | 0.618 | 0.618 | 0.618 | 0.618 | 0.618 | 0.828 | 0.828 | 0.828 | 0.828 | 0.828 | 0.828 | 0.828 | 0.828 |
| Native | hpsmg_plus | 0.020 | 0.040 | 0.060 | 0.080 | 0.100 | 0.120 | 0.140 | 0.160 | 0.180 | 0.200 | 0.220 | 0.240 | 0.260 | 0.280 | 0.300 | 0.320 | 0.340 | 0.360 | 0.380 | 0.400 |
| Native | joint_psrl | 0.450 | 0.640 | 0.656 | 0.656 | 0.832 | 0.832 | 0.832 | 0.832 | 0.832 | 0.832 | 0.832 | 0.832 | 0.832 | 0.832 | 0.832 | 0.832 | 0.832 | 0.832 | 0.832 | 0.832 |
| Native | oracle | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Prompted LLM | llm_belief | 0.190 | 0.482 | 0.742 | 0.886 | 1.068 | 1.168 | 1.312 | 1.380 | 1.598 | 1.780 | 1.820 | 2.056 | 2.274 | 2.308 | 2.600 | 2.640 | 2.680 | 2.824 | 3.034 | 3.074 |
| Prompted LLM | llm_greedy | 0.700 | 1.400 | 2.100 | 2.800 | 3.500 | 4.200 | 4.900 | 5.600 | 6.300 | 7.000 | 7.700 | 8.400 | 9.100 | 9.800 | 10.500 | 11.200 | 11.900 | 12.600 | 13.300 | 14.020 |

### gpt-5.4-nano

| Family | Algorithm | k1 | k2 | k3 | k4 | k5 | k6 | k7 | k8 | k9 | k10 | k11 | k12 | k13 | k14 | k15 | k16 | k17 | k18 | k19 | k20 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| External LLM | atom_tom1 | 0.740 | 1.532 | 2.389 | 3.053 | 3.717 | 4.313 | 4.909 | 5.505 | 6.169 | 6.833 | 7.497 | 8.161 | 8.825 | 9.489 | 10.153 | 10.817 | 11.481 | 12.145 | 12.809 | 13.473 |
| External LLM | econ_bne | 0.744 | 1.488 | 2.232 | 2.976 | 3.720 | 4.464 | 5.208 | 5.952 | 6.696 | 7.440 | 8.184 | 8.928 | 9.672 | 10.416 | 11.160 | 11.904 | 12.648 | 13.392 | 14.136 | 14.880 |
| Native | hpsmg | 0.620 | 0.628 | 0.636 | 0.644 | 0.644 | 0.644 | 0.644 | 0.644 | 0.644 | 0.644 | 0.644 | 0.644 | 0.644 | 0.644 | 0.644 | 0.644 | 0.644 | 0.644 | 0.644 | 0.644 |
| Native | hpsmg_plus | 0.726 | 0.812 | 0.844 | 0.876 | 0.908 | 0.912 | 0.912 | 0.912 | 0.912 | 0.912 | 0.912 | 0.912 | 0.912 | 0.912 | 0.912 | 0.912 | 0.912 | 0.912 | 0.912 | 0.912 |
| Native | joint_psrl | 1.338 | 1.338 | 1.338 | 1.338 | 1.362 | 1.362 | 1.362 | 1.362 | 1.362 | 1.468 | 1.492 | 1.492 | 1.492 | 1.492 | 1.492 | 1.492 | 1.492 | 1.492 | 1.492 | 1.492 |
| Native | oracle | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Prompted LLM | llm_belief | 0.216 | 0.528 | 0.882 | 1.236 | 1.539 | 1.893 | 2.307 | 2.841 | 3.209 | 3.487 | 3.951 | 4.415 | 4.879 | 5.061 | 5.441 | 5.803 | 6.267 | 6.635 | 6.919 | 7.197 |
| Prompted LLM | llm_greedy | 0.870 | 1.740 | 2.610 | 3.480 | 4.350 | 5.220 | 6.090 | 6.960 | 7.830 | 8.700 | 9.576 | 10.446 | 11.316 | 12.186 | 13.056 | 13.926 | 14.796 | 15.666 | 16.536 | 17.406 |

### Kimi-K2.6

| Family | Algorithm | k1 | k2 | k3 | k4 | k5 | k6 | k7 | k8 | k9 | k10 | k11 | k12 | k13 | k14 | k15 | k16 | k17 | k18 | k19 | k20 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| External LLM | atom_tom1 | 0.832 | 1.712 | 2.398 | 3.042 | 3.816 | 4.444 | 5.130 | 5.816 | 6.502 | 7.188 | 7.874 | 8.560 | 9.246 | 9.932 | 10.618 | 11.304 | 11.990 | 12.676 | 13.362 | 14.048 |
| External LLM | econ_bne | 0.678 | 1.304 | 1.894 | 2.366 | 2.838 | 3.310 | 3.852 | 4.470 | 5.060 | 5.650 | 6.122 | 6.594 | 7.184 | 7.656 | 8.128 | 8.600 | 9.072 | 9.544 | 10.016 | 10.488 |
| Native | hpsmg | 0.608 | 0.616 | 0.624 | 0.632 | 0.632 | 0.632 | 0.632 | 0.632 | 0.632 | 0.632 | 0.632 | 0.632 | 0.632 | 0.632 | 0.632 | 0.632 | 0.632 | 0.632 | 0.632 | 0.632 |
| Native | hpsmg_plus | 0.704 | 0.704 | 0.704 | 0.704 | 0.704 | 0.704 | 0.704 | 0.704 | 0.704 | 0.704 | 0.704 | 0.704 | 0.704 | 0.704 | 0.704 | 0.704 | 0.704 | 0.704 | 0.704 | 0.704 |
| Native | joint_psrl | 1.496 | 1.496 | 1.496 | 1.496 | 1.520 | 1.520 | 1.520 | 1.520 | 1.520 | 1.626 | 1.650 | 1.650 | 1.650 | 1.650 | 1.650 | 1.650 | 1.650 | 1.650 | 1.650 | 1.650 |
| Native | oracle | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Prompted LLM | llm_belief | 0.216 | 0.828 | 1.508 | 1.946 | 2.502 | 3.182 | 3.738 | 4.488 | 5.168 | 5.848 | 6.334 | 6.890 | 7.446 | 8.126 | 8.806 | 9.486 | 10.176 | 10.856 | 11.218 | 11.784 |
| Prompted LLM | llm_greedy | 0.974 | 1.584 | 2.496 | 3.470 | 4.444 | 5.234 | 5.964 | 6.938 | 7.912 | 8.708 | 9.504 | 10.688 | 11.662 | 12.570 | 13.544 | 14.452 | 15.420 | 16.394 | 17.362 | 18.270 |

### Llama-4-Maverick

| Family | Algorithm | k1 | k2 | k3 | k4 | k5 | k6 | k7 | k8 | k9 | k10 | k11 | k12 | k13 | k14 | k15 | k16 | k17 | k18 | k19 | k20 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| External LLM | atom_tom1 | 0.558 | 1.396 | 2.210 | 3.024 | 3.752 | 4.566 | 5.380 | 6.114 | 6.894 | 7.708 | 8.484 | 9.298 | 9.792 | 10.476 | 11.548 | 12.362 | 13.176 | 13.990 | 14.962 | 15.710 |
| External LLM | econ_bne | 0.382 | 0.658 | 0.934 | 1.078 | 1.222 | 1.366 | 1.510 | 1.654 | 1.798 | 1.942 | 2.086 | 2.230 | 2.374 | 2.518 | 2.662 | 2.806 | 2.950 | 3.094 | 3.238 | 3.382 |
| Native | hpsmg | 0.356 | 0.364 | 0.372 | 0.714 | 0.732 | 0.732 | 0.732 | 0.732 | 0.732 | 0.732 | 0.732 | 0.732 | 0.732 | 0.732 | 0.732 | 0.732 | 0.732 | 0.732 | 0.732 | 0.732 |
| Native | hpsmg_plus | 0.168 | 0.312 | 0.312 | 0.312 | 0.312 | 0.312 | 0.312 | 0.312 | 0.312 | 0.312 | 0.312 | 0.312 | 0.312 | 0.312 | 0.312 | 0.312 | 0.312 | 0.312 | 0.312 | 0.312 |
| Native | joint_psrl | 0.898 | 1.018 | 1.020 | 1.126 | 1.150 | 1.168 | 1.168 | 1.168 | 1.170 | 1.170 | 1.194 | 1.194 | 1.194 | 1.194 | 1.194 | 1.194 | 1.194 | 1.194 | 1.194 | 1.194 |
| Native | oracle | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Prompted LLM | llm_belief | 0.420 | 0.886 | 1.494 | 2.066 | 2.530 | 3.148 | 3.722 | 4.260 | 4.606 | 5.242 | 5.786 | 6.280 | 6.690 | 7.452 | 7.728 | 8.296 | 8.854 | 9.358 | 9.852 | 10.356 |
| Prompted LLM | llm_greedy | 0.266 | 0.532 | 1.438 | 1.704 | 1.970 | 2.236 | 2.502 | 2.768 | 3.034 | 3.300 | 3.566 | 3.832 | 4.098 | 4.364 | 4.630 | 4.896 | 5.162 | 5.428 | 5.694 | 5.960 |
