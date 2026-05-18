param(
    [double]$MinHours = 10.0,
    [int]$ProfilesPerModelBatch = 4,
    [int]$Workers = 12,
    [string]$ModelWorkers = "gpt-5.5-20260424=4",
    [bool]$RunProbe = $true,
    [int]$K = 20,
    [int]$Seeds = 5,
    [string[]]$Algorithms = @("hpsmg_plus", "hpsmg", "joint_psrl", "map_greedy", "psrl_notype", "iql_independent_actions", "iql", "random", "oracle"),
    [double[]]$Betas = @(0.0, 0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 1.5),
    [string]$StartCalibration = "calibration_cloudgpt_live_continued.npy",
    [string]$OutPrefix = "calibration_cloudgpt_multi_model",
    [string[]]$Models = @(
        "gpt-5.5-20260424",
        "DeepSeek-V3.2",
        "Kimi-K2.6",
        "Llama-4-Maverick-17B-128E-Instruct-FP8",
        "grok-4"
    ),
    [string]$KnownProfileOrder = "2,8,14,20,26,32,39,46,53,61,69,76,84,92,100,108,116,123,1,3,4,6,7,9,10,12,13,15,17,18,19,21,23,24,25,28,29,30,31,34,35,36,37,40,41,42,43,44,47,48,50,51,52,54,55,57,58,59,62,63,64,65,66,68,70,72,73,74,75,77,79,80,81,83,85,86,87,88,89,91,94,95,96,97,98,99,102,103,105,106,107,109,110,111,113,114,117,118,119,120,121,122,0,11,22,33,45,56,67,78,90,101,112,124"
)

$ErrorActionPreference = "Stop"

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Command
    )
    Write-Host ""
    Write-Host "===== $Name ====="
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed: $Name (exit=$LASTEXITCODE)"
    }
}

function ConvertTo-SafeName {
    param([string]$Value)
    return ($Value -replace "[^A-Za-z0-9]+", "_").Trim("_")
}

function Get-CompletedProfilesFromCache {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        return @()
    }
    $entries = Get-Content $Path | Where-Object { $_.Trim().Length -gt 0 } | ForEach-Object { $_ | ConvertFrom-Json }
    if (-not $entries) {
        return @()
    }
    return @(
        $entries |
            Group-Object -Property profile_index |
            Where-Object { $_.Count -ge 12 } |
            ForEach-Object { [int]$_.Name }
    )
}

function Format-BetaName {
    param([double]$Beta)
    return ($Beta.ToString("0.###") -replace "\.", "p")
}

function Get-WorkerMap {
    param([string]$Raw)
    $map = @{}
    if (-not $Raw) {
        return $map
    }
    foreach ($item in $Raw.Split(",")) {
        if (-not $item.Trim()) {
            continue
        }
        $parts = $item.Split("=", 2)
        if ($parts.Count -eq 2) {
            $map[$parts[0].Trim()] = [int]$parts[1].Trim()
        }
    }
    return $map
}

New-Item -ItemType Directory -Force -Path logs, analysis, results/cloudgpt | Out-Null
$runStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$transcriptPath = "logs/cloudgpt_multi_model_live_$runStamp.log"
Start-Transcript -Path $transcriptPath | Out-Null

