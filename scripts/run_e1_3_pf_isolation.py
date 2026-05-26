"""E-1.3 PF-isolation: sweep correlated Dirichlet joint prior over |Theta|^n profiles.

For each alpha in {0.1, 0.5, 1.0, inf} runs the 9 default algorithms on the
n=3 analytic calibration (|Theta|=4, |A|=5 -> |Theta|^n = 64 joint type
profiles, |A|^n = 125 action profiles).  alpha=inf is realized by re-using
the existing uniform-prior path (--prior-mode uniform).

Output: analysis/e1_3_pf_isolation/E1_3_alpha_{alpha}.npz (one per alpha)
and summary.json with final regret per (alpha, algorithm).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "analysis" / "e1_3_pf_isolation"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CALIBRATION_SRC = ROOT / "_archive" / "calibration" / "e1_e4_llm" / "E3_n3_live.npz"
CALIBRATION_DST = OUT_DIR / "calibration_n3_live.npz"

ALPHAS = [0.1, 0.5, 1.0, None]  # None means alpha=inf -> uniform prior
SEEDS = 10
K = 20
ALGOS = [
    "hpsmg_plus", "hpsmg", "joint_psrl", "map_greedy",
    "psrl_notype", "iql_independent_actions", "iql", "random", "oracle",
]


def ensure_calibration() -> Path:
    if not CALIBRATION_DST.exists():
        shutil.copy(CALIBRATION_SRC, CALIBRATION_DST)
    return CALIBRATION_DST


def run_cell(alpha: float | None) -> Path:
    tag = "inf" if alpha is None else f"{alpha:g}"
    out_npz = OUT_DIR / f"E1_3_alpha_{tag}.npz"
    if out_npz.exists():
        print(f"SKIP existing {out_npz.name}")
        return out_npz
    cmd = [
        sys.executable, "-m", "llm_hpgg.run_experiment",
        "--K", str(K),
        "--n", "3",
        "--seeds", str(SEEDS),
        "--beta", "0.25",
        "--algos", *ALGOS,
        "--calibration", str(CALIBRATION_DST),
        "--out", str(out_npz),
        "--matched-seeds",
    ]
    if alpha is not None:
        cmd += ["--prior-mode", "joint_dirichlet", "--joint-prior-alpha", str(alpha)]
    print("RUN", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=str(ROOT))
    return out_npz


def run_shared_type_cell() -> Path:
    out_npz = OUT_DIR / "E1_3_shared_type.npz"
    if out_npz.exists():
        print(f"SKIP existing {out_npz.name}")
        return out_npz
    cmd = [
        sys.executable, "-m", "llm_hpgg.run_experiment",
        "--K", str(K), "--n", "3", "--seeds", str(SEEDS), "--beta", "0.25",
        "--algos", *ALGOS,
        "--calibration", str(CALIBRATION_DST),
        "--out", str(out_npz),
        "--matched-seeds",
        "--prior-mode", "shared_type",
    ]
    print("RUN", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=str(ROOT))
    return out_npz


def summarise() -> dict:
    rows = []
    for alpha in ALPHAS:
        tag = "inf" if alpha is None else f"{alpha:g}"
        npz = OUT_DIR / f"E1_3_alpha_{tag}.npz"
        if not npz.exists():
            continue
        d = np.load(npz, allow_pickle=True)
        algos = [str(a) for a in d["algorithms"]]
        cum = np.asarray(d["cumulative_regret"], dtype=float)
        for i, a in enumerate(algos):
            finals = cum[i, :, -1]
            rows.append({
                "setting": f"dirichlet_a{tag}", "alpha": tag, "algorithm": a,
                "mean": float(np.mean(finals)),
                "sem": float(np.std(finals, ddof=1) / np.sqrt(len(finals))) if len(finals) > 1 else 0.0,
                "seeds": int(len(finals)),
            })
    shared = OUT_DIR / "E1_3_shared_type.npz"
    if shared.exists():
        d = np.load(shared, allow_pickle=True)
        algos = [str(a) for a in d["algorithms"]]
        cum = np.asarray(d["cumulative_regret"], dtype=float)
        for i, a in enumerate(algos):
            finals = cum[i, :, -1]
            rows.append({
                "setting": "shared_type", "alpha": "shared", "algorithm": a,
                "mean": float(np.mean(finals)),
                "sem": float(np.std(finals, ddof=1) / np.sqrt(len(finals))) if len(finals) > 1 else 0.0,
                "seeds": int(len(finals)),
            })
    summary = {"rows": rows, "alphas": [("inf" if a is None else f"{a:g}") for a in ALPHAS] + ["shared"],
               "algorithms": ALGOS, "n": 3, "K": K, "seeds": SEEDS, "beta": 0.25,
               "calibration": str(CALIBRATION_DST.relative_to(ROOT))}
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    ensure_calibration()
    for alpha in ALPHAS:
        run_cell(alpha)
    run_shared_type_cell()
    summary = summarise()
    print(json.dumps(summary["rows"], indent=2))


if __name__ == "__main__":
    main()
