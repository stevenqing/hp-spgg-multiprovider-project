# Available Model Performance Analysis

Date: 2026-05-17

This note summarizes the completed K20/s5 CloudGPT model-performance results available before the full Kimi external sweep finishes. Lower final cumulative regret is better; higher welfare is better.

## Coverage

| Layer | DeepSeek-V3.2 | gpt-5.4-nano | Kimi-K2.6 | Llama-4-Maverick |
|---|---:|---:|---:|---:|
| Prompted LLM baselines | complete | complete | complete | complete |
| External A-ToM/ECON baselines | complete | complete via solo shards | partial: atom_tom0 only | complete via solo shards |

## Prompted LLM Baselines

| Model | Best prompted method | Final cumulative regret mean | Std | Mean welfare | Main readout |
|---|---|---:|---:|---:|---|
| DeepSeek-V3.2 | llm_belief | 3.0740 | 2.2308 | 2.7363 | Best prompted model so far; belief modeling gives a large gain. |
| Llama-4-Maverick | llm_greedy | 5.9600 | 8.5805 | 2.5580 | Strong without belief prompt; belief prompt hurts on this model. |
| gpt-5.4-nano | llm_belief | 7.1967 | 3.4749 | 2.4542 | Belief prompt helps substantially, but still trails DeepSeek and Llama-greedy. |
| Kimi-K2.6 | llm_belief | 11.7840 | 3.3336 | 2.2248 | Belief prompt helps, but Kimi is weakest among completed prompted runs. |

Full prompted results:

| Model | Algorithm | Final cumulative regret mean | Std | Mean per-round regret | Mean welfare |
|---|---|---:|---:|---:|---:|
| DeepSeek-V3.2 | llm_greedy | 14.0200 | 14.6643 | 0.7010 | 2.1590 |
| DeepSeek-V3.2 | llm_belief | 3.0740 | 2.2308 | 0.1537 | 2.7363 |
| gpt-5.4-nano | llm_greedy | 17.4060 | 17.8188 | 0.8703 | 1.8857 |
| gpt-5.4-nano | llm_belief | 7.1967 | 3.4749 | 0.3598 | 2.4542 |
| Kimi-K2.6 | llm_greedy | 18.2700 | 7.6479 | 0.9135 | 1.8505 |
| Kimi-K2.6 | llm_belief | 11.7840 | 3.3336 | 0.5892 | 2.2248 |
| Llama-4-Maverick | llm_greedy | 5.9600 | 8.5805 | 0.2980 | 2.5580 |
| Llama-4-Maverick | llm_belief | 10.3560 | 3.8194 | 0.5178 | 2.3522 |

## External A-ToM/ECON Baselines

| Model | Best completed external method | Final cumulative regret mean | Std | Mean welfare | Main readout |
|---|---|---:|---:|---:|---|
| DeepSeek-V3.2 | econ_bne | 3.9900 | 3.4136 | 2.6105 | ECON is strongest; hedge is close and more welfare-oriented. |
| Llama-4-Maverick | econ_bne | 3.3820 | 4.5338 | 2.6029 | Best external result among completed cross-model external sweeps. |
| gpt-5.4-nano | atom_tom0 | 4.0800 | 4.9406 | 2.5860 | Simpler ToM-0 beats ECON/adaptive methods for nano. |
| Kimi-K2.6 | atom_tom0 only so far | 10.6720 | 6.3559 | 2.2564 | Partial only; do not rank Kimi external yet. |

Complete or currently available external results:

