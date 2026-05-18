# Live Calibration Overnight Summary

calibration: `calibration_cloudgpt_live_continued.npy`
tid_min_gap: `0.0705`
new_live_cells: `132`
parse_failure_count: `0`

## E2 beta sweep

| beta | hpsmg_plus | hpsmg | oracle | random | file |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1.0 | 0.87 | 0.08 | 0.0 | 13.877972 | `results\cloudgpt\E2_sanity_live_continued.npz` |

## Best hpsmg_plus

file: `results\cloudgpt\E2_sanity_live_continued.npz`
beta: `1.0`
final_regret: `{'hpsmg_plus': 0.87, 'hpsmg': 0.08, 'oracle': 0.0, 'random': 13.877972}`

## Audit

```text
backend=cloudgpt_live
tid_min_gap=0.0705
altruistic_builder: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
conditional_cooperator: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
risk_averse_balancer: mean_best_contribution=0.750 best_by_player=0.75,1.00,0.50
free_rider: mean_best_contribution=0.000 best_by_player=0.00,0.00,0.00
```
