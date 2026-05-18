# HP-SPGG Multi-Provider LLM Research Plan

**Project:** Heterogeneous-Persona Sequential Public-Goods Game (HP-SPGG)  
**Paper:** HT-MG-BC  
**Owner:** Shuqing Shi, KCL  
**Date:** May 2026  
**Estimated API cost:** USD 60-150  
**Estimated wall time:** 12-20 hours, mostly parallelisable  

**Primary benchmark:** HP-SPGG, a custom LLM-instantiated Heterogeneous-Persona Sequential Public-Goods Game benchmark designed for evaluating HT-MG-BC. HP-SPGG is not an off-the-shelf benchmark; it is a controlled paper-specific interactive benchmark constructed to instantiate heterogeneous-type Markov game assumptions with LLM agents and LLM-as-judge rewards.

**Public benchmark extension:** Phase 2 adds independently constructed public benchmarks, specifically Concordia substrates and SOTOPIA-Hard, to address the reviewer concern that HP-SPGG may be too controlled or paper-specific.

---

## 1. Research Objective

This project empirically validates three theoretical claims from HT-MG-BC using a multi-provider LLM implementation of the Heterogeneous-Persona Sequential Public-Goods Game.

The main goal is to show that the HP-SPGG results are:

1. not Claude-specific;
2. not closed-source-specific;
3. reproducible across modern LLM provider families;
4. robust to cross-vendor judge/player configurations.

The three theoretical claims tested are:

1. **Posterior decoupling**  
   H-PSMG matches Joint-PSRL in trajectory behaviour while using `O(n|Theta_i|)` storage rather than `O(|Theta|^n)` storage.

2. **Bayesian regret rate**  
   Bayesian type-aware methods achieve sublinear regret, while type-agnostic methods do not.

3. **Exponential burn-in improvement**  
   H-PSMG+ improves over H-PSMG on degenerate-information environments, with a burn-in advantage that reflects the exponential type-space structure.

---

## 2. Core Research Questions

**RQ1. Cross-provider robustness**  
Does the HP-SPGG algorithmic ordering hold across Anthropic, OpenAI, Google, and open-source Qwen3 models?

**RQ2. H-PSMG+ advantage**  
Is H-PSMG+ the lowest-regret non-oracle method across most or all provider families?

**RQ3. Posterior decoupling**  
Does H-PSMG behave similarly to Joint-PSRL while requiring much less posterior storage?

**RQ4. Burn-in improvement**  
Does H-PSMG+ substantially outperform H-PSMG in deep-trap or degenerate-information environments?

**RQ5. Judge bias**  
Does the H-PSMG+ advantage survive when the player model and judge model come from different vendors?

**RQ6. Model capability scaling**  
Does using stronger player or judge models change the algorithmic ranking?

---

## 3. Provider Matrix

The experiment uses four provider families. Each provider has a cheaper or faster model for player agents and a stronger model for judge scoring.

| Provider | Player model | Player USD/M I/O | Judge model | Judge USD/M I/O | Role |
|---|---|---:|---|---:|---|
| Anthropic | Claude Haiku 4.5 | 1 / 5 | Claude Sonnet 4.6 | 3 / 15 | Tier-1 closed frontier |
| OpenAI | GPT-5.4 Mini | 0.75 / 4.50 | GPT-5.4 | 2.50 / 15 | Tier-1 closed frontier |
| Google | Gemini 2.5 Flash | 0.30 / 2.50 | Gemini 2.5 Pro | 1.25 / 10 | Tier-1 closed efficient |
| Qwen3 / DeepInfra | Qwen3-32B | 0.20 / 0.60 | Qwen3-235B-A22B | 0.50 / 1.50 | Open-source representative |

The provider selection is designed to cover both closed-source and open-source models, as well as both frontier and budget-efficient deployment settings.

---

## 4. Experimental Overview

The full plan contains seven experiments. E1-E5 are the main recommended set; E6-E7 are optional robustness extensions.

| Experiment | Purpose | Status | Estimated total cost |
|---|---|---|---:|
| E1 Calibration | Build reward tensor and test type identifiability | Required | USD 3-8 |
| E2 Sanity check | Verify pipeline before main runs | Required | USD 2-4 |
| E3 Main experiment | Cross-provider regret and decoupling result | Required | USD 16-40 |
| E4 Deep-trap variant | Burn-in improvement claim | Recommended | USD 24-60 |
| E5 Persona audit | Check role-play fidelity | Recommended | USD 0.20-0.80 |
| E6 Cross-judge robustness | Rule out same-vendor judge bias | Optional | USD 16-40 |
| E7 Within-vendor scaling | Test model capability effects | Optional | Anthropic only, USD 5-80 |

Recommended priority:

| Priority | Experiments | Purpose |
|---|---|---|
| P0 | E1 + E5 | Confirm personas, reward tensor, and judge reliability |
| P1 | E2 | Prevent wasting budget on broken pipeline |
| P2 | E3 | Produce the main paper result |
| P3 | E4 | Support the burn-in theorem empirically |
| P4 | E6 | Address judge-bias reviewer concerns |
| P5 | E7 | Add model-capability ablation |

Minimum publishable version:

```text
E1 + E2 + E3 + E5
```

Strong camera-ready version:

```text
E1 + E2 + E3 + E4 + E5 + E6
```

Full version:

```text
E1 + E2 + E3 + E4 + E5 + E6 + selected E7
```

---

## 5. Code Layout

The project code should use a provider-agnostic experiment runner with backend-specific LLM wrappers.

```text
llm_hpgg/
├── personas.py
├── environment.py
├── llm_agent.py
├── llm_agent_openai.py
├── llm_agent_google.py
├── llm_agent_deepinfra.py
├── coordinator.py
├── calibration.py
├── run_experiment.py
├── plot_results.py
├── audit_personas.py
├── build_trap_calibration.py
└── results/
    ├── anthropic/
    ├── openai/
    ├── google/
    └── qwen3/
```

The existing `llm_agent.py` should act as the top-level dispatcher. The backend is selected through:

```bash
export LLM_HPGG_BACKEND=anthropic
```

Supported values:

```text
anthropic
openai
google
qwen3
mixed
```

Each backend should expose a shared function:

```python
def _call_llm(system_prompt, user_message, model, max_tokens=256, temperature=0.8):
    ...
```

The `mixed` backend should read:

```bash
export LLM_HPGG_PLAYER_BACKEND=anthropic
export LLM_HPGG_JUDGE_BACKEND=openai
```

---

## 6. Phase 0: Pre-Experiment Setup

**Goal:** Confirm that all providers, model IDs, prompts, and API paths work before spending significant budget.

Tasks:

1. Confirm actual model IDs via provider APIs.
2. Confirm pricing and rate limits.
3. Smoke-test one player call per backend.
4. Smoke-test one judge call per backend.
5. Verify judge outputs are parseable as scalar satisfaction scores.
6. Freeze persona prompts, judge prompts, environment version, and random seeds.
7. Create provider-specific output folders.

Expected outputs:

```text
config/providers.yaml
prompts/personas_v1.md
prompts/judge_v1.md
logs/smoke_<backend>.log
```

Go / no-go criteria:

- Every backend returns non-empty player responses.
- Every judge model returns parseable scores.
- No major safety filter or API routing issue appears.

---

## 7. Phase 1: Calibration and Persona Validity

Corresponding experiments:

```text
E1 Calibration
E5 Persona audit
```

**Goal:** Verify that personas produce distinguishable behaviour and that the reward tensor has enough type identifiability.

Run calibration once per provider:

```bash
for backend in anthropic openai google qwen3; do
    export LLM_HPGG_BACKEND=$backend
    python calibration.py --out calibration_$backend.npy 2>&1 \
        | tee logs/E1_$backend.log
done
```

Run persona audit:

```bash
for backend in anthropic openai google qwen3; do
    export LLM_HPGG_BACKEND=$backend
    python audit_personas.py --out logs/E5_audit_$backend.txt
done
```

Acceptance criteria:

| Metric | Criterion |
|---|---|
| TID min-gap | At least 0.05 |
| Persona reward ordering | altruistic_builder > free_rider |
| Per-cell variance | Below 0.3 |
| Altruistic builder behaviour | Should not contribute <= 0.1 frequently |
| Free rider behaviour | Should not behave like a consistent high contributor |

Decision rules:

- If TID min-gap is below 0.05, strengthen persona prompts and re-run E1.
- If judge scores are weakly discriminative, add anchored examples for 0.0, 0.5, and 1.0.
- If Gemini blocks prompt wording, replace terms such as `secret` with `private belief` and `exploit` with `prioritise self-interest`.
- If Qwen3 endpoint is unstable, add retry/backoff or switch host to Together AI.

Outputs:

```text
calibration_anthropic.npy
calibration_openai.npy
calibration_google.npy
calibration_qwen3.npy
logs/E1_<backend>.log
logs/E5_audit_<backend>.txt
```

---

## 8. Phase 2: Sanity Check

Corresponding experiment:

```text
E2 Sanity check
```

**Goal:** Verify the experiment pipeline before running the expensive main experiment.

Run:

```bash
for backend in anthropic openai google qwen3; do
    export LLM_HPGG_BACKEND=$backend
    python run_experiment.py --K 10 --n 3 --seeds 2 --beta 1.0 \
        --algos hpsmg_plus hpsmg oracle random \
        --calibration calibration_$backend.npy \
        --out results/$backend/E2_sanity.npz \
        2>&1 | tee logs/E2_$backend.log
done
```

Acceptance criteria:

1. Oracle regret is exactly 0.0.
2. Random regret is at least about 3x larger than Bayesian methods.
3. H-PSMG+ is no worse than H-PSMG within SEM.
4. All `.npz` output files have the expected schema.
5. Logs do not contain many parse failures, rate-limit failures, or empty model responses.

If this phase fails, do not proceed to E3 until the root cause is fixed.

Common failure modes:

| Symptom | Likely cause | Fix |
|---|---|---|
| Oracle regret > 0 | Bug in regret formula | Check regret as oracle welfare minus algorithm welfare |
| Random approximately equals Bayesian methods | Judge or environment not discriminative | Improve judge prompt or reward scale |
| H-PSMG+ much worse than H-PSMG | Bonus design or configuration issue | Inspect H-PSMG+ implementation and beta setting |
| Many API failures | Rate limits or network instability | Add retry/backoff and reduce concurrency |

Outputs:

```text
results/<backend>/E2_sanity.npz
logs/E2_<backend>.log
```

---

## 9. Phase 3: Main Cross-Provider Experiment

Corresponding experiment:

```text
E3 Main experiment
```

**Goal:** Produce the headline paper result: cross-provider cumulative regret and algorithmic ranking.

Run:

```bash
for backend in anthropic openai google qwen3; do
    export LLM_HPGG_BACKEND=$backend
    python run_experiment.py --K 30 --n 3 --seeds 5 --beta 1.0 \
        --algos hpsmg_plus hpsmg joint_psrl map_greedy random oracle \
        --calibration calibration_$backend.npy \
        --out results/$backend/E3_main.npz \
        2>&1 | tee logs/E3_$backend.log
done

python plot_results.py --inputs results/*/E3_main.npz \
    --output figs/E3_cross_provider.pdf
```

Expected qualitative ordering:

```text
Oracle < H-PSMG+ <= H-PSMG ~= MAP-Greedy < Joint-PSRL << Random
```

Paper-level acceptance criteria:

1. H-PSMG+ is the lowest-regret non-oracle method on at least 3 of 4 providers.
2. If the fourth provider differs, it should be within SEM of the best method.
3. Random is substantially worse than all Bayesian methods on every provider.
4. H-PSMG and Joint-PSRL have closely matched regret or trajectory behaviour.
5. The storage contrast is clearly documented: H-PSMG uses `O(n|Theta_i|)`, Joint-PSRL uses `O(|Theta|^n)`.

Main analyses:

1. Final cumulative regret at K = 30, mean +/- SEM.
2. Provider-wise regret curves.
3. H-PSMG+ vs H-PSMG paired seed comparison.
4. H-PSMG vs Joint-PSRL behavioural closeness.
5. Random-vs-Bayesian separation.

Outputs:

```text
results/<backend>/E3_main.npz
figs/E3_cross_provider.pdf
tables/E3_cross_provider_regret.tex
analysis/E3_summary.json
```

---

## 10. Phase 4: Deep-Trap Burn-In Experiment

Corresponding experiment:

```text
E4 Deep-trap variant
```

**Goal:** Test the burn-in improvement predicted by Theorem 8.5(ii).

First build trap calibration tensors:

```bash
for backend in anthropic openai google qwen3; do
    python build_trap_calibration.py --in calibration_$backend.npy \
        --out calibration_${backend}_trap.npy
done
```

Then run:

```bash
for backend in anthropic openai google qwen3; do
    export LLM_HPGG_BACKEND=$backend
    python run_experiment.py --K 50 --n 3 --seeds 8 --beta 1.0 \
        --algos hpsmg_plus hpsmg oracle \
        --calibration calibration_${backend}_trap.npy \
        --out results/$backend/E4_trap.npz \
        2>&1 | tee logs/E4_$backend.log
done
```

Key metrics:

1. Burn-in length.
2. Early regret slope.
3. Cumulative regret at K = 10, 20, and 50.
4. H-PSMG+ / H-PSMG regret ratio.
5. Time-to-near-oracle threshold.

Acceptance criteria:

