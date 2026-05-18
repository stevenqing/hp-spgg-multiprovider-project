$ErrorActionPreference = 'Stop'
$dst = 'arr_paper'
New-Item -ItemType Directory $dst -Force | Out-Null
New-Item -ItemType Directory (Join-Path $dst 'figs') -Force | Out-Null
Copy-Item paper\HT_MG\iclr\main.tex $dst\
Copy-Item paper\HT_MG\iclr\ref.bib $dst\
Copy-Item paper\HT_MG\iclr\appendix.tex $dst\
Copy-Item paper\HT_MG\iclr\math_commands.tex $dst\
Copy-Item paper\HT_MG\iclr\legacy.tex $dst\
Copy-Item paper\HT_MG\figs\* (Join-Path $dst 'figs') -Recurse
Copy-Item paper\acl.sty $dst\
Copy-Item paper\acl_natbib.bst $dst\
Get-ChildItem $dst | Select-Object Name,Length | Format-Table -AutoSize
Write-Host '---figs---'
Get-ChildItem (Join-Path $dst 'figs') | Select-Object Name,Length | Format-Table -AutoSize
