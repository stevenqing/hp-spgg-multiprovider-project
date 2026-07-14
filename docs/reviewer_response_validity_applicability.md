# Reviewer Response: Validity, Applicability, and Systems Constraints

This memo maps the validity/applicability review to the revised manuscript and code. It intentionally distinguishes new evidence from claim-scope corrections.

## Summary of substantive changes

1. **General observation likelihood, not a token-logprob-only claim.** Equation (1) now uses a generic persona-conditioned observation likelihood. A deployment may use action-token logprobs, but the reported HP-SPGG native experiments use a Gaussian outcome likelihood centred on a cached LLM-judge calibration tensor (`sigma=0.08`). The manuscript no longer implies that the headline results require online token probabilities or a fixed verbalizer.
2. **Main-text deployment stop rules.** The experiments section now gives operational checks for TI, RL, PF, likelihood calibration/TID, persona-library coverage, and planner quality. It explicitly says that failure of these checks removes the theorem guarantee.
3. **New 500-seed robustness study.** An offline, paired-seed HP-SPGG experiment quantifies likelihood temperature, additive log-likelihood noise, top-k truncation, fixed calibration drift, out-of-library persona mixtures, and restricted planner budgets. It makes zero LLM calls.
4. **SOTOPIA projection claim narrowed.** The manuscript states that SOTOPIA has no native labels for the project's four surrogate classes, so projection accuracy is not identifiable. It does not manufacture a confusion matrix or corruption result from missing labels. The profile-informed surrogate reference is reported as a negative diagnostic, not a ground-truth oracle.
5. **Strict focal oracle in the main text.** Concordia's dashed line is now explicitly `oracle_focal`, a strict bound for the plotted focal metric. Legacy `oracle_joint` naming is separated from the focal objective. Absolute scales and maximum gaps are included in the caption.
6. **Formal CCE versus empirical planner separated.** The theory permits an approximate CCE oracle. The reported HP-SPGG and compact Concordia experiments use deterministic exhaustive joint-profile argmax; SOTOPIA uses no CCE. The appendix no longer claims that the reported experiments solve a CCE linear program.
7. **PACT+ implementation disclosed.** The theory defines pairwise-disagreement bonus `D_k`. The finite HP-SPGG code uses a monotone uncertainty-times-reward-variance proxy and posterior-expected welfare for the reported PACT+ row. `D_k` is defined as episode-level: recompute after a posterior update, then hold fixed during that episode's planning pass.
8. **Cost accounting qualified.** The approximately 500k calls / 650M tokens are labelled retrospective suite-level estimates, not per-deployment requirements. Cached HP-SPGG native evaluation is call-free after calibration; online token scoring has the explicit `n H |Theta_i|` upper formula; PACT+ adds zero calls relative to PACT.
9. **Persona misspecification and ethics.** The new mixture experiment separates task regret from persona semantics, and the discussion adds OOD/abstention, subgroup calibration, outcome-disparity, and anti-stereotyping guidance.
10. **Framework positioning.** AutoGen, CAMEL, AgentVerse, and MetaGPT are cited as orchestration frameworks that can host PACT but do not themselves define a hidden-type coordination policy. ECON and A-ToM remain the closer algorithmic baselines.

## Quantitative robustness response

All entries use `K=20`, `n=3`, four personas, 500 paired seeds, and exact full-information evaluation in the unperturbed environment.

| condition | cumulative regret (mean +/- SE) | final true-type mass | conclusion |
|---|---:|---:|---|
| reference | 0.002 +/- 0.000 | 0.995 | calibrated baseline |
| likelihood temperature `T=4` | 0.004 +/- 0.001 | 0.860 | over-dispersion has limited decision cost |
| log-likelihood noise `sigma=1` | 0.005 +/- 0.002 | 0.873 | zero-mean scoring noise is tolerated here |
| top-2 likelihoods | 0.002 +/- 0.000 | 0.995 | no loss in this separated finite library |
| calibration drift `sigma=0.05` | 0.730 +/- 0.036 | 0.699 | systematic model drift is a material risk |
| 50% adjacent-persona mixture | 0.000 +/- 0.000 | 0.371 | good actions do not imply valid persona semantics |
| 32 of 125 planner candidates | 1.410 +/- 0.027 | 0.995 | planner error can dominate tracker error |
| 8 of 125 planner candidates | 3.838 +/- 0.065 | 0.997 | aggressive search truncation is unsafe |

The complete 17-condition table and all 8,500 per-seed records are in the generated analysis JSON/CSV. The experiment is reproducible with `scripts/run_hp_spgg_deployment_robustness.py` and makes no provider calls.

## Point-by-point response

### 1–2. Validity beyond TI/RL/PF and practitioner misuse

