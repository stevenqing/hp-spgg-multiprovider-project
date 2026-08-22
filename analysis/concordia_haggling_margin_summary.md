# Concordia Compact Haggling Margin Summary

Proposed method: `hpsmg_plus_joint_proxy`
Best baseline excludes oracle and proposed/HPSMG ablations. Primary ordering uses Nash product margin, then focal-min margin.

| domain | config | episodes | proposed_nash | best_baseline | baseline_nash | nash_margin | proposed_min | baseline_min | min_margin | proposed_focal | baseline_focal | focal_margin | source |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| haggling_multi_item | vegbrooke | 30 | 5.1000 | econ_bne_mech | 4.7833 | 0.3167 | 4.0000 | 3.3667 | 0.6333 | 4.5500 | 4.5500 | 0.0000 | analysis/concordia_haggling_multi_item_compact_vegbrooke_s30.json |
| haggling_multi_item | fruitville_gullible | 30 | 5.0889 | econ_bne_mech | 4.7778 | 0.3111 | 6.7667 | 6.7000 | 0.0667 | 6.7667 | 6.7000 | 0.0667 | analysis/concordia_haggling_multi_item_compact_fruitville_gullible_s30.json |
| haggling | fruitville | 30 | 3.8222 | econ_bne_mech | 3.5611 | 0.2611 | 6.7667 | 6.1000 | 0.6667 | 7.8222 | 7.8222 | 0.0000 | analysis/concordia_haggling_compact_fruitville_s30.json |
| haggling_multi_item | fruitville_multi | 30 | 4.8000 | econ_bne_mech | 4.5500 | 0.2500 | 3.9667 | 3.4667 | 0.5000 | 4.4000 | 4.4000 | 0.0000 | analysis/concordia_haggling_multi_item_compact_fruitville_multi_s30.json |
| haggling | vegbrooke_stubborn | 30 | 0.1667 | econ_bne_mech | 0.1000 | 0.0667 | 1.1000 | 0.9667 | 0.1333 | 1.1000 | 0.9667 | 0.1333 | analysis/concordia_haggling_compact_vegbrooke_stubborn_s30.json |
| haggling | vegbrooke | 30 | 0.2694 | econ_bne_mech | 0.2139 | 0.0556 | 0.9333 | 0.4333 | 0.5000 | 1.9833 | 1.7333 | 0.2500 | analysis/concordia_haggling_compact_vegbrooke_s30.json |
| haggling | fruitville_gullible | 30 | 6.0000 | econ_bne_mech | 6.0000 | 0.0000 | 7.4000 | 7.4000 | 0.0000 | 7.4000 | 7.4000 | 0.0000 | analysis/concordia_haggling_compact_fruitville_gullible_s30.json |
| haggling | vegbrooke_strange_game | 30 | 0.0000 | econ_bne_mech | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | analysis/concordia_haggling_compact_vegbrooke_strange_game_s30.json |
| haggling_multi_item | cumulative_score | 30 | 4.0000 | econ_bne_mech | 4.0000 | 0.0000 | 6.0000 | 6.0000 | 0.0000 | 6.0000 | 6.0000 | 0.0000 | analysis/concordia_haggling_multi_item_compact_cumulative_score_s30.json |
