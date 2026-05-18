# Live Calibration Overnight Summary

calibration: `calibration_cloudgpt_multi_model_fast4_8algos_Llama_4_Maverick_17B_128E_Instruct_FP8_c6.npy`
tid_min_gap: `0.1025`
new_live_cells: `48`
parse_failure_count: `0`

## E2 beta sweep

| beta | oracle | hpsmg_plus | hpsmg | joint_psrl | map_greedy | psrl_notype | iql | random | file |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0.0 | 0.0 | 3.596 | 0.732 | 1.326 | 0.854 | 20.272 | 27.344287 | 28.398559 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c6_beta0.npz` |
| 0.05 | 0.0 | 3.576 | 0.732 | 1.326 | 0.854 | 20.272 | 27.344287 | 28.398559 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c6_beta0p05.npz` |
| 0.1 | 0.0 | 3.576 | 0.732 | 1.326 | 0.854 | 20.272 | 27.344287 | 28.398559 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c6_beta0p1.npz` |
| 0.25 | 0.0 | 3.494 | 0.732 | 1.326 | 0.854 | 20.272 | 27.344287 | 28.398559 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c6_beta0p25.npz` |
| 0.5 | 0.0 | 1.912 | 0.732 | 1.326 | 0.854 | 20.272 | 27.344287 | 28.398559 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c6_beta0p5.npz` |
| 0.75 | 0.0 | 1.884 | 0.732 | 1.326 | 0.854 | 20.272 | 27.344287 | 28.398559 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c6_beta0p75.npz` |
| 1.0 | 0.0 | 1.788 | 0.732 | 1.326 | 0.854 | 20.272 | 27.344287 | 28.398559 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c6_beta1.npz` |
| 1.5 | 0.0 | 0.904 | 0.732 | 1.326 | 0.854 | 20.272 | 27.344287 | 28.398559 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c6_beta1p5.npz` |

## Best hpsmg_plus

file: `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c6_beta1p5.npz`
beta: `1.5`
final_regret: `{'hpsmg_plus': 0.904, 'hpsmg': 0.732, 'joint_psrl': 1.326, 'map_greedy': 0.854, 'psrl_notype': 20.272, 'iql': 27.344287, 'random': 28.398559, 'oracle': 0.0}`

## Audit

```text
backend=cloudgpt_live
tid_min_gap=0.1025
altruistic_builder: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
conditional_cooperator: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
risk_averse_balancer: mean_best_contribution=0.750 best_by_player=0.75,1.00,0.50
free_rider: mean_best_contribution=0.000 best_by_player=0.00,0.00,0.00
```