1. H-PSMG+ outperforms H-PSMG on every provider.
2. The K = 50 gap is at least 2x or otherwise visibly substantial.
3. H-PSMG has a higher early-stage regret slope.
4. The result direction supports the exponential burn-in improvement claim.

Outputs:

```text
calibration_<backend>_trap.npy
results/<backend>/E4_trap.npz
figs/E4_burn_in_cross.pdf
tables/E4_burn_in.tex
```

---

## 11. Phase 5: Cross-Judge Robustness

Corresponding experiment:

```text
E6 Cross-judge robustness
```

**Goal:** Rule out same-vendor evaluation bias by mixing player and judge providers.

Recommended cross-pairs:

| Player backend | Judge backend |
|---|---|
| Anthropic | OpenAI |
| OpenAI | Anthropic |
| Google | Anthropic |
| Qwen3 | OpenAI |

Example run:

```bash
export LLM_HPGG_BACKEND=mixed
export LLM_HPGG_PLAYER_BACKEND=anthropic
export LLM_HPGG_JUDGE_BACKEND=openai

python calibration.py --out calibration_mixed_anth_oai.npy

python run_experiment.py --K 30 --n 3 --seeds 5 --beta 1.0 \
    --algos hpsmg_plus hpsmg oracle random \
    --calibration calibration_mixed_anth_oai.npy \
    --out results/mixed_anth_oai/E6.npz
```

Acceptance criteria:

1. H-PSMG+ beats or matches H-PSMG on all 4 cross-pairs.
2. Random remains much worse than Bayesian methods.
3. If absolute judge scales differ, compare normalized regret or within-pair ranks.

Outputs:

```text
results/mixed_*/E6.npz
figs/E6_cross_judge.pdf
tables/E6_cross_judge.tex
```

Paper use:

This result should be used to answer reviewer concerns about same-vendor player/judge evaluation bias.

---

## 12. Phase 6: Within-Vendor Scaling

Corresponding experiment:

```text
E7 Within-vendor scaling
```

**Goal:** Test whether stronger player or judge models change the algorithmic ranking.

Recommended Anthropic configurations:

| Player model | Judge model | Priority |
|---|---|---|
| Haiku 4.5 | Sonnet 4.6 | Baseline |
| Sonnet 4.6 | Sonnet 4.6 | Recommended |
| Sonnet 4.6 | Opus 4.7 | Optional |
| Opus 4.7 | Opus 4.7 | Stress test only |

Example:

```bash
python run_experiment.py --K 30 --n 3 --seeds 5 --beta 1.0 \
    --player-model claude-sonnet-4-6-20250929 \
    --judge-model claude-sonnet-4-6-20250929 \
    --out results/anthropic_e7/E7_sonnet_sonnet.npz
```

Questions addressed:

1. Does stronger player capability reduce persona stochasticity?
2. Does type inference become easier with stronger role-play?
3. Does H-PSMG+ still improve over H-PSMG?
4. Does the bonus become unnecessary or harmful in high-capability regimes?

Acceptance criteria:

1. H-PSMG+ remains below H-PSMG in most configurations.
2. If the gap shrinks, interpret this as stronger persona adherence reducing the exploration burden.
3. If the ranking reverses, discuss whether H-PSMG+ over-explores under high-capability player models.

Outputs:

```text
results/anthropic_e7/*.npz
figs/E7_within_vendor.pdf
```

---

## 13. Execution Timeline

### Day 1: Calibration and persona validity

Estimated time: about 1.5 hours  
Estimated cost: about USD 8

Tasks:

1. Run E1 calibration for all four providers.
2. Run E5 persona audit for all four providers.
3. Inspect TID gaps, reward ordering, variance, and audit logs.
4. Strengthen prompts and re-run E1 if any provider fails.

### Day 2: Sanity and main experiment

Estimated time: about 3 hours, parallelised  
Estimated cost: about USD 20-40

Tasks:

1. Run E2 sanity check.
2. Verify oracle, random, and Bayesian-method behaviour.
3. Run E3 main experiment across all providers.
4. Generate the first cross-provider regret figure.

### Day 3: Deep-trap burn-in

Estimated time: about 3 hours, parallelised  
Estimated cost: about USD 40-60

Tasks:

1. Build trap calibration tensors.
2. Run E4 across all providers.
3. Generate burn-in comparison figure.

### Day 4: Optional robustness

Estimated time: about 3 hours  
Estimated cost: about USD 50+

Tasks:

1. Run E6 cross-judge pairs.
2. Run selected E7 Anthropic scaling configurations.
3. Generate robustness figures and appendix tables.

### Day 5: Paper integration

Estimated time: about 2 hours  
Estimated cost: no additional LLM API cost

Tasks:

1. Aggregate results into paper tables.
2. Update Section 9.7.
3. Add cross-provider robustness subsection.
4. Add burn-in and cross-judge figures.
5. Add cost transparency and model-version footnotes.

---

## 14. Cost Summary

Estimated costs for E1-E5:

| Provider | E1 | E2 | E3 | E4 | E5 | Total |
|---|---:|---:|---:|---:|---:|---:|
| Anthropic | 0.70 | 1.00 | 7.50 | 11.00 | 0.10 | 20.30 |
| OpenAI | 0.80 | 1.20 | 8.50 | 13.00 | 0.10 | 23.60 |
| Google | 0.40 | 0.60 | 4.20 | 6.50 | 0.05 | 11.75 |
| Qwen3 / DeepInfra | 0.20 | 0.30 | 2.10 | 3.20 | 0.03 | 5.83 |
| Total | 2.10 | 3.10 | 22.30 | 33.70 | 0.28 | 61.48 |

Optional additions:

| Optional experiment | Estimated cost |
|---|---:|
| E6 cross-judge robustness | +USD 30 |
| E7 within-Anthropic scaling | +USD 60 |
| Prompt rerun buffer | +20-30% |

Realistic camera-ready budget:

```text
USD 120-150
```

---

## 15. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Provider-specific persona drift | Weak calibration and unstable algorithm ranking | Strengthen persona prompts or upgrade player model |
| Judge scoring too noisy | High regret variance | Add anchored scoring examples and increase calibration samples |
| Gemini safety filtering | Blocked or softened persona responses | Replace sensitive wording with neutral alternatives |
| Qwen3 endpoint instability | Failed runs | Add retry/backoff or use Together AI as fallback host |
| H-PSMG+ not always lowest | Weaker headline claim | Use SEM, paired tests, and rank-based reporting |
| E4 burn-in gap too small | Weak empirical support for theorem | Strengthen trap construction, increase K, or increase seeds |
| Cost overrun | Incomplete optional experiments | Prioritise E1-E4 and delay E6/E7 |
| Wrong model tier routing | Unexpected high cost | Log model names for every API call and inspect logs |

---

## 16. Troubleshooting Matrix

