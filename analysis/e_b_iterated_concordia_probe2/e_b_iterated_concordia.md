# E-B: Iterated Concordia-Derived Compact Benchmark

This is a constructed iterated variant, not Concordia's native one-shot protocol. Types are fixed for K episodes and PF is imposed. Exact upstream payoff functions and finite action menus are reused.

The replay is backbone-invariant because no LLM is called; duplicating the same exact-payoff rows under four model names would not constitute independent evidence.

| config | method | cumulative regret | late instant regret | true-type mass | storage |
|---|---|---:|---:|---:|---:|
| Haggling: fruitville | A-ToM-1 | 2.435 $\pm$ 0.000 | 0.1217 | 0.062 | 8 / 16 |
| Haggling: fruitville | ECON-BNE | 1.217 $\pm$ 0.000 | 0.0609 | 0.062 | 8 / 16 |
| Haggling: fruitville | Joint-PSRL | 0.496 $\pm$ 0.000 | 0.0157 | 0.878 | 8 / 16 |
| Haggling: fruitville | MAP-Type-Greedy | 0.157 $\pm$ 0.000 | 0.0000 | 0.342 | 8 / 16 |
| Haggling: fruitville | PACT | 0.496 $\pm$ 0.000 | 0.0157 | 0.939 | 8 / 16 |
| Haggling: fruitville | PACT+ | 0.496 $\pm$ 0.000 | 0.0157 | 0.939 | 8 / 16 |
| Haggling: fruitville | PSRL-NoType | 1.278 $\pm$ 0.000 | 0.0809 | 0.062 | 8 / 16 |
| Haggling: fruitville | Random | 11.530 $\pm$ 0.000 | 0.6339 | 0.062 | 8 / 16 |
| Haggling: vegbrooke | A-ToM-1 | 0.000 $\pm$ 0.000 | 0.0000 | 0.062 | 8 / 16 |
| Haggling: vegbrooke | ECON-BNE | 0.000 $\pm$ 0.000 | 0.0000 | 0.062 | 8 / 16 |
| Haggling: vegbrooke | Joint-PSRL | 0.822 $\pm$ 0.000 | 0.0000 | 0.849 | 8 / 16 |
| Haggling: vegbrooke | MAP-Type-Greedy | 0.000 $\pm$ 0.000 | 0.0000 | 0.250 | 8 / 16 |
| Haggling: vegbrooke | PACT | 0.822 $\pm$ 0.000 | 0.0000 | 0.924 | 8 / 16 |
| Haggling: vegbrooke | PACT+ | 0.822 $\pm$ 0.000 | 0.0000 | 0.924 | 8 / 16 |
| Haggling: vegbrooke | PSRL-NoType | 1.332 $\pm$ 0.000 | 0.1332 | 0.062 | 8 / 16 |
| Haggling: vegbrooke | Random | 2.498 $\pm$ 0.000 | 0.1332 | 0.062 | 8 / 16 |
| Multi-item: fruitville | A-ToM-1 | 3.939 $\pm$ 0.000 | 0.1970 | 0.062 | 8 / 16 |
| Multi-item: fruitville | ECON-BNE | 0.606 $\pm$ 0.000 | 0.0303 | 0.062 | 8 / 16 |
| Multi-item: fruitville | Joint-PSRL | 0.333 $\pm$ 0.000 | 0.0121 | 0.750 | 8 / 16 |
| Multi-item: fruitville | MAP-Type-Greedy | 0.091 $\pm$ 0.000 | 0.0000 | 0.735 | 8 / 16 |
| Multi-item: fruitville | PACT | 0.576 $\pm$ 0.000 | 0.0121 | 0.967 | 8 / 16 |
| Multi-item: fruitville | PACT+ | 0.636 $\pm$ 0.000 | 0.0182 | 0.984 | 8 / 16 |
| Multi-item: fruitville | PSRL-NoType | 1.545 $\pm$ 0.000 | 0.1303 | 0.062 | 8 / 16 |
| Multi-item: fruitville | Random | 7.667 $\pm$ 0.000 | 0.2939 | 0.062 | 8 / 16 |
| Multi-item: vegbrooke | A-ToM-1 | 1.212 $\pm$ 0.000 | 0.0606 | 0.062 | 8 / 16 |
| Multi-item: vegbrooke | ECON-BNE | 0.000 $\pm$ 0.000 | 0.0000 | 0.062 | 8 / 16 |
| Multi-item: vegbrooke | Joint-PSRL | 0.364 $\pm$ 0.000 | 0.0121 | 0.737 | 8 / 16 |
| Multi-item: vegbrooke | MAP-Type-Greedy | 0.061 $\pm$ 0.000 | 0.0000 | 0.614 | 8 / 16 |
| Multi-item: vegbrooke | PACT | 0.576 $\pm$ 0.000 | 0.0121 | 0.967 | 8 / 16 |
| Multi-item: vegbrooke | PACT+ | 0.636 $\pm$ 0.000 | 0.0182 | 0.984 | 8 / 16 |
| Multi-item: vegbrooke | PSRL-NoType | 1.485 $\pm$ 0.000 | 0.1303 | 0.062 | 8 / 16 |
| Multi-item: vegbrooke | Random | 7.576 $\pm$ 0.000 | 0.2939 | 0.062 | 8 / 16 |
| Pub: london | A-ToM-1 | 0.000 $\pm$ 0.000 | 0.0000 | 0.004 | 16 / 256 |
| Pub: london | ECON-BNE | 0.000 $\pm$ 0.000 | 0.0000 | 0.004 | 16 / 256 |
| Pub: london | Joint-PSRL | 0.000 $\pm$ 0.000 | 0.0000 | 0.078 | 16 / 256 |
| Pub: london | MAP-Type-Greedy | 0.000 $\pm$ 0.000 | 0.0000 | 0.580 | 16 / 256 |
| Pub: london | PACT | 0.000 $\pm$ 0.000 | 0.0000 | 0.580 | 16 / 256 |
| Pub: london | PACT+ | 0.000 $\pm$ 0.000 | 0.0000 | 0.580 | 16 / 256 |
| Pub: london | PSRL-NoType | 0.000 $\pm$ 0.000 | 0.0000 | 0.004 | 16 / 256 |
| Pub: london | Random | 34.339 $\pm$ 0.000 | 1.9592 | 0.004 | 16 / 256 |
| Pub: london_mini | A-ToM-1 | 0.000 $\pm$ 0.000 | 0.0000 | 0.062 | 8 / 16 |
| Pub: london_mini | ECON-BNE | 0.000 $\pm$ 0.000 | 0.0000 | 0.062 | 8 / 16 |
| Pub: london_mini | Joint-PSRL | 0.000 $\pm$ 0.000 | 0.0000 | 0.145 | 8 / 16 |
| Pub: london_mini | MAP-Type-Greedy | 0.000 $\pm$ 0.000 | 0.0000 | 0.390 | 8 / 16 |
| Pub: london_mini | PACT | 0.000 $\pm$ 0.000 | 0.0000 | 0.390 | 8 / 16 |
| Pub: london_mini | PACT+ | 0.000 $\pm$ 0.000 | 0.0000 | 0.390 | 8 / 16 |
| Pub: london_mini | PSRL-NoType | 0.000 $\pm$ 0.000 | 0.0000 | 0.062 | 8 / 16 |
| Pub: london_mini | Random | 22.619 $\pm$ 0.000 | 1.1900 | 0.062 | 8 / 16 |

Persona-value selection seeds: 0..4; held-out report seeds: 1000..1000.
Gaussian likelihood sigma is 0.08 after per-player normalization to [0,1]. All planning is exact enumeration, not a CCE LP.
