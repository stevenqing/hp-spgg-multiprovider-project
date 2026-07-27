"""Extract active input data for fig10_concordia_main_v7."""

from __future__ import annotations

import csv
import glob
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
PLOT_SCRIPT = ROOT / "scripts" / "plot_fig_concordia_main_v4.py"
OUT_CSV = ANALYSIS / "concordia_fig10_main_v7_active_data_long.csv"
OUT_JSON = ANALYSIS / "concordia_fig10_main_v7_active_data_long.json"

spec = importlib.util.spec_from_file_location("plot_fig_concordia_main_v4", PLOT_SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("could not import plot script")
plot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plot)


def line_for_method_metric(path: Path, method: str, metric: str) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    method_line = None
    brace_depth = 0
    in_method_obj = False
    for idx, line in enumerate(lines, start=1):
        if f'"method": "{method}"' in line:
            method_line = idx
            in_method_obj = True
            brace_depth = line.count("{") - line.count("}")
            continue
        if in_method_obj:
            if f'"{metric}"' in line:
                return f"{path.relative_to(ROOT).as_posix()}:{idx}: {line.strip()}"
            brace_depth += line.count("{") - line.count("}")
            if brace_depth <= 0 and idx > (method_line or 0):
                in_method_obj = False
    return f"{path.relative_to(ROOT).as_posix()}:?: method={method} metric={metric} not found"


def line_for_verbal_value(path: Path, metric: str = "focal_score_mean") -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    for idx, line in enumerate(lines, start=1):
        if f'"{metric}"' in line:
            return f"{path.relative_to(ROOT).as_posix()}:{idx}: {line.strip()}"
    return f"{path.relative_to(ROOT).as_posix()}:?: {metric} not found"