| Symptom | Likely cause | Fix |
|---|---|---|
| TID min-gap < 0.05 | Weak provider role-play adherence | Strengthen persona prompts or use stronger player model |
| Oracle regret > 0 | Regret formula bug | Check regret = oracle welfare - algorithm welfare |
| Random approximately equals H-PSMG | Judge is non-discriminative | Improve judge prompt or upgrade judge model |
| H-PSMG+ much worse than H-PSMG | Bonus design issue | Inspect H-PSMG+ bonus and beta configuration |
| Large provider-to-provider differences | Persona or judge scale drift | Use normalized regret and audit logs |
| Cost overrun | Wrong model tier | Check logs for unexpected Sonnet, Opus, GPT-5.5, or Pro calls |
| Rate-limit errors | Too much concurrency | Add sleep, retry, or run providers sequentially |
| Qwen3 5xx errors | Hosting instability | Retry with exponential backoff or switch host |
| Gemini blocks prompt | Safety filter issue | Use softer vocabulary in persona prompts |

---

## 17. Output Deliverables

Expected final directory structure:

```text
results/
├── anthropic/
│   ├── E2_sanity.npz
│   ├── E3_main.npz
│   └── E4_trap.npz
├── openai/
│   ├── E2_sanity.npz
│   ├── E3_main.npz
│   └── E4_trap.npz
├── google/
│   ├── E2_sanity.npz
│   ├── E3_main.npz
│   └── E4_trap.npz
├── qwen3/
│   ├── E2_sanity.npz
│   ├── E3_main.npz
│   └── E4_trap.npz
├── mixed_*/
│   └── E6.npz
└── anthropic_e7/
    └── *.npz

figs/
├── E3_cross_provider.pdf
├── E4_burn_in_cross.pdf
├── E5_persona_audit.pdf
├── E6_cross_judge.pdf
└── E7_within_vendor.pdf

logs/
└── *_<backend>.log

calibration_anthropic.npy
calibration_openai.npy
calibration_google.npy
calibration_qwen3.npy
calibration_*_trap.npy
```

---

## 18. Paper Integration Plan

Update the HT-MG-BC paper as follows:

1. Replace the single-provider Table 4 with a four-provider table.
2. Add Figure 6: cross-provider cumulative regret.
3. Add Figure 7: deep-trap burn-in across providers.
4. Update Section 9.7 to say HP-SPGG is evaluated across four provider families.
5. Add Section 9.7.2: Cross-provider robustness.
6. Add a footnote listing exact model versions.
7. Add cost transparency line.
8. Add appendix table for E6 cross-judge results.
9. Add appendix discussion for selected E7 results.
10. Include backend code and configuration files in supplementary materials.

Suggested paper paragraph:

```latex
\paragraph{Cross-provider robustness.} To establish that the algorithmic ordering
is not specific to a single LLM vendor, we replicate the main experiment across
four provider families: Anthropic (Claude Haiku 4.5 / Sonnet 4.6), OpenAI
(GPT-5.4 Mini / GPT-5.4), Google (Gemini 2.5 Flash / 2.5 Pro), and open-source
Qwen3 (32B / 235B-A22B via DeepInfra). Table~\ref{tab:hp-spgg-providers}
reports cumulative regret at $K = 30$, mean $\pm$ SEM over $5$ seeds. H-PSMG\textsuperscript{+}
achieves the lowest non-oracle regret on most provider families, while Random
incurs substantially larger regret than Bayesian methods on every provider.
This confirms that the type-inference bottleneck is intrinsic to the problem
rather than an artefact of a particular model provider.
```

Suggested cross-judge paragraph:

```latex
\paragraph{Cross-judge robustness.} To rule out same-vendor evaluation bias, we
evaluate four cross-pairs in which the player model and judge model come from
different providers. The H-PSMG\textsuperscript{+} versus H-PSMG ordering is
preserved across the cross-pairs, indicating that the algorithmic advantage is
not an artefact of within-vendor self-evaluation.
```

---

## 19. Final Checklist

- [ ] Confirm exact provider model IDs.
- [ ] Implement OpenAI backend.
- [ ] Implement Google backend.
- [ ] Implement DeepInfra Qwen3 backend.
- [ ] Add backend dispatcher in `llm_agent.py`.
- [ ] Add optional mixed backend support.
- [ ] Add `--player-model` and `--judge-model` overrides.
- [ ] Run E1 calibration for four providers.
- [ ] Run E5 persona audit.
- [ ] Review TID gaps and persona fidelity.
- [ ] Run E2 sanity check.
- [ ] Run E3 main cross-provider experiment.
- [ ] Generate E3 cross-provider figure.
- [ ] Build trap calibration tensors.
- [ ] Run E4 deep-trap experiment.
- [ ] Generate E4 burn-in figure.
- [ ] Optionally run E6 cross-judge robustness.
- [ ] Optionally run selected E7 scaling runs.
- [ ] Replace paper Table 4 with four-provider table.
- [ ] Add cross-provider robustness subsection.
- [ ] Add cost transparency line.
- [ ] Add model-version footnote.
- [ ] Package results, figures, logs, configs, and backend code.

---

## 20. Research Narrative

The recommended narrative is not that the paper compares LLMs. The stronger framing is:

> HP-SPGG is a vendor-robust empirical instantiation of HT-MG-BC. Across closed frontier, closed efficient, open frontier, and open budget model families, the same algorithmic ordering emerges: Bayesian type-aware methods dominate type-agnostic baselines, H-PSMG matches joint posterior reasoning at far lower storage cost, and H-PSMG+ improves burn-in in degenerate-information regimes.

This makes the multi-provider design serve the theory rather than turning the section into a generic model leaderboard.

---

## 21. One-Sentence Plan

First validate persona and judge quality with E1/E5, then run E2 to protect the budget, use E3 for the main cross-provider result, use E4 for the burn-in theorem, and add E6/E7 only if a stronger camera-ready robustness story is needed.

---

# Part B: Phase 2 — Scaling to Public Benchmarks

Phase 1 above uses HP-SPGG, the benchmark we construct, to give a controlled proof of concept where the HT-MG-BC assumptions are directly inspectable. Phase 2 extends the evaluation to independently constructed public benchmarks that we did not design. This gives a standard reviewer response to the concern that the benchmark is contrived: first show the mechanism in HP-SPGG, then show transfer to external benchmark environments.

## 22. Three-Tier Benchmark Structure

```text
Tier 1: HP-SPGG (ours)             -> controlled proof of concept
        n=3, K=30, |Theta_i|=4      -> all core assumptions verifiable
        4 providers, USD 60-80      -> headline cross-provider figure

Tier 2: Concordia substrates        -> public LLM/social-simulation benchmark
        Pub Coordination
        Labor Collective Action     -> mixed-motive social dilemmas
        2 providers, USD 120-160    -> paper Section 9.7.3

Tier 3: SOTOPIA-Hard                -> natural-language stress test
        14 hand-curated episodes    -> multi-turn dialogue, hidden goals
        2 providers, USD 30-50      -> paper Section 9.7.4
```

