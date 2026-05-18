# Live Calibration Overnight Summary

calibration: `calibration_cloudgpt_multi_model_fast4_Llama_4_Maverick_17B_128E_Instruct_FP8_c4.npy`
tid_min_gap: `0.0864`
new_live_cells: `41`
parse_failure_count: `7`

## E2 beta sweep

| beta | hpsmg_plus | hpsmg | oracle | random | file |
| ---: | ---: | ---: | ---: | ---: | --- |
| 0.0 | 2.836 | 0.644 | 0.0 | 26.794828 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c4_beta0.npz` |
| 0.05 | 2.816 | 0.644 | 0.0 | 26.794828 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c4_beta0p05.npz` |
| 0.1 | 2.816 | 0.644 | 0.0 | 26.794828 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c4_beta0p1.npz` |
| 0.25 | 2.734 | 0.644 | 0.0 | 26.794828 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c4_beta0p25.npz` |
| 0.5 | 1.152 | 0.644 | 0.0 | 26.794828 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c4_beta0p5.npz` |
| 0.75 | 1.124 | 0.644 | 0.0 | 26.794828 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c4_beta0p75.npz` |
| 1.0 | 1.028 | 0.644 | 0.0 | 26.794828 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c4_beta1.npz` |
| 1.5 | 0.978 | 0.644 | 0.0 | 26.794828 | `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c4_beta1p5.npz` |

## Best hpsmg_plus

file: `results\cloudgpt\E2_Llama_4_Maverick_17B_128E_Instruct_FP8_c4_beta1p5.npz`
beta: `1.5`
final_regret: `{'hpsmg_plus': 0.978, 'hpsmg': 0.644, 'oracle': 0.0, 'random': 26.794828}`

## Audit

```text
backend=cloudgpt_live
tid_min_gap=0.0864
altruistic_builder: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
conditional_cooperator: mean_best_contribution=0.917 best_by_player=1.00,0.75,1.00
risk_averse_balancer: mean_best_contribution=0.750 best_by_player=0.75,1.00,0.50
free_rider: mean_best_contribution=0.000 best_by_player=0.00,0.00,0.00
```
