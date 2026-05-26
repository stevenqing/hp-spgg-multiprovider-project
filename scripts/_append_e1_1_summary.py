import json, pathlib
rows = json.loads(pathlib.Path('analysis/e1_1_n_scaling/summary.json').read_text())['rows']
md = ['', '## E-1.1 n-scaling (Wave-2)', '',
      'Figure: arr_paper/figs/fig_e1_1_n_scaling.pdf',
      'Data: analysis/e1_1_n_scaling/E1_1_n{3..6}.npz (Llama-Maverick E3 calibrations for n=3..5; synthetic analytic kernel for n=6)',
      '', '| n | algorithm | final cum-regret mean | sem |',
      '| ---: | --- | ---: | ---: |']
for r in rows:
    md.append(f"| {r['n']} | {r['algorithm']} | {r['final_cumulative_regret_mean']:.3f} | {r['final_cumulative_regret_sem']:.3f} |")
md.append('')
md.append('Observation: PACT+ (beta=0.25) dominates Joint-PSRL and vanilla PACT at every n; vanilla PACT vs Joint-PSRL ratio approximately 1/2 (factor-of-2 PF gap) consistent with the section 4.1 theoretical claim. n=6 magnitudes are small because the synthetic analytic kernel admits a near-flat optimum; a follow-up live LLM-tier sweep (scripts/run_e1_1_llm_tier.py) is queued.')
p = pathlib.Path('analysis/wave1_experiment_additions_summary.md')
p.write_text(p.read_text(encoding='utf-8') + '\n'.join(md) + '\n', encoding='utf-8')
print('appended')
