param(
    [double]$MinHours = 10.0,
    [int]$Batches = 999,
    [int]$ProfilesPerBatch = 4,
    [int]$K = 20,
    [int]$Seeds = 5,
    [double[]]$Betas = @(0.0, 0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 1.5),
    [string]$StartCalibration = "calibration_cloudgpt_live_continued.npy",
    [string]$Cache = "logs/cloudgpt_live_cache.jsonl",
    [string]$OutPrefix = "calibration_cloudgpt_live_overnight",
    [string]$KnownProfileOrder = "2,8,14,20,26,32,39,46,53,61,69,76,84,92,100,108,116,123,1,3,4,6,7,9,10,12,13,15,17,18,19,21,23,24,25,28,29,30,31,34,35,36,37,40,41,42,43,44,47,48,50,51,52,54,55,57,58,59,62,63,64,65,66,68,70,72,73,74,75,77,79,80,81,83,85,86,87,88,89,91,94,95,96,97,98,99,102,103,105,106,107,109,110,111,113,114,117,118,119,120,121,122,0,11,22,33,45,56,67,78,90,101,112,124",
    [bool]$RunModelSmoke = $true,
    [string[]]$ModelSpecs = @(
        "cloudgpt|gpt-5.4-mini-20260317|gpt-5.4-mini-20260317",
        "cloudgpt|gpt-5.4-nano-20260317|gpt-5.4-nano-20260317",
        "cloudgpt|gpt-5.5-20260424|gpt-5.5-20260424",
        "cloudgpt|gpt-5.3-chat-20260303|gpt-5.3-chat-20260303",
        "cloudgpt|gpt-5.2-chat-20260210|gpt-5.2-chat-20260210",
        "cloudgpt|gpt-4.1-mini-20250414|gpt-4.1-mini-20250414",
        "cloudgpt|DeepSeek-V3.2|DeepSeek-V3.2",
        "cloudgpt|Kimi-K2.6|Kimi-K2.6",
        "cloudgpt|Llama-4-Maverick-17B-128E-Instruct-FP8|Llama-4-Maverick-17B-128E-Instruct-FP8",
        "cloudgpt|grok-4|grok-4",
        "deepseek|deepseek-ai/DeepSeek-V3.2|deepseek-ai/DeepSeek-V3.2",
        "anthropic|claude-haiku-4-5-20251001|claude-sonnet-4-6-20251101",
        "google|gemini-2.5-flash|gemini-2.5-pro",
        "qwen3|Qwen/Qwen3-32B|Qwen/Qwen3-235B-A22B"
    )
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

function Test-BackendCredential {
    param([string]$Backend)
    switch ($Backend) {
        "cloudgpt" { return $true }
        "anthropic" { return [bool]$env:ANTHROPIC_API_KEY }
        "google" { return [bool]$env:GOOGLE_API_KEY }
        "qwen3" { return [bool]$env:DEEPINFRA_API_KEY }
        "deepseek" { return [bool]$env:DEEPINFRA_API_KEY }
        default { return $false }
    }
}

function Invoke-ModelSmokeMatrix {
    param(
        [string[]]$Specs,
        [string]$RunStamp
    )
    $matrixPath = "analysis/model_smoke_matrix_$RunStamp.jsonl"
    foreach ($spec in $Specs) {
        $parts = $spec.Split("|", 3)
        if ($parts.Count -lt 3) {
            continue
        }
        $backend = $parts[0]
        $playerModel = $parts[1]
        $judgeModel = $parts[2]
        $out = "logs/smoke_${backend}_$RunStamp.json"
        $record = [ordered]@{
            backend = $backend
            player_model = $playerModel
            judge_model = $judgeModel
            out = $out
            status = "pending"
            error = $null
        }
        if (-not (Test-BackendCredential -Backend $backend)) {
            $record.status = "skipped_missing_credentials"
            ($record | ConvertTo-Json -Compress) | Add-Content -Path $matrixPath
            Write-Host "model smoke skipped: $backend missing credentials"
            continue
        }
        try {
            $env:LLM_HPGG_BACKEND = $backend
            $env:LLM_HPGG_PLAYER_MODEL = $playerModel
            $env:LLM_HPGG_JUDGE_MODEL = $judgeModel
            uv run python smoke_test.py --backend $backend --out $out
            if ($LASTEXITCODE -ne 0) {
                throw "smoke_test exit=$LASTEXITCODE"
            }
            $record.status = "ok"
            Write-Host "model smoke ok: $backend"
        }
        catch {
            $record.status = "failed"
            $record.error = $_.Exception.Message
            Write-Host "model smoke failed: $backend $($_.Exception.Message)"
        }
        finally {
            Remove-Item Env:\LLM_HPGG_PLAYER_MODEL -ErrorAction SilentlyContinue
            Remove-Item Env:\LLM_HPGG_JUDGE_MODEL -ErrorAction SilentlyContinue
        }
        ($record | ConvertTo-Json -Compress) | Add-Content -Path $matrixPath
    }
    Write-Host "model smoke matrix: $matrixPath"
}

New-Item -ItemType Directory -Force -Path logs, analysis, results/cloudgpt | Out-Null
$runStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$transcriptPath = "logs/overnight_live_improve_$runStamp.log"
Start-Transcript -Path $transcriptPath | Out-Null

try {
    $env:LLM_HPGG_BACKEND = "cloudgpt"
    $env:CLOUDGPT_USE_AZURE_CLI = "1"
    $profileOrder = $KnownProfileOrder.Split(",") | Where-Object { $_.Trim().Length -gt 0 } | ForEach-Object { [int]$_.Trim() }
    $currentCalibration = $StartCalibration
    $startedAt = Get-Date

    if (-not (Test-Path $currentCalibration)) {
        throw "Start calibration not found: $currentCalibration"
    }

    Write-Host "overnight run started=$startedAt min_hours=$MinHours max_batches=$Batches profiles_per_batch=$ProfilesPerBatch"
    Write-Host "start_calibration=$StartCalibration cache=$Cache"

    if ($RunModelSmoke) {
        Invoke-Step "model smoke matrix" {
            Invoke-ModelSmokeMatrix -Specs $ModelSpecs -RunStamp $runStamp
            $global:LASTEXITCODE = 0
        }
        $env:LLM_HPGG_BACKEND = "cloudgpt"
        $env:CLOUDGPT_USE_AZURE_CLI = "1"
    }

    for ($batch = 1; $batch -le $Batches; $batch++) {
        $elapsedHours = ((Get-Date) - $startedAt).TotalHours
        if ($elapsedHours -ge $MinHours) {
            Write-Host "Reached min_hours=$MinHours after $([Math]::Round($elapsedHours, 2)) hours. Stopping."
            break
        }

        $completedProfiles = Get-CompletedProfilesFromCache -Path $Cache
        $remainingProfiles = @($profileOrder | Where-Object { $completedProfiles -notcontains $_ })
        if ($remainingProfiles.Count -eq 0) {
            Write-Host "No remaining profiles in KnownProfileOrder. Stopping."
            break
        }

        $take = [Math]::Min($ProfilesPerBatch, $remainingProfiles.Count)
        $profileBatch = @($remainingProfiles | Select-Object -First $take)
        $profileList = ($profileBatch -join ",")
        $cellBudget = $profileBatch.Count * 12
        $batchTag = "b$batch"
        $outCalibration = "${OutPrefix}_${batchTag}.npy"
        $report = "analysis/${OutPrefix}_${batchTag}_report.json"
        $audit = "logs/E5_audit_cloudgpt_live_${batchTag}.txt"
        $summaryMd = "analysis/${OutPrefix}_${batchTag}_summary.md"
        $summaryJson = "analysis/${OutPrefix}_${batchTag}_summary.json"

        Write-Host "Batch $batch elapsed_hours=$([Math]::Round($elapsedHours, 2)) profiles=$profileList cell_budget=$cellBudget base=$currentCalibration"

        Invoke-Step "live calibration $batchTag" {
            uv run python calibration_live.py `
                --backend cloudgpt `
                --base-calibration $currentCalibration `
                --out $outCalibration `
                --report $report `
                --cache $Cache `
                --samples 1 `
                --profile-indices $profileList `
                --cell-budget $cellBudget `
                --save-every 12
        }

        Invoke-Step "audit $batchTag" {
            uv run python audit_personas.py `
                --calibration $outCalibration `
                --out $audit
        }

        $resultFiles = @()
        foreach ($beta in $Betas) {
            $betaName = Format-BetaName -Beta $beta
            $resultPath = "results/cloudgpt/E2_live_${batchTag}_beta${betaName}.npz"
            $resultFiles += $resultPath
            Invoke-Step "E2 $batchTag beta=$beta" {
                uv run python run_experiment.py `
                    --K $K `
                    --n 3 `
                    --seeds $Seeds `
                    --beta $beta `
                    --algos hpsmg_plus hpsmg oracle random `
                    --calibration $outCalibration `
                    --out $resultPath
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

        $currentCalibration = $outCalibration
    }

    Write-Host ""
    Write-Host "Done. Transcript: $transcriptPath"
}
finally {
    Stop-Transcript | Out-Null
}