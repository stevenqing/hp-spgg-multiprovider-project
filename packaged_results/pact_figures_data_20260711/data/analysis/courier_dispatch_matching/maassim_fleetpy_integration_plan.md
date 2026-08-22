# MaaSSim and FleetPy Integration Assessment

## Short Recommendation

Use MaaSSim first and keep FleetPy as the second-stage simulator.

MaaSSim is closer to the current CourierDispatch-Rules abstraction because it already has a platform-level matching function `f_match`, driver accept/reject/opt-out/reposition decision functions, microscopic travellers, microscopic drivers, and queue-level offers. FleetPy is more powerful and modern, but it is heavier: integrating PACT cleanly means writing a FleetPy fleet-control operator, not just swapping a matching function.

## MaaSSim Fit

Useful properties from the upstream repo:

| MaaSSim component | Why it helps |
|---|---|
| `PlatformAgent.f_match` is external/user-defined | We can wrap or replace matching with PACT/PACT+ |
| `platform.vehQ`, `platform.reqQ`, `platform.offers`, `platform.tabu` | Natural queue snapshot for candidate assignments |
| `f_driver_decline`, `f_driver_repos`, `f_driver_out` | Direct hooks for hidden driver behavioural rules |
| `driverEvent` logs | Posterior observations can be based on neutral events |
| `sim.res[].veh_exp`, `sim.res[].pax_exp` | KPI output for system and agent-level evaluation |
| SimPy event loop | Real space-time dynamics without building a simulator ourselves |

Main integration idea:

```text
MaaSSim f_match(platform)
  -> extract queued vehicles/requests
  -> build candidate driver-request offer matrix
  -> PACT/PACT+ chooses assignment
  -> create MaaSSim offers and let driver/traveller accept/reject machinery proceed
```

## MaaSSim Risks

| Risk | Mitigation |
|---|---|
| MaaSSim is older and depends on osmnx/simpy/networkx stack | Start with the packaged tiny example, isolate in separate environment |
| Internal objects are pandas/dotmap-heavy | Build a narrow adapter that extracts only IDs, positions, wait time, fare, travel time |
| Regret oracle is not obvious | First report realized KPIs; compute oracle only for queue-level candidate pairs in small smoke runs |
| True hidden rules do not exist by default | Inject synthetic driver rules via user-defined `f_driver_decline` and `f_driver_repos` |
| Closed-loop offer application needs careful MaaSSim internals | Start with shadow `f_match` that logs PACT decisions but calls default `f_match` |

## FleetPy Fit

Useful properties from upstream repo:

| FleetPy component | Why it helps |
|---|---|
| `FleetControlBase` | Strong operator abstraction for assignment and vehicle plans |
| `user_request`, `assign_vehicle_plan`, `time_trigger` | Formal control points for dispatch decisions |
| `FleetPy_gym.py` / `RLBatchOfferSimulation` | Existing RL-style step/reset pathway |
| Large-scale studies and benchmark data | Better eventual ecological validity |
| Output files for user/operator stats | Strong KPI analysis pipeline |

Why not first: PACT would need a custom FleetPy operator or RL simulation environment wrapper. That is the right long-term interface, but it is a bigger first step than MaaSSim's user-defined `f_match`.

## Proposed Work Plan

### Phase 0: Freeze current benchmark

Done as a non-destructive snapshot under `_archive/courier_dispatch_rules_v1_20260709/`.

### Phase 1: MaaSSim shadow adapter

1. Install/clone MaaSSim in an external environment.
2. Run MaaSSim default tutorial or `glance.json` smoke.
3. Use `llm_courier_dispatch_maassim.adapter.make_shadow_match_function` to log queue snapshots while MaaSSim keeps default matching.
4. Export snapshots to `analysis/courier_dispatch_maassim/`.
5. Check that the extracted candidate features are enough for `avoid_long`, `zone_loyal`, `home_pull`, and `surge_only` proxies.

### Phase 2: Synthetic hidden rules inside MaaSSim

1. Add driver-specific latent rules in MaaSSim vehicle attributes.
2. Implement `f_driver_decline` from those rules.
3. Update PACT posterior from neutral MaaSSim driver events.
4. Report P(true), rule accuracy, and realized KPIs in shadow mode.

### Phase 3: Closed-loop MaaSSim PACT

1. Implement `apply_assignment` to create offers from PACT-selected driver-request pairs.
2. Compare PACT+, LLM-PSRL-verbal, random, and MaaSSim nearest-vehicle default.
3. Use small queues first to compute oracle regret over candidate pairs.
4. Scale to richer demand only after semantics are stable.

