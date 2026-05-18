# Live Calibration Overnight Summary

calibration: `calibration_cloudgpt_multi_model_fast4_8algos_Kimi_K2_6_c3.npy`
tid_min_gap: `0.0790`
new_live_cells: `48`
parse_failure_count: `0`

## E2 beta sweep

| beta | oracle | hpsmg_plus | hpsmg | joint_psrl | map_greedy | psrl_notype | iql | random | file |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0.0 | 0.0 | 0.992 | 0.644 | 1.55 | 0.854 | 19.326 | 27.347846 | 29.746521 | `results\cloudgpt\E2_Kimi_K2_6_c3_beta0.npz` |
| 0.05 | 0.0 | 0.992 | 0.644 | 1.55 | 0.854 | 19.326 | 27.347846 | 29.746521 | `results\cloudgpt\E2_Kimi_K2_6_c3_beta0p05.npz` |
| 0.1 | 0.0 | 0.992 | 0.644 | 1.55 | 0.854 | 19.326 | 27.347846 | 29.746521 | `results\cloudgpt\E2_Kimi_K2_6_c3_beta0p1.npz` |
| 0.25 | 0.0 | 0.992 | 0.644 | 1.55 | 0.854 | 19.326 | 27.347846 | 29.746521 | `results\cloudgpt\E2_Kimi_K2_6_c3_beta0p25.npz` |
| 0.5 | 0.0 | 1.016 | 0.644 | 1.55 | 0.854 | 19.326 | 27.347846 | 29.746521 | `results\cloudgpt\E2_Kimi_K2_6_c3_beta0p5.npz` |
| 0.75 | 0.0 | 1.002 | 0.644 | 1.55 | 0.854 | 19.326 | 27.347846 | 29.746521 | `results\cloudgpt\E2_Kimi_K2_6_c3_beta0p75.npz` |
| 1.0 | 0.0 | 0.906 | 0.644 | 1.55 | 0.854 | 19.326 | 27.347846 | 29.746521 | `results\cloudgpt\E2_Kimi_K2_6_c3_beta1.npz` |
| 1.5 | 0.0 | 0.934 | 0.644 | 1.55 | 0.854 | 19.326 | 27.347846 | 29.746521 | `results\cloudgpt\E2_Kimi_K2_6_c3_beta1p5.npz` |

## Best hpsmg_plus

file: `results\cloudgpt\E2_Kimi_K2_6_c3_beta1.npz`
beta: `1.0`
final_regret: `{'hpsmg_plus': 0.906, 'hpsmg': 0.644, 'joint_psrl': 1.55, 'map_greedy': 0.854, 'psrl_notype': 19.326, 'iql': 27.347846, 'random': 29.746521, 'oracle': 0.0}`

## Audit

```text
backend=cloudgpt_live
tid_min_gap=0.0790
altruistic_builder: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
conditional_cooperator: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
risk_averse_balancer: mean_best_contribution=0.750 best_by_player=0.75,1.00,0.50
free_rider: mean_best_contribution=0.333 best_by_player=0.00,0.00,1.00
```
