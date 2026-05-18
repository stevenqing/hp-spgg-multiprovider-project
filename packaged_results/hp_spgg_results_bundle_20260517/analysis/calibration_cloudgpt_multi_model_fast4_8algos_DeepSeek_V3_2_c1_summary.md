# Live Calibration Overnight Summary

calibration: `calibration_cloudgpt_multi_model_fast4_8algos_DeepSeek_V3_2_c1.npy`
tid_min_gap: `0.0922`
new_live_cells: `48`
parse_failure_count: `0`

## E2 beta sweep

| beta | oracle | hpsmg_plus | hpsmg | joint_psrl | map_greedy | psrl_notype | iql | random | file |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0.0 | 0.0 | 1.07 | 0.784 | 1.848 | 0.882 | 17.126 | 29.891846 | 29.970521 | `results\cloudgpt\E2_DeepSeek_V3_2_c1_beta0.npz` |
| 0.05 | 0.0 | 1.07 | 0.784 | 1.848 | 0.882 | 17.126 | 29.891846 | 29.970521 | `results\cloudgpt\E2_DeepSeek_V3_2_c1_beta0p05.npz` |
| 0.1 | 0.0 | 1.07 | 0.784 | 1.848 | 0.882 | 17.126 | 29.891846 | 29.970521 | `results\cloudgpt\E2_DeepSeek_V3_2_c1_beta0p1.npz` |
| 0.25 | 0.0 | 1.07 | 0.784 | 1.848 | 0.882 | 17.126 | 29.891846 | 29.970521 | `results\cloudgpt\E2_DeepSeek_V3_2_c1_beta0p25.npz` |
| 0.5 | 0.0 | 1.07 | 0.784 | 1.848 | 0.882 | 17.126 | 29.891846 | 29.970521 | `results\cloudgpt\E2_DeepSeek_V3_2_c1_beta0p5.npz` |
| 0.75 | 0.0 | 1.07 | 0.784 | 1.848 | 0.882 | 17.126 | 29.891846 | 29.970521 | `results\cloudgpt\E2_DeepSeek_V3_2_c1_beta0p75.npz` |
| 1.0 | 0.0 | 0.878 | 0.784 | 1.848 | 0.882 | 17.126 | 29.891846 | 29.970521 | `results\cloudgpt\E2_DeepSeek_V3_2_c1_beta1.npz` |
| 1.5 | 0.0 | 1.096 | 0.784 | 1.848 | 0.882 | 17.126 | 29.891846 | 29.970521 | `results\cloudgpt\E2_DeepSeek_V3_2_c1_beta1p5.npz` |

## Best hpsmg_plus

file: `results\cloudgpt\E2_DeepSeek_V3_2_c1_beta1.npz`
beta: `1.0`
final_regret: `{'hpsmg_plus': 0.878, 'hpsmg': 0.784, 'joint_psrl': 1.848, 'map_greedy': 0.882, 'psrl_notype': 17.126, 'iql': 29.891846, 'random': 29.970521, 'oracle': 0.0}`

## Audit

```text
backend=cloudgpt_live
tid_min_gap=0.0922
altruistic_builder: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
conditional_cooperator: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
risk_averse_balancer: mean_best_contribution=0.250 best_by_player=0.25,0.25,0.25
free_rider: mean_best_contribution=0.000 best_by_player=0.00,0.00,0.00
```
