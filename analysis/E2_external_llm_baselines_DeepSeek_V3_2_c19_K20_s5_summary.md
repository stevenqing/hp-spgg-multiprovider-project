# External LLM Baseline Summary

Source: `results/cloudgpt/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz`


- Backend: `cloudgpt`
- Model: `DeepSeek-V3.2`
- K: `20`
- Seeds: `5`
- ECON rounds: `3`

| Rank | Algorithm | Final cumulative regret mean | Std | Mean per-round regret | Mean welfare |
|---:|---|---:|---:|---:|---:|
| 1 | `econ_bne` | 3.9900 | 3.4136 | 0.1995 | 2.6105 |
| 2 | `atom_adaptive_hedge` | 4.7900 | 4.5089 | 0.2395 | 2.6605 |
| 3 | `atom_tom0` | 6.0000 | 7.4565 | 0.3000 | 2.5900 |
| 4 | `atom_tom2` | 13.4020 | 10.3200 | 0.6701 | 2.2139 |
| 5 | `atom_adaptive_ftl` | 14.9440 | 1.4313 | 0.7472 | 2.0968 |
| 6 | `atom_tom1` | 16.6760 | 8.2004 | 0.8338 | 2.0182 |
