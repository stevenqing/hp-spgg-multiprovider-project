# Live Calibration Overnight Summary

calibration: `calibration_cloudgpt_multi_model_fast4_Kimi_K2_6_c5.npy`
tid_min_gap: `0.0740`
new_live_cells: `48`
parse_failure_count: `0`

## E2 beta sweep

| beta | oracle | hpsmg_plus | hpsmg | random | file |
| ---: | ---: | ---: | ---: | ---: | --- |
| 0.0 | 0.0 | 0.992 | 0.644 | 26.832619 | `results\cloudgpt\E2_Kimi_K2_6_c5_beta0.npz` |
| 0.05 | 0.0 | 0.992 | 0.644 | 26.832619 | `results\cloudgpt\E2_Kimi_K2_6_c5_beta0p05.npz` |
| 0.1 | 0.0 | 0.992 | 0.644 | 26.832619 | `results\cloudgpt\E2_Kimi_K2_6_c5_beta0p1.npz` |
| 0.25 | 0.0 | 0.992 | 0.644 | 26.832619 | `results\cloudgpt\E2_Kimi_K2_6_c5_beta0p25.npz` |
| 0.5 | 0.0 | 1.016 | 0.644 | 26.832619 | `results\cloudgpt\E2_Kimi_K2_6_c5_beta0p5.npz` |
| 0.75 | 0.0 | 1.002 | 0.644 | 26.832619 | `results\cloudgpt\E2_Kimi_K2_6_c5_beta0p75.npz` |
| 1.0 | 0.0 | 0.906 | 0.644 | 26.832619 | `results\cloudgpt\E2_Kimi_K2_6_c5_beta1.npz` |
| 1.5 | 0.0 | 0.934 | 0.644 | 26.832619 | `results\cloudgpt\E2_Kimi_K2_6_c5_beta1p5.npz` |

## Best hpsmg_plus

file: `results\cloudgpt\E2_Kimi_K2_6_c5_beta1.npz`
beta: `1.0`
final_regret: `{'hpsmg_plus': 0.906, 'hpsmg': 0.644, 'oracle': 0.0, 'random': 26.832619}`

## Audit

```text
backend=cloudgpt_live
tid_min_gap=0.0740
altruistic_builder: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
conditional_cooperator: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
risk_averse_balancer: mean_best_contribution=0.750 best_by_player=0.75,1.00,0.50
free_rider: mean_best_contribution=0.333 best_by_player=0.00,0.00,1.00
```
