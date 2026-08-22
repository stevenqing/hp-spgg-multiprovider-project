# HARP Anonymous Experiment Repository

This repository accompanies an anonymous submission on **HARP**, a coordinator for heterogeneous language-model agents that maintains explicit persona beliefs outside the prompt.

It contains the experiment implementations, completed result data, accepted-response caches needed for offline aggregation, plotting scripts, paper-facing figure assets, preregistrations, and integrity manifests. It intentionally contains no Git history, author names, affiliations, email addresses, private endpoints, tenant/application identifiers, credentials, or local machine paths.

The fastest review path is fully offline and makes no provider calls.

## Quick Start

Python 3.11 or 3.12 is recommended.

### Linux or macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/validate_anonymous_experiment_repo.py
```

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts\validate_anonymous_experiment_repo.py
```

A successful check ends with `"status": "ok"`. The validator checks every packaged file against `MANIFEST.csv` and `SHA256SUMS.txt`, rejects missing or extra files, scans for identity-sensitive strings, checks the primary experiment directories, and validates the locked fingerprints for the recent E-H controls and paper-facing figure data.

## Repository Layout

```text
analysis/                     Completed outputs, preregistrations, and accepted caches
artifacts/figures/            Paper-facing PDFs/PNGs and numeric figure payloads
config/                       Public input manifests and provider example configuration
llm_hpgg/                     HP-SPGG simulator and HARP-family implementations
llm_hpgg_com/                 Generic provider adapters
llm_hpgg_concordia/           Concordia integrations
llm_hpgg_sotopia/             SOTOPIA integration and recurrent tracker
llm_courier_dispatch/         Dispatch environment and utilities
llm_courier_dispatch_maassim/ MaaSSim hidden rules and adapters
prompts/                      Persona, action, and judge prompt templates
scripts/                      Experiment, analysis, plotting, and validation entrypoints
MANIFEST.csv                  Category, byte count, and SHA-256 for every packaged file
SHA256SUMS.txt                Portable integrity list
REPOSITORY_METADATA.json      Anonymous release metadata and experiment inventory
```

The directory is ready to initialize as a fresh anonymous Git repository. No `.git/` directory or commit metadata is included.

## Experiments in Paper-Figure Order

Figure 1 is the method overview and contains no experiment. The experiment report below follows the order in which figures appear in the paper. Internal labels such as E-A or E-H are provided only as secondary implementation indexes.

### Main-text Figure 2 — Environment-Matched HP-SPGG

Four LLM backbones are compared under matched persona profiles, uniform priors, payoff tensors, and exact oracles. The completed E-A release contains four 1,500-cell persona-conditioned calibration tensors, native and prompt-baseline outputs, accepted-response caches, 400 method/backbone/seed rows, and aggregate tables.

| Item | Path |
|---|---|
| Paper-facing figure | `artifacts/figures/fig_e_a_hp_spgg_matched_v16.pdf` |
| Numeric figure payload | `artifacts/figures/fig_e_a_hp_spgg_matched_v16_data.json` |
| Runner / aggregator | `scripts/run_e_a_matched_likelihood.py` |
| Paper-size renderer | `scripts/render_hp_spgg_matched_v16.py` |
| Validator | `scripts/validate_hp_spgg_matched_v16.py` |
| Completed data | `analysis/e_a_matched_likelihood/` |

Offline reproduction:

```bash
python scripts/run_e_a_matched_likelihood.py --stage aggregate
python scripts/render_hp_spgg_matched_v16.py
python scripts/validate_hp_spgg_matched_v16.py
```

Do not pass `--force`: forced calibration or run stages may request live provider calls.

### Main-text Figure 3 — Storage Scaling and Component Attribution

The top panel reports agent-count scaling and factored-versus-joint storage. The bottom panel removes belief components and compares centralized with decentralized execution (E-G).

| Panel | Figure asset | Primary code | Completed data |
|---|---|---|---|
| Top: population/storage scaling | `artifacts/figures/fig_e3_n_agent_scaling_v3.pdf` | `scripts/make_fig_e3.py`, `scripts/run_hp_spgg_analytic_scaling.py` | `analysis/hp_spgg_analytic_scaling/`, `analysis/aaai27_supplemental_experiments/` |
| Bottom: component ladder | `artifacts/figures/fig_e_g_ladder_v1.pdf` | `scripts/run_e_g_hp_spgg_component_ladder.py`, `scripts/render_harp_component_ladder_v1.py` | `analysis/e_g_hp_spgg_component_ladder/` |

