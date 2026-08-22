"""Redraw the HARP reward-locality figure from retained experiment CSVs."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis" / "e_d_reward_locality_violation_combined"
if not DATA.is_dir():
    DATA = ROOT / "analysis" / "e_d_reward_locality_violation"

from run_e_d_reward_locality_violation import plot_results  # noqa: E402


def read_rows(path: Path) -> list[dict[str, object]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def main() -> None:
    raw_path = DATA / "e_d_reward_locality_violation_per_seed.csv"
    summary_path = DATA / "e_d_reward_locality_violation_summary.csv"
    if not raw_path.is_file() or not summary_path.is_file():
        raise FileNotFoundError(f"retained E-D CSVs are missing under {DATA}")
    plot_results(read_rows(raw_path), read_rows(summary_path), DATA)
    print("redrew HARP reward-locality figure")


if __name__ == "__main__":
    main()
