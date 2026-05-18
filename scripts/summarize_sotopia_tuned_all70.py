"""Quick aggregation of sotopia tuned all70 results: model x baseline mean focal score."""
from __future__ import annotations
import glob, json, os, statistics
from collections import defaultdict

BASELINES = ["hpsmg_plus", "atom_tom1", "econ_bne", "llm_belief", "llm_greedy"]

def parse_filename(path: str) -> tuple[str, str]:
    name = os.path.basename(path).replace("sotopia_hard_official_", "").replace("_sotopia_tuned_all70.json", "")
    for bl in BASELINES:
        if name.endswith("_" + bl):
            return name[: -(len(bl) + 1)], bl
    raise ValueError(path)

def collect_scores(d: dict) -> list[float]:
    """Per-episode mean of agent_1/agent_2 'overall'."""
    scores: list[float] = []
    for r in d.get("episodes", []):
        ov = r.get("overall") or {}
        vals = [v for v in ov.values() if isinstance(v, (int, float))]
        if vals:
            scores.append(sum(vals) / len(vals))
    return scores

def main() -> None:
    by_model: dict[str, dict[str, tuple[float, int]]] = defaultdict(dict)
    for path in sorted(glob.glob("analysis/sotopia_hard_official_*_sotopia_tuned_all70.json")):
        model, baseline = parse_filename(path)
        scores = collect_scores(json.load(open(path, encoding="utf-8")))
        mean = statistics.fmean(scores) if scores else float("nan")
        by_model[model][baseline] = (mean, len(scores))

    print(f"{'model':45s}" + "".join(f"{b:>12s}" for b in BASELINES) + "   best  hpsmg+_rank  delta_2nd")
    overall = {b: [] for b in BASELINES}
    wins = 0
    for model in sorted(by_model):
        vals = {b: by_model[model].get(b, (float("nan"), 0))[0] for b in BASELINES}
        for b in BASELINES:
            if vals[b] == vals[b]:
                overall[b].append(vals[b])
        ranking = sorted(BASELINES, key=lambda k: -vals[k])
        best = ranking[0]
        hp_rank = ranking.index("hpsmg_plus") + 1
        rest = [vals[b] for b in BASELINES if b != "hpsmg_plus" and vals[b] == vals[b]]
        delta = vals["hpsmg_plus"] - max(rest) if rest else float("nan")
        wins += int(best == "hpsmg_plus")
        print(f"{model:45s}" + "".join(f"{vals[b]:12.3f}" for b in BASELINES) + f"   {best:11s}  {hp_rank}     {delta:+.3f}")

    print()
    print(f"hpsmg_plus wins (best per model): {wins}/{len(by_model)}")
    print()
    print(f"{'baseline':>12s}  avg_across_models")
    for b in BASELINES:
        if overall[b]:
            print(f"{b:>12s}  {statistics.fmean(overall[b]):.3f}")

if __name__ == "__main__":
    main()
