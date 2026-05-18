param(
    [string]$Model = 'Llama-4-Maverick-17B-128E-Instruct-FP8'
)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true
New-Item -ItemType Directory -Force -Path analysis, figs, tables, logs, results\e1_e4_llm_smoke, calibration\e1_e4_llm_smoke | Out-Null

$env:LLM_HPGG_BACKEND = 'cloudgpt'
$env:LLM_HPGG_PLAYER_BACKEND = 'cloudgpt'
$env:LLM_HPGG_JUDGE_BACKEND = 'cloudgpt'
$env:CLOUDGPT_USE_AZURE_CLI = '1'
$env:CLOUDGPT_TIMEOUT = '180'
$env:CLOUDGPT_MAX_RETRIES = '2'
$env:LLM_HPGG_OFFLINE = '0'

Write-Host '[llm-smoke:E2] live scaling calibration m=2, profile_count=1'
uv run python scripts\build_hp_spgg_scaling_live_calibration.py --n 3 --type-count 2 --judge-model $Model --profile-count 1 --workers 1 --out calibration\e1_e4_llm_smoke\E2_type2_live.npz --report analysis\E2_type2_live_smoke_report.json --cache logs\E2_type2_live_smoke_cache.jsonl
uv run python -m llm_hpgg.run_experiment --K 3 --n 3 --seeds 1 --beta 0.25 --algos hpsmg hpsmg_plus --calibration calibration\e1_e4_llm_smoke\E2_type2_live.npz --out results\e1_e4_llm_smoke\E2_type2_live_smoke.npz --matched-seeds --record-posterior --player-model $Model --judge-model $Model
uv run python scripts\analyze_e2_type_scaling.py --inputs results\e1_e4_llm_smoke\E2_type2_live_smoke.npz --fig figs\E2_type_scaling_llm_smoke.png --out-json analysis\E2_type_scaling_llm_smoke.json --out-csv tables\E2_type_scaling_llm_smoke.csv

Write-Host '[llm-smoke:E3] live n-agent calibration n=2, profile_count=1'
uv run python scripts\build_hp_spgg_scaling_live_calibration.py --n 2 --type-count 4 --judge-model $Model --profile-count 1 --workers 1 --out calibration\e1_e4_llm_smoke\E3_n2_live.npz --report analysis\E3_n2_live_smoke_report.json --cache logs\E3_n2_live_smoke_cache.jsonl
uv run python -m llm_hpgg.run_experiment --K 3 --n 2 --seeds 1 --beta 0.25 --algos hpsmg joint_psrl hpsmg_plus --calibration calibration\e1_e4_llm_smoke\E3_n2_live.npz --out results\e1_e4_llm_smoke\E3_n2_live_smoke.npz --matched-seeds --record-posterior --player-model $Model --judge-model $Model
uv run python scripts\analyze_e3_n_agent_scaling.py --inputs results\e1_e4_llm_smoke\E3_n2_live_smoke.npz --fig figs\E3_n_agent_scaling_llm_smoke.png --out-json analysis\E3_n_agent_scaling_llm_smoke.json --out-csv tables\E3_n_agent_scaling_llm_smoke.csv

Write-Host 'llm_smoke_complete=True'