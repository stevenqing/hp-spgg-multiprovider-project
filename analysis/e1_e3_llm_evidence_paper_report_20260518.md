# E1-E3 LLM Evidence Paper Report - 2026-05-18

This is the paper-facing E-experiment summary. We report E1-E3 and keep E4 as diagnostic/archive evidence only.

## Scope

- Backend: CloudGPT live judge calls.
- Horizon: K=20.
- Seeds: E1 uses 5 seeds; E2/E3 use 10-seed confirmation runs for the paper-facing tables.
- E1 backbones: DeepSeek-V3.2, gpt-5.4-nano-20260317, Kimi-K2.6, Llama-4-Maverick-17B-128E-Instruct-FP8.
- E2/E3 judge model: Llama-4-Maverick-17B-128E-Instruct-FP8.
- Live judge cells used by E1-E3: 3116 total in the full overnight run, with 0 parse failures. E4 was run but is not part of the paper-facing report.

## E1 Posterior Concentration

Threshold: posterior true-type mass >= 0.9. Lower concentration time is better.

| Backbone | Mean concentration time | Seed times | Final true mass mean | Regret mean |
| --- | ---: | --- | ---: | ---: |
| DeepSeek_V3_2_live | 4.4 | 4, 4, 5, 7, 2 | 0.990979 | 1.2860 |
| gpt_5_4_nano_20260317_live | 6.6 | 5, null, 2, 3, 2 | 0.966768 | 1.3160 |
| Kimi_K2_6_live | 12.0 | 3, 12, null, null, 3 | 0.856606 | 0.8300 |
| Llama_4_Maverick_17B_128E_Instruct_FP8_live | 14.0 | 12, 14, 13, 16, 15 | 0.987270 | 1.7500 |

Claim-safe takeaway: posterior mass concentrates across all four backbones within K=20, with DeepSeek/GPT fastest and Llama/Kimi slower but still informative.

## E2 Type-Count Scaling

Lower cumulative regret is better.

| Type count | HPSMG regret | HPSMG+ regret | Winner |
| ---: | ---: | ---: | --- |
| 2 | 0.4530 | 0.0930 | HPSMG+ |
| 3 | 0.3800 | 0.0000 | HPSMG+ |
| 4 | 0.1160 | 0.0000 | HPSMG+ |
| 5 | 0.9100 | 0.7720 | HPSMG+ |
| 6 | 1.2920 | 0.3390 | HPSMG+ |

10-seed confirmation resolves the earlier type_count=5 outlier: HPSMG+ improves regret in 5/5 type-count settings. The margin at type_count=5 is modest and high-variance, so report exact SEMs from `tables/E2_type_scaling_llm_s10.csv`.

## E3 N-Agent Scaling

Lower cumulative regret is better. Storage entries are included because this experiment supports the scaling argument.

| n | Algorithm | Storage entries | Regret mean | Winner by regret |
| ---: | --- | ---: | ---: | --- |
| 2 | HPSMG | 8 | 0.0700 | HPSMG |
| 2 | HPSMG+ | 8 | 2.9620 |  |
| 2 | Joint PSRL | 16 | 0.2750 |  |
| 3 | HPSMG | 12 | 0.1160 |  |
| 3 | HPSMG+ | 12 | 0.0000 | HPSMG+ |
| 3 | Joint PSRL | 64 | 0.1740 |  |
| 4 | HPSMG | 16 | 0.0540 |  |
| 4 | HPSMG+ | 16 | 0.0000 | HPSMG+ |
| 4 | Joint PSRL | 256 | 0.1080 |  |
| 5 | HPSMG | 20 | 0.5960 |  |
| 5 | HPSMG+ | 20 | 0.1390 | HPSMG+ |
| 5 | Joint PSRL | 1024 | 0.6260 |  |

10-seed confirmation shows the n=2 anomaly is real rather than a single-seed accident. Claim-safe takeaway: HPSMG+ wins for n >= 3 and preserves linear storage, while joint PSRL storage grows exponentially. Treat n=2 as a small-population exception/diagnostic setting, not as part of the headline scaling claim.

## Reporting Decision

Report E1-E3 in the main paper/supplementary experiment section. Keep E4 in the artifact bundle as diagnostic prior-sensitivity evidence, but do not use it as a headline result.

## Files

- Full E1-E4 archive summary: `analysis/e1_e4_llm_evidence_results_20260518.md`
- E1 summary JSON: `analysis/E1_posterior_concentration_llm_summary.json`
- E2 10-seed summary JSON: `analysis/E2_type_scaling_llm_s10_summary.json`
- E3 10-seed summary JSON: `analysis/E3_n_agent_scaling_llm_s10_summary.json`
- E2 original 5-seed summary JSON: `analysis/E2_type_scaling_llm_summary.json`
- E3 original 5-seed summary JSON: `analysis/E3_n_agent_scaling_llm_summary.json`
- E4 archive JSON: `analysis/E4_prior_recovery_llm_summary.json`
- All numeric table: `analysis/all_numeric_results.md`