# PACT AAAI-27 Reviewer Experiment Artifact

Generated from code commit `af28efd4d274fe7d7c48569738f6f692829ae26a` with a clean Git tree; ignored experiment data are identified by `MANIFEST.csv` hashes.

- `analysis/aaai27_review/`: consolidated report, requested CSVs, and SOTOPIA raw checkpoints.
- `analysis/courier_dispatch_maassim/`: fixed E-R0 snapshots/personas and retained aggregate comparator.
- `analysis/sotopia_tuned_all70_full_report.md` and `config/aaai27_sotopia_historical_comparators.csv`: E-R3 comparator provenance.
- `external/sotopia_data_probe/`: public metadata and reconstructed 70-case cache; the 180 MB public JSONL is referenced by SHA-256 in the report.
- `scripts/`, `llm_*/`, `docs/`, `pyproject.toml`, and `requirements.txt`: reproduction code and documentation at their repository-relative paths.
- `MANIFEST.csv` and `SHA256SUMS.txt`: source mapping and integrity.

Run the summarizer and validator from this artifact root. E-R3 requires SOTOPIA 0.1.5 on Python 3.12 (the completed run pinned `litellm==1.80.11`); E-R4 requires the public google-deepmind/concordia checkout compatible with gdm-concordia 2.4.0 under `external/concordia`. The public source-data URLs and input hashes are in the consolidated report.

The report distinguishes completed experiments from infrastructure-blocked requests and must be read before interpreting the CSVs. Mutable/provider decision caches are intentionally excluded; E-R0 records the cache-hit/live-fill counts and is a provenance-labelled reconstruction, not recovery of deleted original seed rows.
