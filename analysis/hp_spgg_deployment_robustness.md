# HP-SPGG Deployment Robustness

Offline diagnostic; no LLM/API calls. Regret is measured in the unperturbed environment against exact full-information enumeration.

| condition | family | value | cumulative regret | true-type mass | MAP accuracy | entropy |
|---|---|---:|---:|---:|---:|---:|
| reference | reference | -- | 0.002 $\pm$ 0.000 | 0.995 | 1.000 | 0.018 |
| temperature_0.5 | likelihood_temperature | 0.5 | 0.002 $\pm$ 0.000 | 1.000 | 1.000 | 0.001 |
| temperature_2 | likelihood_temperature | 2.0 | 0.002 $\pm$ 0.001 | 0.958 | 1.000 | 0.107 |
| temperature_4 | likelihood_temperature | 4.0 | 0.004 $\pm$ 0.001 | 0.860 | 1.000 | 0.275 |
| log_noise_0.25 | log_likelihood_noise | 0.25 | 0.002 $\pm$ 0.000 | 0.987 | 0.998 | 0.032 |
| log_noise_0.5 | log_likelihood_noise | 0.5 | 0.002 $\pm$ 0.000 | 0.953 | 0.963 | 0.051 |
| log_noise_1.0 | log_likelihood_noise | 1.0 | 0.005 $\pm$ 0.002 | 0.873 | 0.882 | 0.061 |
| top_k_2 | top_k | 2 | 0.002 $\pm$ 0.000 | 0.995 | 1.000 | 0.018 |
| top_k_1 | top_k | 1 | 0.002 $\pm$ 0.000 | 1.000 | 1.000 | 0.000 |
| calibration_drift_0.02 | calibration_drift | 0.02 | 0.160 $\pm$ 0.015 | 0.945 | 0.977 | 0.081 |
| calibration_drift_0.05 | calibration_drift | 0.05 | 0.730 $\pm$ 0.036 | 0.699 | 0.714 | 0.182 |
| calibration_drift_0.10 | calibration_drift | 0.1 | 1.782 $\pm$ 0.057 | 0.484 | 0.483 | 0.194 |
| persona_mix_0.10 | persona_mixture | 0.1 | 0.006 $\pm$ 0.001 | 0.987 | 1.000 | 0.039 |
| persona_mix_0.25 | persona_mixture | 0.25 | 0.000 $\pm$ 0.000 | 0.763 | 0.743 | 0.101 |
| persona_mix_0.50 | persona_mixture | 0.5 | 0.000 $\pm$ 0.000 | 0.371 | 0.589 | 0.377 |
| planner_candidates_32 | planner_candidates | 32 | 1.410 $\pm$ 0.027 | 0.995 | 1.000 | 0.018 |
| planner_candidates_8 | planner_candidates | 8 | 3.838 $\pm$ 0.065 | 0.997 | 1.000 | 0.011 |

## Interpretation guardrails

- Likelihood temperature and additive log-likelihood noise perturb the Bayes update only.
- Calibration drift perturbs both the planner's candidate reward model and its likelihood centers.
- Persona mixtures are genuinely out of library: the environment interpolates adjacent templates while inference retains the original discrete menu.
- Restricted candidate planning measures search-budget sensitivity; it is not a CCE solver experiment.
- These controlled analytic diagnostics do not quantify SOTOPIA's project-defined keyword projection, for which no native intent labels exist.
