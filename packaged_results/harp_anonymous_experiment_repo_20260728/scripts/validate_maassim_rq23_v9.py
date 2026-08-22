"""Validate Figure 7 v9 page geometry, CRN gates, and unchanged panels b--d."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import fitz
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
V8 = ROOT / "arr_paper" / "figs" / "fig_maassim_rq23_v8.pdf"
V9 = ROOT / "arr_paper" / "figs" / "fig_maassim_rq23_v9.pdf"
DATA = ROOT / "analysis" / "e_h_maassim_grouped_prior" / "k20_softmax_crn_confirm_seed20_59"
EXPECTED_SIZE = (244.8, 205.2)


def page_size(path: Path) -> tuple[float, float]:
    with fitz.open(path) as document:
        rect = document[0].rect
        return float(rect.width), float(rect.height)


def raster(path: Path) -> np.ndarray:
    with fitz.open(path) as document:
        pixmap = document[0].get_pixmap(matrix=fitz.Matrix(4, 4), alpha=False)
    return np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.width, pixmap.n)


def digest(values: np.ndarray) -> str:
    return hashlib.sha256(values.tobytes()).hexdigest()


def decoded(payload: np.lib.npyio.NpzFile, field: str) -> list[dict[str, object]]:
    return [json.loads(str(value)) for value in payload[field].tolist()]


def mismatch_count(payload: np.lib.npyio.NpzFile, field: str, left: str, right: str) -> int:
    return sum(
        left_value != right_value
        for trace in decoded(payload, field)
        for left_value, right_value in zip(trace[left], trace[right])
    )


def main() -> None:
    size_v8 = page_size(V8)
    size_v9 = page_size(V9)
    for actual in (size_v8, size_v9):
        if any(abs(left - right) > 1e-3 for left, right in zip(actual, EXPECTED_SIZE)):
            raise AssertionError(f"unexpected page size: {actual}")
    if any(abs(left - right) > 1e-9 for left, right in zip(size_v8, size_v9)):
        raise AssertionError(f"v8/v9 page-size mismatch: {size_v8} != {size_v9}")

    old = raster(V8)
    new = raster(V9)
    if old.shape != new.shape:
        raise AssertionError(f"v8/v9 raster shape mismatch: {old.shape} != {new.shape}")
    height, width, _ = old.shape
    regions = {
        "b": (slice(0, int(0.50 * height)), slice(int(0.54 * width), width)),
        "c": (slice(int(0.50 * height), height), slice(0, int(0.50 * width))),
        "d": (slice(int(0.50 * height), height), slice(int(0.50 * width), width)),
    }
    panel_hashes = {}
    for panel, region in regions.items():
        old_crop = old[region]
        new_crop = new[region]
        differing_values = int(np.count_nonzero(old_crop != new_crop))
        if differing_values:
            raise AssertionError(f"panel ({panel}) changed at {differing_values} raster values")
        panel_hashes[panel] = digest(new_crop)

    crn = {}
    for rho, left, right in ((0, "joint", "harp"), (1, "joint", "harp_s")):
        for group_size in (2, 4):
            payload = np.load(
                DATA / f"e_h_rho{rho}p0_g{group_size}_n8_m2_s40.npz",
                allow_pickle=False,
            )
            key = f"rho{rho}_g{group_size}"
            crn[key] = {}
            for field in ("action_traces", "utility_traces", "regret_traces"):
                count = mismatch_count(payload, field, left, right)
                if count:
                    raise AssertionError(f"{key} {field} has {count} mismatches")
                crn[key][field] = count

    print(json.dumps({
        "status": "ok",
        "page_size_v8_pt": size_v8,
        "page_size_v9_pt": size_v9,
        "unchanged_panel_raster_sha256": panel_hashes,
        "crn_mismatches": crn,
    }, indent=2))


if __name__ == "__main__":
    main()
