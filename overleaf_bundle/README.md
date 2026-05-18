# Overleaf-ready bundle

## How to compile on Overleaf

1. Create a new blank project on Overleaf.
2. Upload the whole contents of this folder (drag-drop the files, including the `figs/` folder).
3. In Overleaf, set:
   - **Main document:** `main.tex`
   - **Compiler:** `pdfLaTeX`
4. Click **Recompile**. Overleaf will automatically run pdflatex → bibtex → pdflatex → pdflatex.

## File map

| File | Purpose |
|---|---|
| `main.tex` | Main paper (front matter, §1–§5, bibliography hook, appendix include) |
| `appendix.tex` | All technical appendices (full proofs, supplementary figures) — included via `\input{appendix}` at the end of `main.tex` |
| `ref.bib` | BibTeX entries |
| `acl.sty` | ACL/ARR 2024 style file |
| `acl_natbib.bst` | ACL natbib bibliography style |
| `figs/` | All 17 figures referenced by main + appendix |

## Local compilation (optional)

```
pdflatex main.tex
bibtex   main
pdflatex main.tex
pdflatex main.tex
```

Output: `main.pdf` (≈ 37 pages).

## Notes

- `acl.sty` already calls `\bibliographystyle{acl_natbib}` automatically, so do not add a separate `\bibliographystyle` line.
- The appendix is included at the end of `main.tex` via `\input{appendix}`; remove that line to produce a body-only PDF.
- No other `.sty` or `.cls` files are required — every package used (`amsmath`, `amssymb`, `amsthm`, `algorithm`, `algorithmic`, `subfig`, `graphicx`, `booktabs`, `multirow`, `hyperref`, `xcolor`, `tikz`, `bbm`, `mathtools`, `listings`, `lmodern`) ships with the standard TeX Live / MiKTeX distribution that Overleaf uses.
