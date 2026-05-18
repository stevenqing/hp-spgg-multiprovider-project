# Master rollout export — coverage report

Output directory: `analysis/exports/`

| file | rows | notes |
|---|---|---|
| `master_rollouts.jsonl` | 945617 | one row per (method, backbone, substrate, seed, episode_k) |
| `posterior_entropy.csv` | 9600 | LLM trace methods only (numeric / Concordia rows do not log per-agent posteriors) |
| `posterior_kl.csv` | 9600 | KL to point-mass theta_star reconstructed from seed |
| `beta_ablation.csv` | 939200 | HP-SPGG numeric only — paired β ∈ {0, 0.05, 0.1, 0.25, 0.5, 0.75, 1, 1.5} |
| `cum_payoff_trajectories.csv` | 945617 | all sources — Concordia rows are episode_k=1 only |

## Conventions

- `backbone` ∈ {`DeepSeek-V3.2`, `GPT-5.4-nano`, `Kimi-K2.6`, `Llama-Maverick`} for LLM-driven runs.
  Numeric/mechanistic methods use `backbone='mechanistic'`.
- `method` is the algorithm name as logged (`hpsmg_plus`, `hpsmg`, `joint_psrl`, `oracle`,
  `llm_greedy`, `llm_belief`, `atom_tom0/1/2`, `atom_adaptive_ftl`, `atom_adaptive_hedge`,
  `econ_bne`, `hpsmg_plus_proxy`, `hpsmg_plus_joint_proxy`, `oracle_joint`, ...).
- `substrate = hpspgg_c{N}` for HP-SPGG profile index N; Concordia substrates use their compact codenames
  (e.g. `capetown_mechanistic_joint`, `haggling_fruitville`).
- `episode_k` is 1-indexed.
- `theta_star`: reconstructed via `np.random.default_rng(seed).integers(0, 4, size=n)` to match
  `llm_hpgg/run_llm_baselines.py::run_episode`. Persona index order is
  `[altruistic_builder, conditional_cooperator, risk_averse_balancer, free_rider]`.
- `posterior` (LLM rows): empirical one-hot-with-smoothing distribution derived from the model's free-text
  `inferred_personas` field. `posterior_parsed=0` rows are uniform fallbacks (entropy = log 4 ≈ 1.386 nats).
  This is a *hard-label approximation* — to get true soft posteriors we would need to re-prompt the LLM
  to return a distribution.
- `beta`: only set for HP-SPGG numeric rows (the LLM agents don't take β as input).

## Known gaps

1. **LLM β-ablation is missing** — no LLM-driven β=0 vs β=0.25 paired runs. Schema 3 currently
   exists only for numeric agents on `hpspgg_c{1..29}`. To extend, re-run
   `llm_hpgg.run_llm_baselines` and `run_external_llm_baselines` with β=0 (currently β is implicit 0
   in those wrappers — they don't expose β to the LLM, so the comparison is trivially identical).
2. **Concordia compact runs are single-shot** (episode_k=1) — no within-substrate K=20 horizon and
   no posterior dumps. Extending requires modifying `llm_hpgg_concordia/run_pub_coordination_compact.py`
   and `run_haggling_compact.py` to (a) iterate K episodes per seed, (b) maintain a cross-episode
   posterior in mechanistic methods, (c) dump it per episode.
3. **Soft posteriors not available** — `inferred_personas` is free text. Hard-label approximation
   in this export is best-effort: parser does longest-token match against persona keys/labels.
