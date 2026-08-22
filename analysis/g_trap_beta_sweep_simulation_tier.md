# G_trap Beta Sweep Simulation Tier

Metric: final cumulative regret on `G_trap`; lower is better.

Configuration:
- Calibration: `calibration_cloudgpt_trap.npy`
- Runner: `python -m llm_hpgg.run_experiment`
- Algorithms in raw NPZ: `hpsmg_plus`, `hpsmg`, `oracle`
- Primary reported row below: `hpsmg_plus`
- `K=50`, `seeds=8`
- Beta grid: `{0, 0.3, 1, 3, 10}`

## Summary

| beta | mean final regret | std | seed count | source |
|---:|---:|---:|---:|---|
| 0 | 0.0472 | 0.0234 | 8 | `results/cloudgpt/G_trap_beta0_K50_s8.npz` |
| 0.3 | 0.0466 | 0.0233 | 8 | `results/cloudgpt/G_trap_beta0p3_K50_s8.npz` |
| 1 | 0.0493 | 0.0225 | 8 | `results/cloudgpt/G_trap_beta1_K50_s8.npz` |
| 3 | 0.6757 | 0.8488 | 8 | `results/cloudgpt/G_trap_beta3_K50_s8.npz` |
| 10 | 1.2309 | 1.4210 | 8 | `results/cloudgpt/G_trap_beta10_K50_s8.npz` |

## Per-Seed Matrix

| beta | seed0 | seed1 | seed2 | seed3 | seed4 | seed5 | seed6 | seed7 | mean | std |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.0382 | 0.0303 | 0.0517 | 0.0663 | 0.0850 | 0.0634 | 0.0041 | 0.0382 | 0.0472 | 0.0234 |
| 0.3 | 0.0382 | 0.0303 | 0.0474 | 0.0663 | 0.0850 | 0.0634 | 0.0041 | 0.0382 | 0.0466 | 0.0233 |
| 1 | 0.0382 | 0.0517 | 0.0474 | 0.0663 | 0.0850 | 0.0634 | 0.0041 | 0.0382 | 0.0493 | 0.0225 |
| 3 | 2.0287 | 1.0803 | 0.0474 | 0.0663 | 0.0850 | 0.0634 | 0.0055 | 2.0287 | 0.6757 | 0.8488 |
| 10 | 2.0690 | 1.1648 | 0.0474 | 0.0663 | 0.0850 | 0.0634 | 4.2822 | 2.0690 | 1.2309 | 1.4210 |

## Long Form: hpsmg_plus

