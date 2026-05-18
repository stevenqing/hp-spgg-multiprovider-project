# Phase 2 Concordia/SOTOPIA Environment Notes

## Local source locations

- Concordia source: `external/concordia`
- SOTOPIA source: `external/sotopia`
- Repeatable setup script: `scripts/setup_phase2_external_envs.ps1`

The machine does not currently expose `git` in PowerShell, so the repositories were downloaded from GitHub codeload zip archives instead of cloned with git.

## Installed local environments

- Concordia venv: `.venvs/concordia-py314`
  - Python: 3.14.4
  - Installed with `uv pip install -e external/concordia`.
  - Smoke import passed for `concordia.language_model.language_model.LanguageModel` and `concordia.environment.engines.simultaneous.Simultaneous`.
- SOTOPIA venv: `.venvs/sotopia-py312`
  - Python: 3.12.13
  - SOTOPIA requires Python `>=3.10,<3.13`, so it cannot live in the project default Python 3.14 environment.
  - Installed PyPI runtime dependencies directly, then installed local SOTOPIA with `--no-deps` because its `aact` dependency is declared as a git source and local PowerShell has no `git`.
  - CloudGPT dependencies `openai`, `azure-identity`, and `msal` are installed in this venv for live SOTOPIA adapter runs.
  - Smoke import passed for `sotopia.messages.AgentAction`, `sotopia.envs.ParallelSotopiaEnv`, and `sotopia.server.run_async_server` with `SOTOPIA_STORAGE_BACKEND=local`.

## Concordia interface findings

- Concordia is built around entities, components, game masters, and an engine loop.
- The natural external-comparison tasks for our project are in `external/concordia/examples/games`, especially:
  - `pub_coordination`: social coordination over venue choices.
  - `haggling`: dyadic bargaining.
  - `haggling_multi_item`: multi-item bargaining.
- The main LLM integration point is `concordia.language_model.language_model.LanguageModel`:
  - Implement `sample_text(prompt, ...)` by calling our `llm_hpgg.llm_agent.call_player` or backend-specific CloudGPT wrapper.
  - Implement `sample_choice(prompt, responses, ...)` by asking for one of the listed options and validating the selected index.
- Concordia examples expect an embedder for associative memory. For first smoke adapters, use a deterministic local hash/bag-of-words embedder unless a scenario requires semantic retrieval quality.
- The first practical adapter should wrap the `pub_coordination` example, because it is closest to hidden-preference social coordination and gives a useful bridge from HP-SPGG to generative social simulation.

## SOTOPIA interface findings

- SOTOPIA exposes a PettingZoo-style `ParallelSotopiaEnv` and convenience runner `run_async_server`.
- The default storage backend is Redis. For local development and smoke tests, set `SOTOPIA_STORAGE_BACKEND=local` to use `~/.sotopia/data/`.
- The agent interface is `sotopia.agents.base_agent.BaseAgent`:
  - Agents receive an `Observation`.
  - Agents return an `AgentAction(action_type, argument, to)`.
- The built-in `LLMAgent` calls LiteLLM, but for our comparisons we should subclass `BaseAgent` directly so the same LLM-based baseline families are used across HP-SPGG, Concordia, and SOTOPIA.
- Local official SOTOPIA Redis/local profile data is not currently populated: `~/.sotopia/data/` is empty and `EnvironmentProfile.all_pks()` returns zero. Docker is unavailable on this machine, so the official Redis dump install route cannot run directly here.
- A no-Docker official-hard path is now implemented: `llm_hpgg_sotopia/official_hard_data.py` reconstructs the 70 public SOTOPIA-Hard env/agent combos from official HuggingFace `benchmark_agents.json` plus `sotopia_episodes_v1_hf.jsonl`, and `llm_hpgg_sotopia/run_sotopia_hard_official.py` runs them through official `ParallelSotopiaEnv` with our project agents and SOTOPIA-dimension scoring.
- The first practical adapter should run a small local-storage SOTOPIA episode with custom agents implementing:
  - direct prompt baseline (`llm_greedy`)
  - belief prompt baseline (`llm_belief`)
  - A-ToM-style partner modeling
  - ECON-style proposal/executor/refinement loop

## Implementation direction

