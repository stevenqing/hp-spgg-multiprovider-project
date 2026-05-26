"""Summarize Joint-PSRL-Uniform/Aware experiment outputs."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np


BASE = Path("analysis/joint_psrl_aware")


def parse_cell(path: Path) -> tuple[int, int, str]:
    stem = path.stem
    prefix = "E1_jointaware_"
    body = stem[len(prefix):]
    body = body[: -len("_shared_type")]
    parts = body.split("_")
    n = int(parts[0][1:])
    k_rounds = int(parts[1][1:])
    tier = "_".join(parts[2:])
    return n, k_rounds, tier


def main() -> None:
    rows: list[dict[str, object]] = []
    for path in sorted(BASE.glob("E1_jointaware_n*_K*_*_shared_type.npz")):
        n, k_rounds, tier = parse_cell(path)
        data = np.load(path, allow_pickle=True)
        algorithms = [str(item) for item in data["algorithms"]]
        cumulative_regret = np.asarray(data["cumulative_regret"], dtype=float)
        storage = np.asarray(data["storage"], dtype=int)
        for index, algorithm in enumerate(algorithms):
            finals = cumulative_regret[index, :, -1]
            rows.append(
                {
                    "tier": tier,
                    "n": n,
                    "K": k_rounds,
                    "algorithm": algorithm,
                    "mean_cumulative_regret": float(np.mean(finals)),
                    "sem": float(np.std(finals, ddof=1) / np.sqrt(len(finals))) if len(finals) > 1 else 0.0,
                    "storage": int(storage[index]),
                    "seeds": int(cumulative_regret.shape[1]),
                    "source": str(path),
                }
            )
    if not rows:
        raise SystemExit("no E1_jointaware npz files found")
    BASE.mkdir(parents=True, exist_ok=True)
    with (BASE / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    (BASE / "summary.json").write_text(json.dumps({"rows": rows}, indent=2), encoding="utf-8")
    print(f"wrote {BASE / 'summary.csv'} ({len(rows)} rows)")


if __name__ == "__main__":
    main()