"""Render the theory-aligned stochastic-channel Claim-B v2 pilot."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis" / "hp_spgg_burn_in_v2_pilot"
SUMMARY = DATA / "burn_in_v2_summary.csv"
FIT = DATA / "burn_in_v2_fits.json"
OUT_DIRS = (DATA, ROOT / "figs")
M_COLORS = {4: "#557A95", 8: "#D4A04A", 16: "#B64B45"}
H_MARKERS = {1: "o", 4: "s", 16: "^"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    rows = read_csv(SUMMARY)
    fits = json.loads(FIT.read_text(encoding="utf-8"))
    plt.rcParams.update({"font.family": "serif", "font.size": 7.5, "pdf.fonttype": 42, "ps.fonttype": 42})
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 3.0))

    axis = axes[0]
    selected = [row for row in rows if row["phase"] == "type_horizon"]
    for row in selected:
        m, H = int(row["m"]), int(row["H"])
        axis.scatter(float(row["predictor_per_agent"]), float(row["median_per_agent_episode"]),
                     color=M_COLORS[m], marker=H_MARKERS[H], s=34, edgecolor="white", linewidth=0.45, zorder=3)
    x = np.asarray([float(row["predictor_per_agent"]) for row in selected])
    fit = fits["type_horizon_fit"]
    line = np.linspace(0.0, float(x.max()) * 1.03, 100)
    axis.plot(line, fit["slope"] * line + fit["intercept"], color="#222222", linestyle="--", linewidth=1.0,
              label=f"OLS slope={fit['slope']:.3f}, $R^2$={fit['r_squared']:.3f}")
    axis.set_xlabel(r"$\log(m\sqrt{m})/(\rho_{a}H)$")
    axis.set_ylabel("Median per-agent burn-in episode")
    axis.set_title("(a) Type and horizon scaling", loc="left", fontsize=8.4)
    axis.legend(frameon=False, fontsize=6.4, loc="upper left")

    axis = axes[1]
    selected = [row for row in rows if row["phase"] == "population"]
    for row in selected:
        n = int(row["n"])
        axis.scatter(float(row["predictor_all_agent"]), float(row["median_all_agent_episode"]),
                     color="#12345D", marker="o", s=36, edgecolor="white", linewidth=0.45, zorder=3)
        axis.annotate(f"n={n}", (float(row["predictor_all_agent"]), float(row["median_all_agent_episode"])),
                      xytext=(3, 2), textcoords="offset points", fontsize=6.4)
    x = np.asarray([float(row["predictor_all_agent"]) for row in selected])
    fit = fits["population_fit"]
    line = np.linspace(float(x.min()) * 0.98, float(x.max()) * 1.02, 100)
    axis.plot(line, fit["slope"] * line + fit["intercept"], color="#222222", linestyle="--", linewidth=1.0,
              label=f"OLS slope={fit['slope']:.3f}, $R^2$={fit['r_squared']:.3f}")
    axis.set_xlabel(r"$[\log(m\sqrt{m})+\log n]/(\rho_a H)$")
    axis.set_ylabel("Median all-agent burn-in episode")
    axis.set_title("(b) Population maximum", loc="left", fontsize=8.4)
    axis.legend(frameon=False, fontsize=6.4, loc="upper left")

    for axis in axes:
        axis.grid(color="#d8d8d8", linestyle=":", linewidth=0.55)
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.tick_params(labelsize=7.0)
    fig.tight_layout(w_pad=1.2, pad=0.5)
    outputs = []
    for directory in OUT_DIRS:
        directory.mkdir(parents=True, exist_ok=True)
        pdf = directory / "fig_hp_spgg_burn_in_v2_pilot.pdf"
        png = directory / "fig_hp_spgg_burn_in_v2_pilot.png"
        fig.savefig(pdf, bbox_inches="tight", pad_inches=0.03, facecolor="white")
        fig.savefig(png, dpi=260, bbox_inches="tight", pad_inches=0.03, facecolor="white")
        outputs.extend((pdf, png))
    plt.close(fig)
    print(json.dumps({"status": "ok", "outputs": [path.relative_to(ROOT).as_posix() for path in outputs]}, indent=2))


if __name__ == "__main__":
    main()