1. `llm_hpgg_concordia/cloudgpt_model.py` now implements Concordia `LanguageModel` over our provider layer.
2. `llm_hpgg_concordia/embedder.py` now provides a deterministic local hashing embedder for first Concordia smoke runs.
3. `llm_hpgg_sotopia/agents.py` now provides `BaseAgent` subclasses for the LLM-based baseline families.
4. `scripts/smoke_phase2_adapters.ps1` verifies both adapter layers in offline mode.
5. `llm_hpgg_concordia/run_concordia_baselines.py` now provides a repeatable Concordia adapter-level social-choice sweep.
6. `llm_hpgg_sotopia/run_sotopia_baselines.py` now provides a repeatable SOTOPIA-compatible action sweep over synthetic observations.
7. `llm_hpgg_concordia/run_pub_coordination.py` now connects `HPGGConcordiaLanguageModel` to the official Concordia `pub_coordination` simulation.
8. `llm_hpgg_sotopia/run_episode_smoke.py` now connects `HPGGSotopiaAgent` to an official `ParallelSotopiaEnv` loop using local `EnvironmentProfile` and `AgentProfile` objects.
9. `llm_hpgg_sotopia/run_sotopia_hard_official.py` now runs reconstructed official SOTOPIA-Hard combos with SOTOPIA-dimension scoring via the project CloudGPT wrapper.
10. Keep AutoGen/CAMEL-style frameworks out of the baseline list; they can be infrastructure references only, not methods under comparison.

## Adapter smoke commands

```powershell
scripts\setup_phase2_external_envs.ps1
scripts\smoke_phase2_adapters.ps1
.venvs\concordia-py314\Scripts\python.exe -m llm_hpgg_concordia.run_concordia_baselines --model offline --out analysis\concordia_baseline_choice_sweep_offline.json
.venvs\concordia-py314\Scripts\python.exe -m llm_hpgg_concordia.run_pub_coordination --config puppet --model offline --out analysis\concordia_pub_coordination_official_smoke.json
.venvs\sotopia-py312\Scripts\python.exe -m llm_hpgg_sotopia.run_sotopia_baselines --model offline --out analysis\sotopia_baseline_action_sweep_offline.json
.venvs\sotopia-py312\Scripts\python.exe -m llm_hpgg_sotopia.run_episode_smoke --baseline llm_belief --model offline --turns 2 --out analysis\sotopia_official_episode_smoke.json
.venvs\sotopia-py312\Scripts\python.exe -m llm_hpgg_sotopia.run_episode_smoke --baseline llm_belief --model DeepSeek-V3.2 --turns 1 --out analysis\sotopia_official_episode_smoke_DeepSeek_V3_2_live_t1.json
.venvs\sotopia-py312\Scripts\python.exe -m llm_hpgg_sotopia.run_sotopia_hard_official --baseline llm_belief --model offline --evaluator-model offline --turns 2 --limit 1 --out analysis\sotopia_hard_official_offline_smoke.json
.venvs\sotopia-py312\Scripts\python.exe -m llm_hpgg_sotopia.run_sotopia_hard_official --baseline llm_belief --model DeepSeek-V3.2 --evaluator-model DeepSeek-V3.2 --turns 2 --limit 1 --resume --out analysis\sotopia_hard_official_DeepSeek_V3_2_live_smoke.json
.venvs\sotopia-py312\Scripts\python.exe -u -m llm_hpgg_sotopia.run_sotopia_hard_official --baseline llm_belief --model DeepSeek-V3.2 --evaluator-model DeepSeek-V3.2 --turns 6 --limit 0 --resume --out analysis\sotopia_hard_official_DeepSeek_V3_2_llm_belief_all70.json
```

Validated on 2026-05-17:

- Concordia adapter returned text, a valid finite choice tuple, and a fixed-size embedding vector.
- SOTOPIA adapter returned a valid `AgentAction` from a synthetic `Observation` under `SOTOPIA_STORAGE_BACKEND=local`.
- Concordia adapter sweep wrote `analysis/concordia_baseline_choice_sweep_offline.json`.
- Official Concordia `pub_coordination` puppet smoke wrote `analysis/concordia_pub_coordination_official_smoke.json`.
- SOTOPIA adapter sweep wrote `analysis/sotopia_baseline_action_sweep_offline.json`.
- Official SOTOPIA local episode smoke wrote `analysis/sotopia_official_episode_smoke.json`.
- On 2026-05-17, SOTOPIA offline smoke was rechecked with deterministic `model=offline` handling in `HPGGSotopiaAgent`; outputs: `analysis/sotopia_official_episode_smoke_recheck.json` and `analysis/sotopia_baseline_action_sweep_recheck.json`.
- On 2026-05-17, SOTOPIA live CloudGPT smoke passed for `DeepSeek-V3.2` with `llm_belief`, one turn, output `analysis/sotopia_official_episode_smoke_DeepSeek_V3_2_live_t1.json`.
- On 2026-05-17, official SOTOPIA-Hard reconstruction found all 70 hard combos across 14 unique official hard environments from public HuggingFace data. Offline smoke wrote `analysis/sotopia_hard_official_offline_smoke.json`.
- On 2026-05-17, all 70 reconstructed official SOTOPIA-Hard combos completed a two-turn offline enumeration check, output `analysis/sotopia_hard_official_offline_all70_check.json`.
- On 2026-05-17, reconstructed official SOTOPIA-Hard live CloudGPT smoke passed for `DeepSeek-V3.2` with `llm_belief`, one combo, two turns, output `analysis/sotopia_hard_official_DeepSeek_V3_2_live_smoke.json`. Use CloudGPT deployment name `DeepSeek-V3.2`; `deepseek-ai/DeepSeek-V3.2` returned 404 on this endpoint.
- On 2026-05-17, `run_sotopia_hard_official.py` gained per-combo checkpointing and `--resume`, so long live runs can safely continue from an existing output JSON by `combo_pk`.
- On 2026-05-17, all four DeepSeek reconstructed official SOTOPIA-Hard all-70 live baselines were started as detached background processes with checkpointing:
  - `llm_belief`: `analysis/sotopia_hard_official_DeepSeek_V3_2_llm_belief_all70.json`
  - `llm_greedy`: `analysis/sotopia_hard_official_DeepSeek_V3_2_llm_greedy_all70.json`
  - `atom_tom1`: `analysis/sotopia_hard_official_DeepSeek_V3_2_atom_tom1_all70.json`
  - `econ_bne`: `analysis/sotopia_hard_official_DeepSeek_V3_2_econ_bne_all70.json`
  Background logs use matching names under `logs/`, for example `logs/sotopia_hard_official_DeepSeek_V3_2_llm_belief_all70_stdout.log` and `logs/sotopia_hard_official_DeepSeek_V3_2_llm_belief_all70_stderr.log`.
- On 2026-05-17, all four DeepSeek reconstructed official SOTOPIA-Hard all-70 live baselines completed with `complete=true`. Overall means: `econ_bne` 3.1765, `llm_greedy` 3.1643, `atom_tom1` 3.1061, `llm_belief` 3.0776. Summary output: `analysis/sotopia_hard_official_DeepSeek_V3_2_summary.md`; numeric integration: `analysis/all_numeric_results.md`.
- On 2026-05-17, proposed `hpsmg_plus` was added as a fair SOTOPIA adapter mode. It uses the same observation/goal/history as the baselines and prompts a posterior-belief, robust joint-value, and uncertainty-reduction policy; it does not use oracle case labels or hidden evaluator information. Offline smoke wrote `analysis/sotopia_hard_official_hpsmg_plus_offline_smoke.json`; live DeepSeek smoke wrote `analysis/sotopia_hard_official_DeepSeek_V3_2_hpsmg_plus_live_smoke.json` with mean 3.5714.
- On 2026-05-17, proposed `hpsmg_plus` reconstructed official SOTOPIA-Hard all-70 live run completed with `complete=true` at `analysis/sotopia_hard_official_DeepSeek_V3_2_hpsmg_plus_all70.json`. Dedicated monitor: `logs/sotopia_hard_official_hpsmg_plus_monitor.log`. Final mean 3.1939, above the strongest completed baseline `econ_bne` at 3.1765.
- On 2026-05-17, GPT/Kimi/Llama SOTOPIA-Hard all-70 sweeps were started for all five methods: `hpsmg_plus`, `llm_belief`, `llm_greedy`, `atom_tom1`, `econ_bne`. A direct 15-run launch hit CloudGPT 429 rate limits, so the active path is the low-concurrency checkpoint/resume queue `scripts/run_sotopia_hard_model_queue.ps1` with `MaxConcurrent=3`. Queue log: `logs/sotopia_hard_official_model_queue.log`; combined monitor: `logs/sotopia_hard_official_all_models_monitor.log`.

Monitor command:

```powershell
$baselines=@('llm_belief','llm_greedy','atom_tom1','econ_bne')
foreach($b in $baselines){
  $out="analysis\sotopia_hard_official_DeepSeek_V3_2_${b}_all70.json"
  if(Test-Path $out){ .venvs\sotopia-py312\Scripts\python.exe -c "import json; p='$($out.Replace('\\','/'))'; d=json.load(open(p,encoding='utf-8')); print('$b checkpoint=%s/%s complete=%s mean=%s' % (d.get('case_count'), d.get('target_case_count'), d.get('complete'), d.get('summary',{}).get('mean_overall')))" }
  else { Write-Host "$b checkpoint=waiting_for_first_case" }
}
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*run_sotopia_hard_official*' } | Select-Object ProcessId,CreationDate,CommandLine | Format-Table -Wrap
```

Detached combined monitor:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\monitor_sotopia_hard_runs.ps1 -LogPath logs\sotopia_hard_official_monitor.log
Get-Content logs\sotopia_hard_official_monitor.log -Tail 30
```