**Total budget across all tiers:** approximately USD 210-290, compared with USD 60-150 for Tier 1 alone.

**Cross-tier acceptance criterion:** H-PSMG+ should achieve the lowest non-oracle regret on at least one substrate from each tier. The full benchmark suite is designed to triangulate the algorithm's value across controlled mechanism tests, independently designed game environments, and natural-language interaction.

## 23. Tier 2: Concordia Substrates

Concordia is DeepMind's library for generative agent-based modelling and has been used in the NeurIPS Concordia contests. The public benchmark extension should use the two substrates whose structure maps most cleanly to HT-MG-BC:

1. Pub Coordination
2. Labor Collective Action

The intended role of Concordia is not to replace HP-SPGG, but to show that the algorithmic advantage transfers to environments we did not design.

### 23.1 Pub Coordination

**Substrate description:** A small population of agents decides which pub to visit on each day. Each agent has hidden fan loyalty to one of several sports teams. A pub is satisfying when the agent's team is shown there and enough fellow fans are present.

**HT-MG-BC mapping:**

| HT-MG-BC element | Concordia Pub Coordination |
|---|---|
| Type `theta_i` | Fan loyalty, one of 4 teams |
| State `s` | Day's match schedule |
| Action `a_i` | Pub chosen by agent `i` |
| Reward `r_i` | Own satisfaction based on team match and fellow fans |
| Coordinator policy | Chooses match schedule and pub recommendation |
| Horizon `K` | 20-30 days |

**Assumption notes:**

- TI holds because the match schedule is set independently of agent types.
- RL holds because each agent's satisfaction depends on its own loyalty, given the schedule and pub choices.
- PF holds if fan loyalties are sampled independently.
- TID must be checked empirically through calibration.
- ISI holds through the first schedule chosen by the coordinator.
- CSR requires using the centralised-coordinator variant, where the coordinator recommends a joint pub assignment. The fully decentralised version should be left for future work.

**Implementation sketch:**

```python
# llm_hpgg_concordia/run_pub_coordination.py
from concordia.contrib.contest_2024 import pub_coordination
from coordinator import CoordinatorState, dispatch, update_posterior

substrate = pub_coordination.build(
    num_players=4,
    num_days=20,
    num_teams=4,
    background_players=["Maria", "David", "Lisa", "Marcus"],
)

R = calibrate_pub_substrate(substrate, num_samples=3)
state = CoordinatorState(n=4, R=R)
true_loyalties = substrate.get_hidden_types()

for k in range(K):
    action = dispatch("hpsmg_plus", state, rng=rng)
    substrate.set_action(action)
    rewards = substrate.step()
    update_posterior(state, action, rewards)
```

**Cost estimate:** about USD 6-9 per provider. With Anthropic and OpenAI, Pub Coordination should cost roughly USD 16.

### 23.2 Labor Collective Action

**Substrate description:** Workers in a factory decide whether to strike or work. Striking costs wages but creates pressure on management; enough strike participation can generate a wage rise that benefits all workers. Workers have hidden dispositions such as union loyalist, fence-sitter, management ally, or opportunist.

**HT-MG-BC mapping:**

| HT-MG-BC element | Concordia Labor Collective Action |
|---|---|
| Type `theta_i` | Worker disposition, one of 4 archetypes |
| State `s` | Management offer: low, medium, or high |
| Action `a_i` | Strike or work |
| Reward `r_i` | Wage plus ideology/disposition-dependent satisfaction |
| Coordinator policy | Chooses management offer and recommends strike participation |
| Horizon `K` | 20 rounds |

**Why include both Concordia substrates:** Pub Coordination gives a smoother and more symmetric hidden-loyalty coordination problem, while Labor Collective Action gives an asymmetric, conflict-driven mixed-motive problem. Together they test whether H-PSMG+ works beyond the structure of HP-SPGG.

**Cost estimate:** about USD 8-10 per provider. With Anthropic and OpenAI, Labor Collective Action should cost roughly USD 20.

### 23.3 Concordia Setup

Current local setup uses isolated environments because Concordia and SOTOPIA have different Python-version constraints. On this Windows machine `git` was not available in PowerShell, so the setup script downloads GitHub zip archives.

```powershell
scripts\setup_phase2_external_envs.ps1

$env:LLM_HPGG_OFFLINE = "1"
.venvs\concordia-py314\Scripts\python.exe `
    -m llm_hpgg_concordia.run_concordia_baselines `
    --model offline `
    --out analysis\concordia_baseline_choice_sweep_offline.json
```

Implemented scaffold: `llm_hpgg_concordia.cloudgpt_model.HPGGConcordiaLanguageModel` implements Concordia's `LanguageModel` interface over our provider layer, and `llm_hpgg_concordia.embedder.HashingEmbedder` provides a deterministic local embedder for smoke runs. `llm_hpgg_concordia.run_pub_coordination` now runs the official Concordia `examples/games/pub_coordination` simulation with the deterministic `puppet` config as a smoke test. The next step is to run live-model `london_mini`, then add haggling/labor-style mixed-motive substrates.

## 24. Tier 3: SOTOPIA-Hard

SOTOPIA-Hard is a hand-curated subset of 14 SOTOPIA episodes, each involving ambiguous, high-conflict, or subtle-norm social interaction. Each episode has two agents with hidden private goals, and SOTOPIA-Eval scores each agent across dimensions such as goal completion.

**Why include SOTOPIA-Hard:** It tests whether H-PSMG+ works in multi-turn natural-language dialogue, rather than only in single-step or structured game environments.

**HT-MG-BC adaptation:**

| HT-MG-BC element | SOTOPIA-Hard adaptation |
|---|---|
| Type `theta_i` | Agent private goal, restricted to a 3-element per-episode goal space |
| State `s` | Dialogue state: turn number and dialogue history |
| Action `a_i` | Intent class: cooperate, probe, commit, or decline |
| Natural-language realisation | Player LLM expands intent class into an utterance |
| Reward `r_i` | SOTOPIA-Eval goal-completion score at episode end |

The original SOTOPIA goals are free-form text, so this plan restricts each episode to a 3-element discrete type space: the true goal plus two plausible alternatives constructed for that episode. This keeps the evaluation aligned with the discrete-type assumption in HT-MG-BC.

**Implementation sketch:**

```python
# llm_hpgg_sotopia/run_sotopia_hard.py
from sotopia.envs import ParallelSotopiaEnv
from coordinator import CoordinatorState, dispatch, update_posterior

EPISODES = load_sotopia_hard()
GOAL_SPACES = load_goal_perturbations()