### Phase 4: FleetPy second-stage integration

1. Implement a `PACTFleetControl` module extending FleetPy's fleet-control lifecycle.
2. Use FleetPy's existing RL/Gym wrapper only if we want a coarse action-space baseline.
3. Keep FleetPy for stronger large-scale mobility claims, not for the first proof of concept.

## Local Smoke Status 2026-07-09

MaaSSim was cloned to `external/maassim` and imported through `PYTHONPATH`.

Light dependencies installed into the current uv environment:

```powershell
uv pip install dotmap simpy osmnx exmas==0.9.99 scipy scikit-learn
```

Compatibility patches applied only inside the external MaaSSim clone:

| File | Patch |
|---|---|
| `external/maassim/MaaSSim/utils.py` | Compatibility wrapper for `osmnx.distance.nearest_nodes` replacing old `get_nearest_node`; vehicle generation off-by-one fix for modern pandas |
| `external/maassim/MaaSSim/shared.py` | `np.warnings` compatibility for ExMAS and `osmnx.distance.get_nearest_node` shim before importing ExMAS |
| `external/maassim/MaaSSim/pool_price.py` | Guard non-shared requests without `rides` attribute |
| `external/maassim/MaaSSim/performance.py` | Guard non-shared KPI post-processing without `sblts.rides.indexes_orig` |

Smoke command:

```powershell
$env:PYTHONPATH="$PWD\external\maassim;$PWD"
uv run python scripts/run_maassim_shadow_smoke.py --config external\maassim\MaaSSim\data\config.json --root-path external\maassim\MaaSSim --out analysis\courier_dispatch_maassim\shadow_queue_snapshots.jsonl
```

Result:

| Metric | Value |
|---|---:|
| MaaSSim runs | 1 |
| Queue snapshots | 45 |
| Non-empty queue snapshots | 20 |
| Max candidate driver-request pairs in a snapshot | 5 |
| Output | `analysis/courier_dispatch_maassim/shadow_queue_snapshots.jsonl` |

Example extracted candidate:

```json
{"driver_id": 1, "request_id": 0, "driver_position": "550771675", "origin": "550771714", "destination": "1402824249", "wait_time": 41.0, "travel_time": 36.0, "fare": 0.369, "distance": 369.0, "time": 0.0}
```

Mapped CourierDispatch-style features from that offer:

```json
{"long_trip": 0, "leaves_zone": 0, "home_ward": 0, "surge": 1, "pay": 0.369, "after_deadline": 0, "congestion": 0.0, "menu_long_trip": 0, "menu_leaves_zone": 0, "menu_home_ward": 0, "menu_surge": 0, "menu_pay": 0.369}
```

This confirms the first bridge: MaaSSim platform queues can be observed and converted into a candidate-assignment matrix without changing MaaSSim's default matching outcome.

PACT shadow policy smoke also completed:

```powershell
$env:PYTHONPATH="$PWD\external\maassim;$PWD"
uv run python scripts/run_maassim_shadow_smoke.py --config external\maassim\MaaSSim\data\config.json --root-path external\maassim\MaaSSim --policy pact --beta 0.25 --out analysis\courier_dispatch_maassim\pact_shadow_queue_snapshots.jsonl
```

| Metric | Value |
|---|---:|
| Queue snapshots | 45 |
| Snapshots with a PACT shadow assignment | 20 |
| Total evaluated candidate assignments | 61 |
| Max evaluated assignments in one snapshot | 5 |
| Output | `analysis/courier_dispatch_maassim/pact_shadow_queue_snapshots.jsonl` |

First PACT shadow assignment diagnostic:

```json
{"assignment": {"1": 0}, "objective": 0.44735648250666743, "expected_reward": 0.4440465862683724, "bonus": 0.013239584953180061, "evaluated_assignments": 1, "match_count": 1, "candidate_count": 1}
```

This confirms the second bridge: the existing PACT+/factored-value layer can consume MaaSSim candidate offers and produce legal shadow assignments. It still does not intervene in MaaSSim's default matching.

Synthetic hidden-rule posterior smoke completed in stable shadow mode:

```powershell
$env:PYTHONPATH="$PWD\external\maassim;$PWD"
uv run python scripts/run_maassim_shadow_smoke.py --config external\maassim\MaaSSim\data\config.json --root-path external\maassim\MaaSSim --policy pact --beta 0.25 --synthetic-rules --out analysis\courier_dispatch_maassim\pact_synthetic_shadow_queue_snapshots.jsonl --posterior-out analysis\courier_dispatch_maassim\synthetic_rule_posterior.csv
```

