# MaaSSim Persona-Stress LLM Prompt Baseline Comparison

Common-state replay over `5` seeds and the first `20` active snapshots per seed using `gpt-5.4-mini-20260317`. Utility uses `driver_reject_penalty=5.0` and `passenger_reject_penalty=0.5` to make hidden driver persona mistakes more consequential.

| Policy | Utility | Served | Driver rejects | Driver accept | Extra wait/snapshot | Oracle-match | Parse | Repair | Fallback |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nearest | 12.70 +/- 11.83 | 19.6 | 5.4 | 0.822 | 1.66 | 0.920 | n/a | n/a | n/a |
| Random | -27.12 +/- 7.54 | 13.6 | 8.8 | 0.716 | 120.77 | 0.180 | n/a | n/a | n/a |
| LLM-PACT | 18.37 +/- 10.12 | 20.2 | 4.2 | 0.862 | 5.97 | 0.890 | 1.000 | 0.000 | 0.000 |
| LLM-belief | 13.47 +/- 9.94 | 19.4 | 5.0 | 0.835 | 3.06 | 0.920 | 1.000 | 0.000 | 0.000 |
| LLM-PSRL | 13.77 +/- 11.14 | 19.6 | 5.0 | 0.835 | 6.69 | 0.830 | 1.000 | 0.000 | 0.000 |
| A-ToM-0 | 12.67 +/- 11.34 | 19.6 | 5.4 | 0.822 | 1.46 | 0.920 | 1.000 | 0.000 | 0.000 |
| A-ToM-1 | 12.77 +/- 11.46 | 19.6 | 5.4 | 0.822 | 0.62 | 0.950 | 1.000 | 0.000 | 0.000 |
| ECON-BNE | 12.48 +/- 11.47 | 19.6 | 5.4 | 0.822 | 1.76 | 0.910 | 1.000 | 0.000 | 0.000 |
| Oracle | 36.44 +/- 5.09 | 20.6 | 0.4 | 0.989 | 18.48 | 0.740 | n/a | n/a | n/a |

Readout: adding the persona-stress penalty separates LLM-PACT from pure LLM prompt baselines. LLM-PACT improves utility by `+4.60` over LLM-PSRL, `+4.90` over LLM-belief, `+5.60` over A-ToM-1, `+5.70` over A-ToM-0, and `+5.89` over ECON-BNE while maintaining perfect parse behavior. This is still a medium-scale replay rather than a final closed-loop MaaSSim result, but it is a cleaner fairness story: LLM-PACT is compared against LLM-belief, LLM-PSRL, A-ToM, and ECON-BNE under the same legal action interface.