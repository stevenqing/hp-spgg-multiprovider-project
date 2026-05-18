"""Dump full SOTOPIA-tuned all-70 numeric results to a single markdown report.

Sections:
  1. Aggregate model x baseline mean focal score
  2. Per (model, codename) scores for every baseline
  3. Winner counts per (model, codename) pair
  4. Per scenario-family winner counts + mean margin
  5. Top advantage / disadvantage scenarios for hpsmg_plus
"""
from __future__ import annotations
import glob, json, os, statistics
from collections import defaultdict
from pathlib import Path

BASELINES = ["hpsmg_plus", "atom_tom1", "econ_bne", "llm_belief", "llm_greedy"]
GLOB = "analysis/sotopia_hard_official_*_sotopia_tuned_all70.json"
OUT = Path("analysis/sotopia_tuned_all70_full_report.md")

def parse_filename(p: str) -> tuple[str, str]:
    name = os.path.basename(p).replace("sotopia_hard_official_", "").replace("_sotopia_tuned_all70.json", "")
    for bl in BASELINES:
        if name.endswith("_" + bl):
            return name[: -(len(bl) + 1)], bl
    raise ValueError(p)

def ep_score(ep: dict) -> float | None:
    ov = ep.get("overall") or {}
    vals = [v for v in ov.values() if isinstance(v, (int, float))]
    return sum(vals) / len(vals) if vals else None

def per_agent(ep: dict) -> tuple[float | None, float | None]:
    ov = ep.get("overall") or {}
    return ov.get("agent_1"), ov.get("agent_2")

