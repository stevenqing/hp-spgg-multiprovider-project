"""Dump full 9-baseline regret table at E-1.3+ headline cell (n=6, K=100, shared_type) across all backbones."""
from __future__ import annotations
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALGOS = ["hpsmg_plus", "hpsmg", "joint_psrl", "map_greedy", "psrl_notype",
         "iql_independent_actions", "iql", "random", "oracle"]
ALGO_LABEL = {
    "hpsmg_plus": "PACT+", "hpsmg": "PACT", "joint_psrl": "Joint-PSRL",
    "map_greedy": "MAP-greedy", "psrl_notype": "PSRL-NoType",
    "iql_independent_actions": "IQL-indep", "iql": "IQL-joint",
    "random": "Random", "oracle": "Oracle",
}
BACKBONES = [
    ("deepseek", "DeepSeek-V3.2"),
    ("kimi_k2", "Kimi-K2.6"),
    ("llama_maverick", "Llama-4-Maverick"),
    ("gpt5_nano", "GPT-5.4-nano"),
]


def fetch(bk: str, n: int, K: int) -> dict:
    f = ROOT / "analysis" / "e1_3_lower_bound" / f"E1_3lb_n{n}_K{K}_{bk}_shared_type.npz"
    d = np.load(f, allow_pickle=True)
    algos = list(d["algorithms"])
    cr = d["cumulative_regret"]  # shape (A, seeds, K)
    final = cr[:, :, -1]
    out = {}
    for i, a in enumerate(algos):
        m = float(np.mean(final[i]))
        s = float(np.std(final[i], ddof=1) / np.sqrt(final.shape[1]))
        out[a] = {"final_cumulative_regret_mean": m, "final_cumulative_regret_sem": s}
    return out


def main(n: int = 6, K: int = 100) -> None:
    header = f"E-1.3+ full 9-baseline cumulative regret at n={n}, K={K}, shared_type prior (10 matched seeds)"
    print(header)
    print(f"{'algorithm':<13}" + "".join(f"{lbl:>22}" for _, lbl in BACKBONES))
    for algo in ALGOS:
        cells = []
        for bk, _ in BACKBONES:
            res = fetch(bk, n, K)[algo]
            m = res["final_cumulative_regret_mean"]
            s = res["final_cumulative_regret_sem"]
            cells.append(f"{m:>13.3f} +/- {s:>4.2f}")
        print(f"{ALGO_LABEL[algo]:<13}" + "".join(f"{c:>22}" for c in cells))

    print()
    print("LaTeX rows (algo & DS & Kimi & Llama & GPT5n):")
    for algo in ALGOS:
        cells = []
        for bk, _ in BACKBONES:
            m = fetch(bk, n, K)[algo]["final_cumulative_regret_mean"]
            cells.append(f"{m:.2f}" if m >= 1 else f"{m:.3f}")
        print(f"{ALGO_LABEL[algo]} & " + " & ".join(cells) + r" \\")


if __name__ == "__main__":
    main()
