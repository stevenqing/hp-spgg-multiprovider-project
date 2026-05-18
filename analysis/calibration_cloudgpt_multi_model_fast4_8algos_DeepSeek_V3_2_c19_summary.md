# Live Calibration Overnight Summary

calibration: `calibration_cloudgpt_multi_model_fast4_8algos_DeepSeek_V3_2_c19.npy`
tid_min_gap: `0.1324`
new_live_cells: `24`
parse_failure_count: `0`

## E2 beta sweep

| beta | oracle | hpsmg_plus | hpsmg | joint_psrl | map_greedy | psrl_notype | iql | random | file |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0.0 | 0.0 | 0.4 | 0.828 | 0.832 | 0.712 | 13.912 | 28.342 | 28.266 | `results\cloudgpt\E2_DeepSeek_V3_2_c19_beta0.npz` |
| 0.05 | 0.0 | 0.4 | 0.828 | 0.832 | 0.712 | 13.912 | 28.342 | 28.266 | `results\cloudgpt\E2_DeepSeek_V3_2_c19_beta0p05.npz` |
| 0.1 | 0.0 | 0.4 | 0.828 | 0.832 | 0.712 | 13.912 | 28.342 | 28.266 | `results\cloudgpt\E2_DeepSeek_V3_2_c19_beta0p1.npz` |
| 0.25 | 0.0 | 0.4 | 0.828 | 0.832 | 0.712 | 13.912 | 28.342 | 28.266 | `results\cloudgpt\E2_DeepSeek_V3_2_c19_beta0p25.npz` |
| 0.5 | 0.0 | 0.4 | 0.828 | 0.832 | 0.712 | 13.912 | 28.342 | 28.266 | `results\cloudgpt\E2_DeepSeek_V3_2_c19_beta0p5.npz` |
| 0.75 | 0.0 | 0.4 | 0.828 | 0.832 | 0.712 | 13.912 | 28.342 | 28.266 | `results\cloudgpt\E2_DeepSeek_V3_2_c19_beta0p75.npz` |
| 1.0 | 0.0 | 0.53 | 0.828 | 0.832 | 0.712 | 13.912 | 28.342 | 28.266 | `results\cloudgpt\E2_DeepSeek_V3_2_c19_beta1.npz` |
| 1.5 | 0.0 | 0.63 | 0.828 | 0.832 | 0.712 | 13.912 | 28.342 | 28.266 | `results\cloudgpt\E2_DeepSeek_V3_2_c19_beta1p5.npz` |

## Best hpsmg_plus

file: `results\cloudgpt\E2_DeepSeek_V3_2_c19_beta0.npz`
beta: `0.0`
final_regret: `{'hpsmg_plus': 0.4, 'hpsmg': 0.828, 'joint_psrl': 0.832, 'map_greedy': 0.712, 'psrl_notype': 13.912, 'iql': 28.342, 'random': 28.266, 'oracle': 0.0}`

## Audit

```text
backend=cloudgpt_live
tid_min_gap=0.1324
altruistic_builder: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
conditional_cooperator: mean_best_contribution=1.000 best_by_player=1.00,1.00,1.00
risk_averse_balancer: mean_best_contribution=0.250 best_by_player=0.25,0.25,0.25
free_rider: mean_best_contribution=0.000 best_by_player=0.00,0.00,0.00
```