def main() -> None:
    # raw[model][baseline] = list of (codename, score, a1, a2)
    raw: dict[str, dict[str, list[tuple[str, float, float | None, float | None]]]] = defaultdict(lambda: defaultdict(list))
    files_used: list[str] = []
    for p in sorted(glob.glob(GLOB)):
        model, baseline = parse_filename(p)
        d = json.load(open(p, encoding="utf-8"))
        files_used.append(p)
        for ep in d.get("episodes", []):
            s = ep_score(ep)
            if s is None:
                continue
            a1, a2 = per_agent(ep)
            raw[model][baseline].append((ep.get("codename", "?"), s, a1, a2))

    models = sorted(raw)
    out: list[str] = []
    out.append("# SOTOPIA-hard Tuned-Profile All-70 Full Results\n")
    out.append(f"Source files ({len(files_used)}):\n")
    for p in files_used:
        out.append(f"- `{p}`\n")
    out.append("\n_Score = mean of `episode.overall.agent_1` and `episode.overall.agent_2` (Sotopia self-play overall)._\n\n")

    # ---------------- Section 1: aggregate ----------------
    out.append("## 1. Aggregate mean focal score (per model x baseline, averaged over 70 episodes)\n\n")
    header = "| model | " + " | ".join(BASELINES) + " | best | hp+_rank | Δ_vs_2nd |\n"
    sep = "|---|" + "---|" * (len(BASELINES) + 3) + "\n"
    out.append(header)
    out.append(sep)
    overall_by_baseline: dict[str, list[float]] = {b: [] for b in BASELINES}
    for model in models:
        means: dict[str, float] = {}
        for b in BASELINES:
            scores = [s for _, s, *_ in raw[model].get(b, [])]
            means[b] = statistics.fmean(scores) if scores else float("nan")
            if scores:
                overall_by_baseline[b].append(means[b])
        ranking = sorted(BASELINES, key=lambda b: -means[b])
        best = ranking[0]
        hp_rank = ranking.index("hpsmg_plus") + 1
        rest = [means[b] for b in BASELINES if b != "hpsmg_plus" and means[b] == means[b]]
        delta = means["hpsmg_plus"] - max(rest) if rest else float("nan")
        out.append(
            "| " + model + " | " + " | ".join(f"{means[b]:.3f}" for b in BASELINES)
            + f" | {best} | {hp_rank} | {delta:+.3f} |\n"
        )
    out.append("\n**Average across models:**\n\n")
    out.append("| baseline | avg |\n|---|---|\n")
    for b in BASELINES:
        if overall_by_baseline[b]:
            out.append(f"| {b} | {statistics.fmean(overall_by_baseline[b]):.3f} |\n")

    # Aggregate per (model, codename, baseline) — average across repeated episodes
    agg: dict[str, dict[str, dict[str, list[float]]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for model in models:
        for b in BASELINES:
            for code, s, *_ in raw[model].get(b, []):
                agg[model][code][b].append(s)
    agg_mean: dict[str, dict[str, dict[str, float]]] = {
        m: {c: {b: statistics.fmean(v) for b, v in bdict.items()} for c, bdict in cdict.items()}
        for m, cdict in agg.items()
    }
    agg_count: dict[str, dict[str, int]] = {
        m: {c: len(next(iter(bdict.values()))) for c, bdict in cdict.items()} for m, cdict in agg.items()
    }

    # ---------------- Section 2: per (model, codename) full table ----------------
    out.append("\n## 2. Per-(model, codename) mean scores (averaged over repeated episodes)\n\n")
    for model in models:
        out.append(f"### {model}\n\n")
        codes_all = sorted(agg_mean[model])
        out.append("| codename | n | " + " | ".join(BASELINES) + " | best | Δ(hp+ − best_other) |\n")
        out.append("|---|" + "---|" * (len(BASELINES) + 3) + "\n")
        for code in codes_all:
            scores = agg_mean[model][code]
            n = agg_count[model][code]
            row = f"| {code} | {n} | "
            row += " | ".join(f"{scores[b]:.3f}" if b in scores else "—" for b in BASELINES)
            ranking = sorted(scores.items(), key=lambda kv: -kv[1])
            best_b = ranking[0][0]
            if "hpsmg_plus" in scores:
                others = [v for b, v in scores.items() if b != "hpsmg_plus"]
                delta = scores["hpsmg_plus"] - max(others) if others else float("nan")
                row += f" | {best_b} | {delta:+.3f} |\n"
            else:
                row += f" | {best_b} | — |\n"
            out.append(row)
        out.append("\n")

    # ---------------- Section 3: winner counts ----------------
    out.append("## 3. Winner counts across (model, codename) pairs (using averaged scores)\n\n")
    win_count: dict[str, int] = defaultdict(int)
    total = 0
    margins: list[tuple[float, str, str]] = []
    family_wins: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    family_margins: dict[str, list[float]] = defaultdict(list)
    for model in models:
        for code, scores in agg_mean[model].items():
            if "hpsmg_plus" not in scores or len(scores) < 2:
                continue
            ranking = sorted(scores.items(), key=lambda kv: -kv[1])
            win_count[ranking[0][0]] += 1
            total += 1
            others = [v for b, v in scores.items() if b != "hpsmg_plus"]
            m = scores["hpsmg_plus"] - max(others)
            margins.append((m, model, code))
            family = code.rsplit("_", 1)[0] if code.split("_")[-1].isdigit() else code
            family_wins[family][ranking[0][0]] += 1
            family_margins[family].append(m)
    out.append(f"Total (model, codename) pairs with hpsmg_plus + ≥1 other baseline: **{total}**\n\n")
    out.append("| baseline | wins | win% |\n|---|---|---|\n")
    for b in BASELINES:
        n = win_count.get(b, 0)
        out.append(f"| {b} | {n} | {100 * n / total:.1f}% |\n")

    # ---------------- Section 4: family breakdown ----------------
    out.append("\n## 4. Scenario-family breakdown\n\n")
    out.append("### 4a. Winner counts per family\n\n")
    out.append("| family | " + " | ".join(BASELINES) + " | n |\n")
    out.append("|---|" + "---|" * (len(BASELINES) + 1) + "\n")
    for fam in sorted(family_wins, key=lambda f: -sum(family_wins[f].values())):
        row = family_wins[fam]
        n = sum(row.values())
        out.append("| " + fam + " | " + " | ".join(str(row.get(b, 0)) for b in BASELINES) + f" | {n} |\n")

    out.append("\n### 4b. hpsmg_plus mean margin vs best alternative per family\n\n")
    out.append("| family | mean margin | n | win-rate |\n|---|---|---|---|\n")
    fam_sorted = sorted(family_margins.items(), key=lambda kv: -statistics.fmean(kv[1]))
    for fam, ms in fam_sorted:
        wr = sum(1 for x in ms if x > 0) / len(ms)
        out.append(f"| {fam} | {statistics.fmean(ms):+.3f} | {len(ms)} | {wr:.1%} |\n")

    # ---------------- Section 5: top / bottom scenarios for hpsmg_plus ----------------
    out.append("\n## 5. Top scenarios for hpsmg_plus\n\n")
    margins.sort(reverse=True)
    out.append("### 5a. Largest advantage (Δ = hpsmg_plus − best other)\n\n")
    out.append("| Δ | model | codename |\n|---|---|---|\n")
    for m, model, code in margins[:15]:
        out.append(f"| {m:+.3f} | {model} | {code} |\n")
    out.append("\n### 5b. Largest disadvantage\n\n")
    out.append("| Δ | model | codename |\n|---|---|---|\n")
    for m, model, code in margins[-15:][::-1]:
        out.append(f"| {m:+.3f} | {model} | {code} |\n")

    # ---------------- Section 6: per-agent split (focal vs partner) ----------------
    out.append("\n## 6. Per-agent (focal=agent_1 vs partner=agent_2) means per baseline\n\n")
    out.append("Baseline strategy controls **both** agents in Sotopia self-play; this column shows whether the asymmetry between roles matters.\n\n")
    out.append("| model | baseline | agent_1 mean | agent_2 mean | symmetric mean |\n|---|---|---|---|---|\n")
    for model in models:
        for b in BASELINES:
            rows = raw[model].get(b, [])
            if not rows:
                continue
            a1s = [a for _, _, a, _ in rows if isinstance(a, (int, float))]
            a2s = [a for _, _, _, a in rows if isinstance(a, (int, float))]
            sym = [s for _, s, *_ in rows]
            a1_m = statistics.fmean(a1s) if a1s else float("nan")
            a2_m = statistics.fmean(a2s) if a2s else float("nan")
            sym_m = statistics.fmean(sym) if sym else float("nan")
            out.append(f"| {model} | {b} | {a1_m:.3f} | {a2_m:.3f} | {sym_m:.3f} |\n")

    OUT.write_text("".join(out), encoding="utf-8")
    print(f"wrote {OUT}  ({OUT.stat().st_size / 1024:.1f} KB, {sum(1 for _ in OUT.open(encoding='utf-8'))} lines)")

if __name__ == "__main__":
    main()
