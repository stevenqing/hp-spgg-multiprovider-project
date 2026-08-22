"""Render markdown tables for E-1.1 analytic + LLM-tier (9 algos)."""
import json
from pathlib import Path

ALGO_ORDER = ['hpsmg_plus','hpsmg','joint_psrl','map_greedy','psrl_notype','iql','iql_independent_actions','random','oracle']
LABEL = {'hpsmg_plus':'PACT+','hpsmg':'PACT','joint_psrl':'Joint-PSRL','map_greedy':'MAP-greedy',
         'psrl_notype':'PSRL (no type)','iql':'IQL (joint)','iql_independent_actions':'IQL (indep)',
         'random':'Random','oracle':'Oracle'}

def fmt_an():
    rows = json.loads(Path('analysis/e1_1_n_scaling/summary.json').read_text())['rows']
    out = ['| n | algorithm | final cum-regret mean | sem |', '| ---: | --- | ---: | ---: |']
    for n in sorted({r['n'] for r in rows}):
        for a in ALGO_ORDER:
            r = next((x for x in rows if x['n']==n and x['algorithm']==a), None)
            if r is None: continue
            out.append(f"| {n} | {LABEL[a]} | {r['final_cumulative_regret_mean']:.3f} | {r['final_cumulative_regret_sem']:.3f} |")
    return '\n'.join(out)

def fmt_llm():
    rows = json.loads(Path('results_phase2/e1_1_llm_tier/summary.json').read_text())['rows']
    out = ['| backbone | n | algorithm | mean | sem |', '| --- | ---: | --- | ---: | ---: |']
    for bk in ['deepseek','llama_maverick']:
        for n in sorted({r['n'] for r in rows if r['backbone']==bk}):
            for a in ALGO_ORDER:
                r = next((x for x in rows if x['backbone']==bk and x['n']==n and x['algorithm']==a), None)
                if r is None: continue
                out.append(f"| {bk} | {n} | {LABEL[a]} | {r['mean']:.3f} | {r['sem']:.3f} |")
    return '\n'.join(out)

Path('logs/_e1_1_analytic_table.md').write_text(fmt_an(), encoding='utf-8')
Path('logs/_e1_1_llm_table.md').write_text(fmt_llm(), encoding='utf-8')
print('OK')
