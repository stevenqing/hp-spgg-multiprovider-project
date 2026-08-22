"""Validate Figure 6 v22 geometry, data identity, labels, and palette."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import fitz
from PIL import Image

import render_harp_maassim_main_v22 as figure


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "arr_paper" / "figs" / "fig_maassim_combined_v22.pdf"
PNG = ROOT / "arr_paper" / "figs" / "fig_maassim_combined_v22.png"
DATA = ROOT / "arr_paper" / "figs" / "fig_maassim_combined_v22_data.json"
EXPECTED_SIZE_PT = (468.0, 158.4)
EXPECTED_PNG_PX = (1950, 660)
EXPECTED_NUMERIC_SHA256 = "e3a7982614a8dea4636abaac754bffb0133d4d9f1aede174473a7312464d20d4"
EXPECTED_LABELS = (
	"HARP",
	"LLM-belief",
	"LLM-PSRL",
	"A-ToM-1",
	"ECON-BNE",
	"MoA",
	"Puppeteer",
	"Nearest",
	"Oracle",
)
EXPECTED_POLICY_COLORS = {policy: color for policy, _, color in figure.POLICIES}


def main() -> None:
	payload = figure.numeric_payload()
	numeric_sha256 = figure.payload_sha256(payload)
	if numeric_sha256 != EXPECTED_NUMERIC_SHA256:
		raise AssertionError(
			f"v22 numeric payload drifted from v21: {numeric_sha256} != {EXPECTED_NUMERIC_SHA256}"
		)

	retained = json.loads(DATA.read_text(encoding="utf-8"))
	if retained["numeric_payload_sha256"] != EXPECTED_NUMERIC_SHA256:
		raise AssertionError("retained v22 data fingerprint does not match v21")
	if retained["payload"] != payload:
		raise AssertionError("retained v22 data payload differs from the renderer payload")

	with fitz.open(PDF) as document:
		if len(document) != 1:
			raise AssertionError(f"v22 has {len(document)} pages")
		rect = document[0].rect
		actual_size = (float(rect.width), float(rect.height))
		if any(abs(actual - expected) > 1.0 for actual, expected in zip(actual_size, EXPECTED_SIZE_PT)):
			raise AssertionError(f"v22 page size is {actual_size}, expected {EXPECTED_SIZE_PT}")
		text = document[0].get_text()
	missing = [label for label in EXPECTED_LABELS if label not in text]
	if missing:
		raise AssertionError(f"v22 is missing method labels: {missing}")
	if "decomposit" in text or "??" in text:
		raise AssertionError("v22 contains clipped or unresolved text")

	with Image.open(PNG) as image:
		if image.size != EXPECTED_PNG_PX:
			raise AssertionError(f"v22 PNG is {image.size}, expected {EXPECTED_PNG_PX}")

	if figure.POLICY_COLORS != EXPECTED_POLICY_COLORS:
		raise AssertionError(f"v22 policy colors differ from v21: {figure.POLICY_COLORS}")
	if figure.RED != figure.ORACLE_COLOR:
		raise AssertionError("v22 Oracle color differs from v21")

	print(json.dumps({
		"status": "ok",
		"page_size_pt": actual_size,
		"png_size_px": EXPECTED_PNG_PX,
		"numeric_payload_sha256": numeric_sha256,
		"pdf_sha256": hashlib.sha256(PDF.read_bytes()).hexdigest(),
		"methods": list(EXPECTED_LABELS),
		"policy_colors": EXPECTED_POLICY_COLORS,
		"oracle_color": figure.ORACLE_COLOR,
	}, indent=2))


if __name__ == "__main__":
	main()
