# All Numeric Results

Generated: 2026-05-18 12:42:36

This file intentionally stores numeric results only, with minimal labels. HP-SPGG metric: final cumulative regret; lower is better. Concordia metric: focal score; higher is better. SOTOPIA metric: evaluator score; higher is better. Oracle is an upper bound.

## Headline DeepSeek c19 K20 s5: Native + Prompted + External

| group | model | algorithm | final_mean | final_std | median | iqr | per_round | welfare_mean | welfare_std | source |
|---|---|---|---|---|---|---|---|---|---|---|
| Native | DeepSeek-V3.2 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.9500 | 0.0447 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz |
| Native | DeepSeek-V3.2 | hpsmg_plus | 0.4000 | 0.8000 | 0.0000 | [0.0000, 0.0000] | 0.0200 | 2.7600 | 0.1020 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz |
| Native | DeepSeek-V3.2 | map_greedy | 0.7120 | 0.4663 | 0.7200 | [0.6400, 0.7300] | 0.0356 | 2.7144 | 0.2248 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz |
| Native | DeepSeek-V3.2 | hpsmg | 0.8280 | 0.5414 | 1.1100 | [0.3000, 1.2100] | 0.0414 | 2.8526 | 0.2148 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz |
| Native | DeepSeek-V3.2 | joint_psrl | 0.8320 | 0.0796 | 0.8800 | [0.7800, 0.9000] | 0.0416 | 2.8384 | 0.2051 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz |
| Prompted LLM | DeepSeek-V3.2 | llm_belief | 3.0740 | 2.2308 | 1.6800 | [1.5900, 5.2400] | 0.1537 | 2.7363 | 0.3074 | results/cloudgpt/E2_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz |
| External LLM | DeepSeek-V3.2 | econ_bne | 3.9900 | 3.4136 | 3.0000 | [1.9400, 5.0100] | 0.1995 | 2.6105 | 0.2122 | results/cloudgpt/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz |
| External LLM | DeepSeek-V3.2 | atom_adaptive_hedge | 4.7900 | 4.5089 | 1.8000 | [1.6700, 9.6800] | 0.2395 | 2.6605 | 0.4287 | results/cloudgpt/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz |
| External LLM | DeepSeek-V3.2 | atom_tom0 | 6.0000 | 7.4565 | 0.0000 | [0.0000, 13.0000] | 0.3000 | 2.5900 | 0.4620 | results/cloudgpt/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz |
| External LLM | DeepSeek-V3.2 | atom_tom2 | 13.4020 | 10.3200 | 13.4800 | [3.1100, 17.3000] | 0.6701 | 2.2139 | 0.6402 | results/cloudgpt/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz |
| Native | DeepSeek-V3.2 | psrl_notype | 13.9120 | 7.3737 | 13.8200 | [6.3800, 20.8800] | 0.6956 | 2.1744 | 0.7952 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz |
| Prompted LLM | DeepSeek-V3.2 | llm_greedy | 14.0200 | 14.6643 | 13.0000 | [0.1000, 17.0000] | 0.7010 | 2.1590 | 0.7183 | results/cloudgpt/E2_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz |
| External LLM | DeepSeek-V3.2 | atom_adaptive_ftl | 14.9440 | 1.4313 | 15.1100 | [14.4200, 16.2000] | 0.7472 | 2.0968 | 0.1891 | results/cloudgpt/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz |
| External LLM | DeepSeek-V3.2 | atom_tom1 | 16.6760 | 8.2004 | 17.5100 | [16.4000, 17.6500] | 0.8338 | 2.0182 | 0.5421 | results/cloudgpt/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz |
| Native | DeepSeek-V3.2 | random | 28.2660 | 5.1241 | 28.1400 | [24.2100, 31.7800] | 1.4133 | 1.4767 | 0.5568 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz |
| Native | DeepSeek-V3.2 | iql | 28.3420 | 16.9136 | 23.5000 | [21.5600, 32.3500] | 1.4171 | 1.3969 | 0.8222 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz |

## Native c19 Beta Sweeps

