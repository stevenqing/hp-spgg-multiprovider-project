# E-B: Iterated Concordia-Derived Compact Benchmark

This is a constructed iterated variant, not Concordia's native one-shot protocol. Types are fixed for K episodes and PF is imposed. Exact upstream payoff functions and finite action menus are reused.

The replay is backbone-invariant because no LLM is called; duplicating the same exact-payoff rows under four model names would not constitute independent evidence.

| config | method | cumulative regret | late instant regret | true-type mass | storage |
|---|---|---:|---:|---:|---:|
| Pub: london_mini | A-ToM-1 | 0.000 $\pm$ 0.000 | 0.0000 | 0.062 | 8 / 16 |
| Pub: london_mini | ECON-BNE | 0.000 $\pm$ 0.000 | 0.0000 | 0.062 | 8 / 16 |
| Pub: london_mini | Joint-PSRL | 0.000 $\pm$ 0.000 | 0.0000 | 0.298 | 8 / 16 |
| Pub: london_mini | MAP-Type-Greedy | 0.000 $\pm$ 0.000 | 0.0000 | 0.643 | 8 / 16 |
| Pub: london_mini | PACT | 0.000 $\pm$ 0.000 | 0.0000 | 0.643 | 8 / 16 |
| Pub: london_mini | PACT+ | 0.000 $\pm$ 0.000 | 0.0000 | 0.643 | 8 / 16 |
| Pub: london_mini | PSRL-NoType | 0.000 $\pm$ 0.000 | 0.0000 | 0.062 | 8 / 16 |
| Pub: london_mini | Random | 3.808 $\pm$ 0.000 | 0.7389 | 0.062 | 8 / 16 |

Selection seeds: 0..29; held-out report seeds: 99000..99000.
Gaussian likelihood sigma is 0.08 after per-player normalization to [0,1]. All planning is exact enumeration, not a CCE LP.
