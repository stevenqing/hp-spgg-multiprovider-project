"""Validate the theory-aligned stochastic-channel Claim-B v2 pilot."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis" / "hp_spgg_burn_in_v2_pilot"
RAW = DATA / "burn_in_v2_raw.csv"
SUMMARY = DATA / "burn_in_v2_summary.csv"
CONTRACTION = DATA / "burn_in_v2_contraction.csv"
FIT = DATA / "burn_in_v2_fits.json"
REPORT = DATA / "burn_in_v2_design_and_results.md"
FIGURE = DATA / "fig_hp_spgg_burn_in_v2_pilot.pdf"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    for path in (RAW, SUMMARY, CONTRACTION, FIT, REPORT, FIGURE):
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(path)
    raw = read_csv(RAW)
    summary = read_csv(SUMMARY)
    contraction = read_csv(CONTRACTION)
    fits = json.loads(FIT.read_text(encoding="utf-8"))
    if len(raw) != 11_400 or len(summary) != 13 or len(contraction) != 84:
        raise AssertionError(f"B-v2 row counts changed: raw={len(raw)}, summary={len(summary)}, contraction={len(contraction)}")
    if fits["provider_calls"] != 0 or fits["stochastic_channel"] != "y ~ Normal(mu_true(action), sigma^2)":
        raise AssertionError("B-v2 is not the declared zero-provider stochastic channel")
    type_fit = fits["type_horizon_fit"]
    population_fit = fits["population_fit"]
    if type_fit["slope"] <= 0.0 or type_fit["r_squared"] < 0.99 or type_fit["observations"] != 9:
        raise AssertionError(f"B-v2 type/horizon pilot fit changed: {type_fit}")
    if population_fit["slope"] <= 0.0 or population_fit["r_squared"] < 0.99 or population_fit["observations"] != 4:
        raise AssertionError(f"B-v2 population pilot fit changed: {population_fit}")
    if any(int(row["censored_agents"]) != 0 or int(row["censored_seeds"]) != 0 for row in summary):
        raise AssertionError("B-v2 pilot unexpectedly contains censored summary cells")

    lookup = {(row["phase"], int(row["n"]), int(row["m"]), int(row["H"])): row for row in summary}
    expected_type = {
        (4, 1): 6.0, (4, 4): 2.0, (4, 16): 1.0,
        (8, 1): 52.0, (8, 4): 13.0, (8, 16): 4.0,
        (16, 1): 243.0, (16, 4): 61.0, (16, 16): 16.0,
    }
    for (m, H), expected in expected_type.items():
        observed = float(lookup[("type_horizon", 3, m, H)]["median_per_agent_episode"])
        if observed != expected:
            raise AssertionError(f"B-v2 type/horizon median changed: m={m}, H={H}, value={observed}")
    population = [float(lookup[("population", n, 8, 4)]["median_all_agent_episode"]) for n in (2, 4, 8, 16)]
    if population != [17.0, 23.0, 28.0, 35.5] or any(left >= right for left, right in zip(population, population[1:])):
        raise AssertionError(f"B-v2 population medians changed: {population}")

    report = REPORT.read_text(encoding="utf-8")
    for text in ("Gaussian channel", "log(n), not linear n", "0.9975948564535484", "0.9936206311503223"):
        if text not in report:
            raise AssertionError(f"B-v2 report missing: {text}")
    if FIGURE.stat().st_size < 10_000:
        raise AssertionError("B-v2 figure is unexpectedly small")
    print(
        json.dumps(
            {
                "status": "ok",
                "raw_rows": len(raw),
                "summary_rows": len(summary),
                "contraction_rows": len(contraction),
                "type_horizon_fit": type_fit,
                "population_fit": population_fit,
                "population_medians": population,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