| model | beta | algorithm | final_mean | final_std | median | iqr | per_round | welfare_mean | welfare_std | source |
|---|---|---|---|---|---|---|---|---|---|---|
| DeepSeek-V3.2 | beta0 | hpsmg_plus | 0.4000 | 0.8000 | 0.0000 | [0.0000, 0.0000] | 0.0200 | 2.7600 | 0.1020 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0.npz |
| DeepSeek-V3.2 | beta0 | hpsmg | 0.8280 | 0.5414 | 1.1100 | [0.3000, 1.2100] | 0.0414 | 2.8526 | 0.2148 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0.npz |
| DeepSeek-V3.2 | beta0 | joint_psrl | 0.8320 | 0.0796 | 0.8800 | [0.7800, 0.9000] | 0.0416 | 2.8384 | 0.2051 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0.npz |
| DeepSeek-V3.2 | beta0 | map_greedy | 0.7120 | 0.4663 | 0.7200 | [0.6400, 0.7300] | 0.0356 | 2.7144 | 0.2248 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0.npz |
| DeepSeek-V3.2 | beta0 | psrl_notype | 13.9120 | 7.3737 | 13.8200 | [6.3800, 20.8800] | 0.6956 | 2.1744 | 0.7952 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0.npz |
| DeepSeek-V3.2 | beta0 | iql | 28.3420 | 16.9136 | 23.5000 | [21.5600, 32.3500] | 1.4171 | 1.3969 | 0.8222 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0.npz |
| DeepSeek-V3.2 | beta0 | random | 28.2660 | 5.1241 | 28.1400 | [24.2100, 31.7800] | 1.4133 | 1.4767 | 0.5568 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0.npz |
| DeepSeek-V3.2 | beta0 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.9500 | 0.0447 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0.npz |
| DeepSeek-V3.2 | beta0p05 | hpsmg_plus | 0.4000 | 0.8000 | 0.0000 | [0.0000, 0.0000] | 0.0200 | 2.7600 | 0.1020 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p05.npz |
| DeepSeek-V3.2 | beta0p05 | hpsmg | 0.8280 | 0.5414 | 1.1100 | [0.3000, 1.2100] | 0.0414 | 2.8526 | 0.2148 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p05.npz |
| DeepSeek-V3.2 | beta0p05 | joint_psrl | 0.8320 | 0.0796 | 0.8800 | [0.7800, 0.9000] | 0.0416 | 2.8384 | 0.2051 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p05.npz |
| DeepSeek-V3.2 | beta0p05 | map_greedy | 0.7120 | 0.4663 | 0.7200 | [0.6400, 0.7300] | 0.0356 | 2.7144 | 0.2248 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p05.npz |
| DeepSeek-V3.2 | beta0p05 | psrl_notype | 13.9120 | 7.3737 | 13.8200 | [6.3800, 20.8800] | 0.6956 | 2.1744 | 0.7952 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p05.npz |
| DeepSeek-V3.2 | beta0p05 | iql | 28.3420 | 16.9136 | 23.5000 | [21.5600, 32.3500] | 1.4171 | 1.3969 | 0.8222 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p05.npz |
| DeepSeek-V3.2 | beta0p05 | random | 28.2660 | 5.1241 | 28.1400 | [24.2100, 31.7800] | 1.4133 | 1.4767 | 0.5568 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p05.npz |
| DeepSeek-V3.2 | beta0p05 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.9500 | 0.0447 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p05.npz |
| DeepSeek-V3.2 | beta0p1 | hpsmg_plus | 0.4000 | 0.8000 | 0.0000 | [0.0000, 0.0000] | 0.0200 | 2.7600 | 0.1020 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p1.npz |
| DeepSeek-V3.2 | beta0p1 | hpsmg | 0.8280 | 0.5414 | 1.1100 | [0.3000, 1.2100] | 0.0414 | 2.8526 | 0.2148 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p1.npz |
| DeepSeek-V3.2 | beta0p1 | joint_psrl | 0.8320 | 0.0796 | 0.8800 | [0.7800, 0.9000] | 0.0416 | 2.8384 | 0.2051 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p1.npz |
| DeepSeek-V3.2 | beta0p1 | map_greedy | 0.7120 | 0.4663 | 0.7200 | [0.6400, 0.7300] | 0.0356 | 2.7144 | 0.2248 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p1.npz |
| DeepSeek-V3.2 | beta0p1 | psrl_notype | 13.9120 | 7.3737 | 13.8200 | [6.3800, 20.8800] | 0.6956 | 2.1744 | 0.7952 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p1.npz |
| DeepSeek-V3.2 | beta0p1 | iql | 28.3420 | 16.9136 | 23.5000 | [21.5600, 32.3500] | 1.4171 | 1.3969 | 0.8222 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p1.npz |
| DeepSeek-V3.2 | beta0p1 | random | 28.2660 | 5.1241 | 28.1400 | [24.2100, 31.7800] | 1.4133 | 1.4767 | 0.5568 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p1.npz |
| DeepSeek-V3.2 | beta0p1 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.9500 | 0.0447 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p1.npz |
| DeepSeek-V3.2 | beta0p25 | hpsmg_plus | 0.4000 | 0.8000 | 0.0000 | [0.0000, 0.0000] | 0.0200 | 2.7600 | 0.1020 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz |
| DeepSeek-V3.2 | beta0p25 | hpsmg | 0.8280 | 0.5414 | 1.1100 | [0.3000, 1.2100] | 0.0414 | 2.8526 | 0.2148 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz |
| DeepSeek-V3.2 | beta0p25 | joint_psrl | 0.8320 | 0.0796 | 0.8800 | [0.7800, 0.9000] | 0.0416 | 2.8384 | 0.2051 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz |
| DeepSeek-V3.2 | beta0p25 | map_greedy | 0.7120 | 0.4663 | 0.7200 | [0.6400, 0.7300] | 0.0356 | 2.7144 | 0.2248 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz |
| DeepSeek-V3.2 | beta0p25 | psrl_notype | 13.9120 | 7.3737 | 13.8200 | [6.3800, 20.8800] | 0.6956 | 2.1744 | 0.7952 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz |
| DeepSeek-V3.2 | beta0p25 | iql | 28.3420 | 16.9136 | 23.5000 | [21.5600, 32.3500] | 1.4171 | 1.3969 | 0.8222 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz |
| DeepSeek-V3.2 | beta0p25 | random | 28.2660 | 5.1241 | 28.1400 | [24.2100, 31.7800] | 1.4133 | 1.4767 | 0.5568 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz |
| DeepSeek-V3.2 | beta0p25 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.9500 | 0.0447 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz |
| DeepSeek-V3.2 | beta0p5 | hpsmg_plus | 0.4000 | 0.8000 | 0.0000 | [0.0000, 0.0000] | 0.0200 | 2.7600 | 0.1020 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p5.npz |
| DeepSeek-V3.2 | beta0p5 | hpsmg | 0.8280 | 0.5414 | 1.1100 | [0.3000, 1.2100] | 0.0414 | 2.8526 | 0.2148 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p5.npz |
| DeepSeek-V3.2 | beta0p5 | joint_psrl | 0.8320 | 0.0796 | 0.8800 | [0.7800, 0.9000] | 0.0416 | 2.8384 | 0.2051 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p5.npz |
| DeepSeek-V3.2 | beta0p5 | map_greedy | 0.7120 | 0.4663 | 0.7200 | [0.6400, 0.7300] | 0.0356 | 2.7144 | 0.2248 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p5.npz |
| DeepSeek-V3.2 | beta0p5 | psrl_notype | 13.9120 | 7.3737 | 13.8200 | [6.3800, 20.8800] | 0.6956 | 2.1744 | 0.7952 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p5.npz |
| DeepSeek-V3.2 | beta0p5 | iql | 28.3420 | 16.9136 | 23.5000 | [21.5600, 32.3500] | 1.4171 | 1.3969 | 0.8222 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p5.npz |
| DeepSeek-V3.2 | beta0p5 | random | 28.2660 | 5.1241 | 28.1400 | [24.2100, 31.7800] | 1.4133 | 1.4767 | 0.5568 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p5.npz |
| DeepSeek-V3.2 | beta0p5 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.9500 | 0.0447 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p5.npz |
| DeepSeek-V3.2 | beta0p75 | hpsmg_plus | 0.4000 | 0.8000 | 0.0000 | [0.0000, 0.0000] | 0.0200 | 2.7600 | 0.1020 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p75.npz |
| DeepSeek-V3.2 | beta0p75 | hpsmg | 0.8280 | 0.5414 | 1.1100 | [0.3000, 1.2100] | 0.0414 | 2.8526 | 0.2148 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p75.npz |
| DeepSeek-V3.2 | beta0p75 | joint_psrl | 0.8320 | 0.0796 | 0.8800 | [0.7800, 0.9000] | 0.0416 | 2.8384 | 0.2051 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p75.npz |
| DeepSeek-V3.2 | beta0p75 | map_greedy | 0.7120 | 0.4663 | 0.7200 | [0.6400, 0.7300] | 0.0356 | 2.7144 | 0.2248 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p75.npz |
| DeepSeek-V3.2 | beta0p75 | psrl_notype | 13.9120 | 7.3737 | 13.8200 | [6.3800, 20.8800] | 0.6956 | 2.1744 | 0.7952 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p75.npz |
| DeepSeek-V3.2 | beta0p75 | iql | 28.3420 | 16.9136 | 23.5000 | [21.5600, 32.3500] | 1.4171 | 1.3969 | 0.8222 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p75.npz |
| DeepSeek-V3.2 | beta0p75 | random | 28.2660 | 5.1241 | 28.1400 | [24.2100, 31.7800] | 1.4133 | 1.4767 | 0.5568 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p75.npz |
| DeepSeek-V3.2 | beta0p75 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.9500 | 0.0447 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p75.npz |
| DeepSeek-V3.2 | beta1 | hpsmg_plus | 0.5300 | 0.7769 | 0.0000 | [0.0000, 0.6500] | 0.0265 | 2.7535 | 0.1291 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta1.npz |
| DeepSeek-V3.2 | beta1 | hpsmg | 0.8280 | 0.5414 | 1.1100 | [0.3000, 1.2100] | 0.0414 | 2.8526 | 0.2148 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta1.npz |
| DeepSeek-V3.2 | beta1 | joint_psrl | 0.8320 | 0.0796 | 0.8800 | [0.7800, 0.9000] | 0.0416 | 2.8384 | 0.2051 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta1.npz |
| DeepSeek-V3.2 | beta1 | map_greedy | 0.7120 | 0.4663 | 0.7200 | [0.6400, 0.7300] | 0.0356 | 2.7144 | 0.2248 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta1.npz |
| DeepSeek-V3.2 | beta1 | psrl_notype | 13.9120 | 7.3737 | 13.8200 | [6.3800, 20.8800] | 0.6956 | 2.1744 | 0.7952 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta1.npz |
| DeepSeek-V3.2 | beta1 | iql | 28.3420 | 16.9136 | 23.5000 | [21.5600, 32.3500] | 1.4171 | 1.3969 | 0.8222 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta1.npz |
| DeepSeek-V3.2 | beta1 | random | 28.2660 | 5.1241 | 28.1400 | [24.2100, 31.7800] | 1.4133 | 1.4767 | 0.5568 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta1.npz |
| DeepSeek-V3.2 | beta1 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.9500 | 0.0447 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta1.npz |
| DeepSeek-V3.2 | beta1p5 | hpsmg_plus | 0.6300 | 0.3295 | 0.7500 | [0.6500, 0.8000] | 0.0315 | 2.7485 | 0.1970 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta1p5.npz |
| DeepSeek-V3.2 | beta1p5 | hpsmg | 0.8280 | 0.5414 | 1.1100 | [0.3000, 1.2100] | 0.0414 | 2.8526 | 0.2148 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta1p5.npz |
| DeepSeek-V3.2 | beta1p5 | joint_psrl | 0.8320 | 0.0796 | 0.8800 | [0.7800, 0.9000] | 0.0416 | 2.8384 | 0.2051 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta1p5.npz |
| DeepSeek-V3.2 | beta1p5 | map_greedy | 0.7120 | 0.4663 | 0.7200 | [0.6400, 0.7300] | 0.0356 | 2.7144 | 0.2248 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta1p5.npz |
| DeepSeek-V3.2 | beta1p5 | psrl_notype | 13.9120 | 7.3737 | 13.8200 | [6.3800, 20.8800] | 0.6956 | 2.1744 | 0.7952 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta1p5.npz |
| DeepSeek-V3.2 | beta1p5 | iql | 28.3420 | 16.9136 | 23.5000 | [21.5600, 32.3500] | 1.4171 | 1.3969 | 0.8222 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta1p5.npz |
| DeepSeek-V3.2 | beta1p5 | random | 28.2660 | 5.1241 | 28.1400 | [24.2100, 31.7800] | 1.4133 | 1.4767 | 0.5568 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta1p5.npz |
| DeepSeek-V3.2 | beta1p5 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.9500 | 0.0447 | results/cloudgpt/E2_DeepSeek_V3_2_c19_beta1p5.npz |
| gpt-5.4-nano | beta0 | hpsmg_plus | 0.9120 | 0.2919 | 0.9000 | [0.7200, 1.2200] | 0.0456 | 2.5604 | 0.2178 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0.npz |
| gpt-5.4-nano | beta0 | hpsmg | 0.6440 | 0.6310 | 0.5800 | [0.1600, 0.6800] | 0.0322 | 2.8198 | 0.2445 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0.npz |
| gpt-5.4-nano | beta0 | joint_psrl | 1.4920 | 0.3417 | 1.5100 | [1.3000, 1.7600] | 0.0746 | 2.7014 | 0.3390 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0.npz |
| gpt-5.4-nano | beta0 | map_greedy | 0.8540 | 0.4209 | 0.9800 | [0.4500, 1.0200] | 0.0427 | 2.6373 | 0.2614 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0.npz |
| gpt-5.4-nano | beta0 | psrl_notype | 17.7200 | 1.6769 | 17.5200 | [17.3600, 19.2700] | 0.8860 | 1.7500 | 0.6599 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0.npz |
| gpt-5.4-nano | beta0 | iql | 24.7918 | 11.7281 | 26.0100 | [17.1900, 29.0691] | 1.2396 | 1.4444 | 0.6255 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0.npz |
| gpt-5.4-nano | beta0 | random | 26.4584 | 1.8140 | 27.0743 | [24.5991, 28.0925] | 1.3229 | 1.5191 | 0.5483 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0.npz |
| gpt-5.4-nano | beta0 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.8380 | 0.1673 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0.npz |
| gpt-5.4-nano | beta0p05 | hpsmg_plus | 0.9120 | 0.2919 | 0.9000 | [0.7200, 1.2200] | 0.0456 | 2.5604 | 0.2178 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p05.npz |
| gpt-5.4-nano | beta0p05 | hpsmg | 0.6440 | 0.6310 | 0.5800 | [0.1600, 0.6800] | 0.0322 | 2.8198 | 0.2445 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p05.npz |
| gpt-5.4-nano | beta0p05 | joint_psrl | 1.4920 | 0.3417 | 1.5100 | [1.3000, 1.7600] | 0.0746 | 2.7014 | 0.3390 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p05.npz |
| gpt-5.4-nano | beta0p05 | map_greedy | 0.8540 | 0.4209 | 0.9800 | [0.4500, 1.0200] | 0.0427 | 2.6373 | 0.2614 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p05.npz |
| gpt-5.4-nano | beta0p05 | psrl_notype | 17.7200 | 1.6769 | 17.5200 | [17.3600, 19.2700] | 0.8860 | 1.7500 | 0.6599 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p05.npz |
| gpt-5.4-nano | beta0p05 | iql | 24.7918 | 11.7281 | 26.0100 | [17.1900, 29.0691] | 1.2396 | 1.4444 | 0.6255 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p05.npz |
| gpt-5.4-nano | beta0p05 | random | 26.4584 | 1.8140 | 27.0743 | [24.5991, 28.0925] | 1.3229 | 1.5191 | 0.5483 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p05.npz |
| gpt-5.4-nano | beta0p05 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.8380 | 0.1673 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p05.npz |
| gpt-5.4-nano | beta0p1 | hpsmg_plus | 0.9120 | 0.2919 | 0.9000 | [0.7200, 1.2200] | 0.0456 | 2.5604 | 0.2178 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p1.npz |
| gpt-5.4-nano | beta0p1 | hpsmg | 0.6440 | 0.6310 | 0.5800 | [0.1600, 0.6800] | 0.0322 | 2.8198 | 0.2445 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p1.npz |
| gpt-5.4-nano | beta0p1 | joint_psrl | 1.4920 | 0.3417 | 1.5100 | [1.3000, 1.7600] | 0.0746 | 2.7014 | 0.3390 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p1.npz |
| gpt-5.4-nano | beta0p1 | map_greedy | 0.8540 | 0.4209 | 0.9800 | [0.4500, 1.0200] | 0.0427 | 2.6373 | 0.2614 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p1.npz |
| gpt-5.4-nano | beta0p1 | psrl_notype | 17.7200 | 1.6769 | 17.5200 | [17.3600, 19.2700] | 0.8860 | 1.7500 | 0.6599 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p1.npz |
| gpt-5.4-nano | beta0p1 | iql | 24.7918 | 11.7281 | 26.0100 | [17.1900, 29.0691] | 1.2396 | 1.4444 | 0.6255 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p1.npz |
| gpt-5.4-nano | beta0p1 | random | 26.4584 | 1.8140 | 27.0743 | [24.5991, 28.0925] | 1.3229 | 1.5191 | 0.5483 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p1.npz |
| gpt-5.4-nano | beta0p1 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.8380 | 0.1673 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p1.npz |
| gpt-5.4-nano | beta0p25 | hpsmg_plus | 0.9120 | 0.2919 | 0.9000 | [0.7200, 1.2200] | 0.0456 | 2.5604 | 0.2178 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p25.npz |
| gpt-5.4-nano | beta0p25 | hpsmg | 0.6440 | 0.6310 | 0.5800 | [0.1600, 0.6800] | 0.0322 | 2.8198 | 0.2445 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p25.npz |
| gpt-5.4-nano | beta0p25 | joint_psrl | 1.4920 | 0.3417 | 1.5100 | [1.3000, 1.7600] | 0.0746 | 2.7014 | 0.3390 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p25.npz |
| gpt-5.4-nano | beta0p25 | map_greedy | 0.8540 | 0.4209 | 0.9800 | [0.4500, 1.0200] | 0.0427 | 2.6373 | 0.2614 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p25.npz |
| gpt-5.4-nano | beta0p25 | psrl_notype | 17.7200 | 1.6769 | 17.5200 | [17.3600, 19.2700] | 0.8860 | 1.7500 | 0.6599 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p25.npz |
| gpt-5.4-nano | beta0p25 | iql | 24.7918 | 11.7281 | 26.0100 | [17.1900, 29.0691] | 1.2396 | 1.4444 | 0.6255 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p25.npz |
| gpt-5.4-nano | beta0p25 | random | 26.4584 | 1.8140 | 27.0743 | [24.5991, 28.0925] | 1.3229 | 1.5191 | 0.5483 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p25.npz |
| gpt-5.4-nano | beta0p25 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.8380 | 0.1673 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p25.npz |
| gpt-5.4-nano | beta0p5 | hpsmg_plus | 0.9360 | 0.2798 | 0.9000 | [0.8400, 1.2200] | 0.0468 | 2.5592 | 0.2171 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p5.npz |
| gpt-5.4-nano | beta0p5 | hpsmg | 0.6440 | 0.6310 | 0.5800 | [0.1600, 0.6800] | 0.0322 | 2.8198 | 0.2445 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p5.npz |
| gpt-5.4-nano | beta0p5 | joint_psrl | 1.4920 | 0.3417 | 1.5100 | [1.3000, 1.7600] | 0.0746 | 2.7014 | 0.3390 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p5.npz |
| gpt-5.4-nano | beta0p5 | map_greedy | 0.8540 | 0.4209 | 0.9800 | [0.4500, 1.0200] | 0.0427 | 2.6373 | 0.2614 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p5.npz |
| gpt-5.4-nano | beta0p5 | psrl_notype | 17.7200 | 1.6769 | 17.5200 | [17.3600, 19.2700] | 0.8860 | 1.7500 | 0.6599 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p5.npz |
| gpt-5.4-nano | beta0p5 | iql | 24.7918 | 11.7281 | 26.0100 | [17.1900, 29.0691] | 1.2396 | 1.4444 | 0.6255 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p5.npz |
| gpt-5.4-nano | beta0p5 | random | 26.4584 | 1.8140 | 27.0743 | [24.5991, 28.0925] | 1.3229 | 1.5191 | 0.5483 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p5.npz |
| gpt-5.4-nano | beta0p5 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.8380 | 0.1673 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p5.npz |
| gpt-5.4-nano | beta0p75 | hpsmg_plus | 0.9940 | 0.3780 | 0.9000 | [0.8400, 1.0800] | 0.0497 | 2.5563 | 0.2252 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p75.npz |
| gpt-5.4-nano | beta0p75 | hpsmg | 0.6440 | 0.6310 | 0.5800 | [0.1600, 0.6800] | 0.0322 | 2.8198 | 0.2445 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p75.npz |
| gpt-5.4-nano | beta0p75 | joint_psrl | 1.4920 | 0.3417 | 1.5100 | [1.3000, 1.7600] | 0.0746 | 2.7014 | 0.3390 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p75.npz |
| gpt-5.4-nano | beta0p75 | map_greedy | 0.8540 | 0.4209 | 0.9800 | [0.4500, 1.0200] | 0.0427 | 2.6373 | 0.2614 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p75.npz |
| gpt-5.4-nano | beta0p75 | psrl_notype | 17.7200 | 1.6769 | 17.5200 | [17.3600, 19.2700] | 0.8860 | 1.7500 | 0.6599 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p75.npz |
| gpt-5.4-nano | beta0p75 | iql | 24.7918 | 11.7281 | 26.0100 | [17.1900, 29.0691] | 1.2396 | 1.4444 | 0.6255 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p75.npz |
| gpt-5.4-nano | beta0p75 | random | 26.4584 | 1.8140 | 27.0743 | [24.5991, 28.0925] | 1.3229 | 1.5191 | 0.5483 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p75.npz |
| gpt-5.4-nano | beta0p75 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.8380 | 0.1673 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta0p75.npz |
| gpt-5.4-nano | beta1 | hpsmg_plus | 0.8980 | 0.4040 | 0.8400 | [0.6000, 0.9000] | 0.0449 | 2.5611 | 0.2265 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta1.npz |
| gpt-5.4-nano | beta1 | hpsmg | 0.6440 | 0.6310 | 0.5800 | [0.1600, 0.6800] | 0.0322 | 2.8198 | 0.2445 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta1.npz |
| gpt-5.4-nano | beta1 | joint_psrl | 1.4920 | 0.3417 | 1.5100 | [1.3000, 1.7600] | 0.0746 | 2.7014 | 0.3390 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta1.npz |
| gpt-5.4-nano | beta1 | map_greedy | 0.8540 | 0.4209 | 0.9800 | [0.4500, 1.0200] | 0.0427 | 2.6373 | 0.2614 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta1.npz |
| gpt-5.4-nano | beta1 | psrl_notype | 17.7200 | 1.6769 | 17.5200 | [17.3600, 19.2700] | 0.8860 | 1.7500 | 0.6599 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta1.npz |
| gpt-5.4-nano | beta1 | iql | 24.7918 | 11.7281 | 26.0100 | [17.1900, 29.0691] | 1.2396 | 1.4444 | 0.6255 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta1.npz |
| gpt-5.4-nano | beta1 | random | 26.4584 | 1.8140 | 27.0743 | [24.5991, 28.0925] | 1.3229 | 1.5191 | 0.5483 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta1.npz |
| gpt-5.4-nano | beta1 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.8380 | 0.1673 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta1.npz |
| gpt-5.4-nano | beta1p5 | hpsmg_plus | 0.9260 | 0.3993 | 0.9000 | [0.6000, 0.9600] | 0.0463 | 2.5597 | 0.2259 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta1p5.npz |
| gpt-5.4-nano | beta1p5 | hpsmg | 0.6440 | 0.6310 | 0.5800 | [0.1600, 0.6800] | 0.0322 | 2.8198 | 0.2445 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta1p5.npz |
| gpt-5.4-nano | beta1p5 | joint_psrl | 1.4920 | 0.3417 | 1.5100 | [1.3000, 1.7600] | 0.0746 | 2.7014 | 0.3390 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta1p5.npz |
| gpt-5.4-nano | beta1p5 | map_greedy | 0.8540 | 0.4209 | 0.9800 | [0.4500, 1.0200] | 0.0427 | 2.6373 | 0.2614 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta1p5.npz |
| gpt-5.4-nano | beta1p5 | psrl_notype | 17.7200 | 1.6769 | 17.5200 | [17.3600, 19.2700] | 0.8860 | 1.7500 | 0.6599 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta1p5.npz |
| gpt-5.4-nano | beta1p5 | iql | 24.7918 | 11.7281 | 26.0100 | [17.1900, 29.0691] | 1.2396 | 1.4444 | 0.6255 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta1p5.npz |
| gpt-5.4-nano | beta1p5 | random | 26.4584 | 1.8140 | 27.0743 | [24.5991, 28.0925] | 1.3229 | 1.5191 | 0.5483 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta1p5.npz |
| gpt-5.4-nano | beta1p5 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.8380 | 0.1673 | results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_beta1p5.npz |
| Kimi-K2.6 | beta0 | hpsmg_plus | 0.7440 | 0.5125 | 0.4600 | [0.4400, 0.7200] | 0.0372 | 2.5468 | 0.2102 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0.npz |
| Kimi-K2.6 | beta0 | hpsmg | 0.6320 | 0.6091 | 0.5800 | [0.1600, 0.6800] | 0.0316 | 2.8204 | 0.2405 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0.npz |
| Kimi-K2.6 | beta0 | joint_psrl | 1.6500 | 0.4038 | 1.7000 | [1.5100, 1.9600] | 0.0825 | 2.6935 | 0.3682 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0.npz |
| Kimi-K2.6 | beta0 | map_greedy | 0.7620 | 0.3912 | 0.6200 | [0.4500, 1.0200] | 0.0381 | 2.5499 | 0.2925 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0.npz |
| Kimi-K2.6 | beta0 | psrl_notype | 19.5060 | 2.6101 | 19.0700 | [18.2500, 21.6800] | 0.9753 | 1.7787 | 0.6778 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0.npz |
| Kimi-K2.6 | beta0 | iql | 20.1180 | 18.5267 | 17.0400 | [4.2400, 24.6900] | 1.0059 | 1.6661 | 0.8508 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0.npz |
| Kimi-K2.6 | beta0 | random | 26.5400 | 4.5138 | 27.7300 | [22.2100, 28.4200] | 1.3270 | 1.4830 | 0.4153 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0.npz |
| Kimi-K2.6 | beta0 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.7840 | 0.2404 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0.npz |
| Kimi-K2.6 | beta0p05 | hpsmg_plus | 0.7440 | 0.5125 | 0.4600 | [0.4400, 0.7200] | 0.0372 | 2.5468 | 0.2102 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p05.npz |
| Kimi-K2.6 | beta0p05 | hpsmg | 0.6320 | 0.6091 | 0.5800 | [0.1600, 0.6800] | 0.0316 | 2.8204 | 0.2405 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p05.npz |
| Kimi-K2.6 | beta0p05 | joint_psrl | 1.6500 | 0.4038 | 1.7000 | [1.5100, 1.9600] | 0.0825 | 2.6935 | 0.3682 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p05.npz |
| Kimi-K2.6 | beta0p05 | map_greedy | 0.7620 | 0.3912 | 0.6200 | [0.4500, 1.0200] | 0.0381 | 2.5499 | 0.2925 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p05.npz |
| Kimi-K2.6 | beta0p05 | psrl_notype | 19.5060 | 2.6101 | 19.0700 | [18.2500, 21.6800] | 0.9753 | 1.7787 | 0.6778 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p05.npz |
| Kimi-K2.6 | beta0p05 | iql | 20.1180 | 18.5267 | 17.0400 | [4.2400, 24.6900] | 1.0059 | 1.6661 | 0.8508 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p05.npz |
| Kimi-K2.6 | beta0p05 | random | 26.5400 | 4.5138 | 27.7300 | [22.2100, 28.4200] | 1.3270 | 1.4830 | 0.4153 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p05.npz |
| Kimi-K2.6 | beta0p05 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.7840 | 0.2404 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p05.npz |
| Kimi-K2.6 | beta0p1 | hpsmg_plus | 0.7440 | 0.5125 | 0.4600 | [0.4400, 0.7200] | 0.0372 | 2.5468 | 0.2102 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p1.npz |
| Kimi-K2.6 | beta0p1 | hpsmg | 0.6320 | 0.6091 | 0.5800 | [0.1600, 0.6800] | 0.0316 | 2.8204 | 0.2405 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p1.npz |
| Kimi-K2.6 | beta0p1 | joint_psrl | 1.6500 | 0.4038 | 1.7000 | [1.5100, 1.9600] | 0.0825 | 2.6935 | 0.3682 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p1.npz |
| Kimi-K2.6 | beta0p1 | map_greedy | 0.7620 | 0.3912 | 0.6200 | [0.4500, 1.0200] | 0.0381 | 2.5499 | 0.2925 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p1.npz |
| Kimi-K2.6 | beta0p1 | psrl_notype | 19.5060 | 2.6101 | 19.0700 | [18.2500, 21.6800] | 0.9753 | 1.7787 | 0.6778 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p1.npz |
| Kimi-K2.6 | beta0p1 | iql | 20.1180 | 18.5267 | 17.0400 | [4.2400, 24.6900] | 1.0059 | 1.6661 | 0.8508 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p1.npz |
| Kimi-K2.6 | beta0p1 | random | 26.5400 | 4.5138 | 27.7300 | [22.2100, 28.4200] | 1.3270 | 1.4830 | 0.4153 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p1.npz |
| Kimi-K2.6 | beta0p1 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.7840 | 0.2404 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p1.npz |
| Kimi-K2.6 | beta0p25 | hpsmg_plus | 0.7040 | 0.4351 | 0.4600 | [0.4400, 0.7200] | 0.0352 | 2.5488 | 0.2107 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p25.npz |
| Kimi-K2.6 | beta0p25 | hpsmg | 0.6320 | 0.6091 | 0.5800 | [0.1600, 0.6800] | 0.0316 | 2.8204 | 0.2405 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p25.npz |
| Kimi-K2.6 | beta0p25 | joint_psrl | 1.6500 | 0.4038 | 1.7000 | [1.5100, 1.9600] | 0.0825 | 2.6935 | 0.3682 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p25.npz |
| Kimi-K2.6 | beta0p25 | map_greedy | 0.7620 | 0.3912 | 0.6200 | [0.4500, 1.0200] | 0.0381 | 2.5499 | 0.2925 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p25.npz |
| Kimi-K2.6 | beta0p25 | psrl_notype | 19.5060 | 2.6101 | 19.0700 | [18.2500, 21.6800] | 0.9753 | 1.7787 | 0.6778 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p25.npz |
| Kimi-K2.6 | beta0p25 | iql | 20.1180 | 18.5267 | 17.0400 | [4.2400, 24.6900] | 1.0059 | 1.6661 | 0.8508 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p25.npz |
| Kimi-K2.6 | beta0p25 | random | 26.5400 | 4.5138 | 27.7300 | [22.2100, 28.4200] | 1.3270 | 1.4830 | 0.4153 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p25.npz |
| Kimi-K2.6 | beta0p25 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.7840 | 0.2404 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p25.npz |
| Kimi-K2.6 | beta0p5 | hpsmg_plus | 0.7280 | 0.4387 | 0.4600 | [0.4400, 0.8400] | 0.0364 | 2.5476 | 0.2100 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p5.npz |
| Kimi-K2.6 | beta0p5 | hpsmg | 0.6320 | 0.6091 | 0.5800 | [0.1600, 0.6800] | 0.0316 | 2.8204 | 0.2405 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p5.npz |
| Kimi-K2.6 | beta0p5 | joint_psrl | 1.6500 | 0.4038 | 1.7000 | [1.5100, 1.9600] | 0.0825 | 2.6935 | 0.3682 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p5.npz |
| Kimi-K2.6 | beta0p5 | map_greedy | 0.7620 | 0.3912 | 0.6200 | [0.4500, 1.0200] | 0.0381 | 2.5499 | 0.2925 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p5.npz |
| Kimi-K2.6 | beta0p5 | psrl_notype | 19.5060 | 2.6101 | 19.0700 | [18.2500, 21.6800] | 0.9753 | 1.7787 | 0.6778 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p5.npz |
| Kimi-K2.6 | beta0p5 | iql | 20.1180 | 18.5267 | 17.0400 | [4.2400, 24.6900] | 1.0059 | 1.6661 | 0.8508 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p5.npz |
| Kimi-K2.6 | beta0p5 | random | 26.5400 | 4.5138 | 27.7300 | [22.2100, 28.4200] | 1.3270 | 1.4830 | 0.4153 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p5.npz |
| Kimi-K2.6 | beta0p5 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.7840 | 0.2404 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p5.npz |
| Kimi-K2.6 | beta0p75 | hpsmg_plus | 0.7280 | 0.4387 | 0.4600 | [0.4400, 0.8400] | 0.0364 | 2.5476 | 0.2100 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p75.npz |
| Kimi-K2.6 | beta0p75 | hpsmg | 0.6320 | 0.6091 | 0.5800 | [0.1600, 0.6800] | 0.0316 | 2.8204 | 0.2405 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p75.npz |
| Kimi-K2.6 | beta0p75 | joint_psrl | 1.6500 | 0.4038 | 1.7000 | [1.5100, 1.9600] | 0.0825 | 2.6935 | 0.3682 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p75.npz |
| Kimi-K2.6 | beta0p75 | map_greedy | 0.7620 | 0.3912 | 0.6200 | [0.4500, 1.0200] | 0.0381 | 2.5499 | 0.2925 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p75.npz |
| Kimi-K2.6 | beta0p75 | psrl_notype | 19.5060 | 2.6101 | 19.0700 | [18.2500, 21.6800] | 0.9753 | 1.7787 | 0.6778 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p75.npz |
| Kimi-K2.6 | beta0p75 | iql | 20.1180 | 18.5267 | 17.0400 | [4.2400, 24.6900] | 1.0059 | 1.6661 | 0.8508 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p75.npz |
| Kimi-K2.6 | beta0p75 | random | 26.5400 | 4.5138 | 27.7300 | [22.2100, 28.4200] | 1.3270 | 1.4830 | 0.4153 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p75.npz |
| Kimi-K2.6 | beta0p75 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.7840 | 0.2404 | results/cloudgpt/E2_Kimi_K2_6_c19_beta0p75.npz |
| Kimi-K2.6 | beta1 | hpsmg_plus | 0.7280 | 0.4387 | 0.4600 | [0.4400, 0.8400] | 0.0364 | 2.5476 | 0.2100 | results/cloudgpt/E2_Kimi_K2_6_c19_beta1.npz |
| Kimi-K2.6 | beta1 | hpsmg | 0.6320 | 0.6091 | 0.5800 | [0.1600, 0.6800] | 0.0316 | 2.8204 | 0.2405 | results/cloudgpt/E2_Kimi_K2_6_c19_beta1.npz |
| Kimi-K2.6 | beta1 | joint_psrl | 1.6500 | 0.4038 | 1.7000 | [1.5100, 1.9600] | 0.0825 | 2.6935 | 0.3682 | results/cloudgpt/E2_Kimi_K2_6_c19_beta1.npz |
| Kimi-K2.6 | beta1 | map_greedy | 0.7620 | 0.3912 | 0.6200 | [0.4500, 1.0200] | 0.0381 | 2.5499 | 0.2925 | results/cloudgpt/E2_Kimi_K2_6_c19_beta1.npz |
| Kimi-K2.6 | beta1 | psrl_notype | 19.5060 | 2.6101 | 19.0700 | [18.2500, 21.6800] | 0.9753 | 1.7787 | 0.6778 | results/cloudgpt/E2_Kimi_K2_6_c19_beta1.npz |
| Kimi-K2.6 | beta1 | iql | 20.1180 | 18.5267 | 17.0400 | [4.2400, 24.6900] | 1.0059 | 1.6661 | 0.8508 | results/cloudgpt/E2_Kimi_K2_6_c19_beta1.npz |
| Kimi-K2.6 | beta1 | random | 26.5400 | 4.5138 | 27.7300 | [22.2100, 28.4200] | 1.3270 | 1.4830 | 0.4153 | results/cloudgpt/E2_Kimi_K2_6_c19_beta1.npz |
| Kimi-K2.6 | beta1 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.7840 | 0.2404 | results/cloudgpt/E2_Kimi_K2_6_c19_beta1.npz |
| Kimi-K2.6 | beta1p5 | hpsmg_plus | 0.7520 | 0.4473 | 0.4600 | [0.4400, 0.9600] | 0.0376 | 2.5464 | 0.2092 | results/cloudgpt/E2_Kimi_K2_6_c19_beta1p5.npz |
| Kimi-K2.6 | beta1p5 | hpsmg | 0.6320 | 0.6091 | 0.5800 | [0.1600, 0.6800] | 0.0316 | 2.8204 | 0.2405 | results/cloudgpt/E2_Kimi_K2_6_c19_beta1p5.npz |
| Kimi-K2.6 | beta1p5 | joint_psrl | 1.6500 | 0.4038 | 1.7000 | [1.5100, 1.9600] | 0.0825 | 2.6935 | 0.3682 | results/cloudgpt/E2_Kimi_K2_6_c19_beta1p5.npz |
| Kimi-K2.6 | beta1p5 | map_greedy | 0.7620 | 0.3912 | 0.6200 | [0.4500, 1.0200] | 0.0381 | 2.5499 | 0.2925 | results/cloudgpt/E2_Kimi_K2_6_c19_beta1p5.npz |
| Kimi-K2.6 | beta1p5 | psrl_notype | 19.5060 | 2.6101 | 19.0700 | [18.2500, 21.6800] | 0.9753 | 1.7787 | 0.6778 | results/cloudgpt/E2_Kimi_K2_6_c19_beta1p5.npz |
| Kimi-K2.6 | beta1p5 | iql | 20.1180 | 18.5267 | 17.0400 | [4.2400, 24.6900] | 1.0059 | 1.6661 | 0.8508 | results/cloudgpt/E2_Kimi_K2_6_c19_beta1p5.npz |
| Kimi-K2.6 | beta1p5 | random | 26.5400 | 4.5138 | 27.7300 | [22.2100, 28.4200] | 1.3270 | 1.4830 | 0.4153 | results/cloudgpt/E2_Kimi_K2_6_c19_beta1p5.npz |
| Kimi-K2.6 | beta1p5 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.7840 | 0.2404 | results/cloudgpt/E2_Kimi_K2_6_c19_beta1p5.npz |
| Llama-4-Maverick | beta0 | hpsmg_plus | 0.9660 | 1.9320 | 0.0000 | [0.0000, 0.0000] | 0.0483 | 2.7497 | 0.1481 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0.npz |
| Llama-4-Maverick | beta0 | hpsmg | 0.7320 | 0.6086 | 0.7700 | [0.1600, 1.0600] | 0.0366 | 2.8574 | 0.2338 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0.npz |
| Llama-4-Maverick | beta0 | joint_psrl | 1.1940 | 0.3469 | 1.1600 | [0.9600, 1.4500] | 0.0597 | 2.7543 | 0.2735 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0.npz |
| Llama-4-Maverick | beta0 | map_greedy | 0.9740 | 0.4388 | 1.1200 | [0.6500, 1.1800] | 0.0487 | 2.7513 | 0.2569 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0.npz |
| Llama-4-Maverick | beta0 | psrl_notype | 10.6540 | 4.3567 | 10.2300 | [5.9200, 15.5800] | 0.5327 | 2.3113 | 0.7322 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0.npz |
| Llama-4-Maverick | beta0 | iql | 27.5260 | 16.3392 | 26.5700 | [17.4900, 28.2000] | 1.3763 | 1.4837 | 0.8057 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0.npz |
| Llama-4-Maverick | beta0 | random | 24.3418 | 4.3234 | 24.7500 | [23.8600, 24.9800] | 1.2171 | 1.6529 | 0.5765 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0.npz |
| Llama-4-Maverick | beta0 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.8900 | 0.1331 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0.npz |
| Llama-4-Maverick | beta0p05 | hpsmg_plus | 0.9660 | 1.9320 | 0.0000 | [0.0000, 0.0000] | 0.0483 | 2.7497 | 0.1481 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p05.npz |
| Llama-4-Maverick | beta0p05 | hpsmg | 0.7320 | 0.6086 | 0.7700 | [0.1600, 1.0600] | 0.0366 | 2.8574 | 0.2338 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p05.npz |
| Llama-4-Maverick | beta0p05 | joint_psrl | 1.1940 | 0.3469 | 1.1600 | [0.9600, 1.4500] | 0.0597 | 2.7543 | 0.2735 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p05.npz |
| Llama-4-Maverick | beta0p05 | map_greedy | 0.9740 | 0.4388 | 1.1200 | [0.6500, 1.1800] | 0.0487 | 2.7513 | 0.2569 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p05.npz |
| Llama-4-Maverick | beta0p05 | psrl_notype | 10.6540 | 4.3567 | 10.2300 | [5.9200, 15.5800] | 0.5327 | 2.3113 | 0.7322 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p05.npz |
| Llama-4-Maverick | beta0p05 | iql | 27.5260 | 16.3392 | 26.5700 | [17.4900, 28.2000] | 1.3763 | 1.4837 | 0.8057 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p05.npz |
| Llama-4-Maverick | beta0p05 | random | 24.3418 | 4.3234 | 24.7500 | [23.8600, 24.9800] | 1.2171 | 1.6529 | 0.5765 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p05.npz |
| Llama-4-Maverick | beta0p05 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.8900 | 0.1331 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p05.npz |
| Llama-4-Maverick | beta0p1 | hpsmg_plus | 0.9660 | 1.9320 | 0.0000 | [0.0000, 0.0000] | 0.0483 | 2.7497 | 0.1481 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p1.npz |
| Llama-4-Maverick | beta0p1 | hpsmg | 0.7320 | 0.6086 | 0.7700 | [0.1600, 1.0600] | 0.0366 | 2.8574 | 0.2338 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p1.npz |
| Llama-4-Maverick | beta0p1 | joint_psrl | 1.1940 | 0.3469 | 1.1600 | [0.9600, 1.4500] | 0.0597 | 2.7543 | 0.2735 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p1.npz |
| Llama-4-Maverick | beta0p1 | map_greedy | 0.9740 | 0.4388 | 1.1200 | [0.6500, 1.1800] | 0.0487 | 2.7513 | 0.2569 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p1.npz |
| Llama-4-Maverick | beta0p1 | psrl_notype | 10.6540 | 4.3567 | 10.2300 | [5.9200, 15.5800] | 0.5327 | 2.3113 | 0.7322 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p1.npz |
| Llama-4-Maverick | beta0p1 | iql | 27.5260 | 16.3392 | 26.5700 | [17.4900, 28.2000] | 1.3763 | 1.4837 | 0.8057 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p1.npz |
| Llama-4-Maverick | beta0p1 | random | 24.3418 | 4.3234 | 24.7500 | [23.8600, 24.9800] | 1.2171 | 1.6529 | 0.5765 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p1.npz |
| Llama-4-Maverick | beta0p1 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.8900 | 0.1331 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p1.npz |
| Llama-4-Maverick | beta0p25 | hpsmg_plus | 0.3120 | 0.6240 | 0.0000 | [0.0000, 0.0000] | 0.0156 | 2.7824 | 0.1305 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p25.npz |
| Llama-4-Maverick | beta0p25 | hpsmg | 0.7320 | 0.6086 | 0.7700 | [0.1600, 1.0600] | 0.0366 | 2.8574 | 0.2338 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p25.npz |
| Llama-4-Maverick | beta0p25 | joint_psrl | 1.1940 | 0.3469 | 1.1600 | [0.9600, 1.4500] | 0.0597 | 2.7543 | 0.2735 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p25.npz |
| Llama-4-Maverick | beta0p25 | map_greedy | 0.9740 | 0.4388 | 1.1200 | [0.6500, 1.1800] | 0.0487 | 2.7513 | 0.2569 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p25.npz |
| Llama-4-Maverick | beta0p25 | psrl_notype | 10.6540 | 4.3567 | 10.2300 | [5.9200, 15.5800] | 0.5327 | 2.3113 | 0.7322 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p25.npz |
| Llama-4-Maverick | beta0p25 | iql | 27.5260 | 16.3392 | 26.5700 | [17.4900, 28.2000] | 1.3763 | 1.4837 | 0.8057 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p25.npz |
| Llama-4-Maverick | beta0p25 | random | 24.3418 | 4.3234 | 24.7500 | [23.8600, 24.9800] | 1.2171 | 1.6529 | 0.5765 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p25.npz |
| Llama-4-Maverick | beta0p25 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.8900 | 0.1331 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p25.npz |
| Llama-4-Maverick | beta0p5 | hpsmg_plus | 0.3120 | 0.6240 | 0.0000 | [0.0000, 0.0000] | 0.0156 | 2.7824 | 0.1305 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p5.npz |
| Llama-4-Maverick | beta0p5 | hpsmg | 0.7320 | 0.6086 | 0.7700 | [0.1600, 1.0600] | 0.0366 | 2.8574 | 0.2338 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p5.npz |
| Llama-4-Maverick | beta0p5 | joint_psrl | 1.1940 | 0.3469 | 1.1600 | [0.9600, 1.4500] | 0.0597 | 2.7543 | 0.2735 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p5.npz |
| Llama-4-Maverick | beta0p5 | map_greedy | 0.9740 | 0.4388 | 1.1200 | [0.6500, 1.1800] | 0.0487 | 2.7513 | 0.2569 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p5.npz |
| Llama-4-Maverick | beta0p5 | psrl_notype | 10.6540 | 4.3567 | 10.2300 | [5.9200, 15.5800] | 0.5327 | 2.3113 | 0.7322 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p5.npz |
| Llama-4-Maverick | beta0p5 | iql | 27.5260 | 16.3392 | 26.5700 | [17.4900, 28.2000] | 1.3763 | 1.4837 | 0.8057 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p5.npz |
| Llama-4-Maverick | beta0p5 | random | 24.3418 | 4.3234 | 24.7500 | [23.8600, 24.9800] | 1.2171 | 1.6529 | 0.5765 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p5.npz |
| Llama-4-Maverick | beta0p5 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.8900 | 0.1331 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p5.npz |
| Llama-4-Maverick | beta0p75 | hpsmg_plus | 0.3120 | 0.6240 | 0.0000 | [0.0000, 0.0000] | 0.0156 | 2.7824 | 0.1305 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p75.npz |
| Llama-4-Maverick | beta0p75 | hpsmg | 0.7320 | 0.6086 | 0.7700 | [0.1600, 1.0600] | 0.0366 | 2.8574 | 0.2338 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p75.npz |
| Llama-4-Maverick | beta0p75 | joint_psrl | 1.1940 | 0.3469 | 1.1600 | [0.9600, 1.4500] | 0.0597 | 2.7543 | 0.2735 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p75.npz |
| Llama-4-Maverick | beta0p75 | map_greedy | 0.9740 | 0.4388 | 1.1200 | [0.6500, 1.1800] | 0.0487 | 2.7513 | 0.2569 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p75.npz |
| Llama-4-Maverick | beta0p75 | psrl_notype | 10.6540 | 4.3567 | 10.2300 | [5.9200, 15.5800] | 0.5327 | 2.3113 | 0.7322 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p75.npz |
| Llama-4-Maverick | beta0p75 | iql | 27.5260 | 16.3392 | 26.5700 | [17.4900, 28.2000] | 1.3763 | 1.4837 | 0.8057 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p75.npz |
| Llama-4-Maverick | beta0p75 | random | 24.3418 | 4.3234 | 24.7500 | [23.8600, 24.9800] | 1.2171 | 1.6529 | 0.5765 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p75.npz |
| Llama-4-Maverick | beta0p75 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.8900 | 0.1331 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta0p75.npz |
| Llama-4-Maverick | beta1 | hpsmg_plus | 0.3120 | 0.6240 | 0.0000 | [0.0000, 0.0000] | 0.0156 | 2.7824 | 0.1305 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta1.npz |
| Llama-4-Maverick | beta1 | hpsmg | 0.7320 | 0.6086 | 0.7700 | [0.1600, 1.0600] | 0.0366 | 2.8574 | 0.2338 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta1.npz |
| Llama-4-Maverick | beta1 | joint_psrl | 1.1940 | 0.3469 | 1.1600 | [0.9600, 1.4500] | 0.0597 | 2.7543 | 0.2735 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta1.npz |
| Llama-4-Maverick | beta1 | map_greedy | 0.9740 | 0.4388 | 1.1200 | [0.6500, 1.1800] | 0.0487 | 2.7513 | 0.2569 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta1.npz |
| Llama-4-Maverick | beta1 | psrl_notype | 10.6540 | 4.3567 | 10.2300 | [5.9200, 15.5800] | 0.5327 | 2.3113 | 0.7322 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta1.npz |
| Llama-4-Maverick | beta1 | iql | 27.5260 | 16.3392 | 26.5700 | [17.4900, 28.2000] | 1.3763 | 1.4837 | 0.8057 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta1.npz |
| Llama-4-Maverick | beta1 | random | 24.3418 | 4.3234 | 24.7500 | [23.8600, 24.9800] | 1.2171 | 1.6529 | 0.5765 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta1.npz |
| Llama-4-Maverick | beta1 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.8900 | 0.1331 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta1.npz |
| Llama-4-Maverick | beta1p5 | hpsmg_plus | 0.3120 | 0.6240 | 0.0000 | [0.0000, 0.0000] | 0.0156 | 2.7824 | 0.1305 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta1p5.npz |
| Llama-4-Maverick | beta1p5 | hpsmg | 0.7320 | 0.6086 | 0.7700 | [0.1600, 1.0600] | 0.0366 | 2.8574 | 0.2338 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta1p5.npz |
| Llama-4-Maverick | beta1p5 | joint_psrl | 1.1940 | 0.3469 | 1.1600 | [0.9600, 1.4500] | 0.0597 | 2.7543 | 0.2735 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta1p5.npz |
| Llama-4-Maverick | beta1p5 | map_greedy | 0.9740 | 0.4388 | 1.1200 | [0.6500, 1.1800] | 0.0487 | 2.7513 | 0.2569 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta1p5.npz |
| Llama-4-Maverick | beta1p5 | psrl_notype | 10.6540 | 4.3567 | 10.2300 | [5.9200, 15.5800] | 0.5327 | 2.3113 | 0.7322 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta1p5.npz |
| Llama-4-Maverick | beta1p5 | iql | 27.5260 | 16.3392 | 26.5700 | [17.4900, 28.2000] | 1.3763 | 1.4837 | 0.8057 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta1p5.npz |
| Llama-4-Maverick | beta1p5 | random | 24.3418 | 4.3234 | 24.7500 | [23.8600, 24.9800] | 1.2171 | 1.6529 | 0.5765 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta1p5.npz |
| Llama-4-Maverick | beta1p5 | oracle | 0.0000 | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 2.8900 | 0.1331 | results/cloudgpt/E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_beta1p5.npz |

