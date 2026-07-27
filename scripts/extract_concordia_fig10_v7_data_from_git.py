"""Extract fig10_concordia_main_v7 active-data table from plot-script inputs.

The current checkout no longer contains the JSON files that
scripts/plot_fig_concordia_main_v4.py globs from analysis/. This extractor uses
those exact glob rules and, when files are absent from the working tree, reads
the last retained Git snapshot known to contain them (default: 9e7f12b). Source
references are therefore explicit: either path:Lxx for working-tree files or
<commit>:path:Lxx for Git blobs.
"""

from __future__ import annotations

import csv
import fnmatch
import glob
import importlib.util
import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
PLOT_SCRIPT = ROOT / "scripts" / "plot_fig_concordia_main_v4.py"
OUT_CSV = ANALYSIS / "concordia_fig10_main_v7_active_data_long.csv"
OUT_JSON = ANALYSIS / "concordia_fig10_main_v7_active_data_long.json"
GIT_SNAPSHOT = "9e7f12b"

spec = importlib.util.spec_from_file_location("plot_fig_concordia_main_v4", PLOT_SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("could not import plot script")
plot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plot)


@dataclass
class SourceBlob:
    path: str
    text: str
    source_kind: str
    commit: str | None = None

    @property
    def ref_prefix(self) -> str:
        return f"{self.commit}:{self.path}" if self.commit else self.path


def git_lines(commit: str) -> list[str]:
    result = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", commit],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def git_show(commit: str, path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout


GIT_PATHS = git_lines(GIT_SNAPSHOT)


def working_glob(pattern: str) -> list[SourceBlob]:
    blobs = []
    for raw in sorted(glob.glob(pattern)):
        path = Path(raw)
        blobs.append(SourceBlob(path.relative_to(ROOT).as_posix(), path.read_text(encoding="utf-8"), "working_tree"))
    return blobs


def git_glob(pattern: str) -> list[SourceBlob]:
    # Convert an absolute analysis pattern back into a repo-relative Unix glob.
    pat_path = Path(pattern)
    try:
        rel = pat_path.relative_to(ROOT).as_posix()
    except ValueError:
        rel = str(pat_path).replace("\\", "/")
    matches = [path for path in GIT_PATHS if fnmatch.fnmatch(path, rel)]
    return [SourceBlob(path, git_show(GIT_SNAPSHOT, path), "git_blob", GIT_SNAPSHOT) for path in sorted(matches)]


def source_glob(pattern: str) -> list[SourceBlob]:
    working = working_glob(pattern)
    return working if working else git_glob(pattern)


def load_json(blob: SourceBlob) -> dict[str, Any]:
    return json.loads(blob.text)


