"""Print progress for live calibration cache/report files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect live calibration progress.")
    parser.add_argument("--cache", default="logs/cloudgpt_live_cache.jsonl")
    parser.add_argument("--report", default="analysis/cloudgpt_live_continued_report.json")
    args = parser.parse_args()

    cache_path = Path(args.cache)
    report_path = Path(args.report)
    entries = []
    if cache_path.exists():
        entries = [json.loads(line) for line in cache_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"cache={cache_path}")
    print(f"cached_cells={len(entries)}")
    if entries:
        latest = entries[-1]
        print(
            "latest="
            f"profile={latest.get('profile_index')} "
            f"player={latest.get('player_index')} "
            f"persona={latest.get('persona')} "
            f"score={latest.get('score')}"
        )
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        print(f"report={report_path}")
        for key in ("new_live_cells", "cached_cells_loaded", "skipped_cached_cells", "parse_failure_count", "tid_min_gap"):
            if key in report:
                print(f"{key}={report[key]}")
    else:
        print(f"report={report_path} not written yet")


if __name__ == "__main__":
    main()
