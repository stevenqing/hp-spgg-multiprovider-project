"""Summarise and plot E-1.1 LLM-tier n-scaling with all 9 baselines."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "results_phase2" / "e1_1_llm_tier"
FIG_DIR = ROOT / "arr_paper" / "figs"
E2_TRACE = ROOT / "analysis" / "E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5_trace.json"
NS = [3, 4, 5, 6]
BACKBONES = ["deepseek", "llama_maverick", "kimi_k2", "gpt5_nano"]
BACKBONE_LABEL = {"deepseek": "DeepSeek-V3.2", "llama_maverick": "Llama-4-Maverick", "kimi_k2": "Kimi-K2.6", "gpt5_nano": "GPT-5.4-nano"}

ALGO_STYLE = {
    "hpsmg_plus":              ("PACT+",                 "#1b3a6f", "D", "-",  2.0),
    "hpsmg":                   ("PACT",                  "#3d6cb3", "o", "-",  1.6),
    "joint_psrl":              ("Joint-PSRL",            "#c44e52", "s", "-",  1.6),
    "map_greedy":              ("MAP-greedy",            "#8172b2", "^", "--", 1.4),
    "psrl_notype":             ("PSRL (no type)",        "#937860", "v", "--", 1.4),
    "iql":                     ("IQL (joint)",           "#da8b41", "x", ":",  1.4),
    "iql_independent_actions": ("IQL (indep)",           "#dd8452", "+", ":",  1.4),
    "random":                  ("Random",                "#999999", "P", ":",  1.2),
    "oracle":                  ("Oracle (known types)",  "#4c956c", "*", "-",  1.4),
}


def collect():
    rows = []
    for bk in BACKBONES:
        for n in NS:
            path = DATA_DIR / f"E1_1_llm_n{n}_{bk}.npz"
            if not path.exists():
                continue
            data = np.load(path, allow_pickle=True)
            algos = [str(a) for a in data["algorithms"]]
            cum = np.asarray(data["cumulative_regret"], dtype=float)
            for idx, algo in enumerate(algos):
                finals = cum[idx, :, -1]
                rows.append({
                    "backbone": bk,
                    "n": n,
                    "algorithm": algo,
                    "mean": float(np.mean(finals)),
                    "sem": float(np.std(finals, ddof=1) / np.sqrt(len(finals))) if len(finals) > 1 else 0.0,
                    "seeds": int(len(finals)),
                })
    return rows


def load_external_refs():
    """Aggregate per-step welfare gaps into final cumulative regret per algo.

    Expects a list of run dicts with keys ``algorithm``, ``seed`` and a
    ``trace`` list of round entries containing ``welfare`` and
    ``oracle_welfare``.
    """
    if not E2_TRACE.exists():
        return {}
    try:
        payload = json.loads(E2_TRACE.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(payload, list):
        return {}
    buckets: dict[str, dict[int, float]] = {}
    for run in payload:
        algo = run.get("algorithm")
        seed = run.get("seed_index", run.get("seed"))
        trace = run.get("trace") or []
        if algo is None or seed is None or not trace:
            continue
        regret = 0.0
        for step in trace:
            regret += float(step.get("oracle_welfare", 0.0)) - float(step.get("welfare", 0.0))
        buckets.setdefault(algo, {})[seed] = regret
    out = {}
    for algo, per_seed in buckets.items():
        vals = list(per_seed.values())
        if not vals:
            continue
        m = float(np.mean(vals))
        s = float(np.std(vals, ddof=1) / np.sqrt(len(vals))) if len(vals) > 1 else 0.0
        # Pretty label
        label_map = {
            "atom_tom0": "A-ToM (L0)",
            "atom_tom1": "A-ToM (L1)",
            "atom_tom2": "A-ToM (L2)",
            "econ_agent": "ECON",
        }
        out[label_map.get(algo, algo)] = (m, s)
    return out


def plot(rows, ext_refs):
    fig, axes_grid = plt.subplots(2, 2, figsize=(13.0, 9.5), sharey=True)
    axes = axes_grid.flatten()
    for ax, bk in zip(axes, BACKBONES):
        for algo, (label, color, marker, ls, lw) in ALGO_STYLE.items():
            sub = sorted([r for r in rows if r["backbone"] == bk and r["algorithm"] == algo],
                         key=lambda r: r["n"])
            if not sub:
                continue
            xs = [r["n"] for r in sub]
            ys = [r["mean"] for r in sub]
            es = [r["sem"] for r in sub]
            ax.errorbar(xs, ys, yerr=es, label=label,
                        color=color, marker=marker, linestyle=ls,
                        markersize=6.5, linewidth=lw, capsize=2.5)
        if bk == "deepseek" and ext_refs:
            for name, (m, _s) in ext_refs.items():
                ax.axhline(m, linestyle="-.", linewidth=0.9, color="#444444", alpha=0.55)
                ax.text(NS[-1] + 0.04, m, f" {name} (n=3 ref)", fontsize=7,
                        va="center", color="#444444")
        ax.set_yscale("symlog", linthresh=1.0)
        ax.set_xlabel("Number of agents n")
        ax.set_title(f"E-1.1 LLM tier: {BACKBONE_LABEL[bk]}")
        ax.set_xticks(NS)
        ax.grid(alpha=0.25, linestyle=":")
    axes_grid[0, 0].set_ylabel("Final cumulative regret (K=20, symlog)")
    axes_grid[1, 0].set_ylabel("Final cumulative regret (K=20, symlog)")
    axes[0].legend(loc="center left", fontsize=7, ncol=1, bbox_to_anchor=(0.0, 0.5))
    fig.tight_layout()
    out = FIG_DIR / "fig_e1_1_n_scaling_llm.pdf"
    fig.savefig(out)
    fig.savefig(out.with_suffix(".png"), dpi=180)
    plt.close(fig)
    print(f"OK figure: {out}")


def main():
    rows = collect()
    ext = load_external_refs()
    out_json = DATA_DIR / "summary.json"
    out_json.write_text(json.dumps({
        "rows": rows,
        "external_refs": {k: {"mean": v[0], "sem": v[1]} for k, v in ext.items()},
    }, indent=2), encoding="utf-8")
    plot(rows, ext)


if __name__ == "__main__":
    main()
