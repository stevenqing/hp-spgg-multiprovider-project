import json, glob, os
from collections import defaultdict

BASES = ['hpsmg_plus','atom_tom1','econ_bne','llm_belief','llm_greedy']

def fam(code):
    parts = code.split('_')
    while parts and parts[-1].isdigit():
        parts.pop()
    return '_'.join(parts) if parts else code

# (model, family, baseline) -> list of episode scores
buckets = defaultdict(list)
fam_counts = defaultdict(int)

for p in sorted(glob.glob('analysis/sotopia_hard_official_*_sotopia_tuned_all70.json')):
    name = os.path.basename(p).replace('sotopia_hard_official_','').replace('_sotopia_tuned_all70.json','')
    bl = None
    for b in BASES:
        if name.endswith('_'+b):
            bl = b; model = name[:-(len(b)+1)]; break
    d = json.load(open(p, encoding='utf-8'))
    for ep in d.get('episodes', []):
        code = ep.get('codename') or ep.get('env_id') or '?'
        ov = ep.get('overall') or {}
        vals = [v for v in ov.values() if isinstance(v, (int, float))]
        if not vals: continue
        s = sum(vals)/len(vals)
        f = fam(code)
        buckets[(model, f, bl)].append(s)
        if bl == 'hpsmg_plus':
            fam_counts[f] += 1

families = sorted({f for (_,f,_) in buckets})
models = sorted({m for (m,_,_) in buckets})
print('families:', len(families), 'models:', len(models))

# Per-family aggregate across models: mean of (per-model means)
print(f"\n{'family':35s} {'eps':>4s} {'hpsmg':>7s} {'best_alt':>10s} {'best_name':>10s} {'margin':>8s}")
rows = []
for f in families:
    per_method = {}
    for b in BASES:
        scores = []
        for m in models:
            xs = buckets.get((m, f, b))
            if xs: scores.append(sum(xs)/len(xs))
        per_method[b] = sum(scores)/len(scores) if scores else None
    if per_method['hpsmg_plus'] is None: continue
    alts = [(b,v) for b,v in per_method.items() if b != 'hpsmg_plus' and v is not None]
    if not alts: continue
    best_name, best_val = max(alts, key=lambda kv: kv[1])
    h = per_method['hpsmg_plus']
    rows.append((f, fam_counts[f], h, best_val, best_name, h-best_val))

rows.sort(key=lambda r: -r[5])
for r in rows:
    print(f"{r[0]:35s} {r[1]:4d} {r[2]:7.3f} {r[3]:10.3f} {r[4]:>10s} {r[5]:+8.3f}")
wins = sum(1 for r in rows if r[5] > 0.005)
losses = sum(1 for r in rows if r[5] < -0.005)
ties = len(rows) - wins - losses
print(f"\ntotal families: {len(rows)}, wins: {wins}, ties: {ties}, losses: {losses}")
