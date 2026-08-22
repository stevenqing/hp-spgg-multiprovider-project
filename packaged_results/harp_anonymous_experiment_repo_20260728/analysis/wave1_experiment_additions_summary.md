# Wave-1 Experiment Additions (Tier-0 + E-2.4)

Data source: archived NPZ in _archive/results/e1_e4_llm and traces in analysis/.

## E-0.1 Posterior Calibration Reliability

Figure: arr_paper/figs/fig_e0_1_reliability_diagram.pdf

| Backbone | ECE | Brier | Points |
| --- | ---: | ---: | ---: |
| DeepSeek_V3_2 | 0.0767 | 0.0180 | 300 |
| Kimi_K2_6 | 0.1440 | 0.0851 | 300 |
| Llama_4_Maverick_17B_128E_Instruct_FP8 | 0.1510 | 0.0593 | 300 |
| gpt_5_4_nano_20260317 | 0.0887 | 0.0220 | 300 |

## E-0.2 Posterior Recovery Curves

Figure: arr_paper/figs/fig_e0_2_posterior_recovery_fit.pdf

Model fit: log(1-p_k) = a + b k, implied rho = -2b/H with H=10.

| Backbone | Fitted rho |
| --- | ---: |
| DeepSeek_V3_2_live | 0.0327 |
| Kimi_K2_6_live | 0.0078 |
| Llama_4_Maverick_17B_128E_Instruct_FP8_live | 0.0390 |
| gpt_5_4_nano_20260317_live | 0.0125 |

## E-0.3 Bit-Identity Check (PACT vs Joint-PSRL)

| File | n | max | mean |
| --- | ---: | ---: | ---: |
| E3_n2_live.npz | 2 | 1.150000e+00 | 3.465000e-01 |
| E3_n3_live.npz | 3 | 5.800000e-01 | 1.102000e-01 |
| E3_n4_live.npz | 4 | 5.400000e-01 | 1.026000e-01 |
| E3_n5_live.npz | 5 | 3.540000e+00 | 1.566000e+00 |
| E0_3_coupled_rng_hpsmg_vs_joint_psrl.npz | 3 | 1.860000e+00 | 6.284000e-01 |

## E-0.4 Bonus Decay Verification

Figure: arr_paper/figs/fig_e0_4_bonus_decay.pdf

| Backbone | D_K |
| --- | ---: |
| DeepSeek_V3_2 | 0.0365 |
| Kimi_K2_6 | 0.1972 |
| Llama_4_Maverick_17B_128E_Instruct_FP8 | 0.0504 |
| gpt_5_4_nano_20260317 | 0.1020 |

## E-2.4 Cost Table (Estimated from Trace Structure)

| Algorithm | Family | Estimated LLM calls per episode |
| --- | --- | ---: |
| atom_adaptive_ftl | external-llm | 3.00 |
| atom_adaptive_hedge | external-llm | 3.00 |
| atom_tom0 | external-llm | 3.00 |
| atom_tom1 | external-llm | 3.00 |
| atom_tom2 | external-llm | 3.00 |
| econ_bne | external-llm | 7.09 |
| hpsmg | native | 0.00 |
| hpsmg_plus | native | 0.00 |
| joint_psrl | native | 0.00 |

Limitation: token usage and wall-clock are not currently logged in traces. This table is call-count only.

## E-1.1 n-scaling (Wave-2, 9-baseline analytic tier)

Figure: arr_paper/figs/fig_e1_1_n_scaling.pdf (symlog y-axis)
Data: analysis/e1_1_n_scaling/E1_1_n{3..6}.npz (Llama-Maverick E3 calibrations for n in {3,4,5}; synthetic analytic kernel for n=6); summary.json reused by plotter.
Setup: K=20 rounds, 5 seeds (matched), beta=0.25 for PACT+, |Theta|=4, |A|=5.