try {
    $env:LLM_HPGG_BACKEND = "cloudgpt"
    $env:CLOUDGPT_USE_AZURE_CLI = "1"
    $profileOrder = $KnownProfileOrder.Split(",") | Where-Object { $_.Trim().Length -gt 0 } | ForEach-Object { [int]$_.Trim() }
    $startedAt = Get-Date
    $currentCalibrationByModel = @{}
    $workerMap = Get-WorkerMap -Raw $ModelWorkers

    if (-not (Test-Path $StartCalibration)) {
        throw "Start calibration not found: $StartCalibration"
    }

    Write-Host "multi-model run started=$startedAt min_hours=$MinHours profiles_per_model_batch=$ProfilesPerModelBatch workers=$Workers model_workers=$ModelWorkers"
    Write-Host "models=$($Models -join ', ')"
    Write-Host "algorithms=$($Algorithms -join ', ')"
    Write-Host "start_calibration=$StartCalibration"

    if ($RunProbe) {
        Invoke-Step "probe requested CloudGPT models" {
            $modelList = $Models -join ","
            uv run python scripts/probe_cloudgpt_models.py `
                --models $modelList `
                --out "analysis/cloudgpt_multi_model_probe_$runStamp.jsonl"
        }
    }
    else {
        Write-Host "Skipping model probe; using caller-provided model list."
    }

    $cycle = 1
    while (((Get-Date) - $startedAt).TotalHours -lt $MinHours) {
        foreach ($model in $Models) {
            $elapsedHours = ((Get-Date) - $startedAt).TotalHours
            if ($elapsedHours -ge $MinHours) {
                break
            }

            $safeModel = ConvertTo-SafeName -Value $model
            $cache = "logs/cloudgpt_live_cache_$safeModel.jsonl"
            $completedProfiles = Get-CompletedProfilesFromCache -Path $cache
            $remainingProfiles = @($profileOrder | Where-Object { $completedProfiles -notcontains $_ })
            if ($remainingProfiles.Count -eq 0) {
                Write-Host "No remaining profiles for model=$model. Skipping."
                continue
            }

            $take = [Math]::Min($ProfilesPerModelBatch, $remainingProfiles.Count)
            $profileBatch = @($remainingProfiles | Select-Object -First $take)
            $profileList = ($profileBatch -join ",")
            $cellBudget = $profileBatch.Count * 12
            $baseCalibration = if ($currentCalibrationByModel.ContainsKey($model)) { $currentCalibrationByModel[$model] } else { $StartCalibration }
            $batchTag = "${safeModel}_c$cycle"
            $outCalibration = "${OutPrefix}_${batchTag}.npy"
            $report = "analysis/${OutPrefix}_${batchTag}_report.json"
            $audit = "logs/E5_audit_${OutPrefix}_${batchTag}.txt"
            $summaryMd = "analysis/${OutPrefix}_${batchTag}_summary.md"
            $summaryJson = "analysis/${OutPrefix}_${batchTag}_summary.json"
            $modelWorkers = if ($workerMap.ContainsKey($model)) { $workerMap[$model] } else { $Workers }

            Write-Host "Model=$model cycle=$cycle elapsed_hours=$([Math]::Round($elapsedHours, 2)) profiles=$profileList cell_budget=$cellBudget workers=$modelWorkers base=$baseCalibration"

            Invoke-Step "live calibration $batchTag" {
                uv run python calibration_live.py `
                    --backend cloudgpt `
                    --judge-model $model `
                    --base-calibration $baseCalibration `
                    --out $outCalibration `
                    --report $report `
                    --cache $cache `
                    --samples 1 `
                    --profile-indices $profileList `
                    --cell-budget $cellBudget `
                    --save-every 12 `
                    --workers $modelWorkers
            }

            Invoke-Step "audit $batchTag" {
                uv run python audit_personas.py `
                    --calibration $outCalibration `
                    --out $audit
            }

            $resultFiles = @()
            foreach ($beta in $Betas) {
                $betaName = Format-BetaName -Beta $beta
                $resultPath = "results/cloudgpt/E2_${batchTag}_beta${betaName}.npz"
                $resultFiles += $resultPath
                Invoke-Step "E2 $batchTag beta=$beta" {
                    uv run python run_experiment.py `
                        --K $K `
                        --n 3 `
                        --seeds $Seeds `
                        --beta $beta `
                        --algos $Algorithms `
                        --calibration $outCalibration `
                        --out $resultPath `
                        --judge-model $model
                }
            }

            Invoke-Step "summary $batchTag" {
                uv run python scripts/summarize_live_e2.py `
                    --calibration $outCalibration `
                    --report $report `
                    --audit $audit `
                    --results $resultFiles `
                    --out-md $summaryMd `
                    --out-json $summaryJson
            }

            $currentCalibrationByModel[$model] = $outCalibration
        }
        $cycle += 1
    }

    Write-Host ""
    Write-Host "Done. Transcript: $transcriptPath"
}
finally {
    Stop-Transcript | Out-Null
}