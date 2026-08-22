# PACT Figure Inventory

20 unique figures are used in the paper across `main.tex` and `appendix.tex`. Each entry below lists the filename, where it appears, and what it shows.

## Main paper figures (6)

| File | Figure # | Section | Content |
|---|---|---|---|
| `main.png` | Figure 1 | §1 Intro | PACT pipeline overview: sample persona → query LLM → score actions under candidate templates → update per-agent posterior |
| `fig10_hp_spgg_cross_model_v3.png` | Figure 4 | §3.1 HP-SPGG | Cumulative regret bars across 4 backbones × 13 baselines, K=20, 5 seeds. PACT family (blue) lowest; LLM-PSRL-verbal (green) trails by 3.9-59× |
| `fig10_beta_sweep_v3.pdf` | Figure 5 | §3.1 β-sweep | PACT⁺ regret vs β ∈ {0, 0.05, 0.1, 0.25, 0.5, 0.75, 1, 1.5} across 4 backbones; justifies β=0.25 selection |
| `fig10_concordia_main_v7.pdf` | Figure 6 | §3.2 Concordia | Radar plot, 2 substrates × 9 axes each: Pub Coordination (9 village configs), Haggling (5 single + 4 multi-item). PACT⁺ blue, oracle dashed, LLM-PSRL-verbal green |
| `fig_sotopia_three_exp_v1.pdf` | Figure 7(a) | §3.3 SOTOPIA | End-of-dialogue focal score on 3 PF-aligned families (Craigslist Δ=+0.06, Revenge Δ=+0.10, Donate Δ=+0.02). 6 baselines incl. LLM-PSRL-verbal |
| `fig_sotopia_traj_v1.pdf` | Figure 7(b) | §3.3 SOTOPIA | Per-turn focal score trajectory k ∈ {1..6} on same 3 families. PACT⁺ climbs monotonically on Revenge from 2.30 → 3.03 |

## Appendix figures (14)

| File | Section | Content |
|---|---|---|
| `fig_e2_type_scaling_v3.pdf` | App. theoretical validation | E-2: type-count scaling, validates Theorem 4.2 √K rate |
| `E2_native_vs_llm_baselines_main.pdf` | App. E-2 supplement | Native Bayesian vs prompted LLM vs external LLM baseline comparison |
| `fig_e1_1_n_scaling.pdf` | App. A.1 (wave-2) | Analytic-tier 9-baseline n-scaling |
| `fig_e1_1_n_scaling_llm.pdf` | App. A.1 (wave-2) | LLM-tier 9-baseline n-scaling on DeepSeek-V3.2 + Llama-Maverick |
| `fig_e1_3_pf_isolation.pdf` | App. A.1 (wave-2) | Prior swap: correlated Dirichlet sweep + shared-type cell |
| `fig_e1_3_lower_bound_shared_type_analytic.pdf` | App. A.1 (wave-2) | Analytic E-1.3+: PACT vs Joint-PSRL-Strict under shared-type prior |
| `fig_e1_3_lower_bound_shared_type_deepseek.pdf` | App. A.1 (wave-2) | DeepSeek-V3.2 E-1.3+ lower-bound figure |
| `fig_e1_3_lower_bound_shared_type_llama_maverick.pdf` | App. A.1 (wave-2) | Llama-Maverick E-1.3+ lower-bound figure |
| `fig_e1_posterior_concentration_v3.pdf` | App. theoretical validation | E-1: posterior concentration over episodes |
| `fig_e3_n_agent_scaling_v3.pdf` | App. theoretical validation | E-3: n-agent scaling validation |
| `fig_e5_cumulative_regret_trajectories_v3.pdf` | App. theoretical validation | E-5: cumulative regret trajectories |
| `fig_sotopia_hard_appendix_v2.pdf` | App. A.5 SOTOPIA detail | Per-backbone aggregate across 4 backbones × 6 baselines × 70 episodes |
| `fig12_decentralized_price.pdf` | App. decentralised | Decentralised PACT variant price-of-decentralisation |

## Notes

- Both `.pdf` (publication quality) and `.png` (preview) versions are included where available.
- `main.png` is the only main-paper figure that exists as PNG only (the source designer kept it as PNG).
- `fig10_hp_spgg_cross_model_v3` is included only as PNG because the LaTeX source uses `.png`. The corresponding `.pdf` exists in the full archive.
- The `PACT_figures_all.zip` archive includes 61 additional files: alternate versions (v3, v4, v5, etc.), unused drafts, and `.png` companions for `.pdf` figures, retained for reproducibility audit.
