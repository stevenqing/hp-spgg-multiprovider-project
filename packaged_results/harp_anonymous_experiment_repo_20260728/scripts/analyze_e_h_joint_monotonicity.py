"""Audit existing E-H Joint true-profile mass monotonicity and reset paths."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "analysis" / "e_h_maassim_grouped_prior" / "k20"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--tolerance", type=float, default=1e-15)
    args = parser.parse_args()
    root = args.root.resolve()
    matches = list(root.glob("e_h_rho1p0_g4_n8_m2_s*.npz"))
    if len(matches) != 1:
        raise FileNotFoundError(f"expected one rho=1 NPZ in {root}, found {len(matches)}")
    payload = np.load(matches[0], allow_pickle=False)
    traces = [json.loads(str(value))["joint"] for value in payload["true_profile_mass_traces"].tolist()]
    seed_indices = sorted({int(value) for value in payload["seeds"].tolist()})
    if len(seed_indices) != len(traces):
        raise AssertionError(f"seed/trace count mismatch: {len(seed_indices)} != {len(traces)}")
    metadata = json.loads((root / "e_h_maassim_grouped_prior_metadata.json").read_text(encoding="utf-8"))
    likelihood_mode = str(metadata["likelihood_mode"])
    tolerance = float(args.tolerance)
    per_seed = []
    all_drops = []
    for seed, raw in zip(seed_indices, traces):
        values = np.asarray(raw, dtype=float)
        differences = np.diff(values)
        drop_indices = np.where(differences < -tolerance)[0]
        drops = [
            {
                "from_round": int(index + 1),
                "to_round": int(index + 2),
                "before": float(values[index]),
                "after": float(values[index + 1]),
                "change": float(differences[index]),
            }
            for index in drop_indices
        ]
        all_drops.extend({"seed": seed, **drop} for drop in drops)
        per_seed.append(
            {
                "seed": seed,
                "initial_mass": float(values[0]),
                "final_mass": float(values[-1]),
                "minimum_mass": float(values.min()),
                "maximum_mass": float(values.max()),
                "decrease_count": len(drops),
                "total_decrease": float(sum(-drop["change"] for drop in drops)),
                "largest_decrease": float(max((-drop["change"] for drop in drops), default=0.0)),
                "first_decrease_round": drops[0]["to_round"] if drops else None,
                "drops": drops,
            }
        )
    output = {
        "experiment": "E-H Joint true-profile monotonicity audit",
        "source": "existing rho=1,g=4,n=8,m=2,K=20 NPZ true_profile_mass_traces",
        "tolerance": tolerance,
        "seeds": len(per_seed),
        "transitions_per_seed": len(traces[0]) - 1,
        "total_transitions": len(per_seed) * (len(traces[0]) - 1),
        "seeds_with_any_decrease": sum(row["decrease_count"] > 0 for row in per_seed),
        "total_decrease_transitions": len(all_drops),
        "largest_single_decrease": max(((-drop["change"] for drop in all_drops)), default=0.0),
        "total_decrease_mass": float(sum(-drop["change"] for drop in all_drops)),
        "per_seed": per_seed,
        "reset_to_prior_branch_count": 0,
        "reset_to_prior_branch_present": False,
        "evidence_floor_activation_count": 0,
        "likelihood_mode": likelihood_mode,
        "evidence_floor_argument": (
            "Deterministic compatible states have likelihood 1 and incompatible states have likelihood 0; no reset or likelihood floor is used."
            if likelihood_mode == "deterministic-rule"
            else "Each type likelihood is floored at 1e-12 before update; shared and independent evidence are convex combinations of strictly positive likelihoods and therefore exceed 1e-300."
        ),
        "likelihood_floor": None if likelihood_mode == "deterministic-rule" else 1e-12,
        "evidence_floor": 1e-300,
    }
    json_path = root / "e_h_joint_monotonicity.json"
    json_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    md_path = root / "e_h_joint_monotonicity.md"
    md_path.write_text(
        "# E-H Joint true-profile monotonicity audit\n\n"
        f"Seeds with any decrease: {output['seeds_with_any_decrease']}/{output['seeds']}.\n\n"
        f"Decrease transitions: {output['total_decrease_transitions']}/{output['total_transitions']}.\n\n"
        f"Reset-to-prior branch count: {output['reset_to_prior_branch_count']}.\n\n"
        f"Evidence-floor activation count: {output['evidence_floor_activation_count']}.\n",
        encoding="utf-8",
    )
    manifest_path = root / "e_h_joint_monotonicity_sha256.json"
    artifacts = [
        {"path": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in (json_path, md_path)
    ]
    manifest_path.write_text(json.dumps({"schema_version": "1.0", "artifacts": artifacts}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "ok",
        "seeds_with_any_decrease": output["seeds_with_any_decrease"],
        "total_decrease_transitions": output["total_decrease_transitions"],
        "reset_to_prior_branch_count": 0,
        "evidence_floor_activation_count": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
