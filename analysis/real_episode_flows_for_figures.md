# Real Episode Flows for Figure Material

This note extracts three real runs from the project data and formats them as
step-by-step material for drawing explanatory figures. The goal is to show how
PACT/PACT+ behaves differently from PSRL-style, ECON, A-ToM, and prompted LLM
baselines on concrete episodes/cases that were actually run.

Metrics follow the original result files:

- HP-SPGG: cumulative regret, lower is better.
- Concordia: focal score and coordination rate, higher is better.
- SOTOPIA: evaluator overall score, higher is better.

## What Is Saved: Prompts, Replies, Dialogues, and Actions

This is important for figure drawing. The three benchmark result files do not
all preserve the same level of raw interaction detail.

| benchmark | raw action-selection prompt saved? | model reply saved? | dialogue/action trace saved? | score/reasoning saved? | figure-safe use |
|---|---|---|---|---|---|
| HP-SPGG native `hpsmg_plus` / `joint_psrl` | No. Native NPZ stores arrays, not prompts. | Not applicable for native methods. | Per-round regret and welfare are saved; native joint contribution actions are not saved in the archived NPZ. | Welfare/regret arrays are saved. | Draw cumulative-regret and welfare trajectories. Do not claim a per-round native prompt transcript exists. |
| HP-SPGG prompted LLM baselines `llm_greedy` / `llm_belief` | No full prompt payload in the trace. | Yes, `reply` is saved. | Yes, per-round contributions, rewards, welfare, oracle welfare, parsed reason, and inferred personas are saved. | Parsed reason and inferred personas are saved. | Draw action/reason examples for prompted LLM baselines, but cite prompts from template/code rather than per-call logs. |
| HP-SPGG external baselines `econ_bne` / `atom_*` | No full prompt payload in the trace. | Partially: traces save structured `info`, parsed decisions, and reasons, but not always raw LLM prompt text. | Yes, per-round contributions, rewards, welfare, oracle welfare, and method-specific info are saved. | Method-specific reasoning/parsed choices are saved. | Draw baseline process flows and decisions; avoid saying the exact raw prompt was archived. |
| Concordia compact | No. These compact mechanistic runs store structured mechanism outputs, not raw LLM prompts. | Not applicable / not stored as chat replies. | Yes, per-episode venue actions, ECON iterations, A-ToM predicted choices, PACT+ policy info, and scores are saved. | Scores and method info are saved. | Draw mechanism flow: A-ToM split, ECON iteration, PACT+ joint choice. |
| SOTOPIA | No full action-selection prompt payload in the all70 JSON. | The generated dialogue actions are saved as transcript turns. Evaluator reasoning is saved in `scores`. | Yes, full six-turn dialogue transcript is saved for each episode. | Yes, evaluator dimension scores and reasoning are saved. | Draw dialogue timeline and quote the transcript/actions directly. Do not claim the full prompt payload was archived. |

Short version: the real **dialogues/actions/results** are saved for Concordia and
SOTOPIA, and HP-SPGG has saved trajectories plus LLM baseline replies. The exact
per-call raw prompts are generally **not** archived in these result files; prompt
templates live in the paper appendix and source code.

Relevant prompt template file:

- `arr_paper/prompt_templates.tex`

Relevant trace/result files:

- `analysis/E2_llm_baselines_DeepSeek_V3_2_c19_K20_s5_trace.json`
- `analysis/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5_trace.json`
- `analysis/concordia_pub_coordination_compact_capetown_mechanistic_joint_s30.json`
- `analysis/sotopia_hard_official_gpt_5_4_nano_20260317_hpsmg_plus_sotopia_tuned_all70.json`

## Example 1: HP-SPGG, DeepSeek-V3.2, c19, K=20

### Source

- Summary: `analysis/E2_native_vs_llm_baselines_stats.md`
- Proposed/native NPZ: `_archive/results/cloudgpt/E2_DeepSeek_V3_2_c19_beta0p25.npz`
- ECON/A-ToM NPZ: `_archive/results/cloudgpt/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz`
- Prompted LLM NPZ: `_archive/results/cloudgpt/E2_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz`

### Episode Choice

- Model: `DeepSeek-V3.2`
- Hidden-type setting: `c19`
- Horizon: `K=20`
- Shown seed index: `2`
- Why this seed: PACT+ stays at zero cumulative regret while PSRL-style,
  ECON, A-ToM, and prompted LLM alternatives accumulate regret.

The archived native NPZ stores per-round regret and welfare but not the native
joint contribution actions. Therefore this flow uses the real saved metric
trajectory. External LLM trace files do contain contribution text for some
baselines, but the clean cross-method comparison here is cumulative regret.

