# MaaSSim LLM Scenario Suite

This suite implements the first three environment-design knobs: normal replay, reject-penalty stress, and conflict-offer stress. The comparison is LLM-PACT against pure LLM prompt baselines under the same legal-action interface.

| Scenario | LLM-PACT utility | Best prompt baseline | Prompt utility | Utility gap | Driver reject gap | Oracle utility |
|---|---:|---|---:|---:|---:|---:|
| Normal | 31.29 +/- 7.76 | LLM-PSRL | 29.81 +/- 7.80 | 1.47 | 0.6 | 37.64 |
| Reject-stress | 18.37 +/- 10.12 | LLM-PSRL | 13.77 +/- 11.14 | 4.60 | 0.8 | 36.44 |
| Conflict-offer | 8.79 +/- 4.84 | LLM-belief | -30.90 +/- 4.20 | 39.69 | 7.6 | 22.44 |

Readout: the LLM-PACT advantage grows as the environment makes persona mistakes more consequential. The gap is small in the normal setting, larger under rejection-cost stress, and largest when low-wait offers are made persona-risky.

## Detail Rows

| Scenario | Policy | Utility | Driver rejects | Served | Driver accept |
|---|---|---:|---:|---:|---:|
| Normal | LLM-PACT | 31.29 +/- 7.76 | 4.2 | 20.2 | 0.862 |
| Normal | LLM-belief | 28.27 +/- 7.47 | 5.2 | 19.4 | 0.829 |
| Normal | LLM-PSRL | 29.81 +/- 7.80 | 4.8 | 19.8 | 0.841 |
| Normal | A-ToM-1 | 28.97 +/- 8.01 | 5.4 | 19.6 | 0.822 |
| Normal | Oracle | 37.64 +/- 6.01 | 0.4 | 20.6 | 0.989 |
| Normal | ECON-BNE | 28.81 +/- 7.97 | 5.4 | 19.6 | 0.822 |
| Reject-stress | LLM-PACT | 18.37 +/- 10.12 | 4.2 | 20.2 | 0.862 |
| Reject-stress | LLM-belief | 13.47 +/- 9.94 | 5.0 | 19.4 | 0.835 |
| Reject-stress | LLM-PSRL | 13.77 +/- 11.14 | 5.0 | 19.6 | 0.835 |
| Reject-stress | A-ToM-1 | 12.77 +/- 11.46 | 5.4 | 19.6 | 0.822 |
| Reject-stress | ECON-BNE | 12.48 +/- 11.47 | 5.4 | 19.6 | 0.822 |
| Reject-stress | Oracle | 36.44 +/- 5.09 | 0.4 | 20.6 | 0.989 |
| Conflict-offer | LLM-PACT | 8.79 +/- 4.84 | 3.2 | 16.4 | 0.896 |
| Conflict-offer | LLM-belief | -30.90 +/- 4.20 | 10.8 | 13.6 | 0.654 |
| Conflict-offer | LLM-PSRL | -32.93 +/- 7.23 | 11.2 | 13.6 | 0.643 |
| Conflict-offer | A-ToM-1 | -42.43 +/- 3.21 | 12.8 | 12.6 | 0.594 |
| Conflict-offer | Oracle | 22.44 +/- 4.72 | 1.4 | 18.6 | 0.956 |
| Conflict-offer | ECON-BNE | -46.82 +/- 8.02 | 13.4 | 11.8 | 0.575 |
