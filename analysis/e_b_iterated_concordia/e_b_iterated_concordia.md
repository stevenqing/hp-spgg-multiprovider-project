# E-B: Iterated Concordia-Derived Compact Benchmark

This is a constructed iterated variant, not Concordia's native one-shot protocol. Types are fixed for K episodes and PF is imposed. Exact upstream payoff functions and finite action menus are reused.

The replay is backbone-invariant because no LLM is called; duplicating the same exact-payoff rows under four model names would not constitute independent evidence.

| config | method | cumulative regret | late instant regret | true-type mass | storage |
|---|---|---:|---:|---:|---:|
| Haggling: fruitville | A-ToM-1 | 4.468 $\pm$ 0.805 | 0.2234 | 0.062 | 8 / 16 |
| Haggling: fruitville | ECON-BNE | 0.653 $\pm$ 0.347 | 0.0327 | 0.062 | 8 / 16 |
| Haggling: fruitville | Joint-PSRL | 0.552 $\pm$ 0.041 | 0.0117 | 0.894 | 8 / 16 |
| Haggling: fruitville | MAP-Type-Greedy | 0.418 $\pm$ 0.171 | 0.0089 | 0.573 | 8 / 16 |
| Haggling: fruitville | PACT | 0.476 $\pm$ 0.073 | 0.0041 | 0.903 | 8 / 16 |
| Haggling: fruitville | PACT+ | 0.500 $\pm$ 0.051 | 0.0031 | 0.945 | 8 / 16 |
| Haggling: fruitville | PSRL-NoType | 2.019 $\pm$ 0.541 | 0.1086 | 0.062 | 8 / 16 |
| Haggling: fruitville | Random | 10.340 $\pm$ 1.235 | 0.5563 | 0.062 | 8 / 16 |
| Haggling: vegbrooke | A-ToM-1 | 1.151 $\pm$ 0.762 | 0.0576 | 0.062 | 8 / 16 |
| Haggling: vegbrooke | ECON-BNE | 1.167 $\pm$ 0.756 | 0.0583 | 0.062 | 8 / 16 |
| Haggling: vegbrooke | Joint-PSRL | 0.580 $\pm$ 0.080 | 0.0047 | 0.802 | 8 / 16 |
| Haggling: vegbrooke | MAP-Type-Greedy | 0.346 $\pm$ 0.100 | 0.0000 | 0.585 | 8 / 16 |
| Haggling: vegbrooke | PACT | 0.484 $\pm$ 0.131 | 0.0003 | 0.782 | 8 / 16 |
| Haggling: vegbrooke | PACT+ | 0.597 $\pm$ 0.065 | 0.0007 | 0.890 | 8 / 16 |
| Haggling: vegbrooke | PSRL-NoType | 2.328 $\pm$ 0.441 | 0.1340 | 0.062 | 8 / 16 |
| Haggling: vegbrooke | Random | 3.926 $\pm$ 0.880 | 0.2087 | 0.062 | 8 / 16 |
| Multi-item: fruitville | A-ToM-1 | 6.347 $\pm$ 0.739 | 0.3173 | 0.062 | 8 / 16 |
| Multi-item: fruitville | ECON-BNE | 0.176 $\pm$ 0.120 | 0.0088 | 0.062 | 8 / 16 |
| Multi-item: fruitville | Joint-PSRL | 0.339 $\pm$ 0.049 | 0.0060 | 0.758 | 8 / 16 |
| Multi-item: fruitville | MAP-Type-Greedy | 0.162 $\pm$ 0.040 | 0.0000 | 0.575 | 8 / 16 |
| Multi-item: fruitville | PACT | 0.469 $\pm$ 0.033 | 0.0099 | 0.930 | 8 / 16 |
| Multi-item: fruitville | PACT+ | 0.471 $\pm$ 0.056 | 0.0039 | 0.928 | 8 / 16 |
| Multi-item: fruitville | PSRL-NoType | 1.655 $\pm$ 0.166 | 0.0975 | 0.062 | 8 / 16 |
| Multi-item: fruitville | Random | 9.504 $\pm$ 0.545 | 0.4809 | 0.062 | 8 / 16 |
| Multi-item: vegbrooke | A-ToM-1 | 5.205 $\pm$ 1.410 | 0.2602 | 0.062 | 8 / 16 |
| Multi-item: vegbrooke | ECON-BNE | 0.734 $\pm$ 0.454 | 0.0367 | 0.062 | 8 / 16 |
| Multi-item: vegbrooke | Joint-PSRL | 0.409 $\pm$ 0.050 | 0.0035 | 0.735 | 8 / 16 |
| Multi-item: vegbrooke | MAP-Type-Greedy | 0.096 $\pm$ 0.035 | 0.0000 | 0.627 | 8 / 16 |
| Multi-item: vegbrooke | PACT | 0.406 $\pm$ 0.098 | 0.0102 | 0.905 | 8 / 16 |
| Multi-item: vegbrooke | PACT+ | 0.432 $\pm$ 0.102 | 0.0042 | 0.908 | 8 / 16 |
| Multi-item: vegbrooke | PSRL-NoType | 1.508 $\pm$ 0.068 | 0.0910 | 0.062 | 8 / 16 |
| Multi-item: vegbrooke | Random | 9.759 $\pm$ 0.761 | 0.4856 | 0.062 | 8 / 16 |
| Pub: london | A-ToM-1 | 1.418 $\pm$ 1.418 | 0.0709 | 0.004 | 16 / 256 |
| Pub: london | ECON-BNE | 3.918 $\pm$ 2.547 | 0.1959 | 0.004 | 16 / 256 |
| Pub: london | Joint-PSRL | 0.055 $\pm$ 0.055 | 0.0000 | 0.107 | 16 / 256 |
| Pub: london | MAP-Type-Greedy | 0.055 $\pm$ 0.055 | 0.0000 | 0.614 | 16 / 256 |
| Pub: london | PACT | 0.036 $\pm$ 0.036 | 0.0000 | 0.617 | 16 / 256 |
| Pub: london | PACT+ | 0.036 $\pm$ 0.036 | 0.0000 | 0.617 | 16 / 256 |
| Pub: london | PSRL-NoType | 0.618 $\pm$ 0.477 | 0.0237 | 0.004 | 16 / 256 |
| Pub: london | Random | 29.168 $\pm$ 1.719 | 1.5718 | 0.004 | 16 / 256 |
| Pub: london_mini | A-ToM-1 | 0.000 $\pm$ 0.000 | 0.0000 | 0.062 | 8 / 16 |
| Pub: london_mini | ECON-BNE | 1.409 $\pm$ 1.409 | 0.0705 | 0.062 | 8 / 16 |
| Pub: london_mini | Joint-PSRL | 0.037 $\pm$ 0.037 | 0.0037 | 0.429 | 8 / 16 |
| Pub: london_mini | MAP-Type-Greedy | 0.037 $\pm$ 0.037 | 0.0000 | 0.656 | 8 / 16 |
| Pub: london_mini | PACT | 0.000 $\pm$ 0.000 | 0.0000 | 0.634 | 8 / 16 |
| Pub: london_mini | PACT+ | 0.075 $\pm$ 0.075 | 0.0000 | 0.670 | 8 / 16 |
| Pub: london_mini | PSRL-NoType | 0.037 $\pm$ 0.037 | 0.0037 | 0.062 | 8 / 16 |
| Pub: london_mini | Random | 16.351 $\pm$ 1.987 | 0.7692 | 0.062 | 8 / 16 |