for episode, goal_space in zip(EPISODES, GOAL_SPACES):
    env = ParallelSotopiaEnv(episode)
    state = CoordinatorState(n=2, R=calibration_for_episode(episode))
    true_types = (0, 0)

    for turn in range(10):
        action = dispatch("hpsmg_plus", state, rng=rng)
        utterances = [
            llm_agent(
                persona=goal_space[true_types[i]],
                intent_class=action.intent_class[i],
                history=env.history,
            )
            for i in range(2)
        ]
        env.step(utterances)

    rewards = sotopia_eval_judge(env.transcript, episode)
    update_posterior(state, action, rewards)
```

**Cost estimate:** 14 episodes x 5 seeds x 3 algorithms x about 10 turns x player/judge calls gives roughly 4200 calls, or USD 15-25 per provider. With Anthropic and OpenAI, the expected cost is around USD 40.

## 25. Updated Execution Timeline for Phase 2

### Day 4: Concordia

Estimated time: about 3 hours  
Estimated cost: about USD 40

```powershell
scripts\setup_phase2_external_envs.ps1

$env:LLM_HPGG_BACKEND = "cloudgpt"
$env:CLOUDGPT_USE_AZURE_CLI = "1"
.venvs\concordia-py314\Scripts\python.exe `
    -m llm_hpgg_concordia.run_concordia_baselines `
    --model DeepSeek-V3.2 `
    --out analysis\concordia_baseline_choice_sweep_DeepSeek_V3_2.json

# Next milestone: official pub_coordination runner using HPGGConcordiaLanguageModel.
```

### Day 5: SOTOPIA-Hard

Estimated time: about 2 hours  
Estimated cost: about USD 40

```powershell
$env:SOTOPIA_STORAGE_BACKEND = "local"
$env:LLM_HPGG_BACKEND = "cloudgpt"
$env:CLOUDGPT_USE_AZURE_CLI = "1"
.venvs\sotopia-py312\Scripts\python.exe `
    -m llm_hpgg_sotopia.run_sotopia_baselines `
    --model DeepSeek-V3.2 `
    --out analysis\sotopia_baseline_action_sweep_DeepSeek_V3_2.json

# Next milestone: official SOTOPIA local-storage episode runner using HPGGSotopiaAgent.
.venvs\sotopia-py312\Scripts\python.exe `
    -m llm_hpgg_sotopia.run_episode_smoke `
    --baseline llm_belief `
    --model DeepSeek-V3.2 `
    --turns 3 `
    --out analysis\sotopia_official_episode_smoke_DeepSeek_V3_2.json
```

### Day 6: Analysis and Paper Update

Estimated time: about 3 hours  
Estimated cost: no additional LLM API cost

Tasks:

1. Aggregate Phase 1 and Phase 2 results.
2. Generate a three-tier comparison figure.
3. Write Section 9.7.3 for Concordia results.
4. Write Section 9.7.4 for SOTOPIA-Hard results.
5. Update the cross-tier robustness paragraph.

## 26. Updated Cost Summary

| Tier | Benchmark | Providers | Cost | Cumulative |
|---|---|---|---:|---:|
| 1 | HP-SPGG E1-E5 | Anthropic, OpenAI, Google, Qwen3 | USD 61 | USD 61 |
| 1 | HP-SPGG E6 cross-judge | 4 mixed pairs | USD 30 | USD 91 |
| 1 | HP-SPGG E7 within-Anthropic | Anthropic only | USD 60 | USD 151 |
| 2 | Concordia Pub Coordination | Anthropic, OpenAI | USD 16 | USD 167 |
| 2 | Concordia Labor Collective | Anthropic, OpenAI | USD 20 | USD 187 |
| 3 | SOTOPIA-Hard | Anthropic, OpenAI | USD 40 | USD 227 |
| Buffer | 20% re-runs | All tiers | USD 45 | USD 272 |

**Total realistic camera-ready budget:** approximately USD 270-310.

**Minimal scope:** skip optional E6/E7 and run Phase 2 on Anthropic only.

```text
Phase 1 E1-E5 across 4 providers: USD 61
Concordia on 1 provider:          USD 20
SOTOPIA-Hard on 1 provider:       USD 20
Buffer:                           USD 20
Total minimum:                    USD 120
```

## 27. Updated Paper Template

The planned single Section 9.7 should become a multi-subsection LLM benchmark section.

```latex
\subsection{LLM-based heterogeneous public-goods coordination}
\label{sec:experiments-llm}

We evaluate H-PSMG\textsuperscript{+} on three tiers of LLM benchmarks. \textbf{Tier 1}
(HP-SPGG, \S\ref{sec:experiments-hp-spgg}) is a controlled benchmark we construct
in which the HT-MG-BC assumptions are verifiable by construction; this gives a
proof of concept across four LLM provider families. \textbf{Tier 2} (Concordia,
\S\ref{sec:experiments-concordia}) scales the evaluation to two public substrates
from DeepMind's Concordia benchmark, demonstrating that the algorithmic advantage
transfers to environments we did not design. \textbf{Tier 3} (SOTOPIA-Hard,
\S\ref{sec:experiments-sotopia}) stresses the algorithm on hand-curated multi-turn
natural-language episodes from the SOTOPIA benchmark.

\subsubsection{Tier 1: Controlled proof of concept on HP-SPGG}
\label{sec:experiments-hp-spgg}
[Existing HP-SPGG description.]

\subsubsection{Tier 2: Scaling to Concordia substrates}
\label{sec:experiments-concordia}
We evaluate on two substrates from the Concordia framework: \emph{Pub Coordination}
and \emph{Labor Collective Action}. For each substrate, we map the latent loyalty
or disposition to HT-MG-BC's hidden type $\theta_i$ and run the coordinator to
choose the exogenous state and per-agent policy recommendation. Reward signals
are analytic per-agent welfare functions provided by the substrate, so no LLM
judge is required. Table~\ref{tab:hp-spgg-concordia} reports cumulative regret
over $K = 20$ rounds across two LLM providers.

\subsubsection{Tier 3: SOTOPIA-Hard natural-language dialogue}
\label{sec:experiments-sotopia}
We evaluate on the hand-curated SOTOPIA-Hard episodes. Each episode involves two
agents with hidden private goals, restricted to a per-episode three-element type
space. The coordinator chooses each agent's intent class; the player LLM expands
the intent into a natural-language utterance. Rewards are SOTOPIA-Eval per-agent
goal-completion scores.
```

## 28. Cross-Tier Robustness Criterion

For the paper to claim broad usefulness, the target evidence pattern is:

| Tier | Desired H-PSMG+ result |
|---|---|
| Tier 1 HP-SPGG | Lowest non-oracle on at least 3 of 4 providers |
| Tier 2 Concordia | Lowest non-oracle on at least 2 of 2 substrates for Anthropic and at least 1 of 2 for OpenAI |
| Tier 3 SOTOPIA-Hard | Lowest non-oracle on at least 8 of 14 episodes |

