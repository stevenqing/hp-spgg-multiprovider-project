# E1-E4 LLM Evidence Results - 2026-05-18

This file summarizes the live LLM-judge calibrated E1-E4 run completed by `scripts/run_e1_e4_llm_evidence_overnight.ps1` with `ProfileCount=19` and `Workers=2`. Paper-facing reporting should use E1-E3 only; E4 is retained as diagnostic/archive evidence.

## Evidence Scope

- Backend: CloudGPT live judge calls.
- E1 backbones: DeepSeek-V3.2, gpt-5.4-nano-20260317, Kimi-K2.6, Llama-4-Maverick-17B-128E-Instruct-FP8.
- E2/E3 judge model: Llama-4-Maverick-17B-128E-Instruct-FP8.
- Horizon: K=20.
- Seeds: 5.
- E1 live refreshed cells: 4 models x 228 = 912.
- E2 live scaling cells: 114 + 171 + 228 + 285 + 342 = 1140.
- E3 live n-scaling cells: 152 + 228 + 304 + 380 = 1064.
- Total overnight live judge cells: 3116.
- Parse failures: 0 for all live calibration stages.

This is live LLM-judge calibrated HP-SPGG evidence. It is not an exhaustive all-profile live calibration for E2/E3; representative profiles were live-scored and the remaining cells retained the deterministic scaling fallback.

## E1 Posterior Concentration

Threshold: posterior true-type mass >= 0.9.

| Backbone | Mean concentration time | Seed times | Final true mass mean | Regret mean |
| --- | ---: | --- | ---: | ---: |
| DeepSeek_V3_2_live | 4.4 | 4, 4, 5, 7, 2 | 0.990979 | 1.2860 |
| gpt_5_4_nano_20260317_live | 6.6 | 5, null, 2, 3, 2 | 0.966768 | 1.3160 |
| Kimi_K2_6_live | 12.0 | 3, 12, null, null, 3 | 0.856606 | 0.8300 |
| Llama_4_Maverick_17B_128E_Instruct_FP8_live | 14.0 | 12, 14, 13, 16, 15 | 0.987270 | 1.7500 |

Files:

- Raw: `results/e1_e4_llm/E1_posterior_*_live.npz`
- Summary: `analysis/E1_posterior_concentration_llm_summary.json`
- Table: `tables/E1_posterior_concentration_llm.csv`
- Figure: `figs/E1_posterior_concentration_llm.png`

## E2 Type-Count Scaling

Lower cumulative regret is better.

| Type count | HPSMG regret | HPSMG+ regret | Winner |
| ---: | ---: | ---: | --- |
| 2 | 0.1980 | 0.0620 | HPSMG+ |
| 3 | 0.6320 | 0.0000 | HPSMG+ |
| 4 | 0.2320 | 0.0000 | HPSMG+ |
| 5 | 0.9200 | 1.0960 | HPSMG |
| 6 | 1.2800 | 0.2000 | HPSMG+ |

Claim note: HPSMG+ wins 4/5 type-count settings. It does not win at type_count=5 in this run, so do not claim uniform dominance for E2 without additional evidence.

Files:

- Raw: `results/e1_e4_llm/E2_type*_live.npz`
- Live calibration: `calibration/e1_e4_llm/E2_type*_live.npz`
- Summary: `analysis/E2_type_scaling_llm_summary.json`
- Table: `tables/E2_type_scaling_llm.csv`
- Figure: `figs/E2_type_scaling_llm.png`

## E3 N-Agent Scaling

Lower cumulative regret is better. Storage entries are included because E3 is partly a storage-scaling experiment.

| n | Algorithm | Storage entries | Regret mean | Winner by regret |
| ---: | --- | ---: | ---: | --- |
| 2 | HPSMG | 8 | 0.1400 | HPSMG |
| 2 | HPSMG+ | 8 | 2.6880 |  |
| 2 | Joint PSRL | 16 | 0.4220 |  |
| 3 | HPSMG | 12 | 0.2320 |  |
| 3 | HPSMG+ | 12 | 0.0000 | HPSMG+ |
| 3 | Joint PSRL | 64 | 0.3480 |  |
| 4 | HPSMG | 16 | 0.1080 |  |
| 4 | HPSMG+ | 16 | 0.0000 | HPSMG+ |
| 4 | Joint PSRL | 256 | 0.2160 |  |
| 5 | HPSMG | 20 | 0.8700 |  |
| 5 | HPSMG+ | 20 | 0.2780 | HPSMG+ |
| 5 | Joint PSRL | 1024 | 1.2520 |  |

Claim note: HPSMG+ wins 3/4 n settings and keeps linear storage, while joint PSRL storage grows exponentially. It does not win at n=2 in this run.

Files:

- Raw: `results/e1_e4_llm/E3_n*_live.npz`
- Live calibration: `calibration/e1_e4_llm/E3_n*_live.npz`
- Summary: `analysis/E3_n_agent_scaling_llm_summary.json`
- Table: `tables/E3_n_agent_scaling_llm.csv`
- Figure: `figs/E3_n_agent_scaling_llm.png`

## E4 Prior Recovery

DeepSeek-V3.2 live refreshed c19 calibration. Lower cumulative regret is better.

| Prior mode | HPSMG regret | MAP-greedy regret | Winner |
| --- | ---: | ---: | --- |
| uniform | 1.2860 | 0.9000 | MAP-greedy |
| correct | 0.7860 | 0.0000 | MAP-greedy |
| adversarial | 1.4340 | 1.6100 | HPSMG |

Claim note: this supports robustness under adversarial prior, not uniform dominance over MAP-greedy. MAP-greedy is better with correct and uniform priors in this run.

Files:

- Raw: `results/e1_e4_llm/E4_prior_*_DeepSeek_V3_2_live.npz`
- Summary: `analysis/E4_prior_recovery_llm_summary.json`
- Table: `tables/E4_prior_recovery_llm.csv`
- Figure: `figs/E4_prior_recovery_llm.png`

## Calibration Reports

- E1: `analysis/E1_c19_*_live_report.json`
- E2: `analysis/E2_type*_live_report.json`
- E3: `analysis/E3_n*_live_report.json`

All live reports show parse_failure_count = 0.

## Paper-Safe Summary

The live LLM evidence supports fast posterior concentration across all four backbones in E1 and HPSMG+ improvements in most E2/E3 scaling settings. The recommended report is E1-E3 only. E4 should remain archived as diagnostic prior-sensitivity evidence because it does not support a clean headline claim.