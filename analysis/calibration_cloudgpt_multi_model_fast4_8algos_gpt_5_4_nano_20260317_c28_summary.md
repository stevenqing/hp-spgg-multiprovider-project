# Live Calibration Overnight Summary

calibration: `calibration_cloudgpt_multi_model_fast4_8algos_gpt_5_4_nano_20260317_c28.npy`
tid_min_gap: `0.0992`
new_live_cells: `48`
parse_failure_count: `0`

## E2 beta sweep

| beta | oracle | hpsmg_plus | hpsmg | joint_psrl | map_greedy | psrl_notype | iql | random | file |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0.0 | 0.0 | 0.632 | 0.632 | 1.416 | 0.712 | 16.418 | 29.338 | 23.548 | `results\cloudgpt\E2_gpt_5_4_nano_20260317_c28_beta0.npz` |
| 0.05 | 0.0 | 0.632 | 0.632 | 1.416 | 0.712 | 16.418 | 29.338 | 23.548 | `results\cloudgpt\E2_gpt_5_4_nano_20260317_c28_beta0p05.npz` |
| 0.1 | 0.0 | 0.632 | 0.632 | 1.416 | 0.712 | 16.418 | 29.338 | 23.548 | `results\cloudgpt\E2_gpt_5_4_nano_20260317_c28_beta0p1.npz` |
| 0.25 | 0.0 | 0.632 | 0.632 | 1.416 | 0.712 | 16.418 | 29.338 | 23.548 | `results\cloudgpt\E2_gpt_5_4_nano_20260317_c28_beta0p25.npz` |
| 0.5 | 0.0 | 0.632 | 0.632 | 1.416 | 0.712 | 16.418 | 29.338 | 23.548 | `results\cloudgpt\E2_gpt_5_4_nano_20260317_c28_beta0p5.npz` |
| 0.75 | 0.0 | 0.632 | 0.632 | 1.416 | 0.712 | 16.418 | 29.338 | 23.548 | `results\cloudgpt\E2_gpt_5_4_nano_20260317_c28_beta0p75.npz` |
| 1.0 | 0.0 | 0.632 | 0.632 | 1.416 | 0.712 | 16.418 | 29.338 | 23.548 | `results\cloudgpt\E2_gpt_5_4_nano_20260317_c28_beta1.npz` |
| 1.5 | 0.0 | 0.632 | 0.632 | 1.416 | 0.712 | 16.418 | 29.338 | 23.548 | `results\cloudgpt\E2_gpt_5_4_nano_20260317_c28_beta1p5.npz` |

## Best hpsmg_plus

file: `results\cloudgpt\E2_gpt_5_4_nano_20260317_c28_beta0.npz`
beta: `0.0`
final_regret: `{'hpsmg_plus': 0.632, 'hpsmg': 0.632, 'joint_psrl': 1.416, 'map_greedy': 0.712, 'psrl_notype': 16.418, 'iql': 29.338, 'random': 23.548, 'oracle': 0.0}`

## Audit

```text
backend=cloudgpt_live
tid_min_gap=0.0992
altruistic_builder: mean_best_contribution=1.000 best_by_player=1.00,1.00,1.00
conditional_cooperator: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
risk_averse_balancer: mean_best_contribution=0.833 best_by_player=0.75,1.00,0.75
free_rider: mean_best_contribution=0.000 best_by_player=0.00,0.00,0.00
```
