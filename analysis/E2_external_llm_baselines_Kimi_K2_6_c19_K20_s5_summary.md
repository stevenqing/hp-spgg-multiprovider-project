# External LLM Baseline Summary

Source: `results/cloudgpt/E2_external_llm_baselines_Kimi_K2_6_c19_K20_s5.npz`


- Backend: `cloudgpt`
- Model: `Kimi-K2.6`
- K: `20`
- Seeds: `5`
- ECON rounds: `3`

| Rank | Algorithm | Final cumulative regret mean | Std | Mean per-round regret | Mean welfare |
|---:|---|---:|---:|---:|---:|
| 1 | `atom_adaptive_hedge` | 7.4840 | 4.0956 | 0.3742 | 2.4498 |
| 2 | `econ_bne` | 10.4880 | 6.0321 | 0.5244 | 2.1676 |
| 3 | `atom_tom2` | 10.5840 | 8.2186 | 0.5292 | 2.2848 |
| 4 | `atom_tom0` | 10.6720 | 6.3559 | 0.5336 | 2.2564 |
| 5 | `atom_tom1` | 14.0480 | 6.9242 | 0.7024 | 2.0376 |
| 6 | `atom_adaptive_ftl` | 14.2800 | 2.7749 | 0.7140 | 2.0300 |