```bash
python scripts/validate_hp_spgg_analytic_scaling.py
python scripts/validate_e_g_hp_spgg_component_ladder.py
```

### Main-text Figure 4 — MaaSSim Dispatch under Conflict

Panels show realized utility across conflict strength, oracle regret in reject-penalty units, and the utility contribution of different belief sources.

| Item | Path |
|---|---|
| Paper-facing figure | `artifacts/figures/fig_maassim_combined_v22.pdf` |
| Numeric figure payload | `artifacts/figures/fig_maassim_combined_v22_data.json` |
| Runner / mechanism replay | `scripts/replay_maassim_pact_persona_mechanism.py`, `scripts/summarize_maassim_scenario_suite.py` |
| Paper-size renderer | `scripts/render_harp_maassim_main_v22.py` |
| Validator | `scripts/validate_maassim_main_v22.py` |
| Completed data | `analysis/courier_dispatch_maassim/` |

```bash
python scripts/render_harp_maassim_main_v22.py
python scripts/validate_maassim_main_v22.py
```

### Main-text Figure 5 — Concordia Pub Coordination and Haggling

The figure reports focal payoff against exact `oracle_joint` or `oracle_focal` references across selected externally authored configurations.

| Item | Path |
|---|---|
| Paper-facing figure | `artifacts/figures/fig2_concordia_select_v15.pdf` |
| Renderer | `scripts/plot_concordia_selected_main.py` |
| Figure data | `artifacts/paper_data/figure5_bar_data.json`, `artifacts/paper_data/figure5_haggling_llm_psrl.json` |
| Source results | root-level `analysis/concordia_*` JSON/CSV files and `analysis/llm_psrl_verbal/` |

### Main-text Figure 6 — Iterated Concordia

Panel (a) reports HARP-minus-Joint regret by held-out geometry; panel (b) reports update value relative to the no-type control (E-B).

| Item | Path |
|---|---|
| Paper-facing figure | `artifacts/figures/fig_e_b_iterated_concordia_v5.pdf` |
| Runner | `scripts/run_e_b_iterated_concordia.py` |
| Renderer | `scripts/render_iterated_concordia_v5.py` |
| Complete data summarizer | `scripts/summarize_e_b_iterated_concordia_v2_all_data.py` |
| Validator | `scripts/validate_e_b_iterated_concordia_v2_all_data.py` |
| Completed data | `analysis/e_b_iterated_concordia/` |

### Main-text Figure 7 — MaaSSim Joint Prior, Cost, and Mechanism

Panel (a) combines the independent-prior E-E parity cells with grouped-prior E-H controls; panel (b) reports update cost; panels (c,d) report belief accuracy, realized utility, and event-level information.

| Component | Primary code | Completed data |
|---|---|---|
| Independent-prior factored/joint parity (E-E) | `scripts/run_e_e_maassim_tracker_parity.py` | `analysis/e_e_maassim_rq2/` |
| Grouped-prior CRN controls (E-H) | `scripts/run_e_h_maassim_grouped_prior.py`, `scripts/run_e_h_group_size_control.py` | `analysis/e_h_maassim_grouped_prior/` |
| Mechanism panels | `scripts/replay_maassim_pact_persona_mechanism.py` | `analysis/courier_dispatch_maassim/` |
| Renderer and validator | `scripts/render_maassim_rq23_v9.py`, `scripts/validate_maassim_rq23_v9.py` | `artifacts/figures/fig_maassim_rq23_v10.pdf` |

The E-H release includes deterministic and softmax likelihoods, group sizes 2 and 4, discovery seeds 0–19, confirmatory seeds 20–59, preregistrations, trajectory-equality gates, posterior-monotonicity audits, and temperature diagnostics.

```bash
python scripts/validate_e_e_maassim_tracker_parity.py --require-figure
python scripts/analyze_e_h_joint_monotonicity.py \
  --root analysis/e_h_maassim_grouped_prior/k20_deterministic_crn_confirm_seed20_59
python scripts/validate_maassim_rq23_v9.py
```

