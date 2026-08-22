"""Generate Wave-1 experiment artifacts from archived HP-SPGG logs.

This script covers:
1) E-0.1 posterior calibration reliability + ECE
2) E-0.2 posterior recovery exponential fit
3) E-0.3 PACT vs Joint-PSRL pathwise identity check
4) E-2.4 estimated call-cost comparison from trace structure

It uses only local archived data and does not trigger new LLM calls.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_E1 = ROOT / "_archive" / "results" / "e1_e4_llm"
CALIB_DIR = ROOT / "_archive" / "root_calibration_npy"
ANALYSIS_DIR = ROOT / "analysis"
FIG_DIR = ROOT / "arr_paper" / "figs"

FIG_DIR.mkdir(parents=True, exist_ok=True)
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class CalibrationStats:
    backbone: str
    ece: float
    brier: float
    n_points: int


def backbone_label_from_file(path: Path) -> str:
    stem = path.stem
    stem = stem.replace("E1_posterior_", "")
    stem = stem.replace("_live", "")
    return stem


def load_e1_points(npz_path: Path) -> tuple[np.ndarray, np.ndarray]:
    data = np.load(npz_path, allow_pickle=True)
    post = np.asarray(data["posterior_history"], dtype=float)
    true_types = np.asarray(data["true_types"], dtype=int)
    # Shapes: (algos=1, seeds, K, n, m), (algos=1, seeds, n)
    post = post[0]
    true_types = true_types[0]

    seeds, horizon, n_agents, _m = post.shape
    conf = np.zeros((seeds, horizon, n_agents), dtype=float)
    corr = np.zeros((seeds, horizon, n_agents), dtype=float)

    for s in range(seeds):
        for a in range(n_agents):
            t = int(true_types[s, a])
            conf[s, :, a] = post[s, :, a, t]
            pred = np.argmax(post[s, :, a, :], axis=-1)
            corr[s, :, a] = (pred == t).astype(float)

    return conf.reshape(-1), corr.reshape(-1)


def compute_reliability(conf: np.ndarray, corr: np.ndarray, bins: int = 10) -> tuple[np.ndarray, np.ndarray, np.ndarray, float, float]:
    edges = np.linspace(0.0, 1.0, bins + 1)
    centers = 0.5 * (edges[:-1] + edges[1:])
    acc = np.full(bins, np.nan, dtype=float)
    cnt = np.zeros(bins, dtype=int)

    for i in range(bins):
        lo, hi = edges[i], edges[i + 1]
        if i < bins - 1:
            mask = (conf >= lo) & (conf < hi)
        else:
            mask = (conf >= lo) & (conf <= hi)
        cnt[i] = int(mask.sum())
        if cnt[i] > 0:
            acc[i] = float(np.mean(corr[mask]))

    valid = cnt > 0
    ece = float(np.sum((cnt[valid] / cnt.sum()) * np.abs(acc[valid] - centers[valid])))
    brier = float(np.mean((conf - corr) ** 2))
    return centers, acc, cnt, ece, brier


def plot_reliability(all_stats: list[CalibrationStats], all_curves: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]]) -> Path:
    fig, axes = plt.subplots(2, 2, figsize=(9.4, 7.0), sharex=True, sharey=True)
    axes = axes.flatten()
    order = sorted(all_curves.keys())

    for ax, name in zip(axes, order):
        centers, acc, cnt = all_curves[name]
        ax.plot([0, 1], [0, 1], linestyle="--", color="#9aa4b2", linewidth=1.0)
        valid = ~np.isnan(acc)
        ax.plot(centers[valid], acc[valid], marker="o", color="#1b3a6f", linewidth=1.4, markersize=4)
        for x, y, c in zip(centers[valid], acc[valid], cnt[valid]):
            if c > 0:
                ax.text(x, y + 0.03, str(int(c)), fontsize=7, color="#5f6b7a", ha="center")
        s = next(item for item in all_stats if item.backbone == name)
        ax.set_title(f"{name}\nECE={s.ece:.4f}, Brier={s.brier:.4f}", fontsize=9)
        ax.grid(alpha=0.25, linestyle=":")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

    fig.text(0.5, 0.04, "Posterior confidence on true persona", ha="center")
    fig.text(0.04, 0.5, "Empirical correctness frequency", va="center", rotation="vertical")
    fig.suptitle("E-0.1 Reliability Diagram (HP-SPGG archived E1 runs)", fontsize=12)
    fig.tight_layout(rect=(0.05, 0.06, 1.0, 0.95))

    out = FIG_DIR / "fig_e0_1_reliability_diagram.pdf"
    fig.savefig(out)
    fig.savefig(out.with_suffix(".png"), dpi=180)
    plt.close(fig)
    return out


def fit_recovery_rate(backbone: str, trajectories: list[dict], horizon_h: int = 10) -> tuple[np.ndarray, np.ndarray, float]:
    rows = [r for r in trajectories if r["backbone"] == backbone]
    rows = sorted(rows, key=lambda x: int(x["round"]))
    k = np.array([int(r["round"]) for r in rows], dtype=float)
    p = np.array([float(r["mean_true_mass"]) for r in rows], dtype=float)

    # Fit log(1-p_k) = a + b*k. Theoretical form: 1-p_k = O(exp(-rho*H*k/2)).
    eps = 1e-8
    gap = np.clip(1.0 - p, eps, 1.0)
    y = np.log(gap)
    b, a = np.polyfit(k, y, 1)
    rho = max(0.0, float(-2.0 * b / horizon_h))
    return k, p, rho


def plot_recovery(summary_json: Path) -> tuple[Path, dict[str, float]]:
    payload = json.loads(summary_json.read_text(encoding="utf-8"))
    trajectories = payload["trajectories"]
    backbones = sorted({row["backbone"] for row in trajectories})

    fig, ax = plt.subplots(figsize=(8.8, 5.0))
    color_cycle = ["#1b3a6f", "#c44e52", "#2c7a5e", "#b8723d"]
    rho_map: dict[str, float] = {}

    for idx, bb in enumerate(backbones):
        k, p, rho = fit_recovery_rate(bb, trajectories)
        rho_map[bb] = rho
        ax.plot(k, p, marker="o", markersize=3.5, linewidth=1.6, color=color_cycle[idx % len(color_cycle)], label=f"{bb} (rho~{rho:.3f})")

    ax.set_xlabel("Episode k")
    ax.set_ylabel("Mean posterior mass on true persona")
    ax.set_title("E-0.2 Posterior Recovery Curves")
    ax.set_xlim(1, max(k))
    ax.set_ylim(0.35, 1.01)
    ax.grid(alpha=0.25, linestyle=":")
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()

    out = FIG_DIR / "fig_e0_2_posterior_recovery_fit.pdf"
    fig.savefig(out)
    fig.savefig(out.with_suffix(".png"), dpi=180)
    plt.close(fig)
    return out, rho_map


def calibration_path_for_backbone(backbone: str) -> Path:
    name = backbone.replace("_live", "")
    pattern = f"calibration_cloudgpt_multi_model_fast4_8algos_{name}_c19.npy"
    path = CALIB_DIR / pattern
    if not path.exists():
        raise FileNotFoundError(f"Missing calibration for {backbone}: {path}")
    return path


def compute_bonus_decay() -> tuple[Path, dict[str, float]]:
    fig, ax = plt.subplots(figsize=(8.8, 5.0))
    color_cycle = ["#1b3a6f", "#c44e52", "#2c7a5e", "#b8723d"]
    terminal_vals: dict[str, float] = {}

    npz_files = sorted(ARCHIVE_E1.glob("E1_posterior_*_live.npz"))
    for idx, npz_path in enumerate(npz_files):
        backbone = backbone_label_from_file(npz_path).replace("_", " ")
        raw_name = backbone_label_from_file(npz_path)
        data = np.load(npz_path, allow_pickle=True)
        post = np.asarray(data["posterior_history"], dtype=float)[0]  # (seeds, K, n, m)
        seeds, horizon, n_agents, m_types = post.shape

        cal = np.load(calibration_path_for_backbone(raw_name + "_live"), allow_pickle=True).item()
        reward = np.asarray(cal["reward_tensor"], dtype=float)  # (n, m, profiles)
        n_profiles = reward.shape[2]

        # pair_abs[i,t,tp,a] = |r_i(t,a)-r_i(tp,a)|
        pair_abs = np.zeros((n_agents, m_types, m_types, n_profiles), dtype=float)
        for i in range(n_agents):
            for t in range(m_types):
                for tp in range(m_types):
                    pair_abs[i, t, tp, :] = np.abs(reward[i, t, :] - reward[i, tp, :])

        d_series = np.zeros(horizon, dtype=float)
        for k in range(horizon):
            seed_max_vals = []
            for s in range(seeds):
                # posterior over personas for each agent at episode k
                p = post[s, k, :, :]  # (n, m)
                d_profile = np.zeros(n_profiles, dtype=float)
                for i in range(n_agents):
                    w = np.outer(p[i], p[i])[:, :, None]  # (m,m,1)
                    d_profile += np.sum(w * pair_abs[i], axis=(0, 1))
                seed_max_vals.append(float(np.max(d_profile)))
            d_series[k] = float(np.mean(seed_max_vals))

        terminal_vals[raw_name] = float(d_series[-1])
        ax.plot(np.arange(1, horizon + 1), d_series, marker="o", markersize=3.5, linewidth=1.6, color=color_cycle[idx % len(color_cycle)], label=f"{backbone} (D_K={d_series[-1]:.4f})")

    ax.set_xlabel("Episode k")
    ax.set_ylabel("Mean max D_k over profiles")
    ax.set_title("E-0.4 Bonus Decay Verification")
    ax.grid(alpha=0.25, linestyle=":")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()

    out = FIG_DIR / "fig_e0_4_bonus_decay.pdf"
    fig.savefig(out)
    fig.savefig(out.with_suffix(".png"), dpi=180)
    plt.close(fig)
    return out, terminal_vals


def bit_identity_report() -> tuple[list[dict], Path]:
    rows: list[dict] = []
    for npz_path in sorted(ARCHIVE_E1.glob("E3_n*_live.npz")):
        data = np.load(npz_path, allow_pickle=True)
        algos = [str(x) for x in data["algorithms"]]
        cum = np.asarray(data["cumulative_regret"], dtype=float)
        try:
            i_pact = algos.index("hpsmg")
            i_joint = algos.index("joint_psrl")
        except ValueError:
            continue
        diff = np.abs(cum[i_pact] - cum[i_joint])
        rows.append(
            {
                "file": npz_path.name,
                "n": int(npz_path.stem.split("_n")[-1].split("_")[0]),
                "max_abs_diff": float(diff.max()),
                "mean_abs_diff": float(diff.mean()),
            }
        )

    rows = sorted(rows, key=lambda x: x["n"])

    coupled_path = ANALYSIS_DIR / "E0_3_coupled_rng_hpsmg_vs_joint_psrl.npz"
    if coupled_path.exists():
        data = np.load(coupled_path, allow_pickle=True)
        algos = [str(x) for x in data["algorithms"]]
        cum = np.asarray(data["cumulative_regret"], dtype=float)
        if "hpsmg" in algos and "joint_psrl" in algos:
            i_pact = algos.index("hpsmg")
            i_joint = algos.index("joint_psrl")
            diff = np.abs(cum[i_pact] - cum[i_joint])
            rows.append(
                {
                    "file": coupled_path.name,
                    "n": int(np.asarray(data["true_types"]).shape[-1]) if "true_types" in data.files else -1,
                    "max_abs_diff": float(diff.max()),
                    "mean_abs_diff": float(diff.mean()),
                }
            )
    out = ANALYSIS_DIR / "E0_3_bit_identity_summary.json"
    out.write_text(json.dumps({"rows": rows}, indent=2), encoding="utf-8")
    return rows, out


def estimate_call_costs() -> tuple[list[dict], Path]:
    # Native PACT family in HP-SPGG uses cached calibration and analytic planning,
    # so runtime LLM calls per episode are effectively zero in archived runs.
    rows: list[dict] = [
        {"algorithm": "hpsmg", "family": "native", "estimated_calls_per_episode": 0},
        {"algorithm": "hpsmg_plus", "family": "native", "estimated_calls_per_episode": 0},
        {"algorithm": "joint_psrl", "family": "native", "estimated_calls_per_episode": 0},
    ]

    trace_path = ANALYSIS_DIR / "E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5_trace.json"
    traces = json.loads(trace_path.read_text(encoding="utf-8"))

    algo_to_calls: dict[str, list[float]] = {}
    for run in traces:
        algo = str(run["algorithm"])
        episodes = run["trace"]
        calls: list[float] = []
        for ep in episodes:
            info = ep.get("info", {})
            if "players" in info and isinstance(info["players"], list):
                calls.append(float(len(info["players"])))
            elif "iterations" in info and isinstance(info["iterations"], list):
                # ECON: one strategy call + per-iteration executor calls.
                iter_calls = 0
                for it in info["iterations"]:
                    iter_calls += len(it.get("executors", []))
                calls.append(float(iter_calls + 1))
        if calls:
            algo_to_calls.setdefault(algo, []).append(float(np.mean(calls)))

    for algo, vals in sorted(algo_to_calls.items()):
        rows.append(
            {
                "algorithm": algo,
                "family": "external-llm",
                "estimated_calls_per_episode": float(np.mean(vals)),
            }
        )

    rows = sorted(rows, key=lambda x: (x["family"], x["algorithm"]))
    out = ANALYSIS_DIR / "E2_4_cost_estimated_summary.json"
    out.write_text(json.dumps({"rows": rows, "note": "estimated from trace structure; token/wall-clock not logged"}, indent=2), encoding="utf-8")
    return rows, out


def write_markdown_report(
    calibration_stats: list[CalibrationStats],
    rho_map: dict[str, float],
    bit_rows: list[dict],
    cost_rows: list[dict],
    reliability_fig: Path,
    recovery_fig: Path,
    bonus_fig: Path,
    bonus_terminal: dict[str, float],
) -> Path:
    lines: list[str] = []
    lines.append("# Wave-1 Experiment Additions (Tier-0 + E-2.4)")
    lines.append("")
    lines.append("Data source: archived NPZ in _archive/results/e1_e4_llm and traces in analysis/.")
    lines.append("")

    lines.append("## E-0.1 Posterior Calibration Reliability")
    lines.append("")
    lines.append(f"Figure: arr_paper/figs/{reliability_fig.name}")
    lines.append("")
    lines.append("| Backbone | ECE | Brier | Points |")
    lines.append("| --- | ---: | ---: | ---: |")
    for s in sorted(calibration_stats, key=lambda x: x.backbone):
        lines.append(f"| {s.backbone} | {s.ece:.4f} | {s.brier:.4f} | {s.n_points} |")
    lines.append("")

    lines.append("## E-0.2 Posterior Recovery Curves")
    lines.append("")
    lines.append(f"Figure: arr_paper/figs/{recovery_fig.name}")
    lines.append("")
    lines.append("Model fit: log(1-p_k) = a + b k, implied rho = -2b/H with H=10.")
    lines.append("")
    lines.append("| Backbone | Fitted rho |")
    lines.append("| --- | ---: |")
    for bb in sorted(rho_map):
        lines.append(f"| {bb} | {rho_map[bb]:.4f} |")
    lines.append("")

    lines.append("## E-0.3 Bit-Identity Check (PACT vs Joint-PSRL)")
    lines.append("")
    lines.append("| File | n | max | mean |")
    lines.append("| --- | ---: | ---: | ---: |")
    for r in bit_rows:
        lines.append(f"| {r['file']} | {r['n']} | {r['max_abs_diff']:.6e} | {r['mean_abs_diff']:.6e} |")
    lines.append("")

    lines.append("## E-0.4 Bonus Decay Verification")
    lines.append("")
    lines.append(f"Figure: arr_paper/figs/{bonus_fig.name}")
    lines.append("")
    lines.append("| Backbone | D_K |")
    lines.append("| --- | ---: |")
    for bb in sorted(bonus_terminal):
        lines.append(f"| {bb} | {bonus_terminal[bb]:.4f} |")
    lines.append("")

    lines.append("## E-2.4 Cost Table (Estimated from Trace Structure)")
    lines.append("")
    lines.append("| Algorithm | Family | Estimated LLM calls per episode |")
    lines.append("| --- | --- | ---: |")
    for r in cost_rows:
        lines.append(f"| {r['algorithm']} | {r['family']} | {r['estimated_calls_per_episode']:.2f} |")
    lines.append("")
    lines.append("Limitation: token usage and wall-clock are not currently logged in traces. This table is call-count only.")

    out = ANALYSIS_DIR / "wave1_experiment_additions_summary.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def main() -> None:
    calibration_stats: list[CalibrationStats] = []
    curves: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}

    for npz in sorted(ARCHIVE_E1.glob("E1_posterior_*_live.npz")):
        name = backbone_label_from_file(npz)
        conf, corr = load_e1_points(npz)
        centers, acc, cnt, ece, brier = compute_reliability(conf, corr, bins=10)
        curves[name] = (centers, acc, cnt)
        calibration_stats.append(CalibrationStats(backbone=name, ece=ece, brier=brier, n_points=int(conf.size)))

    reliability_fig = plot_reliability(calibration_stats, curves)
    recovery_fig, rho_map = plot_recovery(ANALYSIS_DIR / "E1_posterior_concentration_llm_summary.json")
    bonus_fig, bonus_terminal = compute_bonus_decay()
    bit_rows, _bit_json = bit_identity_report()
    cost_rows, _cost_json = estimate_call_costs()
    report = write_markdown_report(
        calibration_stats,
        rho_map,
        bit_rows,
        cost_rows,
        reliability_fig,
        recovery_fig,
        bonus_fig,
        bonus_terminal,
    )

    print(f"OK reliability: {reliability_fig}")
    print(f"OK recovery:    {recovery_fig}")
    print(f"OK bonus:       {bonus_fig}")
    print(f"OK summary:     {report}")


if __name__ == "__main__":
    main()
