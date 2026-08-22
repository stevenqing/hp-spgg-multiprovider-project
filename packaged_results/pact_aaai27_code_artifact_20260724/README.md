# PACT AAAI-27 Code and Data Artifact

This archive accompanies the anonymous submission **“PACT: Prior-Aware Coordination via Type-inference for LLM Multi-Agent Systems.”** It contains the implementation, completed experiment outputs, accepted-response caches for the fresh matched HP-SPGG control, paper sources, and integrity checks.

The fastest review path is fully offline and makes **no API calls**.

## 1. Quick start

Python 3.11 or 3.12 is recommended. From the extracted archive root:

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts\validate_pact_aaai27_code_artifact.py
```

### Linux or macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/validate_pact_aaai27_code_artifact.py
```

A successful validation ends with `"status": "ok"` and reports:

- E-A historical provenance: 140 rows;
- E-A fresh matched control: 400 method/backbone/seed rows;
- E-B iterated Concordia: 4,800 episode rows;
- E-C corrected SOTOPIA: 720 corruption rows plus both 120-episode component controls;
- E-D reward-locality intervention: 36,000 episode rows;
- E-E MaaSSim tracker parity: 240 tracker-level rows and 9 paired-gap cells;
- E-F MaaSSim frozen bonus: 20 tracker-level rows.

The validator also checks every file against `MANIFEST.csv` and `SHA256SUMS.txt`, rejects missing or extra files, and scans for excluded private endpoint identifiers and local paths.

## 2. What is included

```text
arr_paper/                    Final paper, LaTeX sources, and canonical figures
analysis/                     Completed outputs, aggregates, and accepted caches
config/                       Public input manifests and provider example config
external/sotopia_data_probe/  Small public-input metadata and reconstructed case cache
llm_hpgg/                     HP-SPGG, PACT/PACT+, Joint-PSRL, and prompt baselines
llm_hpgg_concordia/           Compact Concordia adapters
llm_hpgg_sotopia/             SOTOPIA-Hard adapter and corrected recurrent tracker
llm_courier_dispatch/         Dispatch utilities used by the MaaSSim adapter
llm_courier_dispatch_maassim/ MaaSSim hidden-rule and policy adapters
prompts/                      Persona and judge prompt templates
scripts/                      Experiment, analysis, plotting, build, and validation entrypoints
MANIFEST.csv                  Category, byte count, and SHA-256 for every packaged file
SHA256SUMS.txt                Portable integrity list
```

The submission PDF is `arr_paper/PACT_AAAI27.pdf`. The full 29-page bundle with the technical appendix is `arr_paper/main.pdf`.

## 3. Claim-to-code map

| Paper component | Primary implementation | Completed data | Main reproduction/validation entrypoint |
|---|---|---|---|
| PACT factored posterior and planner | `llm_hpgg/coordinator.py`, `llm_hpgg/run_experiment.py` | `analysis/e_a_matched_likelihood/` | `scripts/run_e_a_matched_likelihood.py`, `scripts/audit_e_a_matched_likelihood.py` |
| Practical PACT+ proxy | `llm_hpgg/coordinator.py` | E-A directory above and retained scaling summaries | E-A runner above; `scripts/make_fig_scaling_combined.py` |
| Joint-PSRL and no-type controls | `llm_hpgg/run_experiment.py` | E-A directory above | E-A runner and artifact validator |
| Iterated Concordia diagnostic | `scripts/run_e_b_iterated_concordia.py`, `llm_hpgg_concordia/` | `analysis/e_b_iterated_concordia/`, including the complete 4,800-row RQ2/RQ3 Markdown | runner plus `scripts/validate_e_b_iterated_concordia_v2_all_data.py` |
| Corrected SOTOPIA boundary | `llm_hpgg_sotopia/agents.py`, `llm_hpgg_sotopia/run_sotopia_hard_official.py` | `analysis/aaai27_review/`, `analysis/e_c_sotopia_corrected/` | `scripts/analyze_e_c_sotopia_corrected.py` |
| Reward-locality intervention | `scripts/run_e_d_reward_locality_violation.py` | `analysis/e_d_reward_locality_violation*/` | same runner and artifact validator |
| MaaSSim tracker parity | `scripts/run_e_e_maassim_tracker_parity.py` | `analysis/e_e_maassim_rq2/` | same runner and `scripts/validate_e_e_maassim_tracker_parity.py` |
| MaaSSim frozen bonus | `scripts/run_e_f_maassim_bonus.py` | `analysis/e_f_maassim_bonus/` | same runner and `scripts/validate_e_f_maassim_bonus.py` |
| HP-SPGG RQ3 component ladder | `scripts/run_e_g_hp_spgg_component_ladder.py` | `analysis/e_g_hp_spgg_component_ladder/` | runner plus `scripts/validate_e_g_hp_spgg_component_ladder.py` |
| HP-SPGG analytic population/library scaling | `scripts/run_hp_spgg_analytic_scaling.py` | `analysis/hp_spgg_analytic_scaling/` | runner, `scripts/render_scaling_v1.py`, and `scripts/validate_hp_spgg_analytic_scaling.py` |
| Scaling Claim-A consolidation / Claim-B v2 pilot | `scripts/summarize_hp_spgg_scaling_claim_a.py`, `scripts/run_hp_spgg_burn_in_v2_pilot.py` | `analysis/hp_spgg_analytic_scaling/`, `analysis/hp_spgg_burn_in_v2_pilot/` | dedicated Markdown and pilot validators |
| Claim-B v3 locked confirmatory study | `scripts/run_hp_spgg_burn_in_v3_confirmatory.py` | `analysis/hp_spgg_burn_in_v3_confirmatory/` | locked preregistration, independent-cell raw data, renderer, and strict validator |
| Complete Claim-B single Markdown | `scripts/summarize_hp_spgg_claim_b_all_data.py` | `analysis/hp_spgg_burn_in_v3_confirmatory/claim_b_all_data.md` | exact validation of 120,836 embedded CSV rows, five JSON blocks, two Markdown sources, and 35 hashes |
| MaaSSim directional case study | `llm_courier_dispatch_maassim/`, `llm_courier_dispatch/` | `analysis/courier_dispatch_maassim/` | `scripts/replay_maassim_pact_persona_mechanism.py`, `scripts/plot_maassim_main_figure.py` |
| Paper and submission build | `arr_paper/` | canonical PDFs and figures | `scripts/compile_arr_paper.ps1`, `scripts/build_arr_submission.ps1` |

