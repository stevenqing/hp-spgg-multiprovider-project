# SOTOPIA-hard Tuned-Profile All-70 Full Results
Source files (20):
- `analysis\sotopia_hard_official_DeepSeek_V3_2_atom_tom1_sotopia_tuned_all70.json`
- `analysis\sotopia_hard_official_DeepSeek_V3_2_econ_bne_sotopia_tuned_all70.json`
- `analysis\sotopia_hard_official_DeepSeek_V3_2_hpsmg_plus_sotopia_tuned_all70.json`
- `analysis\sotopia_hard_official_DeepSeek_V3_2_llm_belief_sotopia_tuned_all70.json`
- `analysis\sotopia_hard_official_DeepSeek_V3_2_llm_greedy_sotopia_tuned_all70.json`
- `analysis\sotopia_hard_official_Kimi_K2_6_atom_tom1_sotopia_tuned_all70.json`
- `analysis\sotopia_hard_official_Kimi_K2_6_econ_bne_sotopia_tuned_all70.json`
- `analysis\sotopia_hard_official_Kimi_K2_6_hpsmg_plus_sotopia_tuned_all70.json`
- `analysis\sotopia_hard_official_Kimi_K2_6_llm_belief_sotopia_tuned_all70.json`
- `analysis\sotopia_hard_official_Kimi_K2_6_llm_greedy_sotopia_tuned_all70.json`
- `analysis\sotopia_hard_official_Llama_4_Maverick_17B_128E_Instruct_FP8_atom_tom1_sotopia_tuned_all70.json`
- `analysis\sotopia_hard_official_Llama_4_Maverick_17B_128E_Instruct_FP8_econ_bne_sotopia_tuned_all70.json`
- `analysis\sotopia_hard_official_Llama_4_Maverick_17B_128E_Instruct_FP8_hpsmg_plus_sotopia_tuned_all70.json`
- `analysis\sotopia_hard_official_Llama_4_Maverick_17B_128E_Instruct_FP8_llm_belief_sotopia_tuned_all70.json`
- `analysis\sotopia_hard_official_Llama_4_Maverick_17B_128E_Instruct_FP8_llm_greedy_sotopia_tuned_all70.json`
- `analysis\sotopia_hard_official_gpt_5_4_nano_20260317_atom_tom1_sotopia_tuned_all70.json`
- `analysis\sotopia_hard_official_gpt_5_4_nano_20260317_econ_bne_sotopia_tuned_all70.json`
- `analysis\sotopia_hard_official_gpt_5_4_nano_20260317_hpsmg_plus_sotopia_tuned_all70.json`
- `analysis\sotopia_hard_official_gpt_5_4_nano_20260317_llm_belief_sotopia_tuned_all70.json`
- `analysis\sotopia_hard_official_gpt_5_4_nano_20260317_llm_greedy_sotopia_tuned_all70.json`

_Score = mean of `episode.overall.agent_1` and `episode.overall.agent_2` (Sotopia self-play overall)._

## 1. Aggregate mean focal score (per model x baseline, averaged over 70 episodes)

| model | hpsmg_plus | atom_tom1 | econ_bne | llm_belief | llm_greedy | best | hp+_rank | Δ_vs_2nd |
|---|---|---|---|---|---|---|---|---|
| DeepSeek_V3_2 | 3.248 | 3.261 | 3.313 | 3.195 | 3.193 | econ_bne | 3 | -0.065 |
| Kimi_K2_6 | 2.807 | 2.733 | 2.876 | 2.906 | 2.761 | llm_belief | 3 | -0.099 |
| Llama_4_Maverick_17B_128E_Instruct_FP8 | 3.308 | 3.359 | 3.319 | 3.340 | 3.165 | atom_tom1 | 4 | -0.051 |
| gpt_5_4_nano_20260317 | 2.981 | 2.918 | 2.843 | 3.000 | 2.842 | llm_belief | 2 | -0.019 |

**Average across models:**

| baseline | avg |
|---|---|
| hpsmg_plus | 3.086 |
| atom_tom1 | 3.068 |
| econ_bne | 3.088 |
| llm_belief | 3.110 |
| llm_greedy | 2.990 |