## Prompted LLM c19 K20 s5

| model | algorithm | final_mean | final_std | median | iqr | per_round | welfare_mean | welfare_std | source |
|---|---|---|---|---|---|---|---|---|---|
| DeepSeek-V3.2 | llm_greedy | 14.0200 | 14.6643 | 13.0000 | [0.1000, 17.0000] | 0.7010 | 2.1590 | 0.7183 | results/cloudgpt/E2_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz |
| DeepSeek-V3.2 | llm_belief | 3.0740 | 2.2308 | 1.6800 | [1.5900, 5.2400] | 0.1537 | 2.7363 | 0.3074 | results/cloudgpt/E2_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz |
| gpt-5.4-nano | llm_greedy | 17.4060 | 17.8188 | 11.6000 | [8.4300, 14.6000] | 0.8703 | 1.8857 | 0.8546 | results/cloudgpt/E2_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5.npz |
| gpt-5.4-nano | llm_belief | 7.1967 | 3.4749 | 4.5900 | [4.3200, 11.2506] | 0.3598 | 2.4542 | 0.4264 | results/cloudgpt/E2_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5.npz |
| Kimi-K2.6 | llm_greedy | 18.2700 | 7.6479 | 17.1800 | [13.9500, 19.5500] | 0.9135 | 1.8505 | 0.3764 | results/cloudgpt/E2_llm_baselines_Kimi_K2_6_c19_K20_s5.npz |
| Kimi-K2.6 | llm_belief | 11.7840 | 3.3336 | 10.4400 | [10.0300, 14.0700] | 0.5892 | 2.2248 | 0.3394 | results/cloudgpt/E2_llm_baselines_Kimi_K2_6_c19_K20_s5.npz |
| Llama-4-Maverick | llm_greedy | 5.9600 | 8.5805 | 0.8200 | [0.0000, 6.5800] | 0.2980 | 2.5580 | 0.4407 | results/cloudgpt/E2_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5.npz |
| Llama-4-Maverick | llm_belief | 10.3560 | 3.8194 | 10.1400 | [6.5800, 12.1900] | 0.5178 | 2.3522 | 0.3609 | results/cloudgpt/E2_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5.npz |

## External LLM Merged c19 K20 s5

| model_slug | algorithm | final_mean | final_std | median | iqr | per_round | welfare_mean | welfare_std | source |
|---|---|---|---|---|---|---|---|---|---|
| DeepSeek_V3_2 | atom_tom0 | 6.0000 | 7.4565 | 0.0000 | [0.0000, 13.0000] | 0.3000 | 2.5900 | 0.4620 | results/cloudgpt/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz |
| DeepSeek_V3_2 | atom_tom1 | 16.6760 | 8.2004 | 17.5100 | [16.4000, 17.6500] | 0.8338 | 2.0182 | 0.5421 | results/cloudgpt/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz |
| DeepSeek_V3_2 | atom_tom2 | 13.4020 | 10.3200 | 13.4800 | [3.1100, 17.3000] | 0.6701 | 2.2139 | 0.6402 | results/cloudgpt/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz |
| DeepSeek_V3_2 | atom_adaptive_ftl | 14.9440 | 1.4313 | 15.1100 | [14.4200, 16.2000] | 0.7472 | 2.0968 | 0.1891 | results/cloudgpt/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz |
| DeepSeek_V3_2 | atom_adaptive_hedge | 4.7900 | 4.5089 | 1.8000 | [1.6700, 9.6800] | 0.2395 | 2.6605 | 0.4287 | results/cloudgpt/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz |
| DeepSeek_V3_2 | econ_bne | 3.9900 | 3.4136 | 3.0000 | [1.9400, 5.0100] | 0.1995 | 2.6105 | 0.2122 | results/cloudgpt/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz |
| gpt_5_4_nano_20260317 | atom_tom0 | 4.0800 | 4.9406 | 0.4000 | [0.0000, 8.4000] | 0.2040 | 2.5860 | 0.4298 | results/cloudgpt/E2_external_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5.npz |
| gpt_5_4_nano_20260317 | atom_tom1 | 13.4726 | 6.5896 | 14.7200 | [12.5932, 17.2700] | 0.6736 | 2.0444 | 0.5262 | results/cloudgpt/E2_external_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5.npz |
| gpt_5_4_nano_20260317 | atom_tom2 | 10.2000 | 8.8254 | 12.8000 | [0.8000, 13.0000] | 0.5100 | 2.2440 | 0.6539 | results/cloudgpt/E2_external_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5.npz |
| gpt_5_4_nano_20260317 | atom_adaptive_ftl | 14.8895 | 2.8454 | 16.7300 | [11.9239, 17.0045] | 0.7445 | 1.9995 | 0.1944 | results/cloudgpt/E2_external_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5.npz |
| gpt_5_4_nano_20260317 | atom_adaptive_hedge | 7.6530 | 4.9582 | 8.8311 | [1.8707, 12.2975] | 0.3826 | 2.4414 | 0.4505 | results/cloudgpt/E2_external_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5.npz |
| gpt_5_4_nano_20260317 | econ_bne | 14.8800 | 2.7527 | 14.6000 | [12.4000, 16.2000] | 0.7440 | 1.9480 | 0.2260 | results/cloudgpt/E2_external_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5.npz |
| Kimi_K2_6 | atom_tom0 | 10.6720 | 6.3559 | 8.9900 | [7.5800, 14.3900] | 0.5336 | 2.2564 | 0.4624 | results/cloudgpt/E2_external_llm_baselines_Kimi_K2_6_c19_K20_s5.npz |
| Kimi_K2_6 | atom_tom1 | 14.0480 | 6.9242 | 14.8100 | [11.5900, 16.9000] | 0.7024 | 2.0376 | 0.5258 | results/cloudgpt/E2_external_llm_baselines_Kimi_K2_6_c19_K20_s5.npz |
| Kimi_K2_6 | atom_tom2 | 10.5840 | 8.2186 | 13.1200 | [2.3400, 13.3600] | 0.5292 | 2.2848 | 0.5743 | results/cloudgpt/E2_external_llm_baselines_Kimi_K2_6_c19_K20_s5.npz |
| Kimi_K2_6 | atom_adaptive_ftl | 14.2800 | 2.7749 | 13.7900 | [12.5800, 16.9500] | 0.7140 | 2.0300 | 0.1919 | results/cloudgpt/E2_external_llm_baselines_Kimi_K2_6_c19_K20_s5.npz |
| Kimi_K2_6 | atom_adaptive_hedge | 7.4840 | 4.0956 | 8.1900 | [3.1200, 9.3200] | 0.3742 | 2.4498 | 0.5145 | results/cloudgpt/E2_external_llm_baselines_Kimi_K2_6_c19_K20_s5.npz |
| Kimi_K2_6 | econ_bne | 10.4880 | 6.0321 | 6.7300 | [6.6900, 15.1900] | 0.5244 | 2.1676 | 0.3910 | results/cloudgpt/E2_external_llm_baselines_Kimi_K2_6_c19_K20_s5.npz |
| Llama_4_Maverick_17B_128E_Instruct_FP8 | atom_tom0 | 7.2400 | 7.7886 | 3.0000 | [1.0000, 11.8000] | 0.3620 | 2.5240 | 0.3758 | results/cloudgpt/E2_external_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5.npz |
| Llama_4_Maverick_17B_128E_Instruct_FP8 | atom_tom1 | 15.7100 | 7.9321 | 16.3100 | [15.4600, 16.4600] | 0.7855 | 2.0825 | 0.5337 | results/cloudgpt/E2_external_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5.npz |
| Llama_4_Maverick_17B_128E_Instruct_FP8 | atom_tom2 | 11.8660 | 9.3250 | 12.6800 | [4.7900, 12.9200] | 0.5933 | 2.2507 | 0.6101 | results/cloudgpt/E2_external_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5.npz |
| Llama_4_Maverick_17B_128E_Instruct_FP8 | atom_adaptive_ftl | 13.9220 | 2.6571 | 13.9900 | [11.6000, 16.0200] | 0.6961 | 2.0659 | 0.1190 | results/cloudgpt/E2_external_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5.npz |
| Llama_4_Maverick_17B_128E_Instruct_FP8 | atom_adaptive_hedge | 7.0060 | 4.5831 | 7.9100 | [2.7500, 10.8100] | 0.3503 | 2.5237 | 0.4524 | results/cloudgpt/E2_external_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5.npz |
| Llama_4_Maverick_17B_128E_Instruct_FP8 | econ_bne | 3.3820 | 4.5338 | 1.0000 | [0.0000, 3.9300] | 0.1691 | 2.6029 | 0.2177 | results/cloudgpt/E2_external_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5.npz |

