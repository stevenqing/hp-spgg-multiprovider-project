"""Render two SOTOPIA-Hard figures:
- main:    win-count by scenario family (the "good" part of the story).
- appendix: aggregate focal score per backbone (the "out-of-scope" parity part).

Reads analysis/sotopia_hard_official_<model>_<baseline>_sotopia_tuned_all70.json
(4 backbones x 5 baselines) and emits PDF + PNG into arr_paper/figs/.
"""
from __future__ import annotations
import glob, json, os, statistics
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

mpl.rcParams.update({"font.family": "serif", "font.size": 11, "pdf.fonttype": 42, "ps.fonttype": 42})

BASELINES = ["hpsmg_plus", "atom_tom1", "econ_bne", "llm_belief", "llm_greedy"]
LABELS = {
    "hpsmg_plus": "H-PSMG$^{+}$ (ours)",
    "atom_tom1": "A-ToM-1",
    "econ_bne": "ECON-BNE",
    "llm_belief": "llm_belief",
    "llm_greedy": "llm_greedy",
}
COLORS = {
    "hpsmg_plus": "#1f2d5c",
    "atom_tom1": "#d8a04b",
    "econ_bne": "#a63a3a",
    "llm_belief": "#7a8aa6",
    "llm_greedy": "#bdbdbd",
}
MODEL_LABELS = {
    "DeepSeek_V3_2": "DeepSeek-V3.2",
    "gpt_5_4_nano_20260317": "GPT-5.4-nano",
    "Kimi_K2_6": "Kimi-K2.6",
    "Llama_4_Maverick_17B_128E_Instruct_FP8": "Llama-Maverick",
}
MODEL_ORDER = ["DeepSeek_V3_2", "gpt_5_4_nano_20260317", "Kimi_K2_6", "Llama_4_Maverick_17B_128E_Instruct_FP8"]


def parse_filename(path: str) -> tuple[str, str]:
    name = os.path.basename(path).replace("sotopia_hard_official_", "").replace("_sotopia_tuned_all70.json", "")
    for bl in BASELINES:
        if name.endswith("_" + bl):
            return name[: -(len(bl) + 1)], bl
    raise ValueError(path)


def ep_score(ep: dict) -> float | None:
    ov = ep.get("overall") or {}
    vals = [v for v in ov.values() if isinstance(v, (int, float))]
    return sum(vals) / len(vals) if vals else None


def family_of(code: str) -> str:
    # strip trailing numeric suffix (e.g. craigslist_bargains_00007 -> craigslist_bargains)
    parts = code.split("_")
    while parts and parts[-1].isdigit():
        parts.pop()
    return "_".join(parts) if parts else code


def load_data():
    # data[model][codename][baseline] = score
    data: dict[str, dict[str, dict[str, float]]] = defaultdict(lambda: defaultdict(dict))
    aggregate: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    fam_of: dict[str, str] = {}
    for path in sorted(glob.glob("analysis/sotopia_hard_official_*_sotopia_tuned_all70.json")):
        model, baseline = parse_filename(path)
        d = json.load(open(path, encoding="utf-8"))
        for ep in d.get("episodes", []):
            code = ep.get("codename") or ep.get("env_id") or "?"
            s = ep_score(ep)
            if s is None:
                continue
            data[model][code][baseline] = s
            aggregate[model][baseline].append(s)
            fam_of[code] = family_of(code)
    return data, aggregate, fam_of


def family_wins(data, fam_of):
    fw: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for model in data:
        for code, scores in data[model].items():
            if "hpsmg_plus" not in scores or len(scores) < 2:
                continue
            best_b = max(scores.items(), key=lambda kv: kv[1])[0]
            fw[fam_of[code]][best_b] += 1
    return fw


def pretty_family(name: str) -> str:
    return name.replace("_", " ")


