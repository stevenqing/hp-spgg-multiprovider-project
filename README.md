# Anonymous Artifact: PACT: Prior-Aware Coordination via Type-inference for LLM Multi-Agent Systems

This repository contains the anonymized code artifact for a submission on
PACT: Prior-Aware Coordination via Type-inference for LLM Multi-Agent Systems. The code
covers three evaluation substrates:

- **HP-SPGG**: a controlled Hidden-Persona Sequential Public-Goods Game.
- **Concordia compact tasks**: Pub Coordination and Haggling integrations.
- **SOTOPIA-Hard**: reconstructed 70-case social-interaction evaluations.

The artifact is intended to reproduce experiment runs and regenerate derived
tables or figures from local result files. Large generated artifacts such as
NumPy calibration arrays, PDFs, PNGs, logs, and run outputs are intentionally
not part of the tracked source tree.

## Repository Layout

```text
llm_hpgg/             Core HP-SPGG simulator, coordinators, and LLM adapters
llm_hpgg_concordia/   Concordia compact Pub Coordination / Haggling runners
llm_hpgg_sotopia/     SOTOPIA-Hard agents and official-case runner
scripts/              Experiment launchers, summarizers, and plotting utilities
config/               Provider routing configuration
prompts/              Prompt templates and persona text
```

Generated or paper-facing directories may exist in a working copy, but are not
required for using the source code. They are deliberately omitted from the
artifact commit when they contain figures, PDFs, logs, or raw experiment data.

## Setup

The project uses Python with `uv`:

```powershell
uv sync
```

Set a provider backend before running live LLM experiments:

```powershell
$env:LLM_HPGG_BACKEND = "<backend-name>"
```

For local smoke tests that should avoid external LLM calls:

```powershell
$env:LLM_HPGG_OFFLINE = "1"
```

Some external substrate runners require their local source trees on
`PYTHONPATH`. These third-party checkouts are not vendored in the anonymized
artifact; install them separately or place local copies under `external/`.
For example:

```powershell
$env:PYTHONPATH = "$PWD;$PWD\external\concordia"
$env:PYTHONPATH = "$PWD;$PWD\external\sotopia"
```

## Main Experiment Entrypoints

HP-SPGG:

```powershell
uv run python -m llm_hpgg.run_experiment --help
```

Concordia Pub Coordination compact runner:

```powershell
uv run python -m llm_hpgg_concordia.run_pub_coordination_compact --help
```

Concordia Haggling compact runner:

```powershell
uv run python -m llm_hpgg_concordia.run_haggling_compact --help
```

SOTOPIA-Hard reconstructed official runner:

```powershell
uv run python -m llm_hpgg_sotopia.run_sotopia_hard_official --help
```

MaaSSim RQ2/RQ3 supplements:

```powershell
uv run python scripts\run_e_e_maassim_tracker_parity.py --help
uv run python scripts\validate_e_e_maassim_tracker_parity.py --require-figure
uv run python scripts\run_e_f_maassim_bonus.py
uv run python scripts\validate_e_f_maassim_bonus.py
```

E-E uses closed-loop MaaSSim regeneration by fleet size followed by zero-provider
factored-versus-explicit-joint replay. E-F is a zero-provider frozen-$\beta$
bonus ablation on retained states.

HP-SPGG analytic RQ3 component ladder:

```powershell
uv run python scripts\run_e_g_hp_spgg_component_ladder.py
uv run python scripts\plot_e_g_hp_spgg_component_ladder.py
uv run python scripts\validate_e_g_hp_spgg_component_ladder.py
```

E-G is a deterministic zero-provider run over ten common environment seeds and
writes the complete five-variant, 1,000-row cumulative-regret long table.

Additive analytic population/library scaling:

```powershell
uv run python scripts\run_hp_spgg_analytic_scaling.py --stage all
uv run python scripts\render_scaling_v1.py
uv run python scripts\validate_hp_spgg_analytic_scaling.py
```