## External LLM Solo Shards c19 K20 s5

| model | algorithm | final_mean | final_std | median | iqr | per_round | welfare_mean | welfare_std | source |
|---|---|---|---|---|---|---|---|---|---|
| gpt-5.4-nano | atom_tom0 | 4.0800 | 4.9406 | 0.4000 | [0.0000, 8.4000] | 0.2040 | 2.5860 | 0.4298 | results/cloudgpt/shards/E2_external_gpt_5_4_nano_20260317_c19_K20_s5_atom_tom0.npz |
| gpt-5.4-nano | atom_tom1 | 13.4726 | 6.5896 | 14.7200 | [12.5932, 17.2700] | 0.6736 | 2.0444 | 0.5262 | results/cloudgpt/shards/E2_external_gpt_5_4_nano_20260317_c19_K20_s5_atom_tom1.npz |
| gpt-5.4-nano | atom_tom2 | 10.2000 | 8.8254 | 12.8000 | [0.8000, 13.0000] | 0.5100 | 2.2440 | 0.6539 | results/cloudgpt/shards/E2_external_gpt_5_4_nano_20260317_c19_K20_s5_atom_tom2.npz |
| gpt-5.4-nano | atom_adaptive_ftl | 14.8895 | 2.8454 | 16.7300 | [11.9239, 17.0045] | 0.7445 | 1.9995 | 0.1944 | results/cloudgpt/shards/E2_external_gpt_5_4_nano_20260317_c19_K20_s5_atom_adaptive_ftl.npz |
| gpt-5.4-nano | atom_adaptive_hedge | 7.6530 | 4.9582 | 8.8311 | [1.8707, 12.2975] | 0.3826 | 2.4414 | 0.4505 | results/cloudgpt/shards/E2_external_gpt_5_4_nano_20260317_c19_K20_s5_atom_adaptive_hedge.npz |
| gpt-5.4-nano | econ_bne | 14.8800 | 2.7527 | 14.6000 | [12.4000, 16.2000] | 0.7440 | 1.9480 | 0.2260 | results/cloudgpt/shards/E2_external_gpt_5_4_nano_20260317_c19_K20_s5_econ_bne.npz |
| Kimi-K2.6 | atom_tom0 | 10.6720 | 6.3559 | 8.9900 | [7.5800, 14.3900] | 0.5336 | 2.2564 | 0.4624 | results/cloudgpt/shards/E2_external_Kimi_K2_6_c19_K20_s5_atom_tom0.npz |
| Kimi-K2.6 | atom_tom1 | 14.0480 | 6.9242 | 14.8100 | [11.5900, 16.9000] | 0.7024 | 2.0376 | 0.5258 | results/cloudgpt/shards/E2_external_Kimi_K2_6_c19_K20_s5_atom_tom1.npz |
| Kimi-K2.6 | atom_tom2 | 10.5840 | 8.2186 | 13.1200 | [2.3400, 13.3600] | 0.5292 | 2.2848 | 0.5743 | results/cloudgpt/shards/E2_external_Kimi_K2_6_c19_K20_s5_atom_tom2.npz |
| Kimi-K2.6 | atom_adaptive_ftl | 14.2800 | 2.7749 | 13.7900 | [12.5800, 16.9500] | 0.7140 | 2.0300 | 0.1919 | results/cloudgpt/shards/E2_external_Kimi_K2_6_c19_K20_s5_atom_adaptive_ftl.npz |
| Kimi-K2.6 | atom_adaptive_hedge | 7.4840 | 4.0956 | 8.1900 | [3.1200, 9.3200] | 0.3742 | 2.4498 | 0.5145 | results/cloudgpt/shards/E2_external_Kimi_K2_6_c19_K20_s5_atom_adaptive_hedge.npz |
| Kimi-K2.6 | econ_bne | 10.4880 | 6.0321 | 6.7300 | [6.6900, 15.1900] | 0.5244 | 2.1676 | 0.3910 | results/cloudgpt/shards/E2_external_Kimi_K2_6_c19_K20_s5_econ_bne.npz |
| Llama-4-Maverick | atom_tom0 | 7.2400 | 7.7886 | 3.0000 | [1.0000, 11.8000] | 0.3620 | 2.5240 | 0.3758 | results/cloudgpt/shards/E2_external_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5_atom_tom0.npz |
| Llama-4-Maverick | atom_tom1 | 15.7100 | 7.9321 | 16.3100 | [15.4600, 16.4600] | 0.7855 | 2.0825 | 0.5337 | results/cloudgpt/shards/E2_external_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5_atom_tom1.npz |
| Llama-4-Maverick | atom_tom2 | 11.8660 | 9.3250 | 12.6800 | [4.7900, 12.9200] | 0.5933 | 2.2507 | 0.6101 | results/cloudgpt/shards/E2_external_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5_atom_tom2.npz |
| Llama-4-Maverick | atom_adaptive_ftl | 13.9220 | 2.6571 | 13.9900 | [11.6000, 16.0200] | 0.6961 | 2.0659 | 0.1190 | results/cloudgpt/shards/E2_external_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5_atom_adaptive_ftl.npz |
| Llama-4-Maverick | atom_adaptive_hedge | 7.0060 | 4.5831 | 7.9100 | [2.7500, 10.8100] | 0.3503 | 2.5237 | 0.4524 | results/cloudgpt/shards/E2_external_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5_atom_adaptive_hedge.npz |
| Llama-4-Maverick | econ_bne | 3.3820 | 4.5338 | 1.0000 | [0.0000, 3.9300] | 0.1691 | 2.6029 | 0.2177 | results/cloudgpt/shards/E2_external_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5_econ_bne.npz |

## Fixed Beta0p25 hpsmg_plus vs Best Available Non-Oracle Baseline

| model | hpsmg_plus_mean | hpsmg_plus_std | best_baseline | best_baseline_mean | best_baseline_std | margin | status |
|---|---|---|---|---|---|---|---|
| DeepSeek-V3.2 | 0.4000 | 0.8000 | map_greedy | 0.7120 | 0.4663 | 0.3120 | PASS |
| gpt-5.4-nano | 0.9120 | 0.2919 | hpsmg | 0.6440 | 0.6310 | -0.2680 | VIOLATION |
| Kimi-K2.6 | 0.7040 | 0.4351 | hpsmg | 0.6320 | 0.6091 | -0.0720 | VIOLATION |
| Llama-4-Maverick | 0.3120 | 0.6240 | hpsmg | 0.7320 | 0.6086 | 0.4200 | PASS |

## E1 LLM Posterior Concentration

| backbone | seeds | K | mean_concentration_time | final_true_mass_mean | seed_times | source |
|---|---|---|---|---|---|---|
| DeepSeek_V3_2_live | 5 | 20 | 4.4000 | 0.9910 | 4,4,5,7,2 | results\e1_e4_llm\E1_posterior_DeepSeek_V3_2_live.npz |
| Kimi_K2_6_live | 5 | 20 | 12.0000 | 0.8566 | 3,12,null,null,3 | results\e1_e4_llm\E1_posterior_Kimi_K2_6_live.npz |
| Llama_4_Maverick_17B_128E_Instruct_FP8_live | 5 | 20 | 14.0000 | 0.9873 | 12,14,13,16,15 | results\e1_e4_llm\E1_posterior_Llama_4_Maverick_17B_128E_Instruct_FP8_live.npz |
| gpt_5_4_nano_20260317_live | 5 | 20 | 6.6000 | 0.9668 | 5,null,2,3,2 | results\e1_e4_llm\E1_posterior_gpt_5_4_nano_20260317_live.npz |

## E2 LLM Type-Count Scaling

| type_count | algorithm | mean_final_cumulative_regret | sem | seeds | source |
|---|---|---|---|---|---|
| 2 | hpsmg | 0.1980 | 0.1346 | 5 | results\e1_e4_llm\E2_type2_live.npz |
| 2 | hpsmg_plus | 0.0620 | 0.0620 | 5 | results\e1_e4_llm\E2_type2_live.npz |
| 3 | hpsmg | 0.6320 | 0.4938 | 5 | results\e1_e4_llm\E2_type3_live.npz |
| 3 | hpsmg_plus | 0.0000 | 0.0000 | 5 | results\e1_e4_llm\E2_type3_live.npz |
| 4 | hpsmg | 0.2320 | 0.1421 | 5 | results\e1_e4_llm\E2_type4_live.npz |
| 4 | hpsmg_plus | 0.0000 | 0.0000 | 5 | results\e1_e4_llm\E2_type4_live.npz |
| 5 | hpsmg | 0.9200 | 0.0892 | 5 | results\e1_e4_llm\E2_type5_live.npz |
| 5 | hpsmg_plus | 1.0960 | 0.5779 | 5 | results\e1_e4_llm\E2_type5_live.npz |
| 6 | hpsmg | 1.2800 | 0.2716 | 5 | results\e1_e4_llm\E2_type6_live.npz |
| 6 | hpsmg_plus | 0.2000 | 0.0819 | 5 | results\e1_e4_llm\E2_type6_live.npz |

## E2 LLM Type-Count Scaling 10-Seed Confirmation

| type_count | algorithm | mean_final_cumulative_regret | sem | seeds | source |
|---|---|---|---|---|---|
| 2 | hpsmg | 0.4530 | 0.2060 | 10 | results\e1_e4_llm\E2_type2_live_s10.npz |
| 2 | hpsmg_plus | 0.0930 | 0.0474 | 10 | results\e1_e4_llm\E2_type2_live_s10.npz |
| 3 | hpsmg | 0.3800 | 0.2547 | 10 | results\e1_e4_llm\E2_type3_live_s10.npz |
| 3 | hpsmg_plus | 0.0000 | 0.0000 | 10 | results\e1_e4_llm\E2_type3_live_s10.npz |
| 4 | hpsmg | 0.1160 | 0.0773 | 10 | results\e1_e4_llm\E2_type4_live_s10.npz |
| 4 | hpsmg_plus | 0.0000 | 0.0000 | 10 | results\e1_e4_llm\E2_type4_live_s10.npz |
| 5 | hpsmg | 0.9100 | 0.1100 | 10 | results\e1_e4_llm\E2_type5_live_s10.npz |
| 5 | hpsmg_plus | 0.7720 | 0.3215 | 10 | results\e1_e4_llm\E2_type5_live_s10.npz |
| 6 | hpsmg | 1.2920 | 0.2331 | 10 | results\e1_e4_llm\E2_type6_live_s10.npz |
| 6 | hpsmg_plus | 0.3390 | 0.1904 | 10 | results\e1_e4_llm\E2_type6_live_s10.npz |

## E3 LLM N-Agent Scaling

| n | algorithm | storage_entries | mean_final_cumulative_regret | sem | seeds | source |
|---|---|---|---|---|---|---|
| 2 | hpsmg | 8 | 0.1400 | 0.0620 | 5 | results\e1_e4_llm\E3_n2_live.npz |
| 2 | hpsmg_plus | 8 | 2.6880 | 0.8996 | 5 | results\e1_e4_llm\E3_n2_live.npz |
| 2 | joint_psrl | 16 | 0.4220 | 0.2656 | 5 | results\e1_e4_llm\E3_n2_live.npz |
| 3 | hpsmg | 12 | 0.2320 | 0.1421 | 5 | results\e1_e4_llm\E3_n3_live.npz |
| 3 | hpsmg_plus | 12 | 0.0000 | 0.0000 | 5 | results\e1_e4_llm\E3_n3_live.npz |
| 3 | joint_psrl | 64 | 0.3480 | 0.2320 | 5 | results\e1_e4_llm\E3_n3_live.npz |
| 4 | hpsmg | 16 | 0.1080 | 0.1080 | 5 | results\e1_e4_llm\E3_n4_live.npz |
| 4 | hpsmg_plus | 16 | 0.0000 | 0.0000 | 5 | results\e1_e4_llm\E3_n4_live.npz |
| 4 | joint_psrl | 256 | 0.2160 | 0.2160 | 5 | results\e1_e4_llm\E3_n4_live.npz |
| 5 | hpsmg | 20 | 0.8700 | 0.5878 | 5 | results\e1_e4_llm\E3_n5_live.npz |
| 5 | hpsmg_plus | 20 | 0.2780 | 0.2780 | 5 | results\e1_e4_llm\E3_n5_live.npz |
| 5 | joint_psrl | 1024 | 1.2520 | 0.6479 | 5 | results\e1_e4_llm\E3_n5_live.npz |

## E3 LLM N-Agent Scaling 10-Seed Confirmation

| n | algorithm | storage_entries | mean_final_cumulative_regret | sem | seeds | source |
|---|---|---|---|---|---|---|
| 2 | hpsmg | 8 | 0.0700 | 0.0374 | 10 | results\e1_e4_llm\E3_n2_live_s10.npz |
| 2 | hpsmg_plus | 8 | 2.9620 | 0.5446 | 10 | results\e1_e4_llm\E3_n2_live_s10.npz |
| 2 | joint_psrl | 16 | 0.2750 | 0.1395 | 10 | results\e1_e4_llm\E3_n2_live_s10.npz |
| 3 | hpsmg | 12 | 0.1160 | 0.0773 | 10 | results\e1_e4_llm\E3_n3_live_s10.npz |
| 3 | hpsmg_plus | 12 | 0.0000 | 0.0000 | 10 | results\e1_e4_llm\E3_n3_live_s10.npz |
| 3 | joint_psrl | 64 | 0.1740 | 0.1238 | 10 | results\e1_e4_llm\E3_n3_live_s10.npz |
| 4 | hpsmg | 16 | 0.0540 | 0.0540 | 10 | results\e1_e4_llm\E3_n4_live_s10.npz |
| 4 | hpsmg_plus | 16 | 0.0000 | 0.0000 | 10 | results\e1_e4_llm\E3_n4_live_s10.npz |
| 4 | joint_psrl | 256 | 0.1080 | 0.1080 | 10 | results\e1_e4_llm\E3_n4_live_s10.npz |
| 5 | hpsmg | 20 | 0.5960 | 0.3289 | 10 | results\e1_e4_llm\E3_n5_live_s10.npz |
| 5 | hpsmg_plus | 20 | 0.1390 | 0.1390 | 10 | results\e1_e4_llm\E3_n5_live_s10.npz |
| 5 | joint_psrl | 1024 | 0.6260 | 0.3699 | 10 | results\e1_e4_llm\E3_n5_live_s10.npz |

## E4 LLM Prior Recovery

| prior_mode | algorithm | mean_final_cumulative_regret | sem | seeds | K | source |
|---|---|---|---|---|---|---|
| adversarial | hpsmg | 1.4340 | 0.2562 | 5 | 20 | results\e1_e4_llm\E4_prior_adversarial_DeepSeek_V3_2_live.npz |
| adversarial | map_greedy | 1.6100 | 0.3730 | 5 | 20 | results\e1_e4_llm\E4_prior_adversarial_DeepSeek_V3_2_live.npz |
| correct | hpsmg | 0.7860 | 0.1906 | 5 | 20 | results\e1_e4_llm\E4_prior_correct_DeepSeek_V3_2_live.npz |
| correct | map_greedy | 0.0000 | 0.0000 | 5 | 20 | results\e1_e4_llm\E4_prior_correct_DeepSeek_V3_2_live.npz |
| uniform | hpsmg | 1.2860 | 0.2955 | 5 | 20 | results\e1_e4_llm\E4_prior_uniform_DeepSeek_V3_2_live.npz |
| uniform | map_greedy | 0.9000 | 0.2080 | 5 | 20 | results\e1_e4_llm\E4_prior_uniform_DeepSeek_V3_2_live.npz |

## Concordia Compact Pub Coordination Live s5

