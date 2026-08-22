"""E-1.1 n-scaling experiment runner.

Uses existing archived calibrations for n in {2,3,4,5} and synthesises an
n=6 analytic calibration so that PACT / PACT+ / Joint-PSRL can be evaluated
across the same axis without launching new LLM calls.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from llm_hpgg.environment import build_reward_tensor, save_calibration

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_CAL = ROOT / "_archive" / "calibration" / "e1_e4_llm"
OUT_DIR = ROOT / "analysis" / "e1_1_n_scaling"
OUT_DIR.mkdir(parents=True, exist_ok=True)

NS = [3, 4, 5, 6]
SEEDS = 5
K = 20
ALGOS = [
    "hpsmg_plus",
    "hpsmg",
    "joint_psrl",
    "map_greedy",
    "psrl_notype",
    "iql_independent_actions",
    "iql",
    "random",
    "oracle",
]


def ensure_calibration(n: int) -> Path:
    if n <= 5:
        src = ARCHIVE_CAL / f"E3_n{n}_live.npz"
        if src.exists():
            return src
    out = OUT_DIR / f"calibration_synth_n{n}.npy"
    if out.exists():
        return out
    bundle = build_reward_tensor(n=n, backend="mixed", samples=3, seed=0, trap=False)
    save_calibration(bundle, out)
    return out


def run_cell(n: int, calibration: Path) -> Path:
    out_npz = OUT_DIR / f"E1_1_n{n}.npz"
    if out_npz.exists():
        return out_npz
    cmd = [
        sys.executable,
        "-m",
        "llm_hpgg.run_experiment",
        "--K",
        str(K),
        "--n",
        str(n),
        "--seeds",
        str(SEEDS),
        "--beta",
        "0.25",
        "--algos",
        *ALGOS,
        "--calibration",
        str(calibration),
        "--out",
        str(out_npz),
        "--record-posterior",
        "--matched-seeds",
    ]
    print("RUN", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=str(ROOT))
    return out_npz


def summarise() -> Path:
    rows: list[dict] = []
    for n in NS:
        npz = OUT_DIR / f"E1_1_n{n}.npz"
        if not npz.exists():
            continue
        data = np.load(npz, allow_pickle=True)
        algos = [str(x) for x in data["algorithms"]]
        cum = np.asarray(data["cumulative_regret"], dtype=float)
        for idx, algo in enumerate(algos):
            finals = cum[idx, :, -1]
            rows.append(
                {
                    "n": n,
                    "algorithm": algo,
                    "final_cumulative_regret_mean": float(np.mean(finals)),
                    "final_cumulative_regret_sem": float(np.std(finals, ddof=1) / np.sqrt(len(finals))) if len(finals) > 1 else 0.0,
                    "seeds": int(len(finals)),
                }
            )
    out = OUT_DIR / "summary.json"
    out.write_text(json.dumps({"rows": rows}, indent=2), encoding="utf-8")
    return out


def main() -> None:
    for n in NS:
        cal = ensure_calibration(n)
        run_cell(n, cal)
    summary = summarise()
    print(f"OK summary: {summary}")


if __name__ == "__main__":
    main()
