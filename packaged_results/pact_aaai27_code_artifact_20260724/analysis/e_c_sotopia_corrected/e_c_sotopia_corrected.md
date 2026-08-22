# E-C: Corrected SOTOPIA Tracker Analysis

The retained corrected run reads `Observation.last_turn` and records nonzero recurrent updates. SOTOPIA has no native labels for the project's four persona classes; all concentration numbers below use the existing profile-derived oracle projection as a proxy.

## Branch decision

| family | corrected p=0 | historical best | delta | branch |
|---|---:|---:|---:|---|
| craigslist_bargains | 2.665 $\pm$ 0.074 | 2.760 (llm_belief) | -0.095 | clean-boundary |
| donate_funds | 3.229 $\pm$ 0.121 | 3.386 (atom_tom1) | -0.157 | clean-boundary |
| revenge_plot | 2.743 $\pm$ 0.102 | 3.200 (llm_greedy) | -0.457 | clean-boundary |

## Proxy concentration

| family | turn | proxy mass | entropy | MAP agreement |
|---|---:|---:|---:|---:|
| craigslist_bargains | 0 | 0.250 $\pm$ 0.000 | 1.000 | 0.850 |
| craigslist_bargains | 1 | 0.246 $\pm$ 0.002 | 0.993 | 0.494 |
| craigslist_bargains | 2 | 0.242 $\pm$ 0.003 | 0.983 | 0.125 |
| craigslist_bargains | 3 | 0.233 $\pm$ 0.005 | 0.966 | 0.131 |
| craigslist_bargains | 4 | 0.233 $\pm$ 0.005 | 0.966 | 0.131 |
| craigslist_bargains | 5 | 0.233 $\pm$ 0.005 | 0.966 | 0.131 |
| craigslist_bargains | 6 | 0.233 $\pm$ 0.005 | 0.966 | 0.131 |
| donate_funds | 0 | 0.250 $\pm$ 0.000 | 1.000 | 0.800 |
| donate_funds | 1 | 0.257 $\pm$ 0.005 | 0.989 | 0.700 |
| donate_funds | 2 | 0.244 $\pm$ 0.006 | 0.984 | 0.200 |
| donate_funds | 3 | 0.261 $\pm$ 0.013 | 0.951 | 0.200 |
| donate_funds | 4 | 0.261 $\pm$ 0.013 | 0.951 | 0.200 |
| donate_funds | 5 | 0.261 $\pm$ 0.013 | 0.951 | 0.200 |
| donate_funds | 6 | 0.261 $\pm$ 0.013 | 0.951 | 0.200 |
| revenge_plot | 0 | 0.250 $\pm$ 0.000 | 1.000 | 0.800 |
| revenge_plot | 1 | 0.266 $\pm$ 0.007 | 0.983 | 0.550 |
| revenge_plot | 2 | 0.281 $\pm$ 0.008 | 0.964 | 0.300 |
| revenge_plot | 3 | 0.304 $\pm$ 0.012 | 0.933 | 0.250 |
| revenge_plot | 4 | 0.304 $\pm$ 0.012 | 0.933 | 0.250 |
| revenge_plot | 5 | 0.304 $\pm$ 0.012 | 0.933 | 0.250 |
| revenge_plot | 6 | 0.304 $\pm$ 0.012 | 0.933 | 0.250 |

## Menu corruption

| family | p | episodes | focal score |
|---|---:|---:|---:|
| craigslist_bargains | 0.00 | 80 | 2.665 $\pm$ 0.074 |
| craigslist_bargains | 0.10 | 80 | 2.658 $\pm$ 0.076 |
| craigslist_bargains | 0.20 | 80 | 2.603 $\pm$ 0.072 |
| craigslist_bargains | 0.25 | 80 | 2.700 $\pm$ 0.080 |
| craigslist_bargains | 0.30 | 80 | 2.642 $\pm$ 0.076 |
| craigslist_bargains | 0.50 | 80 | 2.612 $\pm$ 0.079 |
| donate_funds | 0.00 | 20 | 3.229 $\pm$ 0.121 |
| donate_funds | 0.10 | 20 | 3.357 $\pm$ 0.137 |
| donate_funds | 0.20 | 20 | 3.118 $\pm$ 0.170 |
| donate_funds | 0.25 | 20 | 3.429 $\pm$ 0.143 |
| donate_funds | 0.30 | 20 | 3.461 $\pm$ 0.114 |
| donate_funds | 0.50 | 20 | 3.389 $\pm$ 0.132 |
| revenge_plot | 0.00 | 20 | 2.743 $\pm$ 0.102 |
| revenge_plot | 0.10 | 20 | 2.864 $\pm$ 0.126 |
| revenge_plot | 0.20 | 20 | 2.675 $\pm$ 0.120 |
| revenge_plot | 0.25 | 20 | 2.779 $\pm$ 0.112 |
| revenge_plot | 0.30 | 20 | 2.779 $\pm$ 0.073 |
| revenge_plot | 0.50 | 20 | 2.889 $\pm$ 0.110 |

## Corrected component variants

| family | variant | episodes | focal score | paired PACT-minus-variant |
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

The completed grid contains 0%, 10%, 20%, 25%, 30%, and 50% corruption; every point is a measured rerun, not interpolation. The corrected p=0 run is below the retained GPT-nano comparator in all three families. Applying the corrected component/concentration rule selects the clean-boundary branch.