## 2. Per-(model, codename) mean scores (averaged over repeated episodes)

### DeepSeek_V3_2

| codename | n | hpsmg_plus | atom_tom1 | econ_bne | llm_belief | llm_greedy | best | Δ(hp+ − best_other) |
|---|---|---|---|---|---|---|---|---|
| craigslist_bargains_00000 | 5 | 3.386 | 3.229 | 2.986 | 3.500 | 3.143 | llm_belief | -0.114 |
| craigslist_bargains_00002 | 5 | 3.100 | 3.043 | 3.186 | 2.936 | 2.971 | econ_bne | -0.086 |
| craigslist_bargains_00003 | 5 | 3.557 | 3.043 | 3.300 | 3.014 | 3.371 | hpsmg_plus | +0.186 |
| craigslist_bargains_00007 | 5 | 3.314 | 3.271 | 2.871 | 3.071 | 2.914 | hpsmg_plus | +0.043 |
| divide_items | 5 | 3.857 | 3.514 | 3.814 | 3.700 | 3.486 | hpsmg_plus | +0.043 |
| donate_funds | 5 | 3.000 | 3.500 | 3.414 | 3.557 | 3.086 | llm_belief | -0.557 |
| game_winning | 5 | 3.057 | 3.243 | 3.271 | 3.043 | 3.400 | llm_greedy | -0.343 |
| join_trip | 5 | 3.600 | 3.929 | 3.671 | 3.557 | 3.771 | atom_tom1 | -0.329 |
| revenge_plot | 5 | 2.829 | 2.829 | 2.600 | 2.357 | 2.514 | atom_tom1 | -0.000 |
| sell_item | 5 | 2.800 | 3.571 | 3.686 | 3.343 | 3.471 | econ_bne | -0.886 |
| share_blanket | 5 | 2.843 | 3.129 | 2.957 | 2.871 | 3.229 | llm_greedy | -0.386 |
| share_stuff | 5 | 3.357 | 2.914 | 3.543 | 3.243 | 2.843 | econ_bne | -0.186 |
| sleep_arrangement | 5 | 3.729 | 3.600 | 3.657 | 3.629 | 3.471 | hpsmg_plus | +0.071 |
| unwelcome_guest | 5 | 3.043 | 2.843 | 3.429 | 2.914 | 3.029 | econ_bne | -0.386 |

### Kimi_K2_6

| codename | n | hpsmg_plus | atom_tom1 | econ_bne | llm_belief | llm_greedy | best | Δ(hp+ − best_other) |
|---|---|---|---|---|---|---|---|---|
| craigslist_bargains_00000 | 5 | 2.586 | 2.029 | 2.357 | 2.086 | 2.400 | hpsmg_plus | +0.186 |
| craigslist_bargains_00002 | 5 | 2.757 | 2.786 | 2.714 | 2.529 | 2.943 | llm_greedy | -0.186 |
| craigslist_bargains_00003 | 5 | 1.757 | 2.257 | 2.286 | 2.200 | 2.143 | econ_bne | -0.529 |
| craigslist_bargains_00007 | 5 | 2.500 | 2.329 | 2.386 | 2.314 | 2.157 | hpsmg_plus | +0.114 |
| divide_items | 5 | 2.300 | 2.471 | 2.757 | 3.043 | 2.429 | llm_belief | -0.743 |
| donate_funds | 5 | 3.114 | 2.829 | 2.571 | 2.914 | 2.571 | hpsmg_plus | +0.200 |
| game_winning | 5 | 2.986 | 3.071 | 2.943 | 3.229 | 2.786 | llm_belief | -0.243 |
| join_trip | 5 | 3.271 | 3.100 | 3.357 | 3.743 | 3.486 | llm_belief | -0.471 |
| revenge_plot | 5 | 3.057 | 2.386 | 2.800 | 2.743 | 2.514 | hpsmg_plus | +0.257 |
| sell_item | 5 | 3.029 | 3.014 | 3.100 | 3.286 | 3.200 | llm_belief | -0.257 |
| share_blanket | 5 | 2.771 | 2.900 | 3.014 | 2.900 | 2.843 | econ_bne | -0.243 |
| share_stuff | 5 | 3.086 | 3.129 | 3.643 | 3.357 | 3.043 | econ_bne | -0.557 |
| sleep_arrangement | 5 | 3.171 | 3.071 | 3.200 | 3.157 | 3.214 | llm_greedy | -0.043 |
| unwelcome_guest | 5 | 2.914 | 2.886 | 3.129 | 3.186 | 2.929 | llm_belief | -0.271 |