This mode updates posterior beliefs from synthetic hidden-rule observations, but it does not let the synthetic rules control MaaSSim driver decline decisions. MaaSSim's default decline function remains active. This is deliberate: when synthetic rules were allowed to intervene directly, the older MaaSSim event logic became unstable under repeated rejected offers.

| Metric | Value |
|---|---:|
| Posterior update events | 21 |
| Drivers with posterior updates | 5 |
| Mean final P(true) | 0.228 |
| Mean final rule accuracy | 0.733 |
| Synthetic decline rate | 0.333 |
| Actual MaaSSim decline rate | 0.048 |
| Intervened in driver declines | no |
| Posterior output | `analysis/courier_dispatch_maassim/synthetic_rule_posterior.csv` |

Final per-driver recovery in the smoke:

| Driver | True type | Final P(true) | Final rule acc | Last synthetic reason |
|---:|---|---:|---:|---|
| 1 | `1001` | 0.370 | 0.810 | accept |
| 2 | `0110` | 0.010 | 0.625 | home_pull |
| 3 | `1100` | 0.070 | 0.652 | zone_loyal |
| 4 | `0011` | 0.505 | 0.872 | home_pull |
| 5 | `1010` | 0.185 | 0.706 | home_pull |

This confirms the third bridge: MaaSSim offers can be transformed into rule-feature observations, and the existing CourierDispatch posterior machinery can update and score recovery on synthetic hidden driver rules.

Controlled closed-loop PACT matcher smoke completed with synthetic rules intervening in actual MaaSSim driver declines:

```powershell
$env:PYTHONPATH="$PWD\external\maassim;$PWD"
uv run python scripts/run_maassim_shadow_smoke.py --seed 0 --config external\maassim\MaaSSim\data\config.json --root-path external\maassim\MaaSSim --policy pact --beta 0.25 --control-match --synthetic-rules --intervene-driver-rules --out analysis\courier_dispatch_maassim\pact_controlled_synthetic_queue_snapshots.jsonl --posterior-out analysis\courier_dispatch_maassim\controlled_synthetic_rule_posterior.csv
```

| Metric | Value |
|---|---:|
| Queue snapshots | 79 |
| Snapshots with controlled PACT assignment | 62 |
| Max candidate pairs in a snapshot | 5 |
| Posterior update events | 62 |
| Drivers with posterior updates | 5 |
| Mean final P(true) | 0.333 |
| Mean final rule accuracy | 0.826 |
| Synthetic decline rate | 0.742 |
| Actual MaaSSim decline rate | 0.742 |
| Passenger count | 20 |
| Vehicle rides | 16 |
| Vehicle rejects | 44 |
| Mean passenger wait | 143.85 |
| Mean passenger travel | 99.65 |
| Intervened in driver declines | yes |

Final per-driver recovery in the controlled smoke:

| Driver | True type | Final P(true) | Final rule acc | Last synthetic reason |
|---:|---|---:|---:|---|
| 1 | `1001` | 1.000 | 1.000 | avoid_long |
| 2 | `0110` | 0.000 | 0.720 | home_pull |
| 3 | `1100` | 0.000 | 0.750 | avoid_long |
| 4 | `0011` | 0.566 | 0.891 | home_pull |
| 5 | `1010` | 0.098 | 0.772 | avoid_long |

This confirms the fourth bridge: PACT can control MaaSSim matching in closed loop, synthetic hidden rules can affect real driver decline behavior, and posterior recovery metrics can be logged from simulator events.

First baseline smoke comparison over seeds `{0,1,2,3,4}`:

| Policy | Seeds | P(true) | Rule acc | Mean wait | Rides | Rejects | Synthetic decline |
|---|---:|---:|---:|---:|---:|---:|---:|
| Nearest | 5 | 0.199 +/- 0.030 | 0.695 +/- 0.023 | 102.8 +/- 15.4 | 19.6 +/- 0.4 | 12.0 +/- 3.8 | 0.347 |
| Random | 5 | 0.233 +/- 0.037 | 0.731 +/- 0.021 | 136.6 +/- 5.9 | 19.8 +/- 0.2 | 13.2 +/- 3.8 | 0.370 |
| PACT-proxy | 5 | 0.204 +/- 0.034 | 0.707 +/- 0.029 | 132.3 +/- 10.3 | 19.6 +/- 0.2 | 10.0 +/- 2.6 | 0.318 |
| PACT+-proxy | 5 | 0.216 +/- 0.030 | 0.720 +/- 0.020 | 133.2 +/- 10.0 | 19.6 +/- 0.2 | 11.8 +/- 2.0 | 0.369 |
| PACT | 5 | 0.198 +/- 0.029 | 0.702 +/- 0.029 | 99.8 +/- 12.7 | 19.6 +/- 0.4 | 13.0 +/- 5.0 | 0.353 |
| PACT+ | 5 | 0.198 +/- 0.029 | 0.702 +/- 0.029 | 99.8 +/- 12.7 | 19.6 +/- 0.4 | 13.0 +/- 5.0 | 0.353 |
| Oracle | 5 | 0.200 +/- 0.029 | 0.688 +/- 0.023 | 102.8 +/- 15.4 | 19.6 +/- 0.4 | 10.2 +/- 3.9 | 0.304 |

