"""Validate Figure 2 v16 geometry, data identity, and labels."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import fitz
from PIL import Image

import render_hp_spgg_matched_v16 as figure


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "arr_paper" / "figs" / "fig_e_a_hp_spgg_matched_v16.pdf"
PNG = ROOT / "arr_paper" / "figs" / "fig_e_a_hp_spgg_matched_v16.png"
DATA = ROOT / "arr_paper" / "figs" / "fig_e_a_hp_spgg_matched_v16_data.json"
EXPECTED_SIZE_PT = (237.6, 183.6)
EXPECTED_PNG_PX = (990, 765)
EXPECTED_METHODS = (
    "Oracle",
    "HARP+",
    "HARP",
    "Joint-PSRL",
    "LLM-PSRL",
    "A-ToM-1",
    "ECON-BNE",
)
EXPECTED_BACKBONES = ("DeepSeek-V3.2", "GPT-5.4-nano", "Kimi-K2.6", "Llama-4-Maverick")


def main() -> None:
    payload = figure.read_payload()
    numeric_sha256 = figure.payload_sha256(payload)
    retained = json.loads(DATA.read_text(encoding="utf-8"))
    if retained["numeric_payload_sha256"] != numeric_sha256:
        raise AssertionError("retained v16 fingerprint does not match the source rows")
    if retained["payload"] != payload:
        raise AssertionError("retained v16 payload differs from the renderer payload")
    if tuple(payload["labels"]) != EXPECTED_METHODS:
        raise AssertionError(f"v16 method order changed: {payload['labels']}")
    if tuple(payload["backbones"]) != EXPECTED_BACKBONES:
        raise AssertionError(f"v16 backbone order changed: {payload['backbones']}")

    with fitz.open(PDF) as document:
        if len(document) != 1:
            raise AssertionError(f"v16 has {len(document)} pages")
        rect = document[0].rect
        actual_size = (float(rect.width), float(rect.height))
        if any(abs(actual - expected) > 1.0 for actual, expected in zip(actual_size, EXPECTED_SIZE_PT)):
            raise AssertionError(f"v16 page size is {actual_size}, expected {EXPECTED_SIZE_PT}")
        text = document[0].get_text()
    for value in (*EXPECTED_METHODS, *EXPECTED_BACKBONES):
        if value not in text:
            raise AssertionError(f"v16 PDF is missing text: {value}")
    for forbidden in ("PSRL-NoType", "A-ToM-0", "A-ToM-2", "??"):
        if forbidden in text:
            raise AssertionError(f"v16 PDF contains forbidden text: {forbidden}")

    with Image.open(PNG) as image:
        if image.size != EXPECTED_PNG_PX:
            raise AssertionError(f"v16 PNG is {image.size}, expected {EXPECTED_PNG_PX}")

    print(json.dumps({
        "status": "ok",
        "page_size_pt": actual_size,
        "png_size_px": EXPECTED_PNG_PX,
        "numeric_payload_sha256": numeric_sha256,
        "pdf_sha256": hashlib.sha256(PDF.read_bytes()).hexdigest(),
        "png_sha256": hashlib.sha256(PNG.read_bytes()).hexdigest(),
        "methods": list(EXPECTED_METHODS),
        "backbones": list(EXPECTED_BACKBONES),
    }, indent=2))


if __name__ == "__main__":
    main()
