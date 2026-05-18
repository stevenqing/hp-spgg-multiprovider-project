# Live Calibration Overnight Summary

calibration: `calibration_cloudgpt_multi_model_fast4_8algos_Llama_4_Maverick_17B_128E_Instruct_FP8_c17.npy`
tid_min_gap: `0.1158`
new_live_cells: `37`
parse_failure_count: `0`

## E2 beta sweep

| beta | oracle | hpsmg_plus | hpsmg | joint_psrl | map_greedy | psrl_notype | iql | random | file |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0.0 | 0.0 | 0.312 | 0.732 | 1.194 | 0.974 | 11.022 | 27.526 | 25.503382 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c17_beta0.npz` |
| 0.05 | 0.0 | 0.312 | 0.732 | 1.194 | 0.974 | 11.022 | 27.526 | 25.503382 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c17_beta0p05.npz` |
| 0.1 | 0.0 | 0.312 | 0.732 | 1.194 | 0.974 | 11.022 | 27.526 | 25.503382 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c17_beta0p1.npz` |
| 0.25 | 0.0 | 0.312 | 0.732 | 1.194 | 0.974 | 11.022 | 27.526 | 25.503382 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c17_beta0p25.npz` |
| 0.5 | 0.0 | 0.312 | 0.732 | 1.194 | 0.974 | 11.022 | 27.526 | 25.503382 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c17_beta0p5.npz` |
| 0.75 | 0.0 | 0.312 | 0.732 | 1.194 | 0.974 | 11.022 | 27.526 | 25.503382 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c17_beta0p75.npz` |
| 1.0 | 0.0 | 0.312 | 0.732 | 1.194 | 0.974 | 11.022 | 27.526 | 25.503382 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c17_beta1.npz` |
| 1.5 | 0.0 | 0.312 | 0.732 | 1.194 | 0.974 | 11.022 | 27.526 | 25.503382 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c17_beta1p5.npz` |

## Best hpsmg_plus

file: `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c17_beta0.npz`
beta: `0.0`
final_regret: `{'hpsmg_plus': 0.312, 'hpsmg': 0.732, 'joint_psrl': 1.194, 'map_greedy': 0.974, 'psrl_notype': 11.022, 'iql': 27.526, 'random': 25.503382, 'oracle': 0.0}`

## Audit

```text
backend=cloudgpt_live
tid_min_gap=0.1158
altruistic_builder: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
conditional_cooperator: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
risk_averse_balancer: mean_best_contribution=0.500 best_by_player=0.50,0.50,0.50
free_rider: mean_best_contribution=0.000 best_by_player=0.00,0.00,0.00
```