Output table: [../courier_dispatch_maassim/maassim_controlled_synthetic_baseline_summary.md](../courier_dispatch_maassim/maassim_controlled_synthetic_baseline_summary.md)

Figure: [../../figs/fig_maassim_controlled_baselines.png](../../figs/fig_maassim_controlled_baselines.png)

Readout: this first smoke is useful as an integration check, not a final performance result. The current PACT scorer now has the lowest mean wait, which confirms the diagnosis that the previous performance issue was objective mismatch rather than simulator connection failure. PACT and PACT+ still do not separate because candidate sets are small and the exploration bonus rarely changes the selected assignment.

Batch-matching smoke with `nP=40`, `nV=8`, and `batch_time=120`:

| Policy | Seeds | P(true) | Rule acc | Mean wait | Rides | Rejects | Synthetic decline |
|---|---:|---:|---:|---:|---:|---:|---:|
| Nearest | 5 | 0.214 +/- 0.023 | 0.742 +/- 0.007 | 167.5 +/- 6.9 | 39.0 +/- 0.4 | 24.2 +/- 3.2 | 0.433 |
| Random | 5 | 0.224 +/- 0.022 | 0.751 +/- 0.016 | 216.8 +/- 9.1 | 39.0 +/- 0.4 | 34.4 +/- 5.5 | 0.520 |
| PACT | 5 | 0.208 +/- 0.022 | 0.730 +/- 0.013 | 170.7 +/- 7.2 | 39.0 +/- 0.4 | 22.2 +/- 3.5 | 0.409 |
| PACT+ | 5 | 0.208 +/- 0.022 | 0.728 +/- 0.013 | 170.7 +/- 7.2 | 39.0 +/- 0.4 | 22.0 +/- 3.6 | 0.406 |
| Oracle | 5 | 0.198 +/- 0.020 | 0.705 +/- 0.018 | 170.2 +/- 7.4 | 39.2 +/- 0.5 | 16.8 +/- 4.0 | 0.336 |

Batch output table: [../courier_dispatch_maassim/maassim_batch_controlled_synthetic_baseline_summary.md](../courier_dispatch_maassim/maassim_batch_controlled_synthetic_baseline_summary.md)

Batch figure: [../../figs/fig_maassim_batch_controlled_baselines.png](../../figs/fig_maassim_batch_controlled_baselines.png)

Batch readout: increasing queue depth makes Random clearly worse and shows that PACT reduces rejects. Mean wait is still slightly better for nearest, which points to a specific remaining tuning problem: the score penalizes rejection risk enough to lower rejects, but not yet in the right balance to dominate nearest on wait.

KPI calibration sweep over `wait_weight in {0.04,0.08,0.12}`, `reject_penalty in {0,0.25,0.5}`, and `fare_weight in {0,0.5}`:

| Best target | Setting | Value |
|---|---|---:|
| Lowest mean wait | `wait_weight=0.12`, `reject_penalty=0.0`, `fare_weight=0.0` | 167.6 |
| Fewest rejects | `wait_weight=0.04`, `reject_penalty=0.25`, `fare_weight=0.5` | 23.0 |

Calibration output table: [../courier_dispatch_maassim/maassim_kpi_calibration_sweep.md](../courier_dispatch_maassim/maassim_kpi_calibration_sweep.md)

Calibration heatmap: [../../figs/fig_maassim_kpi_calibration_sweep.png](../../figs/fig_maassim_kpi_calibration_sweep.png)

Calibration readout: wait-first tuning nearly matches nearest on wait but does not robustly beat it. Reject-aware tuning reduces rejects modestly. This makes the next scientific question sharper: on the tiny Nootdorp scenario, nearest is already a strong wait-time heuristic, so PACT's advantage needs either richer queue depth, future-aware simulator value, or a hidden-rule setup where reject avoidance has larger downstream value.

