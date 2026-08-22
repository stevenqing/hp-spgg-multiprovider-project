# Live Calibration Overnight Summary

calibration: `calibration_anthropic.npy`
tid_min_gap: `0.0519`
new_live_cells: `48`
parse_failure_count: `0`

## E2 beta sweep

| beta | oracle | hpsmg_plus | hpsmg | joint_psrl | map_greedy | psrl_notype | iql | random | file |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.088508 | 5.55027 | 2.389837 | `results\smoke_8_algos.npz` |

## Best hpsmg_plus

file: `results\smoke_8_algos.npz`
beta: `1.0`
final_regret: `{'hpsmg_plus': 0.0, 'hpsmg': 0.0, 'joint_psrl': 0.0, 'map_greedy': 0.0, 'psrl_notype': 0.088508, 'iql': 5.55027, 'random': 2.389837, 'oracle': 0.0}`

## Audit

```text
backend=cloudgpt_live
tid_min_gap=0.0795
altruistic_builder: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
conditional_cooperator: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
risk_averse_balancer: mean_best_contribution=0.750 best_by_player=0.75,1.00,0.50
free_rider: mean_best_contribution=0.000 best_by_player=0.00,0.00,0.00
```