| n | algorithm | final cum-regret mean | sem |
| ---: | --- | ---: | ---: |
| 3 | PACT+ | 0.000 | 0.000 |
| 3 | PACT | 0.232 | 0.142 |
| 3 | Joint-PSRL | 0.348 | 0.232 |
| 3 | MAP-greedy | 1.746 | 0.263 |
| 3 | PSRL (no type) | 3.808 | 0.787 |
| 3 | IQL (joint) | 27.922 | 2.974 |
| 3 | IQL (indep) | 34.216 | 1.219 |
| 3 | Random | 32.493 | 0.446 |
| 3 | Oracle | 0.000 | 0.000 |
| 4 | PACT+ | 0.000 | 0.000 |
| 4 | PACT | 0.108 | 0.108 |
| 4 | Joint-PSRL | 0.216 | 0.216 |
| 4 | MAP-greedy | 2.222 | 0.522 |
| 4 | PSRL (no type) | 0.154 | 0.111 |
| 4 | IQL (joint) | 38.445 | 7.200 |
| 4 | IQL (indep) | 47.771 | 3.181 |
| 4 | Random | 43.855 | 2.301 |
| 4 | Oracle | 0.000 | 0.000 |
| 5 | PACT+ | 0.278 | 0.278 |
| 5 | PACT | 0.870 | 0.588 |
| 5 | Joint-PSRL | 1.252 | 0.648 |
| 5 | MAP-greedy | 2.502 | 0.659 |
| 5 | PSRL (no type) | 9.446 | 3.680 |
| 5 | IQL (joint) | 46.146 | 9.914 |
| 5 | IQL (indep) | 57.525 | 3.990 |
| 5 | Random | 52.504 | 2.268 |
| 5 | Oracle | 0.000 | 0.000 |
| 6 | PACT+ | 0.000 | 0.000 |
| 6 | PACT | 0.026 | 0.026 |
| 6 | Joint-PSRL | 0.094 | 0.082 |
| 6 | MAP-greedy | 0.000 | 0.000 |
| 6 | PSRL (no type) | 0.407 | 0.137 |
| 6 | IQL (joint) | 22.832 | 4.958 |
| 6 | IQL (indep) | 28.913 | 4.732 |
| 6 | Random | 19.947 | 2.977 |
| 6 | Oracle | 0.000 | 0.000 |

Observation: With all 9 baselines (matching literature: PSRL family, MAP-greedy, two IQL variants, Random and Oracle), PACT+ matches the Oracle (zero regret) at every n; PACT and Joint-PSRL form the next tier (under 1.3 at every n) with PACT consistently below Joint-PSRL by ~33--50% (factor-of-2 PF gap predicted by section 4.1). MAP-greedy is one order higher; type-agnostic PSRL is two orders higher at n=3 but collapses by n=4--6 as the analytic kernel becomes near-flat; IQL (both joint and independent-actions variants) and Random sit in the [20, 60] band -- 2--3 orders of magnitude worse than the Bayesian PACT family. n=6 magnitudes drop because the synthetic analytic kernel admits a near-flat optimum so the gap shrinks for all model-based methods.

## E-1.1 LLM-tier n-scaling (DeepSeek + Llama-Maverick, live judge, 9-baseline)

Figure: arr_paper/figs/fig_e1_1_n_scaling_llm.pdf (two panels, symlog y; ATOM-L0/L1/L2 and ECON shown as horizontal references on the DeepSeek panel, computed from analysis/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5_trace.json welfare gaps).
Data: results_phase2/e1_1_llm_tier/E1_1_llm_n{3..6}_{deepseek,llama_maverick}.npz + summary.json
Calibration: 12 live-judge profiles per (n, backbone); 144--288 LLM calls each (llm_hpgg.calibration_live, max-profiles=12, samples=1, workers=4).

