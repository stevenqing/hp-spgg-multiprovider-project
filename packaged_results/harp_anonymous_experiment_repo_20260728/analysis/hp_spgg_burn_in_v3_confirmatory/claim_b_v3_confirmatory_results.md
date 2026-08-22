# HP-SPGG Claim B v3 — Confirmatory Results

Overall locked decision: **SUPPORTED**.

Preregistration JSON SHA-256: `1cbaf2a8eaf215f241e9274e4296c7be9137bdff8ad8f84eefb053e81f84fb44`.
Preregistration Markdown SHA-256: `4acdb89a5dd39b8a13ef73f160a56ca17f4faee2dda862a02b0969e43ddf11fd`.

The original `(n+1) log(m)/(rho H)` formula is not relabeled as supported. The tested claim is the corrected per-agent Hellinger-contraction statement plus a `log(n)` simultaneous-agent term.

## Locked gate disposition

| gate | passed | details |
|---|---|---|
| G1_affinity_core | True | {"fit": {"intercept": -0.002796939059747679, "observations": 15, "r_squared": 0.999961566366418, "slope": 1.0006662000190958}, "gates": {"absolute_intercept": true, "bootstrap_ci_covers_one": true, "maximum_standardized_cell_error": true, "point_slope": true, "r_squared": true}, "intercept_ci95": [-0.008503541803895679, 0.0033210416287198577], "max_abs_standardized_cell_error": 2.271146732087432, "passed": true, "slope_ci95": [0.9908306842746964, 1.0092331281289515]} |
| G2_type_horizon | True | {"fit": {"intercept": 22.22312038611031, "observations": 28, "r_squared": 0.9063552092907146, "slope": 0.26857190925472035}, "gates": {"bootstrap_slope_ci_low_positive": true, "censoring": true, "r_squared": true, "turn_equivalent_ratio": true}, "max_censoring_fraction": 0.0, "passed": true, "slope_ci95": [0.26445659991076587, 0.27282188942087177], "turn_equivalent_ratios": {"12": 1.03715531762697, "16": 1.0571672892569421, "2": 1.0950687922385194, "3": 1.085082437321566, "4": 1.0628053853928758, "6": 1.0499523336032723, "8": 1.049089952552554}} |
| G3_population | True | {"corrected_fit": {"intercept": -70.6672761904762, "observations": 6, "r_squared": 0.9939789286305318, "slope": 0.587070592635135}, "corrected_slope_ci95": [0.5613050935193366, 0.6128584550020979], "gates": {"bootstrap_slope_ci_low_positive": true, "censoring": true, "corrected_advantage": true, "r_squared": true}, "max_censoring_fraction": 0.0, "original_linear_n_fit": {"intercept": 115.00730063965882, "observations": 6, "r_squared": 0.8489110276396015, "slope": 0.014261609741729483}, "original_linear_n_slope_ci95": [0.013518119397880826, 0.014989264348703813], "passed": true, "r_squared_advantage": 0.14506790099093037} |
| G4_K_independent_proxy | True | {"gates": {"all_upper95_below_bound": true, "relative_increment": true}, "max_relative_increment_1024_to_2048": 0.018275419337221235, "passed": true, "relative_increments": {"m12_H1": 0.018275419337221235, "m12_H2": 1.7593183592465618e-05, "m12_H4": 2.6033743025880954e-13, "m12_H8": 0.0, "m16_H1": 0.015571318062792494, "m16_H2": 5.14541109078781e-05, "m16_H4": 1.3837901003820546e-10, "m16_H8": 0.0, "m2_H1": 0.006895750870023861, "m2_H2": 0.0016988470008615756, "m2_H4": 5.770703788962479e-13, "m2_H8": 0.0, "m3_H1": 0.016851045031331266, "m3_H2": 0.00015573082827633283, "m3_H4": 8.087551001599697e-12, "m3_H8": 0.0, "m4_H1": 0.01624186330266621, "m4_H2": 6.989443351952574e-05, "m4_H4": 2.9406919208307876e-11, "m4_H8": 0.0, "m6_H1": 0.013502523170294654, "m6_H2": 0.00021942536209146758, "m6_H4": 5.360846539127555e-13, "m6_H8": 0.0, "m8_H1": 0.012144479406989232, "m8_H2": 1.1322843559937422e-05, "m8_H4": 1.9341091459920413e-13, "m8_H8": 0.0}} |
| G5_adaptive_robustness | True | {"gates": {"all_upper95_errors_below_global_bound": true, "censoring": true, "relative_proxy_increment": true}, "max_censoring_fraction": 0.0, "max_relative_proxy_increment": 0.004797564321331912, "passed": true} |

## Hellinger affinity core

