# HP-SPGG Analytic Scaling Run Report

Generated UTC: 2026-07-25T03:09:13.508005+00:00.
NPZ artifact wall-clock span: 2396.896 seconds (a lower bound when reconstructed in a later summarize pass).
Provider calls: 0.

## Completion

- Requested sweep cells: 19.
- Unique $(n,m)$ cells: 17.
- Cell-method summaries: 95.
- NPZ files: 950.
- Planner action count read from substrate: 5.
- Joint frontier for S3: {'largest_feasible_n': 6, 'first_infeasible_n': 7}.

## Type separation

| m | rho_hat | threshold applies | synthesis |
|---:|---:|---|---|
| 4 | 9.41900515e-08 | False | retained four-archetype Fischbacher-Gaechter-Fehr library |
| 8 | 0.00535938724 | True | re-spaced monotone grid inside four-archetype parameter bounds |
| 16 | 0.00116960975 | True | re-spaced monotone grid inside four-archetype parameter bounds |

## Factored / explicit-joint parity

| sweep | n | m | joint feasible | PACT-Joint mean | 95% CI | max trajectory gap | action mismatches |
|---|---:|---:|---|---:|---:|---:|---:|
| s1_population_m4 | 2 | 4 | True | 0.0 | [0.0, 0.0] | 0.0 | 0 |
| s1_population_m4 | 3 | 4 | True | 0.0 | [0.0, 0.0] | 0.0 | 0 |
| s1_population_m4 | 4 | 4 | True | 0.0 | [0.0, 0.0] | 0.0 | 0 |
| s1_population_m4 | 5 | 4 | True | 0.0 | [0.0, 0.0] | 0.0 | 0 |
| s1_population_m4 | 6 | 4 | True | 0.0 | [0.0, 0.0] | 0.0 | 0 |
| s1_population_m4 | 7 | 4 | True | 0.0 | [0.0, 0.0] | 0.0 | 0 |
| s1_population_m4 | 8 | 4 | True | 0.0 | [0.0, 0.0] | 0.0 | 0 |
| s1_population_m4 | 9 | 4 | True | 0.0 | [0.0, 0.0] | 0.0 | 0 |
| s1_population_m4 | 10 | 4 | True | 0.0 | [0.0, 0.0] | 0.0 | 0 |
| s2_library_n3 | 3 | 4 | True | 0.0 | [0.0, 0.0] | 0.0 | 0 |
| s2_library_n3 | 3 | 8 | True | 0.0 | [0.0, 0.0] | 0.0 | 0 |
| s2_library_n3 | 3 | 16 | True | 0.0 | [0.0, 0.0] | 0.0 | 0 |
| s3_frontier_m16 | 2 | 16 | True | 0.0 | [0.0, 0.0] | 0.0 | 0 |
| s3_frontier_m16 | 3 | 16 | True | 0.0 | [0.0, 0.0] | 0.0 | 0 |
| s3_frontier_m16 | 4 | 16 | True | 0.0 | [0.0, 0.0] | 0.0 | 0 |
| s3_frontier_m16 | 5 | 16 | True | 0.0 | [0.0, 0.0] | 0.0 | 0 |
| s3_frontier_m16 | 6 | 16 | True | 0.0 | [0.0, 0.0] | 0.0 | 0 |
| s3_frontier_m16 | 7 | 16 | False | nan | [nan, nan] | nan | 0 |
| s3_frontier_m16 | 8 | 16 | False | nan | [nan, nan] | nan | 0 |

## Feasibility events

| sweep | n | m | method | feasible | rule |
|---|---:|---:|---|---|---|
| s1_population_m4 | 2 | 4 | joint_psrl_uniform | True | none |
| s1_population_m4 | 3 | 4 | joint_psrl_uniform | True | none |
| s1_population_m4 | 4 | 4 | joint_psrl_uniform | True | none |
| s1_population_m4 | 5 | 4 | joint_psrl_uniform | True | none |
| s1_population_m4 | 6 | 4 | joint_psrl_uniform | True | none |
| s1_population_m4 | 7 | 4 | joint_psrl_uniform | True | none |
| s1_population_m4 | 8 | 4 | joint_psrl_uniform | True | none |
| s1_population_m4 | 9 | 4 | joint_psrl_uniform | True | none |
| s1_population_m4 | 10 | 4 | joint_psrl_uniform | True | none |
| s2_library_n3 | 3 | 4 | joint_psrl_uniform | True | none |
| s2_library_n3 | 3 | 8 | joint_psrl_uniform | True | none |
| s2_library_n3 | 3 | 16 | joint_psrl_uniform | True | none |
| s3_frontier_m16 | 2 | 16 | joint_psrl_uniform | True | none |
| s3_frontier_m16 | 3 | 16 | joint_psrl_uniform | True | none |
| s3_frontier_m16 | 4 | 16 | joint_psrl_uniform | True | none |
| s3_frontier_m16 | 5 | 16 | joint_psrl_uniform | True | none |
| s3_frontier_m16 | 6 | 16 | joint_psrl_uniform | True | none |
| s3_frontier_m16 | 7 | 16 | joint_psrl_uniform | False | first_update_gt_1s |
| s3_frontier_m16 | 8 | 16 | joint_psrl_uniform | False | joint_table_gt_4GB |