| config | model | method | episodes | focal_score_mean | focal_score_min_mean | coordination_rate_mean | valid_action_rate_mean | source |
|---|---|---|---|---|---|---|---|---|
| capetown | none | oracle_joint | 100 | 1.2651 | 0.9508 | 0.9767 | 1.0000 | analysis/concordia_pub_coordination_compact_capetown_mechanistic_joint_s100.json |
| capetown | none | hpsmg_plus_joint_proxy | 100 | 1.2483 | 0.9550 | 0.9900 | 1.0000 | analysis/concordia_pub_coordination_compact_capetown_mechanistic_joint_s100.json |
| capetown | none | econ_bne_mech | 100 | 1.0423 | 0.7168 | 0.7233 | 1.0000 | analysis/concordia_pub_coordination_compact_capetown_mechanistic_joint_s100.json |
| capetown | none | atom_tom1_mech | 100 | 0.9830 | 0.5612 | 0.6750 | 1.0000 | analysis/concordia_pub_coordination_compact_capetown_mechanistic_joint_s100.json |
| capetown | none | hpsmg_plus_proxy | 100 | 0.9830 | 0.5612 | 0.6750 | 1.0000 | analysis/concordia_pub_coordination_compact_capetown_mechanistic_joint_s100.json |
| capetown | none | oracle_joint | 30 | 1.2759 | 0.9833 | 0.9944 | 1.0000 | analysis/concordia_pub_coordination_compact_capetown_mechanistic_joint_s30.json |
| capetown | none | hpsmg_plus_joint_proxy | 30 | 1.2472 | 0.9833 | 1.0000 | 1.0000 | analysis/concordia_pub_coordination_compact_capetown_mechanistic_joint_s30.json |
| capetown | none | econ_bne_mech | 30 | 1.0439 | 0.7511 | 0.7278 | 1.0000 | analysis/concordia_pub_coordination_compact_capetown_mechanistic_joint_s30.json |
| capetown | none | atom_tom1_mech | 30 | 0.9650 | 0.5811 | 0.6500 | 1.0000 | analysis/concordia_pub_coordination_compact_capetown_mechanistic_joint_s30.json |
| capetown | none | hpsmg_plus_proxy | 30 | 0.9650 | 0.5811 | 0.6500 | 1.0000 | analysis/concordia_pub_coordination_compact_capetown_mechanistic_joint_s30.json |
| london_mini | DeepSeek-V3.2 | oracle_joint | 5 | 1.3000 | 1.1000 | 1.0000 | 1.0000 | analysis/concordia_pub_coordination_compact_DeepSeek_V3_2_live_s5.json |
| london_mini | DeepSeek-V3.2 | hpsmg_plus_proxy | 5 | 1.1083 | 0.9500 | 0.8000 | 1.0000 | analysis/concordia_pub_coordination_compact_DeepSeek_V3_2_live_s5.json |
| london_mini | DeepSeek-V3.2 | atom_tom1 | 5 | 0.8250 | 0.6500 | 0.6000 | 1.0000 | analysis/concordia_pub_coordination_compact_DeepSeek_V3_2_live_s5.json |
| london_mini | DeepSeek-V3.2 | econ_bne | 5 | 0.8250 | 0.6500 | 0.6000 | 1.0000 | analysis/concordia_pub_coordination_compact_DeepSeek_V3_2_live_s5.json |
| london_mini | DeepSeek-V3.2 | llm_belief | 5 | 0.8250 | 0.6500 | 0.6000 | 1.0000 | analysis/concordia_pub_coordination_compact_DeepSeek_V3_2_live_s5.json |
| london_mini | DeepSeek-V3.2 | llm_greedy | 5 | 0.8250 | 0.6500 | 0.6000 | 1.0000 | analysis/concordia_pub_coordination_compact_DeepSeek_V3_2_live_s5.json |
| edinburgh_closures | none | oracle_joint | 30 | 1.2257 | 0.9444 | 0.9833 | 1.0000 | analysis/concordia_pub_coordination_compact_edinburgh_closures_mechanistic_joint_s30.json |
| edinburgh_closures | none | hpsmg_plus_joint_proxy | 30 | 1.2083 | 0.9500 | 1.0000 | 1.0000 | analysis/concordia_pub_coordination_compact_edinburgh_closures_mechanistic_joint_s30.json |
| edinburgh_closures | none | econ_bne_mech | 30 | 1.0865 | 0.7562 | 0.8889 | 1.0000 | analysis/concordia_pub_coordination_compact_edinburgh_closures_mechanistic_joint_s30.json |
| edinburgh_closures | none | hpsmg_plus_proxy | 30 | 1.0552 | 0.6111 | 0.8167 | 1.0000 | analysis/concordia_pub_coordination_compact_edinburgh_closures_mechanistic_joint_s30.json |
| edinburgh_closures | none | atom_tom1_mech | 30 | 1.0132 | 0.5322 | 0.8333 | 1.0000 | analysis/concordia_pub_coordination_compact_edinburgh_closures_mechanistic_joint_s30.json |
| edinburgh | none | atom_tom1_mech | 30 | 1.2700 | 0.9500 | 1.0000 | 1.0000 | analysis/concordia_pub_coordination_compact_edinburgh_mechanistic_joint_s30.json |
| edinburgh | none | econ_bne_mech | 30 | 1.2700 | 0.9500 | 1.0000 | 1.0000 | analysis/concordia_pub_coordination_compact_edinburgh_mechanistic_joint_s30.json |
| edinburgh | none | hpsmg_plus_joint_proxy | 30 | 1.2700 | 0.9500 | 1.0000 | 1.0000 | analysis/concordia_pub_coordination_compact_edinburgh_mechanistic_joint_s30.json |
| edinburgh | none | hpsmg_plus_proxy | 30 | 1.2700 | 0.9500 | 1.0000 | 1.0000 | analysis/concordia_pub_coordination_compact_edinburgh_mechanistic_joint_s30.json |
| edinburgh | none | oracle_joint | 30 | 1.2700 | 0.9500 | 0.9933 | 1.0000 | analysis/concordia_pub_coordination_compact_edinburgh_mechanistic_joint_s30.json |
| edinburgh_tough_friendship | none | atom_tom1_mech | 30 | 1.2533 | 1.0000 | 1.0000 | 1.0000 | analysis/concordia_pub_coordination_compact_edinburgh_tough_friendship_mechanistic_joint_s30.json |
| edinburgh_tough_friendship | none | econ_bne_mech | 30 | 1.2533 | 1.0000 | 1.0000 | 1.0000 | analysis/concordia_pub_coordination_compact_edinburgh_tough_friendship_mechanistic_joint_s30.json |
| edinburgh_tough_friendship | none | hpsmg_plus_joint_proxy | 30 | 1.2533 | 1.0000 | 1.0000 | 1.0000 | analysis/concordia_pub_coordination_compact_edinburgh_tough_friendship_mechanistic_joint_s30.json |
| edinburgh_tough_friendship | none | hpsmg_plus_proxy | 30 | 1.2533 | 1.0000 | 1.0000 | 1.0000 | analysis/concordia_pub_coordination_compact_edinburgh_tough_friendship_mechanistic_joint_s30.json |
| edinburgh_tough_friendship | none | oracle_joint | 30 | 1.2533 | 1.0000 | 1.0000 | 1.0000 | analysis/concordia_pub_coordination_compact_edinburgh_tough_friendship_mechanistic_joint_s30.json |
| london_mini | gpt-5.4-nano-20260317 | hpsmg_plus_joint_proxy | 5 | 1.3000 | 1.1000 | 1.0000 | 1.0000 | analysis/concordia_pub_coordination_compact_gpt_5_4_nano_20260317_live_s5.json |
| london_mini | gpt-5.4-nano-20260317 | oracle_joint | 5 | 1.3000 | 1.1000 | 1.0000 | 1.0000 | analysis/concordia_pub_coordination_compact_gpt_5_4_nano_20260317_live_s5.json |
| london_mini | gpt-5.4-nano-20260317 | econ_bne | 5 | 1.1250 | 0.9000 | 0.8000 | 1.0000 | analysis/concordia_pub_coordination_compact_gpt_5_4_nano_20260317_live_s5.json |
| london_mini | gpt-5.4-nano-20260317 | atom_tom1_mech | 5 | 1.1083 | 0.9500 | 0.8000 | 1.0000 | analysis/concordia_pub_coordination_compact_gpt_5_4_nano_20260317_live_s5.json |
| london_mini | gpt-5.4-nano-20260317 | econ_bne_mech | 5 | 1.1083 | 0.9500 | 0.8000 | 1.0000 | analysis/concordia_pub_coordination_compact_gpt_5_4_nano_20260317_live_s5.json |
| london_mini | gpt-5.4-nano-20260317 | hpsmg_plus_proxy | 5 | 1.1083 | 0.9500 | 0.8000 | 1.0000 | analysis/concordia_pub_coordination_compact_gpt_5_4_nano_20260317_live_s5.json |
| london_mini | gpt-5.4-nano-20260317 | llm_greedy | 5 | 1.0500 | 0.8000 | 0.9000 | 1.0000 | analysis/concordia_pub_coordination_compact_gpt_5_4_nano_20260317_live_s5.json |
| london_mini | gpt-5.4-nano-20260317 | atom_tom1 | 5 | 1.0083 | 0.7500 | 0.7000 | 1.0000 | analysis/concordia_pub_coordination_compact_gpt_5_4_nano_20260317_live_s5.json |
| london_mini | gpt-5.4-nano-20260317 | llm_belief | 5 | 1.0083 | 0.7500 | 0.7000 | 1.0000 | analysis/concordia_pub_coordination_compact_gpt_5_4_nano_20260317_live_s5.json |
| london_mini | Llama-4-Maverick-17B-128E-Instruct-FP8 | hpsmg_plus_joint_proxy | 5 | 1.3000 | 1.1000 | 1.0000 | 1.0000 | analysis/concordia_pub_coordination_compact_Llama_4_Maverick_17B_128E_Instruct_FP8_live_s5.json |
| london_mini | Llama-4-Maverick-17B-128E-Instruct-FP8 | oracle_joint | 5 | 1.3000 | 1.1000 | 1.0000 | 1.0000 | analysis/concordia_pub_coordination_compact_Llama_4_Maverick_17B_128E_Instruct_FP8_live_s5.json |
| london_mini | Llama-4-Maverick-17B-128E-Instruct-FP8 | atom_tom1_mech | 5 | 1.1083 | 0.9500 | 0.8000 | 1.0000 | analysis/concordia_pub_coordination_compact_Llama_4_Maverick_17B_128E_Instruct_FP8_live_s5.json |
| london_mini | Llama-4-Maverick-17B-128E-Instruct-FP8 | econ_bne_mech | 5 | 1.1083 | 0.9500 | 0.8000 | 1.0000 | analysis/concordia_pub_coordination_compact_Llama_4_Maverick_17B_128E_Instruct_FP8_live_s5.json |
| london_mini | Llama-4-Maverick-17B-128E-Instruct-FP8 | hpsmg_plus_proxy | 5 | 1.1083 | 0.9500 | 0.8000 | 1.0000 | analysis/concordia_pub_coordination_compact_Llama_4_Maverick_17B_128E_Instruct_FP8_live_s5.json |
| london_mini | Llama-4-Maverick-17B-128E-Instruct-FP8 | atom_tom1 | 5 | 0.8250 | 0.6500 | 0.6000 | 1.0000 | analysis/concordia_pub_coordination_compact_Llama_4_Maverick_17B_128E_Instruct_FP8_live_s5.json |
| london_mini | Llama-4-Maverick-17B-128E-Instruct-FP8 | econ_bne | 5 | 0.8250 | 0.6500 | 0.6000 | 1.0000 | analysis/concordia_pub_coordination_compact_Llama_4_Maverick_17B_128E_Instruct_FP8_live_s5.json |
| london_mini | Llama-4-Maverick-17B-128E-Instruct-FP8 | llm_belief | 5 | 0.8250 | 0.6500 | 0.6000 | 1.0000 | analysis/concordia_pub_coordination_compact_Llama_4_Maverick_17B_128E_Instruct_FP8_live_s5.json |
| london_mini | Llama-4-Maverick-17B-128E-Instruct-FP8 | llm_greedy | 5 | 0.8250 | 0.6500 | 0.6000 | 1.0000 | analysis/concordia_pub_coordination_compact_Llama_4_Maverick_17B_128E_Instruct_FP8_live_s5.json |
| london_closures | none | oracle_joint | 30 | 1.2750 | 1.0167 | 1.0000 | 1.0000 | analysis/concordia_pub_coordination_compact_london_closures_mechanistic_joint_s30.json |
| london_closures | none | hpsmg_plus_joint_proxy | 30 | 1.2667 | 1.0167 | 1.0000 | 1.0000 | analysis/concordia_pub_coordination_compact_london_closures_mechanistic_joint_s30.json |
| london_closures | none | econ_bne_mech | 30 | 1.2349 | 0.9889 | 0.9417 | 1.0000 | analysis/concordia_pub_coordination_compact_london_closures_mechanistic_joint_s30.json |
| london_closures | none | atom_tom1_mech | 30 | 1.2242 | 0.9656 | 0.9500 | 1.0000 | analysis/concordia_pub_coordination_compact_london_closures_mechanistic_joint_s30.json |
| london_closures | none | hpsmg_plus_proxy | 30 | 1.2242 | 0.9656 | 0.9500 | 1.0000 | analysis/concordia_pub_coordination_compact_london_closures_mechanistic_joint_s30.json |
| london | none | oracle_joint | 30 | 1.3354 | 1.0333 | 0.9917 | 1.0000 | analysis/concordia_pub_coordination_compact_london_mechanistic_joint_s30.json |
| london | none | hpsmg_plus_joint_proxy | 30 | 1.3167 | 1.0333 | 1.0000 | 1.0000 | analysis/concordia_pub_coordination_compact_london_mechanistic_joint_s30.json |
| london | none | econ_bne_mech | 30 | 1.2017 | 0.9550 | 0.8167 | 1.0000 | analysis/concordia_pub_coordination_compact_london_mechanistic_joint_s30.json |
| london | none | atom_tom1_mech | 30 | 1.1537 | 0.8450 | 0.8000 | 1.0000 | analysis/concordia_pub_coordination_compact_london_mechanistic_joint_s30.json |
| london | none | hpsmg_plus_proxy | 30 | 1.1537 | 0.8450 | 0.8000 | 1.0000 | analysis/concordia_pub_coordination_compact_london_mechanistic_joint_s30.json |
| london_mini | none | oracle_joint | 30 | 1.3167 | 1.1333 | 0.9500 | 1.0000 | analysis/concordia_pub_coordination_compact_london_mini_mechanistic_joint_s30.json |
| london_mini | none | hpsmg_plus_joint_proxy | 30 | 1.3083 | 1.1167 | 0.9667 | 1.0000 | analysis/concordia_pub_coordination_compact_london_mini_mechanistic_joint_s30.json |
| london_mini | none | econ_bne_mech | 30 | 1.0764 | 0.9417 | 0.8333 | 1.0000 | analysis/concordia_pub_coordination_compact_london_mini_mechanistic_joint_s30.json |
| london_mini | none | atom_tom1_mech | 30 | 1.0639 | 0.9056 | 0.8500 | 1.0000 | analysis/concordia_pub_coordination_compact_london_mini_mechanistic_joint_s30.json |
| london_mini | none | hpsmg_plus_proxy | 30 | 1.0639 | 0.9056 | 0.8500 | 1.0000 | analysis/concordia_pub_coordination_compact_london_mini_mechanistic_joint_s30.json |
| london_mini | none | hpsmg_plus_joint_proxy | 5 | 1.3000 | 1.1000 | 1.0000 | 1.0000 | analysis/concordia_pub_coordination_compact_mechanistic_joint_s5.json |
| london_mini | none | oracle_joint | 5 | 1.3000 | 1.1000 | 1.0000 | 1.0000 | analysis/concordia_pub_coordination_compact_mechanistic_joint_s5.json |
| london_mini | none | atom_tom1_mech | 5 | 1.1083 | 0.9500 | 0.8000 | 1.0000 | analysis/concordia_pub_coordination_compact_mechanistic_joint_s5.json |
| london_mini | none | econ_bne_mech | 5 | 1.1083 | 0.9500 | 0.8000 | 1.0000 | analysis/concordia_pub_coordination_compact_mechanistic_joint_s5.json |
| london_mini | none | hpsmg_plus_proxy | 5 | 1.1083 | 0.9500 | 0.8000 | 1.0000 | analysis/concordia_pub_coordination_compact_mechanistic_joint_s5.json |

## Concordia Compact Haggling

| domain | config | method | episodes | focal_score_mean | focal_score_min_mean | deal_score_mean | deal_min_score_mean | agreement_rate_mean | nash_product_mean | valid_action_rate_mean | source |
|---|---|---|---|---|---|---|---|---|---|---|---|
| haggling | fruitville_gullible | econ_bne_mech | 30 | 7.4000 | 7.4000 | 5.0000 | 2.0000 | 1.0000 | 6.0000 | 1.0000 | analysis/concordia_haggling_compact_fruitville_gullible_s30.json |
| haggling | fruitville_gullible | hpsmg_plus_joint_proxy | 30 | 7.4000 | 7.4000 | 5.0000 | 2.0000 | 1.0000 | 6.0000 | 1.0000 | analysis/concordia_haggling_compact_fruitville_gullible_s30.json |
| haggling | fruitville_gullible | hpsmg_plus_proxy | 30 | 7.4000 | 7.4000 | 5.0000 | 2.0000 | 1.0000 | 6.0000 | 1.0000 | analysis/concordia_haggling_compact_fruitville_gullible_s30.json |
| haggling | fruitville_gullible | atom_tom1_mech | 30 | 7.0000 | 7.0000 | 5.0000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 | analysis/concordia_haggling_compact_fruitville_gullible_s30.json |
| haggling | fruitville_gullible | oracle_joint | 30 | 7.0000 | 7.0000 | 5.0000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 | analysis/concordia_haggling_compact_fruitville_gullible_s30.json |
| haggling | fruitville | hpsmg_plus_joint_proxy | 30 | 7.8222 | 6.7667 | 3.9111 | 1.6889 | 1.0000 | 3.8222 | 1.0000 | analysis/concordia_haggling_compact_fruitville_s30.json |
| haggling | fruitville | hpsmg_plus_proxy | 30 | 7.8222 | 6.7667 | 3.9111 | 1.6889 | 1.0000 | 3.8222 | 1.0000 | analysis/concordia_haggling_compact_fruitville_s30.json |
| haggling | fruitville | econ_bne_mech | 30 | 7.8222 | 6.1000 | 3.9111 | 1.4278 | 1.0000 | 3.5611 | 1.0000 | analysis/concordia_haggling_compact_fruitville_s30.json |
| haggling | fruitville | atom_tom1_mech | 30 | 7.8222 | 1.6000 | 3.9111 | 0.0000 | 1.0000 | 0.0000 | 1.0000 | analysis/concordia_haggling_compact_fruitville_s30.json |
| haggling | fruitville | oracle_joint | 30 | 7.8222 | 0.0000 | 3.9111 | -0.5722 | 1.0000 | 0.0000 | 1.0000 | analysis/concordia_haggling_compact_fruitville_s30.json |
| haggling | vegbrooke | hpsmg_plus_joint_proxy | 30 | 1.9833 | 0.9333 | 0.6611 | 0.1944 | 0.3917 | 0.2694 | 1.0000 | analysis/concordia_haggling_compact_vegbrooke_s30.json |
| haggling | vegbrooke | hpsmg_plus_proxy | 30 | 1.9833 | 0.9333 | 0.6611 | 0.1944 | 0.6750 | 0.2694 | 1.0000 | analysis/concordia_haggling_compact_vegbrooke_s30.json |
| haggling | vegbrooke | econ_bne_mech | 30 | 1.7333 | 0.4333 | 0.5778 | 0.1389 | 0.3833 | 0.2139 | 1.0000 | analysis/concordia_haggling_compact_vegbrooke_s30.json |
| haggling | vegbrooke | atom_tom1_mech | 30 | 1.9833 | 0.2667 | 0.6611 | 0.0000 | 0.6750 | 0.0000 | 1.0000 | analysis/concordia_haggling_compact_vegbrooke_s30.json |
| haggling | vegbrooke | oracle_joint | 30 | 1.9833 | -3.3667 | 0.6611 | -0.6833 | 0.3917 | 0.0000 | 1.0000 | analysis/concordia_haggling_compact_vegbrooke_s30.json |
| haggling | vegbrooke_strange_game | econ_bne_mech | 30 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | analysis/concordia_haggling_compact_vegbrooke_strange_game_s30.json |
| haggling | vegbrooke_strange_game | hpsmg_plus_joint_proxy | 30 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | analysis/concordia_haggling_compact_vegbrooke_strange_game_s30.json |
| haggling | vegbrooke_strange_game | hpsmg_plus_proxy | 30 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | analysis/concordia_haggling_compact_vegbrooke_strange_game_s30.json |
| haggling | vegbrooke_strange_game | oracle_joint | 30 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | analysis/concordia_haggling_compact_vegbrooke_strange_game_s30.json |
| haggling | vegbrooke_strange_game | atom_tom1_mech | 30 | -10.0000 | -17.6667 | -5.0000 | -5.0000 | 1.0000 | 0.0000 | 1.0000 | analysis/concordia_haggling_compact_vegbrooke_strange_game_s30.json |
| haggling | vegbrooke_stubborn | hpsmg_plus_joint_proxy | 30 | 1.1000 | 1.1000 | 0.5200 | 0.1333 | 0.3533 | 0.1667 | 1.0000 | analysis/concordia_haggling_compact_vegbrooke_stubborn_s30.json |
| haggling | vegbrooke_stubborn | hpsmg_plus_proxy | 30 | 1.1000 | 1.1000 | 0.5200 | 0.1333 | 0.6200 | 0.1667 | 1.0000 | analysis/concordia_haggling_compact_vegbrooke_stubborn_s30.json |
| haggling | vegbrooke_stubborn | econ_bne_mech | 30 | 0.9667 | 0.9667 | 0.4600 | 0.0667 | 0.3667 | 0.1000 | 1.0000 | analysis/concordia_haggling_compact_vegbrooke_stubborn_s30.json |
| haggling | vegbrooke_stubborn | atom_tom1_mech | 30 | 0.7667 | 0.7667 | 0.5200 | 0.0000 | 0.6200 | 0.0000 | 1.0000 | analysis/concordia_haggling_compact_vegbrooke_stubborn_s30.json |
| haggling | vegbrooke_stubborn | oracle_joint | 30 | -0.3333 | -0.3333 | 0.5200 | -0.5933 | 0.3533 | 0.0000 | 1.0000 | analysis/concordia_haggling_compact_vegbrooke_stubborn_s30.json |
| haggling_multi_item | cumulative_score | econ_bne_mech | 30 | 6.0000 | 6.0000 | 4.0000 | 2.0000 | 1.0000 | 4.0000 | 1.0000 | analysis/concordia_haggling_multi_item_compact_cumulative_score_s30.json |
| haggling_multi_item | cumulative_score | hpsmg_plus_joint_proxy | 30 | 6.0000 | 6.0000 | 4.0000 | 2.0000 | 1.0000 | 4.0000 | 1.0000 | analysis/concordia_haggling_multi_item_compact_cumulative_score_s30.json |
| haggling_multi_item | cumulative_score | hpsmg_plus_proxy | 30 | 6.0000 | 6.0000 | 4.0000 | 2.0000 | 1.0000 | 4.0000 | 1.0000 | analysis/concordia_haggling_multi_item_compact_cumulative_score_s30.json |
| haggling_multi_item | cumulative_score | atom_tom1_mech | 30 | 5.6000 | 5.6000 | 4.0000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 | analysis/concordia_haggling_multi_item_compact_cumulative_score_s30.json |
| haggling_multi_item | cumulative_score | oracle_joint | 30 | 5.6000 | 5.6000 | 4.0000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 | analysis/concordia_haggling_multi_item_compact_cumulative_score_s30.json |
| haggling_multi_item | fruitville_gullible | hpsmg_plus_joint_proxy | 30 | 6.7667 | 6.7667 | 4.5444 | 2.0000 | 1.0000 | 5.0889 | 1.0000 | analysis/concordia_haggling_multi_item_compact_fruitville_gullible_s30.json |
| haggling_multi_item | fruitville_gullible | hpsmg_plus_proxy | 30 | 6.7667 | 6.7667 | 4.5444 | 2.0000 | 1.0000 | 5.0889 | 1.0000 | analysis/concordia_haggling_multi_item_compact_fruitville_gullible_s30.json |
| haggling_multi_item | fruitville_gullible | econ_bne_mech | 30 | 6.7000 | 6.7000 | 4.5444 | 1.6889 | 1.0000 | 4.7778 | 1.0000 | analysis/concordia_haggling_multi_item_compact_fruitville_gullible_s30.json |
| haggling_multi_item | fruitville_gullible | oracle_joint | 30 | 6.3000 | 6.3000 | 4.5444 | -0.3111 | 1.0000 | 0.0000 | 1.0000 | analysis/concordia_haggling_multi_item_compact_fruitville_gullible_s30.json |
| haggling_multi_item | fruitville_gullible | atom_tom1_mech | 30 | 5.6667 | 5.6667 | 3.9667 | 0.0000 | 1.0000 | 0.0000 | 1.0000 | analysis/concordia_haggling_multi_item_compact_fruitville_gullible_s30.json |
| haggling_multi_item | fruitville_multi | hpsmg_plus_joint_proxy | 30 | 4.4000 | 3.9667 | 4.4000 | 1.9833 | 1.0000 | 4.8000 | 1.0000 | analysis/concordia_haggling_multi_item_compact_fruitville_multi_s30.json |
| haggling_multi_item | fruitville_multi | hpsmg_plus_proxy | 30 | 4.4000 | 3.9667 | 4.4000 | 1.9833 | 1.0000 | 4.8000 | 1.0000 | analysis/concordia_haggling_multi_item_compact_fruitville_multi_s30.json |
| haggling_multi_item | fruitville_multi | econ_bne_mech | 30 | 4.4000 | 3.4667 | 4.4000 | 1.7333 | 1.0000 | 4.5500 | 1.0000 | analysis/concordia_haggling_multi_item_compact_fruitville_multi_s30.json |
| haggling_multi_item | fruitville_multi | atom_tom1_mech | 30 | 3.9333 | 0.0000 | 3.9333 | 0.0000 | 1.0000 | 0.0000 | 1.0000 | analysis/concordia_haggling_multi_item_compact_fruitville_multi_s30.json |
| haggling_multi_item | fruitville_multi | oracle_joint | 30 | 4.4000 | -0.5333 | 4.4000 | -0.2667 | 1.0000 | 0.0000 | 1.0000 | analysis/concordia_haggling_multi_item_compact_fruitville_multi_s30.json |
| haggling_multi_item | vegbrooke | hpsmg_plus_joint_proxy | 30 | 4.5500 | 4.0000 | 4.5500 | 2.0000 | 1.0000 | 5.1000 | 1.0000 | analysis/concordia_haggling_multi_item_compact_vegbrooke_s30.json |
| haggling_multi_item | vegbrooke | hpsmg_plus_proxy | 30 | 4.5500 | 4.0000 | 4.5500 | 2.0000 | 1.0000 | 5.1000 | 1.0000 | analysis/concordia_haggling_multi_item_compact_vegbrooke_s30.json |
| haggling_multi_item | vegbrooke | econ_bne_mech | 30 | 4.5500 | 3.3667 | 4.5500 | 1.6833 | 1.0000 | 4.7833 | 1.0000 | analysis/concordia_haggling_multi_item_compact_vegbrooke_s30.json |
| haggling_multi_item | vegbrooke | atom_tom1_mech | 30 | 4.1000 | 0.0000 | 4.1000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 | analysis/concordia_haggling_multi_item_compact_vegbrooke_s30.json |
| haggling_multi_item | vegbrooke | oracle_joint | 30 | 4.5500 | -0.6333 | 4.5500 | -0.3167 | 1.0000 | 0.0000 | 1.0000 | analysis/concordia_haggling_multi_item_compact_vegbrooke_s30.json |

