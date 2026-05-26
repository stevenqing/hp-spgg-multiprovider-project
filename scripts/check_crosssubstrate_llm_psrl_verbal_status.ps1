$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root
Write-Host "=== process ==="
if (Test-Path logs\crosssubstrate_llm_psrl_verbal.pid) {
  $pidValue = [int](Get-Content logs\crosssubstrate_llm_psrl_verbal.pid -Raw)
  Get-Process -Id $pidValue -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, StartTime, HasExited | Format-Table -AutoSize
} else { Write-Host "no PID file" }

Write-Host "=== latest transcript tail ==="
$latest = Get-ChildItem logs\crosssubstrate_llm_psrl_verbal_*.transcript.log -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($latest) { Get-Content $latest.FullName -Tail 35 } else { Write-Host "no transcript" }

Write-Host "=== Concordia Pub ==="
$rows = @()
foreach ($f in Get-ChildItem analysis\llm_psrl_verbal\concordia_pub_london_mini_*_llmpsrl_s5.json -ErrorAction SilentlyContinue) {
  try { $j=Get-Content $f.FullName -Raw | ConvertFrom-Json; $m=($j.summary | Where-Object method -eq 'llm_psrl_verbal').focal_score_mean; $rows += [PSCustomObject]@{File=$f.Name; Complete=($j.summary -ne $null); Mean=[math]::Round([double]$m,4); Updated=$f.LastWriteTime.ToString('HH:mm:ss')} } catch {}
}
if ($rows.Count) { $rows | Sort-Object File | Format-Table -AutoSize } else { Write-Host "none yet" }

Write-Host "=== Concordia Haggling ==="
$rows = @()
foreach ($f in Get-ChildItem analysis\llm_psrl_verbal\concordia_haggling_fruitville_*_llmpsrl_s30.json -ErrorAction SilentlyContinue) {
  try { $j=Get-Content $f.FullName -Raw | ConvertFrom-Json; $m=($j.summary | Where-Object method -eq 'llm_psrl_verbal').focal_score_mean; $rows += [PSCustomObject]@{File=$f.Name; Complete=($j.summary -ne $null); Mean=[math]::Round([double]$m,4); Updated=$f.LastWriteTime.ToString('HH:mm:ss')} } catch {}
}
if ($rows.Count) { $rows | Sort-Object File | Format-Table -AutoSize } else { Write-Host "none yet" }

Write-Host "=== SOTOPIA all70 ==="
$rows = @()
foreach ($f in Get-ChildItem analysis\llm_psrl_verbal\sotopia_hard_*_llm_psrl_verbal_all70.json -ErrorAction SilentlyContinue) {
  try { $j=Get-Content $f.FullName -Raw | ConvertFrom-Json; $rows += [PSCustomObject]@{File=$f.Name; Cases=$j.case_count; Complete=$j.complete; Mean=if($j.summary.mean_overall -ne $null){[math]::Round([double]$j.summary.mean_overall,4)}else{$null}; Updated=$f.LastWriteTime.ToString('HH:mm:ss')} } catch {}
}
if ($rows.Count) { $rows | Sort-Object File | Format-Table -AutoSize } else { Write-Host "none yet" }