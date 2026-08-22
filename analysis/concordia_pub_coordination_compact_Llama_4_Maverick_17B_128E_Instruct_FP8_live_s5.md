# Compact Concordia Pub Coordination Results

Config: `london_mini`
Model: `Llama-4-Maverick-17B-128E-Instruct-FP8`
Seeds: `[0, 1, 2, 3, 4]`

| method | episodes | focal_score_mean | focal_score_min_mean | coordination_rate_mean | valid_action_rate_mean |
|---|---:|---:|---:|---:|---:|
| hpsmg_plus_joint_proxy | 5 | 1.3000 | 1.1000 | 1.0000 | 1.0000 |
| oracle_joint | 5 | 1.3000 | 1.1000 | 1.0000 | 1.0000 |
| atom_tom1_mech | 5 | 1.1083 | 0.9500 | 0.8000 | 1.0000 |
| econ_bne_mech | 5 | 1.1083 | 0.9500 | 0.8000 | 1.0000 |
| hpsmg_plus_proxy | 5 | 1.1083 | 0.9500 | 0.8000 | 1.0000 |
| atom_tom1 | 5 | 0.8250 | 0.6500 | 0.6000 | 1.0000 |
| econ_bne | 5 | 0.8250 | 0.6500 | 0.6000 | 1.0000 |
| llm_belief | 5 | 0.8250 | 0.6500 | 0.6000 | 1.0000 |
| llm_greedy | 5 | 0.8250 | 0.6500 | 0.6000 | 1.0000 |
