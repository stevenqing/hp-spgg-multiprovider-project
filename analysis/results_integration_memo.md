# HP-SPGG Results Integration Memo

Date: 2026-05-17

Subject: Assessment of the current multi-baseline results and recommended paper-integration actions.

## Summary

The current DeepSeek-V3.2 `c19` result set is paper-worthy. The strongest headline is that `hpsmg_plus` reaches cumulative regret `0.400` at `K=20`, while the strongest external LLM coordination baseline, `atom_adaptive_hedge`, reaches `3.7833`, and the ECON-style baseline reaches `3.9800`. This gives an approximately 9.5x to 10x separation against the strongest LLM coordination baselines we have run so far.

The current result hierarchy is:

| Cluster | Method | Final cumulative regret at K=20 | Comment |
| --- | --- | ---: | --- |
| Upper bound | `oracle` | 0.0000 | True-type access |
| Bayesian/type-aware | `hpsmg_plus` | 0.4000 | Headline proposed method |
| Bayesian/type-aware | `map_greedy` | 0.7120 | Strong on informative HP-SPGG cells |
| Bayesian/type-aware | `hpsmg` | 0.8280 | Proposed ablation |
| Bayesian/type-aware | `joint_psrl` | 0.8320 | Explicit joint posterior baseline |
| External LLM coordination | `atom_adaptive_hedge` | 3.7833 | Strongest external LLM baseline |
| External LLM coordination | `econ_bne` | 3.9800 | ECON-style BNE coordinator |
| Prompted LLM coordination | `llm_belief` | 4.3567 | Best lightweight prompted baseline |
| External LLM coordination | `atom_tom0` | 10.0000 | Simple ToM baseline |
| Type-agnostic | `psrl_notype` | 13.9120 | No type posterior update |
| Type-agnostic | `random` | 28.2660 | Random action profile |
| Type-agnostic | `iql` | 28.3420 | Joint-profile Q-learning ablation |

## Why The Result Is Strong

1. The gap against the strongest external LLM baseline is large. `hpsmg_plus` has about 9.5x lower cumulative regret than `atom_adaptive_hedge`, which makes the result hard to explain away as tuning noise.

2. The ECON-style comparison is important. `econ_bne` is the closest conceptual competitor among LLM-coordination baselines because it uses belief-style reasoning and a coordinator/executor refinement loop. `hpsmg_plus` is about 10x lower regret on the current HP-SPGG setting.

3. The type-aware versus type-agnostic split is very clear. The Bayesian/type-aware cluster stays under cumulative regret `0.85`, while `psrl_notype`, `random`, and `iql` are much worse. This supports the paper's rate-separation story.

4. The beta sweep is stable. `hpsmg_plus` remains at `0.400` for beta values from `0.0` through `0.75`, so the headline does not depend on a fragile hyperparameter choice.

5. Cross-provider sanity checks already point in the same broad direction: type-aware methods remain low-regret across Anthropic, CloudGPT, Google, OpenAI, and Qwen3 calibrations.

## Issues To Address Before Submission

### Issue 1: Seed-count mismatch

Native HP-SPGG runs currently use `seeds=5`, while external A-ToM/ECON and prompted LLM baselines use `seeds=3`.

Recommended fix: rerun the most important external baselines at `seeds=5`, at least `atom_adaptive_hedge` and `econ_bne`. If time or budget is tight, report a 3-seed native subset in the headline table and keep 5-seed native results as a robustness appendix.

### Issue 2: Joint-PSRL and H-PSMG variance mismatch

`hpsmg` and `joint_psrl` have nearly identical means (`0.8280` versus `0.8320`) but different standard deviations. This suggests the implementations are statistically aligned but not coupled with identical random streams.

Recommended framing for now: claim statistical equivalence in the empirical section, not bit-identical trajectory equality. RNG coupling can be added later as camera-ready polish.

### Issue 3: MAP-Type-Greedy is strong on c19

`map_greedy` beats `hpsmg` and `joint_psrl` on c19 and is close to `hpsmg_plus`. This is not a problem: HP-SPGG c19 appears highly informative, so point-estimate MAP methods can converge quickly. The paper should not claim H-PSMG always beats MAP on HP-SPGG.

Recommended framing: on informative HP-SPGG cells, type-aware methods cluster tightly; MAP-vs-Bayesian separation should be demonstrated on deeper-trap or low-information HT-MG settings.

### Issue 4: H-PSMG+ standard deviation

`hpsmg_plus` has mean `0.4000` and standard deviation `0.8000`. This is plausible near the oracle floor but should be made reviewer-friendly.

Recommended fix: add median/IQR and bootstrap confidence intervals for the headline table. Native methods are cheap, so additional native seeds can also tighten SEM.

### Issue 5: Phase 2 scored results are not complete

Concordia and SOTOPIA adapters are installed and smoke-tested, but not yet scored as formal benchmark results.

Recommended prioritization: run live CloudGPT Concordia first, especially `pub_coordination` and a collective-action/labor-style task if available. Concordia has cleaner analytic rewards than SOTOPIA-Hard, which likely requires judge scoring.

### Issue 6: Regret curves are missing

Tables are strong, but a regret-curve figure will be more persuasive.

Recommended plots:

- Main comparison: `oracle`, `hpsmg_plus`, `atom_adaptive_hedge`, `econ_bne`, `llm_belief`, `random`.
- Native cluster: `oracle`, `hpsmg_plus`, `hpsmg`, `joint_psrl`, `map_greedy`, `psrl_notype`, `iql`, `random`.

## Recommended Action Sequence

1. Generate paper-ready combined table and regret curves from existing results. This is no-cost and should be done first.
2. Rerun the critical external baselines at `seeds=5`, focusing on `atom_adaptive_hedge` and `econ_bne` first.
3. Add median/IQR and bootstrap confidence intervals to the headline summary.
4. Run live CloudGPT Concordia `pub_coordination`; then add one collective-action task if the installed Concordia examples support it cleanly.
5. Update the paper's empirical section with the current numbers and caveats.
6. Defer full SOTOPIA-Hard scoring unless the Concordia tier is already complete.
7. Optionally implement RNG coupling between H-PSMG and Joint-PSRL as camera-ready polish.

## Paper Claim Draft

On the HP-SPGG benchmark, `hpsmg_plus` achieves cumulative Bayesian regret of `0.400` at `K=20` across heterogeneous LLM personas, about 9.5x lower than the strongest external LLM-coordination baseline we have run so far (`atom_adaptive_hedge`) and about 10x lower than the ECON-style BNE coordinator, while preserving the predicted separation between type-aware and type-agnostic methods.

## Missing Item

The user-mentioned `section_9_7_draft.tex` is not currently present in the workspace. It should be added or generated before paper integration.