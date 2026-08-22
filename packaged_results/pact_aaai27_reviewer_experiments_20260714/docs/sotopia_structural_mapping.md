# SOTOPIA-Hard Structural Mapping Audit

Audit date: 2026-07-13; implementation-path recheck: 2026-07-14

## Bottom line

The SOTOPIA-Hard evaluation is a useful transfer experiment, but it is not an exact or near-exact instantiation of the HT-MG-BC model. It falls outside the theorem on several axes simultaneously:

- curated dyadic case pairs do not expose a factored generative persona prior;
- actions are open-ended natural-language utterances;
- reward is produced by an LLM evaluator that sees both agents' goals and the joint transcript;
- action likelihoods are not known or estimated from next-token probabilities;
- the project's four-type posterior is a hand-built keyword surrogate, not a calibrated posterior over native SOTOPIA personas;
- no finite CCE planner or exact joint-action oracle is available;
- the type-identifiability condition is not tested.

The three families highlighted in the main figure are best described as **exploratory private-goal families**, not as families proven to satisfy TI+RL+PF. The remaining eight families are the aggregate remainder, not a code-derived set of PF violations.

## Case construction

[official_hard_data.py](../llm_hpgg_sotopia/official_hard_data.py) reconstructs 70 curated benchmark combinations from public episode logs. Each case contains:

- one environment/scenario identifier;
- exactly two fixed agent IDs;
- two fixed background/profile strings;
- two fixed social goals.

The loader does not sample two personas independently from a product prior. It reads the pair selected by the benchmark combination. `make_environment_profile()` also sets the relationship to `stranger`, while preserving the paired goals.

Consequences:

- there is no substrate-level `P_0(theta_1, theta_2)` object whose factorisation is checked;
- dependence or independence of the empirical pair distribution is not estimated;
- initializing two algorithmic surrogate marginals independently does not establish PF for the benchmark data-generating process.

## Agent information and action generation

[agents.py](../llm_hpgg_sotopia/agents.py) gives each acting agent:

- its own private goal;
- its reconstructed private profile, including personality/values and secret;
- the public observation and dialogue history;
- for selected baselines, a four-class posterior over the opponent surrogate persona.

The action is an LLM-generated `AgentAction` with an open-ended text argument. Both participants run the same baseline in self-play.

