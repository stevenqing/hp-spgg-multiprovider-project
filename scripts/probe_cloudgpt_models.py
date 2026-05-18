"""Probe CloudGPT deployment names with a tiny chat request."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_hpgg.llm_agent_cloudgpt import API_VERSION, BASE_URL, _get_token_provider


DEFAULT_CANDIDATES = [
    "gpt-4o-20240513",
    "gpt-4o-20240806",
    "gpt-4o-20241120",
    "gpt-4o-mini-20240718",
    "gpt-4.1-20250414",
    "gpt-4.1-mini-20250414",
    "gpt-4.1-nano-20250414",
    "gpt-5-20250807",
    "gpt-5-mini-20250807",
    "gpt-5-nano-20250807",
    "gpt-5-pro-20251006",
    "gpt-5.1-20251113",
    "gpt-5.2-20251211",
    "gpt-5.4-20240305",
    "gpt-5.4-pro-20260305",
    "gpt-5.4-mini-20260317",
    "gpt-5.4-nano-20260317",
    "gpt-5.5-20260424",
    "gpt-5-chat-20250807",
    "gpt-5-chat-20251003",
    "gpt-5.1-chat-20251113",
    "gpt-5.2-chat-20251211",
    "gpt-5.2-chat-20260210",
    "gpt-5.3-chat-20260303",
    "o1-20241217",
    "o3-mini-20250131",
    "o3-20250416",
    "o3-pro-20250610",
    "o4-mini-20250416",
    "DeepSeek-V3-0324",
    "DeepSeek-R1",
    "DeepSeek-R1-0528",
    "DeepSeek-V3.1",
    "DeepSeek-V3.2",
    "Kimi-K2-Thinking",
    "Kimi-K2.5",
    "Kimi-K2.6",
    "Llama-3.3-70B-Instruct",
    "Llama-4-Maverick-17B-128E-Instruct-FP8",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe CloudGPT chat deployments.")
    parser.add_argument("--models", default=None, help="Comma-separated model names. Defaults to known local CloudGPT registry names.")
    parser.add_argument("--out", default="analysis/cloudgpt_model_probe.jsonl")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    try:
        from openai import AzureOpenAI
    except ImportError as exc:
        raise RuntimeError("Install openai to probe CloudGPT models") from exc

    models = [value.strip() for value in args.models.split(",") if value.strip()] if args.models else DEFAULT_CANDIDATES
    if args.limit > 0:
        models = models[: args.limit]

    client = AzureOpenAI(
        api_version=API_VERSION,
        base_url=BASE_URL,
        azure_ad_token_provider=_get_token_provider(),
        timeout=20.0,
        max_retries=0,
    )
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for model in models:
            record = probe_model(client, model)
            handle.write(json.dumps(record) + "\n")
            status = record["status"]
            detail = record.get("reply") or record.get("error", "")
            print(f"{status}\t{model}\t{detail}")
    print(f"saved={out_path}")


def probe_model(client, model: str) -> dict[str, object]:
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Reply with OK only."}],
            max_completion_tokens=8,
        )
        return {
            "model": model,
            "status": "ok",
            "reply": (response.choices[0].message.content or "").strip(),
        }
    except Exception as exc:
        return {
            "model": model,
            "status": "failed",
            "error_type": type(exc).__name__,
            "error": str(exc)[:500],
        }


if __name__ == "__main__":
    main()