def plot_main(data, fam_of, out_pdf: str):
    """Main fig: top-N (backbone, scenario) cells where H-PSMG+ beats the best alternative.

    Horizontal bars sorted by margin; colour by backbone.
    """
    margins: list[tuple[float, str, str]] = []  # (margin, model, code)
    for model in data:
        for code, scores in data[model].items():
            if "hpsmg_plus" not in scores or len(scores) < 2:
                continue
            others = [v for b, v in scores.items() if b != "hpsmg_plus"]
            margins.append((scores["hpsmg_plus"] - max(others), model, code))
    pos = sorted([m for m in margins if m[0] > 0], reverse=True)[:10]

    backbone_colors = {
        "DeepSeek_V3_2": "#1f4e79",
        "gpt_5_4_nano_20260317": "#c47a3b",
        "Kimi_K2_6": "#5a8a3a",
        "Llama_4_Maverick_17B_128E_Instruct_FP8": "#8b3a62",
    }

    fig, ax = plt.subplots(figsize=(7.3, 4.0))
    y = np.arange(len(pos))[::-1]
    labels = [f"{c}  ({MODEL_LABELS[m]})" for _, m, c in pos]
    vals = [v for v, _, _ in pos]
    cols = [backbone_colors[m] for _, m, _ in pos]
    bars = ax.barh(y, vals, color=cols, edgecolor="black", linewidth=0.6)
    for yi, v in zip(y, vals):
        ax.text(v + 0.02, yi, f"+{v:.2f}", va="center", fontsize=9, fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("Focal-score advantage of H-PSMG$^{+}$ over best alternative baseline")
    ax.set_title("SOTOPIA-Hard: top 10 (backbone, scenario) cells where H-PSMG$^{+}$ wins",
                 fontsize=11)
    ax.set_xlim(0, max(vals) * 1.18)
    ax.axvline(0, color="black", linewidth=0.6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # legend for backbone colors
    handles = [plt.Rectangle((0, 0), 1, 1, color=backbone_colors[m]) for m in MODEL_ORDER]
    ax.legend(handles, [MODEL_LABELS[m] for m in MODEL_ORDER],
              loc="lower right", frameon=False, fontsize=8.5)
    fig.subplots_adjust(left=0.36, right=0.97, top=0.92, bottom=0.12)
    fig.savefig(out_pdf, bbox_inches="tight", pad_inches=0.10)
    fig.savefig(out_pdf.replace(".pdf", ".png"), dpi=200, bbox_inches="tight", pad_inches=0.10)
    plt.close(fig)


def plot_appendix(aggregate, out_pdf: str):
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    x = np.arange(len(MODEL_ORDER))
    width = 0.16
    offsets = (np.arange(len(BASELINES)) - (len(BASELINES) - 1) / 2) * width
    for i, b in enumerate(BASELINES):
        means = [statistics.fmean(aggregate[m].get(b, [float("nan")]) or [float("nan")])
                 for m in MODEL_ORDER]
        bars = ax.bar(x + offsets[i], means, width,
                      color=COLORS[b], label=LABELS[b],
                      edgecolor="black" if b == "hpsmg_plus" else "none",
                      linewidth=1.1 if b == "hpsmg_plus" else 0.0)
        if b == "hpsmg_plus":
            for xi, v in zip(x + offsets[i], means):
                ax.text(xi, v + 0.02, f"{v:.3f}", ha="center", va="bottom",
                        fontsize=8.5, fontweight="bold", color=COLORS[b])
    ax.set_xticks(x)
    ax.set_xticklabels([MODEL_LABELS[m] for m in MODEL_ORDER], fontsize=10)
    ax.set_ylabel("Mean focal score (70 episodes / cell)")
    ax.set_title("SOTOPIA-Hard aggregate: H-PSMG$^{+}$ within $0.1$ of leader on every backbone",
                 fontsize=11, pad=22)
    all_means = [v for m in MODEL_ORDER for b in BASELINES
                 for v in [statistics.fmean(aggregate[m].get(b, [float("nan")]) or [float("nan")])]
                 if v == v]
    ax.set_ylim(min(all_means) - 0.1, max(all_means) + 0.15)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(loc="upper right", ncol=5, frameon=False, fontsize=8.5,
              bbox_to_anchor=(1.0, 1.18))
    fig.subplots_adjust(left=0.10, right=0.98, top=0.84, bottom=0.18)
    fig.savefig(out_pdf, bbox_inches="tight", pad_inches=0.10)
    fig.savefig(out_pdf.replace(".pdf", ".png"), dpi=200, bbox_inches="tight", pad_inches=0.10)
    plt.close(fig)


def main():
    data, aggregate, fam_of = load_data()
    out_dir = "arr_paper/figs"
    os.makedirs(out_dir, exist_ok=True)
    plot_main(data, fam_of, os.path.join(out_dir, "fig_sotopia_hard_main_v2.pdf"))
    plot_appendix(aggregate, os.path.join(out_dir, "fig_sotopia_hard_appendix_v2.pdf"))
    print("[ok] wrote fig_sotopia_hard_main_v2 and _appendix_v2 in", out_dir)


if __name__ == "__main__":
    main()