| Model | Algorithm | Final cumulative regret mean | Std | Mean per-round regret | Mean welfare | Status |
|---|---|---:|---:|---:|---:|---|
| DeepSeek-V3.2 | atom_tom0 | 6.0000 | 7.4565 | 0.3000 | 2.5900 | complete |
| DeepSeek-V3.2 | atom_tom1 | 16.6760 | 8.2004 | 0.8338 | 2.0182 | complete |
| DeepSeek-V3.2 | atom_tom2 | 13.4020 | 10.3200 | 0.6701 | 2.2139 | complete |
| DeepSeek-V3.2 | atom_adaptive_ftl | 14.9440 | 1.4313 | 0.7472 | 2.0968 | complete |
| DeepSeek-V3.2 | atom_adaptive_hedge | 4.7900 | 4.5089 | 0.2395 | 2.6605 | complete |
| DeepSeek-V3.2 | econ_bne | 3.9900 | 3.4136 | 0.1995 | 2.6105 | complete |
| gpt-5.4-nano | atom_tom0 | 4.0800 | 4.9406 | 0.2040 | 2.5860 | complete shard |
| gpt-5.4-nano | atom_tom1 | 13.4726 | 6.5896 | 0.6736 | 2.0444 | complete shard |
| gpt-5.4-nano | atom_tom2 | 10.2000 | 8.8254 | 0.5100 | 2.2440 | complete shard |
| gpt-5.4-nano | atom_adaptive_ftl | 14.8895 | 2.8454 | 0.7445 | 1.9995 | complete shard |
| gpt-5.4-nano | atom_adaptive_hedge | 7.6530 | 4.9582 | 0.3826 | 2.4414 | complete shard |
| gpt-5.4-nano | econ_bne | 14.8800 | 2.7527 | 0.7440 | 1.9480 | complete shard |
| Kimi-K2.6 | atom_tom0 | 10.6720 | 6.3559 | 0.5336 | 2.2564 | partial external sweep |
| Llama-4-Maverick | atom_tom0 | 7.2400 | 7.7886 | 0.3620 | 2.5240 | complete shard |
| Llama-4-Maverick | atom_tom1 | 15.7100 | 7.9321 | 0.7855 | 2.0825 | complete shard |
| Llama-4-Maverick | atom_tom2 | 11.8660 | 9.3250 | 0.5933 | 2.2507 | complete shard |
| Llama-4-Maverick | atom_adaptive_ftl | 13.9220 | 2.6571 | 0.6961 | 2.0659 | complete shard |
| Llama-4-Maverick | atom_adaptive_hedge | 7.0060 | 4.5831 | 0.3503 | 2.5237 | complete shard |
| Llama-4-Maverick | econ_bne | 3.3820 | 4.5338 | 0.1691 | 2.6029 | complete shard |

## Initial Interpretation

1. Belief prompting is model-dependent. It is strongly beneficial for DeepSeek, nano, and Kimi, but harmful for Llama in this setup. This suggests the belief prompt is not universally calibrated; Llama may already encode a useful cooperative heuristic under the greedy prompt, while the belief prompt may overcomplicate or destabilize its action choices.

2. External reasoning methods are not uniformly better than direct prompted play. DeepSeek and Llama benefit from ECON, while nano performs best with simple `atom_tom0`. This points to a model-by-method interaction rather than a single best external scaffold.

3. Deeper explicit ToM is not monotonic. `atom_tom1` and `atom_tom2` are usually worse than `atom_tom0`, which likely means prediction noise compounds as recursive reasoning depth increases. The practical baseline story is that shallow partner prediction is often more reliable than deeper recursive prompting.

4. Hedge dominates FTL across completed external sweeps. `atom_adaptive_hedge` beats `atom_adaptive_ftl` for DeepSeek, nano, and Llama, consistent with the idea that soft level mixing is safer than committing to a single currently best level under noisy LLM predictions.

5. The strongest completed LLM-family methods are now close to, but still worse than, native planning baselines from the DeepSeek c19 summary. In particular, native `hpsmg_plus` remains around 0.4000 final cumulative regret, while the best completed LLM result here is Llama ECON at 3.3820 and DeepSeek belief at 3.0740.

## Current Takeaway

For the paper narrative, the strongest early claim is not simply "larger/better model wins." The more interesting claim is that hidden-persona social dilemmas expose a three-way interaction among model, social-reasoning scaffold, and uncertainty handling. DeepSeek is strongest under belief prompting, Llama is strongest under direct greedy and ECON scaffolding, nano prefers shallow ToM over ECON, and Kimi currently lags in prompted runs while its external sweep is still incomplete.