If any tier fails, the paper can still report the failure mode honestly. The three tiers are complementary rather than redundant:

1. Tier 1 isolates the mechanism under controlled assumptions.
2. Tier 2 tests generalisation to independently designed game-theoretic environments.
3. Tier 3 tests generalisation to natural-language interaction.

A reviewer asking whether the result works outside the custom HP-SPGG benchmark gets two distinct external tests: Concordia and SOTOPIA-Hard.

## 29. Phase 2 Status

Phase 2 is ready to integrate. Concordia and SOTOPIA are Python-installable and have documented APIs. The main engineering task is wrapping their substrates with the existing `CoordinatorState` and `dispatch` interface. Expected implementation effort is about one day of coding, followed by the scripted runs above.

---

# Part E: Integrated Baseline Suite Added During Execution

This section records the additional baselines that were implemented and run after the original plan was drafted. These should be treated as part of the main HP-SPGG evaluation plan going forward, not as ad-hoc side experiments.

## 30. Unified HP-SPGG baseline suite

The HP-SPGG benchmark now includes eleven methods: nine tabular / posterior / MARL baselines and two LLM-based coordinator baselines.

| # | Method | Family | Posterior over hidden types? | Purpose | Implementation |
|---:|---|---|:--:|---|---|
| 1 | `hpsmg_plus` | Ours | factored | Proposed method with type-discrimination bonus | `llm_hpgg/coordinator.py` |
| 2 | `hpsmg` | Ours | factored | Ablation without bonus | `llm_hpgg/coordinator.py` |
| 3 | `joint_psrl` | Bayesian baseline | joint | Joint posterior PSRL comparison for posterior decoupling | `llm_hpgg/coordinator.py` |
| 4 | `map_greedy` | Bayesian baseline | factored MAP | Greedy MAP-type baseline | `llm_hpgg/coordinator.py` |
| 5 | `psrl_notype` | Type-agnostic baseline | no | Samples type profiles uniformly and never updates type belief | `llm_hpgg/coordinator.py` |
| 6 | `iql_independent_actions` | MARL baseline | no | Canonical independent-action IQL: each player learns Q over its own contribution actions | `llm_hpgg/run_experiment.py` |
| 7 | `iql` / `joint_profile_iql` | MARL ablation | no | Joint-profile Q baseline retained for comparison with earlier runs | `llm_hpgg/run_experiment.py` |
| 8 | `random` | Sanity baseline | no | Uniform random action profile | `llm_hpgg/coordinator.py` |
| 9 | `oracle` | Upper bound | true type known | Knows the true hidden type profile | `llm_hpgg/coordinator.py` |
| 10 | `llm_greedy` | LLM-based baseline | implicit | Prompted LLM directly chooses a joint contribution profile from public history | `llm_hpgg/run_llm_baselines.py` |
| 11 | `llm_belief` | LLM-based belief baseline | implicit / prompted | Prompted LLM infers likely personas from history before choosing action | `llm_hpgg/run_llm_baselines.py` |

The two LLM-based baselines are lightweight executable analogues of belief / theory-of-mind style LLM coordination methods. They are not full ECON or A-ToM reproductions, but they directly test a reviewer-relevant alternative: whether a prompted LLM coordinator can replace the closed-form Bayesian posterior. A web-backed implementation audit is saved at `analysis/baseline_implementation_audit.md`.

The primary IQL baseline is now `iql_independent_actions`, which is the canonical per-agent action-level variant. The older `iql` implementation is retained as a joint-profile Q ablation for continuity with previous runs.

## 31. Updated HP-SPGG experiment commands

### 31.1 Main nine-method tabular suite

```powershell
uv run python run_experiment.py `
    --K 20 `
    --n 3 `
    --seeds 5 `
    --beta 1.0 `
    --algos hpsmg_plus hpsmg joint_psrl map_greedy psrl_notype iql_independent_actions iql random oracle `
    --calibration calibration_<backend_or_model>.npy `
    --out results/<backend>/E2_9algos_<tag>.npz
```

This command is now also used inside `scripts/run_cloudgpt_multi_model_live.ps1`, which runs the full nine-method suite for every beta in the sweep.

### 31.2 LLM-based coordinator baselines

```powershell
$env:LLM_HPGG_BACKEND = "cloudgpt"
$env:CLOUDGPT_USE_AZURE_CLI = "1"
$env:CLOUDGPT_TIMEOUT = "60"

uv run python -m llm_hpgg.run_llm_baselines `
    --K 20 `
    --n 3 `
    --seeds 3 `
    --algos llm_greedy llm_belief `
    --calibration calibration_cloudgpt_multi_model_fast4_8algos_DeepSeek_V3_2_c19.npy `
    --out results/cloudgpt/E2_llm_baselines_DeepSeek_V3_2_c19_K20_s3.npz `
    --trace-out analysis/E2_llm_baselines_DeepSeek_V3_2_c19_K20_s3_trace.json `
    --cache logs/llm_baseline_cache_DeepSeek_V3_2.json `
    --model DeepSeek-V3.2
```

The LLM-baseline runner caches LLM coordinator replies, so larger follow-up runs can reuse previous calls.

## 32. Completed LLM-based baseline result

Calibration: `calibration_cloudgpt_multi_model_fast4_8algos_DeepSeek_V3_2_c19.npy`

Coordinator model: `DeepSeek-V3.2` through CloudGPT

Setting: `K=20`, `seeds=3`

Output: `results/cloudgpt/E2_llm_baselines_DeepSeek_V3_2_c19_K20_s3.npz`

Trace: `analysis/E2_llm_baselines_DeepSeek_V3_2_c19_K20_s3_trace.json`

Cache: `logs/llm_baseline_cache_DeepSeek_V3_2.json`

| Method | Final cumulative regret mean |
|---|---:|
| `llm_greedy` | 10.000 |
| `llm_belief` | 4.357 |

Same-setting tabular comparison, using `K=20`, `seeds=3`, `beta=1.0`:

| Method | Final cumulative regret mean |
|---|---:|
| `oracle` | 0.000 |
| `joint_psrl` | 0.860 |
| `hpsmg` | 0.877 |
| `hpsmg_plus` | 0.883 |
| `map_greedy` | 0.943 |
| `llm_belief` | 4.357 |
| `llm_greedy` | 10.000 |
| `psrl_notype` | 14.100 |
| `iql` | 29.267 |
| `random` | 30.580 |

Interpretation: the LLM belief baseline is meaningfully better than type-agnostic baselines, but still substantially worse than the closed-form Bayesian type-aware methods. This supports the paper's distinction from LLM belief / ToM-style coordination methods: prompting an LLM to reason about hidden personas helps, but explicit posterior structure helps more.

