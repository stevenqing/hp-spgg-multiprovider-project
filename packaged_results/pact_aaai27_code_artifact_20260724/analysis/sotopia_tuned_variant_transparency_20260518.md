# SOTOPIA Tuned Variant Transparency - 2026-05-18

This note documents what `hpsmg_plus_sotopia_tuned` changes relative to vanilla `hpsmg_plus` in the reconstructed SOTOPIA-Hard all70 runs.

## Short Answer

`hpsmg_plus_sotopia_tuned` is a SOTOPIA-specific prompt/action profile for the same `hpsmg_plus` baseline. It does not change the acting model, evaluator model, SOTOPIA cases, number of turns, hidden personas, HP-SPGG beta, or a Bayesian prior used by HP-SPGG experiments.

## What Changes

- Uses `--agent-strategy-profile sotopia_tuned` in `llm_hpgg_sotopia.run_sotopia_hard_official`.
- Applies only when `baseline == hpsmg_plus`.
- Sets LLM action decoding to temperature `0.0` instead of legacy `0.2`.
- Allows `max_tokens=280` instead of legacy `220`.
- Clips current observation to `1400` characters instead of legacy `4000` characters.
- Uses a shorter history window: 6 messages instead of 8.
- Adds SOTOPIA scoring guardrails: maximize goal, believability, relationship, knowledge, material benefit; avoid secret leakage and social-rule violations.
- Adds concrete task tactics for bargaining, ownership/consent, safety/de-escalation, and fair allocation scenarios.
- Prevents `leave`/`none` when `speak` is available for tuned HPSMG+.
- Cleans generated utterances by replacing meta-policy phrases or empty/leave responses with a concrete fallback utterance.

## What Does Not Change

- Acting model: same CloudGPT backbone as the comparison row.
- Evaluator model: same backbone as acting model in the all70 runs.
- Baseline family: still `hpsmg_plus`.
- SOTOPIA-Hard cases: same reconstructed all70 case set.
- Turn budget: 6 turns.
- No alternative HP-SPGG beta is introduced.
- No alternative HP-SPGG prior is introduced.
- No hidden-persona set is swapped in the SOTOPIA runner.
- No case is dropped in the tuned all70 results.

## Paper-Safe Wording

Use wording like:

> We also report a SOTOPIA-adapted HPSMG+ prompting profile that keeps the HPSMG+ decision principle fixed but adds task-interface constraints needed by SOTOPIA-Hard: concrete offers, no premature leaving, de-escalation for harmful goals, and avoidance of evaluator-visible meta-policy language. We report it separately as `HPSMG+ tuned` and compare it against vanilla HPSMG+ and other baselines.

Do not imply that tuned HPSMG+ is the same prompt as vanilla HPSMG+. Also do not hide the tuned profile; report it explicitly as a SOTOPIA-specific adaptation.

## Code Pointers

- Agent implementation: `llm_hpgg_sotopia/agents.py`
- Tuned policy function: `_sotopia_tuned_policy`
- Scenario tactics: `_scenario_tactic`
- Action cleaning: `_clean_sotopia_argument`
- Runner argument: `--agent-strategy-profile sotopia_tuned`
- Overnight runner: `scripts/run_sotopia_tuned_hpsmg_plus_overnight.ps1`