| gap | target_information | turns | x_exact_information | empirical_mean_root_lr | theoretical_affinity_product | standardized_error |
|---|---|---|---|---|---|---|
| 1 | 0.25 | 71 | 0.24927458419067167 | 0.7825662207681697 | 0.7793659424347471 | 2.271146732087432 |
| 1 | 0.5 | 142 | 0.49854916838134333 | 0.6088340166466208 | 0.6074112722272015 | 0.7934499612343784 |
| 1 | 1.0 | 285 | 1.000609246399175 | 0.3684812937045844 | 0.3676553802076764 | 0.3858111519525578 |
| 1 | 1.5 | 427 | 1.4991584147805184 | 0.2250039557852825 | 0.2233180222331202 | 0.8078151807988099 |
| 1 | 2.0 | 570 | 2.00121849279835 | 0.1348156521180554 | 0.13517047859565112 | -0.1640059585752114 |
| 2 | 0.25 | 18 | 0.2527854938271591 | 0.7785103447287743 | 0.7766344568424479 | 1.3271976339929483 |
| 2 | 0.5 | 36 | 0.5055709876543182 | 0.6040288691545758 | 0.603161079554964 | 0.48151021837299474 |
| 2 | 1.0 | 71 | 0.9970983367626831 | 0.3690189791726647 | 0.3689484536286688 | 0.034144661021868784 |
| 2 | 1.5 | 107 | 1.5026693244170013 | 0.22489942629487875 | 0.22253534759080246 | 1.0850927442955076 |
| 2 | 2.0 | 142 | 1.9941966735253662 | 0.1351068934743986 | 0.13612296143498595 | -0.41672933774188775 |
| 3 | 0.25 | 8 | 0.25278549382715976 | 0.7768538179937313 | 0.7766344568424474 | 0.15571549999928064 |
| 3 | 0.5 | 16 | 0.5055709876543195 | 0.6041666443425943 | 0.6031610795549632 | 0.5581049557848976 |
| 3 | 1.0 | 32 | 1.011141975308639 | 0.3641433392418454 | 0.3638032878899087 | 0.16545178063761964 |
| 3 | 1.5 | 47 | 1.4851147762345636 | 0.2271538685065038 | 0.22647634508255282 | 0.3071207159013333 |
| 3 | 2.0 | 63 | 1.990685763888883 | 0.13727324551073355 | 0.13660171679365496 | 0.3382925833526426 |

## Fixed-channel cell summaries

