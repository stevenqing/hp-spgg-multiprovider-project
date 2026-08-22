"""Validate optional E-F MaaSSim frozen-beta bonus artifacts."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
E_F = ROOT / "analysis" / "e_f_maassim_bonus"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def main() -> None:
    per_seed = rows(E_F / "e_f_maassim_bonus_per_seed.csv")
    summary = rows(E_F / "e_f_maassim_bonus_summary.csv")
    metadata = json.loads((E_F / "e_f_maassim_bonus_metadata.json").read_text(encoding="utf-8"))
    expected = {(seed, tracker) for seed in range(10) for tracker in ("pact", "pact_plus")}
    observed = {(int(row["seed"]), row["tracker"]) for row in per_seed}
    if len(per_seed) != 20 or observed != expected:
        raise AssertionError(f"E-F grid mismatch: rows={len(per_seed)}")
    if len(summary) != 2:
        raise AssertionError(f"E-F summary rows={len(summary)}, expected 2")
    for row in per_seed:
        expected_beta = 0.25 if row["tracker"] == "pact_plus" else 0.0
        if not math.isclose(float(row["beta"]), expected_beta):
            raise AssertionError(f"E-F beta mismatch: {row}")
    pact = {int(row["seed"]): float(row["utility"]) for row in per_seed if row["tracker"] == "pact"}
    plus = {int(row["seed"]): float(row["utility"]) for row in per_seed if row["tracker"] == "pact_plus"}
    gaps = [plus[seed] - pact[seed] for seed in range(10)]
    paired = metadata["paired_gap"]
    if not math.isclose(float(paired["pact_plus_minus_pact_mean"]), mean(gaps), abs_tol=1e-12):
        raise AssertionError("E-F paired mean is inconsistent with per-seed rows")
    if not (float(paired["ci95_low"]) <= 0.0 <= float(paired["ci95_high"])):
        raise AssertionError("E-F release expects the observed unresolved bonus gap")
    changed = sum(int(row["assignment_changes_vs_pact"]) for row in per_seed if row["tracker"] == "pact_plus")
    compared = sum(int(row["compared_snapshots"]) for row in per_seed if row["tracker"] == "pact_plus")
    if changed != 4 or compared != 406:
        raise AssertionError(f"E-F assignment accounting changed: {changed}/{compared}")
    mechanism = rows(ROOT / "analysis" / "courier_dispatch_maassim" / "maassim_pact_persona_mechanism_summary.csv")
    source_pact = next(row for row in mechanism if row["variant"] == "pact")
    if not math.isclose(mean(list(pact.values())), float(source_pact["realized_utility"]), abs_tol=1e-12):
        raise AssertionError("E-F PACT reference does not reproduce the mechanism replay")
    if metadata.get("provider_calls") != 0 or metadata.get("beta") != 0.25:
        raise AssertionError("E-F metadata is not a zero-provider frozen-beta run")
    print(
        json.dumps(
            {
                "status": "ok",
                "rows": len(per_seed),
                "assignment_changes": changed,
                "compared_snapshots": compared,
                "paired_gap": paired,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
