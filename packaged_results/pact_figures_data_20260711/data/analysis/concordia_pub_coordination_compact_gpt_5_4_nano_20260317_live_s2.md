# Compact Concordia Pub Coordination Results

Config: `london_mini`
Model: `gpt-5.4-nano-20260317`
Seeds: `[0, 1]`

| method | episodes | focal_score_mean | focal_score_min_mean | coordination_rate_mean | valid_action_rate_mean |
|---|---:|---:|---:|---:|---:|
| hpsmg_plus_joint_proxy | 2 | 1.2500 | 1.0000 | 1.0000 | 1.0000 |
| oracle_joint | 2 | 1.2500 | 1.0000 | 1.0000 | 1.0000 |
| atom_tom1_mech | 2 | 1.2500 | 1.0000 | 0.7500 | 1.0000 |
| econ_bne_mech | 2 | 1.2500 | 1.0000 | 0.7500 | 1.0000 |
| hpsmg_plus_proxy | 2 | 1.2500 | 1.0000 | 0.7500 | 1.0000 |
| econ_bne | 2 | 1.0000 | 0.7500 | 0.7500 | 1.0000 |
| atom_tom1 | 2 | 1.0000 | 0.7500 | 0.5000 | 1.0000 |
| llm_belief | 2 | 1.0000 | 0.7500 | 0.5000 | 1.0000 |
| llm_greedy | 2 | 0.6250 | 0.2500 | 0.7500 | 1.0000 |

## Information Fairness Audit

| method | mode | all_preferences | full_relationship_matrix | known_payoff_model | privileged_oracle_objective | comparable_baseline |
|---|---|---|---|---|---|---|
| llm_greedy | decentralized_per_player_prompt | false | false | false | false | true |
| llm_belief | decentralized_per_player_prompt | false | false | false | false | true |
| atom_tom1 | decentralized_per_player_prompt | false | false | false | false | true |
| econ_bne | decentralized_per_player_prompt | false | false | false | false | true |
| atom_tom1_mech | centralized_full_case | true | true | true | false | true |
| econ_bne_mech | centralized_full_case | true | true | true | false | true |
| hpsmg_plus_proxy | centralized_full_case | true | true | true | false | true |
| hpsmg_plus_joint_proxy | centralized_full_case | true | true | true | false | true |
| oracle_joint | privileged_upper_bound | true | true | true | true | false |
