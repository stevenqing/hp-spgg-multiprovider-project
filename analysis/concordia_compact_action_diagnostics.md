# Concordia Compact Action Diagnostics

Source: `analysis/concordia_pub_coordination_compact_DeepSeek_V3_2_live_s5.json`
Config: `london_mini`
Model: `DeepSeek-V3.2`
Seeds: `[0, 1, 2, 3, 4]`

## Prompt-Only Baseline Collapse

This diagnostic checks whether the prompt-only baselines produced identical joint actions per seed. Identical actions necessarily produce identical payoff scores.

| seed | prompt_only_unique_joint_actions | collapsed |
|---:|---:|---|
| 0 | 1 | yes |
| 1 | 1 | yes |
| 2 | 1 | yes |
| 3 | 1 | yes |
| 4 | 1 | yes |

Collapsed seeds: `5/5`

## Per-Seed Actions

| seed | method | focal_score_mean | coordination_rate | joint_action |
|---:|---|---:|---:|---|
| 0 | llm_greedy | 0.7500 | 0.5000 | Noah=The Golden Fleece; Sophie=The Red Lion; Benjamin=The Golden Fleece; Amelia=The Golden Fleece; Molly=The Red Lion |
| 0 | llm_belief | 0.7500 | 0.5000 | Noah=The Golden Fleece; Sophie=The Red Lion; Benjamin=The Golden Fleece; Amelia=The Golden Fleece; Molly=The Red Lion |
| 0 | atom_tom1 | 0.7500 | 0.5000 | Noah=The Golden Fleece; Sophie=The Red Lion; Benjamin=The Golden Fleece; Amelia=The Golden Fleece; Molly=The Red Lion |
| 0 | econ_bne | 0.7500 | 0.5000 | Noah=The Golden Fleece; Sophie=The Red Lion; Benjamin=The Golden Fleece; Amelia=The Golden Fleece; Molly=The Red Lion |
| 0 | hpsmg_plus_proxy | 1.2500 | 1.0000 | Noah=The Golden Fleece; Sophie=The Golden Fleece; Benjamin=The Golden Fleece; Amelia=The Golden Fleece; Molly=The Golden Fleece |
| 0 | oracle_joint | 1.2500 | 1.0000 | Noah=The Red Lion; Sophie=The Red Lion; Benjamin=The Red Lion; Amelia=The Red Lion; Molly=The Red Lion |
| 1 | llm_greedy | 1.2500 | 0.5000 | Evie=The Crooked Billet; Jack=The Clapton Hart; Alexander=The Crooked Billet; William=The Clapton Hart; Thomas=The Clapton Hart |
| 1 | llm_belief | 1.2500 | 0.5000 | Evie=The Crooked Billet; Jack=The Clapton Hart; Alexander=The Crooked Billet; William=The Clapton Hart; Thomas=The Clapton Hart |
| 1 | atom_tom1 | 1.2500 | 0.5000 | Evie=The Crooked Billet; Jack=The Clapton Hart; Alexander=The Crooked Billet; William=The Clapton Hart; Thomas=The Clapton Hart |
| 1 | econ_bne | 1.2500 | 0.5000 | Evie=The Crooked Billet; Jack=The Clapton Hart; Alexander=The Crooked Billet; William=The Clapton Hart; Thomas=The Clapton Hart |
| 1 | hpsmg_plus_proxy | 1.2500 | 0.5000 | Evie=The Crooked Billet; Jack=The Clapton Hart; Alexander=The Crooked Billet; William=The Clapton Hart; Thomas=The Clapton Hart |
| 1 | oracle_joint | 1.2500 | 1.0000 | Evie=The Clapton Hart; Jack=The Clapton Hart; Alexander=The Clapton Hart; William=The Clapton Hart; Thomas=The Clapton Hart |
| 2 | llm_greedy | 0.7917 | 0.5000 | Thomas=The Crooked Billet; Harry=The Princess of Wales; Phoebe=The Crooked Billet; Jacob=The Crooked Billet; Lily=The Princess of Wales |
| 2 | llm_belief | 0.7917 | 0.5000 | Thomas=The Crooked Billet; Harry=The Princess of Wales; Phoebe=The Crooked Billet; Jacob=The Crooked Billet; Lily=The Princess of Wales |
| 2 | atom_tom1 | 0.7917 | 0.5000 | Thomas=The Crooked Billet; Harry=The Princess of Wales; Phoebe=The Crooked Billet; Jacob=The Crooked Billet; Lily=The Princess of Wales |
| 2 | econ_bne | 0.7917 | 0.5000 | Thomas=The Crooked Billet; Harry=The Princess of Wales; Phoebe=The Crooked Billet; Jacob=The Crooked Billet; Lily=The Princess of Wales |
| 2 | hpsmg_plus_proxy | 0.7917 | 0.5000 | Thomas=The Crooked Billet; Harry=The Princess of Wales; Phoebe=The Crooked Billet; Jacob=The Crooked Billet; Lily=The Princess of Wales |
| 2 | oracle_joint | 1.2500 | 1.0000 | Thomas=The Princess of Wales; Harry=The Princess of Wales; Phoebe=The Princess of Wales; Jacob=The Princess of Wales; Lily=The Princess of Wales |
| 3 | llm_greedy | 0.5000 | 1.0000 | Henry=The King's Head; Ruby=The King's Head; William=The Black Swan; Evie=The Black Swan; Logan=The King's Head |
| 3 | llm_belief | 0.5000 | 1.0000 | Henry=The King's Head; Ruby=The King's Head; William=The Black Swan; Evie=The Black Swan; Logan=The King's Head |
| 3 | atom_tom1 | 0.5000 | 1.0000 | Henry=The King's Head; Ruby=The King's Head; William=The Black Swan; Evie=The Black Swan; Logan=The King's Head |
| 3 | econ_bne | 0.5000 | 1.0000 | Henry=The King's Head; Ruby=The King's Head; William=The Black Swan; Evie=The Black Swan; Logan=The King's Head |
| 3 | hpsmg_plus_proxy | 1.0000 | 1.0000 | Henry=The Black Swan; Ruby=The Black Swan; William=The Black Swan; Evie=The Black Swan; Logan=The Black Swan |
| 3 | oracle_joint | 1.5000 | 1.0000 | Henry=The King's Head; Ruby=The King's Head; William=The King's Head; Evie=The King's Head; Logan=The King's Head |
| 4 | llm_greedy | 0.8333 | 0.5000 | Lily=The Queen's Arms; Poppy=The King's Head; Jessica=The King's Head; Michael=The King's Head; Emily=The Queen's Arms |
| 4 | llm_belief | 0.8333 | 0.5000 | Lily=The Queen's Arms; Poppy=The King's Head; Jessica=The King's Head; Michael=The King's Head; Emily=The Queen's Arms |
| 4 | atom_tom1 | 0.8333 | 0.5000 | Lily=The Queen's Arms; Poppy=The King's Head; Jessica=The King's Head; Michael=The King's Head; Emily=The Queen's Arms |
| 4 | econ_bne | 0.8333 | 0.5000 | Lily=The Queen's Arms; Poppy=The King's Head; Jessica=The King's Head; Michael=The King's Head; Emily=The Queen's Arms |
| 4 | hpsmg_plus_proxy | 1.2500 | 1.0000 | Lily=The King's Head; Poppy=The King's Head; Jessica=The King's Head; Michael=The King's Head; Emily=The King's Head |
| 4 | oracle_joint | 1.2500 | 1.0000 | Lily=The King's Head; Poppy=The King's Head; Jessica=The King's Head; Michael=The King's Head; Emily=The King's Head |
