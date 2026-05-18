param(
    [string]$Model = 'Llama-4-Maverick-17B-128E-Instruct-FP8'
)

$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path analysis, figs, tables, logs, results\e1_e4_smoke, calibration\e1_e4_smoke | Out-Null

$calib = 'calibration_cloudgpt_multi_model_fast4_8algos_Llama_4_Maverick_17B_128E_Instruct_FP8_c19.npy'

Write-Host '[smoke:E1] posterior trace'
uv run python -m llm_hpgg.run_experiment --K 3 --n 3 --seeds 1 --beta 0 --algos hpsmg --calibration $calib --out results\e1_e4_smoke\E1_posterior_Llama_smoke.npz --record-posterior --matched-seeds --player-model $Model --judge-model $Model
uv run python scripts\analyze_e1_posterior_concentration.py --inputs results\e1_e4_smoke\E1_posterior_Llama_smoke.npz --fig figs\E1_posterior_concentration_smoke.png --out-json analysis\E1_posterior_concentration_smoke.json --out-csv tables\E1_posterior_concentration_smoke.csv

Write-Host '[smoke:E2] type scaling m=2,3'
foreach ($m in @(2, 3)) {
    $cal = "calibration\e1_e4_smoke\E2_type${m}_n3.npz"
    uv run python scripts\build_hp_spgg_scaling_calibration.py --n 3 --type-count $m --backend $Model --samples 1 --out $cal
    uv run python -m llm_hpgg.run_experiment --K 3 --n 3 --seeds 1 --beta 0.25 --algos hpsmg hpsmg_plus --calibration $cal --out "results\e1_e4_smoke\E2_type${m}_smoke.npz" --matched-seeds --record-posterior --player-model $Model --judge-model $Model
}
uv run python scripts\analyze_e2_type_scaling.py --inputs results\e1_e4_smoke\E2_type2_smoke.npz results\e1_e4_smoke\E2_type3_smoke.npz --fig figs\E2_type_scaling_smoke.png --out-json analysis\E2_type_scaling_smoke.json --out-csv tables\E2_type_scaling_smoke.csv

Write-Host '[smoke:E3] n-agent scaling n=2,3'
foreach ($n in @(2, 3)) {
    $cal = "calibration\e1_e4_smoke\E3_n${n}_types4.npz"
    uv run python scripts\build_hp_spgg_scaling_calibration.py --n $n --type-count 4 --backend $Model --samples 1 --out $cal
    uv run python -m llm_hpgg.run_experiment --K 3 --n $n --seeds 1 --beta 0.25 --algos hpsmg joint_psrl hpsmg_plus --calibration $cal --out "results\e1_e4_smoke\E3_n${n}_smoke.npz" --matched-seeds --record-posterior --player-model $Model --judge-model $Model
}
uv run python scripts\analyze_e3_n_agent_scaling.py --inputs results\e1_e4_smoke\E3_n2_smoke.npz results\e1_e4_smoke\E3_n3_smoke.npz --fig figs\E3_n_agent_scaling_smoke.png --out-json analysis\E3_n_agent_scaling_smoke.json --out-csv tables\E3_n_agent_scaling_smoke.csv

Write-Host '[smoke:E4] prior recovery'
foreach ($prior in @('uniform', 'correct', 'adversarial')) {
    uv run python -m llm_hpgg.run_experiment --K 3 --n 3 --seeds 1 --beta 0 --algos hpsmg map_greedy --calibration $calib --out "results\e1_e4_smoke\E4_prior_${prior}_smoke.npz" --prior-mode $prior --prior-mass 0.7 --matched-seeds --record-posterior --player-model $Model --judge-model $Model
}
uv run python scripts\analyze_e4_prior_recovery.py --inputs results\e1_e4_smoke\E4_prior_uniform_smoke.npz results\e1_e4_smoke\E4_prior_correct_smoke.npz results\e1_e4_smoke\E4_prior_adversarial_smoke.npz --fig figs\E4_prior_recovery_smoke.png --out-json analysis\E4_prior_recovery_smoke.json --out-csv tables\E4_prior_recovery_smoke.csv

Write-Host 'smoke_complete=True'