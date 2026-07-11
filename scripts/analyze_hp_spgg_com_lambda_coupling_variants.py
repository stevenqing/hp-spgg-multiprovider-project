"""Compare lambda_couple decoupling-error curves across coupling variants."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_hpgg.personas import PERSONAS  # noqa: E402
from scripts.run_hp_spgg_com_lambda_couple import (  # noqa: E402
    ANALYSIS_DIR,
    JUDGES,
    RealMessagePolicy,
    build_coupled_tensor,
    decoupled_closed_form_value,
    exact_value,
    is_non_decreasing,
    load_base,
    make_coupled_model,
    parse_lam_grid,
)


DEFAULT_LAM_GRID = "0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0,1.25,1.5,2.0"
RANDOM_SEED = 20260624
SPARSE_SEED = 20260625


def center_and_scale(raw: np.ndarray, base: np.ndarray) -> tuple[np.ndarray, dict[str, float]]:
    centered = raw - raw.mean(axis=2, keepdims=True)
    base_std = float(base.std())
    centered_std = float(centered.std())
    if centered_std <= 1e-12:
        raise ValueError("Cannot scale a zero-variance coupling")
    scaled = centered * (base_std / centered_std)
    max_center_abs = float(np.max(np.abs(scaled.mean(axis=2))))
    return scaled, {
        "base_std": base_std,
        "raw_std": float(raw.std()),
        "centered_std": centered_std,
        "scaled_std": float(scaled.std()),
        "max_abs_theta_j_mean_after_scaling": max_center_abs,
        "scaled_min": float(scaled.min()),
        "scaled_max": float(scaled.max()),
    }


def raw_type_match(action_profiles: np.ndarray, type_count: int) -> np.ndarray:
    n_agents, profile_count = 2, len(action_profiles)
    raw = np.zeros((n_agents, type_count, type_count, profile_count), dtype=float)
    targets = np.array([float(persona.target_contribution) for persona in PERSONAS[:type_count]], dtype=float)
    cooperation = np.array([float(persona.cooperation_weight) for persona in PERSONAS[:type_count]], dtype=float)
    sensitivity = 0.75 + 0.25 * (cooperation / max(float(np.max(cooperation)), 1e-12))
    for agent in range(n_agents):
        own_actions = action_profiles[:, agent]
        for own_type in range(type_count):
            for partner_type in range(type_count):
                fit_to_partner = 1.0 - np.abs(own_actions - targets[partner_type])
                raw[agent, own_type, partner_type] = sensitivity[own_type] * fit_to_partner
    return raw


def raw_random(shape: tuple[int, ...], seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(0.0, 1.0, size=shape)


def raw_sparse(shape: tuple[int, ...], seed: int, density: float = 0.1) -> np.ndarray:
    rng = np.random.default_rng(seed)
    mask = rng.random(size=shape) < density
    values = rng.normal(0.0, 1.0, size=shape)
    return values * mask


def build_coupling_variants(base: np.ndarray, action_profiles: np.ndarray) -> dict[str, tuple[np.ndarray, dict[str, object]]]:
    raw_match = raw_type_match(action_profiles, base.shape[1])
    variants: dict[str, tuple[np.ndarray, dict[str, object]]] = {}
    for name, raw, extra in [
        ("C_match", raw_match, {"description": "type-match coordination term"}),
        ("C_random", raw_random(raw_match.shape, RANDOM_SEED), {"description": "Gaussian random coupling", "seed": RANDOM_SEED}),
        ("C_adversarial", -raw_match, {"description": "negative type-match / type-mismatch coupling"}),
        ("C_sparse", raw_sparse(raw_match.shape, SPARSE_SEED), {"description": "10% sparse Gaussian coupling", "seed": SPARSE_SEED, "density": 0.1}),
    ]:
        coupling, stats = center_and_scale(raw, base)
        if not np.allclose(build_coupled_tensor(base, coupling, 0.0)[:, :, 0, :], base):
            raise AssertionError(f"{name}: lambda=0 collapse failed")
        if float(np.max(np.abs(coupling.mean(axis=2)))) > 1e-10:
            raise AssertionError(f"{name}: theta_j centering failed")
        if not np.isclose(coupling.std(), base.std(), rtol=1e-10, atol=1e-12):
            raise AssertionError(f"{name}: scaling to base std failed")
        variants[name] = (coupling, {**extra, **stats})
    return variants


def no_comm_error(base: np.ndarray, action_profiles: np.ndarray, actions: np.ndarray, coupling: np.ndarray, lam: float) -> float:
    model = make_coupled_model(
        base,
        action_profiles,
        actions,
        coupling,
        lam,
        identifiability=0.35,
        comm_cost=0.15,
    )
    policy = RealMessagePolicy("NO_COMM", np.zeros((2, base.shape[1]), dtype=bool))
    return float(abs(decoupled_closed_form_value(model, policy) - exact_value(model, policy)))


def run() -> dict[str, object]:
    lam_grid = parse_lam_grid(DEFAULT_LAM_GRID)
    table_rows = []
    curve_rows = []
    coupling_summaries = []
    for judge in JUDGES:
        base, action_profiles, actions = load_base(judge.calibration)
        variants = build_coupling_variants(base, action_profiles)
        for coupling_name, (coupling, stats) in variants.items():
            errors = [no_comm_error(base, action_profiles, actions, coupling, lam) for lam in lam_grid]
            errors_by_lam = {f"{lam:.2f}": err for lam, err in zip(lam_grid, errors, strict=True)}
            monotone_0_1 = is_non_decreasing([err for lam, err in zip(lam_grid, errors, strict=True) if lam <= 1.0 + 1e-12])
            row = {
                "base_tensor": judge.name,
                "coupling": coupling_name,
                "lambda_0_error": errors_by_lam["0.00"],
                "lambda_0_5_error": errors_by_lam["0.50"],
                "lambda_1_0_error": errors_by_lam["1.00"],
                "lambda_2_0_error": errors_by_lam["2.00"],
                "error_monotone_on_0_1": bool(monotone_0_1),
            }
            table_rows.append(row)
            coupling_summaries.append({"base_tensor": judge.name, "coupling": coupling_name, "stats": stats})
            for lam, error in zip(lam_grid, errors, strict=True):
                curve_rows.append({"base_tensor": judge.name, "coupling": coupling_name, "lambda_couple": lam, "abs_error": error})
    return {
        "setting": {
            "diagnostic_policy": "NO_COMM",
            "lambda_grid": lam_grid,
            "identifiability": 0.35,
            "comm_cost": 0.15,
            "invariants": [
                "All couplings are centered along theta_j.",
                "All couplings are scaled to the corresponding R_base standard deviation.",
                "lambda=0 collapses to R_base for every coupling variant.",
            ],
        },
        "all_variants_monotone_on_0_1": all(row["error_monotone_on_0_1"] for row in table_rows),
        "table_rows": table_rows,
        "curve_rows": curve_rows,
        "coupling_summaries": coupling_summaries,
    }


def main() -> None:
    payload = run()
    out_path = ANALYSIS_DIR / "lambda_couple_variant_summary.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(out_path.relative_to(ROOT)), "all_variants_monotone_on_0_1": payload["all_variants_monotone_on_0_1"]}, indent=2))
    print("base_tensor,coupling,lambda_0_error,lambda_0_5_error,lambda_1_0_error,lambda_2_0_error,error_monotone_on_0_1")
    for row in payload["table_rows"]:
        print(
            f"{row['base_tensor']},{row['coupling']},{row['lambda_0_error']:.6g},"
            f"{row['lambda_0_5_error']:.6g},{row['lambda_1_0_error']:.6g},{row['lambda_2_0_error']:.6g},"
            f"{row['error_monotone_on_0_1']}"
        )


if __name__ == "__main__":
    main()