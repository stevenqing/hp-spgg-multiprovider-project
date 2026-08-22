"""Run the official Concordia pub_coordination simulation through our adapter."""

from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import json
from pathlib import Path
import sys
from typing import Any

from .cloudgpt_model import HPGGConcordiaLanguageModel
from .embedder import HashingEmbedder


def ensure_concordia_examples_on_path() -> None:
    root = Path(__file__).resolve().parents[1]
    examples_root = root / "external" / "concordia"
    if examples_root.exists():
        sys.path.insert(0, str(examples_root))


def load_config(config_name: str) -> Any:
    if "." not in config_name:
        config_name = f"examples.games.pub_coordination.configs.{config_name}"
    return importlib.import_module(config_name)


def serializable_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "focal_scores": result.get("focal_scores", {}),
        "background_scores": result.get("background_scores", {}),
        "joint_action": dict(result.get("joint_action") or {}),
        "focal_players": list(result.get("focal_players", [])),
        "background_players": list(result.get("background_players", [])),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="puppet", help="Config module name or short config name.")
    parser.add_argument("--model")
    parser.add_argument("--out", default="analysis/concordia_pub_coordination_official_smoke.json")
    parser.add_argument("--max-steps", type=int, help="Override config MAX_STEPS for short smoke runs.")
    parser.add_argument("--show-log", action="store_true", help="Do not suppress Concordia's verbose simulation log.")
    args = parser.parse_args()

    ensure_concordia_examples_on_path()
    from examples.games.pub_coordination import simulation

    config = load_config(args.config)
    if args.max_steps is not None:
        setattr(config, "MAX_STEPS", args.max_steps)

    model = HPGGConcordiaLanguageModel(model=args.model)
    embedder = HashingEmbedder()
    if args.show_log:
        result = simulation.run_simulation(config, model, embedder)
        captured_log = ""
    else:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            result = simulation.run_simulation(config, model, embedder)
        captured_log = buffer.getvalue()

    payload = serializable_result(result or {})
    payload.update(
        {
            "config": args.config,
            "model": args.model or "",
            "captured_log_tail": captured_log[-4000:],
        }
    )
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({key: payload[key] for key in ["config", "joint_action", "focal_scores"]}, indent=2))
    print(f"saved={out_path}")


if __name__ == "__main__":
    main()
