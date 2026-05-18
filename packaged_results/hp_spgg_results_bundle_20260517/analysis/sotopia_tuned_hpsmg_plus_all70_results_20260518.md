# SOTOPIA Tuned HPSMG+ All70 Results - 2026-05-18

This summarizes `scripts/run_sotopia_tuned_hpsmg_plus_overnight.ps1`, run with `MaxConcurrent=2` and `MaxTotalSotopiaProcesses=4`.

## Run Status

- Jobs prepared: 7.
- Completed: 7/7.
- Failed: 0.
- Full all70 models completed: DeepSeek-V3.2, gpt-5.4-nano-20260317, Kimi-K2.6, Llama-4-Maverick-17B-128E-Instruct-FP8.
- Pilot jobs completed: GPT case12, Kimi case2, Llama case48.

## Tuned HPSMG+ All70 Scores

| Model | Mean overall | Cases | Complete |
| --- | ---: | ---: | --- |
| DeepSeek-V3.2 | 3.247959 | 70 | true |
| gpt-5.4-nano-20260317 | 2.980612 | 70 | true |
| Kimi-K2.6 | 2.807143 | 70 | true |
| Llama-4-Maverick-17B-128E-Instruct-FP8 | 3.308163 | 70 | true |

## Ranking Against Available All70 Baselines

Higher mean overall is better.

Important fairness note: this ranking mixes vanilla baselines with the SOTOPIA-adapted HPSMG+ prompt/action profile. Use it as an adaptation result, not as the strict vanilla baseline comparison. See `analysis/sotopia_fairness_audit_20260518.md`.

### DeepSeek-V3.2

| Rank | Method | Mean overall |
| ---: | --- | ---: |
| 1 | HPSMG+ tuned | 3.247959 |
| 2 | HPSMG+ original | 3.193878 |
| 3 | ECON-BNE | 3.176531 |
| 4 | LLM greedy | 3.164286 |
| 5 | A-ToM1 | 3.106122 |
| 6 | LLM belief | 3.077551 |

### gpt-5.4-nano-20260317

| Rank | Method | Mean overall |
| ---: | --- | ---: |
| 1 | HPSMG+ tuned | 2.980612 |
| 2 | ECON-BNE | 2.969388 |
| 3 | LLM belief | 2.937755 |
| 4 | LLM greedy | 2.890816 |
| 5 | A-ToM1 | 2.770408 |
| 6 | HPSMG+ original | 2.685714 |

### Kimi-K2.6

| Rank | Method | Mean overall |
| ---: | --- | ---: |
| 1 | HPSMG+ tuned | 2.807143 |
| 2 | ECON-BNE legacy | 2.448980 |
| 3 | LLM greedy | 2.128571 |
| 4 | A-ToM1 | 1.836735 |
| 5 | HPSMG+ original | 1.577551 |
| 6 | LLM belief | 1.553061 |

### Llama-4-Maverick-17B-128E-Instruct-FP8

| Rank | Method | Mean overall |
| ---: | --- | ---: |
| 1 | HPSMG+ tuned | 3.308163 |
| 2 | ECON-BNE legacy | 3.263265 |
| 3 | LLM belief | 3.176531 |
| 4 | LLM greedy legacy | 3.154082 |
| 5 | HPSMG+ original | 3.153061 |
| 6 | A-ToM1 legacy | 3.129592 |

## Claim-Safe Summary

Tuned HPSMG+ ranks first among the available all70 rows for all four tested CloudGPT models. Because only HPSMG+ used the `sotopia_tuned` adaptation, this should be framed as a transparent SOTOPIA-adapted HPSMG+ result. The strict vanilla comparison is mixed and should be reported separately.

## Files

- Log: `logs/sotopia_tuned_hpsmg_plus_overnight.log`
- DeepSeek: `analysis/sotopia_hard_official_DeepSeek_V3_2_hpsmg_plus_sotopia_tuned_all70.json`
- GPT: `analysis/sotopia_hard_official_gpt_5_4_nano_20260317_hpsmg_plus_sotopia_tuned_all70.json`
- Kimi: `analysis/sotopia_hard_official_Kimi_K2_6_hpsmg_plus_sotopia_tuned_all70.json`
- Llama: `analysis/sotopia_hard_official_Llama_4_Maverick_17B_128E_Instruct_FP8_hpsmg_plus_sotopia_tuned_all70.json`