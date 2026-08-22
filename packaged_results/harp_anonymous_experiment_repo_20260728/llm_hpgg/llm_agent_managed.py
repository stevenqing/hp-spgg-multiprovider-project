"""ManagedProvider backend using Azure AD authentication."""

from __future__ import annotations

import os
import shutil
import time
from typing import Callable


TENANT_ID = os.getenv("MANAGED_PROVIDER_TENANT_ID", "")
SCOPE = os.getenv("MANAGED_PROVIDER_SCOPE", "")
BASE_URL = os.getenv("MANAGED_PROVIDER_BASE_URL", "")
API_VERSION = "2025-04-01-preview"

_TOKEN_PROVIDER: Callable[[], str] | None = None


def _call_llm(system_prompt: str, user_message: str, model: str, max_tokens: int = 256, temperature: float = 0.8) -> str:
    try:
        from openai import AzureOpenAI
    except ImportError as exc:
        raise RuntimeError("Install the openai package to use LLM_HPGG_BACKEND=managed") from exc

    base_url = os.getenv("MANAGED_PROVIDER_BASE_URL", BASE_URL)
    if not base_url:
        raise RuntimeError("Set MANAGED_PROVIDER_BASE_URL before using the organization-managed provider backend")
    client = AzureOpenAI(
        api_version=os.getenv("MANAGED_PROVIDER_API_VERSION", API_VERSION),
        base_url=base_url,
        azure_ad_token_provider=_get_token_provider(),
        timeout=float(os.getenv("MANAGED_PROVIDER_TIMEOUT", "60")),
        max_retries=int(os.getenv("MANAGED_PROVIDER_MAX_RETRIES", "0")),
    )
    last_error: Exception | None = None
    attempts = max(1, int(os.getenv("MANAGED_PROVIDER_ATTEMPTS", "4")))
    for attempt in range(attempts):
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
    raise RuntimeError(f"ManagedProvider call failed after {attempts} attempts: {last_error}")


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

    static_token = os.getenv("MANAGED_PROVIDER_BEARER_TOKEN")
    if static_token:
        _TOKEN_PROVIDER = lambda: static_token
        return _TOKEN_PROVIDER

    try:
        from azure.identity import AzureCliCredential, DeviceCodeCredential, get_bearer_token_provider
    except ImportError as exc:
        raise RuntimeError("Install azure-identity to use LLM_HPGG_BACKEND=managed") from exc

    tenant_id = os.getenv("MANAGED_PROVIDER_TENANT_ID", TENANT_ID)
    scope = os.getenv("MANAGED_PROVIDER_SCOPE", SCOPE)
    if not tenant_id or not scope:
        raise RuntimeError(
            "Set MANAGED_PROVIDER_TENANT_ID and MANAGED_PROVIDER_SCOPE, or provide MANAGED_PROVIDER_BEARER_TOKEN"
        )
    use_azure_cli = os.getenv("MANAGED_PROVIDER_USE_AZURE_CLI")
    if os.getenv("MANAGED_PROVIDER_USE_BROKER_LOGIN", "0") == "1":
        credential = _interactive_or_device_credential(tenant_id)
    elif os.getenv("MANAGED_PROVIDER_USE_DEVICE_CODE", "0") == "1":
        credential = DeviceCodeCredential(tenant_id=tenant_id)
    elif use_azure_cli == "1" or (use_azure_cli is None and shutil.which("az")):
        credential = AzureCliCredential(tenant_id=tenant_id)
    else:
        credential = _interactive_or_device_credential(tenant_id)

    _TOKEN_PROVIDER = get_bearer_token_provider(credential, scope)
    return _TOKEN_PROVIDER


def _interactive_or_device_credential(tenant_id: str):
    try:
        import msal
        from azure.identity.broker import InteractiveBrowserBrokerCredential

        return InteractiveBrowserBrokerCredential(
            tenant_id=tenant_id,
            use_default_broker_account=True,
            parent_window_handle=msal.PublicClientApplication.CONSOLE_WINDOW_HANDLE,
        )
    except Exception:
        from azure.identity import DeviceCodeCredential

        return DeviceCodeCredential(tenant_id=tenant_id)