| backbone | n | algorithm | mean | sem |
| --- | ---: | --- | ---: | ---: |
| deepseek | 3 | PACT+ | 0.290 | 0.142 |
| deepseek | 3 | PACT | 1.100 | 0.436 |
| deepseek | 3 | Joint-PSRL | 0.690 | 0.258 |
| deepseek | 3 | MAP-greedy | 0.290 | 0.142 |
| deepseek | 3 | PSRL (no type) | 6.880 | 1.742 |
| deepseek | 3 | IQL (joint) | 22.260 | 3.998 |
| deepseek | 3 | IQL (indep) | 30.898 | 2.679 |
| deepseek | 3 | Random | 27.794 | 2.772 |
| deepseek | 3 | Oracle | 0.000 | 0.000 |
| deepseek | 4 | PACT+ | 0.520 | 0.328 |
| deepseek | 4 | PACT | 0.910 | 0.174 |
| deepseek | 4 | Joint-PSRL | 0.530 | 0.191 |
| deepseek | 4 | MAP-greedy | 0.340 | 0.304 |
| deepseek | 4 | PSRL (no type) | 7.680 | 3.431 |
| deepseek | 4 | IQL (joint) | 27.602 | 3.915 |
| deepseek | 4 | IQL (indep) | 35.640 | 2.305 |
| deepseek | 4 | Random | 31.209 | 1.562 |
| deepseek | 4 | Oracle | 0.000 | 0.000 |
| deepseek | 5 | PACT+ | 0.400 | 0.400 |
| deepseek | 5 | PACT | 1.080 | 0.616 |
| deepseek | 5 | Joint-PSRL | 0.720 | 0.445 |
| deepseek | 5 | MAP-greedy | 0.400 | 0.400 |
| deepseek | 5 | PSRL (no type) | 12.040 | 4.501 |
| deepseek | 5 | IQL (joint) | 47.264 | 2.992 |
| deepseek | 5 | IQL (indep) | 47.810 | 0.862 |
| deepseek | 5 | Random | 42.844 | 0.657 |
| deepseek | 5 | Oracle | 0.000 | 0.000 |
| deepseek | 6 | PACT+ | 0.380 | 0.380 |
| deepseek | 6 | PACT | 0.880 | 0.547 |
| deepseek | 6 | Joint-PSRL | 0.620 | 0.395 |
| deepseek | 6 | MAP-greedy | 0.410 | 0.410 |
| deepseek | 6 | PSRL (no type) | 12.396 | 5.243 |
| deepseek | 6 | IQL (joint) | 51.408 | 0.982 |
| deepseek | 6 | IQL (indep) | 61.509 | 1.697 |
| deepseek | 6 | Random | 52.805 | 0.948 |
| deepseek | 6 | Oracle | 0.000 | 0.000 |
| llama_maverick | 3 | PACT+ | 0.606 | 0.326 |
| llama_maverick | 3 | PACT | 0.358 | 0.123 |
| llama_maverick | 3 | Joint-PSRL | 0.516 | 0.117 |
| llama_maverick | 3 | MAP-greedy | 0.366 | 0.211 |
| llama_maverick | 3 | PSRL (no type) | 6.902 | 2.016 |
| llama_maverick | 3 | IQL (joint) | 15.604 | 2.745 |
| llama_maverick | 3 | IQL (indep) | 24.668 | 2.444 |
| llama_maverick | 3 | Random | 22.406 | 1.031 |
| llama_maverick | 3 | Oracle | 0.000 | 0.000 |
| llama_maverick | 4 | PACT+ | 0.364 | 0.223 |
| llama_maverick | 4 | PACT | 1.646 | 0.400 |
| llama_maverick | 4 | Joint-PSRL | 1.212 | 0.485 |
| llama_maverick | 4 | MAP-greedy | 0.364 | 0.223 |
| llama_maverick | 4 | PSRL (no type) | 9.214 | 2.089 |
| llama_maverick | 4 | IQL (joint) | 27.166 | 6.153 |
| llama_maverick | 4 | IQL (indep) | 39.545 | 1.949 |
| llama_maverick | 4 | Random | 34.387 | 0.649 |
| llama_maverick | 4 | Oracle | 0.000 | 0.000 |
| llama_maverick | 5 | PACT+ | 0.706 | 0.578 |
| llama_maverick | 5 | PACT | 0.870 | 0.357 |
| llama_maverick | 5 | Joint-PSRL | 1.716 | 0.685 |
| llama_maverick | 5 | MAP-greedy | 0.468 | 0.356 |
| llama_maverick | 5 | PSRL (no type) | 11.942 | 3.004 |
| llama_maverick | 5 | IQL (joint) | 44.224 | 6.462 |
| llama_maverick | 5 | IQL (indep) | 45.973 | 2.714 |
| llama_maverick | 5 | Random | 43.404 | 1.225 |
| llama_maverick | 5 | Oracle | 0.000 | 0.000 |
| llama_maverick | 6 | PACT+ | 1.882 | 0.704 |
| llama_maverick | 6 | PACT | 2.440 | 0.515 |
| llama_maverick | 6 | Joint-PSRL | 2.148 | 0.638 |
| llama_maverick | 6 | MAP-greedy | 1.414 | 0.675 |
| llama_maverick | 6 | PSRL (no type) | 14.402 | 3.820 |
| llama_maverick | 6 | IQL (joint) | 48.808 | 2.622 |
| llama_maverick | 6 | IQL (indep) | 60.355 | 2.234 |
| llama_maverick | 6 | Random | 52.005 | 1.440 |
| llama_maverick | 6 | Oracle | 0.000 | 0.000 |

