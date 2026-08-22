# E-A Matched-Likelihood Audit

**Status: blocked; no matched-likelihood result is claimed.**

The recovered historical external baselines already received analytic c19 rewards in `recent_public_history`, but their runner used algorithm-specific RNG seeds. Thus they do not share PACT's type profiles or initial states. The raw c19 calibration tensors and LLM response caches were not retained, so a valid matched rerun requires fresh model calls.

| model | PACT+ | best PACT-family | best historical baseline | family ratio | matched? |
|---|---:|---:|---:|---:|---|
| DeepSeek-V3.2 | 0.400 $\pm$ 0.400 | hpsmg_plus 0.400 $\pm$ 0.400 | econ_bne 3.990 $\pm$ 1.707 | 9.97$\times$ | no |
| GPT-5.4-nano | 0.912 $\pm$ 0.146 | hpsmg 0.644 $\pm$ 0.315 | atom_tom0 4.080 $\pm$ 2.470 | 6.34$\times$ | no |
| Kimi-K2.6 | 0.704 $\pm$ 0.218 | hpsmg 0.632 $\pm$ 0.305 | atom_adaptive_hedge 7.484 $\pm$ 2.048 | 11.84$\times$ | no |
| Llama-4-Maverick | 0.312 $\pm$ 0.312 | hpsmg_plus 0.312 $\pm$ 0.312 | econ_bne 3.382 $\pm$ 2.267 | 10.84$\times$ | no |

No appendix matched-control table should be added from these rows. They are retained only to expose provenance and to prevent the old aggregate from being mislabeled as E-A.