def best_run_for(pattern_v2: str, pattern_v1: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    seen: set[str] = set()
    for pat in (pattern_v2, pattern_v1):
        for raw_path in sorted(glob.glob(pat)):
            path = Path(raw_path)
            data = json.loads(path.read_text(encoding="utf-8"))
            cfg = data.get("config", path.name)
            if cfg in seen:
                continue
            summary = {row["method"]: row for row in data["summary"]}
            out[cfg] = {"summary": summary, "path": path, "data": data}
            seen.add(cfg)
    return out


def pub_axes() -> list[dict[str, Any]]:
    runs = best_run_for(
        str(ANALYSIS / "concordia_pub_coordination_compact_*mechanistic_joint_v2.json"),
        str(ANALYSIS / "concordia_pub_coordination_compact_*mechanistic_joint_s*.json"),
    )
    order = [
        ("capetown_s100", "capetown\n(s=100)"),
        ("capetown_s30", "capetown\n(s=30)"),
        ("edinburgh_s30", "edinburgh\n(s=30)"),
        ("edinburgh_closures_s30", "edinburgh\nclosures"),
        ("edinburgh_tough_friendship_s30", "edinburgh\ntough fr."),
        ("london_s30", "london\n(s=30)"),
        ("london_closures_s30", "london\nclosures"),
        ("london_mini_s30", "london mini\n(s=30)"),
    ]
    axes = []
    for key, label in order:
        match = None
        for _, value in runs.items():
            tag = value["path"].as_posix().split("/")[-1]
            if key in tag:
                match = value
                break
        if match is not None:
            axes.append({"panel": "Pub Coordination", "domain": "pub", "config_key": key, "axis_label": label, **match})
    return axes


def hag_axes() -> list[dict[str, Any]]:
    runs_single = best_run_for(
        str(ANALYSIS / "concordia_haggling_compact_*_s30_v3.json"),
        str(ANALYSIS / "concordia_haggling_compact_*_s30_v2.json"),
    ) or best_run_for(
        str(ANALYSIS / "concordia_haggling_compact_*_s30.json"),
        str(ANALYSIS / "concordia_haggling_compact_*_s30.json"),
    )
    runs_multi = best_run_for(
        str(ANALYSIS / "concordia_haggling_multi_item_compact_*_s30_v3.json"),
        str(ANALYSIS / "concordia_haggling_multi_item_compact_*_s30_v2.json"),
    ) or best_run_for(
        str(ANALYSIS / "concordia_haggling_multi_item_compact_*_s30.json"),
        str(ANALYSIS / "concordia_haggling_multi_item_compact_*_s30.json"),
    )
    axes = []
    for key, label in [
        ("fruitville", "fruitville\n(single)"),
        ("fruitville_gullible", "fruitville\ngullible\n(single)"),
        ("vegbrooke", "vegbrooke\n(single)"),
        ("vegbrooke_stubborn", "vegbrooke\nstubborn"),
        ("vegbrooke_strange_game", "vegbrooke\nstrange"),
    ]:
        if key in runs_single:
            axes.append({"panel": "Haggling", "domain": "haggling", "config_key": key, "axis_label": label, **runs_single[key]})
    for key, label in [
        ("fruitville_multi", "fruitville\nmulti"),
        ("fruitville_gullible", "fruitville\ngullible (multi)"),
        ("vegbrooke", "vegbrooke\n(multi)"),
        ("cumulative_score", "cumulative\nscore (multi)"),
    ]:
        if key in runs_multi:
            axes.append({"panel": "Haggling", "domain": "haggling_multi_item", "config_key": key, "axis_label": label, **runs_multi[key]})
    return axes


def verbal_sources(domain: str, config_key: str) -> tuple[float | None, list[str], str]:
    pattern = ANALYSIS / "llm_psrl_verbal" / f"concordia_full_{domain}_{config_key}_*_llmpsrl.json"
    values = []
    sources = []
    for raw_path in sorted(glob.glob(str(pattern))):
        path = Path(raw_path)
        data = json.loads(path.read_text(encoding="utf-8"))
        for row in data.get("summary", []):
            if row.get("method") == "llm_psrl_verbal" and row.get("focal_score_mean") is not None:
                values.append(float(row["focal_score_mean"]))
                sources.append(line_for_verbal_value(path, "focal_score_mean"))
    if not values:
        return None, [], str(pattern.relative_to(ROOT) if pattern.is_relative_to(ROOT) else pattern)
    return float(sum(values) / len(values)), sources, str(pattern.relative_to(ROOT))


def norm(values: list[float | None]) -> tuple[list[float], float | None, float | None, str | None, str | None]:
    present = [(idx, value) for idx, value in enumerate(values) if value is not None and math.isfinite(value)]
    if not present:
        return [0.0] * len(values), None, None, None, None
    lo_idx, lo = min(present, key=lambda item: item[1])
    hi_idx, hi = max(present, key=lambda item: item[1])
    if hi <= lo:
        return [1.0 if value is not None and math.isfinite(value) else 0.0 for value in values], lo, hi, None, None
    return [((value - lo) / (hi - lo)) if value is not None and math.isfinite(value) else 0.0 for value in values], lo, hi, str(lo_idx), str(hi_idx)


def build_rows() -> list[dict[str, Any]]:
    rows = []
    for axes, methods in ((pub_axes(), plot.PUB_METHODS), (hag_axes(), plot.HAG_METHODS)):
        for axis in axes:
            metric = "focal_score_mean"
            raw_values: list[float | None] = []
            source_refs: list[str] = []
            effective_methods: list[str] = []
            for method in methods:
                effective = "oracle_joint" if method == "oracle_focal" and axis["panel"] == "Pub Coordination" and "oracle_focal" not in axis["summary"] else method
                value = None
                source_ref = ""
                if method == "llm_psrl_verbal":
                    value, sources, pattern = verbal_sources(axis["domain"], axis["config_key"])
                    source_ref = "; ".join(sources) if sources else f"未找到: {pattern}"
                elif method == "oracle_focal" and axis["panel"] == "Haggling":
                    value = plot.TRUE_HAG_ORACLE_FOCAL.get((axis["domain"], axis["config_key"]))
                    if value is not None:
                        source_ref = "computed: scripts/analyze_concordia_haggling_true_oracle_focal.py oracle_focal.focal_score_mean"
                    else:
                        source_ref = f"未找到: TRUE_HAG_ORACLE_FOCAL[{axis['domain']},{axis['config_key']}]"
                else:
                    row = axis["summary"].get(effective)
                    if row is not None and row.get(metric) is not None:
                        value = float(row[metric])
                        source_ref = line_for_method_metric(axis["path"], effective, metric)
                    else:
                        source_ref = f"未找到: {axis['path'].relative_to(ROOT).as_posix()} summary[{effective}].{metric}"
                raw_values.append(value)
                source_refs.append(source_ref)
                effective_methods.append(effective)
            normalized, axis_min, axis_max, _, _ = norm(raw_values)
            present = [(method, value) for method, value in zip(methods, raw_values) if value is not None and math.isfinite(value)]
            min_method, min_value = min(present, key=lambda item: item[1]) if present else ("", None)
            max_method, max_value = max(present, key=lambda item: item[1]) if present else ("", None)
            for method, effective, value, radius, source_ref in zip(methods, effective_methods, raw_values, normalized, source_refs):
                rows.append({
                    "panel": axis["panel"],
                    "config_key": axis["config_key"],
                    "axis_label": axis["axis_label"].replace("\n", " "),
                    "method": method,
                    "effective_source_method": effective,
                    "metric_name": metric,
                    "absolute_value": "" if value is None else f"{value:.12g}",
                    "normalized_radius": f"{radius:.12g}",
                    "axis_min_method": min_method,
                    "axis_min_value": "" if min_value is None else f"{min_value:.12g}",
                    "axis_max_method": max_method,
                    "axis_max_value": "" if max_value is None else f"{max_value:.12g}",
                    "source_file_line": source_ref,
                })
    return rows


def main() -> None:
    rows = build_rows()
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    OUT_JSON.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"rows={len(rows)} csv={OUT_CSV.relative_to(ROOT)} json={OUT_JSON.relative_to(ROOT)}")
    missing = [row for row in rows if not row["absolute_value"]]
    print(f"missing={len(missing)}")
    for row in missing[:20]:
        print(row["panel"], row["config_key"], row["method"], row["source_file_line"])


if __name__ == "__main__":
    main()
