# PACT / HP-SPGG Figures and Data Bundle

Generated from repository commit `af28efd4d274fe7d7c48569738f6f692829ae26a` on `2026-07-15`.

## Contents

| category | files | size (MB) |
|---|---:|---:|
| data | 245 | 7.88 |
| other_canonical_figure | 262 | 21.15 |
| paper_referenced_figure | 20 | 1.07 |
| paper_source | 8 | 2.33 |
| plotting_code | 56 | 0.66 |
| provenance | 13 | 0.39 |

## Layout

- `figures/paper_referenced/`: every figure currently referenced by `arr_paper/main.tex` or `appendix.tex`.
- `figures/all_other_canonical/`: every remaining PDF, PNG, and GIF from `arr_paper/figs`; together the two figure directories reproduce the complete canonical figure archive.
- `data/analysis/` and `data/tables/`: current result data and reports. Cache files and temporary replay files are excluded.
- `paper/`: paper source, bibliography/style files, and compiled PDF.
- `plotting_code/`: every Python file detected as a figure renderer, plus plotting, aggregation, analysis, animation, and summarization helper scripts.
- `provenance/`: project metadata and figure/data provenance documentation.

## Validation

`MANIFEST.csv` maps each packaged file back to its repository source. `SHA256SUMS.txt` contains checksums for integrity verification.

Third-party checkouts, virtual environments, caches, and raw model credentials are intentionally excluded.
