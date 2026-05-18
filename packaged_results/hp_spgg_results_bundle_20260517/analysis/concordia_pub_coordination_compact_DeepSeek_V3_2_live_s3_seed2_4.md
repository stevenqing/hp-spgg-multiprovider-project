# Compact Concordia Pub Coordination Results

Config: `london_mini`
Model: `DeepSeek-V3.2`
Seeds: `[2, 3, 4]`

| method | episodes | focal_score_mean | focal_score_min_mean | coordination_rate_mean | valid_action_rate_mean |
|---|---:|---:|---:|---:|---:|
| oracle_joint | 3 | 1.3333 | 1.1667 | 1.0000 | 1.0000 |
| hpsmg_plus_proxy | 3 | 1.0139 | 0.9167 | 0.8333 | 1.0000 |
| atom_tom1 | 3 | 0.7083 | 0.5833 | 0.6667 | 1.0000 |
| econ_bne | 3 | 0.7083 | 0.5833 | 0.6667 | 1.0000 |
| llm_belief | 3 | 0.7083 | 0.5833 | 0.6667 | 1.0000 |
| llm_greedy | 3 | 0.7083 | 0.5833 | 0.6667 | 1.0000 |
