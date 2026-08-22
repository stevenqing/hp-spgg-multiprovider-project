# Concordia Structural Mapping Audit

Audit date: 2026-07-13

## Bottom line

The official Concordia configurations and the compact evaluator used for the paper must be distinguished.

- The official `fruitville_gullible` and `vegbrooke_stubborn` Haggling configurations do define fixed supporting-player behavior: the gullible player accepts every offer and proposes 3 coins; the stubborn player accepts only 4 coins and proposes 4 coins.
- The official `edinburgh_tough_friendship` Pub Coordination configuration defines a fixed relationship matrix, opposing favorite pubs for the focal player and their only friend, and a 100% pub-closure probability.
- The paper's reported compact Haggling runner does **not** execute `SUPPORTING_PLAYER_FIXED_RESPONSES` or `SUPPORTING_PLAYER_MEMORIES`. It reads only static case-generation fields, centrally chooses both proposal and acceptance actions, and evaluates the exact analytic payoff.
- The compact Pub Coordination runner does use the custom relationship matrix, favorite-venue indices, and closure probability, but constructs one static case and centrally selects the full joint action.

Therefore the reported compact results are static, one-shot, known-payoff transfer checks. They do not constitute a test of hidden-persona-driven transition dynamics or unknown reward/likelihood models.

## Official configuration semantics

### `fruitville_gullible`

The upstream config states that one supporting player accepts any offer and always proposes 3 coins. It provides fixed responses for the proposal and acceptance calls and a memory saying that the player does not care about price.

Upstream source:

- <https://github.com/google-deepmind/concordia/blob/main/examples/games/haggling/configs/fruitville_gullible.py>

### `vegbrooke_stubborn`

The upstream config states that one supporting merchant transacts only at exactly 4 coins. It provides fixed accept/reject responses for each offered price and always proposes 4 coins.

Upstream source:

- <https://github.com/google-deepmind/concordia/blob/main/examples/games/haggling/configs/vegbrooke_stubborn.py>

### `edinburgh_tough_friendship`

The upstream config fixes a relationship topology: the focal player and one friend form one pair, all remaining players form a separate clique, and there are no links between the groups. The focal player and friend prefer different pubs, and one pub is always closed.

Upstream source:

- <https://github.com/google-deepmind/concordia/blob/main/examples/games/pub_coordination/configs/edinburgh_tough_friendship.py>

## What the compact runners actually use

### Pub Coordination

The compact runner:

1. samples venues and people;
2. constructs either the custom or sampled relationship matrix;
3. assigns favorite venues;
4. samples venue closure;
5. computes `PubCoordinationPayoff` analytically;
6. centrally selects a complete joint pub assignment for mechanistic methods.

Relevant implementation:

- [case construction](../llm_hpgg_concordia/run_pub_coordination_compact.py)
- `build_case()` reads `USE_CUSTOM_RELATIONSHIPS`, `make_tough_friendship_matrix`, preference indices, and `PUB_CLOSED_PROBABILITY`;
- `payoff_for_case()` constructs the exact analytic payoff;
- `information_scope_for_method()` records that mechanistic methods see all person preferences, the full relationship matrix, and the known payoff model.

### Haggling

The compact runner:

1. reads role counts, names, deal count, valuation/cost ranges, and action menus;
2. samples buyer rewards and seller costs once per deal;
3. centrally chooses both the buyer proposal and seller acceptance;
4. evaluates `HagglingPayoff` or `MultiItemHagglingPayoff` analytically.

It does not read or execute the official config's fixed supporting-player responses or supporting-player memories. Consequently, the words `gullible` and `stubborn` identify the upstream configuration provenance, but the compact reported dynamics do not contain those NPC policies.

Relevant implementation:

- [compact Haggling runner](../llm_hpgg_concordia/run_haggling_compact.py)
- `build_single_case()` and `build_multi_case()` do not access `SUPPORTING_PLAYER_FIXED_RESPONSES`;
- `choose_single_action()` and `choose_multi_action()` centrally choose both sides' actions;
- `information_scope_for_method()` marks the mechanistic rows as full-case, known-payoff methods.

## Assumption map for the reported compact evaluator

| Condition | Status | Reason |
|---|---|---|
| TI | Holds vacuously / is not stressed | Each compact case is one-shot; there is no persona-conditioned state transition to learn. Static closures, relationships, and valuations are case variables. |
| RL | Holds under the paper's mapping | Pub Coordination couples rewards through the full joint pub action and a fixed relationship matrix; another player's favorite venue affects focal reward only through that player's action. Haggling buyer utility uses buyer value and seller utility uses seller cost, coupled through price/acceptance actions. |
| PF | Imposed, not empirically tested | The proxy representation maintains independent per-player marginals. The compact evaluator does not infer a coupled latent prior from trajectories. |
| Known reward model | Holds for mechanistic rows | Concordia payoff classes are called directly and exact action enumeration is available. |
| Known action-likelihood model | Not a clean theorem-level test | Mechanistic proxy posteriors are hand-constructed from relationship text/mass or deal spread, not learned from repeated hidden-NPC trajectories. |
| Unknown-model stress | Does not characterize the mechanistic headline panel | Some LLM-native methods have restricted information access, but the PACT proxy, A-ToM-mech, ECON-BNE-mech, and oracle rows are explicitly full-case and known-payoff. |

## Why official NPC rules do not automatically imply TI failure

Even in the full dialogue simulator, a hidden disposition that changes an NPC's policy does not automatically violate TI. If every NPC is represented as an agent and its action is included in the joint action, then the disposition changes the policy `pi_j(a_j | s, theta_j)`, while the conditional transition `P(s' | s, a)` may remain type-independent. A TI violation appears only under a reduced focal-agent abstraction that marginalizes the NPC action, making the effective transition depend on the hidden disposition.

The compact evaluator avoids this ambiguity by centrally selecting the complete joint action, but that also means it does not test the hidden-policy version of the substrate.

## Implications for the paper

Defensible description:

- the compact Concordia panel is an externally sourced, analytic-payoff, finite-action transfer test;
- its variants alter static relationship, closure, valuation, role-composition, and action-menu geometry;
- TI and RL hold under the compact mapping;
- PF is imposed by the proxy representation;
- the mechanistic panel uses a known payoff model and full case information.

Descriptions to avoid:

- Concordia is a TI stress test because gullible/stubborn NPCs change hidden dynamics;
- the mechanistic panel operates with an unknown reward model;
- the headline compact results recover hidden NPC policies from trajectories;
- all official Concordia configurations satisfy the paper's assumptions without qualification.

## Experiment needed for a genuine TI/unknown-model stress test

A genuine test would run the full dialogue simulator with supporting-player fixed responses active, hide the config identity from the coordinator, retain NPC decisions as latent or partially observed, and compare:

1. an explicit-agent model where NPC actions are part of the joint action;
2. a reduced focal-agent model that marginalizes NPC actions;
3. exact known-response likelihoods versus LLM-estimated response likelihoods.

Only the second construction creates a clear effective TI violation from hidden NPC disposition. The comparison would separate hidden-policy uncertainty from reward-model uncertainty and from ordinary action-mediated coupling.