Historical internal algorithm identifiers `hpsmg` and `hpsmg_plus` correspond to PACT and practical PACT+, respectively.

## 4. Offline reproduction paths

### 4.1 Validate all released experiment grids

```powershell
python scripts\validate_pact_aaai27_supplemental_experiments.py --require-components --require-matched-e-a
```

This validates row counts, unique keys, environment-matched E-A inputs, four complete 1,500-cell tensors, 400 per-seed NPZ files, E-C component controls, the E-D zero-coupling anchor, E-E joint-marginal identity, the E-F frozen-beta grid, and the 1,000-row zero-provider E-G component ladder.

The complete Figure-5 iterated-Concordia data document can be regenerated and checked without provider calls:

```powershell
python scripts\summarize_e_b_iterated_concordia_v2_all_data.py
python scripts\validate_e_b_iterated_concordia_v2_all_data.py
```

### 4.2 Regenerate the paper-facing supplemental summary

```powershell
python scripts\summarize_pact_aaai27_supplemental_experiments.py
```

Output is written under `analysis/aaai27_supplemental_experiments/`. This command reads completed artifacts only and performs no provider calls.

### 4.3 Re-aggregate fresh E-A without provider calls

All accepted tensor, verbal-baseline, and external-baseline responses are cache-pinned. To recompute E-A tables and figures from the retained outputs:

```powershell
python scripts\run_e_a_matched_likelihood.py --stage aggregate
python scripts\audit_e_a_matched_likelihood.py `
  --source-dir analysis\e_a_matched_likelihood\source_snapshot `
  --out-dir analysis\e_a_matched_likelihood
```

Do not pass `--force`; forced calibration or experiment stages can request live provider calls.

### 4.4 Re-run the analytic E-D tier

```powershell
python scripts\run_e_d_reward_locality_violation.py `
  --alphas 0,0.25,0.5,1,2,4 `
  --episodes 100 --seeds 10 --seed-offset 40000 `
  --action-values 0,0.5,1 `
  --include-analytic
```

The analytic tier uses no LLM. The retained live-tensor tier can also be replayed locally by supplying the included calibration with `--calibration LABEL=PATH`.

### 4.5 Re-run MaaSSim E-E/E-F from retained states

```powershell
python scripts\run_e_e_maassim_tracker_parity.py --stage run
python scripts\validate_e_e_maassim_tracker_parity.py --require-figure
python scripts\run_e_f_maassim_bonus.py
python scripts\validate_e_f_maassim_bonus.py
```

These replay stages make no provider calls. Regenerating E-E's closed-loop sub-fleet source states requires the optional MaaSSim checkout described below.

### 4.6 Re-run the analytic RQ3 component ladder

```powershell
python scripts\run_e_g_hp_spgg_component_ladder.py
python scripts\plot_e_g_hp_spgg_component_ladder.py
python scripts\validate_e_g_hp_spgg_component_ladder.py
```

E-G uses only NumPy and the retained analytic HP-SPGG kernel; it makes zero provider calls.

### 4.7 Re-run additive analytic scaling

```powershell
python scripts\run_hp_spgg_analytic_scaling.py --stage all
python scripts\render_scaling_v1.py
python scripts\validate_hp_spgg_analytic_scaling.py
```

