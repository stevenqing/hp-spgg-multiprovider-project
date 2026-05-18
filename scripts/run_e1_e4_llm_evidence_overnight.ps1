param(
    [int]$ProfileCount = 19,
    [int]$Workers = 2,
    [string]$LogPath = 'logs\e1_e4_llm_evidence_overnight.log'
)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true
New-Item -ItemType Directory -Force -Path analysis, figs, tables, logs, results\e1_e4_llm, calibration\e1_e4_llm | Out-Null

$env:LLM_HPGG_BACKEND = 'cloudgpt'
$env:LLM_HPGG_PLAYER_BACKEND = 'cloudgpt'
$env:LLM_HPGG_JUDGE_BACKEND = 'cloudgpt'
$env:CLOUDGPT_USE_AZURE_CLI = '1'
$env:CLOUDGPT_TIMEOUT = '180'
$env:CLOUDGPT_MAX_RETRIES = '2'
$env:LLM_HPGG_OFFLINE = '0'

function Write-RunLog([string]$Message) {
    $line = '[{0}] {1}' -f (Get-Date).ToString('yyyy-MM-dd HH:mm:ss'), $Message
    Add-Content -Path $LogPath -Value $line -Encoding UTF8
    Write-Host $line
}

function Invoke-Step([string]$Name, [scriptblock]$Block) {
    Write-RunLog "start $Name"
    & $Block 2>&1 | Tee-Object -FilePath "logs\${Name}.log"
    Write-RunLog "done $Name"
}

$models = @(
    @{ Slug = 'DeepSeek_V3_2'; Model = 'DeepSeek-V3.2'; Calib = 'calibration_cloudgpt_multi_model_fast4_8algos_DeepSeek_V3_2_c19.npy' },
    @{ Slug = 'gpt_5_4_nano_20260317'; Model = 'gpt-5.4-nano-20260317'; Calib = 'calibration_cloudgpt_multi_model_fast4_8algos_gpt_5_4_nano_20260317_c19.npy' },
    @{ Slug = 'Kimi_K2_6'; Model = 'Kimi-K2.6'; Calib = 'calibration_cloudgpt_multi_model_fast4_8algos_Kimi_K2_6_c19.npy' },
    @{ Slug = 'Llama_4_Maverick_17B_128E_Instruct_FP8'; Model = 'Llama-4-Maverick-17B-128E-Instruct-FP8'; Calib = 'calibration_cloudgpt_multi_model_fast4_8algos_Llama_4_Maverick_17B_128E_Instruct_FP8_c19.npy' }
)

Write-RunLog "overnight_start E1-E4 LLM evidence profile_count=$ProfileCount workers=$Workers"

foreach ($entry in $models) {
    $slug = $entry.Slug
    $model = $entry.Model
    Invoke-Step "E1_live_refresh_${slug}" {
        uv run python -m llm_hpgg.calibration_live --backend cloudgpt --judge-model $model --base-calibration $entry.Calib --out "calibration\e1_e4_llm\E1_c19_${slug}_live.npy" --report "analysis\E1_c19_${slug}_live_report.json" --cache "logs\E1_c19_${slug}_live_cache.jsonl" --samples 1 --max-profiles $ProfileCount --workers $Workers --save-every 24
    }
    Invoke-Step "E1_run_${slug}" {
        uv run python -m llm_hpgg.run_experiment --K 20 --n 3 --seeds 5 --beta 0 --algos hpsmg --calibration "calibration\e1_e4_llm\E1_c19_${slug}_live.npy" --out "results\e1_e4_llm\E1_posterior_${slug}_live.npz" --record-posterior --matched-seeds --player-model $model --judge-model $model
    }
}
Invoke-Step 'E1_llm_analyze' {
    uv run python scripts\analyze_e1_posterior_concentration.py --inputs results\e1_e4_llm\E1_posterior_*_live.npz --fig figs\E1_posterior_concentration_llm.png --out-json analysis\E1_posterior_concentration_llm_summary.json --out-csv tables\E1_posterior_concentration_llm.csv
}

