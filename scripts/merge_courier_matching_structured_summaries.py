"""Merge CourierDispatch structured-live summary JSON files.

This is used to append supplement baseline runs, such as LLM-PSRL-verbal and
Random, to the existing w_LLM=0 headline run without rerunning the full method
set.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_courier_dispatch.live_structured_matching_dispatch import (  # noqa: E402
    ANALYSIS_DIR,
    summarize,
    write_csv,
    write_summary_csv,
)


def resolve(path: str) -> Path:
    raw = Path(path)
    if raw.is_absolute():
        return raw
    if raw.exists():
        return raw
    return ANALYSIS_DIR / raw


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", nargs="+", required=True, help="Summary JSON files to merge")
    parser.add_argument("--out-prefix", required=True, help="Output prefix under analysis/courier_dispatch_matching")
    args = parser.parse_args()

    payloads = [json.loads(resolve(path).read_text(encoding="utf-8")) for path in args.inputs]
    rows = []
    for payload in payloads:
        rows.extend(payload.get("rows", []))
    if not rows:
        raise ValueError("no rows found in input summaries")

    setting = dict(payloads[0].get("setting", {}))
    methods = []
    models = []
    for payload in payloads:
        for method in payload.get("setting", {}).get("live_methods", []):
            if method not in methods:
                methods.append(method)
        for model in payload.get("setting", {}).get("models", []):
            if model not in models:
                models.append(model)
    setting["live_methods"] = methods
    setting["models"] = models
    setting["merged_from"] = [str(resolve(path).relative_to(ROOT)) for path in args.inputs]

    summary = summarize(rows)
    out_json = ANALYSIS_DIR / f"{args.out_prefix}_summary.json"
    out_rows = ANALYSIS_DIR / f"{args.out_prefix}_rows.csv"
    out_summary_csv = ANALYSIS_DIR / f"{args.out_prefix}_summary.csv"
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps({"setting": setting, "summary": summary, "rows": rows}, indent=2), encoding="utf-8")
    write_csv(out_rows, rows)
    write_summary_csv(out_summary_csv, summary)
    print(json.dumps({"summary_path": str(out_json.relative_to(ROOT)), "rows_csv": str(out_rows.relative_to(ROOT)), "summary_csv": str(out_summary_csv.relative_to(ROOT)), "rows": len(rows)}, indent=2))


if __name__ == "__main__":
    main()