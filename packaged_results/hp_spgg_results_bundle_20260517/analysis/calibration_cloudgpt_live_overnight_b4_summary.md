# Live Calibration Overnight Summary

calibration: `calibration_cloudgpt_live_overnight_b4.npy`
tid_min_gap: `0.0901`
new_live_cells: `48`
parse_failure_count: `0`

## E2 beta sweep

| beta | hpsmg_plus | hpsmg | oracle | random | file |
| ---: | ---: | ---: | ---: | ---: | --- |
| 0.0 | 0.878 | 0.728 | 0.0 | 27.792098 | `results\cloudgpt\E2_live_b4_beta0.npz` |
| 0.05 | 0.878 | 0.728 | 0.0 | 27.792098 | `results\cloudgpt\E2_live_b4_beta0p05.npz` |
| 0.1 | 0.878 | 0.728 | 0.0 | 27.792098 | `results\cloudgpt\E2_live_b4_beta0p1.npz` |
| 0.25 | 0.834 | 0.728 | 0.0 | 27.792098 | `results\cloudgpt\E2_live_b4_beta0p25.npz` |
| 0.5 | 0.878 | 0.728 | 0.0 | 27.792098 | `results\cloudgpt\E2_live_b4_beta0p5.npz` |
| 0.75 | 0.878 | 0.728 | 0.0 | 27.792098 | `results\cloudgpt\E2_live_b4_beta0p75.npz` |
| 1.0 | 1.006 | 0.728 | 0.0 | 27.792098 | `results\cloudgpt\E2_live_b4_beta1.npz` |
| 1.5 | 1.03 | 0.728 | 0.0 | 27.792098 | `results\cloudgpt\E2_live_b4_beta1p5.npz` |

## Best hpsmg_plus

file: `results\cloudgpt\E2_live_b4_beta0p25.npz`
beta: `0.25`
final_regret: `{'hpsmg_plus': 0.834, 'hpsmg': 0.728, 'oracle': 0.0, 'random': 27.792098}`

## Audit

```text
backend=cloudgpt_live
tid_min_gap=0.0901
altruistic_builder: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
conditional_cooperator: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
risk_averse_balancer: mean_best_contribution=0.667 best_by_player=0.50,1.00,0.50
free_rider: mean_best_contribution=0.000 best_by_player=0.00,0.00,0.00
```
