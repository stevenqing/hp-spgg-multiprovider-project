"""Per-scenario breakdown: where does hpsmg_plus beat the best alternative baseline?

For each (model, codename), compute mean focal score per baseline (averaged over both agents
within the episode), then rank baselines and show how often hpsmg_plus wins.
"""
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

def ep_score(ep: dict) -> float | None:
    ov = ep.get("overall") or {}
    vals = [v for v in ov.values() if isinstance(v, (int, float))]
    if not vals:
        return None
    return sum(vals) / len(vals)

def main() -> None:
    # data[model][codename][baseline] = score
    data: dict[str, dict[str, dict[str, float]]] = defaultdict(lambda: defaultdict(dict))
    scenario_family: dict[str, str] = {}

    for path in sorted(glob.glob("analysis/sotopia_hard_official_*_sotopia_tuned_all70.json")):
        model, baseline = parse_filename(path)
        d = json.load(open(path, encoding="utf-8"))
        for ep in d.get("episodes", []):
            codename = ep.get("codename") or ep.get("env_id") or "?"
            s = ep_score(ep)
            if s is None:
                continue
            data[model][codename][baseline] = s
            family = codename.rsplit("_", 1)[0]
            scenario_family[codename] = family

    # Per-(model, codename) winner table
    print("=== per-scenario winners (model x codename) ===")
    win_count: dict[str, int] = defaultdict(int)
    total = 0
    hp_margins: list[tuple[float, str, str]] = []  # margin, model, codename
    family_wins: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for model in sorted(data):
        for code in sorted(data[model]):
            scores = data[model][code]
            if "hpsmg_plus" not in scores or len(scores) < 2:
                continue
            ranking = sorted(scores.items(), key=lambda kv: -kv[1])
            best_b, best_v = ranking[0]
            win_count[best_b] += 1
            total += 1
            family_wins[scenario_family[code]][best_b] += 1
            hp = scores["hpsmg_plus"]
            others = [v for b, v in scores.items() if b != "hpsmg_plus"]
            margin = hp - max(others)
            hp_margins.append((margin, model, code))

    print(f"total (model, codename) pairs: {total}")
    print("baseline           wins  win%")
    for b in BASELINES:
        n = win_count.get(b, 0)
        print(f"  {b:16s} {n:4d}  {100*n/total:5.1f}%")

    # Where hpsmg_plus has biggest advantage / disadvantage
    hp_margins.sort(reverse=True)
    print("\n=== top-10 scenarios where hpsmg_plus has LARGEST advantage over best other baseline ===")
    print(f"{'margin':>7s}  model                                  codename")
    for m, model, code in hp_margins[:10]:
        print(f"{m:+7.3f}  {model:38s} {code}")
    print("\n=== top-10 scenarios where hpsmg_plus is WORST behind best other ===")
    for m, model, code in hp_margins[-10:][::-1]:
        print(f"{m:+7.3f}  {model:38s} {code}")

    # Family-level breakdown
    print("\n=== per scenario-family winner counts ===")
    families = sorted(family_wins, key=lambda f: -sum(family_wins[f].values()))
    header = f"{'family':40s}" + "".join(f"{b:>12s}" for b in BASELINES) + "  n"
    print(header)
    for fam in families:
        row = family_wins[fam]
        n = sum(row.values())
        print(f"{fam:40s}" + "".join(f"{row.get(b,0):12d}" for b in BASELINES) + f" {n:3d}")

    # Family-level hpsmg+ vs best alternative mean margin
    print("\n=== per-family hpsmg_plus mean margin vs best alternative (avg across models) ===")
    fam_margins: dict[str, list[float]] = defaultdict(list)
    for model in data:
        for code, scores in data[model].items():
            if "hpsmg_plus" not in scores or len(scores) < 2:
                continue
            others = [v for b, v in scores.items() if b != "hpsmg_plus"]
            fam_margins[scenario_family[code]].append(scores["hpsmg_plus"] - max(others))
    rows = sorted(fam_margins.items(), key=lambda kv: -statistics.fmean(kv[1]))
    print(f"{'family':40s} mean_margin   n   win_rate")
    for fam, ms in rows:
        wr = sum(1 for x in ms if x > 0) / len(ms)
        print(f"{fam:40s}   {statistics.fmean(ms):+6.3f}  {len(ms):3d}   {wr:5.1%}")

if __name__ == "__main__":
    main()