### Llama_4_Maverick_17B_128E_Instruct_FP8

| codename | n | hpsmg_plus | atom_tom1 | econ_bne | llm_belief | llm_greedy | best | Δ(hp+ − best_other) |
|---|---|---|---|---|---|---|---|---|
| craigslist_bargains_00000 | 5 | 3.457 | 3.614 | 3.557 | 3.514 | 3.600 | atom_tom1 | -0.157 |
| craigslist_bargains_00002 | 5 | 3.943 | 3.929 | 3.843 | 4.057 | 3.657 | llm_belief | -0.114 |
| craigslist_bargains_00003 | 5 | 3.614 | 3.757 | 3.614 | 3.600 | 3.514 | atom_tom1 | -0.143 |
| craigslist_bargains_00007 | 5 | 3.657 | 3.700 | 3.329 | 3.514 | 3.386 | atom_tom1 | -0.043 |
| divide_items | 5 | 4.143 | 4.271 | 3.986 | 3.943 | 3.886 | atom_tom1 | -0.129 |
| donate_funds | 5 | 3.214 | 3.257 | 3.414 | 3.171 | 3.129 | econ_bne | -0.200 |
| game_winning | 5 | 2.800 | 2.829 | 2.857 | 2.814 | 2.957 | llm_greedy | -0.157 |
| join_trip | 5 | 3.743 | 3.857 | 3.700 | 3.700 | 3.614 | atom_tom1 | -0.114 |
| revenge_plot | 5 | 3.000 | 3.029 | 3.100 | 3.029 | 2.914 | econ_bne | -0.100 |
| sell_item | 5 | 2.629 | 2.629 | 2.829 | 2.700 | 2.343 | econ_bne | -0.200 |
| share_blanket | 5 | 2.857 | 3.014 | 3.029 | 3.086 | 2.457 | llm_belief | -0.229 |
| share_stuff | 5 | 2.614 | 2.829 | 2.771 | 3.014 | 2.457 | llm_belief | -0.400 |
| sleep_arrangement | 5 | 3.586 | 3.300 | 3.500 | 3.400 | 3.514 | hpsmg_plus | +0.071 |
| unwelcome_guest | 5 | 3.057 | 3.014 | 2.943 | 3.214 | 2.886 | llm_belief | -0.157 |

### gpt_5_4_nano_20260317

| codename | n | hpsmg_plus | atom_tom1 | econ_bne | llm_belief | llm_greedy | best | Δ(hp+ − best_other) |
|---|---|---|---|---|---|---|---|---|
| craigslist_bargains_00000 | 5 | 2.129 | 2.629 | 2.071 | 2.329 | 2.300 | atom_tom1 | -0.500 |
| craigslist_bargains_00002 | 5 | 3.471 | 2.714 | 2.757 | 3.171 | 2.914 | hpsmg_plus | +0.300 |
| craigslist_bargains_00003 | 5 | 2.500 | 2.500 | 2.486 | 2.571 | 2.571 | llm_belief | -0.071 |
| craigslist_bargains_00007 | 5 | 2.900 | 2.786 | 3.000 | 2.971 | 2.643 | econ_bne | -0.100 |
| divide_items | 5 | 3.429 | 3.643 | 3.429 | 4.357 | 3.386 | llm_belief | -0.929 |
| donate_funds | 5 | 3.714 | 3.386 | 2.771 | 3.257 | 3.114 | hpsmg_plus | +0.329 |
| game_winning | 5 | 3.014 | 3.429 | 2.829 | 3.371 | 3.129 | atom_tom1 | -0.414 |
| join_trip | 5 | 2.929 | 2.671 | 2.543 | 2.729 | 2.100 | hpsmg_plus | +0.200 |
| revenge_plot | 5 | 2.843 | 2.800 | 2.829 | 2.829 | 3.200 | llm_greedy | -0.357 |
| sell_item | 5 | 3.100 | 3.000 | 3.243 | 3.071 | 3.029 | econ_bne | -0.143 |
| share_blanket | 5 | 2.143 | 2.043 | 2.486 | 1.943 | 2.543 | llm_greedy | -0.400 |
| share_stuff | 5 | 3.729 | 3.286 | 3.271 | 3.743 | 3.271 | llm_belief | -0.014 |
| sleep_arrangement | 5 | 3.214 | 3.300 | 3.414 | 3.029 | 3.300 | econ_bne | -0.200 |
| unwelcome_guest | 5 | 2.614 | 2.671 | 2.671 | 2.629 | 2.286 | atom_tom1 | -0.057 |

