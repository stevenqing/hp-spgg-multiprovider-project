# Compact Concordia Pub Coordination Results

Config: `london_mini`
Model: `gpt-5.4-nano-20260317`
Seeds: `[0, 1, 2, 3, 4]`

| method | episodes | focal_score_mean | focal_score_min_mean | coordination_rate_mean | valid_action_rate_mean |
|---|---:|---:|---:|---:|---:|
| hpsmg_plus_joint_proxy | 5 | 1.3000 | 1.1000 | 1.0000 | 1.0000 |
| oracle_joint | 5 | 1.3000 | 1.1000 | 1.0000 | 1.0000 |
| econ_bne | 5 | 1.1250 | 0.9000 | 0.8000 | 1.0000 |
| atom_tom1_mech | 5 | 1.1083 | 0.9500 | 0.8000 | 1.0000 |
| econ_bne_mech | 5 | 1.1083 | 0.9500 | 0.8000 | 1.0000 |
| hpsmg_plus_proxy | 5 | 1.1083 | 0.9500 | 0.8000 | 1.0000 |
| llm_greedy | 5 | 1.0500 | 0.8000 | 0.9000 | 1.0000 |
| atom_tom1 | 5 | 1.0083 | 0.7500 | 0.7000 | 1.0000 |
| llm_belief | 5 | 1.0083 | 0.7500 | 0.7000 | 1.0000 |