## SOTOPIA-Hard Vanilla Fair all70

| model | baseline | cases | target_cases | complete | mean_overall | agent_1_overall | agent_2_overall | source |
|---|---|---|---|---|---|---|---|---|
| DeepSeek-V3.2 | hpsmg_plus | 70 | 70 | True | 3.1939 | 2.9735 | 3.4143 | analysis/sotopia_hard_official_DeepSeek_V3_2_hpsmg_plus_all70.json |
| DeepSeek-V3.2 | econ_bne | 70 | 70 | True | 3.1765 | 2.9939 | 3.3592 | analysis/sotopia_hard_official_DeepSeek_V3_2_econ_bne_all70.json |
| DeepSeek-V3.2 | llm_greedy | 70 | 70 | True | 3.1643 | 2.9265 | 3.4020 | analysis/sotopia_hard_official_DeepSeek_V3_2_llm_greedy_all70.json |
| DeepSeek-V3.2 | atom_tom1 | 70 | 70 | True | 3.1061 | 2.8776 | 3.3347 | analysis/sotopia_hard_official_DeepSeek_V3_2_atom_tom1_all70.json |
| DeepSeek-V3.2 | llm_belief | 70 | 70 | True | 3.0776 | 2.8612 | 3.2939 | analysis/sotopia_hard_official_DeepSeek_V3_2_llm_belief_all70.json |
| Kimi-K2.6 | econ_bne | 70 | 70 | True | 2.4490 | 2.2367 | 2.6612 | analysis/sotopia_hard_official_Kimi_K2_6_econ_bne_all70.json |
| Kimi-K2.6 | llm_greedy | 70 | 70 | True | 2.1286 | 1.8898 | 2.3673 | analysis/sotopia_hard_official_Kimi_K2_6_llm_greedy_all70.json |
| Kimi-K2.6 | atom_tom1 | 70 | 70 | True | 1.8367 | 1.7265 | 1.9469 | analysis/sotopia_hard_official_Kimi_K2_6_atom_tom1_all70.json |
| Kimi-K2.6 | hpsmg_plus | 70 | 70 | True | 1.5776 | 1.4551 | 1.7000 | analysis/sotopia_hard_official_Kimi_K2_6_hpsmg_plus_all70.json |
| Kimi-K2.6 | llm_belief | 70 | 70 | True | 1.5531 | 1.3327 | 1.7735 | analysis/sotopia_hard_official_Kimi_K2_6_llm_belief_all70.json |
| Llama-4-Maverick | econ_bne | 70 | 70 | True | 3.2633 | 3.2878 | 3.2388 | analysis/sotopia_hard_official_Llama_4_Maverick_17B_128E_Instruct_FP8_econ_bne_all70.json |
| Llama-4-Maverick | llm_belief | 70 | 70 | True | 3.1765 | 3.1878 | 3.1653 | analysis/sotopia_hard_official_Llama_4_Maverick_17B_128E_Instruct_FP8_llm_belief_all70.json |
| Llama-4-Maverick | llm_greedy | 70 | 70 | True | 3.1541 | 3.1673 | 3.1408 | analysis/sotopia_hard_official_Llama_4_Maverick_17B_128E_Instruct_FP8_llm_greedy_all70.json |
| Llama-4-Maverick | hpsmg_plus | 70 | 70 | True | 3.1531 | 3.1673 | 3.1388 | analysis/sotopia_hard_official_Llama_4_Maverick_17B_128E_Instruct_FP8_hpsmg_plus_all70.json |
| Llama-4-Maverick | atom_tom1 | 70 | 70 | True | 3.1296 | 3.1898 | 3.0694 | analysis/sotopia_hard_official_Llama_4_Maverick_17B_128E_Instruct_FP8_atom_tom1_all70.json |
| gpt-5.4-nano | econ_bne | 70 | 70 | True | 2.9694 | 3.0388 | 2.9000 | analysis/sotopia_hard_official_gpt_5_4_nano_20260317_econ_bne_all70.json |
| gpt-5.4-nano | llm_belief | 70 | 70 | True | 2.9378 | 3.0245 | 2.8510 | analysis/sotopia_hard_official_gpt_5_4_nano_20260317_llm_belief_all70.json |
| gpt-5.4-nano | llm_greedy | 70 | 70 | True | 2.8908 | 2.9347 | 2.8469 | analysis/sotopia_hard_official_gpt_5_4_nano_20260317_llm_greedy_all70.json |
| gpt-5.4-nano | atom_tom1 | 70 | 70 | True | 2.7704 | 2.8163 | 2.7245 | analysis/sotopia_hard_official_gpt_5_4_nano_20260317_atom_tom1_all70.json |
| gpt-5.4-nano | hpsmg_plus | 70 | 70 | True | 2.6857 | 2.7878 | 2.5837 | analysis/sotopia_hard_official_gpt_5_4_nano_20260317_hpsmg_plus_all70.json |

## SOTOPIA-Hard Tuned All-Baseline Fair all70 Complete Rows

| model | baseline | cases | target_cases | complete | mean_overall | agent_1_overall | agent_2_overall | source |
|---|---|---|---|---|---|---|---|---|
| DeepSeek-V3.2 | econ_bne_sotopia_tuned | 70 | 70 | True | 3.3133 | 3.0551 | 3.5714 | analysis/sotopia_hard_official_DeepSeek_V3_2_econ_bne_sotopia_tuned_all70.json |
| DeepSeek-V3.2 | atom_tom1_sotopia_tuned | 70 | 70 | True | 3.2612 | 3.0694 | 3.4531 | analysis/sotopia_hard_official_DeepSeek_V3_2_atom_tom1_sotopia_tuned_all70.json |
| DeepSeek-V3.2 | hpsmg_plus_sotopia_tuned | 70 | 70 | True | 3.2480 | 2.9816 | 3.5143 | analysis/sotopia_hard_official_DeepSeek_V3_2_hpsmg_plus_sotopia_tuned_all70.json |
| DeepSeek-V3.2 | llm_belief_sotopia_tuned | 70 | 70 | True | 3.1954 | 2.9469 | 3.4439 | analysis/sotopia_hard_official_DeepSeek_V3_2_llm_belief_sotopia_tuned_all70.json |
| DeepSeek-V3.2 | llm_greedy_sotopia_tuned | 70 | 70 | True | 3.1929 | 2.9571 | 3.4286 | analysis/sotopia_hard_official_DeepSeek_V3_2_llm_greedy_sotopia_tuned_all70.json |
| Kimi-K2.6 | llm_belief_sotopia_tuned | 70 | 70 | True | 2.9061 | 2.7122 | 3.1000 | analysis/sotopia_hard_official_Kimi_K2_6_llm_belief_sotopia_tuned_all70.json |
| Kimi-K2.6 | econ_bne_sotopia_tuned | 70 | 70 | True | 2.8755 | 2.6857 | 3.0653 | analysis/sotopia_hard_official_Kimi_K2_6_econ_bne_sotopia_tuned_all70.json |
| Kimi-K2.6 | hpsmg_plus_sotopia_tuned | 70 | 70 | True | 2.8071 | 2.6531 | 2.9612 | analysis/sotopia_hard_official_Kimi_K2_6_hpsmg_plus_sotopia_tuned_all70.json |
| Kimi-K2.6 | llm_greedy_sotopia_tuned | 70 | 70 | True | 2.7612 | 2.5878 | 2.9347 | analysis/sotopia_hard_official_Kimi_K2_6_llm_greedy_sotopia_tuned_all70.json |
| Kimi-K2.6 | atom_tom1_sotopia_tuned | 70 | 70 | True | 2.7327 | 2.5776 | 2.8878 | analysis/sotopia_hard_official_Kimi_K2_6_atom_tom1_sotopia_tuned_all70.json |
| Llama-4-Maverick | atom_tom1_sotopia_tuned | 70 | 70 | True | 3.3592 | 3.4224 | 3.2959 | analysis/sotopia_hard_official_Llama_4_Maverick_17B_128E_Instruct_FP8_atom_tom1_sotopia_tuned_all70.json |
| Llama-4-Maverick | llm_belief_sotopia_tuned | 70 | 70 | True | 3.3398 | 3.4306 | 3.2490 | analysis/sotopia_hard_official_Llama_4_Maverick_17B_128E_Instruct_FP8_llm_belief_sotopia_tuned_all70.json |
| Llama-4-Maverick | econ_bne_sotopia_tuned | 70 | 70 | True | 3.3194 | 3.3816 | 3.2571 | analysis/sotopia_hard_official_Llama_4_Maverick_17B_128E_Instruct_FP8_econ_bne_sotopia_tuned_all70.json |
| Llama-4-Maverick | hpsmg_plus_sotopia_tuned | 70 | 70 | True | 3.3082 | 3.3857 | 3.2306 | analysis/sotopia_hard_official_Llama_4_Maverick_17B_128E_Instruct_FP8_hpsmg_plus_sotopia_tuned_all70.json |
| Llama-4-Maverick | llm_greedy_sotopia_tuned | 70 | 70 | True | 3.1653 | 3.1837 | 3.1469 | analysis/sotopia_hard_official_Llama_4_Maverick_17B_128E_Instruct_FP8_llm_greedy_sotopia_tuned_all70.json |
| gpt-5.4-nano | llm_belief_sotopia_tuned | 70 | 70 | True | 3.0000 | 3.1184 | 2.8816 | analysis/sotopia_hard_official_gpt_5_4_nano_20260317_llm_belief_sotopia_tuned_all70.json |
| gpt-5.4-nano | hpsmg_plus_sotopia_tuned | 70 | 70 | True | 2.9806 | 3.1224 | 2.8388 | analysis/sotopia_hard_official_gpt_5_4_nano_20260317_hpsmg_plus_sotopia_tuned_all70.json |
| gpt-5.4-nano | atom_tom1_sotopia_tuned | 70 | 70 | True | 2.9184 | 2.9939 | 2.8429 | analysis/sotopia_hard_official_gpt_5_4_nano_20260317_atom_tom1_sotopia_tuned_all70.json |
| gpt-5.4-nano | econ_bne_sotopia_tuned | 70 | 70 | True | 2.8429 | 2.9612 | 2.7245 | analysis/sotopia_hard_official_gpt_5_4_nano_20260317_econ_bne_sotopia_tuned_all70.json |
| gpt-5.4-nano | llm_greedy_sotopia_tuned | 70 | 70 | True | 2.8418 | 2.8755 | 2.8082 | analysis/sotopia_hard_official_gpt_5_4_nano_20260317_llm_greedy_sotopia_tuned_all70.json |

## SOTOPIA-Hard Official Reconstruction all70 Combined

