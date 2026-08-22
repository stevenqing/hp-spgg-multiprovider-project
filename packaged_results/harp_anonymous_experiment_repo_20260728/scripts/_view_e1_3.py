import json
d = json.loads(open('analysis/e1_3_pf_isolation/summary.json').read())
header = f"{'setting':>16} {'PACT+':>8} {'PACT':>8} {'Joint':>8} {'MAP':>8} {'noType':>8} {'IQL':>8} {'Rand':>8}"
print(header)
seen = []
for r in d['rows']:
    s = r['setting']
    if s in seen:
        continue
    seen.append(s)
    cells = {x['algorithm']: x['mean'] for x in d['rows'] if x['setting'] == s}
    print(f"{s:>16} {cells['hpsmg_plus']:>8.3f} {cells['hpsmg']:>8.3f} {cells['joint_psrl']:>8.3f} {cells['map_greedy']:>8.3f} {cells['psrl_notype']:>8.3f} {cells['iql']:>8.3f} {cells['random']:>8.3f}")
