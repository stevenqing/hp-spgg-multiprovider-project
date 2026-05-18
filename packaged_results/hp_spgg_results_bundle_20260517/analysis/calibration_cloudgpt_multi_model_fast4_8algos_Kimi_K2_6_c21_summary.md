# Live Calibration Overnight Summary

calibration: `calibration_cloudgpt_multi_model_fast4_8algos_Kimi_K2_6_c21.npy`
tid_min_gap: `0.0956`
new_live_cells: `24`
parse_failure_count: `0`

## E2 beta sweep

| beta | oracle | hpsmg_plus | hpsmg | joint_psrl | map_greedy | psrl_notype | iql | random | file |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0.0 | 0.0 | 0.25 | 0.38 | 0.998 | 0.802 | 12.906 | 23.832 | 28.684 | `results\cloudgpt\E2_Kimi_K2_6_c21_beta0.npz` |
| 0.05 | 0.0 | 0.25 | 0.38 | 0.998 | 0.802 | 12.906 | 23.832 | 28.684 | `results\cloudgpt\E2_Kimi_K2_6_c21_beta0p05.npz` |
| 0.1 | 0.0 | 0.25 | 0.38 | 0.998 | 0.802 | 12.906 | 23.832 | 28.684 | `results\cloudgpt\E2_Kimi_K2_6_c21_beta0p1.npz` |
| 0.25 | 0.0 | 0.25 | 0.38 | 0.998 | 0.802 | 12.906 | 23.832 | 28.684 | `results\cloudgpt\E2_Kimi_K2_6_c21_beta0p25.npz` |
| 0.5 | 0.0 | 0.25 | 0.38 | 0.998 | 0.802 | 12.906 | 23.832 | 28.684 | `results\cloudgpt\E2_Kimi_K2_6_c21_beta0p5.npz` |
| 0.75 | 0.0 | 0.25 | 0.38 | 0.998 | 0.802 | 12.906 | 23.832 | 28.684 | `results\cloudgpt\E2_Kimi_K2_6_c21_beta0p75.npz` |
| 1.0 | 0.0 | 0.25 | 0.38 | 0.998 | 0.802 | 12.906 | 23.832 | 28.684 | `results\cloudgpt\E2_Kimi_K2_6_c21_beta1.npz` |
| 1.5 | 0.0 | 0.942 | 0.38 | 0.998 | 0.802 | 12.906 | 23.832 | 28.684 | `results\cloudgpt\E2_Kimi_K2_6_c21_beta1p5.npz` |

## Best hpsmg_plus

file: `results\cloudgpt\E2_Kimi_K2_6_c21_beta0.npz`
beta: `0.0`
final_regret: `{'hpsmg_plus': 0.25, 'hpsmg': 0.38, 'joint_psrl': 0.998, 'map_greedy': 0.802, 'psrl_notype': 12.906, 'iql': 23.832, 'random': 28.684, 'oracle': 0.0}`

## Audit

```text
backend=cloudgpt_live
tid_min_gap=0.0956
altruistic_builder: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
conditional_cooperator: mean_best_contribution=0.917 best_by_player=0.75,1.00,1.00
risk_averse_balancer: mean_best_contribution=0.583 best_by_player=0.75,0.50,0.50
free_rider: mean_best_contribution=0.000 best_by_player=0.00,0.00,0.00
```