| model | baseline | cases | target_cases | complete | mean_overall | agent_1_overall | agent_2_overall | source |
|---|---|---|---|---|---|---|---|---|
| DeepSeek-V3.2 | econ_bne_sotopia_tuned | 70 | 70 | True | 3.3133 | 3.0551 | 3.5714 | analysis/sotopia_hard_official_DeepSeek_V3_2_econ_bne_sotopia_tuned_all70.json |
| DeepSeek-V3.2 | atom_tom1_sotopia_tuned | 70 | 70 | True | 3.2612 | 3.0694 | 3.4531 | analysis/sotopia_hard_official_DeepSeek_V3_2_atom_tom1_sotopia_tuned_all70.json |
| DeepSeek-V3.2 | hpsmg_plus_sotopia_tuned | 70 | 70 | True | 3.2480 | 2.9816 | 3.5143 | analysis/sotopia_hard_official_DeepSeek_V3_2_hpsmg_plus_sotopia_tuned_all70.json |
| DeepSeek-V3.2 | llm_belief_sotopia_tuned | 70 | 70 | True | 3.1954 | 2.9469 | 3.4439 | analysis/sotopia_hard_official_DeepSeek_V3_2_llm_belief_sotopia_tuned_all70.json |
| DeepSeek-V3.2 | hpsmg_plus | 70 | 70 | True | 3.1939 | 2.9735 | 3.4143 | analysis/sotopia_hard_official_DeepSeek_V3_2_hpsmg_plus_all70.json |
| DeepSeek-V3.2 | llm_greedy_sotopia_tuned | 70 | 70 | True | 3.1929 | 2.9571 | 3.4286 | analysis/sotopia_hard_official_DeepSeek_V3_2_llm_greedy_sotopia_tuned_all70.json |
| DeepSeek-V3.2 | econ_bne | 70 | 70 | True | 3.1765 | 2.9939 | 3.3592 | analysis/sotopia_hard_official_DeepSeek_V3_2_econ_bne_all70.json |
| DeepSeek-V3.2 | llm_greedy | 70 | 70 | True | 3.1643 | 2.9265 | 3.4020 | analysis/sotopia_hard_official_DeepSeek_V3_2_llm_greedy_all70.json |
| DeepSeek-V3.2 | atom_tom1 | 70 | 70 | True | 3.1061 | 2.8776 | 3.3347 | analysis/sotopia_hard_official_DeepSeek_V3_2_atom_tom1_all70.json |
| DeepSeek-V3.2 | llm_belief | 70 | 70 | True | 3.0776 | 2.8612 | 3.2939 | analysis/sotopia_hard_official_DeepSeek_V3_2_llm_belief_all70.json |
| Kimi-K2.6 | llm_belief_sotopia_tuned | 70 | 70 | True | 2.9061 | 2.7122 | 3.1000 | analysis/sotopia_hard_official_Kimi_K2_6_llm_belief_sotopia_tuned_all70.json |
| Kimi-K2.6 | econ_bne_sotopia_tuned | 70 | 70 | True | 2.8755 | 2.6857 | 3.0653 | analysis/sotopia_hard_official_Kimi_K2_6_econ_bne_sotopia_tuned_all70.json |
| Kimi-K2.6 | hpsmg_plus_sotopia_tuned | 70 | 70 | True | 2.8071 | 2.6531 | 2.9612 | analysis/sotopia_hard_official_Kimi_K2_6_hpsmg_plus_sotopia_tuned_all70.json |
| Kimi-K2.6 | llm_greedy_sotopia_tuned | 70 | 70 | True | 2.7612 | 2.5878 | 2.9347 | analysis/sotopia_hard_official_Kimi_K2_6_llm_greedy_sotopia_tuned_all70.json |
| Kimi-K2.6 | atom_tom1_sotopia_tuned | 70 | 70 | True | 2.7327 | 2.5776 | 2.8878 | analysis/sotopia_hard_official_Kimi_K2_6_atom_tom1_sotopia_tuned_all70.json |
| Kimi-K2.6 | econ_bne | 70 | 70 | True | 2.4490 | 2.2367 | 2.6612 | analysis/sotopia_hard_official_Kimi_K2_6_econ_bne_all70.json |
| Kimi-K2.6 | llm_greedy | 70 | 70 | True | 2.1286 | 1.8898 | 2.3673 | analysis/sotopia_hard_official_Kimi_K2_6_llm_greedy_all70.json |
| Kimi-K2.6 | atom_tom1 | 70 | 70 | True | 1.8367 | 1.7265 | 1.9469 | analysis/sotopia_hard_official_Kimi_K2_6_atom_tom1_all70.json |
| Kimi-K2.6 | hpsmg_plus | 70 | 70 | True | 1.5776 | 1.4551 | 1.7000 | analysis/sotopia_hard_official_Kimi_K2_6_hpsmg_plus_all70.json |
| Kimi-K2.6 | llm_belief | 70 | 70 | True | 1.5531 | 1.3327 | 1.7735 | analysis/sotopia_hard_official_Kimi_K2_6_llm_belief_all70.json |
| Llama-4-Maverick | atom_tom1_sotopia_tuned | 70 | 70 | True | 3.3592 | 3.4224 | 3.2959 | analysis/sotopia_hard_official_Llama_4_Maverick_17B_128E_Instruct_FP8_atom_tom1_sotopia_tuned_all70.json |
| Llama-4-Maverick | llm_belief_sotopia_tuned | 70 | 70 | True | 3.3398 | 3.4306 | 3.2490 | analysis/sotopia_hard_official_Llama_4_Maverick_17B_128E_Instruct_FP8_llm_belief_sotopia_tuned_all70.json |
| Llama-4-Maverick | econ_bne_sotopia_tuned | 70 | 70 | True | 3.3194 | 3.3816 | 3.2571 | analysis/sotopia_hard_official_Llama_4_Maverick_17B_128E_Instruct_FP8_econ_bne_sotopia_tuned_all70.json |
| Llama-4-Maverick | hpsmg_plus_sotopia_tuned | 70 | 70 | True | 3.3082 | 3.3857 | 3.2306 | analysis/sotopia_hard_official_Llama_4_Maverick_17B_128E_Instruct_FP8_hpsmg_plus_sotopia_tuned_all70.json |
| Llama-4-Maverick | econ_bne | 70 | 70 | True | 3.2633 | 3.2878 | 3.2388 | analysis/sotopia_hard_official_Llama_4_Maverick_17B_128E_Instruct_FP8_econ_bne_all70.json |
| Llama-4-Maverick | llm_belief | 70 | 70 | True | 3.1765 | 3.1878 | 3.1653 | analysis/sotopia_hard_official_Llama_4_Maverick_17B_128E_Instruct_FP8_llm_belief_all70.json |
| Llama-4-Maverick | llm_greedy_sotopia_tuned | 70 | 70 | True | 3.1653 | 3.1837 | 3.1469 | analysis/sotopia_hard_official_Llama_4_Maverick_17B_128E_Instruct_FP8_llm_greedy_sotopia_tuned_all70.json |
| Llama-4-Maverick | llm_greedy | 70 | 70 | True | 3.1541 | 3.1673 | 3.1408 | analysis/sotopia_hard_official_Llama_4_Maverick_17B_128E_Instruct_FP8_llm_greedy_all70.json |
| Llama-4-Maverick | hpsmg_plus | 70 | 70 | True | 3.1531 | 3.1673 | 3.1388 | analysis/sotopia_hard_official_Llama_4_Maverick_17B_128E_Instruct_FP8_hpsmg_plus_all70.json |
| Llama-4-Maverick | atom_tom1 | 70 | 70 | True | 3.1296 | 3.1898 | 3.0694 | analysis/sotopia_hard_official_Llama_4_Maverick_17B_128E_Instruct_FP8_atom_tom1_all70.json |
| gpt-5.4-nano | llm_belief_sotopia_tuned | 70 | 70 | True | 3.0000 | 3.1184 | 2.8816 | analysis/sotopia_hard_official_gpt_5_4_nano_20260317_llm_belief_sotopia_tuned_all70.json |
| gpt-5.4-nano | hpsmg_plus_sotopia_tuned | 70 | 70 | True | 2.9806 | 3.1224 | 2.8388 | analysis/sotopia_hard_official_gpt_5_4_nano_20260317_hpsmg_plus_sotopia_tuned_all70.json |
| gpt-5.4-nano | econ_bne | 70 | 70 | True | 2.9694 | 3.0388 | 2.9000 | analysis/sotopia_hard_official_gpt_5_4_nano_20260317_econ_bne_all70.json |
| gpt-5.4-nano | llm_belief | 70 | 70 | True | 2.9378 | 3.0245 | 2.8510 | analysis/sotopia_hard_official_gpt_5_4_nano_20260317_llm_belief_all70.json |
| gpt-5.4-nano | atom_tom1_sotopia_tuned | 70 | 70 | True | 2.9184 | 2.9939 | 2.8429 | analysis/sotopia_hard_official_gpt_5_4_nano_20260317_atom_tom1_sotopia_tuned_all70.json |
| gpt-5.4-nano | llm_greedy | 70 | 70 | True | 2.8908 | 2.9347 | 2.8469 | analysis/sotopia_hard_official_gpt_5_4_nano_20260317_llm_greedy_all70.json |
| gpt-5.4-nano | econ_bne_sotopia_tuned | 70 | 70 | True | 2.8429 | 2.9612 | 2.7245 | analysis/sotopia_hard_official_gpt_5_4_nano_20260317_econ_bne_sotopia_tuned_all70.json |
| gpt-5.4-nano | llm_greedy_sotopia_tuned | 70 | 70 | True | 2.8418 | 2.8755 | 2.8082 | analysis/sotopia_hard_official_gpt_5_4_nano_20260317_llm_greedy_sotopia_tuned_all70.json |
| gpt-5.4-nano | atom_tom1 | 70 | 70 | True | 2.7704 | 2.8163 | 2.7245 | analysis/sotopia_hard_official_gpt_5_4_nano_20260317_atom_tom1_all70.json |
| gpt-5.4-nano | hpsmg_plus | 70 | 70 | True | 2.6857 | 2.7878 | 2.5837 | analysis/sotopia_hard_official_gpt_5_4_nano_20260317_hpsmg_plus_all70.json |

## SOTOPIA-Hard Official Reconstruction Dimension Means

