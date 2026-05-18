$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$external = Join-Path $root "external"
$venvs = Join-Path $root ".venvs"
$downloads = Join-Path $external ".downloads"

New-Item -ItemType Directory -Force -Path $external | Out-Null
New-Item -ItemType Directory -Force -Path $venvs | Out-Null
New-Item -ItemType Directory -Force -Path $downloads | Out-Null

$repos = @(
    @{ Name = "concordia"; Url = "https://codeload.github.com/google-deepmind/concordia/zip/refs/heads/main"; Prefix = "concordia-main" },
    @{ Name = "sotopia"; Url = "https://codeload.github.com/sotopia-lab/sotopia/zip/refs/heads/main"; Prefix = "sotopia-main" }
)

foreach ($repo in $repos) {
    $zip = Join-Path $downloads ($repo.Name + ".zip")
    $target = Join-Path $external $repo.Name
    $expanded = Join-Path $external $repo.Prefix

    if (-not (Test-Path $target)) {
        Invoke-WebRequest -Uri $repo.Url -OutFile $zip
        Expand-Archive -Path $zip -DestinationPath $external -Force
        if (Test-Path $expanded) {
            Rename-Item -Path $expanded -NewName $repo.Name
        }
    }
}

uv venv (Join-Path $venvs "concordia-py314") --python 3.14
uv pip install --python (Join-Path $venvs "concordia-py314\Scripts\python.exe") -e (Join-Path $external "concordia")
uv pip install --python (Join-Path $venvs "concordia-py314\Scripts\python.exe") openai azure-identity msal

uv venv (Join-Path $venvs "sotopia-py312") --python 3.12
uv pip install --python (Join-Path $venvs "sotopia-py312\Scripts\python.exe") `
    lxml openai rich PettingZoo==1.25.0 redis-om gin-config json-repair absl-py `
    together pydantic hiredis litellm gymnasium typer pydantic-settings python-dotenv
uv pip install --python (Join-Path $venvs "sotopia-py312\Scripts\python.exe") openai azure-identity msal
uv pip install --python (Join-Path $venvs "sotopia-py312\Scripts\python.exe") --no-deps -e (Join-Path $external "sotopia")

& (Join-Path $venvs "concordia-py314\Scripts\python.exe") -c "from concordia.language_model import language_model; from concordia.environment.engines import simultaneous; print('concordia-ok', language_model.LanguageModel.__name__, simultaneous.Simultaneous.__name__)"
$env:SOTOPIA_STORAGE_BACKEND = "local"
& (Join-Path $venvs "sotopia-py312\Scripts\python.exe") -c "from sotopia.messages import AgentAction; from sotopia.envs import ParallelSotopiaEnv; print('sotopia-local-ok', AgentAction(action_type='none', argument='', to=[]).to_natural_language(), ParallelSotopiaEnv.__name__)"
