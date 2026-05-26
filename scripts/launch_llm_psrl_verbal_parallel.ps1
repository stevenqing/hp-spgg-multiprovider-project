$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root
New-Item -ItemType Directory -Force logs | Out-Null
$modelMap = @{
  deepseek       = "DeepSeek-V3.2"
  gpt5_nano      = "gpt-5.4-nano-20260317"
  kimi_k2        = "Kimi-K2.6"
  llama_maverick = "Llama-4-Maverick-17B-128E-Instruct-FP8"
}
$records = @()
foreach ($tier in $modelMap.Keys) {
  $model = $modelMap[$tier]
  foreach ($kind in "hp", "haggling", "sotopia") {
    if ($kind -eq "hp") { $script = "scripts\run_hp_verbal_tier.ps1" }
    elseif ($kind -eq "haggling") { $script = "scripts\run_concordia_haggling_verbal_tier.ps1" }
    else { $script = "scripts\run_sotopia_verbal_tier.ps1" }
    $stdout = "logs\parallel_${kind}_${tier}_stdout.log"
    $stderr = "logs\parallel_${kind}_${tier}_stderr.log"
    Remove-Item -Force -ErrorAction SilentlyContinue $stdout,$stderr
    $p = Start-Process powershell.exe -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Resolve-Path $script).Path,'-Tier',$tier,'-Model',$model) -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru -WindowStyle Hidden
    $records += [PSCustomObject]@{Kind=$kind; Tier=$tier; Model=$model; Pid=$p.Id; Stdout=$stdout; Stderr=$stderr}
  }
}
$records | ConvertTo-Json -Depth 3 | Set-Content logs\llm_psrl_verbal_parallel_jobs.json
$records | Format-Table -AutoSize