| model | baseline | dimension | agent_1 | agent_2 | mean_agents |
|---|---|---|---|---|---|
| DeepSeek-V3.2 | hpsmg_plus | believability | 7.9714 | 8.4429 | 8.2071 |
| DeepSeek-V3.2 | hpsmg_plus | relationship | 2.2000 | 3.2000 | 2.7000 |
| DeepSeek-V3.2 | hpsmg_plus | knowledge | 7.0143 | 7.5714 | 7.2929 |
| DeepSeek-V3.2 | hpsmg_plus | secret | -2.2714 | -2.1571 | -2.2143 |
| DeepSeek-V3.2 | hpsmg_plus | social_rules | -1.9143 | -1.2571 | -1.5857 |
| DeepSeek-V3.2 | hpsmg_plus | financial_and_material_benefits | 1.8000 | 1.2286 | 1.5143 |
| DeepSeek-V3.2 | hpsmg_plus | goal | 6.0143 | 6.8714 | 6.4429 |
| DeepSeek-V3.2 | llm_belief | believability | 8.0000 | 8.4000 | 8.2000 |
| DeepSeek-V3.2 | llm_belief | relationship | 2.2571 | 3.1143 | 2.6857 |
| DeepSeek-V3.2 | llm_belief | knowledge | 6.9000 | 7.3286 | 7.1143 |
| DeepSeek-V3.2 | llm_belief | secret | -2.8000 | -2.6429 | -2.7214 |
| DeepSeek-V3.2 | llm_belief | social_rules | -2.1286 | -1.4000 | -1.7643 |
| DeepSeek-V3.2 | llm_belief | financial_and_material_benefits | 1.8286 | 1.2714 | 1.5500 |
| DeepSeek-V3.2 | llm_belief | goal | 5.9714 | 6.9857 | 6.4786 |
| DeepSeek-V3.2 | llm_greedy | believability | 7.9429 | 8.6000 | 8.2714 |
| DeepSeek-V3.2 | llm_greedy | relationship | 2.0143 | 3.0429 | 2.5286 |
| DeepSeek-V3.2 | llm_greedy | knowledge | 7.1286 | 7.7714 | 7.4500 |
| DeepSeek-V3.2 | llm_greedy | secret | -2.6286 | -2.5143 | -2.5714 |
| DeepSeek-V3.2 | llm_greedy | social_rules | -2.2286 | -1.6714 | -1.9500 |
| DeepSeek-V3.2 | llm_greedy | financial_and_material_benefits | 2.1000 | 1.3286 | 1.7143 |
| DeepSeek-V3.2 | llm_greedy | goal | 6.1571 | 7.2571 | 6.7071 |
| DeepSeek-V3.2 | atom_tom1 | believability | 8.0429 | 8.5286 | 8.2857 |
| DeepSeek-V3.2 | atom_tom1 | relationship | 2.1571 | 3.2429 | 2.7000 |
| DeepSeek-V3.2 | atom_tom1 | knowledge | 7.0000 | 7.5571 | 7.2786 |
| DeepSeek-V3.2 | atom_tom1 | secret | -2.8571 | -2.9000 | -2.8786 |
| DeepSeek-V3.2 | atom_tom1 | social_rules | -1.9000 | -1.2429 | -1.5714 |
| DeepSeek-V3.2 | atom_tom1 | financial_and_material_benefits | 1.7286 | 1.2000 | 1.4643 |
| DeepSeek-V3.2 | atom_tom1 | goal | 5.9714 | 6.9571 | 6.4643 |
| DeepSeek-V3.2 | econ_bne | believability | 8.0286 | 8.5429 | 8.2857 |
| DeepSeek-V3.2 | econ_bne | relationship | 2.5143 | 3.4143 | 2.9643 |
| DeepSeek-V3.2 | econ_bne | knowledge | 6.9000 | 7.3857 | 7.1429 |
| DeepSeek-V3.2 | econ_bne | secret | -2.5429 | -2.4000 | -2.4714 |
| DeepSeek-V3.2 | econ_bne | social_rules | -1.8571 | -1.4714 | -1.6643 |
| DeepSeek-V3.2 | econ_bne | financial_and_material_benefits | 1.7429 | 1.0143 | 1.3786 |
| DeepSeek-V3.2 | econ_bne | goal | 6.1714 | 7.0286 | 6.6000 |
| DeepSeek-V3.2 | hpsmg_plus_sotopia_tuned | believability | 7.6429 | 8.4429 | 8.0429 |
| DeepSeek-V3.2 | hpsmg_plus_sotopia_tuned | relationship | 2.2714 | 3.0571 | 2.6643 |
| DeepSeek-V3.2 | hpsmg_plus_sotopia_tuned | knowledge | 6.8714 | 7.6286 | 7.2500 |
| DeepSeek-V3.2 | hpsmg_plus_sotopia_tuned | secret | -2.4429 | -2.3429 | -2.3929 |
| DeepSeek-V3.2 | hpsmg_plus_sotopia_tuned | social_rules | -1.8286 | -1.2571 | -1.5429 |
| DeepSeek-V3.2 | hpsmg_plus_sotopia_tuned | financial_and_material_benefits | 2.3714 | 1.9286 | 2.1500 |
| DeepSeek-V3.2 | hpsmg_plus_sotopia_tuned | goal | 5.9857 | 7.1429 | 6.5643 |
| DeepSeek-V3.2 | llm_belief_sotopia_tuned | believability | 7.6857 | 8.4571 | 8.0714 |
| DeepSeek-V3.2 | llm_belief_sotopia_tuned | relationship | 2.2000 | 2.9286 | 2.5643 |
| DeepSeek-V3.2 | llm_belief_sotopia_tuned | knowledge | 6.8714 | 7.4000 | 7.1357 |
| DeepSeek-V3.2 | llm_belief_sotopia_tuned | secret | -2.4857 | -2.3857 | -2.4357 |
| DeepSeek-V3.2 | llm_belief_sotopia_tuned | social_rules | -1.6714 | -1.3357 | -1.5036 |
| DeepSeek-V3.2 | llm_belief_sotopia_tuned | financial_and_material_benefits | 2.0571 | 1.8143 | 1.9357 |
| DeepSeek-V3.2 | llm_belief_sotopia_tuned | goal | 5.9714 | 7.2286 | 6.6000 |
| DeepSeek-V3.2 | llm_greedy_sotopia_tuned | believability | 7.6857 | 8.4000 | 8.0429 |
| DeepSeek-V3.2 | llm_greedy_sotopia_tuned | relationship | 2.0714 | 2.9714 | 2.5214 |
| DeepSeek-V3.2 | llm_greedy_sotopia_tuned | knowledge | 6.8143 | 7.3286 | 7.0714 |
| DeepSeek-V3.2 | llm_greedy_sotopia_tuned | secret | -2.1286 | -2.2571 | -2.1929 |
| DeepSeek-V3.2 | llm_greedy_sotopia_tuned | social_rules | -1.8571 | -1.4429 | -1.6500 |
| DeepSeek-V3.2 | llm_greedy_sotopia_tuned | financial_and_material_benefits | 2.2429 | 1.8000 | 2.0214 |
| DeepSeek-V3.2 | llm_greedy_sotopia_tuned | goal | 5.8714 | 7.2000 | 6.5357 |
| DeepSeek-V3.2 | atom_tom1_sotopia_tuned | believability | 7.8714 | 8.5000 | 8.1857 |
| DeepSeek-V3.2 | atom_tom1_sotopia_tuned | relationship | 2.2857 | 2.9000 | 2.5929 |
| DeepSeek-V3.2 | atom_tom1_sotopia_tuned | knowledge | 6.9143 | 7.5000 | 7.2071 |
| DeepSeek-V3.2 | atom_tom1_sotopia_tuned | secret | -2.1143 | -2.2000 | -2.1571 |
| DeepSeek-V3.2 | atom_tom1_sotopia_tuned | social_rules | -1.5857 | -1.2571 | -1.4214 |
| DeepSeek-V3.2 | atom_tom1_sotopia_tuned | financial_and_material_benefits | 2.1143 | 1.7571 | 1.9357 |
| DeepSeek-V3.2 | atom_tom1_sotopia_tuned | goal | 6.0000 | 6.9714 | 6.4857 |
| DeepSeek-V3.2 | econ_bne_sotopia_tuned | believability | 7.6714 | 8.3857 | 8.0286 |
| DeepSeek-V3.2 | econ_bne_sotopia_tuned | relationship | 2.4857 | 3.0429 | 2.7643 |
| DeepSeek-V3.2 | econ_bne_sotopia_tuned | knowledge | 6.9286 | 7.3857 | 7.1571 |
| DeepSeek-V3.2 | econ_bne_sotopia_tuned | secret | -2.1857 | -1.9286 | -2.0571 |
| DeepSeek-V3.2 | econ_bne_sotopia_tuned | social_rules | -1.7714 | -1.2857 | -1.5286 |
| DeepSeek-V3.2 | econ_bne_sotopia_tuned | financial_and_material_benefits | 2.3143 | 2.1429 | 2.2286 |
| DeepSeek-V3.2 | econ_bne_sotopia_tuned | goal | 5.9429 | 7.2571 | 6.6000 |
| gpt-5.4-nano | hpsmg_plus | believability | 7.5000 | 7.7714 | 7.6357 |
| gpt-5.4-nano | hpsmg_plus | relationship | 2.6429 | 2.6571 | 2.6500 |
| gpt-5.4-nano | hpsmg_plus | knowledge | 5.6714 | 5.4571 | 5.5643 |
| gpt-5.4-nano | hpsmg_plus | secret | -5.4000 | -5.4286 | -5.4143 |
| gpt-5.4-nano | hpsmg_plus | social_rules | -1.4286 | -1.0571 | -1.2429 |
| gpt-5.4-nano | hpsmg_plus | financial_and_material_benefits | 2.5000 | 1.1429 | 1.8214 |
| gpt-5.4-nano | hpsmg_plus | goal | 8.0286 | 7.5429 | 7.7857 |
| gpt-5.4-nano | llm_belief | believability | 7.7143 | 7.9571 | 7.8357 |
| gpt-5.4-nano | llm_belief | relationship | 2.8000 | 2.8857 | 2.8429 |
| gpt-5.4-nano | llm_belief | knowledge | 5.9429 | 5.8714 | 5.9071 |
| gpt-5.4-nano | llm_belief | secret | -4.3571 | -4.2143 | -4.2857 |
| gpt-5.4-nano | llm_belief | social_rules | -1.3571 | -1.2143 | -1.2857 |
| gpt-5.4-nano | llm_belief | financial_and_material_benefits | 2.3714 | 1.2714 | 1.8214 |
| gpt-5.4-nano | llm_belief | goal | 8.0571 | 7.4000 | 7.7286 |
| gpt-5.4-nano | llm_greedy | believability | 7.6286 | 7.8857 | 7.7571 |
| gpt-5.4-nano | llm_greedy | relationship | 2.4857 | 2.7286 | 2.6071 |
| gpt-5.4-nano | llm_greedy | knowledge | 5.8571 | 6.0286 | 5.9429 |
| gpt-5.4-nano | llm_greedy | secret | -4.3714 | -4.2571 | -4.3143 |
| gpt-5.4-nano | llm_greedy | social_rules | -1.7286 | -1.1857 | -1.4571 |
| gpt-5.4-nano | llm_greedy | financial_and_material_benefits | 2.4143 | 1.1571 | 1.7857 |
| gpt-5.4-nano | llm_greedy | goal | 8.2571 | 7.5714 | 7.9143 |
| gpt-5.4-nano | atom_tom1 | believability | 7.5714 | 7.8714 | 7.7214 |
| gpt-5.4-nano | atom_tom1 | relationship | 2.6714 | 2.8143 | 2.7429 |
| gpt-5.4-nano | atom_tom1 | knowledge | 5.8143 | 5.7857 | 5.8000 |
| gpt-5.4-nano | atom_tom1 | secret | -5.3571 | -5.1857 | -5.2714 |
| gpt-5.4-nano | atom_tom1 | social_rules | -1.5429 | -0.9714 | -1.2571 |
| gpt-5.4-nano | atom_tom1 | financial_and_material_benefits | 2.4286 | 1.1000 | 1.7643 |
| gpt-5.4-nano | atom_tom1 | goal | 8.1286 | 7.6571 | 7.8929 |
| gpt-5.4-nano | econ_bne | believability | 7.7857 | 8.0286 | 7.9071 |
| gpt-5.4-nano | econ_bne | relationship | 2.9429 | 2.9857 | 2.9643 |
| gpt-5.4-nano | econ_bne | knowledge | 5.9571 | 5.9286 | 5.9429 |
| gpt-5.4-nano | econ_bne | secret | -4.5571 | -4.5143 | -4.5357 |
| gpt-5.4-nano | econ_bne | social_rules | -1.1286 | -0.9000 | -1.0143 |
| gpt-5.4-nano | econ_bne | financial_and_material_benefits | 2.2857 | 1.2571 | 1.7714 |
| gpt-5.4-nano | econ_bne | goal | 7.9857 | 7.5143 | 7.7500 |
| gpt-5.4-nano | hpsmg_plus_sotopia_tuned | believability | 7.9571 | 8.1429 | 8.0500 |
| gpt-5.4-nano | hpsmg_plus_sotopia_tuned | relationship | 2.7571 | 2.7143 | 2.7357 |
| gpt-5.4-nano | hpsmg_plus_sotopia_tuned | knowledge | 6.3000 | 6.2714 | 6.2857 |
| gpt-5.4-nano | hpsmg_plus_sotopia_tuned | secret | -4.5429 | -4.6000 | -4.5714 |
| gpt-5.4-nano | hpsmg_plus_sotopia_tuned | social_rules | -1.2143 | -1.2000 | -1.2071 |
| gpt-5.4-nano | hpsmg_plus_sotopia_tuned | financial_and_material_benefits | 2.5429 | 1.2429 | 1.8929 |
| gpt-5.4-nano | hpsmg_plus_sotopia_tuned | goal | 8.0571 | 7.3000 | 7.6786 |
| gpt-5.4-nano | llm_belief_sotopia_tuned | believability | 7.8286 | 8.0714 | 7.9500 |
| gpt-5.4-nano | llm_belief_sotopia_tuned | relationship | 2.7286 | 2.7571 | 2.7429 |
| gpt-5.4-nano | llm_belief_sotopia_tuned | knowledge | 6.3143 | 6.2000 | 6.2571 |
| gpt-5.4-nano | llm_belief_sotopia_tuned | secret | -4.1857 | -3.9857 | -4.0857 |
| gpt-5.4-nano | llm_belief_sotopia_tuned | social_rules | -1.4429 | -1.1857 | -1.3143 |
| gpt-5.4-nano | llm_belief_sotopia_tuned | financial_and_material_benefits | 2.5857 | 1.1143 | 1.8500 |
| gpt-5.4-nano | llm_belief_sotopia_tuned | goal | 8.0000 | 7.2000 | 7.6000 |
| gpt-5.4-nano | llm_greedy_sotopia_tuned | believability | 7.8286 | 7.9857 | 7.9071 |
| gpt-5.4-nano | llm_greedy_sotopia_tuned | relationship | 2.6286 | 2.6857 | 2.6571 |
| gpt-5.4-nano | llm_greedy_sotopia_tuned | knowledge | 6.0857 | 5.9000 | 5.9929 |
| gpt-5.4-nano | llm_greedy_sotopia_tuned | secret | -5.2429 | -5.0286 | -5.1357 |
| gpt-5.4-nano | llm_greedy_sotopia_tuned | social_rules | -1.5714 | -1.1000 | -1.3357 |
| gpt-5.4-nano | llm_greedy_sotopia_tuned | financial_and_material_benefits | 2.6429 | 1.4714 | 2.0571 |
| gpt-5.4-nano | llm_greedy_sotopia_tuned | goal | 7.7571 | 7.7429 | 7.7500 |
| gpt-5.4-nano | atom_tom1_sotopia_tuned | believability | 7.9286 | 8.1714 | 8.0500 |
| gpt-5.4-nano | atom_tom1_sotopia_tuned | relationship | 2.6857 | 2.9429 | 2.8143 |
| gpt-5.4-nano | atom_tom1_sotopia_tuned | knowledge | 6.1000 | 6.1286 | 6.1143 |
| gpt-5.4-nano | atom_tom1_sotopia_tuned | secret | -4.8143 | -4.8143 | -4.8143 |
| gpt-5.4-nano | atom_tom1_sotopia_tuned | social_rules | -1.3571 | -0.9571 | -1.1571 |
| gpt-5.4-nano | atom_tom1_sotopia_tuned | financial_and_material_benefits | 2.5429 | 1.2857 | 1.9143 |
| gpt-5.4-nano | atom_tom1_sotopia_tuned | goal | 7.8714 | 7.1429 | 7.5071 |
| gpt-5.4-nano | econ_bne_sotopia_tuned | believability | 7.9714 | 8.0714 | 8.0214 |
| gpt-5.4-nano | econ_bne_sotopia_tuned | relationship | 2.8714 | 2.8857 | 2.8786 |
| gpt-5.4-nano | econ_bne_sotopia_tuned | knowledge | 6.1857 | 6.0143 | 6.1000 |
| gpt-5.4-nano | econ_bne_sotopia_tuned | secret | -5.4429 | -5.2143 | -5.3286 |
| gpt-5.4-nano | econ_bne_sotopia_tuned | social_rules | -1.3286 | -1.1857 | -1.2571 |
| gpt-5.4-nano | econ_bne_sotopia_tuned | financial_and_material_benefits | 2.5857 | 1.2857 | 1.9357 |
| gpt-5.4-nano | econ_bne_sotopia_tuned | goal | 7.8857 | 7.2143 | 7.5500 |
| Kimi-K2.6 | hpsmg_plus | believability | 4.9571 | 4.4714 | 4.7143 |
| Kimi-K2.6 | hpsmg_plus | relationship | 0.1857 | 0.3429 | 0.2643 |
| Kimi-K2.6 | hpsmg_plus | knowledge | 3.9000 | 4.0714 | 3.9857 |
| Kimi-K2.6 | hpsmg_plus | secret | -0.1857 | -0.0571 | -0.1214 |
| Kimi-K2.6 | hpsmg_plus | social_rules | -1.8857 | -1.5571 | -1.7214 |
| Kimi-K2.6 | hpsmg_plus | financial_and_material_benefits | 0.0571 | 0.2571 | 0.1571 |
| Kimi-K2.6 | hpsmg_plus | goal | 3.1571 | 4.3714 | 3.7643 |
| Kimi-K2.6 | llm_belief | believability | 4.9000 | 4.8714 | 4.8857 |
| Kimi-K2.6 | llm_belief | relationship | -0.0286 | 0.1286 | 0.0500 |
| Kimi-K2.6 | llm_belief | knowledge | 3.7571 | 4.1143 | 3.9357 |
| Kimi-K2.6 | llm_belief | secret | -0.1429 | 0.0000 | -0.0714 |
| Kimi-K2.6 | llm_belief | social_rules | -1.7286 | -1.4000 | -1.5643 |
| Kimi-K2.6 | llm_belief | financial_and_material_benefits | -0.1143 | 0.3714 | 0.1286 |
| Kimi-K2.6 | llm_belief | goal | 2.6857 | 4.3286 | 3.5071 |
| Kimi-K2.6 | llm_greedy | believability | 6.6000 | 5.9714 | 6.2857 |
| Kimi-K2.6 | llm_greedy | relationship | -0.0143 | 0.4286 | 0.2071 |
| Kimi-K2.6 | llm_greedy | knowledge | 4.8857 | 5.3571 | 5.1214 |
| Kimi-K2.6 | llm_greedy | secret | -0.3286 | -0.0143 | -0.1714 |
| Kimi-K2.6 | llm_greedy | social_rules | -1.8000 | -1.1143 | -1.4571 |
| Kimi-K2.6 | llm_greedy | financial_and_material_benefits | -0.0571 | 0.2429 | 0.0929 |
| Kimi-K2.6 | llm_greedy | goal | 3.9429 | 5.7000 | 4.8214 |
| Kimi-K2.6 | atom_tom1 | believability | 5.9286 | 5.5286 | 5.7286 |
| Kimi-K2.6 | atom_tom1 | relationship | -0.0143 | 0.2429 | 0.1143 |
| Kimi-K2.6 | atom_tom1 | knowledge | 4.3143 | 4.2714 | 4.2929 |
| Kimi-K2.6 | atom_tom1 | secret | -0.3000 | -0.1429 | -0.2214 |
| Kimi-K2.6 | atom_tom1 | social_rules | -1.7571 | -1.5714 | -1.6643 |
| Kimi-K2.6 | atom_tom1 | financial_and_material_benefits | 0.2000 | 0.1857 | 0.1929 |
| Kimi-K2.6 | atom_tom1 | goal | 3.7143 | 5.1143 | 4.4143 |
| Kimi-K2.6 | econ_bne | believability | 7.0429 | 6.7571 | 6.9000 |
| Kimi-K2.6 | econ_bne | relationship | 1.0000 | 1.2143 | 1.1071 |
| Kimi-K2.6 | econ_bne | knowledge | 5.1286 | 5.1857 | 5.1571 |
| Kimi-K2.6 | econ_bne | secret | -0.1143 | -0.0286 | -0.0714 |
| Kimi-K2.6 | econ_bne | social_rules | -1.1857 | -0.8714 | -1.0286 |
| Kimi-K2.6 | econ_bne | financial_and_material_benefits | -0.1571 | 0.3571 | 0.1000 |
| Kimi-K2.6 | econ_bne | goal | 3.9429 | 6.0143 | 4.9786 |
| Kimi-K2.6 | hpsmg_plus_sotopia_tuned | believability | 7.5000 | 7.5571 | 7.5286 |
| Kimi-K2.6 | hpsmg_plus_sotopia_tuned | relationship | 1.4143 | 1.5286 | 1.4714 |
| Kimi-K2.6 | hpsmg_plus_sotopia_tuned | knowledge | 5.5571 | 5.6571 | 5.6071 |
| Kimi-K2.6 | hpsmg_plus_sotopia_tuned | secret | -0.1571 | -0.0714 | -0.1143 |
| Kimi-K2.6 | hpsmg_plus_sotopia_tuned | social_rules | -0.8286 | -0.6000 | -0.7143 |
| Kimi-K2.6 | hpsmg_plus_sotopia_tuned | financial_and_material_benefits | 0.1571 | 0.5571 | 0.3571 |
| Kimi-K2.6 | hpsmg_plus_sotopia_tuned | goal | 4.9286 | 6.1000 | 5.5143 |
| Kimi-K2.6 | llm_belief_sotopia_tuned | believability | 7.2571 | 7.5571 | 7.4071 |
| Kimi-K2.6 | llm_belief_sotopia_tuned | relationship | 1.9143 | 1.9429 | 1.9286 |
| Kimi-K2.6 | llm_belief_sotopia_tuned | knowledge | 5.6714 | 5.8857 | 5.7786 |
| Kimi-K2.6 | llm_belief_sotopia_tuned | secret | -0.1143 | -0.1286 | -0.1214 |
| Kimi-K2.6 | llm_belief_sotopia_tuned | social_rules | -0.5571 | -0.4000 | -0.4786 |
| Kimi-K2.6 | llm_belief_sotopia_tuned | financial_and_material_benefits | 0.0857 | 0.8143 | 0.4500 |
| Kimi-K2.6 | llm_belief_sotopia_tuned | goal | 4.7286 | 6.0286 | 5.3786 |
| Kimi-K2.6 | llm_greedy_sotopia_tuned | believability | 7.5286 | 7.6143 | 7.5714 |
| Kimi-K2.6 | llm_greedy_sotopia_tuned | relationship | 1.1714 | 1.3857 | 1.2786 |
| Kimi-K2.6 | llm_greedy_sotopia_tuned | knowledge | 5.5286 | 5.6143 | 5.5714 |
| Kimi-K2.6 | llm_greedy_sotopia_tuned | secret | -0.1571 | -0.0571 | -0.1071 |
| Kimi-K2.6 | llm_greedy_sotopia_tuned | social_rules | -0.9143 | -0.5429 | -0.7286 |
| Kimi-K2.6 | llm_greedy_sotopia_tuned | financial_and_material_benefits | 0.3000 | 0.5857 | 0.4429 |
| Kimi-K2.6 | llm_greedy_sotopia_tuned | goal | 4.6571 | 5.9429 | 5.3000 |
| Kimi-K2.6 | atom_tom1_sotopia_tuned | believability | 7.3286 | 7.6286 | 7.4786 |
| Kimi-K2.6 | atom_tom1_sotopia_tuned | relationship | 1.4143 | 1.6000 | 1.5071 |
| Kimi-K2.6 | atom_tom1_sotopia_tuned | knowledge | 5.3286 | 5.4000 | 5.3643 |
| Kimi-K2.6 | atom_tom1_sotopia_tuned | secret | -0.1714 | -0.1000 | -0.1357 |
| Kimi-K2.6 | atom_tom1_sotopia_tuned | social_rules | -0.7286 | -0.5000 | -0.6143 |
| Kimi-K2.6 | atom_tom1_sotopia_tuned | financial_and_material_benefits | 0.0143 | 0.2857 | 0.1500 |
| Kimi-K2.6 | atom_tom1_sotopia_tuned | goal | 4.8571 | 5.9000 | 5.3786 |
| Kimi-K2.6 | econ_bne_sotopia_tuned | believability | 7.4571 | 7.4857 | 7.4714 |
| Kimi-K2.6 | econ_bne_sotopia_tuned | relationship | 1.6857 | 1.7429 | 1.7143 |
| Kimi-K2.6 | econ_bne_sotopia_tuned | knowledge | 5.6571 | 5.6571 | 5.6571 |
| Kimi-K2.6 | econ_bne_sotopia_tuned | secret | -0.1714 | -0.0857 | -0.1286 |
| Kimi-K2.6 | econ_bne_sotopia_tuned | social_rules | -0.7000 | -0.4286 | -0.5643 |
| Kimi-K2.6 | econ_bne_sotopia_tuned | financial_and_material_benefits | 0.0857 | 1.0571 | 0.5714 |
| Kimi-K2.6 | econ_bne_sotopia_tuned | goal | 4.7857 | 6.0286 | 5.4071 |
| Llama-4-Maverick | hpsmg_plus | believability | 7.9000 | 8.1714 | 8.0357 |
| Llama-4-Maverick | hpsmg_plus | relationship | 0.8143 | 0.6143 | 0.7143 |
| Llama-4-Maverick | hpsmg_plus | knowledge | 7.5286 | 7.3857 | 7.4571 |
| Llama-4-Maverick | hpsmg_plus | secret | -0.3857 | -0.1143 | -0.2500 |
| Llama-4-Maverick | hpsmg_plus | social_rules | -1.3571 | -0.7286 | -1.0429 |
| Llama-4-Maverick | hpsmg_plus | financial_and_material_benefits | 1.2286 | 0.3429 | 0.7857 |
| Llama-4-Maverick | hpsmg_plus | goal | 6.4429 | 6.3000 | 6.3714 |
| Llama-4-Maverick | llm_belief | believability | 7.8857 | 8.1429 | 8.0143 |
| Llama-4-Maverick | llm_belief | relationship | 1.0714 | 1.0286 | 1.0500 |
| Llama-4-Maverick | llm_belief | knowledge | 7.4571 | 7.2571 | 7.3571 |
| Llama-4-Maverick | llm_belief | secret | -0.4286 | -0.3429 | -0.3857 |
| Llama-4-Maverick | llm_belief | social_rules | -1.2857 | -0.7143 | -1.0000 |
| Llama-4-Maverick | llm_belief | financial_and_material_benefits | 1.1143 | 0.3714 | 0.7429 |
| Llama-4-Maverick | llm_belief | goal | 6.5000 | 6.4143 | 6.4571 |
| Llama-4-Maverick | llm_greedy | believability | 7.8286 | 8.1714 | 8.0000 |
| Llama-4-Maverick | llm_greedy | relationship | 0.7571 | 0.6857 | 0.7214 |
| Llama-4-Maverick | llm_greedy | knowledge | 7.4143 | 7.3143 | 7.3643 |
| Llama-4-Maverick | llm_greedy | secret | -0.4429 | -0.3571 | -0.4000 |
| Llama-4-Maverick | llm_greedy | social_rules | -1.6143 | -0.7143 | -1.1643 |
| Llama-4-Maverick | llm_greedy | financial_and_material_benefits | 1.7286 | 0.4429 | 1.0857 |
| Llama-4-Maverick | llm_greedy | goal | 6.5000 | 6.4429 | 6.4714 |
| Llama-4-Maverick | atom_tom1 | believability | 7.7714 | 8.0286 | 7.9000 |
| Llama-4-Maverick | atom_tom1 | relationship | 0.9143 | 0.9429 | 0.9286 |
| Llama-4-Maverick | atom_tom1 | knowledge | 7.5857 | 7.3857 | 7.4857 |
| Llama-4-Maverick | atom_tom1 | secret | -0.4143 | -0.2286 | -0.3214 |
| Llama-4-Maverick | atom_tom1 | social_rules | -1.4857 | -0.8714 | -1.1786 |
| Llama-4-Maverick | atom_tom1 | financial_and_material_benefits | 1.5429 | 0.2714 | 0.9071 |
| Llama-4-Maverick | atom_tom1 | goal | 6.4143 | 5.9571 | 6.1857 |
| Llama-4-Maverick | econ_bne | believability | 7.8000 | 8.1000 | 7.9500 |
| Llama-4-Maverick | econ_bne | relationship | 1.4000 | 1.3714 | 1.3857 |
| Llama-4-Maverick | econ_bne | knowledge | 7.5000 | 7.5000 | 7.5000 |
| Llama-4-Maverick | econ_bne | secret | -0.5000 | -0.3571 | -0.4286 |
| Llama-4-Maverick | econ_bne | social_rules | -1.3714 | -0.7286 | -1.0500 |
| Llama-4-Maverick | econ_bne | financial_and_material_benefits | 1.6714 | 0.4000 | 1.0357 |
| Llama-4-Maverick | econ_bne | goal | 6.5143 | 6.3857 | 6.4500 |
| Llama-4-Maverick | hpsmg_plus_sotopia_tuned | believability | 7.9429 | 8.2571 | 8.1000 |
| Llama-4-Maverick | hpsmg_plus_sotopia_tuned | relationship | 1.4857 | 1.4857 | 1.4857 |
| Llama-4-Maverick | hpsmg_plus_sotopia_tuned | knowledge | 7.6857 | 7.6143 | 7.6500 |
| Llama-4-Maverick | hpsmg_plus_sotopia_tuned | secret | -0.5571 | -0.3714 | -0.4643 |
| Llama-4-Maverick | hpsmg_plus_sotopia_tuned | social_rules | -1.2143 | -0.7143 | -0.9643 |
| Llama-4-Maverick | hpsmg_plus_sotopia_tuned | financial_and_material_benefits | 1.8000 | 0.0000 | 0.9000 |
| Llama-4-Maverick | hpsmg_plus_sotopia_tuned | goal | 6.5571 | 6.3429 | 6.4500 |
| Llama-4-Maverick | llm_belief_sotopia_tuned | believability | 7.9429 | 8.2429 | 8.0929 |
| Llama-4-Maverick | llm_belief_sotopia_tuned | relationship | 1.5286 | 1.4857 | 1.5071 |
| Llama-4-Maverick | llm_belief_sotopia_tuned | knowledge | 7.6857 | 7.6714 | 7.6786 |
| Llama-4-Maverick | llm_belief_sotopia_tuned | secret | -0.4286 | -0.3429 | -0.3857 |
| Llama-4-Maverick | llm_belief_sotopia_tuned | social_rules | -1.0857 | -0.6286 | -0.8571 |
| Llama-4-Maverick | llm_belief_sotopia_tuned | financial_and_material_benefits | 1.7857 | -0.0857 | 0.8500 |
| Llama-4-Maverick | llm_belief_sotopia_tuned | goal | 6.5857 | 6.4000 | 6.4929 |
| Llama-4-Maverick | llm_greedy_sotopia_tuned | believability | 7.8857 | 8.2143 | 8.0500 |
| Llama-4-Maverick | llm_greedy_sotopia_tuned | relationship | 1.1571 | 1.1429 | 1.1500 |
| Llama-4-Maverick | llm_greedy_sotopia_tuned | knowledge | 7.5000 | 7.4714 | 7.4857 |
| Llama-4-Maverick | llm_greedy_sotopia_tuned | secret | -0.5857 | -0.3286 | -0.4571 |
| Llama-4-Maverick | llm_greedy_sotopia_tuned | social_rules | -1.4000 | -0.8714 | -1.1357 |
| Llama-4-Maverick | llm_greedy_sotopia_tuned | financial_and_material_benefits | 1.3143 | 0.0714 | 0.6929 |
| Llama-4-Maverick | llm_greedy_sotopia_tuned | goal | 6.4143 | 6.3286 | 6.3714 |
| Llama-4-Maverick | atom_tom1_sotopia_tuned | believability | 7.8857 | 8.2143 | 8.0500 |
| Llama-4-Maverick | atom_tom1_sotopia_tuned | relationship | 1.3000 | 1.3857 | 1.3429 |
| Llama-4-Maverick | atom_tom1_sotopia_tuned | knowledge | 7.8714 | 7.7000 | 7.7857 |
| Llama-4-Maverick | atom_tom1_sotopia_tuned | secret | -0.4571 | -0.2571 | -0.3571 |
| Llama-4-Maverick | atom_tom1_sotopia_tuned | social_rules | -1.1000 | -0.6429 | -0.8714 |
| Llama-4-Maverick | atom_tom1_sotopia_tuned | financial_and_material_benefits | 1.7429 | -0.0143 | 0.8643 |
| Llama-4-Maverick | atom_tom1_sotopia_tuned | goal | 6.7143 | 6.6857 | 6.7000 |
| Llama-4-Maverick | econ_bne_sotopia_tuned | believability | 7.9429 | 8.2571 | 8.1000 |
| Llama-4-Maverick | econ_bne_sotopia_tuned | relationship | 1.6429 | 1.6571 | 1.6500 |
| Llama-4-Maverick | econ_bne_sotopia_tuned | knowledge | 7.5571 | 7.6143 | 7.5857 |
| Llama-4-Maverick | econ_bne_sotopia_tuned | secret | -0.4286 | -0.1714 | -0.3000 |
| Llama-4-Maverick | econ_bne_sotopia_tuned | social_rules | -1.1429 | -0.6857 | -0.9143 |
| Llama-4-Maverick | econ_bne_sotopia_tuned | financial_and_material_benefits | 1.6143 | -0.2286 | 0.6929 |
| Llama-4-Maverick | econ_bne_sotopia_tuned | goal | 6.4857 | 6.3571 | 6.4214 |
