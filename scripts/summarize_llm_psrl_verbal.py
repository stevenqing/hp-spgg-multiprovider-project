"""Aggregate llm_psrl_verbal sweep results into summary CSV/JSON."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np


def main() -> None:
    base = Path("analysis/llm_psrl_verbal")
    files = sorted(base.glob("E_llmpsrl_n*_K*_*.npz"))
    if not files:
        raise SystemExit("No result files found matching analysis/llm_psrl_verbal/E_llmpsrl_n*_K*_*.npz")

    rows: list[dict[str, object]] = []
    for file_path in files:
        stem = file_path.stem
        parts = stem.split("_")
        n = int(parts[2][1:])
        k_rounds = int(parts[3][1:])
        tier = "_".join(parts[4:])
        data = np.load(file_path, allow_pickle=True)
        algorithms = [str(item) for item in data["algorithms"]]
        cumulative_regret = np.asarray(data["cumulative_regret"], dtype=float)
        seeds = cumulative_regret.shape[1]
        sample_ok = np.asarray(data.get("verbal_sample_ok", np.zeros((len(algorithms), seeds))), dtype=float)
        sample_fallback = np.asarray(data.get("verbal_sample_fallback", np.zeros((len(algorithms), seeds))), dtype=float)
        update_ok = np.asarray(data.get("verbal_update_ok", np.zeros((len(algorithms), seeds))), dtype=float)
        update_failed = np.asarray(data.get("verbal_update_failed", np.zeros((len(algorithms), seeds))), dtype=float)
        for index, algorithm in enumerate(algorithms):
            final = cumulative_regret[index, :, -1]
            sample_total = float(sample_ok[index].sum() + sample_fallback[index].sum())
            update_total = float(update_ok[index].sum() + update_failed[index].sum())
            rows.append(
                {
                    "tier": tier,
                    "n": n,
                    "K": k_rounds,
                    "algorithm": algorithm,
                    "mean_cumulative_regret": float(final.mean()),
                    "sem": float(final.std(ddof=1) / np.sqrt(seeds)) if seeds > 1 else 0.0,
                    "seeds": int(seeds),
                    "sample_success_rate": float(sample_ok[index].sum() / sample_total) if sample_total else "NA",
                    "update_success_rate": float(update_ok[index].sum() / update_total) if update_total else "NA",
                    "source": str(file_path),
                }
            )

    out_csv = base / "summary.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    (base / "summary.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")

    print(f"{'tier':18s} {'n':>2} {'K':>3} {'PACT':>8} {'PACT+':>8} {'verbal':>8} {'verbal/PACT':>12} {'sample':>8} {'update':>8}")
    print("-" * 92)
    by_cell: dict[tuple[str, int, int], dict[str, dict[str, object]]] = {}
    for row in rows:
        by_cell.setdefault((str(row["tier"]), int(row["n"]), int(row["K"])), {})[str(row["algorithm"])] = row
    for (tier, n, k_rounds), algs in sorted(by_cell.items()):
        pact = algs.get("hpsmg", {}).get("mean_cumulative_regret")
        pact_plus = algs.get("hpsmg_plus", {}).get("mean_cumulative_regret")
        verbal = algs.get("llm_psrl_verbal", {}).get("mean_cumulative_regret")
        if pact is None or verbal is None:
            continue
        pact_float = float(pact)
        verbal_float = float(verbal)
        ratio = "inf" if pact_float <= 1e-12 else f"{verbal_float / pact_float:.2f}x"
        sample_rate = algs.get("llm_psrl_verbal", {}).get("sample_success_rate", "NA")
        update_rate = algs.get("llm_psrl_verbal", {}).get("update_success_rate", "NA")
        sample_text = "NA" if sample_rate == "NA" else f"{float(sample_rate):.2f}"
        update_text = "NA" if update_rate == "NA" else f"{float(update_rate):.2f}"
        print(
            f"{tier:18s} {n:>2} {k_rounds:>3} {pact_float:>8.3f} "
            f"{float(pact_plus) if pact_plus is not None else float('nan'):>8.3f} {verbal_float:>8.3f} "
            f"{ratio:>12s} {sample_text:>8s} {update_text:>8s}"
        )
    print(f"wrote {out_csv}")


if __name__ == "__main__":
    main()