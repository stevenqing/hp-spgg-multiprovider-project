# HP-SPGG Claim B v3 — Locked Confirmatory Design

Status: **locked before any v3 confirmatory outcomes are generated**.

## Why the claim must be corrected

The original scaling specification proposed `(n+1) log(m)/(rho H)`. That expression is not Proposition `prop:tid-collapse`: the proposition is per-agent, its proof uses `C=m*pi_min^(-1/2)`, and simultaneous control of independent agents adds `log(n)` through a union bound rather than a linear `n` factor. With a uniform prior, `log C = log(m*sqrt(m))`.

The completed original run remains a preregistered null. The v2 stochastic pilot was used only to design this new study. Its seeds are excluded.

## Confirmatory claim

On the stochastic Gaussian analytic HP-SPGG outcome channel:

1. expected square-root posterior odds contract by the product of Hellinger affinities;
2. cumulative posterior-sampling type error is independent of the terminal episode count after burn-in;
3. operational per-agent first-passage episodes scale with `log(m*sqrt(m))/(rho_action*H)`; and
4. simultaneous all-agent first passage adds `log(n)/(rho_action*H)`, not linear `n`.

## Design

- Sigma: `0.08`; threshold: posterior true-type mass greater than `0.9`.
- Fixed diagnostic action: all agents contribute `1.0`.
- Nested type family: prefixes `m={2,3,4,6,8,12,16}` of the existing respaced `m=16` library. This holds adjacent spacing and both measured Hellinger margins fixed across `m`.
- Every `(phase,n,m,H)` cell uses an independent RNG stream.
- Fixed-channel cells use 500 new seeds beginning at 30000.
- Adaptive PACT robustness cells use 200 new seeds beginning at 50000.
- Cell uncertainty uses 2,000 seed-cluster bootstrap replicates with fixed seed 91073.
- Censored observations are never deleted; restricted values use `max_episodes+1`, and censoring itself is a hard gate.

### Phases

1. **Hellinger core:** 200,000 independent samples per cell, three pair gaps and five information levels.
2. **Type/horizon:** `n=3`, seven `m` values, `H={1,2,4,8}`, maximum 2,048 episodes.
3. **Population:** `m=8`, `H=4`, `n={2,4,8,16,32,64}`, maximum 2,048 episodes.
4. **Adaptive robustness:** sampled-profile PACT, `n=3`, `m={4,8,16}`, `H={1,4}`, maximum 4,096 episodes.

## Hard gates

- **G1:** affinity fit R-squared at least 0.995; point slope in `[0.98,1.02]`; bootstrap interval covers 1; absolute intercept at most 0.03; maximum standardized cell error at most 4.5.
- **G2:** type/horizon fit R-squared at least 0.90; bootstrap slope lower endpoint positive; censoring at most 1%; within each `m`, the largest/smallest `H * restricted_mean_episode` ratio at most 1.35.
- **G3:** population fit R-squared at least 0.90; bootstrap slope lower endpoint positive; censoring at most 1%; corrected-predictor R-squared exceeds the original linear-`n` comparator by at least 0.10.
- **G4:** every empirical posterior-error-proxy upper 95% mean lies below the finite Hellinger bound; maximum relative increment from episode 1,024 to 2,048 is at most 2%.
- **G5:** adaptive censoring at most 5%; every selected empirical posterior-error upper 95% mean lies below the prespecified global-rho bound; maximum proxy increment from half horizon to the end is at most 5%.

Claim B-v3 is supported only if **all five gates pass without changing anything above**. No LaTeX is changed before the run and validator finish.

The machine-readable source of truth is `preregistration.json`; its SHA-256 is recorded separately before execution.