## 33. Updated paper-facing master table

For the HP-SPGG main table, include all methods below when space permits:

| Cluster | Methods |
|---|---|
| Oracle upper bound | `oracle` |
| Type-aware Bayesian methods | `hpsmg_plus`, `hpsmg`, `joint_psrl`, `map_greedy` |
| LLM-based coordinator methods | `llm_belief`, `llm_greedy` |
| Type-agnostic baselines | `psrl_notype`, `iql`, `random` |

If the main paper table is too wide, report the full eleven-method table in the appendix and keep the main table to: `oracle`, `hpsmg_plus`, `hpsmg`, `joint_psrl`, `llm_belief`, `psrl_notype`, `iql_independent_actions`, `random`.

## 34. Updated reviewer-facing claim

The expanded baseline suite supports two separate empirical claims:

1. Type-aware Bayesian methods outperform type-agnostic baselines (`psrl_notype`, `iql`, `random`) by a large margin.
2. The closed-form Bayesian posterior outperforms prompted LLM belief / ToM-style coordination (`llm_belief`, `llm_greedy`) on the same HP-SPGG calibration.

This directly addresses the reviewer question: "Why not just ask an LLM coordinator to infer the hidden types?" The answer from the current run is that LLM belief prompting helps, but remains worse than explicit Bayesian posterior updates.

## 35. Full external LLM-baseline implementations

The current `llm_greedy` and `llm_belief` baselines are useful lightweight prompted baselines. Full HP-SPGG adapters for A-ToM and ECON are now implemented separately in `llm_hpgg/run_external_llm_baselines.py`:

| Target baseline | Reference implementation | HP-SPGG adapter requirement | Status |
|---|---|---|---|
| A-ToM | `ChunjiangMonkey/Adaptive-ToM` | Implements 0/1/2-order ToM and adaptive ToM action prediction over HP-SPGG public reward/action history; maps predicted partner actions to HP-SPGG contribution profiles; runs the same K/seeds/evaluation loop. | Implemented |
| ECON | `tmlr-group/ECON` | Implements ECON-style coordinator strategy, executor roles, BNE-style refinement rounds, convergence check, and final joint contribution commitment. | Implemented |

The completed strictness upgrades are:

1. `joint_psrl` now maintains an explicit joint posterior table.
2. `iql_independent_actions` now provides the canonical independent-action IQL baseline.
3. The older `iql` remains only as a joint-profile Q-learning ablation.

In the paper, `llm_belief` should remain labeled as a lightweight prompted baseline. The full external-family comparisons should use the new `atom_*` and `econ_bne` adapters.

### 35.1 External LLM baseline command

```powershell
$env:LLM_HPGG_BACKEND = "cloudgpt"
$env:CLOUDGPT_USE_AZURE_CLI = "1"
$env:CLOUDGPT_TIMEOUT = "60"

uv run python -m llm_hpgg.run_external_llm_baselines `
    --K 20 `
    --n 3 `
    --seeds 3 `
    --algos atom_tom0 atom_tom1 atom_tom2 atom_adaptive_ftl atom_adaptive_hedge econ_bne `
    --calibration calibration_cloudgpt_multi_model_fast4_8algos_DeepSeek_V3_2_c19.npy `
    --out results/cloudgpt/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s3.npz `
    --trace-out analysis/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s3_trace.json `
    --cache logs/external_llm_baseline_cache_DeepSeek_V3_2.json `
    --model DeepSeek-V3.2 `
    --econ-rounds 3
```

For smoke testing without LLM calls, add `--offline`. The offline smoke test has been validated with `K=2`, `seeds=1` over all six external algorithms.

## 36. LLM-based external comparisons and baselines

The external environment scope should stay focused on Concordia and SOTOPIA. Additional baselines should be LLM-based methods that actually solve social coordination, hidden-belief reasoning, public-goods cooperation, or repeated-agent decision-making. Generic orchestration frameworks such as AutoGen, CAMEL, AgentVerse, MetaGPT, and Microsoft Agent Framework are not baselines; they are infrastructure.

| Class | Candidate method | Paper / code status | HP-SPGG relevance | Suggested action |
|---|---|---|---|---|
| ToM-based LLM coordination | A-ToM: "Adaptive Theory of Mind for LLM-based Multi-Agent Coordination" | arXiv:2603.16264 / AAAI 2026; `ChunjiangMonkey/Adaptive-ToM` | Directly models partner reasoning depth and action prediction in repeated coordination tasks | Already implemented as the `atom_*` family; keep as a primary LLM-based baseline |
| Equilibrium/belief LLM coordination | ECON: "From Debate to Equilibrium: Belief-Driven Multi-Agent LLM Reasoning via Bayesian Nash Equilibrium" | arXiv:2506.08292 / ICML 2025; `tmlr-group/ECON` | Treats multi-LLM coordination as an incomplete-information game and computes BNE-style commitments | Already implemented as `econ_bne`; keep as a primary LLM-based baseline |
| Public-goods LLM incentive method | MAC-SPGG: "Everyone Contributes! Incentivizing Strategic Cooperation in Multi-LLM Systems via Sequential Public Goods Games" | arXiv:2508.02076; no public GitHub found in checked pages | Very close sequential public-goods/free-riding framing | Add as related work now; optionally implement a paper-inspired incentive/reward variant, clearly labeled as not official code |
| Public-goods LLM behavioral protocol | "Corrupted by Reasoning: Reasoning Language Models Become Free-Riders in Public Goods Games" | COLM 2025 OpenReview; supplementary material found, no GitHub found in checked page | Directly studies LLM cooperation/free-riding in repeated public-goods games with institutional choice and sanctioning | Use for related work and optional behavioral-prompt ablations; not a coordinator algorithm |
| Generic LLM-agent verbal learning | Reflexion | NeurIPS 2023; `noahshinn/reflexion` | Learns from scalar/free-form feedback through verbal reflection memory across trials | Optional weak baseline for repeated HP-SPGG/Concordia/SOTOPIA episodes |
| Generic LLM reason-act policy | ReAct | ICLR 2023; `ysymyth/ReAct` | Interleaves reasoning and environment actions, useful as a generic LLM-agent control baseline | Optional weak baseline for Concordia/SOTOPIA; not a hidden-type method |

Traditional MARL methods such as LOLA, QMIX, VDN, MADDPG, and PyMARL should not be the next baseline direction because they are not LLM-based. They can stay in background related work if needed, but the main comparison should use `llm_greedy`, `llm_belief`, A-ToM, ECON, and possibly MAC-SPGG-inspired / Reflexion-style LLM variants.

A fuller LLM-focused candidate table is saved at `analysis/related_work_candidate_baselines.md`. The recommended order is: run the existing full A-ToM/ECON adapters; keep Concordia and SOTOPIA as the external benchmarks; then add only LLM-based optional variants if needed.
