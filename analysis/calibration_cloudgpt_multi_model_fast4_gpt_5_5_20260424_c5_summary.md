# Live Calibration Overnight Summary

calibration: `calibration_cloudgpt_multi_model_fast4_gpt_5_5_20260424_c5.npy`
tid_min_gap: `0.0799`
new_live_cells: `2`
parse_failure_count: `4`

## E2 beta sweep

| beta | oracle | hpsmg_plus | hpsmg | random | file |
| ---: | ---: | ---: | ---: | ---: | --- |
| 0.0 | 0.0 | 0.912 | 0.644 | 28.32616 | `results\cloudgpt\E2_gpt_5_5_20260424_c5_beta0.npz` |
| 0.05 | 0.0 | 0.912 | 0.644 | 28.32616 | `results\cloudgpt\E2_gpt_5_5_20260424_c5_beta0p05.npz` |
| 0.1 | 0.0 | 0.912 | 0.644 | 28.32616 | `results\cloudgpt\E2_gpt_5_5_20260424_c5_beta0p1.npz` |
| 0.25 | 0.0 | 0.912 | 0.644 | 28.32616 | `results\cloudgpt\E2_gpt_5_5_20260424_c5_beta0p25.npz` |
| 0.5 | 0.0 | 0.936 | 0.644 | 28.32616 | `results\cloudgpt\E2_gpt_5_5_20260424_c5_beta0p5.npz` |
| 0.75 | 0.0 | 0.994 | 0.644 | 28.32616 | `results\cloudgpt\E2_gpt_5_5_20260424_c5_beta0p75.npz` |
| 1.0 | 0.0 | 0.898 | 0.644 | 28.32616 | `results\cloudgpt\E2_gpt_5_5_20260424_c5_beta1.npz` |
| 1.5 | 0.0 | 0.926 | 0.644 | 28.32616 | `results\cloudgpt\E2_gpt_5_5_20260424_c5_beta1p5.npz` |

## Best hpsmg_plus

file: `results\cloudgpt\E2_gpt_5_5_20260424_c5_beta1.npz`
beta: `1.0`
final_regret: `{'hpsmg_plus': 0.898, 'hpsmg': 0.644, 'oracle': 0.0, 'random': 28.32616}`

## Audit

```text
backend=cloudgpt_live
tid_min_gap=0.0799
altruistic_builder: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
conditional_cooperator: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
risk_averse_balancer: mean_best_contribution=0.750 best_by_player=0.75,1.00,0.50
free_rider: mean_best_contribution=0.000 best_by_player=0.00,0.00,0.00
```