## 3. Winner counts across (model, codename) pairs (using averaged scores)

Total (model, codename) pairs with hpsmg_plus + ≥1 other baseline: **56**

| baseline | wins | win% |
|---|---|---|
| hpsmg_plus | 12 | 21.4% |
| atom_tom1 | 10 | 17.9% |
| econ_bne | 13 | 23.2% |
| llm_belief | 14 | 25.0% |
| llm_greedy | 7 | 12.5% |

## 4. Scenario-family breakdown

### 4a. Winner counts per family

| family | hpsmg_plus | atom_tom1 | econ_bne | llm_belief | llm_greedy | n |
|---|---|---|---|---|---|---|
| craigslist_bargains | 5 | 4 | 3 | 3 | 1 | 16 |
| donate_funds | 2 | 0 | 1 | 1 | 0 | 4 |
| revenge_plot | 1 | 1 | 1 | 0 | 1 | 4 |
| sleep_arrangement | 2 | 0 | 1 | 0 | 1 | 4 |
| join_trip | 1 | 2 | 0 | 1 | 0 | 4 |
| game_winning | 0 | 1 | 0 | 1 | 2 | 4 |
| divide_items | 1 | 1 | 0 | 2 | 0 | 4 |
| sell_item | 0 | 0 | 3 | 1 | 0 | 4 |
| unwelcome_guest | 0 | 1 | 1 | 2 | 0 | 4 |
| share_blanket | 0 | 0 | 1 | 1 | 2 | 4 |
| share_stuff | 0 | 0 | 2 | 2 | 0 | 4 |

### 4b. hpsmg_plus mean margin vs best alternative per family

| family | mean margin | n | win-rate |
|---|---|---|---|
| sleep_arrangement | -0.025 | 4 | 50.0% |
| revenge_plot | -0.050 | 4 | 25.0% |
| donate_funds | -0.057 | 4 | 50.0% |
| craigslist_bargains | -0.076 | 16 | 31.2% |
| join_trip | -0.179 | 4 | 25.0% |
| unwelcome_guest | -0.218 | 4 | 0.0% |
| game_winning | -0.289 | 4 | 0.0% |
| share_stuff | -0.289 | 4 | 0.0% |
| share_blanket | -0.314 | 4 | 0.0% |
| sell_item | -0.371 | 4 | 0.0% |
| divide_items | -0.439 | 4 | 25.0% |

## 5. Top scenarios for hpsmg_plus

### 5a. Largest advantage (Δ = hpsmg_plus − best other)

| Δ | model | codename |
|---|---|---|
| +0.329 | gpt_5_4_nano_20260317 | donate_funds |
| +0.300 | gpt_5_4_nano_20260317 | craigslist_bargains_00002 |
| +0.257 | Kimi_K2_6 | revenge_plot |
| +0.200 | Kimi_K2_6 | donate_funds |
| +0.200 | gpt_5_4_nano_20260317 | join_trip |
| +0.186 | Kimi_K2_6 | craigslist_bargains_00000 |
| +0.186 | DeepSeek_V3_2 | craigslist_bargains_00003 |
| +0.114 | Kimi_K2_6 | craigslist_bargains_00007 |
| +0.071 | DeepSeek_V3_2 | sleep_arrangement |
| +0.071 | Llama_4_Maverick_17B_128E_Instruct_FP8 | sleep_arrangement |
| +0.043 | DeepSeek_V3_2 | craigslist_bargains_00007 |
| +0.043 | DeepSeek_V3_2 | divide_items |
| -0.000 | DeepSeek_V3_2 | revenge_plot |
| -0.014 | gpt_5_4_nano_20260317 | share_stuff |
| -0.043 | Kimi_K2_6 | sleep_arrangement |