Persona v2 activates both driver and passenger personas.

| Persona side | Hidden bits | Role |
|---|---|---|
| Driver | `avoid_long`, `zone_loyal`, `home_pull`, `surge_sensitive` | Repeated type inference and dispatch value |
| Passenger | `impatient`, `price_sensitive`, `delay_sensitive`, `pooling_averse` | Demand heterogeneity and local passenger utility |

Persona v2 main run (`nP=40`, `nV=8`, `batch_time=120`, random factored personas, seeds `{0,1,2,3,4,5,6,7,8,9}`):

| Policy | Driver P(true) | Driver rule acc | Mean wait | Rides | Rejects | Passenger rule acc | Passenger reject |
|---|---:|---:|---:|---:|---:|---:|---:|
| Nearest | 0.257 +/- 0.046 | 0.732 +/- 0.025 | 121.4 +/- 4.6 | 30.3 +/- 1.2 | 18.9 +/- 3.4 | 0.532 +/- 0.003 | 0.233 |
| Random | 0.321 +/- 0.054 | 0.778 +/- 0.020 | 145.9 +/- 6.0 | 25.3 +/- 0.9 | 26.3 +/- 3.2 | 0.551 +/- 0.002 | 0.354 |
| PACT | 0.268 +/- 0.040 | 0.739 +/- 0.022 | 127.6 +/- 7.0 | 29.8 +/- 1.1 | 18.5 +/- 2.8 | 0.531 +/- 0.002 | 0.230 |
| PACT+ | 0.268 +/- 0.040 | 0.739 +/- 0.022 | 127.6 +/- 7.0 | 29.8 +/- 1.1 | 18.5 +/- 2.8 | 0.531 +/- 0.002 | 0.230 |
| Oracle | 0.268 +/- 0.040 | 0.739 +/- 0.022 | 127.6 +/- 7.0 | 29.8 +/- 1.1 | 18.5 +/- 2.8 | 0.531 +/- 0.002 | 0.230 |

Persona v2 readout: the setting now better matches the paper assumptions, but it also exposes a design issue. Driver type inference is viable because drivers appear repeatedly. Passenger type inference is weak because MaaSSim passengers are mostly one-shot. Passenger personas are still useful for reward locality and demand heterogeneity, but repeated-rider scenarios are needed before passenger posterior recovery should be central. In the main run, nearest remains the strongest wait-time heuristic, while PACT is close on wait and clearly better than random.

Assumption mapping:

| Assumption | Current MaaSSim Persona v2 status | Next step |
|---|---|---|
| Type inference | Strongest for drivers; weak for one-shot passengers | Add repeated-rider scenario or focus recovery on drivers |
| Reward locality | Driver/passenger decisions depend on own persona and own offer | Keep coupling only as explicit stress test |
| Factored prior | Supported by `--persona-assignment random`, which samples driver/passenger personas independently and writes the realized type map | Use random persona assignment for final runs |

Random factored-persona smoke with `--persona-assignment random`:

| Metric | Value |
|---|---:|
| Driver personas | 8 |
| Passenger personas | 40 |
| Mean wait | 121.35 |
| Rides | 27 |
| Driver rejects | 18 |
| Passenger rejections | 13 |
| Driver final P(true) | 0.316 |
| Driver final rule acc | 0.770 |
| Passenger final rule acc | 0.539 |

Persona config: [../courier_dispatch_maassim/persona_v2_random_smoke_personas.json](../courier_dispatch_maassim/persona_v2_random_smoke_personas.json)

Summary: [../courier_dispatch_maassim/persona_v2_random_smoke_summary.json](../courier_dispatch_maassim/persona_v2_random_smoke_summary.json)

Persona v2 main table: [../courier_dispatch_maassim/maassim_persona_v2_main_summary.md](../courier_dispatch_maassim/maassim_persona_v2_main_summary.md)

Persona v2 main figure: [../../figs/fig_maassim_persona_v2_main.png](../../figs/fig_maassim_persona_v2_main.png)

Nearest-optimality diagnostic over Persona v2 main snapshots:

| Policy | Exact-match rate to immediate wait oracle | Extra wait / snapshot |
|---|---:|---:|
| Nearest | 0.906 | 3.06 +/- 1.71 |
| Random | 0.257 | 115.74 +/- 5.44 |
| PACT | 0.994 | 0.00 +/- 0.00 |
| PACT+ | 0.990 | 0.00 +/- 0.00 |
| Oracle | 0.994 | 0.00 +/- 0.00 |

