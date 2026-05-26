import json, pathlib
rows = json.loads(pathlib.Path('results_phase2/e1_1_llm_tier/summary.json').read_text())['rows']
md = ['', '## E-1.1 LLM-tier n-scaling (DeepSeek + Llama-Maverick, live judge)', '',
      'Figure: arr_paper/figs/fig_e1_1_n_scaling_llm.pdf',
      'Data: results_phase2/e1_1_llm_tier/E1_1_llm_n{3..6}_{deepseek,llama_maverick}.npz',
      'Calibration: 12 live judge profiles per (n, backbone); 144--288 LLM calls each (Llm_hpgg.calibration_live)',
      '', '| backbone | n | algorithm | mean | sem |',
      '| --- | ---: | --- | ---: | ---: |']
for r in rows:
    md.append(f"| {r['backbone']} | {r['n']} | {r['algorithm']} | {r['mean']:.3f} | {r['sem']:.3f} |")
md.append('')
md.append('Observation: DeepSeek backbone reproduces the clean PACT+ < Joint-PSRL < PACT ordering at every n with PACT/Joint-PSRL ratio near 1.5--2 (consistent with the section 4.1 PF gap). Llama-4-Maverick shows the same ordering at n in {3,4,5}; at n=6 the 12-profile live calibration is too sparse relative to |A|^n=15625 profiles, yielding tid_min_gap approx 0.056 and large posterior variance which inflates all algorithms (PACT+ in particular). Densifying the n=6 Llama calibration (--max-profiles 32) is queued as a follow-up; see scripts/run_e1_1_llm_tier.py.')
p = pathlib.Path('analysis/wave1_experiment_additions_summary.md')
p.write_text(p.read_text(encoding='utf-8') + '\n'.join(md) + '\n', encoding='utf-8')
print('appended')
