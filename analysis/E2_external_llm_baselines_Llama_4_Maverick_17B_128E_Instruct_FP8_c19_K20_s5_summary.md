# External LLM Baseline Summary

Source: `results/cloudgpt/E2_external_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5.npz`


- Backend: `cloudgpt`
- Model: `Llama-4-Maverick-17B-128E-Instruct-FP8`
- K: `20`
- Seeds: `5`
- ECON rounds: `3`

| Rank | Algorithm | Final cumulative regret mean | Std | Mean per-round regret | Mean welfare |
|---:|---|---:|---:|---:|---:|
| 1 | `econ_bne` | 3.3820 | 4.5338 | 0.1691 | 2.6029 |
| 2 | `atom_adaptive_hedge` | 7.0060 | 4.5831 | 0.3503 | 2.5237 |
| 3 | `atom_tom0` | 7.2400 | 7.7886 | 0.3620 | 2.5240 |
| 4 | `atom_tom2` | 11.8660 | 9.3250 | 0.5933 | 2.2507 |
| 5 | `atom_adaptive_ftl` | 13.9220 | 2.6571 | 0.6961 | 2.0659 |
| 6 | `atom_tom1` | 15.7100 | 7.9321 | 0.7855 | 2.0825 |
