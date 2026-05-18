# Live Calibration Overnight Summary

calibration: `calibration_cloudgpt_multi_model_fast4_8algos_Kimi_K2_6_c14.npy`
tid_min_gap: `0.0899`
new_live_cells: `48`
parse_failure_count: `0`

## E2 beta sweep

| beta | oracle | hpsmg_plus | hpsmg | joint_psrl | map_greedy | psrl_notype | iql | random | file |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0.0 | 0.0 | 0.936 | 0.644 | 1.55 | 0.854 | 19.426 | 27.109825 | 27.887358 | `results\cloudgpt\E2_Kimi_K2_6_c14_beta0.npz` |
| 0.05 | 0.0 | 0.936 | 0.644 | 1.55 | 0.854 | 19.426 | 27.109825 | 27.887358 | `results\cloudgpt\E2_Kimi_K2_6_c14_beta0p05.npz` |
| 0.1 | 0.0 | 0.936 | 0.644 | 1.55 | 0.854 | 19.426 | 27.109825 | 27.887358 | `results\cloudgpt\E2_Kimi_K2_6_c14_beta0p1.npz` |
| 0.25 | 0.0 | 0.936 | 0.644 | 1.55 | 0.854 | 19.426 | 27.109825 | 27.887358 | `results\cloudgpt\E2_Kimi_K2_6_c14_beta0p25.npz` |
| 0.5 | 0.0 | 0.96 | 0.644 | 1.55 | 0.854 | 19.426 | 27.109825 | 27.887358 | `results\cloudgpt\E2_Kimi_K2_6_c14_beta0p5.npz` |
| 0.75 | 0.0 | 0.932 | 0.644 | 1.55 | 0.854 | 19.426 | 27.109825 | 27.887358 | `results\cloudgpt\E2_Kimi_K2_6_c14_beta0p75.npz` |
| 1.0 | 0.0 | 0.946 | 0.644 | 1.55 | 0.854 | 19.426 | 27.109825 | 27.887358 | `results\cloudgpt\E2_Kimi_K2_6_c14_beta1.npz` |
| 1.5 | 0.0 | 0.974 | 0.644 | 1.55 | 0.854 | 19.426 | 27.109825 | 27.887358 | `results\cloudgpt\E2_Kimi_K2_6_c14_beta1p5.npz` |

## Best hpsmg_plus

file: `results\cloudgpt\E2_Kimi_K2_6_c14_beta0p75.npz`
beta: `0.75`
final_regret: `{'hpsmg_plus': 0.932, 'hpsmg': 0.644, 'joint_psrl': 1.55, 'map_greedy': 0.854, 'psrl_notype': 19.426, 'iql': 27.109825, 'random': 27.887358, 'oracle': 0.0}`

## Audit

```text
backend=cloudgpt_live
tid_min_gap=0.0899
altruistic_builder: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
conditional_cooperator: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
risk_averse_balancer: mean_best_contribution=0.750 best_by_player=0.75,1.00,0.50
free_rider: mean_best_contribution=0.333 best_by_player=0.00,0.00,1.00
```