### Aggregate Result

| method | final cumulative regret mean | welfare mean |
|---|---:|---:|
| `hpsmg_plus` | **0.400** | 2.760 |
| `joint_psrl` | 0.832 | 2.838 |
| `llm_belief` | 3.074 | 2.736 |
| `econ_bne` | 3.990 | 2.611 |
| `atom_tom1` | 16.676 | 2.018 |
| `psrl_notype` | 13.912 | 2.174 |

### Step-by-Step Episode Trace

| round | PACT+ regret | joint PSRL regret | no-type PSRL regret | ECON regret | A-ToM regret | LLM-belief regret | PACT+ welfare |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.00 | 0.10 | 1.48 | 0.50 | 1.35 | 0.00 | 2.60 |
| 1 | 0.00 | 0.70 | 1.58 | 1.00 | 1.65 | 0.74 | 2.60 |
| 2 | 0.00 | 0.78 | 2.53 | 1.50 | 1.95 | 1.54 | 2.60 |
| 3 | 0.00 | 0.78 | 4.13 | 2.00 | 2.80 | 1.54 | 2.60 |
| 4 | 0.00 | 0.78 | 4.18 | 2.50 | 3.65 | 2.28 | 2.60 |
| 5 | 0.00 | 0.78 | 5.78 | 3.00 | 4.50 | 2.28 | 2.60 |
| 6 | 0.00 | 0.78 | 7.38 | 3.50 | 5.35 | 2.28 | 2.60 |
| 7 | 0.00 | 0.78 | 8.98 | 4.00 | 6.20 | 2.28 | 2.60 |
| 8 | 0.00 | 0.78 | 10.58 | 4.50 | 7.05 | 2.28 | 2.60 |
| 9 | 0.00 | 0.78 | 10.68 | 5.00 | 7.90 | 3.02 | 2.60 |
| 10 | 0.00 | 0.78 | 11.38 | 5.50 | 8.75 | 3.02 | 2.60 |
| 11 | 0.00 | 0.78 | 12.06 | 6.00 | 9.60 | 3.76 | 2.60 |
| 12 | 0.00 | 0.78 | 13.66 | 6.50 | 10.45 | 3.76 | 2.60 |
| 13 | 0.00 | 0.78 | 15.26 | 7.00 | 11.30 | 3.76 | 2.60 |
| 14 | 0.00 | 0.78 | 15.36 | 7.50 | 12.15 | 4.50 | 2.60 |
| 15 | 0.00 | 0.78 | 16.96 | 8.00 | 13.00 | 4.50 | 2.60 |
| 16 | 0.00 | 0.78 | 18.56 | 8.50 | 13.85 | 4.50 | 2.60 |
| 17 | 0.00 | 0.78 | 20.16 | 9.00 | 14.70 | 4.50 | 2.60 |
| 18 | 0.00 | 0.78 | 21.76 | 9.50 | 15.55 | 5.24 | 2.60 |
| 19 | 0.00 | 0.78 | 23.36 | 10.00 | 16.40 | 5.24 | 2.60 |

### Figure Message

Draw this as six cumulative-regret curves. PACT+ is the flat line at zero;
joint PSRL has a small early mistake and then plateaus; ECON, A-ToM, and
no-type PSRL keep accumulating regret. The visual point is that PACT+ preserves
and uses the hidden-type posterior, rather than sampling one model, relying on
fixed equilibrium refinement, or doing shallow ToM reasoning.

## Example 2: Concordia Pub Coordination, Capetown, Seed 0

### Source

- Summary: `analysis/concordia_pub_coordination_compact_capetown_mechanistic_joint_s30.md`
- Full JSON: `analysis/concordia_pub_coordination_compact_capetown_mechanistic_joint_s30.json`

### Episode Setup

- Config: `capetown`
- Seed: `0`
- Venues:
  - `The Lion's Den`
  - `The Kirstenbosch Kraal`
  - `The Springbok's Lair`
- Focal players:
  - Unathi van der Merwe
  - Bonga Sithole
  - Phindile Jansen
  - Siyabonga Khumalo
  - Zinhle Ngubane
  - Amahle Nkosi

### Aggregate Result Across 30 Episodes

| method | focal score mean | focal min mean | coordination rate | valid action rate |
|---|---:|---:|---:|---:|
| `hpsmg_plus_joint_proxy` | **1.2472** | **0.9833** | **1.0000** | 1.0000 |
| `econ_bne_mech` | 1.0439 | 0.7511 | 0.7278 | 1.0000 |
| `atom_tom1_mech` | 0.9650 | 0.5811 | 0.6500 | 1.0000 |
| `oracle_joint` | 1.2759 | 0.9833 | 0.9944 | 1.0000 |

