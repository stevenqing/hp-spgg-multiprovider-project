# E-A Environment-Matched HP-SPGG Control

Protocol: n=3, |Theta_i|=4, K=20, 10 common seeds, beta=0.25. 
Within each backbone every method uses the same complete 125-profile live tensor, true-type profile, uniform prior, no additional board state, and exact tensor oracle; each method receives its own realized-reward history from that tensor.

| backbone | PACT+ | PACT | Joint-PSRL | LLM-PSRL | best coordination baseline | PACT+ ratio | best-family ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| DeepSeek-V3.2 | 0.360 ± 0.142 | 0.985 ± 0.298 | 0.955 ± 0.203 | 18.270 ± 5.141 | ECON-BNE 2.550 ± 1.049 | 7.08x | 7.08x |
| GPT-5.4-nano | 0.159 ± 0.038 | 0.544 ± 0.150 | 0.391 ± 0.100 | 2.193 ± 0.714 | ECON-BNE 6.960 ± 1.376 | 43.77x | 43.77x |
| Kimi-K2.6 | 0.325 ± 0.088 | 0.547 ± 0.116 | 0.642 ± 0.159 | 6.701 ± 1.325 | ECON-BNE 2.957 ± 1.366 | 9.10x | 9.10x |
| Llama-4-Maverick | 0.430 ± 0.217 | 1.202 ± 0.212 | 1.276 ± 0.228 | 13.510 ± 3.431 | A-ToM-0 0.700 ± 0.396 | 1.63x | 1.63x |

Matched best-family ratio range: **1.63x–43.77x**.

Ratios are ratios of per-backbone mean cumulative regrets. SEM uses sample standard deviation over the ten common seeds. The selected strongest coordination baseline is chosen by the lowest mean regret within ECON-BNE, A-ToM-{0,1,2}, MoA, and Puppeteer; paired gaps use the same seed indices.
