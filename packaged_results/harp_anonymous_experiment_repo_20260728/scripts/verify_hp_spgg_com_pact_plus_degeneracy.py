"""Verify the PACT+ / Mode-2 T=1 action-space degeneration.

The strict equality claim needs one normalization detail. In the binary
one-step action-space case, PACT+'s pairwise type-disagreement bonus is a
belief-dependent constant multiple of the Mode-2 myopic value of information.
The constant is independent of the candidate action, so the criteria induce the
same action ranking. They are numerically equal at the uniform prior.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_hpgg_com.hp_spgg_com import (  # noqa: E402
    mode2_binary_myopic_voi,
    pact_plus_binary_disagreement_bonus,
    pact_plus_mode2_scale,
)


OUT_DIR = ROOT / "analysis" / "hp_spgg_com"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    probs = [0.1, 0.25, 0.5, 0.75, 0.9]
    gaps = [0.0, 0.1, 0.25, 0.5, 1.0]
    rows = []
    max_normalized_error = 0.0
    max_uniform_error = 0.0
    ranking_ok = True
    for prob in probs:
        scale = pact_plus_mode2_scale(prob)
        mode2_values = []
        pact_values = []
        for gap in gaps:
            mode2 = mode2_binary_myopic_voi(prob, gap)
            pact = pact_plus_binary_disagreement_bonus(prob, gap)
            normalized_pact = pact / scale if scale > 0 else pact
            error = abs(normalized_pact - mode2)
            max_normalized_error = max(max_normalized_error, error)
            if abs(prob - 0.5) < 1e-12:
                max_uniform_error = max(max_uniform_error, abs(pact - mode2))
            mode2_values.append(mode2)
            pact_values.append(pact)
            rows.append(
                {
                    "prob_type1": prob,
                    "reward_gap": gap,
                    "mode2_myopic_voi": mode2,
                    "pact_plus_disagreement_bonus": pact,
                    "belief_scale": scale,
                    "normalized_pact_bonus": normalized_pact,
                    "normalized_abs_error": error,
                }
            )
        mode2_order = sorted(range(len(gaps)), key=lambda idx: mode2_values[idx])
        pact_order = sorted(range(len(gaps)), key=lambda idx: pact_values[idx])
        ranking_ok = ranking_ok and (mode2_order == pact_order)

    payload = {
        "claim": (
            "For binary types in the T=1 action-space case, PACT+'s pairwise "
            "type-discrimination bonus is a belief-dependent constant multiple "
            "of the Mode-2 myopic value-of-information criterion. The constant "
            "is independent of the candidate action, so rankings coincide; at "
            "uniform prior p=0.5 the two quantities are numerically equal."
        ),
        "max_normalized_error": max_normalized_error,
        "max_uniform_prior_unscaled_error": max_uniform_error,
        "ranking_identical_for_tested_grid": ranking_ok,
        "rows": rows,
    }
    out = OUT_DIR / "pact_plus_mode2_degeneracy.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"OK: {out}")
    print(f"max_normalized_error={max_normalized_error:.3g}")
    print(f"max_uniform_prior_unscaled_error={max_uniform_error:.3g}")
    print(f"ranking_identical_for_tested_grid={ranking_ok}")


if __name__ == "__main__":
    main()