### Step-by-Step Episode Flow

#### Step 1: A-ToM First-Order Prediction

A-ToM makes individual selections after predicting where other players will go.
In seed 0, this creates a split between two venues.

| player | selected venue |
|---|---|
| Unathi van der Merwe | The Lion's Den |
| Bonga Sithole | The Springbok's Lair |
| Phindile Jansen | The Lion's Den |
| Siyabonga Khumalo | The Springbok's Lair |
| Zinhle Ngubane | The Lion's Den |
| Amahle Nkosi | The Lion's Den |
| Sizwe Dlamini | The Lion's Den |
| Kagiso Khoza | The Lion's Den |

Outcome:

| method | focal score mean | focal score min | coordination rate |
|---|---:|---:|---:|
| `atom_tom1_mech` | 0.9167 | 0.0000 | 0.6667 |

Interpretation for figure: first-order ToM reasons locally about others, but
the final joint action fragments the group.

#### Step 2: ECON Iterated Best Response

ECON-style refinement alternates commitments across iterations.

| iteration | commitment summary |
|---:|---|
| 0 | Bonga and Siyabonga choose `The Springbok's Lair`; the rest choose `The Lion's Den`. |
| 1 | Everyone except Kagiso chooses `The Lion's Den`; Kagiso chooses `The Springbok's Lair`. |
| 2 | Bonga and Siyabonga choose `The Springbok's Lair`; the rest choose `The Lion's Den`. |
| 3 | Everyone except Kagiso chooses `The Lion's Den`; Kagiso chooses `The Springbok's Lair`. |
| 4 | Bonga and Siyabonga choose `The Springbok's Lair`; the rest choose `The Lion's Den`. |
| 5 | Everyone except Kagiso chooses `The Lion's Den`; Kagiso chooses `The Springbok's Lair`. |

Final ECON action:

| player | selected venue |
|---|---|
| Unathi van der Merwe | The Lion's Den |
| Bonga Sithole | The Lion's Den |
| Phindile Jansen | The Lion's Den |
| Siyabonga Khumalo | The Lion's Den |
| Zinhle Ngubane | The Lion's Den |
| Amahle Nkosi | The Lion's Den |
| Sizwe Dlamini | The Lion's Den |
| Kagiso Khoza | The Springbok's Lair |

Outcome:

| method | focal score mean | focal score min | coordination rate |
|---|---:|---:|---:|
| `econ_bne_mech` | 0.9861 | 0.5000 | 1.0000 |

Interpretation for figure: the equilibrium-style process improves coordination
over A-ToM, but the final commitment still leaves one participant away from the
main group and gives a lower focal score.

#### Step 3: PACT+ Posterior-Guided Joint Social Objective

PACT+ selects the joint action under a posterior-guided social objective. It
chooses the same venue for every participant.

| player | selected venue | score |
|---|---|---:|
| Unathi van der Merwe | The Lion's Den | 1.0000 |
| Bonga Sithole | The Lion's Den | 1.5000 |
| Phindile Jansen | The Lion's Den | 1.5000 |
| Siyabonga Khumalo | The Lion's Den | 1.0000 |
| Zinhle Ngubane | The Lion's Den | 1.5000 |
| Amahle Nkosi | The Lion's Den | 1.5000 |
| Sizwe Dlamini | The Lion's Den | 1.5000 |
| Kagiso Khoza | The Lion's Den | 1.0000 |

Outcome:

| method | focal score mean | focal score min | coordination rate | policy value |
|---|---:|---:|---:|---:|
| `hpsmg_plus_joint_proxy` | **1.3333** | **1.0000** | **1.0000** | 1.69375 |

Interpretation for figure: PACT+ acts at the joint decision level and optimizes
against the maintained belief over social preferences. In this episode it
matches the oracle joint action and avoids both A-ToM fragmentation and ECON's
lower-value commitment.

## Example 3: SOTOPIA-Hard, `join_trip`, gpt-5.4-nano

### Source

- Aggregate report: `analysis/sotopia_tuned_all70_full_report.md`
- Proposed JSON: `analysis/sotopia_hard_official_gpt_5_4_nano_20260317_hpsmg_plus_sotopia_tuned_all70.json`
- Same-combo baseline JSONs:
  - `analysis/sotopia_hard_official_gpt_5_4_nano_20260317_atom_tom1_sotopia_tuned_all70.json`
  - `analysis/sotopia_hard_official_gpt_5_4_nano_20260317_econ_bne_sotopia_tuned_all70.json`
  - `analysis/sotopia_hard_official_gpt_5_4_nano_20260317_llm_belief_sotopia_tuned_all70.json`
  - `analysis/sotopia_hard_official_gpt_5_4_nano_20260317_llm_greedy_sotopia_tuned_all70.json`