## Correctness gates

```json
{
  "kernel_planner_regression": {
    "passed": true,
    "max_reward_tensor_difference": 1.1102230246251565e-16,
    "all_64_sampled_profile_actions_equal": true,
    "posterior_mean_bonus_actions_equal": true,
    "reference": "build_reward_tensor(n=3, backend=mixed, samples=1, seed=0)"
  },
  "pathwise_identity_n3_m4": {
    "passed": true,
    "actions_identical": true,
    "regrets_identical_atol_1e-8": true,
    "max_abs_regret_diff": 0.0
  },
  "oracle_sanity": {
    "passed": true,
    "max_cumulative_regret": 0.0
  },
  "psrl_notype_linearity": {
    "passed": true,
    "minimum_r_squared": 0.9968985574813005,
    "cells": {
      "s1_population_m4:n2:m4": 1.0,
      "s1_population_m4:n3:m4": 1.0,
      "s1_population_m4:n4:m4": 1.0,
      "s1_population_m4:n5:m4": 1.0,
      "s1_population_m4:n6:m4": 1.0,
      "s1_population_m4:n7:m4": 1.0,
      "s1_population_m4:n8:m4": 1.0,
      "s1_population_m4:n9:m4": 1.0,
      "s1_population_m4:n10:m4": 1.0,
      "s2_library_n3:n3:m4": 1.0,
      "s2_library_n3:n3:m8": 0.9988721636414127,
      "s2_library_n3:n3:m16": 0.9988638786644121,
      "s3_frontier_m16:n2:m16": 0.9968985574813005,
      "s3_frontier_m16:n3:m16": 0.9988638786644121,
      "s3_frontier_m16:n4:m16": 0.9980369406124701,
      "s3_frontier_m16:n5:m16": 0.9982727742649679,
      "s3_frontier_m16:n6:m16": 0.9981668752551466,
      "s3_frontier_m16:n7:m16": 0.9972244316456588,
      "s3_frontier_m16:n8:m16": 0.999144712677508
    }
  },
  "determinism": {
    "passed": true,
    "scientific_arrays_bitwise": true,
    "full_npz_reconstruction_bitwise": true,
    "timing_policy": "original measured wall-clock arrays reused because physical clocks are nondeterministic",
    "source": "analysis/hp_spgg_analytic_scaling/npz/s1_population_m4/n03_m04/pact_seed1000.npz"
  },
  "dgp_probes": {
    "passed": true,
    "rows": 17
  }
}
```

## Notes

- The repository action grid has five values, so S1 n=10 enumerates 5^10=9,765,625 profiles, not 4^10.
- Synthetic m=8 and m=16 libraries are re-spaced only after direct archetype interpolation fails rho_hat >= 1e-3.
- The m=4 library is retained unchanged even though its empirical full-grid rho_hat is below the synthetic-library threshold.
- Cells are additive; no existing experiment output or LaTeX file is modified.
## Post-render burn-in fit

- Claim (a): every feasible PACT/Joint cell is pathwise identical; S3 remains joint-feasible through n=6 and first fails at n=7.
- S1 is decision-degenerate on this retained m=4 analytic kernel: maximum mean final regret across displayed methods is 0. Its parity result is exact but not performance-separating.
- The worst n=10,m=4 cell used all 5^10 actions and completed in 1723.880s, below the 1,800s cap.
- Canonical method: PACT; uncensored OLS observations: 11.
- Fitted slope: -0.247784; intercept: 13.6432; R^2: 0.00649867.
- Under the preregistered directional criterion, this finite K=50 fit **does not support** a pooled linear relation.
- Open markers at K+1 are majority-censored cells and are excluded from OLS rather than imputed.
- Per-library 1/(rho_hat H) references are recorded in scaling_burn_in_fit.json; rho_hat is a worst-case reachable-grid margin and is not retuned to the observed trajectories.
