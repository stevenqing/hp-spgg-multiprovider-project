# PACT AAAI-27 Supplemental Experiments

## Status

| Experiment | Status | Claim-safe disposition |
|---|---|---|
| E-A matched likelihood | complete | Four-backbone, ten-common-environment-seed control shares each pinned tensor, type profile, uniform prior, no additional board state, and oracle; each method generates its own trajectory. |
| E-B iterated Concordia | complete | Constructed exact-payoff diagnostic: plateau-vs-linear result; not native Concordia or backbone evidence. |
| E-C corrected SOTOPIA | clean-boundary | Corrected tracker updates; no score lead, so clean-boundary branch. |
| E-D RL violation | complete | Posterior TV grows with coupling, but paired regret gaps remain null on this geometry. |
| E-E MaaSSim tracker parity | complete | Joint marginals match factored tracking to numerical precision through n=4; independent sampling leaves one of nine nominal utility CIs non-covering. |
| E-F MaaSSim frozen bonus | complete | Beta 0.25 changes 4/406 assignments; paired utility gap remains unresolved. |
| E-G HP-SPGG component ladder | complete | One analytic substrate/metric: update and dispatch paired effects resolve; bonus and identity do not. |

## E-A environment-matched control

| model | PACT+ | PACT | Joint-PSRL | LLM-PSRL | best baseline | family ratio |
|---|---:|---:|---:|---:|---:|---:|
| DeepSeek-V3.2 | 0.360 $\pm$ 0.142 | 0.985 $\pm$ 0.298 | 0.955 $\pm$ 0.203 | 18.270 $\pm$ 5.141 | econ_bne 2.550 | 7.08x |
| GPT-5.4-nano | 0.159 $\pm$ 0.038 | 0.544 $\pm$ 0.150 | 0.391 $\pm$ 0.100 | 2.193 $\pm$ 0.714 | econ_bne 6.960 | 43.77x |
| Kimi-K2.6 | 0.325 $\pm$ 0.088 | 0.547 $\pm$ 0.116 | 0.642 $\pm$ 0.159 | 6.701 $\pm$ 1.325 | econ_bne 2.957 | 9.10x |
| Llama-4-Maverick | 0.430 $\pm$ 0.217 | 1.202 $\pm$ 0.212 | 1.276 $\pm$ 0.228 | 13.510 $\pm$ 3.431 | atom_tom0 0.700 | 1.63x |

Environment seeds and type profiles are matched. Provider sampling seeds are unavailable, so accepted raw responses are content-hash cache-pinned rather than claimed to be pathwise provider-RNG matched.
Accepted response-cache entries: 23,178; strict external format repairs: 262.

### Historical source audit (unmatched; retained for provenance)

| model | PACT+ | best PACT family | best baseline | historical family ratio |
|---|---:|---:|---:|---:|
| DeepSeek-V3.2 | 0.400 | hpsmg_plus 0.400 | econ_bne 3.990 | 9.97x |
| GPT-5.4-nano | 0.912 | hpsmg 0.644 | atom_tom0 4.080 | 6.34x |
| Kimi-K2.6 | 0.704 | hpsmg 0.632 | atom_adaptive_hedge 7.484 | 11.84x |
| Llama-4-Maverick | 0.312 | hpsmg_plus 0.312 | econ_bne 3.382 | 10.84x |

## E-B aggregate

| scope | method | regret K=20 | late regret | paired gap vs PACT+ |
|---|---|---:|---:|---:|
| all_selected | pact | 0.312 $\pm$ 0.026 | 0.0041 | -0.040 $\pm$ 0.030 |
| all_selected | pact_plus | 0.352 $\pm$ 0.035 | 0.0020 | +0.000 $\pm$ 0.000 |
| all_selected | joint_psrl_uniform | 0.329 $\pm$ 0.030 | 0.0049 | -0.023 $\pm$ 0.043 |
| all_selected | psrl_notype | 1.361 $\pm$ 0.172 | 0.0764 | +1.009 $\pm$ 0.201 |
| informative_haggling | pact | 0.459 $\pm$ 0.040 | 0.0061 | -0.041 $\pm$ 0.026 |
| informative_haggling | pact_plus | 0.500 $\pm$ 0.046 | 0.0030 | +0.000 $\pm$ 0.000 |
| informative_haggling | joint_psrl_uniform | 0.470 $\pm$ 0.037 | 0.0065 | -0.030 $\pm$ 0.050 |
| informative_haggling | psrl_notype | 1.877 $\pm$ 0.271 | 0.1078 | +1.377 $\pm$ 0.299 |

## E-G HP-SPGG analytic component ladder

| variant | cumulative regret | paired minus full | 95% CI | ratio vs full |
|---|---:|---:|---:|---:|
| full | 0.015 $\pm$ 0.007 | +0.000 | [+0.000, +0.000] | 1.00x |
| minus_bonus | 0.016 $\pm$ 0.007 | +0.001 | [-0.002, +0.003] | 1.05x |
| minus_update | 0.675 $\pm$ 0.114 | +0.660 | [+0.406, +0.915] | 45.61x |
| minus_identity | 0.700 $\pm$ 0.368 | +0.685 | [-0.141, +1.512] | 47.29x |
| minus_dispatch | 6.324 $\pm$ 0.439 | +6.309 | [+5.310, +7.307] | 427.17x |

## E-C branch

| family | corrected p=0 | delta vs retained best | branch |
|---|---:|---:|---|
| craigslist_bargains | 2.665 $\pm$ 0.074 | -0.095 | clean-boundary |
| donate_funds | 3.229 $\pm$ 0.121 | -0.157 | clean-boundary |
| revenge_plot | 2.743 $\pm$ 0.102 | -0.457 | clean-boundary |

