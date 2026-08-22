# Concordia Haggling Joint-Optimal Focal Intervals

The compact Haggling `oracle_joint` maximizes total buyer+seller payoff. Because price is a transfer, many accepted prices have identical total surplus but different focal-player payoffs. The stored `oracle_joint` focal score is therefore a tie-break point, not the focal-best value within the joint-optimal set.

`oracle_joint` itself is pure total surplus in `run_haggling_compact.py`. The `hpsmg_plus_blend_a0` implementation is not pure total surplus: at alpha=0 it uses `buyer_score + seller_score + 0.35 * min(buyer_score, seller_score) + 0.15 * nash`.

| Config | joint-opt focal interval | stored oracle_joint focal | PACT+ focal | joint surplus oracle / PACT+ | min surplus oracle / PACT+ | Nash oracle / PACT+ |
|---|---:|---:|---:|---:|---:|---:|
| Fruitville: gullible buyer | [1.400, 13.400] | 7.000 | 7.400 | 5.000 / 5.000 | 0.000 / 2.000 | 0.000 / 6.000 |
| Vegbrooke: stubborn seller | [-5.100, 7.300] | -0.333 | 1.100 | 0.520 / 0.520 | -0.593 / 0.133 | 0.000 / 0.167 |
| Multi-item: cumulative | [0.000, 12.000] | 5.600 | 6.000 | 4.000 / 4.000 | 0.000 / 2.000 | 0.000 / 4.000 |
| Multi-item: gullible | [-0.967, 14.600] | 6.300 | 6.767 | 4.544 / 4.544 | -0.311 / 2.000 | 0.000 / 5.089 |

Interpretation:

- The Haggling `oracle_joint` focal value can look worse because it is an arbitrary tie-break inside a flat total-surplus optimum set.
- On all four selected configs, PACT+ matches the `oracle_joint` mean joint surplus while choosing a more balanced/focal-favorable split than the stored tie-break.
- PACT+ is not claimed to reach the upper end of the joint-optimal focal interval; the interval is a diagnostic for transfer-allocation indeterminacy, not a new strict ceiling.
