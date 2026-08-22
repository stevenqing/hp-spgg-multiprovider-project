# Concordia Haggling Pareto beta=0 Legacy Joint Endpoint

Source status: the current working tree and retained ZIP artifacts do not contain the `concordia_haggling_blend_*.json` files referenced by `scripts/plot_fig_haggling_pareto.py`. The four endpoint values below are recovered from the retained historical compact Haggling JSON blobs at Git snapshot `9e7f12b`, using the `oracle_joint` summary row. They are legacy total-surplus reference points, not the true focal oracle.

For these four selected configurations, each episode has exactly one focal player, so the per-episode summed focal score equals the episode `focal_score_mean`; averaging across the 30 seeds gives the same number as the `summary[].focal_score_mean` field.

| Config | Domain | Episodes | beta=0 / oracle_joint focal score | Source |
|---|---|---:|---:|---|
| Fruitville: gullible buyer | haggling | 30 | 7.000000 | `9e7f12b:analysis/concordia_haggling_compact_fruitville_gullible_s30.json:L128` |
| Vegbrooke: stubborn seller | haggling | 30 | -0.333333 | `9e7f12b:analysis/concordia_haggling_compact_vegbrooke_stubborn_s30.json:L128` |
| Multi-item: cumulative | haggling_multi_item | 30 | 5.600000 | `9e7f12b:analysis/concordia_haggling_multi_item_compact_cumulative_score_s30.json:L128` |
| Multi-item: gullible | haggling_multi_item | 30 | 6.300000 | `9e7f12b:analysis/concordia_haggling_multi_item_compact_fruitville_gullible_s30.json:L117` |

The true upper reference for the plotted Haggling metric is `oracle_focal`, not `oracle_joint`. See `analysis/concordia_haggling_true_oracle_focal.md` for the recomputed focal oracle values.

Metric interpretation:

- The Concordia main radar/grouped-bar script plots `focal_score_mean` on both Pub Coordination and Haggling panels, not joint welfare or Nash product.
- In legacy Pub Coordination JSONs, the row may be stored under `oracle_joint`, but the recorded policy is focal, so the active script relabels that dashed reference as `oracle_focal`.
- In Haggling, `oracle_joint` and `oracle_focal` are distinct policies: `oracle_joint` maximizes total buyer+seller payoff, while `oracle_focal` maximizes the reported focal payoff. When an `oracle_joint` row is plotted, its y-value is still that policy's achieved `focal_score_mean`, not the total-payoff objective value.
- Total buyer+seller payoff in Haggling is flat over many feasible transfer prices, so the stored `oracle_joint` focal values above are tie-break points inside a broader joint-optimal focal interval. See `analysis/concordia_haggling_joint_optimal_focal_intervals.md` for the interval audit.
- The current `hpsmg_plus_blend_a0` implementation uses a shaped joint/fairness/Nash objective, so the safest provenance statement is to cite these four beta=0 endpoint numbers as recovered `oracle_joint` focal-score values from the historical compact JSONs, not as newly regenerated blend JSON values.