**Action:** Added a main-text diagnostic checklist and explicit stop rules. SOTOPIA is described as broad out-of-model descriptive transfer, not a PF-only test. Compact Concordia is described as static known-payoff geometry transfer, not hidden-transition inference.

**Boundary:** We do not provide a theorem under violated TI or RL. The correct recommendation is to use a joint type/dynamics or joint reward model, not to reuse the factored guarantee.

### 3–4. Token probabilities, fixed verbalizers, top-k, and drift

**Action:** Corrected the observation channel to match the implementation and added the robustness study. Top-k and zero-mean likelihood perturbations are benign in the controlled separated library; systematic calibration drift is not.

**Boundary:** These numbers are not a universal logprob robustness theorem. A new API/backbone still requires held-out calibration and posterior-predictive checks.

### 5–6. SOTOPIA intent projection

**Action:** Defined the projection map conceptually, stated that native target labels are absent, and reported the profile-informed reference as a negative check: its average (3.103) is below the best non-oracle average (3.110), and A-ToM-1 exceeds it on Llama (3.359 versus 3.282).

**Not claimed:** No per-family projection accuracy or 10–20% corruption curve is reported because the retained benchmark data contain neither native four-class labels nor the raw experiment inputs needed for a valid corruption rerun. The manuscript now says exactly what data would be required.

### 7–8. Focal versus joint oracle

**Action:** Replaced ambiguous headline language with a strict `oracle_focal` ceiling for focal plots. The Concordia caption reports absolute score ranges and the maximum focal gap. `oracle_policy` on SOTOPIA is labelled a profile-informed best-of-5 search reference with extra budget, not a strict oracle.

### 9–10. CCE and planner details

**Action:** Separated the formal approximate-CCE interface from empirical exhaustive argmax. Added the 32/8 candidate study. LLM latency is outside the CPU planner; it affects action/evaluator calls and observation calibration.

**Correction to the review premise:** SOTOPIA does not run a planner over a surrogate intent menu and does not solve a CCE. Its agents generate open-text utterances autoregressively.

### 11–12. Computational footprint

**Action:** Added a main-text cost paragraph and corrected appendix accounting. The suite total is contextualised as a retrospective estimate. One-time calibration, online call formulas, and incremental PACT+ cost are separated.

**Why no single calls-per-percent number:** The compared methods use incompatible call structures (cached native evaluation, prompted baselines, analytic Concordia, and judged dialogue). A scalar normalisation would obscure rather than control compute. The manuscript reports interface-specific costs instead.

### 13–14. Persona-library coverage

**Action:** Added convex-mixture misspecification at 10%, 25%, and 50%. At 50%, regret stays low while nominal true-type mass falls to 0.371 and MAP accuracy to 0.563. The discussion therefore separates policy quality from semantic type recovery and recommends OOD/abstention.

**Boundary:** This is a controlled interpolation test, not a continuous-persona theorem.

### 15–16. Baseline and literature coverage

**Action:** Added AutoGen, CAMEL, AgentVerse, and MetaGPT to Related Work and explained why they are systems frameworks rather than hidden-type coordination policies. Existing ECON, A-ToM, prompted-belief, LLM-PSRL, Bayesian, and type-agnostic baselines remain the direct algorithm comparisons.

### 17. Notation and `D_k`

**Action:** Standardised the manuscript display to PACT and PACT+ and clarified that `D_k` is recomputed once per posterior update/episode, not at every within-episode planning step. The implementation proxy is disclosed separately from the theoretical quantity.

## Figure/table-specific actions

- **HP-SPGG bars:** Caption now states that each bar has a numeric mean label.
- **Concordia radar:** Caption now reports absolute focal ranges and explicitly identifies the strict focal ceiling.
- **SOTOPIA:** Caption labels the selected family split as descriptive and the best-of-5 line as a non-strict search reference.
- **New robustness evidence:** Representative conditions are in the main text; all 17 are in the appendix.
- **Positive MaaSSim comments:** No claim correction was required by these comments; MaaSSim evidence remains methodologically separate from the TI/RL/PF theorem claim.

## Files

- `arr_paper/main.tex` — main-text revisions and selected robustness table.
- `arr_paper/appendix.tex` — full robustness table, CCE boundary, projection status, and corrected cost accounting.
- `arr_paper/ref.bib` — framework citations.
- `scripts/run_hp_spgg_deployment_robustness.py` — deterministic offline experiment.
- `analysis/hp_spgg_deployment_robustness.json` — full configuration, summaries, and per-seed records.
- `analysis/hp_spgg_deployment_robustness.csv` — compact summary.
- `analysis/hp_spgg_deployment_robustness.md` — readable result report.
