# MaaSSim LLM Prompt Variant Comparison

Common-state replay over `2` seeds and the first `12` active snapshots per seed using `gpt-5.4-mini-20260317`.

| Variant | Prompt contents | Utility | Served | Driver rejects | Driver accept | Extra wait/snapshot | Parse | Repair | Fallback |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LLM-basic | Candidate features, persona belief marginals, legal assignment menu | 8.29 +/- 5.51 | 9.5 | 5.0 | 0.727 | 0.00 | 1.000 | 0.000 | 0.000 |
| LLM+PACT-score | LLM-basic plus assignment-level PACT-style expected accepts, expected rejects, estimated utility, and risk summaries | 8.52 +/- 5.29 | 9.5 | 4.5 | 0.754 | 2.54 | 1.000 | 0.000 | 0.000 |

Baseline rows from the same replay setting:

| Policy | Utility | Served | Driver rejects | Driver accept | Extra wait/snapshot |
|---|---:|---:|---:|---:|---:|
| Nearest | 7.21 +/- 6.59 | 9.0 | 5.0 | 0.727 | 1.12 |
| Random | -2.80 +/- 5.21 | 7.0 | 5.0 | 0.731 | 106.54 |
| PACT | 8.52 +/- 5.29 | 9.5 | 4.5 | 0.754 | 2.54 |
| Oracle | 16.15 +/- 2.15 | 10.0 | 0.0 | 1.000 | 22.62 |

Readout: the legal-assignment menu solved format compliance (`parse=1.000`). Under the current baseline-compatible prompt implementation, adding assignment-level PACT-style persona-aware scores improves LLM utility by `+0.23` over LLM-basic and matches PACT in this small smoke. This is still a small-sample diagnostic; the next step is scaling LLM+PACT-score and the A-ToM baselines to more seeds and all active snapshots.