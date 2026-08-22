"""Redraw every HARP paper figure from data or explicit release tables."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "arr_paper"
FIGURES = PAPER / "figs"
MANIFEST = PAPER / "HARP_FIGURE_REDRAW_MANIFEST.json"

COMMANDS = [
    (["scripts/make_figures_v3_all.py"], ROOT),
    (["scripts/plot_fig6_e5_trajectories.py"], ROOT),
    (["scripts/plot_fig7_native_vs_llm_baselines.py"], ROOT),
    (["scripts/make_fig_scaling_combined.py"], ROOT),
    (["scripts/render_harp_decentralized_summary.py"], ROOT),
    (["scripts/plot_fig_haggling_pareto.py"], ROOT),
    (["arr_paper/figs/make_fig2_v15.py"], ROOT),
    (["make_fig2_v11c.py"], FIGURES),
    (["scripts/render_iterated_concordia_v5.py"], ROOT),
    (["scripts/render_harp_component_ladder_v1.py"], ROOT),
    (["scripts/render_maassim_rq23_v9.py"], ROOT),
    (["scripts/plot_maassim_main_figure.py"], ROOT),
    (["scripts/render_harp_maassim_main_v21.py"], ROOT),
    (["scripts/replay_maassim_pact_persona_mechanism.py"], ROOT),
    (["scripts/run_e_a_matched_likelihood.py", "--stage", "aggregate"], ROOT),
    (["scripts/render_harp_release_tables.py"], ROOT),
    (["scripts/render_harp_maassim_appendix.py"], ROOT),
    (["scripts/render_harp_sotopia_combined.py"], ROOT),
    (["scripts/render_harp_sotopia_corrected.py"], ROOT),
    (["scripts/render_harp_reward_locality.py"], ROOT),
    (["scripts/make_fig_e1.py"], ROOT),
    (["scripts/make_fig_e3.py"], ROOT),
    (["scripts/render_harp_overview.py"], ROOT),
]

OUTPUT_GENERATORS = {
    "figs/main.pdf": "scripts/render_harp_overview.py",
    "figs/fig_e_a_hp_spgg_matched.pdf": "scripts/run_e_a_matched_likelihood.py --stage aggregate",
    "figs/fig_e3_n_agent_scaling_v3.pdf": "scripts/make_fig_e3.py",
    "figs/fig_e_g_ladder_v1.pdf": "scripts/render_harp_component_ladder_v1.py",
    "figs/fig_maassim_combined_v21.pdf": "scripts/render_harp_maassim_main_v21.py",
    "figs/fig2_concordia_select_v15.pdf": "arr_paper/figs/make_fig2_v15.py",
    "figs/fig_e_b_iterated_concordia_v5.pdf": "scripts/render_iterated_concordia_v5.py",
    "figs/fig_maassim_rq23_v9.pdf": "scripts/render_maassim_rq23_v9.py",
    "figs/fig_sotopia_combined_v7.pdf": "scripts/render_harp_sotopia_combined.py",
    "figs/fig_e_c_sotopia_corrected.pdf": "scripts/render_harp_sotopia_corrected.py",
    "figs/fig_e_c_sotopia_component_corrected.pdf": "scripts/render_harp_sotopia_corrected.py",
    "figs/fig_e1_1_n_scaling.pdf": "scripts/render_harp_release_tables.py",
    "figs/fig_e1_1_n_scaling_llm.pdf": "scripts/render_harp_release_tables.py",
    "figs/fig_e_d_reward_locality_violation.pdf": "scripts/render_harp_reward_locality.py",
    "figs/fig_e1_3_pf_isolation.pdf": "scripts/render_harp_release_tables.py",
    "figs/fig_e5_cumulative_regret_trajectories_v3.pdf": "scripts/plot_fig6_e5_trajectories.py",
    "figs/fig_e1_posterior_concentration_v3.pdf": "scripts/make_fig_e1.py",
    "figs/E2_native_vs_llm_baselines_main.pdf": "scripts/plot_fig7_native_vs_llm_baselines.py",
    "figs/fig_scaling_hidden_complexity_v5.pdf": "scripts/make_fig_scaling_combined.py",
    "figs/fig10_beta_sweep_v3.pdf": "scripts/make_figures_v3_all.py",
    "figs/fig12_decentralized_price.pdf": "scripts/render_harp_decentralized_summary.py",
    "figs/fig_maassim_concentration_v1.pdf": "scripts/render_harp_maassim_appendix.py",
    "figs/fig_maassim_wait_reject_tradeoff_v1.pdf": "scripts/render_harp_maassim_appendix.py",
    "figs/fig_maassim_pact_persona_mechanism.pdf": "scripts/replay_maassim_pact_persona_mechanism.py",
    "figs/fig_maassim_conflict_dynamics_v4.pdf": "scripts/render_harp_maassim_appendix.py",
    "figs/fig_maassim_unit_validation_v3.pdf": "scripts/plot_maassim_main_figure.py",
    "figs/fig2_concordia_strip_v11c.pdf": "arr_paper/figs/make_fig2_v11c.py",
    "figs/fig11_haggling_pareto.png": "scripts/plot_fig_haggling_pareto.py",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], cwd: Path, environment: dict[str, str]) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, *command], cwd=cwd, env=environment,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"figure command failed ({completed.returncode}): {' '.join(command)}\n"
            + "\n".join((completed.stdout + completed.stderr).splitlines()[-30:])
        )
    return {
        "command": [sys.executable, *command],
        "cwd": cwd.relative_to(ROOT).as_posix() if cwd != ROOT else ".",
        "returncode": completed.returncode,
        "tail": (completed.stdout + completed.stderr).splitlines()[-5:],
    }


def main() -> None:
    started_ns = time.time_ns()
    environment = os.environ.copy()
    environment["MPLBACKEND"] = "Agg"
    environment["PYTHONPATH"] = os.pathsep.join((str(ROOT), str(ROOT / "scripts")))
    command_records = [run(command, cwd, environment) for command, cwd in COMMANDS]

    output_records = []
    for relative, generator in OUTPUT_GENERATORS.items():
        path = PAPER / relative
        if not path.is_file() or path.stat().st_size == 0:
            raise AssertionError(f"redraw did not produce {relative}")
        if path.stat().st_mtime_ns < started_ns:
            raise AssertionError(f"redraw did not refresh {relative}")
        output_records.append({
            "path": relative,
            "generator": generator,
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "modified_ns": path.stat().st_mtime_ns,
        })

    manifest = {
        "schema_version": "1.0",
        "redraw_started_ns": started_ns,
        "policy": "All figures are generated by plotting code; PDF text overlays are prohibited.",
        "commands": command_records,
        "outputs": output_records,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "commands": len(command_records), "outputs": len(output_records), "manifest": MANIFEST.relative_to(ROOT).as_posix()}, indent=2))


if __name__ == "__main__":
    main()