| phase | n | m | H | rho_action | restricted_mean_per_agent_episode | restricted_mean_all_agent_episode | censoring_fraction_agents | censoring_fraction_seeds |
|---|---|---|---|---|---|---|---|---|
| type_horizon | 3 | 2 | 1 | 0.0035047535997874135 | 156.946 | 273.274 | 0.0 | 0.0 |
| type_horizon | 3 | 2 | 2 | 0.0035047535997874135 | 84.07 | 146.608 | 0.0 | 0.0 |
| type_horizon | 3 | 2 | 4 | 0.0035047535997874135 | 42.60666666666667 | 72.68 | 0.0 | 0.0 |
| type_horizon | 3 | 2 | 8 | 0.0035047535997874135 | 21.483333333333334 | 35.77 | 0.0 | 0.0 |
| type_horizon | 3 | 3 | 1 | 0.0035047535997874135 | 209.69466666666668 | 347.958 | 0.0 | 0.0 |
| type_horizon | 3 | 3 | 2 | 0.0035047535997874135 | 107.59866666666667 | 177.076 | 0.0 | 0.0 |
| type_horizon | 3 | 3 | 4 | 0.0035047535997874135 | 54.318666666666665 | 88.004 | 0.0 | 0.0 |
| type_horizon | 3 | 3 | 8 | 0.0035047535997874135 | 28.442 | 45.798 | 0.0 | 0.0 |
| type_horizon | 3 | 4 | 1 | 0.0035047535997874135 | 238.76933333333332 | 379.128 | 0.0 | 0.0 |
| type_horizon | 3 | 4 | 2 | 0.0035047535997874135 | 125.488 | 198.546 | 0.0 | 0.0 |
| type_horizon | 3 | 4 | 4 | 0.0035047535997874135 | 61.37533333333333 | 95.74 | 0.0 | 0.0 |
| type_horizon | 3 | 4 | 8 | 0.0035047535997874135 | 31.720666666666666 | 48.47 | 0.0 | 0.0 |
| type_horizon | 3 | 6 | 1 | 0.0035047535997874135 | 260.574 | 400.052 | 0.0 | 0.0 |
| type_horizon | 3 | 6 | 2 | 0.0035047535997874135 | 130.07066666666665 | 194.374 | 0.0 | 0.0 |
| type_horizon | 3 | 6 | 4 | 0.0035047535997874135 | 67.74 | 101.932 | 0.0 | 0.0 |
| type_horizon | 3 | 6 | 8 | 0.0035047535997874135 | 34.142 | 51.1 | 0.0 | 0.0 |
| type_horizon | 3 | 8 | 1 | 0.0035047535997874135 | 269.91266666666667 | 397.484 | 0.0 | 0.0 |
| type_horizon | 3 | 8 | 2 | 0.0035047535997874135 | 137.22533333333334 | 202.362 | 0.0 | 0.0 |
| type_horizon | 3 | 8 | 4 | 0.0035047535997874135 | 69.854 | 102.092 | 0.0 | 0.0 |
| type_horizon | 3 | 8 | 8 | 0.0035047535997874135 | 35.39533333333333 | 52.372 | 0.0 | 0.0 |
| type_horizon | 3 | 12 | 1 | 0.0035047535997874135 | 290.22 | 413.446 | 0.0 | 0.0 |
| type_horizon | 3 | 12 | 2 | 0.0035047535997874135 | 144.45666666666668 | 209.238 | 0.0 | 0.0 |
| type_horizon | 3 | 12 | 4 | 0.0035047535997874135 | 74.05466666666666 | 108.692 | 0.0 | 0.0 |
| type_horizon | 3 | 12 | 8 | 0.0035047535997874135 | 37.456 | 53.38 | 0.0 | 0.0 |
| type_horizon | 3 | 16 | 1 | 0.0035047535997874135 | 299.46866666666665 | 427.542 | 0.0 | 0.0 |
| type_horizon | 3 | 16 | 2 | 0.0035047535997874135 | 148.352 | 214.444 | 0.0 | 0.0 |
| type_horizon | 3 | 16 | 4 | 0.0035047535997874135 | 74.06333333333333 | 105.29 | 0.0 | 0.0 |
| type_horizon | 3 | 16 | 8 | 0.0035047535997874135 | 39.148666666666664 | 55.894 | 0.0 | 0.0 |
| population | 2 | 8 | 4 | 0.0035047535997874135 | 73.488 | 95.376 | 0.0 | 0.0 |
| population | 4 | 8 | 4 | 0.0035047535997874135 | 69.5585 | 113.202 | 0.0 | 0.0 |
| population | 8 | 8 | 4 | 0.0035047535997874135 | 70.8795 | 143.104 | 0.0 | 0.0 |
| population | 16 | 8 | 4 | 0.0035047535997874135 | 70.682375 | 174.528 | 0.0 | 0.0 |
| population | 32 | 8 | 4 | 0.0035047535997874135 | 70.667375 | 207.176 | 0.0 | 0.0 |
| population | 64 | 8 | 4 | 0.0035047535997874135 | 70.442875 | 235.894 | 0.0 | 0.0 |

## Adaptive PACT robustness

| n | m | H | rho_global | upper95_error_final_preupdate | global_rho_error_bound | censoring_fraction_agents | relative_proxy_increment |
|---|---|---|---|---|---|---|---|
| 3 | 4 | 1 | 0.0011696097542561734 | 2.0843242437915343e-13 | 0.04989709599301191 | 0.0 | 1.0942461844328228e-05 |
| 3 | 4 | 4 | 0.0011696097542561734 | 0.0 | 2.8697715820384105e-08 | 0.0 | 0.0 |
| 3 | 8 | 1 | 0.0011696097542561734 | 7.842052249643489e-13 | 0.16465201637814922 | 0.0 | 0.00014697193558154352 |
| 3 | 8 | 4 | 0.0011696097542561734 | 0.0 | 9.469763081873764e-08 | 0.0 | 0.0 |
| 3 | 16 | 1 | 0.0011696097542561734 | 1.1801715005224208e-10 | 0.4989709599301191 | 0.0 | 0.004797564321331912 |
| 3 | 16 | 4 | 0.0011696097542561734 | 0.0 | 2.8697715820384103e-07 | 0.0 | 0.0 |

## Complete machine-readable result

