# E-B: Iterated Concordia-Derived Compact Benchmark

This is a constructed iterated variant, not Concordia's native one-shot protocol. Types are fixed for K episodes and PF is imposed. Exact upstream payoff functions and finite action menus are reused.

The replay is backbone-invariant because no LLM is called; duplicating the same exact-payoff rows under four model names would not constitute independent evidence.

| config | method | cumulative regret | late instant regret | true-type mass | storage |
|---|---|---:|---:|---:|---:|
| Haggling: fruitville gullible | A-ToM-1 | 14.667 $\pm$ 0.000 | 0.7333 | 0.062 | 8 / 16 |
| Haggling: fruitville gullible | ECON-BNE | 4.000 $\pm$ 0.000 | 0.2000 | 0.062 | 8 / 16 |
| Haggling: fruitville gullible | Joint-PSRL | 0.000 $\pm$ 0.000 | 0.0000 | 0.424 | 8 / 16 |
| Haggling: fruitville gullible | MAP-Type-Greedy | 0.000 $\pm$ 0.000 | 0.0000 | 0.675 | 8 / 16 |
| Haggling: fruitville gullible | PACT | 0.000 $\pm$ 0.000 | 0.0000 | 0.675 | 8 / 16 |
| Haggling: fruitville gullible | PACT+ | 0.000 $\pm$ 0.000 | 0.0000 | 0.675 | 8 / 16 |
| Haggling: fruitville gullible | PSRL-NoType | 0.000 $\pm$ 0.000 | 0.0000 | 0.062 | 8 / 16 |
| Haggling: fruitville gullible | Random | 9.578 $\pm$ 0.000 | 0.5089 | 0.062 | 8 / 16 |
| Haggling: vegbrooke stubborn | A-ToM-1 | 4.444 $\pm$ 0.000 | 0.2222 | 0.062 | 8 / 16 |
| Haggling: vegbrooke stubborn | ECON-BNE | 4.444 $\pm$ 0.000 | 0.2222 | 0.062 | 8 / 16 |
| Haggling: vegbrooke stubborn | Joint-PSRL | 0.667 $\pm$ 0.000 | 0.0000 | 0.997 | 8 / 16 |
| Haggling: vegbrooke stubborn | MAP-Type-Greedy | 4.444 $\pm$ 0.000 | 0.2222 | 0.250 | 8 / 16 |
| Haggling: vegbrooke stubborn | PACT | 0.444 $\pm$ 0.000 | 0.0000 | 0.999 | 8 / 16 |
| Haggling: vegbrooke stubborn | PACT+ | 0.000 $\pm$ 0.000 | 0.0000 | 1.000 | 8 / 16 |
| Haggling: vegbrooke stubborn | PSRL-NoType | 2.889 $\pm$ 0.000 | 0.1333 | 0.062 | 8 / 16 |
| Haggling: vegbrooke stubborn | Random | 6.667 $\pm$ 0.000 | 0.3333 | 0.062 | 8 / 16 |
| Multi-item: cumulative score | A-ToM-1 | 0.000 $\pm$ 0.000 | 0.0000 | 0.062 | 8 / 16 |
| Multi-item: cumulative score | ECON-BNE | 9.091 $\pm$ 0.000 | 0.4545 | 0.062 | 8 / 16 |
| Multi-item: cumulative score | Joint-PSRL | 0.000 $\pm$ 0.000 | 0.0000 | 1.000 | 8 / 16 |
| Multi-item: cumulative score | MAP-Type-Greedy | 0.000 $\pm$ 0.000 | 0.0000 | 1.000 | 8 / 16 |
| Multi-item: cumulative score | PACT | 0.000 $\pm$ 0.000 | 0.0000 | 1.000 | 8 / 16 |
| Multi-item: cumulative score | PACT+ | 0.000 $\pm$ 0.000 | 0.0000 | 1.000 | 8 / 16 |
| Multi-item: cumulative score | PSRL-NoType | 0.000 $\pm$ 0.000 | 0.0000 | 0.062 | 8 / 16 |
| Multi-item: cumulative score | Random | 15.682 $\pm$ 0.000 | 0.8182 | 0.062 | 8 / 16 |
| Multi-item: fruitville gullible | A-ToM-1 | 9.091 $\pm$ 0.000 | 0.4545 | 0.062 | 8 / 16 |
| Multi-item: fruitville gullible | ECON-BNE | 1.818 $\pm$ 0.000 | 0.0909 | 0.062 | 8 / 16 |
| Multi-item: fruitville gullible | Joint-PSRL | 0.000 $\pm$ 0.000 | 0.0000 | 0.481 | 8 / 16 |
| Multi-item: fruitville gullible | MAP-Type-Greedy | 0.000 $\pm$ 0.000 | 0.0000 | 0.731 | 8 / 16 |
| Multi-item: fruitville gullible | PACT | 0.000 $\pm$ 0.000 | 0.0000 | 0.731 | 8 / 16 |
| Multi-item: fruitville gullible | PACT+ | 0.000 $\pm$ 0.000 | 0.0000 | 0.731 | 8 / 16 |
| Multi-item: fruitville gullible | PSRL-NoType | 0.000 $\pm$ 0.000 | 0.0000 | 0.062 | 8 / 16 |
| Multi-item: fruitville gullible | Random | 5.606 $\pm$ 0.000 | 0.2485 | 0.062 | 8 / 16 |
| Pub: capetown | A-ToM-1 | 3.514 $\pm$ 0.000 | 0.1757 | 0.000 | 24 / 4096 |
| Pub: capetown | ECON-BNE | 3.514 $\pm$ 0.000 | 0.1757 | 0.000 | 24 / 4096 |
| Pub: capetown | Joint-PSRL | 0.155 $\pm$ 0.000 | 0.0155 | 0.075 | 24 / 4096 |
| Pub: capetown | MAP-Type-Greedy | 0.000 $\pm$ 0.000 | 0.0000 | 0.664 | 24 / 4096 |
| Pub: capetown | PACT | 0.104 $\pm$ 0.000 | 0.0052 | 0.675 | 24 / 4096 |
| Pub: capetown | PACT+ | 0.104 $\pm$ 0.000 | 0.0052 | 0.675 | 24 / 4096 |
| Pub: capetown | PSRL-NoType | 0.000 $\pm$ 0.000 | 0.0000 | 0.000 | 24 / 4096 |
| Pub: capetown | Random | 38.989 $\pm$ 0.000 | 2.0237 | 0.000 | 24 / 4096 |
| Pub: london_mini | A-ToM-1 | 0.000 $\pm$ 0.000 | 0.0000 | 0.062 | 8 / 16 |
| Pub: london_mini | ECON-BNE | 0.000 $\pm$ 0.000 | 0.0000 | 0.062 | 8 / 16 |
| Pub: london_mini | Joint-PSRL | 0.000 $\pm$ 0.000 | 0.0000 | 0.145 | 8 / 16 |
| Pub: london_mini | MAP-Type-Greedy | 0.000 $\pm$ 0.000 | 0.0000 | 0.390 | 8 / 16 |
| Pub: london_mini | PACT | 0.000 $\pm$ 0.000 | 0.0000 | 0.390 | 8 / 16 |
| Pub: london_mini | PACT+ | 0.000 $\pm$ 0.000 | 0.0000 | 0.390 | 8 / 16 |
| Pub: london_mini | PSRL-NoType | 0.000 $\pm$ 0.000 | 0.0000 | 0.062 | 8 / 16 |
| Pub: london_mini | Random | 22.619 $\pm$ 0.000 | 1.1900 | 0.062 | 8 / 16 |

Selection seeds: 0..29; held-out report seeds: 1000..1000.
Gaussian likelihood sigma is 0.08 after per-player normalization to [0,1]. All planning is exact enumeration, not a CCE LP.