Completed corruption levels: [0.0, 0.1, 0.2, 0.25, 0.3, 0.5].

### Corrected component variants

| family | variant | n | score | paired PACT-minus-variant |
|---|---|---:|---:|---:|
| craigslist_bargains | PACT+ corrected | 80 | 2.665 $\pm$ 0.074 | +0.000 $\pm$ 0.000 |
| craigslist_bargains | naive-belief corrected | 80 | 2.621 $\pm$ 0.078 | +0.044 $\pm$ 0.096 |
| craigslist_bargains | surrogate-only corrected | 80 | 2.603 $\pm$ 0.073 | +0.063 $\pm$ 0.077 |
| donate_funds | PACT+ corrected | 20 | 3.229 $\pm$ 0.121 | +0.000 $\pm$ 0.000 |
| donate_funds | naive-belief corrected | 20 | 3.136 $\pm$ 0.125 | +0.093 $\pm$ 0.182 |
| donate_funds | surrogate-only corrected | 20 | 3.307 $\pm$ 0.134 | -0.079 $\pm$ 0.090 |
| revenge_plot | PACT+ corrected | 20 | 2.743 $\pm$ 0.102 | +0.000 $\pm$ 0.000 |
| revenge_plot | naive-belief corrected | 20 | 2.786 $\pm$ 0.111 | -0.043 $\pm$ 0.150 |
| revenge_plot | surrogate-only corrected | 20 | 2.850 $\pm$ 0.140 | -0.107 $\pm$ 0.166 |

## E-D posterior coupling and regret

| tier | alpha | PACT | Joint | paired gap | marginal TV |
|---|---:|---:|---:|---:|---:|
| analytic-mixed | 0 | 0.001 $\pm$ 0.001 | 0.001 $\pm$ 0.001 | +0.000 $\pm$ 0.000 | 0.0000 $\pm$ 0.0000 |
| analytic-mixed | 1 | 0.155 $\pm$ 0.065 | 0.206 $\pm$ 0.087 | -0.051 $\pm$ 0.051 | 0.0000 $\pm$ 0.0000 |
| analytic-mixed | 2 | 0.212 $\pm$ 0.064 | 0.203 $\pm$ 0.065 | +0.009 $\pm$ 0.009 | 0.0010 $\pm$ 0.0004 |
| analytic-mixed | 4 | 0.199 $\pm$ 0.057 | 0.213 $\pm$ 0.057 | -0.013 $\pm$ 0.013 | 0.0071 $\pm$ 0.0025 |
| DeepSeek-V3.2-live | 0 | 1.130 $\pm$ 0.154 | 1.130 $\pm$ 0.154 | +0.000 $\pm$ 0.000 | 0.0000 $\pm$ 0.0000 |
| DeepSeek-V3.2-live | 1 | 0.583 $\pm$ 0.115 | 0.575 $\pm$ 0.116 | +0.008 $\pm$ 0.008 | 0.0082 $\pm$ 0.0042 |
| DeepSeek-V3.2-live | 2 | 0.587 $\pm$ 0.132 | 0.545 $\pm$ 0.108 | +0.042 $\pm$ 0.047 | 0.0128 $\pm$ 0.0065 |
| DeepSeek-V3.2-live | 4 | 0.517 $\pm$ 0.131 | 0.466 $\pm$ 0.108 | +0.051 $\pm$ 0.107 | 0.0171 $\pm$ 0.0047 |

## E-E MaaSSim tracker parity

| n | lambda | factored utility | joint utility | joint - factored 95% CI | max TV | storage ratio |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 0 | -8.460 $\pm$ 6.028 | -6.611 $\pm$ 6.327 | +1.849 [+0.192, +3.506] | 7.81e-16 | 8.0x |
| 2 | 0.5 | -42.924 $\pm$ 8.369 | -43.307 $\pm$ 8.439 | -0.383 [-3.104, +2.338] | 7.81e-16 | 8.0x |
| 2 | 1 | -52.488 $\pm$ 8.598 | -52.374 $\pm$ 9.375 | +0.114 [-2.870, +3.098] | 7.81e-16 | 8.0x |
| 3 | 0 | -7.481 $\pm$ 8.161 | -6.150 $\pm$ 7.818 | +1.331 [-0.708, +3.370] | 2.47e-15 | 85.3x |
| 3 | 0.5 | -53.485 $\pm$ 6.623 | -56.524 $\pm$ 7.283 | -3.039 [-7.237, +1.159] | 2.47e-15 | 85.3x |
| 3 | 1 | -57.150 $\pm$ 7.629 | -58.739 $\pm$ 7.084 | -1.589 [-5.126, +1.948] | 2.47e-15 | 85.3x |
| 4 | 0 | -7.141 $\pm$ 8.333 | -8.516 $\pm$ 9.015 | -1.375 [-3.901, +1.151] | 2.55e-14 | 1,024.0x |
| 4 | 0.5 | -59.281 $\pm$ 9.498 | -56.652 $\pm$ 10.911 | +2.629 [-2.687, +7.945] | 2.55e-14 | 1,024.0x |
| 4 | 1 | -60.362 $\pm$ 8.604 | -60.734 $\pm$ 9.534 | -0.372 [-4.081, +3.337] | 2.55e-14 | 1,024.0x |

## E-F MaaSSim frozen bonus

PACT utility: 27.607 $\pm$ 11.647; PACT+ utility: 27.360 $\pm$ 11.563. Paired PACT+ minus PACT: -0.247 [-0.806, +0.312] (95% CI); 4/406 assignments change.