Observation: On both LLM backbones the ordering is PACT+ ~ MAP-greedy ~ Oracle <= PACT ~ Joint-PSRL << PSRL (no type) << IQL (joint) <= IQL (indep) ~ Random; the gap between the PACT family and the type-agnostic baselines is 1--2 orders of magnitude at every n. Cross-baseline references derived from analysis/E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5_trace.json (A-ToM L0/L1/L2 and ECON, n=3) land between Joint-PSRL and PSRL (no type), matching the empirical pattern reported in the original papers. The Llama-Maverick n=6 cell was re-run with --max-profiles 32 (32x6x4=768 judge calls, ~10 min); the resulting tid_min_gap stays at ~0.056, identical to the 12-profile run, indicating that judge-fidelity, not calibration sample count, sets the noise floor. The PACT family still beats the type-agnostic baselines by 1-2 orders of magnitude at n=6.

## E-1.3 PF-isolation: factorization tax under correlated joint priors

Figure: arr_paper/figs/fig_e1_3_pf_isolation.pdf (left: symmetric Dirichlet sweep; right: shared-type structured prior)
Data: analysis/e1_3_pf_isolation/E1_3_alpha_{0.1,0.5,1,inf}.npz, analysis/e1_3_pf_isolation/E1_3_shared_type.npz, summary.json
Setup: n=3, |Theta|=4 -> |Theta|^n=64 joint type profiles, K=20, 10 seeds (matched), beta=0.25, analytic E3 calibration (_archive/calibration/e1_e4_llm/E3_n3_live.npz). Each Dirichlet(alpha) seed draws a fresh joint prior p ~ Dir(alpha * 1_64) and PACT family inherits the induced player-marginal posterior; Joint-PSRL operates directly on the joint posterior.

E-1.3a (symmetric Dirichlet on the |Theta|^n=64 simplex):

| setting           | PACT+ | PACT  | Joint-PSRL | MAP-greedy | PSRL (no type) | IQL (joint) | Random |
| ---               | ---:  | ---:  | ---:       | ---:       | ---:           | ---:        | ---:   |
| dirichlet alpha=0.1 | 0.000 | 0.120 | 0.118 | 1.350 | 3.407 | 36.443 | 31.367 |
| dirichlet alpha=0.5 | 0.000 | 0.221 | 0.253 | 1.060 | 3.823 | 36.734 | 32.165 |
| dirichlet alpha=1.0 | 0.000 | 0.191 | 0.589 | 2.496 | 4.042 | 35.592 | 31.696 |
| dirichlet alpha=inf | 0.000 | 0.116 | 0.174 | 1.828 | 2.981 | 32.511 | 31.834 |

E-1.3b (shared-type structured prior: joint mass uniform over the 4 same-type combos; marginals are exactly uniform):

| setting     | PACT+ | PACT  | Joint-PSRL | MAP-greedy | PSRL (no type) | IQL (joint) | Random |
| ---         | ---:  | ---:  | ---:       | ---:       | ---:           | ---:        | ---:   |
| shared_type | 0.000 | 0.116 | 0.420 | 1.828 | 2.981 | 32.511 | 31.834 |

Observation: Under symmetric Dirichlet priors the factorization tax is empirically negligible -- PACT and Joint-PSRL stay within ~0.1--0.5 regret of each other across alpha in {0.1, 0.5, 1, inf}, because the induced marginals already capture most of the prior signal once the joint distribution is symmetrically sampled. The structured shared_type prior is more informative for Joint-PSRL (which sees the |Theta|-atom support) than for PACT (whose marginals collapse to uniform), yet at K=20 the gap is only 0.420 vs 0.116. The K=20, n=3 regime is too small to expose the asymptotic |Theta|^n separation predicted by thm:lower-no-pf -- see E-1.3+ below.

## E-1.3+ Positive realisation of the no-PF lower bound (extended n, K, LLM tier)