## Appendix Experiments in Figure Order

The appendix continues in the following figure order. This table is the shortest route from a displayed appendix result to its code and completed data.

| Order | Appendix figure / purpose | Figure asset | Code | Completed data |
|---:|---|---|---|---|
| 1 | Historical SOTOPIA boundary | `artifacts/figures/fig_sotopia_combined_v7.pdf` | `scripts/render_harp_sotopia_combined.py` | root-level SOTOPIA analyses, `analysis/aaai27_review/` |
| 2 | Corrected recurrent SOTOPIA | `artifacts/figures/fig_e_c_sotopia_corrected.pdf` | `scripts/analyze_e_c_sotopia_corrected.py`, `scripts/render_harp_sotopia_corrected.py` | `analysis/e_c_sotopia_corrected/` |
| 3 | Corrected SOTOPIA components | `artifacts/figures/fig_e_c_sotopia_component_corrected.pdf` | same E-C analysis/renderer | `analysis/e_c_sotopia_corrected/` |
| 4 | Analytic HP-SPGG population scaling | `artifacts/figures/fig_e1_1_n_scaling.pdf` | `scripts/run_e1_1_n_scaling.py`, `scripts/render_harp_release_tables.py` | `analysis/hp_spgg_analytic_scaling/` |
| 5 | Live-LLM population scaling | `artifacts/figures/fig_e1_1_n_scaling_llm.pdf` | `scripts/run_e1_1_llm_tier.py`, `scripts/render_harp_release_tables.py` | retained scaling analyses |
| 6 | Reward-locality violation | `artifacts/figures/fig_e_d_reward_locality_violation.pdf` | `scripts/run_e_d_reward_locality_violation.py`, `scripts/render_harp_reward_locality.py` | `analysis/e_d_reward_locality_violation*/` |
| 7 | Prior-factorization intervention | `artifacts/figures/fig_e1_3_pf_isolation.pdf` | `scripts/run_e1_3_pf_isolation.py`, `scripts/plot_e1_3_pf_isolation.py` | retained PF analyses |
| 8 | Rate and burn-in trajectories | `artifacts/figures/fig_e5_cumulative_regret_trajectories_v3.pdf`, `artifacts/figures/fig_e1_posterior_concentration_v3.pdf` | `scripts/plot_fig6_e5_trajectories.py`, `scripts/make_fig_e1.py` | retained HP-SPGG analyses |
| 9 | Analytic-kernel cross-check | `artifacts/figures/E2_native_vs_llm_baselines_main.pdf` | `scripts/plot_fig7_native_vs_llm_baselines.py` | retained E-A/native analyses |
| 10 | Hidden-complexity scaling | `artifacts/figures/fig_scaling_hidden_complexity_v5.pdf` | `scripts/make_fig_scaling_combined.py` | scaling analyses |
| 11 | Beta sweep | `artifacts/figures/fig10_beta_sweep_v3.pdf` | `scripts/make_figures_v3_all.py` | supplemental analyses |
| 12 | Price of decentralization | `artifacts/figures/fig12_decentralized_price.pdf` | `scripts/render_harp_decentralized_summary.py` | retained Concordia analyses |
| 13 | MaaSSim posterior concentration | `artifacts/figures/fig_maassim_concentration_v1.pdf` | `scripts/render_harp_maassim_appendix.py` | `analysis/courier_dispatch_maassim/` |
| 14 | MaaSSim wait/reject trade-off | `artifacts/figures/fig_maassim_wait_reject_tradeoff_v1.pdf` | `scripts/render_harp_maassim_appendix.py` | `analysis/courier_dispatch_maassim/` |
| 15 | MaaSSim persona mechanism | `artifacts/figures/fig_maassim_pact_persona_mechanism.pdf` | `scripts/replay_maassim_pact_persona_mechanism.py` | `analysis/courier_dispatch_maassim/` |
| 16 | MaaSSim conflict dynamics | `artifacts/figures/fig_maassim_conflict_dynamics_v4.pdf` | `scripts/render_harp_maassim_appendix.py` | `analysis/courier_dispatch_maassim/` |
| 17 | Main-regret unit validation | `artifacts/figures/fig_maassim_unit_validation_v3.pdf` | `scripts/plot_maassim_main_figure.py` | `analysis/courier_dispatch_maassim/` |
| 18 | Full Concordia comparison | `artifacts/figures/fig2_concordia_strip_v11c.pdf` | `scripts/plot_concordia_selected_main.py` | root-level Concordia analyses |
| 19 | Haggling focal/joint frontier | `artifacts/figures/fig11_haggling_pareto.png` | `scripts/plot_fig_haggling_pareto.py` | retained Haggling analyses |

