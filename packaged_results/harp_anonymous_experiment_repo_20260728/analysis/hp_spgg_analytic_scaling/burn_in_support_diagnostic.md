# Why Claim (b) Is Unsupported

This diagnostic is derived from the completed scaling NPZs and the current proof of Proposition `prop:tid-collapse`. It does not rerun or retune the experiment.

## Bottom line

The null is not primarily evidence against Proposition `prop:tid-collapse`. The experiment regressed a different statistic against a predictor that is not the proposition's formula, under a deterministic-mean DGP that does not instantiate the stochastic Gaussian outcome channel used by the Hellinger proof.

The preregistered uncensored PACT fit is slope `-0.24778382996700402`, R-squared `0.006498673740053196`, with `11` observations; it does not support the proposed pooled relation.

## Theory mismatch

The current proposition is per-agent and states an upper bound on expected cumulative reward-channel regret:

`O(H + rho^{-1} log(m / pi_min))`.

The displayed proof uses `C=m*pi_min^{-1/2}` at its switching point. For a uniform prior, the proposition statement gives `2 log(m)` and that proof step gives `1.5 log(m)`; both are only order-level `O(log m)` statements. Neither contains a linear `n` term. Requiring simultaneous control over all agents would introduce `log(n)` through a union bound, not `(n+1) log(m)`. The measured median all-agent first passage is also not the proposition's expected regret quantity. The label `thm:any-coupling` is absent from the current paper source.

## Data diagnosis

### S1 population sweep

| n | median all-agent burn-in | mean observed | censored | unique PACT actions | modal share | global rho_hat | visited-action rho |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 8.0 | 7.5 | 0 | 1 | 1.000 | 7.29405133e-06 | 0.0743381973 |
| 3 | 8.0 | 7.5 | 0 | 1 | 1.000 | 7.29405133e-06 | 0.0743381973 |
| 4 | 8.0 | 8.0 | 0 | 1 | 1.000 | 7.29405133e-06 | 0.0743381973 |
| 5 | 8.0 | 8.0 | 0 | 1 | 1.000 | 7.29405133e-06 | 0.0743381973 |
| 6 | 8.0 | 8.0 | 0 | 1 | 1.000 | 7.29405133e-06 | 0.0743381973 |
| 7 | 8.0 | 8.0 | 0 | 1 | 1.000 | 9.41900515e-08 | 0.0743381973 |
| 8 | 8.0 | 8.0 | 0 | 1 | 1.000 | 3.72146141e-06 | 0.0743381973 |
| 9 | 8.0 | 8.0 | 0 | 1 | 1.000 | 7.29405133e-06 | 0.0743381973 |
| 10 | 8.0 | 8.0 | 0 | 1 | 1.000 | 7.29405133e-06 | 0.0743381973 |

PACT chooses the all-contribution action in all 4,500 S1 decisions. Under this deterministic channel, original types 0/1 cross 0.9 at episode 8 and types 2/3 at episode 3. The probability that an n-agent profile includes at least one slow type is `1-(1/2)^n`, already 0.75 at n=2, so the median maximum is 8 for every n. This is median saturation, not a failed posterior update.

### S2 library sweep

| m | median all-agent burn-in | censored | unique PACT actions | modal share | global rho_hat | visited-action rho |
|---:|---:|---:|---:|---:|---:|---:|
| 4 | 8.0 | 0 | 1 | 1.000 | 7.29405133e-06 | 0.0743381973 |
| 8 | 45.0 | 0 | 8 | 0.774 | 0.00535938724 | 0.00997758662 |
| 16 | nan | 9 | 8 | 0.794 | 0.00116960975 | 0.00218142665 |

## Why the OLS slope turns negative

1. Nine S1 points move right with n but all remain at burn-in 8.
2. The only uncensored library-growth point, m=8, is 45 at the same x-value as the S1 n=5 point at 8.
3. The informative m=16 point lies at the right but is 9/10 censored and excluded from OLS.
4. Pooling these as independent complete cases yields a small negative slope and near-zero R-squared; this is a weighting/censoring artifact, not a contraction-rate estimate.

## Causes

1. **theory-target mismatch.** Proposition prop:tid-collapse bounds per-agent expected cumulative reward-channel regret. It does not predict that an all-agent posterior first-passage median equals (n+1) log(m)/(rho H).
2. **wrong population functional form.** For independent agent channels, controlling all agents by a union bound contributes log(n). A linear n factor is not present in the current proof, and thm:any-coupling is not a label in the current paper source.
3. **deterministic analytic observations.** The runner observes the calibrated reward mean exactly and only evaluates a Gaussian likelihood around it; it does not sample y from the Gaussian q_theta used in the Hellinger contraction proof. Conditional hitting times therefore become almost deterministic by true type.
4. **no horizon scaling dimension.** The analytic runner has one action/reward observation per episode and records H=1. It cannot test inverse-H dependence because H is neither greater than one nor swept.
5. **S1 action/channel degeneracy.** PACT visits only the all-contribution action in every S1 episode. At m=4, types 0/1 cross 0.9 at episode 8 and types 2/3 at episode 3. From n=2 onward, the median maximum is already the slow-type value 8 and cannot reveal further n growth.
6. **rho_hat is a worst-case unvisited margin.** The global reachable-grid rho_hat can be orders of magnitude smaller than the margin on actions actually visited. It is valid for a conservative uniform bound but not an empirical equality predictor.
7. **rho varies with m but the OLS x-axis omits it.** m=8 and m=16 use different rho_hat values, while Fig B regresses only on (n+1) log(m). There is no single slope that can be compared with 1/(rho_hat H) across libraries.
8. **informative censoring and pseudo-replication.** The m=16 point is 9/10 censored at K=50 and excluded from OLS, biasing the complete-case slope downward. Nine flat S1 points from one m=4 channel dominate the pooled fit.
9. **median saturation and low seed resolution.** The all-agent median is discrete and saturates once more than half of profiles contain any slow type; ten seeds cannot resolve the much weaker max-order/log(n) effect.

## Recommended disposition and follow-up

Keep the current run as a preregistered null. Do not change seeds, K, rho spacing, threshold, or OLS inclusion to manufacture support.

- Test per-agent posterior error or log-odds contraction, the quantity directly controlled by prop:tid-collapse.
- Sample stochastic outcomes from q_theta instead of always observing the channel mean.
- Use realized cumulative information sum_h D_H^2(q_true,q_competitor) on visited actions, or hold rho fixed across libraries.
- If measuring all-agent first passage, use a predictor with log(n), not linear n, and analyze right censoring with survival/AFT methods.
- Sweep a genuine multi-turn H if inverse-H behavior is a target; the completed runner has H=1 only.
- Increase K for m=16 and increase seeds before estimating a population-order effect; preregister this as a new experiment rather than altering the completed run.

The follow-up would be a new, separately preregistered experiment. Claim (a)—exact factored/joint parity and the n=7/n=8 feasibility wall—remains unaffected.
