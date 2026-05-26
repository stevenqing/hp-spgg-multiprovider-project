# Anonymous Artifact: Hidden-Persona Multi-Agent Coordination

This repository contains the anonymized code artifact for a submission on
posterior-sharing coordination in hidden-persona multi-agent games. The code
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

## Baselines

The experiment runners expose the following baseline families:

| ID | Description | Reference |
| --- | --- | --- |
| `random` | Uniform random action selection. | Standard control baseline. |
| `llm_greedy` | Prompted LLM policy that optimizes the visible local objective. | Direct-prompt LLM-agent baseline. |
| `llm_belief` / `surrogate_only` | Prompted LLM policy using a fixed or shared surrogate persona menu. | Direct-prompt LLM-agent baseline. |
| `naive_belief` | Natural-language partner-type guess without numeric Bayesian updates. | Direct-prompt belief baseline. |
| `llm_psrl_verbal` | Natural-language posterior-sampling style belief tracking. | Arumugam and Griffiths, 2026, LLM-PSRL ([arXiv:2504.20997](https://arxiv.org/abs/2504.20997)). |
| `atom_tom1` / `atom_tom2` | First- and second-order theory-of-mind prompting. | Li et al., 2023, Theory of Mind for Multi-Agent Collaboration ([arXiv:2310.10701](https://arxiv.org/abs/2310.10701)). |
| `econ_bne` | Economic best-response / Bayes-Nash-style baseline. | Harsanyi, 1967-1968, games with incomplete information. |
| `hpsmg` | Posterior-guided method without the exploration bonus. | This paper's method ablation. |
| `hpsmg_plus` | Posterior-guided method with the exploration bonus. | This paper's main method. |
| `oracle_joint` / `oracle_policy` | Oracle-information upper-reference policies. | Oracle reference baseline. |

Substrate integrations also include SOTOPIA beta-sweep support, Concordia
beta-zero aliases such as `hpsmg_proxy` and `hpsmg_joint_proxy`, Concordia
verbal-baseline sweep scripts, and SOTOPIA data-production utilities.

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