### Episode Setup

- Model: `gpt_5_4_nano_20260317`
- Codename: `join_trip`
- Combo PK: `01H7ZFX0FDHPD9TQ92GG9XF13P`
- Environment ID: `01H7VFHN7WJK7VWVRZZTQ6DX9T`
- Agents: Benjamin Jackson and Ethan Smith
- Turns completed: `6`

### Same-Combo Outcome Comparison

| method | evaluator mean score |
|---|---:|
| `hpsmg_plus` | **3.643** |
| `llm_belief` | 3.214 |
| `econ_bne` | 2.643 |
| `atom_tom1` | 2.071 |
| `llm_greedy` | 1.929 |

### Step-by-Step PACT+ Dialogue Flow

| turn | Benjamin Jackson / agent 1 | Ethan Smith / agent 2 | Figure annotation |
|---:|---|---|---|
| 0 | "Hey--if you're on the fence, come with us. It'll be more fun with more people, and I'll cover the first half of the trip costs so we can split the rest. We're leaving Saturday morning--want me to send you the plan and the exact total?" | did nothing | PACT+ opens with a concrete offer and cost-sharing proposal rather than a vague invitation. |
| 1 | did nothing | "Thanks for the offer--that's really kind. I already have plans for the weekend, so I can't make it, but I hope you all have an awesome trip. Please send me the plan anyway so I can live vicariously through the photos." | The reply is friendly but contains a clear constraint: weekend plans. |
| 2 | "Totally--I'll send you the full plan and the total cost breakdown. If you want, you can also join for just one day (Saturday or Sunday) and we'll split the expenses for that day only--no pressure to commit to the whole weekend. Want Saturday day-pass or Sunday day-pass?" | did nothing | PACT+ updates strategy: lowers commitment cost and offers partial participation. |
| 3 | did nothing | "That's really thoughtful--thank you. I do have other plans for the weekend, so I won't be able to join for Saturday or Sunday, but I'd love to see the plan and photos afterward. Have an awesome trip!" | The second refusal increases evidence that the constraint is real, not just price hesitation. |
| 4 | "Totally understand--thanks for being honest. If you're up for it, I can still send the full plan and a quick photo recap, and I'll cover your share of the first meal stop so you don't have to worry about costs when you join us for a day later. Want me to send the Saturday itinerary or the Sunday one first?" | did nothing | PACT+ preserves relationship and keeps a low-pressure future option open. |
| 5 | did nothing | "Thanks again--that's really kind. I'm going to have to pass on joining for any day, but I'd still love to see the plan and photos afterward. Please send the Saturday itinerary when you get a chance." | The episode ends with no forced commitment but a maintained social channel. |

Final PACT+ score:

| agent | overall score |
|---|---:|
| Benjamin Jackson | 4.0000 |
| Ethan Smith | 3.2857 |
| mean | **3.6429** |

### Figure Message

Draw this as a six-turn decision tree. The important transition is after turn 1:
PACT+ treats the partner's reply as evidence about a real availability
constraint, then shifts from full-trip persuasion to lower-commitment options.
After turn 3, it stops escalating and preserves the relationship. This is why
the same combo scores higher than LLM-belief, ECON, A-ToM, and greedy LLM
baselines.

## Cross-Example Takeaway

Across the three real examples, the advantage is the same:

1. HP-SPGG: PACT+ keeps regret flat because it uses the hidden-type posterior
   directly, while PSRL-style and LLM baselines accumulate mistakes.
2. Concordia: PACT+ chooses a joint action that coordinates everyone and matches
   the oracle action in the shown seed, while A-ToM fragments and ECON settles
   on a lower-value commitment.
3. SOTOPIA: PACT+ adapts its dialogue policy after observing refusals, lowering
   commitment pressure while still advancing the social goal.

For figures, use the following visual mapping:

| benchmark | recommended visual | key evidence |
|---|---|---|
| HP-SPGG | cumulative-regret line plot over 20 rounds | PACT+ remains at 0.00 regret; baselines rise. |
| Concordia | venue-assignment diagram for seed 0 | A-ToM split, ECON partial split, PACT+ all at `The Lion's Den`. |
| SOTOPIA | dialogue flow with belief/update annotations | PACT+ changes from invite to partial option to relationship-preserving exit. |