## Aggregate across selected configs

| scope | method | cumulative regret | late instant regret | paired gap vs PACT+ |
|---|---|---:|---:|---:|
| all_selected | PACT | 0.312 $\pm$ 0.026 | 0.0041 $\pm$ 0.0012 | -0.040 $\pm$ 0.030 |
| all_selected | PACT+ | 0.352 $\pm$ 0.035 | 0.0020 $\pm$ 0.0017 | +0.000 $\pm$ 0.000 |
| all_selected | Joint-PSRL | 0.329 $\pm$ 0.030 | 0.0049 $\pm$ 0.0012 | -0.023 $\pm$ 0.043 |
| all_selected | PSRL-NoType | 1.361 $\pm$ 0.172 | 0.0764 $\pm$ 0.0139 | +1.009 $\pm$ 0.201 |
| informative_haggling | PACT | 0.459 $\pm$ 0.040 | 0.0061 $\pm$ 0.0019 | -0.041 $\pm$ 0.026 |
| informative_haggling | PACT+ | 0.500 $\pm$ 0.046 | 0.0030 $\pm$ 0.0025 | +0.000 $\pm$ 0.000 |
| informative_haggling | Joint-PSRL | 0.470 $\pm$ 0.037 | 0.0065 $\pm$ 0.0019 | -0.030 $\pm$ 0.050 |
| informative_haggling | PSRL-NoType | 1.877 $\pm$ 0.271 | 0.1078 $\pm$ 0.0224 | +1.377 $\pm$ 0.299 |

Persona-value selection seeds: 0..4; held-out report seeds: 1000..1004.
Gaussian likelihood sigma is 0.08 after per-player normalization to [0,1]. All planning is exact enumeration, not a CCE LP.
