# External LLM Baseline Summary

Source: `results/cloudgpt/E2_external_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5.npz`


- Backend: `cloudgpt`
- Model: `gpt-5.4-nano-20260317`
- K: `20`
- Seeds: `5`
- ECON rounds: `3`

| Rank | Algorithm | Final cumulative regret mean | Std | Mean per-round regret | Mean welfare |
|---:|---|---:|---:|---:|---:|
| 1 | `atom_tom0` | 4.0800 | 4.9406 | 0.2040 | 2.5860 |
| 2 | `atom_adaptive_hedge` | 7.6530 | 4.9582 | 0.3826 | 2.4414 |
| 3 | `atom_tom2` | 10.2000 | 8.8254 | 0.5100 | 2.2440 |
| 4 | `atom_tom1` | 13.4726 | 6.5896 | 0.6736 | 2.0444 |
| 5 | `econ_bne` | 14.8800 | 2.7527 | 0.7440 | 1.9480 |
| 6 | `atom_adaptive_ftl` | 14.8895 | 2.8454 | 0.7445 | 1.9995 |
