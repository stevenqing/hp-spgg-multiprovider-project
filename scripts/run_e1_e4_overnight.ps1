param(
    [string]$Model = 'Llama-4-Maverick-17B-128E-Instruct-FP8',
    [string]$DeepSeekModel = 'DeepSeek-V3.2',
    [string]$LogPath = 'logs\e1_e4_overnight.log',
    [switch]$SkipE3
)

$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path analysis, figs, tables, logs, results\e1_e4, calibration\e1_e4 | Out-Null

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

$calibs = @{
    'DeepSeek_V3_2' = 'calibration_cloudgpt_multi_model_fast4_8algos_DeepSeek_V3_2_c19.npy'
    'gpt_5_4_nano_20260317' = 'calibration_cloudgpt_multi_model_fast4_8algos_gpt_5_4_nano_20260317_c19.npy'
    'Kimi_K2_6' = 'calibration_cloudgpt_multi_model_fast4_8algos_Kimi_K2_6_c19.npy'
    'Llama_4_Maverick_17B_128E_Instruct_FP8' = 'calibration_cloudgpt_multi_model_fast4_8algos_Llama_4_Maverick_17B_128E_Instruct_FP8_c19.npy'
}

Write-RunLog 'overnight_start E1-E4'

foreach ($slug in $calibs.Keys) {
    Invoke-Step "E1_${slug}" {
        uv run python -m llm_hpgg.run_experiment --K 20 --n 3 --seeds 5 --beta 0 --algos hpsmg --calibration $calibs[$slug] --out "results\e1_e4\E1_posterior_${slug}.npz" --record-posterior --matched-seeds --player-model $slug --judge-model $slug
    }
}
Invoke-Step 'E1_analyze' {
    uv run python scripts\analyze_e1_posterior_concentration.py --inputs results\e1_e4\E1_posterior_*.npz --fig figs\E1_posterior_concentration.png --out-json analysis\E1_posterior_concentration_summary.json --out-csv tables\E1_posterior_concentration.csv
}

foreach ($m in @(2, 3, 4, 5, 6)) {
    Invoke-Step "E2_build_type${m}" {
        uv run python scripts\build_hp_spgg_scaling_calibration.py --n 3 --type-count $m --backend $Model --samples 3 --out "calibration\e1_e4\E2_type${m}_n3_${Model}.npz"
    }
    Invoke-Step "E2_run_type${m}" {
        uv run python -m llm_hpgg.run_experiment --K 20 --n 3 --seeds 5 --beta 0.25 --algos hpsmg hpsmg_plus --calibration "calibration\e1_e4\E2_type${m}_n3_${Model}.npz" --out "results\e1_e4\E2_type${m}_${Model}.npz" --matched-seeds --record-posterior --player-model $Model --judge-model $Model
    }
}
Invoke-Step 'E2_analyze' {
    uv run python scripts\analyze_e2_type_scaling.py --inputs results\e1_e4\E2_type*.npz --fig figs\E2_type_scaling.png --out-json analysis\E2_type_scaling_summary.json --out-csv tables\E2_type_scaling.csv
}

if (-not $SkipE3) {
    foreach ($n in @(2, 3, 4, 5)) {
        Invoke-Step "E3_build_n${n}" {
            uv run python scripts\build_hp_spgg_scaling_calibration.py --n $n --type-count 4 --backend $Model --samples 3 --out "calibration\e1_e4\E3_n${n}_types4_${Model}.npz"
        }
        Invoke-Step "E3_run_n${n}" {
            uv run python -m llm_hpgg.run_experiment --K 20 --n $n --seeds 5 --beta 0.25 --algos hpsmg joint_psrl hpsmg_plus --calibration "calibration\e1_e4\E3_n${n}_types4_${Model}.npz" --out "results\e1_e4\E3_n${n}_${Model}.npz" --matched-seeds --record-posterior --player-model $Model --judge-model $Model
        }
    }
    Invoke-Step 'E3_analyze' {
        uv run python scripts\analyze_e3_n_agent_scaling.py --inputs results\e1_e4\E3_n*.npz --fig figs\E3_n_agent_scaling.png --out-json analysis\E3_n_agent_scaling_summary.json --out-csv tables\E3_n_agent_scaling.csv
    }
}

$deepSeekCalib = $calibs['DeepSeek_V3_2']
foreach ($prior in @('uniform', 'correct', 'adversarial')) {
    Invoke-Step "E4_prior_${prior}" {
        uv run python -m llm_hpgg.run_experiment --K 20 --n 3 --seeds 5 --beta 0 --algos hpsmg map_greedy --calibration $deepSeekCalib --out "results\e1_e4\E4_prior_${prior}_DeepSeek_V3_2.npz" --prior-mode $prior --prior-mass 0.7 --matched-seeds --record-posterior --player-model $DeepSeekModel --judge-model $DeepSeekModel
    }
}
Invoke-Step 'E4_analyze' {
    uv run python scripts\analyze_e4_prior_recovery.py --inputs results\e1_e4\E4_prior_*_DeepSeek_V3_2.npz --fig figs\E4_prior_recovery.png --out-json analysis\E4_prior_recovery_summary.json --out-csv tables\E4_prior_recovery.csv
}

Write-RunLog 'overnight_complete E1-E4'