Diagnostic table: [../courier_dispatch_maassim/maassim_nearest_optimality_diagnostic.md](../courier_dispatch_maassim/maassim_nearest_optimality_diagnostic.md)

Readout: nearest is close to immediate pickup-wait optimal in its own trajectory, but PACT is also immediate-wait optimal in its own trajectory. The mean-wait gap in the main table is therefore a dynamic closed-loop effect, not a one-step assignment mistake.

Common-state replay evaluation fixes the exogenous queue snapshots to the nearest Persona v2 main trajectory and evaluates every policy on the same saved persona maps.

| Policy | Oracle-match | Extra wait / snapshot | Served | Driver rejects | Passenger rejects |
|---|---:|---:|---:|---:|---:|
| Wait-oracle | 1.000 | 0.00 +/- 0.00 | 29.4 | 25.4 | 9.3 |
| Nearest | 0.906 | 3.06 +/- 1.71 | 30.4 | 26.0 | 9.2 |
| Random | 0.231 | 108.86 +/- 6.49 | 20.4 | 30.6 | 14.6 |
| PACT | 0.991 | 0.00 +/- 0.00 | 29.6 | 25.3 | 9.2 |
| PACT+ | 0.988 | 0.00 +/- 0.00 | 29.7 | 25.2 | 9.2 |
| Oracle | 0.991 | 0.00 +/- 0.00 | 29.6 | 25.3 | 9.2 |

Replay table: [../courier_dispatch_maassim/maassim_common_state_replay_summary.md](../courier_dispatch_maassim/maassim_common_state_replay_summary.md)

Replay figure: [../../figs/fig_maassim_common_state_replay.png](../../figs/fig_maassim_common_state_replay.png)

Replay readout: nearest is not literally optimal on the same candidate states; it pays about `3.06` extra seconds of pickup wait per active snapshot. PACT, PACT+, and Oracle are effectively immediate-wait-oracle on this replay. The remaining closed-loop mean-wait gap is therefore caused by trajectory/state-distribution effects rather than PACT choosing worse matches in a fixed queue.

PACT persona-mechanism replay keeps the same common states but changes only the driver-persona belief source used inside PACT.

| Variant | Belief source | Utility | Served | Driver rejects | Driver accept | Policy rule acc |
|---|---|---:|---:|---:|---:|---:|
| PACT-prior | uniform prior | 11.11 +/- 10.74 | 29.8 | 25.1 | 0.635 | 0.500 |
| PACT-shuffled | learned posterior, shuffled across drivers | 6.87 +/- 9.55 | 29.0 | 26.5 | 0.609 | 0.521 |
| PACT | learned posterior | 27.61 +/- 11.65 | 33.3 | 18.5 | 0.740 | 0.720 |
| Oracle | true hidden persona | 38.92 +/- 11.17 | 34.7 | 13.2 | 0.822 | 1.000 |

Mechanism table: [../courier_dispatch_maassim/maassim_pact_persona_mechanism_summary.md](../courier_dispatch_maassim/maassim_pact_persona_mechanism_summary.md)

Mechanism figure: [../../figs/fig_maassim_pact_persona_mechanism.png](../../figs/fig_maassim_pact_persona_mechanism.png)

Mechanism readout: PACT improves utility over PACT-prior by `16.50` and closes `59.3%` of the prior-to-oracle utility gap. Shuffling learned posteriors across drivers destroys the gain, which supports the claim that the improvement comes from using recovered persona beliefs attached to the correct driver.

CloudGPT LLM direct-dispatch smoke connects LLM-family policies to the same common-state replay. All LLM-family baselines see a legal one-to-one assignment menu and return JSON with `assignment_id` plus copied `candidate_ids`. The assisted `LLM+PACT-score` policy additionally receives assignment-level PACT-style expected accepts, expected driver rejects, estimated utility, and risk summaries; it is not a pure prompt baseline.

Persona-stress LLM prompt baseline comparison (`driver_reject_penalty=5.0`, `5` seeds, `20` active snapshots per seed):

