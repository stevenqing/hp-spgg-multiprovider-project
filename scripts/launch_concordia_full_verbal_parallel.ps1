$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root
New-Item -ItemType Directory -Force logs | Out-Null
$tiers = @("deepseek", "gpt5_nano", "kimi_k2", "llama_maverick")
$records = @()
foreach ($tier in $tiers) {
  $stdout = "logs\concordia_full_${tier}_stdout.log"
  $stderr = "logs\concordia_full_${tier}_stderr.log"
  Remove-Item -Force -ErrorAction SilentlyContinue $stdout,$stderr
  $p = Start-Process powershell.exe -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Resolve-Path 'scripts\run_concordia_full_verbal.ps1').Path,'-OnlyTier',$tier) -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru -WindowStyle Hidden
  $records += [PSCustomObject]@{Tier=$tier; Pid=$p.Id; Stdout=$stdout; Stderr=$stderr}
}
$records | ConvertTo-Json | Set-Content logs\concordia_full_verbal_parallel_jobs.json
$records | Format-Table -AutoSize