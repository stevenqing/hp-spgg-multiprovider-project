# LLM-Based Candidate Baselines and Related Work

Last updated: 2026-05-17

This note narrows the comparison set to LLM-based methods for multi-agent coordination, hidden-belief reasoning, public-goods cooperation, and social-dilemma behavior. General-purpose agent frameworks such as AutoGen, CAMEL, AgentVerse, MetaGPT, and Microsoft Agent Framework are not treated as baselines here: they are infrastructure, not methods that solve the HP-SPGG-style problem.

## Baselines that match the HP-SPGG problem class

| Candidate method | Paper / source | Code status | Why it is comparable | HP-SPGG adaptation |
|---|---|---|---|---|
| Adaptive ToM / A-ToM | Mu et al., "Adaptive Theory of Mind for LLM-based Multi-Agent Coordination", arXiv:2603.16264 / AAAI 2026 | `ChunjiangMonkey/Adaptive-ToM` | Direct LLM-based coordination method. It estimates partner ToM order from previous interactions and uses 0/1/2-order partner-action prediction. | Already implemented as `atom_tom0`, `atom_tom1`, `atom_tom2`, `atom_adaptive_ftl`, and `atom_adaptive_hedge`. This remains the strongest ToM-family baseline. |
| ECON | Xie et al., "From Debate to Equilibrium: Belief-Driven Multi-Agent LLM Reasoning via Bayesian Nash Equilibrium", arXiv:2506.08292 / ICML 2025 | `tmlr-group/ECON` | Direct LLM-based belief/equilibrium method. It treats multi-LLM coordination as an incomplete-information game and seeks BNE-style commitments under belief uncertainty. | Already implemented as `econ_bne`. This remains the strongest equilibrium/belief-coordination baseline. |
| MAC-SPGG | Liang et al., "Everyone Contributes! Incentivizing Strategic Cooperation in Multi-LLM Systems via Sequential Public Goods Games", arXiv:2508.02076 | No public GitHub found from checked pages | Very close public-goods setup. It uses sequential public-goods incentives for multi-LLM cooperation and explicitly targets free-riding. | Add a MAC-SPGG-style incentive/reward variant if we want another close baseline. Since no code was found, label as paper-inspired adaptation rather than official reproduction. |
| Public-goods LLM cooperation protocol | Guzman Piedrahita et al., "Corrupted by Reasoning: Reasoning Language Models Become Free-Riders in Public Goods Games", COLM 2025 / OpenReview | OpenReview supplementary material found; no GitHub found in checked page | Directly studies LLM agents in repeated public-goods games with institutional choice, costly sanctioning, norm enforcement, and free-riding. | Use as a behavioral comparison protocol: run HP-SPGG agents with individual-rational, pro-social, sanctioning, and narrative prompt variants; compare cooperation/free-riding archetypes. Not a coordinator algorithm. |
| Reflexion-style LLM agent | Shinn et al., "Reflexion: Language Agents with Verbal Reinforcement Learning", NeurIPS 2023 | `noahshinn/reflexion` | LLM agent learns from scalar/free-form feedback through verbal self-reflection memory without weight updates. Relevant for repeated HP-SPGG/Concordia/SOTOPIA episodes. | Optional weak baseline: each player stores previous outcome feedback and generates a reflection before the next action. Useful to test whether generic verbal learning can replace explicit posterior updates. |
| ReAct-style LLM agent | Yao et al., "ReAct: Synergizing Reasoning and Acting in Language Models", ICLR 2023 | `ysymyth/ReAct` | General LLM decision-making method that interleaves reasoning traces and actions in an external environment. | Optional weak baseline for Concordia/SOTOPIA: each agent uses reason-then-act traces from public/private observations. It does not explicitly model hidden types, so it should not be overclaimed. |

## Not baselines for the main comparison

| Candidate | Why it should not be a main baseline |
|---|---|
| AutoGen, CAMEL, AgentVerse, MetaGPT, Microsoft Agent Framework | These are orchestration frameworks. They can host agents, but they do not specify a problem-solving policy for hidden-type public-goods coordination. |
| LOLA, QMIX, VDN, MADDPG, PyMARL | These are traditional MARL baselines, not LLM-based methods. They can remain background related work, but they are not the right next comparison for this paper. |
| Generic multi-agent debate / DyLAN / MAD | These are LLM-based reasoning/collaboration methods, but their target problem is factuality, math, code, or general task solving rather than repeated social-dilemma coordination under hidden types. They are lower priority than A-ToM, ECON, MAC-SPGG, and public-goods LLM protocols. |

## Recommended LLM-based comparison suite

For the HP-SPGG paper, the cleanest LLM-based comparison story is:

1. Keep `llm_greedy` as the simple prompted LLM coordinator baseline.
2. Keep `llm_belief` as the simple prompted belief / persona-inference baseline.
3. Run the full A-ToM family: `atom_tom0`, `atom_tom1`, `atom_tom2`, `atom_adaptive_ftl`, `atom_adaptive_hedge`.
4. Run ECON: `econ_bne`.
5. Add one MAC-SPGG-inspired incentive variant only if we want another public-goods-specific method beyond A-ToM/ECON.
6. Add Reflexion-style verbal feedback only as an optional weak generic LLM-agent baseline.

Concordia and SOTOPIA should be the external environments. The baseline methods inside those environments should remain LLM-based: direct prompting, belief prompting, A-ToM-style partner modeling, ECON-style belief/equilibrium coordination, and optionally Reflexion-style verbal feedback.

## Paper-facing positioning

The paper should say that HP-SPGG compares against LLM-based alternatives that actually attempt social coordination or belief reasoning, rather than generic agent frameworks:

1. Prompted LLM coordinators test whether direct language reasoning is enough.
2. A-ToM tests nested partner-model reasoning.
3. ECON tests equilibrium-style belief coordination.
4. MAC-SPGG/public-goods LLM papers motivate the public-goods setting and free-riding failure modes.
5. Reflexion/ReAct can be cited or used as weak generic LLM-agent baselines, but not as the primary comparison.