### 5b. Largest disadvantage

| Δ | model | codename |
|---|---|---|
| -0.929 | gpt_5_4_nano_20260317 | divide_items |
| -0.886 | DeepSeek_V3_2 | sell_item |
| -0.743 | Kimi_K2_6 | divide_items |
| -0.557 | Kimi_K2_6 | share_stuff |
| -0.557 | DeepSeek_V3_2 | donate_funds |
| -0.529 | Kimi_K2_6 | craigslist_bargains_00003 |
| -0.500 | gpt_5_4_nano_20260317 | craigslist_bargains_00000 |
| -0.471 | Kimi_K2_6 | join_trip |
| -0.414 | gpt_5_4_nano_20260317 | game_winning |
| -0.400 | Llama_4_Maverick_17B_128E_Instruct_FP8 | share_stuff |
| -0.400 | gpt_5_4_nano_20260317 | share_blanket |
| -0.386 | DeepSeek_V3_2 | share_blanket |
| -0.386 | DeepSeek_V3_2 | unwelcome_guest |
| -0.357 | gpt_5_4_nano_20260317 | revenge_plot |
| -0.343 | DeepSeek_V3_2 | game_winning |

## 6. Per-agent (focal=agent_1 vs partner=agent_2) means per baseline

Baseline strategy controls **both** agents in Sotopia self-play; this column shows whether the asymmetry between roles matters.

| model | baseline | agent_1 mean | agent_2 mean | symmetric mean |
|---|---|---|---|---|
| DeepSeek_V3_2 | hpsmg_plus | 2.982 | 3.514 | 3.248 |
| DeepSeek_V3_2 | atom_tom1 | 3.069 | 3.453 | 3.261 |
| DeepSeek_V3_2 | econ_bne | 3.055 | 3.571 | 3.313 |
| DeepSeek_V3_2 | llm_belief | 2.947 | 3.444 | 3.195 |
| DeepSeek_V3_2 | llm_greedy | 2.957 | 3.429 | 3.193 |
| Kimi_K2_6 | hpsmg_plus | 2.653 | 2.961 | 2.807 |
| Kimi_K2_6 | atom_tom1 | 2.578 | 2.888 | 2.733 |
| Kimi_K2_6 | econ_bne | 2.686 | 3.065 | 2.876 |
| Kimi_K2_6 | llm_belief | 2.712 | 3.100 | 2.906 |
| Kimi_K2_6 | llm_greedy | 2.588 | 2.935 | 2.761 |
| Llama_4_Maverick_17B_128E_Instruct_FP8 | hpsmg_plus | 3.386 | 3.231 | 3.308 |
| Llama_4_Maverick_17B_128E_Instruct_FP8 | atom_tom1 | 3.422 | 3.296 | 3.359 |
| Llama_4_Maverick_17B_128E_Instruct_FP8 | econ_bne | 3.382 | 3.257 | 3.319 |
| Llama_4_Maverick_17B_128E_Instruct_FP8 | llm_belief | 3.431 | 3.249 | 3.340 |
| Llama_4_Maverick_17B_128E_Instruct_FP8 | llm_greedy | 3.184 | 3.147 | 3.165 |
| gpt_5_4_nano_20260317 | hpsmg_plus | 3.122 | 2.839 | 2.981 |
| gpt_5_4_nano_20260317 | atom_tom1 | 2.994 | 2.843 | 2.918 |
| gpt_5_4_nano_20260317 | econ_bne | 2.961 | 2.724 | 2.843 |
| gpt_5_4_nano_20260317 | llm_belief | 3.118 | 2.882 | 3.000 |
| gpt_5_4_nano_20260317 | llm_greedy | 2.876 | 2.808 | 2.842 |