def best_run_for(pattern_v2: str, pattern_v1: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    seen: set[str] = set()
    for pattern in (pattern_v2, pattern_v1):
        for blob in source_glob(pattern):
            data = load_json(blob)
            cfg = data.get("config", Path(blob.path).name)
            if cfg in seen:
                continue
            summary = {row["method"]: row for row in data["summary"]}
            out[cfg] = {"summary": summary, "blob": blob, "data": data}
            seen.add(cfg)
    return out


def line_for_method_metric(blob: SourceBlob, method: str, metric: str) -> str:
    lines = blob.text.splitlines()
    in_obj = False
    in_summary = False
    depth = 0
    for index, line in enumerate(lines, start=1):
        if '"summary"' in line and "[" in line:
            in_summary = True
            continue
        if in_summary and '"episodes"' in line and "[" in line:
            break
        if not in_summary:
            continue
        if f'"method": "{method}"' in line:
            in_obj = True
            depth = max(1, line.count("{") - line.count("}"))
            continue
        if in_obj:
            if f'"{metric}"' in line:
                return f"{blob.ref_prefix}:L{index}: {line.strip()}"
            depth += line.count("{") - line.count("}")
            if depth <= 0:
                in_obj = False
    return f"{blob.ref_prefix}:?: method={method} metric={metric} not found"


def line_for_verbal_value(blob: SourceBlob, metric: str = "focal_score_mean") -> str:
    for index, line in enumerate(blob.text.splitlines(), start=1):
        if f'"{metric}"' in line:
            return f"{blob.ref_prefix}:L{index}: {line.strip()}"
    return f"{blob.ref_prefix}:?: {metric} not found"


def pub_axes() -> list[dict[str, Any]]:
    runs = best_run_for(
        str(ANALYSIS / "concordia_pub_coordination_compact_*mechanistic_joint_v2.json"),
        str(ANALYSIS / "concordia_pub_coordination_compact_*mechanistic_joint_s*.json"),
    )
    order = [
        ("capetown_s100", "capetown\\n(s=100)"),
        ("capetown_s30", "capetown\\n(s=30)"),
        ("edinburgh_s30", "edinburgh\\n(s=30)"),
        ("edinburgh_closures_s30", "edinburgh\\nclosures"),
        ("edinburgh_tough_friendship_s30", "edinburgh\\ntough fr."),
        ("london_s30", "london\\n(s=30)"),
        ("london_closures_s30", "london\\nclosures"),
        ("london_mini_s30", "london mini\\n(s=30)"),
    ]
    axes: list[dict[str, Any]] = []
    for key, label in order:
        match = None
        for _, value in runs.items():
            if key in Path(value["blob"].path).name:
                match = value
                break
        if match is None:
            legacy_name = {
                "capetown_s100": "concordia_pub_coordination_compact_capetown_mechanistic_joint_s100.json",
                "capetown_s30": "concordia_pub_coordination_compact_capetown_mechanistic_joint_s30.json",
                "edinburgh_s30": "concordia_pub_coordination_compact_edinburgh_mechanistic_joint_s30.json",
                "edinburgh_closures_s30": "concordia_pub_coordination_compact_edinburgh_closures_mechanistic_joint_s30.json",
                "edinburgh_tough_friendship_s30": "concordia_pub_coordination_compact_edinburgh_tough_friendship_mechanistic_joint_s30.json",
                "london_s30": "concordia_pub_coordination_compact_london_mechanistic_joint_s30.json",
                "london_closures_s30": "concordia_pub_coordination_compact_london_closures_mechanistic_joint_s30.json",
                "london_mini_s30": "concordia_pub_coordination_compact_london_mini_mechanistic_joint_s30.json",
            }[key]
            legacy_path = f"analysis/{legacy_name}"
            if legacy_path in GIT_PATHS:
                blob = SourceBlob(legacy_path, git_show(GIT_SNAPSHOT, legacy_path), "git_blob_legacy_name", GIT_SNAPSHOT)
                data = load_json(blob)
                match = {"summary": {row["method"]: row for row in data["summary"]}, "blob": blob, "data": data}
        if match:
            axes.append({"panel": "Pub Coordination", "domain": "pub", "config_key": key, "axis_label": label, **match})
    return axes


def hag_axes() -> list[dict[str, Any]]:
    runs_single = best_run_for(
        str(ANALYSIS / "concordia_haggling_compact_*_s30_v3.json"),
        str(ANALYSIS / "concordia_haggling_compact_*_s30_v2.json"),
    )
    if not runs_single:
        runs_single = best_run_for(
            str(ANALYSIS / "concordia_haggling_compact_*_s30.json"),
            str(ANALYSIS / "concordia_haggling_compact_*_s30.json"),
        )
    runs_multi = best_run_for(
        str(ANALYSIS / "concordia_haggling_multi_item_compact_*_s30_v3.json"),
        str(ANALYSIS / "concordia_haggling_multi_item_compact_*_s30_v2.json"),
    )
    if not runs_multi:
        runs_multi = best_run_for(
            str(ANALYSIS / "concordia_haggling_multi_item_compact_*_s30.json"),
            str(ANALYSIS / "concordia_haggling_multi_item_compact_*_s30.json"),
        )
    axes: list[dict[str, Any]] = []
    for key, label in [
        ("fruitville", "fruitville\\n(single)"),
        ("fruitville_gullible", "fruitville\\ngullible\\n(single)"),
        ("vegbrooke", "vegbrooke\\n(single)"),
        ("vegbrooke_stubborn", "vegbrooke\\nstubborn"),
        ("vegbrooke_strange_game", "vegbrooke\\nstrange"),
    ]:
        if key in runs_single:
            axes.append({"panel": "Haggling", "domain": "haggling", "config_key": key, "axis_label": label, **runs_single[key]})
    for key, label in [
        ("fruitville_multi", "fruitville\\nmulti"),
        ("fruitville_gullible", "fruitville\\ngullible (multi)"),
        ("vegbrooke", "vegbrooke\\n(multi)"),
        ("cumulative_score", "cumulative\\nscore (multi)"),
    ]:
        if key in runs_multi:
            axes.append({"panel": "Haggling", "domain": "haggling_multi_item", "config_key": key, "axis_label": label, **runs_multi[key]})
    return axes


def verbal_sources(domain: str, config_key: str) -> tuple[float | None, list[str], str]:
    pattern = ANALYSIS / "llm_psrl_verbal" / f"concordia_full_{domain}_{config_key}_*_llmpsrl.json"
    values: list[float] = []
    sources: list[str] = []
    for blob in source_glob(str(pattern)):
        data = load_json(blob)
        for row in data.get("summary", []):
            if row.get("method") == "llm_psrl_verbal" and row.get("focal_score_mean") is not None:
                values.append(float(row["focal_score_mean"]))
                sources.append(line_for_verbal_value(blob, "focal_score_mean"))
    if not values:
        rel = pattern.relative_to(ROOT).as_posix()
        return None, [], rel
    return float(sum(values) / len(values)), sources, pattern.relative_to(ROOT).as_posix()


def norm(values: list[float | None]) -> list[float]:
    present = [value for value in values if value is not None and math.isfinite(value)]
    if not present:
        return [0.0] * len(values)
    lo, hi = min(present), max(present)
    if hi <= lo:
        return [1.0 if value is not None and math.isfinite(value) else 0.0 for value in values]
    return [((value - lo) / (hi - lo)) if value is not None and math.isfinite(value) else 0.0 for value in values]


def build_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for axes, methods in ((pub_axes(), plot.PUB_METHODS), (hag_axes(), plot.HAG_METHODS)):
        for axis in axes:
            metric = "focal_score_mean"
            raw_values: list[float | None] = []
            source_refs: list[str] = []
            effective_methods: list[str] = []
            for method in methods:
                effective = "oracle_joint" if method == "oracle_focal" and axis["panel"] == "Pub Coordination" and "oracle_focal" not in axis["summary"] else method
                value: float | None = None
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
                        source_ref = line_for_method_metric(axis["blob"], effective, metric)
                    else:
                        source_ref = f"未找到: {axis['blob'].ref_prefix} summary[{effective}].{metric}"
                raw_values.append(value)
                source_refs.append(source_ref)
                effective_methods.append(effective)
            radii = norm(raw_values)
            present = [(method, value) for method, value in zip(methods, raw_values) if value is not None and math.isfinite(value)]
            min_method, min_value = min(present, key=lambda item: item[1]) if present else ("", None)
            max_method, max_value = max(present, key=lambda item: item[1]) if present else ("", None)
            for method, effective, value, radius, source_ref in zip(methods, effective_methods, raw_values, radii, source_refs):
                rows.append({
                    "panel": axis["panel"],
                    "config_key": axis["config_key"],
                    "axis_label": axis["axis_label"].replace("\\n", " "),
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
                    "input_source_kind": axis["blob"].source_kind,
                    "input_snapshot": axis["blob"].commit or "working_tree",
                })
    return rows


def main() -> None:
    rows = build_rows()
    if not rows:
        raise SystemExit("no rows extracted")
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    OUT_JSON.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    missing = [row for row in rows if not row["absolute_value"]]
    print(f"rows={len(rows)} csv={OUT_CSV.relative_to(ROOT)} json={OUT_JSON.relative_to(ROOT)} missing={len(missing)}")
    for row in missing[:30]:
        safe_source = row["source_file_line"].encode("unicode_escape").decode("ascii")
        print(row["panel"], row["config_key"], row["method"], safe_source)


if __name__ == "__main__":
    main()