$llama = 'Llama-4-Maverick-17B-128E-Instruct-FP8'
foreach ($m in @(2, 3, 4, 5, 6)) {
    Invoke-Step "E2_live_calib_type${m}" {
        uv run python scripts\build_hp_spgg_scaling_live_calibration.py --n 3 --type-count $m --judge-model $llama --profile-count $ProfileCount --workers $Workers --out "calibration\e1_e4_llm\E2_type${m}_live.npz" --report "analysis\E2_type${m}_live_report.json" --cache "logs\E2_type${m}_live_cache.jsonl"
    }
    Invoke-Step "E2_run_type${m}" {
        uv run python -m llm_hpgg.run_experiment --K 20 --n 3 --seeds 5 --beta 0.25 --algos hpsmg hpsmg_plus --calibration "calibration\e1_e4_llm\E2_type${m}_live.npz" --out "results\e1_e4_llm\E2_type${m}_live.npz" --matched-seeds --record-posterior --player-model $llama --judge-model $llama
    }
}
Invoke-Step 'E2_llm_analyze' {
    uv run python scripts\analyze_e2_type_scaling.py --inputs results\e1_e4_llm\E2_type*_live.npz --fig figs\E2_type_scaling_llm.png --out-json analysis\E2_type_scaling_llm_summary.json --out-csv tables\E2_type_scaling_llm.csv
}

foreach ($n in @(2, 3, 4, 5)) {
    Invoke-Step "E3_live_calib_n${n}" {
        uv run python scripts\build_hp_spgg_scaling_live_calibration.py --n $n --type-count 4 --judge-model $llama --profile-count $ProfileCount --workers $Workers --out "calibration\e1_e4_llm\E3_n${n}_live.npz" --report "analysis\E3_n${n}_live_report.json" --cache "logs\E3_n${n}_live_cache.jsonl"
    }
    Invoke-Step "E3_run_n${n}" {
        uv run python -m llm_hpgg.run_experiment --K 20 --n $n --seeds 5 --beta 0.25 --algos hpsmg joint_psrl hpsmg_plus --calibration "calibration\e1_e4_llm\E3_n${n}_live.npz" --out "results\e1_e4_llm\E3_n${n}_live.npz" --matched-seeds --record-posterior --player-model $llama --judge-model $llama
    }
}
Invoke-Step 'E3_llm_analyze' {
    uv run python scripts\analyze_e3_n_agent_scaling.py --inputs results\e1_e4_llm\E3_n*_live.npz --fig figs\E3_n_agent_scaling_llm.png --out-json analysis\E3_n_agent_scaling_llm_summary.json --out-csv tables\E3_n_agent_scaling_llm.csv
}

foreach ($prior in @('uniform', 'correct', 'adversarial')) {
    Invoke-Step "E4_llm_prior_${prior}" {
        uv run python -m llm_hpgg.run_experiment --K 20 --n 3 --seeds 5 --beta 0 --algos hpsmg map_greedy --calibration calibration\e1_e4_llm\E1_c19_DeepSeek_V3_2_live.npy --out "results\e1_e4_llm\E4_prior_${prior}_DeepSeek_V3_2_live.npz" --prior-mode $prior --prior-mass 0.7 --matched-seeds --record-posterior --player-model DeepSeek-V3.2 --judge-model DeepSeek-V3.2
    }
}
Invoke-Step 'E4_llm_analyze' {
    uv run python scripts\analyze_e4_prior_recovery.py --inputs results\e1_e4_llm\E4_prior_*_DeepSeek_V3_2_live.npz --fig figs\E4_prior_recovery_llm.png --out-json analysis\E4_prior_recovery_llm_summary.json --out-csv tables\E4_prior_recovery_llm.csv
}

Write-RunLog 'overnight_complete E1-E4 LLM evidence'