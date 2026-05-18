# Live Calibration Overnight Summary

calibration: `calibration_cloudgpt_multi_model_DeepSeek_V3_2_c2.npy`
tid_min_gap: `0.0757`
new_live_cells: `48`
parse_failure_count: `0`

## E2 beta sweep

| beta | hpsmg_plus | hpsmg | oracle | random | file |
| ---: | ---: | ---: | ---: | ---: | --- |
| 0.0 | 1.088 | 0.644 | 0.0 | 28.13626 | `results\cloudgpt\E2_DeepSeek_V3_2_c2_beta0.npz` |
| 0.05 | 1.088 | 0.644 | 0.0 | 28.13626 | `results\cloudgpt\E2_DeepSeek_V3_2_c2_beta0p05.npz` |
| 0.1 | 1.088 | 0.644 | 0.0 | 28.13626 | `results\cloudgpt\E2_DeepSeek_V3_2_c2_beta0p1.npz` |
| 0.25 | 1.088 | 0.644 | 0.0 | 28.13626 | `results\cloudgpt\E2_DeepSeek_V3_2_c2_beta0p25.npz` |
| 0.5 | 1.112 | 0.644 | 0.0 | 28.13626 | `results\cloudgpt\E2_DeepSeek_V3_2_c2_beta0p5.npz` |
| 0.75 | 1.082 | 0.644 | 0.0 | 28.13626 | `results\cloudgpt\E2_DeepSeek_V3_2_c2_beta0p75.npz` |
| 1.0 | 0.986 | 0.644 | 0.0 | 28.13626 | `results\cloudgpt\E2_DeepSeek_V3_2_c2_beta1.npz` |
| 1.5 | 1.014 | 0.644 | 0.0 | 28.13626 | `results\cloudgpt\E2_DeepSeek_V3_2_c2_beta1p5.npz` |

## Best hpsmg_plus

file: `results\cloudgpt\E2_DeepSeek_V3_2_c2_beta1.npz`
beta: `1.0`
final_regret: `{'hpsmg_plus': 0.986, 'hpsmg': 0.644, 'oracle': 0.0, 'random': 28.13626}`

## Audit

```text
backend=cloudgpt_live
tid_min_gap=0.0757
altruistic_builder: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
conditional_cooperator: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
risk_averse_balancer: mean_best_contribution=0.750 best_by_player=0.75,1.00,0.50
free_rider: mean_best_contribution=0.000 best_by_player=0.00,0.00,0.00
```