| Policy | Utility | Served | Driver rejects | Driver accept | Extra wait/snapshot | LLM parse | LLM repair | LLM fallback |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Nearest | 12.70 +/- 11.83 | 19.6 | 5.4 | 0.822 | 1.66 | n/a | n/a | n/a |
| Random | -27.12 +/- 7.54 | 13.6 | 8.8 | 0.716 | 120.77 | n/a | n/a | n/a |
| LLM-PACT | 18.37 +/- 10.12 | 20.2 | 4.2 | 0.862 | 5.97 | 1.000 | 0.000 | 0.000 |
| LLM-belief | 13.47 +/- 9.94 | 19.4 | 5.0 | 0.835 | 3.06 | 1.000 | 0.000 | 0.000 |
| LLM-PSRL | 13.77 +/- 11.14 | 19.6 | 5.0 | 0.835 | 6.69 | 1.000 | 0.000 | 0.000 |
| A-ToM-0 | 12.67 +/- 11.34 | 19.6 | 5.4 | 0.822 | 1.46 | 1.000 | 0.000 | 0.000 |
| A-ToM-1 | 12.77 +/- 11.46 | 19.6 | 5.4 | 0.822 | 0.62 | 1.000 | 0.000 | 0.000 |
| ECON-BNE | 12.48 +/- 11.47 | 19.6 | 5.4 | 0.822 | 1.76 | 1.000 | 0.000 | 0.000 |
| Oracle | 36.44 +/- 5.09 | 20.6 | 0.4 | 0.989 | 18.48 | n/a | n/a | n/a |

Stress LLM prompt baseline table: [../courier_dispatch_maassim/maassim_llm_prompt_stress_s5_m20.md](../courier_dispatch_maassim/maassim_llm_prompt_stress_s5_m20.md)

Stress LLM prompt baseline figure: [../../figs/fig_maassim_llm_prompt_stress_s5_m20.png](../../figs/fig_maassim_llm_prompt_stress_s5_m20.png)

Prompt comparison: [../courier_dispatch_maassim/maassim_llm_prompt_variant_comparison.md](../courier_dispatch_maassim/maassim_llm_prompt_variant_comparison.md)

A-ToM / ECON-BNE comparison: [../courier_dispatch_maassim/maassim_llm_atom_baseline_comparison.md](../courier_dispatch_maassim/maassim_llm_atom_baseline_comparison.md)

Persona-stress comparison: [../courier_dispatch_maassim/maassim_llm_prompt_stress_comparison.md](../courier_dispatch_maassim/maassim_llm_prompt_stress_comparison.md)

Scenario-suite table: [../courier_dispatch_maassim/maassim_llm_scenario_suite_summary.md](../courier_dispatch_maassim/maassim_llm_scenario_suite_summary.md)

Scenario-suite figure: [../../figs/fig_maassim_llm_scenario_suite.png](../../figs/fig_maassim_llm_scenario_suite.png)

Animated comparison GIF: [../../figs/fig_maassim_llm_prompt_stress_comparison.gif](../../figs/fig_maassim_llm_prompt_stress_comparison.gif)

Fig5-style policy trace GIF: [../../figs/fig_maassim_fig5_policy_trace_comparison.gif](../../figs/fig_maassim_fig5_policy_trace_comparison.gif)

People-and-cars policy replay GIF: [../../figs/fig_maassim_people_cars_llm_pact_vs_psrl.gif](../../figs/fig_maassim_people_cars_llm_pact_vs_psrl.gif)

Full smaller A-ToM smoke table: [../courier_dispatch_maassim/maassim_llm_atom_baselines_s2_m12.md](../courier_dispatch_maassim/maassim_llm_atom_baselines_s2_m12.md)

LLM readout: the legal-assignment menu prompt reaches `1.000` parse rate with `0.000` repair and fallback rates across LLM-PACT, LLM-belief, LLM-PSRL, A-ToM, and ECON-BNE. Under persona stress, LLM-PACT is higher than every pure LLM prompt baseline: `18.37` vs `13.77` for LLM-PSRL, `13.47` for LLM-belief, and `12.48-12.77` for A-ToM/ECON-BNE. This is the fair LLM-vs-LLM comparison; PACT itself remains a mechanism/reference policy.

Scenario-suite readout: the LLM-PACT advantage grows as the environment makes persona mistakes more consequential. The utility gap over the best pure prompt baseline is `+1.47` in the normal replay, `+4.60` under reject-cost stress, and `+39.69` under conflict-offer stress, where low-wait offers are made persona-risky.

Controlled smoke visualizations were generated:

