"""CloudGPT backend using Azure AD authentication."""

from __future__ import annotations

import os
import shutil
import time
from typing import Callable


TENANT_ID = "72f988bf-86f1-41af-91ab-2d7cd011db47"
SCOPE = "api://feb7b661-cac7-44a8-8dc1-163b63c23df2/.default"
BASE_URL = "https://cloudgpt-openai.azure-api.net/openai/"
API_VERSION = "2025-04-01-preview"

_TOKEN_PROVIDER: Callable[[], str] | None = None


def _call_llm(system_prompt: str, user_message: str, model: str, max_tokens: int = 256, temperature: float = 0.8) -> str:
    try:
        from openai import AzureOpenAI
    except ImportError as exc:
        raise RuntimeError("Install the openai package to use LLM_HPGG_BACKEND=cloudgpt") from exc

    client = AzureOpenAI(
        api_version=os.getenv("CLOUDGPT_API_VERSION", API_VERSION),
        base_url=os.getenv("CLOUDGPT_BASE_URL", BASE_URL),
        azure_ad_token_provider=_get_token_provider(),
        timeout=float(os.getenv("CLOUDGPT_TIMEOUT", "60")),
        max_retries=int(os.getenv("CLOUDGPT_MAX_RETRIES", "0")),
    )
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            request = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "max_completion_tokens": max_tokens,
            }
            if _supports_custom_temperature(model):
                request["temperature"] = temperature
            else:
                request["temperature"] = 1
            extra_body = _extra_body_for_model(model)
            if extra_body:
                request["extra_body"] = extra_body
            response = client.chat.completions.create(
                **request,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            last_error = exc
            time.sleep(min(2**attempt, 8))
    raise RuntimeError(f"CloudGPT call failed after retries: {last_error}")


def _supports_custom_temperature(model: str) -> bool:
    model_lower = model.lower()
    default_temperature_models = ("gpt-5.5", "kimi-")
    return not model_lower.startswith(default_temperature_models)


def _extra_body_for_model(model: str) -> dict[str, object] | None:
    if model.lower().startswith("kimi-"):
        return {"thinking": {"type": "disabled"}, "reasoning_effort": "none"}
    return None


def _get_token_provider() -> Callable[[], str]:
    global _TOKEN_PROVIDER
    if _TOKEN_PROVIDER is not None:
        return _TOKEN_PROVIDER

    try:
        from azure.identity import AzureCliCredential, DeviceCodeCredential, get_bearer_token_provider
    except ImportError as exc:
        raise RuntimeError("Install azure-identity to use LLM_HPGG_BACKEND=cloudgpt") from exc

    if os.getenv("CLOUDGPT_USE_DEVICE_CODE", "0") == "1":
        credential = DeviceCodeCredential(tenant_id=TENANT_ID)
    elif os.getenv("CLOUDGPT_USE_AZURE_CLI", "0") == "1" or shutil.which("az"):
        credential = AzureCliCredential(tenant_id=TENANT_ID)
    else:
        credential = _interactive_or_device_credential()

    _TOKEN_PROVIDER = get_bearer_token_provider(credential, SCOPE)
    return _TOKEN_PROVIDER


def _interactive_or_device_credential():
    try:
        import msal
        from azure.identity.broker import InteractiveBrowserBrokerCredential

        return InteractiveBrowserBrokerCredential(
            tenant_id=TENANT_ID,
            use_default_broker_account=True,
            parent_window_handle=msal.PublicClientApplication.CONSOLE_WINDOW_HANDLE,
        )
    except Exception:
        from azure.identity import DeviceCodeCredential

        return DeviceCodeCredential(tenant_id=TENANT_ID)
