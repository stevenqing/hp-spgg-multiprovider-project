# External LLM Baseline Summary

Source: `results/cloudgpt/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s3.npz`


- Backend: `cloudgpt`
- Model: `DeepSeek-V3.2`
- K: `20`
- Seeds: `3`
- ECON rounds: `3`

| Rank | Algorithm | Final cumulative regret mean | Std | Mean per-round regret | Mean welfare |
|---:|---|---:|---:|---:|---:|
| 1 | `atom_adaptive_hedge` | 3.7833 | 4.2249 | 0.1892 | 2.7608 |
| 2 | `econ_bne` | 3.9800 | 4.3298 | 0.1990 | 2.6677 |
| 3 | `atom_tom0` | 10.0000 | 7.2572 | 0.5000 | 2.3500 |
| 4 | `atom_tom2` | 11.1167 | 6.2414 | 0.5558 | 2.3175 |
| 5 | `atom_adaptive_ftl` | 14.4700 | 1.6293 | 0.7235 | 2.0832 |
| 6 | `atom_tom1` | 17.1867 | 0.5592 | 0.8593 | 2.0073 |
