# MaaSSim LLM Scenario Suite

This suite holds the rejection penalty fixed at 5.0 and varies conflict strength lambda in {0, 0.5, 1}. The comparison is LLM-PACT against pure LLM prompt baselines under the same legal-action interface.

| Scenario | LLM-PACT utility | Best prompt baseline | Prompt utility | Utility gap | Driver reject gap | Oracle utility |
|---|---:|---|---:|---:|---:|---:|
| Reject-stress | 18.37 +/- 10.12 | LLM-PSRL | 13.77 +/- 11.14 | 4.60 | 0.8 | 36.44 |
| Mid-conflict | 8.96 +/- 5.47 | Puppeteer | -20.86 +/- 9.86 | 29.81 | 6.6 | 30.70 |
| Full-conflict | 8.79 +/- 4.84 | LLM-belief | -30.90 +/- 4.20 | 39.69 | 7.6 | 22.44 |

Readout: the LLM-PACT advantage grows as conflict strength makes low-wait offers increasingly persona-risky.

## Detail Rows

| Scenario | Policy | Utility | Driver rejects | Served | Driver accept |
|---|---|---:|---:|---:|---:|
| Reject-stress | MoA | 12.80 +/- 11.45 | 5.4 | 19.6 | 0.822 |
| Reject-stress | Puppeteer | 12.82 +/- 11.44 | 5.4 | 19.6 | 0.822 |
| Reject-stress | LLM-PACT | 18.37 +/- 10.12 | 4.2 | 20.2 | 0.862 |
| Reject-stress | LLM-belief | 13.47 +/- 9.94 | 5.0 | 19.4 | 0.835 |
| Reject-stress | LLM-PSRL | 13.77 +/- 11.14 | 5.0 | 19.6 | 0.835 |
| Reject-stress | A-ToM-1 | 12.77 +/- 11.46 | 5.4 | 19.6 | 0.822 |
| Reject-stress | ECON-BNE | 12.48 +/- 11.47 | 5.4 | 19.6 | 0.822 |
| Reject-stress | Oracle | 36.44 +/- 5.09 | 0.4 | 20.6 | 0.989 |
| Mid-conflict | LLM-PACT | 8.96 +/- 5.47 | 3.2 | 17.4 | 0.896 |
| Mid-conflict | LLM-belief | -22.80 +/- 10.17 | 10.0 | 15.2 | 0.677 |
| Mid-conflict | LLM-PSRL | -31.13 +/- 10.10 | 11.4 | 14.4 | 0.634 |
| Mid-conflict | A-ToM-1 | -31.88 +/- 12.30 | 11.4 | 14.0 | 0.633 |
| Mid-conflict | ECON-BNE | -26.09 +/- 10.33 | 10.8 | 15.2 | 0.654 |
| Mid-conflict | Oracle | 30.70 +/- 5.99 | 1.0 | 21.6 | 0.970 |
| Mid-conflict | MoA | -25.60 +/- 12.49 | 10.6 | 15.0 | 0.657 |
| Mid-conflict | Puppeteer | -20.86 +/- 9.86 | 9.8 | 15.6 | 0.687 |
| Full-conflict | MoA | -48.16 +/- 8.80 | 13.6 | 11.6 | 0.566 |
| Full-conflict | Puppeteer | -33.03 +/- 5.80 | 11.4 | 13.8 | 0.633 |
| Full-conflict | LLM-PACT | 8.79 +/- 4.84 | 3.2 | 16.4 | 0.896 |
| Full-conflict | LLM-belief | -30.90 +/- 4.20 | 10.8 | 13.6 | 0.654 |
| Full-conflict | LLM-PSRL | -32.93 +/- 7.23 | 11.2 | 13.6 | 0.643 |
| Full-conflict | A-ToM-1 | -42.43 +/- 3.21 | 12.8 | 12.6 | 0.594 |
| Full-conflict | Oracle | 22.44 +/- 4.72 | 1.4 | 18.6 | 0.956 |
| Full-conflict | ECON-BNE | -46.82 +/- 8.02 | 13.4 | 11.8 | 0.575 |
