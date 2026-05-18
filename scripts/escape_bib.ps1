$bib = Get-Content paper\ref.bib -Raw
# Escape underscores everywhere except inside @misc{KEY,
$lines = $bib -split "`r`n"
for ($i=0; $i -lt $lines.Count; $i++) {
  if ($lines[$i] -match '^(@misc\{[^,]+,)(.*)$') {
    $head = $Matches[1]
    $rest = $Matches[2] -replace '_','\_'
    $lines[$i] = $head + $rest
  } else {
    $lines[$i] = $lines[$i] -replace '_','\_'
  }
}
($lines -join "`r`n") | Set-Content -Encoding ASCII paper\ref.bib
Select-String -Path paper\ref.bib -Pattern 'concordia|atom|sotopia' | Select-Object -First 6 | ForEach-Object { $_.Line }
