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
docs/                 Data provenance and repository notes
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

## Recently Added Baselines and Utilities

The source tree includes code for the following additional comparisons:

- `llm_psrl_verbal`: a natural-language posterior tracking baseline.
- SOTOPIA `hpsmg` / `hpsmg_plus` beta handling, including beta-sweep support.
- Concordia beta-zero PACT aliases such as `hpsmg_proxy` and
	`hpsmg_joint_proxy` for compact posterior-guided objectives.
- Full Concordia verbal-baseline sweep launch/check scripts.
- Data-only SOTOPIA revenge-plot production with per-turn JSONL dumps.

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