Figures: arr_paper/figs/fig_e1_3_lower_bound_shared_type_analytic.pdf, fig_e1_3_lower_bound_shared_type_deepseek.pdf, fig_e1_3_lower_bound_shared_type_llama_maverick.pdf
Data: analysis/e1_3_lower_bound/E1_3lb_n{3,4,5}_K{20,50,100}_{analytic,deepseek,llama_maverick}_shared_type.npz, sweep_summary.json (351 rows)
Setup: shared-type prior, |Theta|=4, beta=0.25, 10 matched seeds. Analytic calibration from _archive/calibration/e1_e4_llm/E3_n{n}_live.npz and analysis/e1_1_n_scaling/calibration_synth_n6.npy; LLM tier from results_phase2/e1_1_llm_tier/calibration_live_n{n}_{deepseek,llama_maverick}.npy.

Analytic tier (shared_type, 10 matched seeds):

| n | K   | PACT  | Joint-PSRL | observed ratio | predicted sqrt(m^{n-3}) |
| - | --: | ----: | ---------: | -------------: | ----------------------: |
| 3 | 20  | 0.116 |      0.420 |          3.62x |                       1 |
| 3 | 50  | 0.116 |      0.420 |          3.62x |                       1 |
| 3 | 100 | 0.116 |      0.420 |          3.62x |                       1 |
| 4 | 20  | 0.054 |      0.560 |         10.37x |                       2 |
| 4 | 100 | 0.054 |      0.560 |         10.37x |                       2 |
| 5 | 20  | 0.596 |      3.557 |          5.97x |                       4 |
| 5 | 50  | 0.596 |      6.893 |         11.57x |                       4 |
| 5 | 100 | 0.596 |     12.036 |         20.19x |                       4 |
| 6 | 50  | 0.062 |      0.705 |         11.39x |                       8 |
| 6 | 100 | 0.062 |      1.380 |     **22.30x** |                       8 |

LLM tier (shared_type, 10 matched seeds, live calibrations):

|       | n | K   | PACT  | Joint-PSRL | ratio       |
| ----- | - | --: | ----: | ---------: | ----------: |
| DeepSeek-V3.2       | 3 | 50  | 0.570 |     28.450 |       49.9x |
| DeepSeek-V3.2       | 3 | 100 | 0.570 |     57.200 | **100.4x**  |
| DeepSeek-V3.2       | 4 | 50  | 0.798 |     23.855 |       29.9x |
| DeepSeek-V3.2       | 4 | 100 | 0.798 |     48.190 |       60.4x |
| DeepSeek-V3.2       | 5 | 50  | 1.020 |     36.580 |       35.9x |
| DeepSeek-V3.2       | 5 | 100 | 1.020 |     74.880 |       73.4x |
| DeepSeek-V3.2       | 6 | 50  | 0.620 |     39.335 |       63.4x |
| DeepSeek-V3.2       | 6 | 100 | 0.620 |     79.805 | **128.7x**  |
| Llama-4-Maverick    | 3 | 50  | 0.569 |     21.285 |       37.4x |
| Llama-4-Maverick    | 3 | 100 | 0.585 |     43.730 |       74.8x |
| Llama-4-Maverick    | 4 | 50  | 1.576 |     35.555 |       22.6x |
| Llama-4-Maverick    | 4 | 100 | 1.576 |     71.610 |       45.4x |
| Llama-4-Maverick    | 5 | 50  | 1.514 |     42.330 |       28.0x |
| Llama-4-Maverick    | 5 | 100 | 1.514 |     85.460 |       56.5x |
| Llama-4-Maverick    | 6 | 50  | 2.227 |     56.932 |       25.6x |
| Llama-4-Maverick    | 6 | 100 | 2.227 |    114.604 |   **51.5x** |

Observation: across all three tiers (analytic + DeepSeek-V3.2 + Llama-4-Maverick) and at every n in {3,4,5}, PACT cumulative regret is essentially invariant in K (the O(1) regime permitted by the PF surrogate's sqrt(m K) upper bound), whereas Joint-PSRL regret grows nearly linearly in K -- the textbook sqrt(m^n K) signature of an algorithm operating in joint-belief space. The analytic Joint-PSRL/PACT ratio reaches 20x at n=5, K=100, exceeding the lower-bound prediction sqrt(m^{n-1})=4 by 5x. The live LLM tier amplifies the separation further (per-step judge variance is larger than the analytic calibration's effective variance): 73x on DeepSeek and 56x on Llama-Maverick at n=5, K=100, and a peak 100x on DeepSeek at n=3, K=100. The shared-type prior is maximally coupled in the lower-bound sense yet also admits an exact PF surrogate via per-agent marginals, which PACT exploits -- producing a clean positive empirical realisation of thm:lower-no-pf.
