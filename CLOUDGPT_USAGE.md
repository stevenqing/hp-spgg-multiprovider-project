# CloudGPT Usage

CloudGPT support was discovered locally in:

- `C:\Users\v-shuqingshi\BazaarBench\shuqing\cloudgpt_client.py`
- `C:\Users\v-shuqingshi\BazaarBench\scripts\cloudgpt_proxy.py`

It uses Azure AD authentication, not an `OPENAI_API_KEY` secret.

## Direct Backend

This project now supports:

```powershell
$env:LLM_HPGG_BACKEND = "cloudgpt"
uv run python smoke_test.py --backend cloudgpt --out logs/smoke_cloudgpt.log
```

Default CloudGPT models are configured in `config/providers.yaml`:

```text
player_model = gpt-5.4-mini-20260317
judge_model  = gpt-5.4-mini-20260317
```

You can override them with:

```powershell
$env:LLM_HPGG_PLAYER_MODEL = "gpt-5.4-mini-20260317"
$env:LLM_HPGG_JUDGE_MODEL = "gpt-5.4-mini-20260317"
```

Authentication order:

1. Azure CLI, because `az` is installed on this machine.
2. Device-code login if you set `CLOUDGPT_USE_DEVICE_CODE=1`.
3. Interactive broker fallback when Azure CLI is not selected.

Useful auth flags:

```powershell
$env:CLOUDGPT_USE_AZURE_CLI = "1"
$env:CLOUDGPT_USE_DEVICE_CODE = "1"
```

## Run HP-SPGG With CloudGPT Label

For the synthetic benchmark pipeline:

```powershell
.\scripts\run_hp_spgg_benchmark.ps1 -Backends cloudgpt
```

For live LLM smoke testing, run the smoke command first. Live calibration is not yet wired to replace the synthetic reward tensor with model-judged rewards, so the current benchmark runner uses `cloudgpt` as a provider label unless explicit LLM calls are added to calibration.

## BazaarBench Proxy Pattern

BazaarBench also includes a local proxy:

```powershell
cd C:\Users\v-shuqingshi\BazaarBench
python scripts\cloudgpt_proxy.py --port 18900
```

Then OpenAI-compatible clients can use:

```powershell
$env:OPENAI_API_KEY = "dummy"
$env:OPENAI_BASE_URL = "http://127.0.0.1:18900"
```

The proxy forwards `/v1/chat/completions` to:

```text
https://cloudgpt-openai.azure-api.net/openai/v1/chat/completions
```

and refreshes Azure AD bearer tokens automatically.