```json
{
  "status": "supported",
  "claim_b_v3_supported": true,
  "original_linear_n_formula_supported": false,
  "original_linear_n_formula_disposition": "retired as inconsistent with the current per-agent proposition",
  "preregistration_sha256": "1cbaf2a8eaf215f241e9274e4296c7be9137bdff8ad8f84eefb053e81f84fb44",
  "preregistration_markdown_sha256": "4acdb89a5dd39b8a13ef73f160a56ca17f4faee2dda862a02b0969e43ddf11fd",
  "provider_calls": 0,
  "gates": {
    "G1_affinity_core": {
      "fit": {
        "slope": 1.0006662000190958,
        "intercept": -0.002796939059747679,
        "r_squared": 0.999961566366418,
        "observations": 15
      },
      "slope_ci95": [
        0.9908306842746964,
        1.0092331281289515
      ],
      "intercept_ci95": [
        -0.008503541803895679,
        0.0033210416287198577
      ],
      "max_abs_standardized_cell_error": 2.271146732087432,
      "gates": {
        "r_squared": true,
        "point_slope": true,
        "bootstrap_ci_covers_one": true,
        "absolute_intercept": true,
        "maximum_standardized_cell_error": true
      },
      "passed": true
    },
    "G2_type_horizon": {
      "fit": {
        "slope": 0.26857190925472035,
        "intercept": 22.22312038611031,
        "r_squared": 0.9063552092907146,
        "observations": 28
      },
      "slope_ci95": [
        0.26445659991076587,
        0.27282188942087177
      ],
      "max_censoring_fraction": 0.0,
      "turn_equivalent_ratios": {
        "2": 1.0950687922385194,
        "3": 1.085082437321566,
        "4": 1.0628053853928758,
        "6": 1.0499523336032723,
        "8": 1.049089952552554,
        "12": 1.03715531762697,
        "16": 1.0571672892569421
      },
      "gates": {
        "r_squared": true,
        "bootstrap_slope_ci_low_positive": true,
        "censoring": true,
        "turn_equivalent_ratio": true
      },
      "passed": true
    },
    "G3_population": {
      "corrected_fit": {
        "slope": 0.587070592635135,
        "intercept": -70.6672761904762,
        "r_squared": 0.9939789286305318,
        "observations": 6
      },
      "corrected_slope_ci95": [
        0.5613050935193366,
        0.6128584550020979
      ],
      "original_linear_n_fit": {
        "slope": 0.014261609741729483,
        "intercept": 115.00730063965882,
        "r_squared": 0.8489110276396015,
        "observations": 6
      },
      "original_linear_n_slope_ci95": [
        0.013518119397880826,
        0.014989264348703813
      ],
      "r_squared_advantage": 0.14506790099093037,
      "max_censoring_fraction": 0.0,
      "gates": {
        "r_squared": true,
        "bootstrap_slope_ci_low_positive": true,
        "censoring": true,
        "corrected_advantage": true
      },
      "passed": true
    },
    "G4_K_independent_proxy": {
      "max_relative_increment_1024_to_2048": 0.018275419337221235,
      "relative_increments": {
        "m2_H1": 0.006895750870023861,
        "m2_H2": 0.0016988470008615756,
        "m2_H4": 5.770703788962479e-13,
        "m2_H8": 0.0,
        "m3_H1": 0.016851045031331266,
        "m3_H2": 0.00015573082827633283,
        "m3_H4": 8.087551001599697e-12,
        "m3_H8": 0.0,
        "m4_H1": 0.01624186330266621,
        "m4_H2": 6.989443351952574e-05,
        "m4_H4": 2.9406919208307876e-11,
        "m4_H8": 0.0,
        "m6_H1": 0.013502523170294654,
        "m6_H2": 0.00021942536209146758,
        "m6_H4": 5.360846539127555e-13,
        "m6_H8": 0.0,
        "m8_H1": 0.012144479406989232,
        "m8_H2": 1.1322843559937422e-05,
        "m8_H4": 1.9341091459920413e-13,
        "m8_H8": 0.0,
        "m12_H1": 0.018275419337221235,
        "m12_H2": 1.7593183592465618e-05,
        "m12_H4": 2.6033743025880954e-13,
        "m12_H8": 0.0,
        "m16_H1": 0.015571318062792494,
        "m16_H2": 5.14541109078781e-05,
        "m16_H4": 1.3837901003820546e-10,
        "m16_H8": 0.0
      },
      "gates": {
        "all_upper95_below_bound": true,
        "relative_increment": true
      },
      "passed": true
    },
    "G5_adaptive_robustness": {
      "max_censoring_fraction": 0.0,
      "max_relative_proxy_increment": 0.004797564321331912,
      "gates": {
        "censoring": true,
        "all_upper95_errors_below_global_bound": true,
        "relative_proxy_increment": true
      },
      "passed": true
    }
  },
  "row_counts": {
    "affinity_batches": 3000,
    "affinity_summary": 15,
    "fixed_agent_results": 105000,
    "fixed_cell_summary": 34,
    "proxy_checkpoints": 84,
    "adaptive_seed_results": 1200,
    "adaptive_cell_summary": 6
  }
}
```

## Interpretation boundary

Passing supports the stochastic outcome-channel mechanism used by Proposition `prop:tid-collapse`: exact Hellinger root-odds contraction, a K-independent cumulative type-error proxy, inverse-H operational concentration, and logarithmic simultaneous-agent growth. It is not evidence for the retired linear-n formula, and it does not turn an upper bound into an exact equality.