## Additional Non-Figure Confirmatory Data

The paper also reports table-only or theorem-supporting experiments. These remain included after the figure-ordered section because they do not have a unique main-text figure position:

- E-F frozen MaaSSim bonus: `analysis/e_f_maassim_bonus/`;
- HP-SPGG Claim-A scaling consolidation: `analysis/hp_spgg_analytic_scaling/`;
- Claim-B v2 pilot and v3 preregistered confirmation: `analysis/hp_spgg_burn_in_v2_pilot/`, `analysis/hp_spgg_burn_in_v3_confirmatory/`;
- E-H deterministic/softmax likelihood robustness and group-size preregistrations: `analysis/e_h_maassim_grouped_prior/`.

```bash
python scripts/validate_e_f_maassim_bonus.py
python scripts/validate_hp_spgg_analytic_scaling.py
python scripts/validate_hp_spgg_scaling_claim_a_md.py
python scripts/validate_hp_spgg_burn_in_v3_confirmatory.py
python scripts/validate_hp_spgg_claim_b_all_data_md.py
```

Historical internal identifiers such as `hpsmg`, `hpsmg_plus`, and compatibility filenames containing `pact` are retained because they are part of stored schemas and command-line compatibility. Visible documentation uses HARP terminology.

## Reproducibility Levels

### Level 1: Integrity and completed-result audit

No network or third-party simulator is required:

```bash
python scripts/validate_anonymous_experiment_repo.py
```

### Level 2: Offline aggregation and plotting

Install the base dependencies and run the relevant summarizer, validator, or renderer. Completed arrays and accepted-response caches are included.

### Level 3: Full regeneration

Some experiments require public third-party dependencies or provider access:

- Concordia: a compatible `google-deepmind/concordia` installation;
- SOTOPIA: SOTOPIA 0.1.5 and public SOTOPIA-Hard inputs;
- MaaSSim: a compatible public MaaSSim checkout for source-state regeneration;
- live language-model experiments: credentials for a reviewer-selected provider.

Third-party repositories, model weights, downloaded datasets, credentials, and private organization-managed endpoints are not redistributed.

## Provider Configuration

`config/providers.example.yaml` contains placeholders only. Credentials must be supplied through environment variables and must never be committed.

The completed experiments used multiple public model families through a hosted provider path. Provider-side sampling seeds were unavailable. Accepted responses and calibration outputs are therefore cache-pinned for offline audit, while a new live run through another provider is a new experiment rather than a bitwise replay.

## Interpretation Boundaries

- HP-SPGG numeric HARP-family rows use persona-conditioned outcome tensors and a Gaussian reward likelihood; they are not token-log-probability experiments.
- The practical HARP+ implementation uses posterior uncertainty, reward variance, and a small action-spread term.
- Iterated Concordia is an exact-payoff constructed diagnostic rather than native dialogue Concordia.
- SOTOPIA is an open-text surrogate outside the exact finite-model assumptions.
- MaaSSim uses retained queue snapshots and deterministic hidden driver rules for the zero-provider replay controls.
- E-H common-random-number comparisons must be interpreted from the CRN directories; older independent-RNG exploratory outputs are retained only for audit provenance.

## Anonymous Repository Hygiene

The packaging process excludes:

- `.git/`, branches, commits, and remotes;
- editor state and session logs;
- local absolute paths and user names;
- author names, affiliations, and email addresses;
- private provider endpoints and tenant/application identifiers;
- API keys, bearer tokens, and local `.env` files;
- third-party source trees and downloaded datasets.

Before uploading, run the repository validator from a clean extraction. `MANIFEST.csv` and `SHA256SUMS.txt` describe the pristine package; regenerating figures or analyses intentionally changes files and should be done in a working copy.

## License and Notice

This anonymous research artifact is supplied for peer review and reproducibility evaluation. External software, datasets, and model APIs remain subject to their respective licenses and terms.
