# PACT: Anonymous Code Repository

This repository contains the anonymized implementation for **PACT: Prior-Aware Coordination via Type-inference for LLM Multi-Agent Systems**.

This is a **code-only submission repository**. It intentionally contains no experiment outputs, model-response caches, paper files, compiled figures, third-party source trees, credentials, private provider endpoints, Git history, or author-identifying metadata.

## Repository layout

```text
llm_hpgg/                     Core HP-SPGG simulator and PACT implementations
llm_hpgg_concordia/           Compact Concordia integrations
llm_hpgg_sotopia/             SOTOPIA-Hard integration and recurrent tracker
llm_courier_dispatch/         Dispatch utilities used by the MaaSSim adapter
llm_courier_dispatch_maassim/ MaaSSim hidden-rule and policy adapters
scripts/                      Experiment, analysis, validation, and plotting entrypoints
config/                       Anonymous provider configuration example
prompts/                      Persona and judge prompt templates
```

Scripts create local outputs under directories such as `analysis/`, `figs/`, or user-specified output paths. Those directories are not included in this code-only archive.

## Method-to-code map

| Component | Main implementation |
|---|---|
| PACT factored posterior | `llm_hpgg/coordinator.py` |
| Practical PACT+ proxy | `llm_hpgg/coordinator.py` |
| HP-SPGG simulator, Joint-PSRL, and no-type controls | `llm_hpgg/run_experiment.py` |
| Prompt baselines and verbal PSRL | `llm_hpgg/run_external_llm_baselines.py`, `llm_hpgg/verbal_belief.py` |
| Matched HP-SPGG experiment | `scripts/run_e_a_matched_likelihood.py` |
| Iterated Concordia diagnostic | `scripts/run_e_b_iterated_concordia.py`, `scripts/summarize_e_b_iterated_concordia_v2_all_data.py` |
| Corrected SOTOPIA analysis | `llm_hpgg_sotopia/agents.py`, `scripts/analyze_e_c_sotopia_corrected.py` |
| Reward-locality intervention | `scripts/run_e_d_reward_locality_violation.py` |
| MaaSSim factored/joint tracker parity (E-E) | `scripts/run_e_e_maassim_tracker_parity.py` |
| MaaSSim frozen bonus ablation (E-F) | `scripts/run_e_f_maassim_bonus.py` |
| HP-SPGG analytic component ladder (E-G) | `scripts/run_e_g_hp_spgg_component_ladder.py` |
| HP-SPGG analytic scaling sweeps | `scripts/run_hp_spgg_analytic_scaling.py`, `scripts/render_scaling_v1.py` |
| Scaling Claim-A report / Claim-B stochastic pilot | `scripts/summarize_hp_spgg_scaling_claim_a.py`, `scripts/run_hp_spgg_burn_in_v2_pilot.py` |
| Claim-B v3 locked confirmatory study | `scripts/run_hp_spgg_burn_in_v3_confirmatory.py`, `scripts/validate_hp_spgg_burn_in_v3_confirmatory.py` |
| Complete Claim-B Markdown generator/validator | `scripts/summarize_hp_spgg_claim_b_all_data.py`, `scripts/validate_hp_spgg_claim_b_all_data_md.py` |
| MaaSSim case study | `llm_courier_dispatch_maassim/`, `scripts/replay_maassim_pact_persona_mechanism.py` |

Historical internal identifiers `hpsmg` and `hpsmg_plus` in command-line choices and stored-schema compatibility code correspond to PACT and practical PACT+, respectively.

## Setup

Python 3.11 or 3.12 is recommended.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Linux or macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The project can also be initialized with `uv sync`.

## Offline smoke test

The provider dispatcher has an explicit offline mode that makes no network calls:

### Windows PowerShell

```powershell
$env:LLM_HPGG_OFFLINE = "1"
python -m llm_hpgg.smoke_test
```

### Linux or macOS

```bash
export LLM_HPGG_OFFLINE=1
python -m llm_hpgg.smoke_test
```

Expected output contains one deterministic player reply and one JSON judge score.

## Primary entrypoints

Display the available arguments without starting an experiment:

```powershell
python -m llm_hpgg.run_experiment --help
python scripts\run_e_a_matched_likelihood.py --help
python scripts\run_e_b_iterated_concordia.py --help
python scripts\run_e_d_reward_locality_violation.py --help
python scripts\run_e_e_maassim_tracker_parity.py --help
```

A small zero-provider E-D execution is available without result data:

```powershell
python scripts\run_e_d_reward_locality_violation.py `
  --alphas 0,1 --episodes 3 --seeds 2 `
  --action-values 0,0.5,1 `
  --out-dir analysis\e_d_smoke
```

## Provider configuration

Public adapters are included for OpenAI, Anthropic, Google, and OpenAI-compatible endpoints. Set credentials only through environment variables.

The paper experiments also used a hosted organization-managed endpoint. Its endpoint, tenant/application identifiers, credentials, and provider-side sampling controls are deliberately absent. The anonymized adapter uses the neutral backend name `managed` and requires explicit environment configuration:

```text
LLM_HPGG_BACKEND=managed
MANAGED_PROVIDER_BASE_URL=...
MANAGED_PROVIDER_API_VERSION=...
MANAGED_PROVIDER_BEARER_TOKEN=...
```

Alternatively, Azure-compatible token acquisition can be configured with `MANAGED_PROVIDER_TENANT_ID` and `MANAGED_PROVIDER_SCOPE`. The example file under `config/` contains placeholders only.

Exact provider-path replay is therefore unavailable from this code-only repository. Running with another provider produces a new experiment rather than a bitwise reproduction of the paper outputs.

## Optional substrate dependencies

Third-party repositories are not vendored.

### Concordia

The compact and iterated Concordia code expects a public `google-deepmind/concordia` checkout compatible with `gdm-concordia==2.4.0` under `external/concordia`, or an equivalent installation on `PYTHONPATH`.

```powershell
$env:PYTHONPATH = "$PWD;$PWD\external\concordia"
python scripts\run_e_b_iterated_concordia.py --help
```

### SOTOPIA

The SOTOPIA adapter expects SOTOPIA 0.1.5. The completed corrected-run environment used Python 3.12 and `litellm==1.80.11`. Public SOTOPIA-Hard inputs must be obtained from the `cmu-lti/sotopia` dataset.

```powershell
$env:PYTHONPATH = "$PWD;$PWD\external\sotopia"
python -m llm_hpgg_sotopia.run_sotopia_hard_official --help
```

### MaaSSim

MaaSSim experiments require a compatible public checkout under `external/maassim`. The project-specific adapter is included, but third-party MaaSSim code and datasets are not redistributed.

## Reproducing paper experiments

This repository provides the code paths, but the code-only submission does not include result data or response caches:

- E-A requires calibration tensors or live provider access.
- E-B requires the public Concordia dependency.
- E-C requires public SOTOPIA inputs and live provider access for new episodes.
- E-D has a fully analytic zero-provider tier and optional supplied calibration tensors.
- E-E regenerates self-consistent MaaSSim sub-fleets and then performs zero-provider tracker replay.
- E-F is a zero-provider frozen-$\beta$ replay but requires the saved states generated by the MaaSSim pipeline.
- E-G is a fully analytic zero-provider HP-SPGG component ladder and regenerates its deterministic kernel locally.
- The additive HP-SPGG scaling runner is also fully analytic and enforces explicit joint-memory, update-time, planner-size, and per-cell runtime caps.
- Other MaaSSim evaluations require the public simulator and locally generated snapshots.

Data validators and summarizers are included for use when the separate result artifact is available. They are expected to fail with missing-file errors in this code-only repository until the corresponding result directories are supplied.

## Important implementation boundaries

- HP-SPGG numeric PACT-family runs consume a persona-conditioned outcome tensor and use a Gaussian reward likelihood; they do not query token log-probabilities.
- The practical PACT+ code uses posterior uncertainty, reward variance, and a small action-spread term. It differs from the idealized pairwise-disagreement bonus in the theoretical analysis.
- Optional E-F uses a separately disclosed one-step pairwise utility-disagreement bonus with beta frozen at 0.25; it is not presented as the tensor proxy or as theorem validation.
- E-B is a constructed exact-payoff iterated diagnostic rather than native dialogue Concordia.
- The SOTOPIA tracker is an open-text surrogate outside the exact theorem assumptions.
- The MaaSSim policy is a score-assisted hybrid rather than a pure prompt baseline.

## Anonymity and repository hygiene

The submitted ZIP is generated without `.git/`, virtual environments, outputs, caches, PDFs, local absolute paths, private endpoint configuration, editor state, or backup trees. The managed-provider implementation and environment-variable names are generalized during packaging.

Do not commit API keys, bearer tokens, downloaded datasets, generated model responses, or local result directories. The included `.gitignore` covers the standard generated paths.

## License and third-party software

This anonymous research code is supplied for peer review and reproducibility evaluation. External Concordia, SOTOPIA, MaaSSim, model APIs, and datasets remain subject to their own licenses and terms.
