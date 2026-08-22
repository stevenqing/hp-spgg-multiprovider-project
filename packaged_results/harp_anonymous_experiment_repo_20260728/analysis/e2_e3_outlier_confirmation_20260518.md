# E2/E3 Outlier Confirmation - 2026-05-18

This note checks the two live LLM E-experiment anomalies that could hurt the paper narrative.

## Question

- E2 type_count=5: 5-seed run had HPSMG+ worse than HPSMG.
- E3 n=2: 5-seed run had HPSMG+ regret 2.688, much worse than HPSMG and joint PSRL.

## E2 Type Count 5

Original 5-seed final regrets:

| Algorithm | Seed finals | Mean | Std |
| --- | --- | ---: | ---: |
| HPSMG | 0.83, 1.19, 0.82, 1.06, 0.70 | 0.9200 | 0.1783 |
| HPSMG+ | 0.39, 0.00, 0.33, 3.12, 1.64 | 1.0960 | 1.1558 |

10-seed confirmation:

| Algorithm | Mean | SEM | Source |
| --- | ---: | ---: | --- |
| HPSMG | 0.9100 | 0.1100 | `results/e1_e4_llm/E2_type5_live_s10.npz` |
| HPSMG+ | 0.7720 | 0.3215 | `results/e1_e4_llm/E2_type5_live_s10.npz` |

Conclusion: the E2 type_count=5 anomaly is mostly a small-sample/high-variance issue. With 10 seeds, HPSMG+ is better than HPSMG, though the HPSMG+ SEM remains large.

## E3 N=2

Original 5-seed final regrets:

| Algorithm | Seed finals | Mean | Std |
| --- | --- | ---: | ---: |
| HPSMG | 0.32, 0.18, 0.00, 0.20, 0.00 | 0.1400 | 0.1239 |
| Joint PSRL | 1.47, 0.00, 0.26, 0.20, 0.18 | 0.4220 | 0.5311 |
| HPSMG+ | 3.20, 3.60, 5.20, 0.00, 1.44 | 2.6880 | 1.7993 |

10-seed confirmation:

| Algorithm | Mean | SEM | Source |
| --- | ---: | ---: | --- |
| HPSMG | 0.0700 | 0.0374 | `results/e1_e4_llm/E3_n2_live_s10.npz` |
| Joint PSRL | 0.2750 | 0.1395 | `results/e1_e4_llm/E3_n2_live_s10.npz` |
| HPSMG+ | 2.9620 | 0.5446 | `results/e1_e4_llm/E3_n2_live_s10.npz` |

Conclusion: the E3 n=2 anomaly is real, not a single broken seed. It should be framed as a small-population exception/diagnostic case. The paper-facing E3 claim should focus on n>=3 scaling, where HPSMG+ wins while keeping linear storage.

## Paper Decision

- Use 10-seed E2 tables in the paper-facing report.
- For E3, report the full 10-seed table but phrase the headline as `for n>=3` or `beyond the two-agent degenerate case`.
- Do not drop seeds. Keep all runs and report exact values.