The private profile and goal therefore affect the agent's action policy. This does not by itself prove a TI violation: if the complete utterance is included in the joint action, appending it to the transcript can remain type-independent. However, the project does not identify or test a finite transition kernel `P(s' | s, a)`, so exact TI should not be claimed.

## The surrogate posterior is not next-token Bayes

For `hpsmg` and `hpsmg_plus`, the intended implementation starts from a uniform distribution over the four HP-SPGG persona labels and updates log scores using `_persona_log_likelihood_increment()`.

That function counts hand-selected words and phrases associated with cooperation, conditionality, risk aversion, and selfishness. The increments are added to the log scores and softmax-normalized. It does not call the backbone for persona-conditioned next-token probabilities, and it is not calibrated against the native SOTOPIA profile distribution.

The 2026-07-14 execution audit found an additional implementation issue in the runs underlying the retained headline figures. The adapter attempted to read partner messages from the agent inbox, but SOTOPIA 0.1.5 supplies the previous action through `Observation.last_turn`; profile construction also replaces the slot name (`agent_1`) with the character name. As a result, the historical path recorded zero numeric-posterior updates and the table remained uniform. The E-R3 reviewer experiment corrects this by storing the slot ID, parsing the partner action from `Observation.last_turn`, and recording update/corruption counts per episode. Its corrected reruns must be distinguished from the retained pre-fix figure data.

Therefore:

- the corrected E-R3 update is a recurrent numeric heuristic and may be described as a pseudo-Bayesian surrogate;
- it should not be described as the closed-form next-token Bayes update used by PACT on HP-SPGG;
- the retained plotted dialogue trajectories cannot establish that recurrent numeric updating caused late-turn improvement because their historical update count was zero;
- only reruns with nonzero audited update counts may support a menu-corruption sensitivity statement, and even those do not establish native projection accuracy.

## Oracle semantics

`oracle_one_hot_from_profile()` does not recover a native ground-truth SOTOPIA persona label. It applies the same keyword heuristic to the opponent's full reconstructed profile and converts the highest-scoring surrogate class into a one-hot vector.

Thus:

- `oracle_joint` / `oracle_belief` are privileged **profile-derived surrogate-type** references;
- they are not exact ground-truth type oracles;
- `oracle_policy` additionally runs multiple stochastic episodes and retains the one with the highest score from the same LLM evaluator;
- best-of-5 is a sample-based reference, not a strict global policy upper bound over the open-ended action space.

## Reward construction and reward locality

[run_sotopia_hard_official.py](../llm_hpgg_sotopia/run_sotopia_hard_official.py) evaluates the transcript with an LLM judge. The evaluator prompt contains:

- the scenario;
- both agent names;
- both private social goals;
- the complete dialogue history;
- seven SOTOPIA dimensions.

The judge then returns per-agent believability, relationship, knowledge, secret, social-rules, financial/material-benefit, and goal scores.

This reward is:

- unknown and non-analytic;
- judge-dependent;
- not guaranteed to be local in an agent's own latent type;
- potentially directly dependent on the partner's goal even when the transcript is held fixed.

Accordingly, RL is unverified and can fail under the paper's mapping. The reward should not be represented as `r_i(s,a,theta_i)` without qualification.

## Assumption map

| Condition | Status in the implemented SOTOPIA evaluation | Reason |
|---|---|---|
| Number of agents | Outside scaling regime | Dyadic self-play (`n=2`). |
| Finite/tabular action space | Fails | Action arguments are open-ended text. |
| TI | Plausible only under full joint-utterance conditioning; not verified | Hidden profile/goal changes action policy, while transcript evolution may be action-conditioned. No finite kernel is identified or tested. |
| RL | Unverified and potentially violated | The LLM evaluator sees both goals and joint history when assigning each agent's score. |
| PF | Not established | Cases are curated profile/goal pairs; no product prior is sampled or tested. |
| Known reward model | Fails | Reward is an LLM-as-judge output. |
| Known action likelihood | Fails | Surrogate updates use keyword increments, not a known likelihood or next-token probability. |
| TID | Not tested | No likelihood-separation or posterior-calibration audit over native profiles. |
| CCE/CSR | Not instantiated | Agents independently generate utterances; no finite centralized CCE oracle/tie-break. |
| Exact PACT posterior | Not instantiated | The four-class posterior is a heuristic projection of native profiles and utterances. |

## The three highlighted families

The plotting code explicitly lists:

- `craigslist_bargains`;
- `revenge_plot`;
- `donate_funds`.

There is no implementation-level predicate that tests TI, RL, or PF and assigns these three families to an in-scope class. They are plausible private-goal examples and have favorable aggregate PACT results, but the exact `3/8` structural split is not derived from the runner.

The retained all-70 report further shows that PACT's mean margin against the per-cell best alternative is negative for every family when margins are computed cell by cell. The three selected families can still show a positive difference after first averaging each baseline across backbones/family instances, but this is an aggregation choice, not proof of structural precondition satisfaction.

Defensible wording:

- “three exploratory private-goal families selected for detailed analysis”;
- “the remaining eight families are reported in aggregate”;
- “the subgroup pattern is consistent with a private-goal hypothesis, but does not identify PF or RL.”

Wording to avoid:

- “the three families satisfy the theoretical preconditions”;
- “the remaining eight violate PF”;
- “SOTOPIA stresses only PF”;
- “PACT performs exact Bayes updates on every utterance”;
- “oracle belief has the ground-truth opponent persona”;
- “oracle policy is a strict upper bound.”

## Interpretation of the retained results

The aggregate all-70 result is the most defensible headline:

- no method dominates;
- the best baseline rotates by backbone;
- PACT remains competitive but does not lead on average;
- the profile-derived one-hot reference provides little benefit;
- best-of-5 judge selection provides much larger gains, showing that open-action search and evaluator variance dominate the retained surrogate-belief effect.

The selected-family and trajectory figures are exploratory diagnostics. The historical trajectory figure additionally predates the `Observation.last_turn` update-path fix and cannot be interpreted as evidence for recurrent posterior revision. It should not be used as a theorem-precondition or mechanism validation; the corrected E-R3 rerun is the relevant sensitivity evidence.

## Experiments needed for a stronger structural claim

1. Define native latent variables from SOTOPIA profiles/goals before observing outcomes.
2. Estimate the empirical joint pair distribution and test whether it factorizes.
3. Hold transcript fixed and counterfactually vary the partner goal/profile in the evaluator prompt to test RL.
4. Hold the full joint utterance fixed and vary profiles to test whether environment transitions/termination satisfy TI.
5. Replace keyword increments with explicit persona-conditioned next-token likelihoods or report posterior calibration.
6. Pre-register family classifications using measurable structural criteria rather than result margins.
7. Export per-seed/per-case results for paired significance tests.
8. Treat best-of-K judge selection as a search reference, not a strict oracle.