This additive S1/S2/S3 run makes zero provider calls and does not modify paper sources.

### 4.8 Rebuild the paper on Windows

MiKTeX with `pdflatex`, `bibtex`, Poppler `pdfinfo`/`pdftotext`/`pdfseparate`/`pdfunite`, and PowerShell 5.1 or newer are required:

```powershell
.\scripts\compile_arr_paper.ps1
.\scripts\build_arr_submission.ps1
```

The first command builds the full bundle. The second extracts the resolved main text plus references and checklist into the canonical submission PDF without the technical appendix.

## 5. Optional substrate dependencies

The base requirements are sufficient for package validation, HP-SPGG offline analysis, and E-D. Third-party substrate source trees are intentionally not vendored.

### Concordia

E-B re-execution requires a public `google-deepmind/concordia` checkout compatible with `gdm-concordia==2.4.0` under `external/concordia`, or an equivalent installation on `PYTHONPATH`:

```powershell
$env:PYTHONPATH = "$PWD;$PWD\external\concordia"
python scripts\run_e_b_iterated_concordia.py --episodes 20 --seeds 5 --seed-offset 1000
```

E-B is an exact-payoff, constructed iterated diagnostic, not native dialogue Concordia and not backbone evidence.

### SOTOPIA

Corrected E-C analysis requires SOTOPIA 0.1.5; the completed run used Python 3.12 and `litellm==1.80.11`. Place a compatible checkout under `external/sotopia` or install it separately. The package includes the reconstructed 70-case cache and public input hashes. The original 180 MB public episode JSONL is omitted; its download URL and SHA-256 are in `config/aaai27_sotopia_input_manifest.csv`.

With the dependency installed, the stored p=0 transcripts can be re-analyzed without API calls:

```powershell
$env:PYTHONPATH = "$PWD;$PWD\external\sotopia"
python scripts\analyze_e_c_sotopia_corrected.py
```

### MaaSSim

MaaSSim re-simulation requires a compatible public MaaSSim checkout under `external/maassim`. Retained snapshots, aggregate outputs, and the project adapter are included; provider-generated original paired seed rows were not retained, as disclosed in the paper.

## 6. Live provider runs

Public adapters for OpenAI, Anthropic, Google, and OpenAI-compatible endpoints are included. Credentials must be supplied only through environment variables; never place keys in the artifact.

The exact four-backbone paper path used an organization-managed provider proxy. Its endpoint, tenant configuration, credentials, and provider-side sampling seeds are not included. The backend key used by historical scripts is retained for code compatibility, but `config/providers.example.yaml` contains placeholders only. Consequently:

- completed cache-pinned outputs can be replayed and audited exactly;
- environment seeds and persona profiles are matched across E-A methods;
- provider RNG paths cannot be replayed exactly;
- regenerating live responses through a different provider is a new run, not a bitwise reproduction.

## 7. Interpretation boundaries

- HP-SPGG numeric PACT-family rows use an offline persona-conditioned outcome tensor and a Gaussian reward likelihood; they are not online autonomous-player conversations and do not use token log-probabilities.
- The practical PACT+ implementation uses posterior uncertainty, reward variance, and a small action-spread term. It is not the idealized pairwise-disagreement bonus analyzed in the theorem.
- E-F separately uses a disclosed one-step pairwise utility-disagreement bonus with beta frozen at 0.25; it changes 4/406 MaaSSim assignments but has no resolved utility gain.
- E-A ratios against prompt baselines are descriptive system-level comparisons because information access differs. PACT versus Joint-PSRL is the representation-matched comparison.
- E-B is a constructed exact-payoff iterated diagnostic.
- SOTOPIA is an open-text surrogate outside the exact theorem assumptions; the corrected tracker updates but yields no score gain.
- MaaSSim is a score-assisted hybrid and provides directional evidence rather than a factorial isolation.

## 8. Known artifact limitations

1. Some earlier scaling NPZs and historical SOTOPIA all-70 raw episode JSONs were removed before this release. Their canonical figures and aggregate reports remain, but raw trajectories cannot be reconstructed from those summaries.
2. The exact provider proxy and credentials are unavailable in the anonymous artifact.
3. Provider sampling seeds were unavailable; accepted responses are content-hash/cache pinned rather than provider-RNG matched.
4. External Concordia, SOTOPIA, and MaaSSim source trees are not redistributed.
5. Accepted-response counts exclude transient retries and are not billing totals.

## 9. Integrity and expected modification behavior

`MANIFEST.csv` and `SHA256SUMS.txt` describe the pristine extracted archive. Regenerating figures, summaries, or PDFs will intentionally change files and cause the full artifact validator to report hash differences. Preserve a clean extraction for integrity verification and use a separate working copy for reproduction.

This artifact is supplied for anonymous review and reproducibility evaluation. No private credentials or provider endpoint configuration are included.