| Figure | Description |
|---|---|
| [../../figs/fig_maassim_controlled_smoke_overview.png](../../figs/fig_maassim_controlled_smoke_overview.png) | 2x2 overview of queue dynamics, PACT assignment activity, posterior trajectories, and final recovery |
| [../../figs/fig_maassim_controlled_smoke_map.png](../../figs/fig_maassim_controlled_smoke_map.png) | Nootdorp graph with observed driver positions, request origins, and destinations |
| [../../figs/fig_maassim_controlled_vehicle_trace.png](../../figs/fig_maassim_controlled_vehicle_trace.png) | Fig5-style route trace for the most eventful vehicle |
| [../../figs/fig_maassim_controlled_smoke_animation.gif](../../figs/fig_maassim_controlled_smoke_animation.gif) | Animated replay of smoke-run vehicle positions |
| [../../figs/fig_maassim_controlled_baselines.png](../../figs/fig_maassim_controlled_baselines.png) | Baseline comparison over seeds `{0,1,2,3,4}` |
| [../../figs/fig_maassim_batch_controlled_baselines.png](../../figs/fig_maassim_batch_controlled_baselines.png) | Batch-matching baseline comparison with larger queues |
| [../../figs/fig_maassim_kpi_calibration_sweep.png](../../figs/fig_maassim_kpi_calibration_sweep.png) | KPI wait/reject calibration heatmap |
| [../../figs/fig_maassim_common_state_replay.png](../../figs/fig_maassim_common_state_replay.png) | Common-state replay comparison against the immediate wait oracle |
| [../../figs/fig_maassim_pact_persona_mechanism.png](../../figs/fig_maassim_pact_persona_mechanism.png) | PACT prior/shuffled/learned/oracle persona-mechanism replay |
| [../../figs/fig_maassim_llm_replay_smoke_s2_m12.png](../../figs/fig_maassim_llm_replay_smoke_s2_m12.png) | CloudGPT LLM direct-dispatch common-state smoke |
| [../../figs/fig_maassim_llm_replay_scored_s2_m12.png](../../figs/fig_maassim_llm_replay_scored_s2_m12.png) | CloudGPT LLM scored-menu common-state smoke |
| [../../figs/fig_maassim_llm_atom_baselines_s2_m12.png](../../figs/fig_maassim_llm_atom_baselines_s2_m12.png) | CloudGPT LLM-scored vs A-ToM and ECON-BNE common-state smoke |
| [../../figs/fig_maassim_llm_atom_core_s5_m20.png](../../figs/fig_maassim_llm_atom_core_s5_m20.png) | Scaled CloudGPT LLM+PACT-score vs A-ToM and ECON-BNE core comparison |
| [../../figs/fig_maassim_llm_prompt_stress_s5_m20.png](../../figs/fig_maassim_llm_prompt_stress_s5_m20.png) | Persona-stress LLM-PACT vs LLM-belief, LLM-PSRL, A-ToM, and ECON-BNE comparison |
| [../../figs/fig_maassim_llm_scenario_suite.png](../../figs/fig_maassim_llm_scenario_suite.png) | Scenario suite showing LLM-PACT gap growth from normal to reject-stress to conflict-offer environments |
| [../../figs/fig_maassim_llm_prompt_stress_comparison.gif](../../figs/fig_maassim_llm_prompt_stress_comparison.gif) | Animated persona-stress LLM-PACT vs prompt-baseline comparison for README/GitHub presentation |
| [../../figs/fig_maassim_fig5_policy_trace_comparison.gif](../../figs/fig_maassim_fig5_policy_trace_comparison.gif) | Focused Fig5-style route trace window where LLM-PACT has fewer rejected pickup attempts than LLM-PSRL, A-ToM-1, and ECON-BNE |
| [../../figs/fig_maassim_people_cars_llm_pact_vs_psrl.gif](../../figs/fig_maassim_people_cars_llm_pact_vs_psrl.gif) | Full-episode people-and-cars replay in the MaaSSim README style: LLM-PACT has fewer driver-reject Xs than LLM-PSRL (4 vs 7) |

Reproduce with:

```powershell
uv run python scripts/plot_maassim_integration_smoke.py
```

Performance caveat: the early controlled runs are structured PACT/MaaSSim integration smokes with synthetic hidden rules. The LLM direct-dispatch smoke is now connected separately through common-state replay. The prompt format is stable across LLM-PACT and pure prompt baselines. LLM-PACT is assisted by PACT-style assignment scores; pure prompt baselines are LLM-belief, LLM-PSRL, A-ToM-0, A-ToM-1, and ECON-BNE. The persona-stress run is a stronger LLM-vs-LLM diagnostic, but still not a final closed-loop MaaSSim significance claim.

## Immediate Next Command Once MaaSSim Is Available

```powershell
uv run python -c "import MaaSSim; print(MaaSSim.__file__)"
```

If that import works, run the shadow smokes above. The next task after the completed controlled synthetic smoke is to add baseline comparison under the same controlled matcher interface: MaaSSim nearest-vehicle default, Random, PACT, and PACT+.
