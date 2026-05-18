$tex = Get-Content paper\main.tex -Raw
$tex = $tex -replace [regex]::Escape('\usepackage{iclr2023_conference,times}'), '\usepackage{acl}'
$tex = $tex -replace [regex]::Escape('%\bibliography{ref}'), '\bibliography{ref}'
$tex = $tex -replace [regex]::Escape('%\bibliographystyle{iclr2023_conference}'), '% acl.sty sets \bibliographystyle{acl_natbib} automatically'
$tex | Set-Content -Encoding UTF8 paper\main.tex
Select-String -Path paper\main.tex -Pattern 'usepackage\{acl|^\\bibliography|acl_natbib' | ForEach-Object { "$($_.LineNumber): $($_.Line)" }
