"""E-1.3+ extended sweep to empirically probe the no-PF lower bound.

For each (n, K, backbone, prior) cell we run the 9 default algorithms with
matched seeds, reusing calibrations that already exist on disk so no new LLM
calls are made:

  backbone=analytic  -> _archive/calibration/e1_e4_llm/E3_n{n}_live.npz   (n in 2..5)
                        analysis/e1_1_n_scaling/calibration_synth_n6.npy (n=6)
  backbone=deepseek  -> results_phase2/e1_1_llm_tier/calibration_live_n{n}_deepseek.npy
  backbone=llama_maverick
                      -> results_phase2/e1_1_llm_tier/calibration_live_n{n}_llama_maverick.npy

The goal is to compare Joint-PSRL (which respects the joint correlated prior)
against PACT / PACT+ (which uses a factored prior) as n and K grow.  Under
thm:lower-no-pf the regret gap should scale like sqrt(|Theta|^{n-1} K).

Output: analysis/e1_3_lower_bound/E1_3lb_n{n}_K{K}_{backbone}_{prior_tag}.npz
        analysis/e1_3_lower_bound/sweep_summary.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from itertools import product
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "analysis" / "e1_3_lower_bound"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ALGOS = [
    "hpsmg_plus", "hpsmg", "joint_psrl", "map_greedy",
    "psrl_notype", "iql_independent_actions", "iql", "random", "oracle",
]

# (backbone, n) -> calibration path
ANALYTIC_ARCHIVE = ROOT / "_archive" / "calibration" / "e1_e4_llm"
SYNTH_N6 = ROOT / "analysis" / "e1_1_n_scaling" / "calibration_synth_n6.npy"
LLM_TIER_DIR = ROOT / "results_phase2" / "e1_1_llm_tier"


def calibration_path(backbone: str, n: int) -> Path:
    if backbone == "analytic":
        if n <= 5:
            p = ANALYTIC_ARCHIVE / f"E3_n{n}_live.npz"
        else:
            p = SYNTH_N6
    elif backbone in {"deepseek", "llama_maverick", "kimi_k2", "gpt5_nano"}:
        p = LLM_TIER_DIR / f"calibration_live_n{n}_{backbone}.npy"
    else:
        raise ValueError(f"unknown backbone {backbone}")
    if not p.exists():
        raise FileNotFoundError(f"calibration not found: {p}")
    return p


PRIOR_SPECS = {
    # tag -> (prior-mode, joint-prior-alpha or None)
    "uniform":     ("uniform", None),
    "dir_a0p1":    ("joint_dirichlet", 0.1),
    "dir_a1":      ("joint_dirichlet", 1.0),
    "shared_type": ("shared_type", None),
}


def cell_out(n: int, K: int, backbone: str, prior_tag: str) -> Path:
    return OUT_DIR / f"E1_3lb_n{n}_K{K}_{backbone}_{prior_tag}.npz"


def run_cell(n: int, K: int, backbone: str, prior_tag: str, seeds: int,
             beta: float, overwrite: bool) -> Path:
    out_npz = cell_out(n, K, backbone, prior_tag)
    if out_npz.exists() and not overwrite:
        print(f"SKIP existing {out_npz.name}")
        return out_npz
    cal = calibration_path(backbone, n)
    mode, alpha = PRIOR_SPECS[prior_tag]
    cmd = [
        sys.executable, "-m", "llm_hpgg.run_experiment",
        "--K", str(K),
        "--n", str(n),
        "--seeds", str(seeds),
        "--beta", str(beta),
        "--algos", *ALGOS,
        "--calibration", str(cal),
        "--out", str(out_npz),
        "--matched-seeds",
        "--prior-mode", mode,
    ]
    if alpha is not None:
        cmd += ["--joint-prior-alpha", str(alpha)]
    print(f"RUN n={n} K={K} backbone={backbone} prior={prior_tag}")
    print("  ", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=str(ROOT))
    return out_npz


def summarise(rows_out: Path) -> dict:
    rows = []
    for npz in sorted(OUT_DIR.glob("E1_3lb_*.npz")):
        # parse name: E1_3lb_n{n}_K{K}_{backbone}_{prior_tag}.npz
        stem = npz.stem[len("E1_3lb_"):]
        parts = stem.split("_")
        n = int(parts[0][1:])
        K = int(parts[1][1:])
        # backbone may itself contain "_" (llama_maverick) — re-join
        # last component(s) are prior_tag; prior_tag is one of PRIOR_SPECS keys
        # find which suffix matches a known prior_tag
        prior_tag = None
        for tag in PRIOR_SPECS:
            if stem.endswith("_" + tag):
                prior_tag = tag
                backbone = stem[len(f"n{n}_K{K}_") : -(len(tag) + 1)]
                break
        if prior_tag is None:
            print(f"WARN cannot parse prior from {npz.name}")
            continue
        d = np.load(npz, allow_pickle=True)
        algos = [str(a) for a in d["algorithms"]]
        cum = np.asarray(d["cumulative_regret"], dtype=float)
        for i, a in enumerate(algos):
            finals = cum[i, :, -1]
            rows.append({
                "n": n, "K": K, "backbone": backbone, "prior": prior_tag,
                "algorithm": a,
                "mean": float(np.mean(finals)),
                "sem": float(np.std(finals, ddof=1) / np.sqrt(len(finals))) if len(finals) > 1 else 0.0,
                "seeds": int(len(finals)),
            })
    summary = {
        "rows": rows,
        "algorithms": ALGOS,
        "priors": list(PRIOR_SPECS.keys()),
    }
    rows_out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ns", type=int, nargs="+", default=[3, 4, 5])
    ap.add_argument("--Ks", type=int, nargs="+", default=[20, 50, 100])
    ap.add_argument("--backbones", type=str, nargs="+",
                    default=["analytic"],
                    choices=["analytic", "deepseek", "llama_maverick", "kimi_k2", "gpt5_nano"])
    ap.add_argument("--priors", type=str, nargs="+",
                    default=["uniform", "dir_a0p1", "shared_type"],
                    choices=list(PRIOR_SPECS.keys()))
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--beta", type=float, default=0.25)
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--summary-only", action="store_true",
                    help="Skip runs, just rebuild summary.json from existing cells.")
    args = ap.parse_args()

    if not args.summary_only:
        for n, K, backbone, prior_tag in product(args.ns, args.Ks, args.backbones, args.priors):
            try:
                run_cell(n, K, backbone, prior_tag,
                         seeds=args.seeds, beta=args.beta, overwrite=args.overwrite)
            except FileNotFoundError as e:
                print(f"SKIP missing calibration: {e}")

    summary = summarise(OUT_DIR / "sweep_summary.json")
    print(f"\nWrote {len(summary['rows'])} rows to {OUT_DIR/'sweep_summary.json'}")


if __name__ == "__main__":
    main()
