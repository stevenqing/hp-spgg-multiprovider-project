"""Audit E-H Joint likelihood consistency, prior support, and batch/incremental updates."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "analysis" / "e_h_maassim_grouped_prior" / "k20"
SOURCE_ROOT = ROOT / "analysis" / "e_e_maassim_rq2"

from llm_courier_dispatch.dispatch_env import ACCEPT, CourierDispatchEnv, state_from_dict
from llm_courier_dispatch_maassim.hidden_rules import grouped_driver_types, synthetic_action_for_type
from scripts.run_e_e_maassim_tracker_parity import RULE_CONFIG, cell_paths, conflict_transform, legal_assignments, load_cell
from scripts.run_e_h_maassim_grouped_prior import GroupedJointTracker, selected_rounds, true_type_indices


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def raw_likelihood_vector(env: CourierDispatchEnv, features: dict[str, float | int], action: int) -> np.ndarray:
    state = state_from_dict(features)
    accepted = int(action) == ACCEPT
    values = []
    for theta in env.type_space:
        accept_probability = env.likelihood(ACCEPT, state, theta)
        values.append(accept_probability if accepted else 1.0 - accept_probability)
    return np.asarray(values, dtype=float)


def tracker_state_difference(left: GroupedJointTracker, right: GroupedJointTracker) -> dict[str, float]:
    return {
        "shared_probs_max_abs": float(np.max(np.abs(left.shared_probs - right.shared_probs))),
        "independent_probs_max_abs": float(np.max(np.abs(left.independent_probs - right.independent_probs))),
        "shared_weight_abs": abs(float(left.shared_weight) - float(right.shared_weight)),
        "marginals_max_abs": float(np.max(np.abs(left.marginals() - right.marginals()))),
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--tolerance", type=float, default=1e-13)
    args = parser.parse_args()
    root = args.root.resolve()
    npz = np.load(root / "e_h_rho1p0_g4_n8_m2_s20.npz", allow_pickle=False)
    stored_mass = [json.loads(str(value))["joint"] for value in npz["true_profile_mass_traces"].tolist()]
    strength = float(npz["strength"])
    tolerance = float(args.tolerance)

    true_likelihoods = []
    events = []
    initial_masses = []
    support_checks = []
    batch_differences = []
    stored_trace_differences = []
    evidence_floor_count = 0
    reset_count = 0

    for seed in range(20):
        snapshots, driver_source, _, _ = load_cell(cell_paths(SOURCE_ROOT, 8, seed), seed, 8)
        driver_ids = sorted(driver_source.true_types)
        env = CourierDispatchEnv(n_agents=1, rule_count=4, horizon=1, seed=seed)
        true_types = grouped_driver_types(driver_ids, seed=seed, rho=1.0, group_size=4, type_space=env.type_space)
        driver_source.true_types = true_types
        true_profile = np.asarray([true_types[driver_id] for driver_id in driver_ids], dtype=int)
        true_indices = true_type_indices(env.type_space, true_profile)
        groups = [driver_ids[:4], driver_ids[4:]]
        support_ok = all(len({true_types[driver_id] for driver_id in group}) == 1 for group in groups)
        support_checks.append(support_ok)
        incremental = GroupedJointTracker(driver_ids, env.type_space, rho=1.0, group_size=4)
        initial_mass = incremental.true_profile_mass(true_profile)
        initial_masses.append(initial_mass)
        history = []
        rounds = [conflict_transform(snapshot, strength) for snapshot in selected_rounds(snapshots, 20, 2)]
        for round_index, snapshot in enumerate(rounds):
            stored_difference = abs(float(stored_mass[seed][round_index]) - incremental.true_profile_mass(true_profile))
            stored_trace_differences.append(stored_difference)
            elicitation = legal_assignments(snapshot)[0]
            offer_by_pair = {(int(offer.driver_id), int(offer.request_id)): offer for offer in snapshot.candidates}
            for event_index, (driver_id, request_id) in enumerate(elicitation):
                offer = offer_by_pair[(driver_id, request_id)]
                action, _ = synthetic_action_for_type(true_types[driver_id], offer, RULE_CONFIG)
                features = driver_source.features_for_offer(offer)
                raw = raw_likelihood_vector(env, features, action)
                true_likelihood = float(raw[true_indices[incremental.driver_index[driver_id]]])
                floor_hit = true_likelihood <= 1e-12
                true_likelihoods.append(true_likelihood)
                events.append({
                    "seed": seed,
                    "round": round_index + 1,
                    "event_in_round": event_index + 1,
                    "driver_id": driver_id,
                    "request_id": request_id,
                    "action": int(action),
                    "true_likelihood": true_likelihood,
                    "floor_hit": floor_hit,
                    "true_is_max_likelihood": true_likelihood >= float(raw.max()) - 1e-15,
                    "true_likelihood_rank": int(1 + np.sum(raw > true_likelihood + 1e-15)),
                    "max_likelihood": float(raw.max()),
                })
                floored = np.maximum(raw, 1e-12)
                log_likelihood = np.log(floored)
                before_weight = incremental.shared_weight
                incremental.update(driver_id, log_likelihood)
                if before_weight > 0.0 and incremental.shared_weight == 0.0:
                    reset_count += 1
                history.append((driver_id, log_likelihood.copy()))
                batch = GroupedJointTracker(driver_ids, env.type_space, rho=1.0, group_size=4)
                for old_driver, old_log_likelihood in history:
                    batch.update(old_driver, old_log_likelihood)
                difference = tracker_state_difference(incremental, batch)
                difference.update({"seed": seed, "round": round_index + 1, "history_events": len(history)})
                batch_differences.append(difference)
                if floor_hit:
                    evidence_floor_count += 1

    likelihood_array = np.asarray(true_likelihoods, dtype=float)
    output = {
        "experiment": "E-H Joint update correctness audit",
        "source": "existing rho=1,g=4,n=8,m=2,K=20 snapshots and stored true-profile traces",
        "events": len(events),
        "true_type_likelihood": {
            "floor": 1e-12,
            "floor_hit_count": int(np.sum(likelihood_array <= 1e-12)),
            "minimum": float(likelihood_array.min()),
            "maximum": float(likelihood_array.max()),
            "mean": float(likelihood_array.mean()),
            "true_is_max_count": sum(bool(event["true_is_max_likelihood"]) for event in events),
            "true_not_max_count": sum(not bool(event["true_is_max_likelihood"]) for event in events),
            "rank_counts": {str(rank): sum(event["true_likelihood_rank"] == rank for event in events) for rank in sorted({event["true_likelihood_rank"] for event in events})},
        },
        "initial_true_profile_mass": {
            "expected": 1.0 / 256.0,
            "minimum": min(initial_masses),
            "maximum": max(initial_masses),
            "max_abs_error": max(abs(value - 1.0 / 256.0) for value in initial_masses),
            "exact_count": sum(value == 1.0 / 256.0 for value in initial_masses),
            "support_consistent_seed_count": sum(support_checks),
        },
        "batch_vs_incremental": {
            "checkpoints": len(batch_differences),
            "shared_probs_max_abs": max(item["shared_probs_max_abs"] for item in batch_differences),
            "independent_probs_max_abs": max(item["independent_probs_max_abs"] for item in batch_differences),
            "shared_weight_max_abs": max(item["shared_weight_abs"] for item in batch_differences),
            "marginals_max_abs": max(item["marginals_max_abs"] for item in batch_differences),
            "all_within_tolerance": all(max(item[key] for key in ("shared_probs_max_abs", "independent_probs_max_abs", "shared_weight_abs", "marginals_max_abs")) <= tolerance for item in batch_differences),
            "tolerance": tolerance,
        },
        "stored_trace_vs_recomputed_incremental": {
            "checkpoints": len(stored_trace_differences),
            "max_abs_true_profile_mass_difference": max(stored_trace_differences),
            "all_within_tolerance": max(stored_trace_differences) <= tolerance,
        },
        "reset_to_prior_branch_present": False,
        "reset_to_prior_trigger_count": reset_count,
        "evidence_floor_trigger_count": evidence_floor_count,
        "events_detail": events,
    }
    json_path = root / "e_h_joint_update_audit.json"
    json_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    md_path = root / "e_h_joint_update_audit.md"
    md_path.write_text(
        "# E-H Joint update correctness audit\n\n"
        f"True-type likelihood floor hits: {output['true_type_likelihood']['floor_hit_count']}/{output['events']}.\n\n"
        f"Initial mass exact: {output['initial_true_profile_mass']['exact_count']}/20.\n\n"
        f"Batch/incremental max marginal difference: {output['batch_vs_incremental']['marginals_max_abs']:.3e}.\n\n"
        f"Reset trigger count: {output['reset_to_prior_trigger_count']}.\n",
        encoding="utf-8",
    )
    manifest_path = root / "e_h_joint_update_audit_sha256.json"
    artifacts = [{"path": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)} for path in (json_path, md_path)]
    manifest_path.write_text(json.dumps({"schema_version": "1.0", "artifacts": artifacts}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "ok",
        "events": output["events"],
        "floor_hits": output["true_type_likelihood"]["floor_hit_count"],
        "initial_exact": output["initial_true_profile_mass"]["exact_count"],
        "batch_incremental_match": output["batch_vs_incremental"]["all_within_tolerance"],
        "reset_triggers": output["reset_to_prior_trigger_count"],
    }, indent=2))


if __name__ == "__main__":
    main()
