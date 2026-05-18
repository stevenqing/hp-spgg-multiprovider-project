# Live Calibration Overnight Summary

calibration: `calibration_cloudgpt_multi_model_fast_DeepSeek_V3_2_c1.npy`
tid_min_gap: `0.0806`
new_live_cells: `48`
parse_failure_count: `0`

## E2 beta sweep

| beta | hpsmg_plus | hpsmg | oracle | random | file |
| ---: | ---: | ---: | ---: | ---: | --- |
| 0.0 | 0.75 | 0.728 | 0.0 | 27.704738 | `results\cloudgpt\E2_DeepSeek_V3_2_c1_beta0.npz` |
| 0.05 | 0.75 | 0.728 | 0.0 | 27.704738 | `results\cloudgpt\E2_DeepSeek_V3_2_c1_beta0p05.npz` |
| 0.1 | 0.75 | 0.728 | 0.0 | 27.704738 | `results\cloudgpt\E2_DeepSeek_V3_2_c1_beta0p1.npz` |
| 0.25 | 0.75 | 0.728 | 0.0 | 27.704738 | `results\cloudgpt\E2_DeepSeek_V3_2_c1_beta0p25.npz` |
| 0.5 | 0.824 | 0.728 | 0.0 | 27.704738 | `results\cloudgpt\E2_DeepSeek_V3_2_c1_beta0p5.npz` |
| 0.75 | 0.824 | 0.728 | 0.0 | 27.704738 | `results\cloudgpt\E2_DeepSeek_V3_2_c1_beta0p75.npz` |
| 1.0 | 0.824 | 0.728 | 0.0 | 27.704738 | `results\cloudgpt\E2_DeepSeek_V3_2_c1_beta1.npz` |
| 1.5 | 0.936 | 0.728 | 0.0 | 27.704738 | `results\cloudgpt\E2_DeepSeek_V3_2_c1_beta1p5.npz` |

## Best hpsmg_plus

file: `results\cloudgpt\E2_DeepSeek_V3_2_c1_beta0.npz`
beta: `0.0`
final_regret: `{'hpsmg_plus': 0.75, 'hpsmg': 0.728, 'oracle': 0.0, 'random': 27.704738}`

## Audit

```text
backend=cloudgpt_live
tid_min_gap=0.0806
altruistic_builder: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
conditional_cooperator: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
risk_averse_balancer: mean_best_contribution=0.750 best_by_player=0.75,1.00,0.50
free_rider: mean_best_contribution=0.000 best_by_player=0.00,0.00,0.00
```