| graph | beta | algorithm | seed | K | final_cumulative_regret | source |
|---|---:|---|---:|---:|---:|---|
| G_trap | 0 | hpsmg_plus | 0 | 50 | 0.03824900 | `results/cloudgpt/G_trap_beta0_K50_s8.npz` |
| G_trap | 0 | hpsmg_plus | 1 | 50 | 0.03027404 | `results/cloudgpt/G_trap_beta0_K50_s8.npz` |
| G_trap | 0 | hpsmg_plus | 2 | 50 | 0.05171785 | `results/cloudgpt/G_trap_beta0_K50_s8.npz` |
| G_trap | 0 | hpsmg_plus | 3 | 50 | 0.06626882 | `results/cloudgpt/G_trap_beta0_K50_s8.npz` |
| G_trap | 0 | hpsmg_plus | 4 | 50 | 0.08495601 | `results/cloudgpt/G_trap_beta0_K50_s8.npz` |
| G_trap | 0 | hpsmg_plus | 5 | 50 | 0.06339015 | `results/cloudgpt/G_trap_beta0_K50_s8.npz` |
| G_trap | 0 | hpsmg_plus | 6 | 50 | 0.00412266 | `results/cloudgpt/G_trap_beta0_K50_s8.npz` |
| G_trap | 0 | hpsmg_plus | 7 | 50 | 0.03824900 | `results/cloudgpt/G_trap_beta0_K50_s8.npz` |
| G_trap | 0.3 | hpsmg_plus | 0 | 50 | 0.03824900 | `results/cloudgpt/G_trap_beta0p3_K50_s8.npz` |
| G_trap | 0.3 | hpsmg_plus | 1 | 50 | 0.03027404 | `results/cloudgpt/G_trap_beta0p3_K50_s8.npz` |
| G_trap | 0.3 | hpsmg_plus | 2 | 50 | 0.04742121 | `results/cloudgpt/G_trap_beta0p3_K50_s8.npz` |
| G_trap | 0.3 | hpsmg_plus | 3 | 50 | 0.06626882 | `results/cloudgpt/G_trap_beta0p3_K50_s8.npz` |
| G_trap | 0.3 | hpsmg_plus | 4 | 50 | 0.08495601 | `results/cloudgpt/G_trap_beta0p3_K50_s8.npz` |
| G_trap | 0.3 | hpsmg_plus | 5 | 50 | 0.06339015 | `results/cloudgpt/G_trap_beta0p3_K50_s8.npz` |
| G_trap | 0.3 | hpsmg_plus | 6 | 50 | 0.00412266 | `results/cloudgpt/G_trap_beta0p3_K50_s8.npz` |
| G_trap | 0.3 | hpsmg_plus | 7 | 50 | 0.03824900 | `results/cloudgpt/G_trap_beta0p3_K50_s8.npz` |
| G_trap | 1 | hpsmg_plus | 0 | 50 | 0.03824900 | `results/cloudgpt/G_trap_beta1_K50_s8.npz` |
| G_trap | 1 | hpsmg_plus | 1 | 50 | 0.05170398 | `results/cloudgpt/G_trap_beta1_K50_s8.npz` |
| G_trap | 1 | hpsmg_plus | 2 | 50 | 0.04742121 | `results/cloudgpt/G_trap_beta1_K50_s8.npz` |
| G_trap | 1 | hpsmg_plus | 3 | 50 | 0.06626882 | `results/cloudgpt/G_trap_beta1_K50_s8.npz` |
| G_trap | 1 | hpsmg_plus | 4 | 50 | 0.08495601 | `results/cloudgpt/G_trap_beta1_K50_s8.npz` |
| G_trap | 1 | hpsmg_plus | 5 | 50 | 0.06339015 | `results/cloudgpt/G_trap_beta1_K50_s8.npz` |
| G_trap | 1 | hpsmg_plus | 6 | 50 | 0.00412266 | `results/cloudgpt/G_trap_beta1_K50_s8.npz` |
| G_trap | 1 | hpsmg_plus | 7 | 50 | 0.03824900 | `results/cloudgpt/G_trap_beta1_K50_s8.npz` |
| G_trap | 3 | hpsmg_plus | 0 | 50 | 2.02867288 | `results/cloudgpt/G_trap_beta3_K50_s8.npz` |
| G_trap | 3 | hpsmg_plus | 1 | 50 | 1.08034076 | `results/cloudgpt/G_trap_beta3_K50_s8.npz` |
| G_trap | 3 | hpsmg_plus | 2 | 50 | 0.04742121 | `results/cloudgpt/G_trap_beta3_K50_s8.npz` |
| G_trap | 3 | hpsmg_plus | 3 | 50 | 0.06626882 | `results/cloudgpt/G_trap_beta3_K50_s8.npz` |
| G_trap | 3 | hpsmg_plus | 4 | 50 | 0.08495601 | `results/cloudgpt/G_trap_beta3_K50_s8.npz` |
| G_trap | 3 | hpsmg_plus | 5 | 50 | 0.06339015 | `results/cloudgpt/G_trap_beta3_K50_s8.npz` |
| G_trap | 3 | hpsmg_plus | 6 | 50 | 0.00549688 | `results/cloudgpt/G_trap_beta3_K50_s8.npz` |
| G_trap | 3 | hpsmg_plus | 7 | 50 | 2.02867288 | `results/cloudgpt/G_trap_beta3_K50_s8.npz` |
| G_trap | 10 | hpsmg_plus | 0 | 50 | 2.06901715 | `results/cloudgpt/G_trap_beta10_K50_s8.npz` |
| G_trap | 10 | hpsmg_plus | 1 | 50 | 1.16484390 | `results/cloudgpt/G_trap_beta10_K50_s8.npz` |
| G_trap | 10 | hpsmg_plus | 2 | 50 | 0.04742121 | `results/cloudgpt/G_trap_beta10_K50_s8.npz` |
| G_trap | 10 | hpsmg_plus | 3 | 50 | 0.06626882 | `results/cloudgpt/G_trap_beta10_K50_s8.npz` |
| G_trap | 10 | hpsmg_plus | 4 | 50 | 0.08495601 | `results/cloudgpt/G_trap_beta10_K50_s8.npz` |
| G_trap | 10 | hpsmg_plus | 5 | 50 | 0.06339015 | `results/cloudgpt/G_trap_beta10_K50_s8.npz` |
| G_trap | 10 | hpsmg_plus | 6 | 50 | 4.28220043 | `results/cloudgpt/G_trap_beta10_K50_s8.npz` |
| G_trap | 10 | hpsmg_plus | 7 | 50 | 2.06901715 | `results/cloudgpt/G_trap_beta10_K50_s8.npz` |
