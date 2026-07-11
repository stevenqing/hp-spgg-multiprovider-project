# PACT Paper Finalization TODO

Coding-agent should execute these tasks sequentially. Each task has explicit acceptance criteria. Stop and surface any failure rather than guessing.

Working directory in this repo: `arr_paper/` for paper files. Main files: `arr_paper/main.tex`, `arr_paper/appendix.tex`, `arr_paper/ref.bib`, `arr_paper/figs/`.

---

## Related Work Discovery Summary (context for coding agent)

Lit search identified these prior works that overlap with PACT's "LLM-as-likelihood + Bayesian belief tracking" framing. PACT must cite and differentiate from each. The four-rocks framing of the paper (R1 decoupling theorem, R2 cross-backbone stability, R3 Concordia oracle match, R4 method primitive) survives, but R4 specifically must be reframed from "novel primitive" to "novel application to multi-agent coordination with structural decoupling".

### Tier A: Most critical (must cite + differentiate explicitly)

| Work | Setting | Bayes update style |
|---|---|---|
| **Arumugam & Griffiths, ICLR 2026** ([arXiv:2504.20997](https://arxiv.org/abs/2504.20997)) | Single-agent MDP, LLM-PSRL | LLM-generated NL hypothesis, NL posterior update |
| **LAIP (Gelpi et al., July 2025)** ([arXiv:2507.03682](https://arxiv.org/abs/2507.03682)) | Single observer modelling single target, ToM inverse planning | LLM-simulated likelihood, mathematical posterior |
| **Hypothetical Minds (Cross et al., ICLR 2025)** ([arXiv:2407.07086](https://arxiv.org/abs/2407.07086)) | Multi-agent Melting Pot, ToM | LLM-generated NL strategy hypotheses, reinforcement-based refinement |
| **CoBel-World (Wang et al., Sep 2025)** ([arXiv:2509.21981](https://arxiv.org/abs/2509.21981)) | Multi-agent embodied (TDW-MAT, C-WAH) | Symbolic belief language + zero-shot Bayesian-style LLM reasoning |

### Tier B: Important secondary

| Work | Setting |
|---|---|
| **Bayesian Orchestration (Amin, Jan 2026)** ([arXiv:2601.01522](https://arxiv.org/abs/2601.01522)) | Single-agent cost-aware classification, multi-LLM ensemble |
| **Adaptive Querying with AI Persona Priors (~2026)** ([arXiv:2605.00696](https://arxiv.org/abs/2605.00696)) | Single-user CAT/IRT, closed-form posterior |
| **CSP4SDG (Xu et al., Nov 2025)** ([arXiv:2511.06175](https://arxiv.org/abs/2511.06175)) | Social deduction games (Avalon/Mafia/Werewolf) |
| **Theory of Mind for Multi-Agent Collaboration (Li et al., 2023)** ([arXiv:2310.10701](https://arxiv.org/abs/2310.10701)) | Multi-agent cooperative text game with explicit belief state |

### PACT's defensible novelty given this landscape

1. Multi-agent Markov game with hidden agent personas.
2. Closed-form decoupling theorem under TI+RL+PF.
3. Closed-form Bayesian update via direct next-token probability.
4. CCE planner integration + $\tilde O(\sqrt K)$ regret bound for heterogeneous-type Markov games.

---

## Phase 1 - Critical: Related-work paragraph + citations

### Task 1.1 - Audit existing `ref.bib`

Check Tier A and Tier B works. Acceptance criterion: each of the eight works in Tier A + Tier B has exactly one entry in `ref.bib` with a unique citation key.

### Task 1.2 - Add missing BibTeX entries to `ref.bib`

Append missing entries for:
- `arumugamgriffiths2026exploration`
- `gelpi2025laip`
- `cross2025hypothetical`
- `wang2025cobel`
- `amin2026bayesian`
- `xu2025csp4sdg`
- `li2023tom`
- existing `mu2026adaptive` should be verified

### Task 1.3 - Insert related-work paragraph into `main.tex`

Insert the specified paragraph at the end of Introduction, immediately before the next `\section{...}`.

### Task 1.4 - Compile and verify

Run LaTeX + BibTeX and verify zero unresolved citations/references.

---

## Phase 2 - Optional: LLM-PSRL-verbal baseline

Decision point: skip unless time budget supports roughly 1 day of implementation.

---

## Phase 3 - Optional: Backbone extension for tables

Run Joint-PSRL-Uniform and true shared-type DGP on GPT-5.4-nano, Kimi-K2.6, Llama-Maverick if budget allows.

---

## Phase 4 - Optional: SOTOPIA donate_funds ablation

Run donate_funds ablation or adjust claims if needed.

---

## Phase 5 - Polish and verification

### Task 5.1 - Number consistency audit

Verify numeric claims in `main.tex` and `appendix.tex` against summary files.

### Task 5.2 - Final PDF compile

Compile with BibTeX and require zero unresolved citations/references.

### Task 5.3 - Final zip package

Package `main.tex`, `appendix.tex`, `ref.bib`, `figs/`, `main.pdf`, `acl.sty`, `acl_natbib.bst`, `math_commands.tex`.

---

## Minimum viable for submission

Phase 1 + Phase 5.
