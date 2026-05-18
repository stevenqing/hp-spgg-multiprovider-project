# Live Calibration Overnight Summary

calibration: `calibration_cloudgpt_multi_model_fast4_8algos_gpt_5_4_nano_20260317_c26.npy`
tid_min_gap: `0.1021`
new_live_cells: `48`
parse_failure_count: `0`

## E2 beta sweep

| beta | oracle | hpsmg_plus | hpsmg | joint_psrl | map_greedy | psrl_notype | iql | random | file |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0.0 | 0.0 | 0.824 | 0.644 | 1.492 | 0.854 | 17.562 | 28.288 | 23.72 | `results\cloudgpt\E2_gpt_5_4_nano_20260317_c26_beta0.npz` |
| 0.05 | 0.0 | 0.824 | 0.644 | 1.492 | 0.854 | 17.562 | 28.288 | 23.72 | `results\cloudgpt\E2_gpt_5_4_nano_20260317_c26_beta0p05.npz` |
| 0.1 | 0.0 | 0.824 | 0.644 | 1.492 | 0.854 | 17.562 | 28.288 | 23.72 | `results\cloudgpt\E2_gpt_5_4_nano_20260317_c26_beta0p1.npz` |
| 0.25 | 0.0 | 0.824 | 0.644 | 1.492 | 0.854 | 17.562 | 28.288 | 23.72 | `results\cloudgpt\E2_gpt_5_4_nano_20260317_c26_beta0p25.npz` |
| 0.5 | 0.0 | 0.848 | 0.644 | 1.492 | 0.854 | 17.562 | 28.288 | 23.72 | `results\cloudgpt\E2_gpt_5_4_nano_20260317_c26_beta0p5.npz` |
| 0.75 | 0.0 | 0.906 | 0.644 | 1.492 | 0.854 | 17.562 | 28.288 | 23.72 | `results\cloudgpt\E2_gpt_5_4_nano_20260317_c26_beta0p75.npz` |
| 1.0 | 0.0 | 0.81 | 0.644 | 1.492 | 0.854 | 17.562 | 28.288 | 23.72 | `results\cloudgpt\E2_gpt_5_4_nano_20260317_c26_beta1.npz` |
| 1.5 | 0.0 | 0.838 | 0.644 | 1.492 | 0.854 | 17.562 | 28.288 | 23.72 | `results\cloudgpt\E2_gpt_5_4_nano_20260317_c26_beta1p5.npz` |

## Best hpsmg_plus

file: `results\cloudgpt\E2_gpt_5_4_nano_20260317_c26_beta1.npz`
beta: `1.0`
final_regret: `{'hpsmg_plus': 0.81, 'hpsmg': 0.644, 'joint_psrl': 1.492, 'map_greedy': 0.854, 'psrl_notype': 17.562, 'iql': 28.288, 'random': 23.72, 'oracle': 0.0}`

## Audit

```text
backend=cloudgpt_live
tid_min_gap=0.1021
altruistic_builder: mean_best_contribution=1.000 best_by_player=1.00,1.00,1.00
conditional_cooperator: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
risk_averse_balancer: mean_best_contribution=0.750 best_by_player=0.75,1.00,0.50
free_rider: mean_best_contribution=0.000 best_by_player=0.00,0.00,0.00
```
