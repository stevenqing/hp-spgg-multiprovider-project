$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    $env:LLM_HPGG_OFFLINE = "1"

    & .venvs\concordia-py314\Scripts\python.exe -c "from llm_hpgg_concordia.cloudgpt_model import HPGGConcordiaLanguageModel; from llm_hpgg_concordia.embedder import HashingEmbedder; m=HPGGConcordiaLanguageModel(model='offline'); print('concordia-text', m.sample_text('hello', max_tokens=8)[:30]); print('concordia-choice', m.sample_choice('pick one', ['A','B'], seed=1)[:2]); print('concordia-embed', HashingEmbedder(8)('hello world').shape)"
    & .venvs\concordia-py314\Scripts\python.exe -m llm_hpgg_concordia.run_pub_coordination --config puppet --model offline --out analysis\concordia_pub_coordination_official_smoke.json

    $env:SOTOPIA_STORAGE_BACKEND = "local"
    & .venvs\sotopia-py312\Scripts\python.exe -c "from sotopia.messages import Observation; from llm_hpgg_sotopia.agents import HPGGSotopiaAgent; obs=Observation(last_turn='You meet another participant.', turn_number=1, available_actions=['speak','none'], action_instruction='Choose an action.'); agent=HPGGSotopiaAgent('agent_1','llm_belief',model='offline'); agent.goal='Reach a mutually acceptable agreement.'; action=agent.act(obs); print('sotopia-action', action.action_type, action.argument, action.to)"
    & .venvs\sotopia-py312\Scripts\python.exe -m llm_hpgg_sotopia.run_episode_smoke --baseline llm_belief --model offline --turns 2 --out analysis\sotopia_official_episode_smoke.json
}
finally {
    Pop-Location
}