The S1/S2/S3 scaling suite makes zero provider calls and writes only under
`analysis/hp_spgg_analytic_scaling/` and generated `figs/`; it does not modify
paper sources or existing experiment outputs.

Claim-A consolidation and theory-aligned Claim-B pilot:

```powershell
uv run python scripts\summarize_hp_spgg_scaling_claim_a.py
uv run python scripts\validate_hp_spgg_scaling_claim_a_md.py
uv run python scripts\run_hp_spgg_burn_in_v2_pilot.py
uv run python scripts\render_hp_spgg_burn_in_v2_pilot.py
uv run python scripts\validate_hp_spgg_burn_in_v2_pilot.py
uv run python scripts\run_hp_spgg_burn_in_v3_confirmatory.py
uv run python scripts\validate_hp_spgg_burn_in_v3_confirmatory.py
uv run python scripts\render_hp_spgg_burn_in_v3_confirmatory.py
uv run python scripts\summarize_hp_spgg_claim_b_all_data.py
uv run python scripts\validate_hp_spgg_claim_b_all_data_md.py
```

The Claim-B pilot samples the Gaussian outcome channel and tests per-agent
contraction, inverse-H scaling, and the all-agent log-n maximum separately.
The v3 confirmatory study is hash-locked before execution, uses independent
cells and seed-cluster bootstrap uncertainty, and retains the original
linear-n experiment as a null rather than retuning it.
The final two commands consolidate the original null, v2 pilot, locked v3
study, and all 120,836 embedded CSV rows into one strictly validated Markdown.

## Baselines

The experiment runners expose the following baseline families:

| Baseline | Description | Reference |
| --- | --- | --- |
| `random` | Uniform random action selection. | Standard control baseline. |
| `llm_greedy` | Prompted LLM policy that optimizes the visible local objective. | Direct-prompt LLM-agent baseline. |
| `llm_belief` / `surrogate_only` | Prompted LLM policy using a fixed or shared surrogate persona menu. | Direct-prompt LLM-agent baseline. |
| `naive_belief` | Natural-language partner-type guess without numeric Bayesian updates. | Direct-prompt belief baseline. |
| `llm_psrl_verbal` | Natural-language posterior-sampling style belief tracking. | Arumugam and Griffiths, 2026, Toward Efficient Exploration by Large Language Model Agents. |
| `atom_tom1` / `atom_tom2` | First- and second-order theory-of-mind prompting. | Mu et al., 2026, Adaptive Theory of Mind for LLM-Based Multi-Agent Coordination. |
| `econ_bne` | Economic best-response / Bayes-Nash-style baseline. | Xie et al., 2025, From Debate to Equilibrium: Belief-Driven Multi-Agent LLM Reasoning via Bayesian Nash Equilibrium. |
| PACT | Posterior-guided method without the exploration bonus. | This paper's method ablation. |
| PACT+ | Posterior-guided method with the exploration bonus. | This paper's main method. |
| `oracle_joint` / `oracle_policy` | Oracle-information upper-reference policies. | Oracle reference baseline. |

Substrate integrations also include SOTOPIA beta-sweep support, Concordia
PACT aliases for compact posterior-guided objectives, Concordia verbal-baseline
sweep scripts, and SOTOPIA data-production utilities.

Representative scripts:

```powershell
uv run python scripts\produce_sotopia_revenge_n100.py --help
uv run python scripts\plot_llm_psrl_verbal_figures.py
uv run python scripts\combine_sotopia_figure4.py
```

## Artifact Hygiene

The repository ignores generated arrays and run outputs by default. In
particular, `*.npy` and `*.npz` files are excluded because they are generated
calibration or experiment artifacts rather than source code.

If a reproduction run creates files under `analysis/`, `results/`,
`results_phase2/`, `figs/`, or `logs/`, treat them as local outputs unless a
specific artifact package explicitly asks for them.

## License

This anonymized artifact is provided for review and reproducibility purposes.
