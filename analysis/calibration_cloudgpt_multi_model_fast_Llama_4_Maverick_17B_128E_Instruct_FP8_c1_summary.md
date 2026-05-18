# Live Calibration Overnight Summary

calibration: `calibration_cloudgpt_multi_model_fast_Llama_4_Maverick_17B_128E_Instruct_FP8_c1.npy`
tid_min_gap: `0.0785`
new_live_cells: `45`
parse_failure_count: `3`

## E2 beta sweep

| beta | hpsmg_plus | hpsmg | oracle | random | file |
| ---: | ---: | ---: | ---: | ---: | --- |
| 0.0 | 1.432 | 0.644 | 0.0 | 27.573829 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c1_beta0.npz` |
| 0.05 | 1.432 | 0.644 | 0.0 | 27.573829 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c1_beta0p05.npz` |
| 0.1 | 1.432 | 0.644 | 0.0 | 27.573829 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c1_beta0p1.npz` |
| 0.25 | 1.432 | 0.644 | 0.0 | 27.573829 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c1_beta0p25.npz` |
| 0.5 | 1.456 | 0.644 | 0.0 | 27.573829 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c1_beta0p5.npz` |
| 0.75 | 1.046 | 0.644 | 0.0 | 27.573829 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c1_beta0p75.npz` |
| 1.0 | 0.95 | 0.644 | 0.0 | 27.573829 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c1_beta1.npz` |
| 1.5 | 0.978 | 0.644 | 0.0 | 27.573829 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c1_beta1p5.npz` |

## Best hpsmg_plus

file: `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c1_beta1.npz`
beta: `1.0`
final_regret: `{'hpsmg_plus': 0.95, 'hpsmg': 0.644, 'oracle': 0.0, 'random': 27.573829}`

## Audit

```text
backend=cloudgpt_live
tid_min_gap=0.0785
altruistic_builder: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
conditional_cooperator: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
risk_averse_balancer: mean_best_contribution=0.750 best_by_player=0.75,1.00,0.50
free_rider: mean_best_contribution=0.000 best_by_player=0.00,0.00,0.00
```
