$keys = Get-Content paper\_cite_keys.txt | Where-Object { $_ -match '\S' }
$bib = "% Auto-generated stub bibliography.`r`n"
foreach ($k in $keys) {
  $title = $k -replace '_','\_'
  $bib += "@misc{$k, author={Anon.}, title={Placeholder for $title}, year={2024}, note={Stub entry}}`r`n"
}
$bib | Set-Content -Encoding ASCII paper\ref.bib
Write-Host "wrote $($keys.Count) entries"
Select-String -Path paper\ref.bib -Pattern 'concordia|sotopia' | ForEach-Object { $_.Line }
