$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

Write-Host "=== background process ==="
if (Test-Path logs\remaining_experiments.pid) {
  $pidValue = [int](Get-Content logs\remaining_experiments.pid -Raw)
  Get-Process -Id $pidValue -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, StartTime, HasExited | Format-Table -AutoSize
} else {
  Write-Host "no PID file"
}

Write-Host "=== latest transcript tail ==="
$latest = Get-ChildItem logs\remaining_experiments_*.transcript.log -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($latest) { Get-Content $latest.FullName -Tail 25 } else { Write-Host "no transcript yet" }

Write-Host "=== HP-SPGG file counts ==="
[PSCustomObject]@{
  JointAwareNpz = (Get-ChildItem analysis\joint_psrl_aware\E1_jointaware_*.npz -ErrorAction SilentlyContinue).Count
  TrueSharedNpz = (Get-ChildItem analysis\true_shared_type\E1_truesharedtype_*.npz -ErrorAction SilentlyContinue).Count
} | Format-Table -AutoSize

Write-Host "=== SOTOPIA donate_funds cells ==="
$rows = @()
foreach ($f in Get-ChildItem analysis\sotopia_intent_ablation\sotopia_intent_*_donate_funds_s5.json -ErrorAction SilentlyContinue) {
  try {
    $j = Get-Content $f.FullName -Raw | ConvertFrom-Json
    $rows += [PSCustomObject]@{File=$f.Name; Cases=$j.case_count; Complete=$j.complete; Mean=[math]::Round([double]$j.summary.mean_overall, 4); Updated=$f.LastWriteTime.ToString("HH:mm:ss")}
  } catch {
    $rows += [PSCustomObject]@{File=$f.Name; Cases="ERR"; Complete=$false; Mean=$null; Updated=$f.LastWriteTime.ToString("HH:mm:ss")}
  }
}
if ($rows.Count) { $rows | Sort-Object File | Format-Table -AutoSize } else { Write-Host "no donate_funds cells yet" }

Write-Host "=== partial judge entries ==="
if (Test-Path analysis\sotopia_intent_ablation\partial_judge_cache.json) {
  $j = Get-Content analysis\sotopia_intent_ablation\partial_judge_cache.json -Raw | ConvertFrom-Json
  ($j.entries.PSObject.Properties | Measure-Object).Count
} else {
  Write-Host "no partial cache"
}