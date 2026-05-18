# SOTOPIA-Hard Official Reconstruction Summary

Generated: 2026-05-17 21:45:56

Metric: SOTOPIA 7-dimension evaluator score; higher is better. Each baseline uses the same 70 reconstructed official SOTOPIA-Hard combinations, DeepSeek-V3.2 player calls, DeepSeek-V3.2 evaluator calls, and six-turn cap.

## Overall

| baseline | model_slug | cases | target_cases | complete | mean_overall | agent_1_overall | agent_2_overall | source |
|---|---|---|---|---|---|---|---|---|
| hpsmg_plus | DeepSeek_V3_2 | 70 | 70 | True | 3.1939 | 2.9735 | 3.4143 | analysis/sotopia_hard_official_DeepSeek_V3_2_hpsmg_plus_all70.json |
| econ_bne | DeepSeek_V3_2 | 70 | 70 | True | 3.1765 | 2.9939 | 3.3592 | analysis/sotopia_hard_official_DeepSeek_V3_2_econ_bne_all70.json |
| llm_greedy | DeepSeek_V3_2 | 70 | 70 | True | 3.1643 | 2.9265 | 3.4020 | analysis/sotopia_hard_official_DeepSeek_V3_2_llm_greedy_all70.json |
| atom_tom1 | DeepSeek_V3_2 | 70 | 70 | True | 3.1061 | 2.8776 | 3.3347 | analysis/sotopia_hard_official_DeepSeek_V3_2_atom_tom1_all70.json |
| llm_belief | DeepSeek_V3_2 | 70 | 70 | True | 3.0776 | 2.8612 | 3.2939 | analysis/sotopia_hard_official_DeepSeek_V3_2_llm_belief_all70.json |

## Dimension Means

| baseline | model_slug | dimension | agent_1 | agent_2 | mean_agents |
|---|---|---|---|---|---|
| atom_tom1 | DeepSeek_V3_2 | believability | 8.0429 | 8.5286 | 8.2857 |
| atom_tom1 | DeepSeek_V3_2 | relationship | 2.1571 | 3.2429 | 2.7000 |
| atom_tom1 | DeepSeek_V3_2 | knowledge | 7.0000 | 7.5571 | 7.2786 |
| atom_tom1 | DeepSeek_V3_2 | secret | -2.8571 | -2.9000 | -2.8786 |
| atom_tom1 | DeepSeek_V3_2 | social_rules | -1.9000 | -1.2429 | -1.5714 |
| atom_tom1 | DeepSeek_V3_2 | financial_and_material_benefits | 1.7286 | 1.2000 | 1.4643 |
| atom_tom1 | DeepSeek_V3_2 | goal | 5.9714 | 6.9571 | 6.4643 |
| econ_bne | DeepSeek_V3_2 | believability | 8.0286 | 8.5429 | 8.2857 |
| econ_bne | DeepSeek_V3_2 | relationship | 2.5143 | 3.4143 | 2.9643 |
| econ_bne | DeepSeek_V3_2 | knowledge | 6.9000 | 7.3857 | 7.1429 |
| econ_bne | DeepSeek_V3_2 | secret | -2.5429 | -2.4000 | -2.4714 |
| econ_bne | DeepSeek_V3_2 | social_rules | -1.8571 | -1.4714 | -1.6643 |
| econ_bne | DeepSeek_V3_2 | financial_and_material_benefits | 1.7429 | 1.0143 | 1.3786 |
| econ_bne | DeepSeek_V3_2 | goal | 6.1714 | 7.0286 | 6.6000 |
| hpsmg_plus | DeepSeek_V3_2 | believability | 7.9714 | 8.4429 | 8.2071 |
| hpsmg_plus | DeepSeek_V3_2 | relationship | 2.2000 | 3.2000 | 2.7000 |
| hpsmg_plus | DeepSeek_V3_2 | knowledge | 7.0143 | 7.5714 | 7.2929 |
| hpsmg_plus | DeepSeek_V3_2 | secret | -2.2714 | -2.1571 | -2.2143 |
| hpsmg_plus | DeepSeek_V3_2 | social_rules | -1.9143 | -1.2571 | -1.5857 |
| hpsmg_plus | DeepSeek_V3_2 | financial_and_material_benefits | 1.8000 | 1.2286 | 1.5143 |
| hpsmg_plus | DeepSeek_V3_2 | goal | 6.0143 | 6.8714 | 6.4429 |
| llm_belief | DeepSeek_V3_2 | believability | 8.0000 | 8.4000 | 8.2000 |
| llm_belief | DeepSeek_V3_2 | relationship | 2.2571 | 3.1143 | 2.6857 |
| llm_belief | DeepSeek_V3_2 | knowledge | 6.9000 | 7.3286 | 7.1143 |
| llm_belief | DeepSeek_V3_2 | secret | -2.8000 | -2.6429 | -2.7214 |
| llm_belief | DeepSeek_V3_2 | social_rules | -2.1286 | -1.4000 | -1.7643 |
| llm_belief | DeepSeek_V3_2 | financial_and_material_benefits | 1.8286 | 1.2714 | 1.5500 |
| llm_belief | DeepSeek_V3_2 | goal | 5.9714 | 6.9857 | 6.4786 |
| llm_greedy | DeepSeek_V3_2 | believability | 7.9429 | 8.6000 | 8.2714 |
| llm_greedy | DeepSeek_V3_2 | relationship | 2.0143 | 3.0429 | 2.5286 |
| llm_greedy | DeepSeek_V3_2 | knowledge | 7.1286 | 7.7714 | 7.4500 |
| llm_greedy | DeepSeek_V3_2 | secret | -2.6286 | -2.5143 | -2.5714 |
| llm_greedy | DeepSeek_V3_2 | social_rules | -2.2286 | -1.6714 | -1.9500 |
| llm_greedy | DeepSeek_V3_2 | financial_and_material_benefits | 2.1000 | 1.3286 | 1.7143 |
| llm_greedy | DeepSeek_V3_2 | goal | 6.1571 | 7.2571 | 6.7071 |
