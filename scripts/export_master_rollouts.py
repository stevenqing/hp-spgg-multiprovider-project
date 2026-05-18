"""Export HP-SPGG (+Concordia) K=20 rollouts to the 4 schemas the figures pipeline expects.

Produces under analysis/exports/:
  master_rollouts.jsonl              -- one row per (method, backbone, substrate, seed, episode_k)
  posterior_entropy.csv              -- schema 1
  posterior_kl.csv                   -- schema 2
  beta_ablation.csv                  -- schema 3
  cum_payoff_trajectories.csv        -- schema 4
  EXPORT_COVERAGE.md                 -- what was found / what is missing

Conventions:
  - backbone = LLM model name (DeepSeek-V3.2, GPT-5.4-nano, Kimi-K2.6, Llama-Maverick) for LLM
    methods; "mechanistic" for numeric agents (hpsmg_plus, hpsmg, joint_psrl, oracle, ...).
  - substrate = "hpspgg_c{N}" for HP-SPGG profile index N, or Concordia substrate codename.
  - episode_k = 1..K (1-indexed).
  - theta_star reconstructed from seed via the same rng used in run_llm_baselines.py
    (np.random.default_rng(seed).integers(0, type_count, size=n) -- deterministic).
  - posterior (LLM): empirical distribution over PERSONAS derived by matching the
    LLM's inferred_personas string(s) against persona labels (best-effort token match).
    Each round produces ONE posterior vector per agent. When the LLM returns a flat
    list of n labels, agent i gets a (1-epsilon)/epsilon one-hot at the matched label;
    when text is unparseable, posterior is uniform (entropy = log |Theta|).
  - posterior_entropy = H(posterior) in nats.
  - kl_to_truth = -log(posterior[theta_star]) in nats.
"""
from __future__ import annotations

import csv
import glob
import json
import math
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from llm_hpgg.personas import PERSONAS  # noqa: E402

PERSONA_LABELS = [p.label for p in PERSONAS]
PERSONA_KEYS = [p.key for p in PERSONAS]
PERSONA_LOOKUP: list[tuple[int, list[str]]] = []
for idx, p in enumerate(PERSONAS):
    keys = {p.key.lower(), p.label.lower()}
    # add tokens like "altruistic", "free rider", "free-rider"
    for tok in [p.label.lower(), p.key.lower().replace("_", " "), p.key.lower().replace("_", "-")]:
        keys.add(tok)
    PERSONA_LOOKUP.append((idx, sorted(keys, key=len, reverse=True)))

N_PERSONAS = len(PERSONAS)
LOG_N = math.log(N_PERSONAS)
EPS_ONE_HOT = 0.05  # mass kept on non-matched personas to avoid -inf KL on misses

OUT_DIR = ROOT / "analysis" / "exports"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BACKBONE_NAMES = {
    "DeepSeek_V3_2": "DeepSeek-V3.2",
    "DeepSeek-V3.2": "DeepSeek-V3.2",
    "Kimi_K2_6": "Kimi-K2.6",
    "Kimi-K2.6": "Kimi-K2.6",
    "Llama_4_Maverick_17B_128E_Instruct_FP8": "Llama-Maverick",
    "Llama-4-Maverick-17B-128E-Instruct-FP8": "Llama-Maverick",
    "gpt_5_4_nano_20260317": "GPT-5.4-nano",
    "gpt-5.4-nano-20260317": "GPT-5.4-nano",
    "gpt_5_5_20260424": "GPT-5.5",
    "gpt-5.5-20260424": "GPT-5.5",
}


def norm_backbone(name: str) -> str:
    return BACKBONE_NAMES.get(name, name)


# ---------------------------------------------------------------------------
# theta_star reconstruction (matches run_llm_baselines.run_episode)
# ---------------------------------------------------------------------------

DEFAULT_SEEDS_BY_INDEX = [90000, 90001, 90002, 90003, 90004]  # seen in trace seed_index→seed


def true_types_for(seed: int, n: int = 3, type_count: int = N_PERSONAS) -> list[int]:
    rng = np.random.default_rng(seed)
    return [int(x) for x in rng.integers(0, type_count, size=n)]


# ---------------------------------------------------------------------------
# Inferred-persona text parser
# ---------------------------------------------------------------------------

def parse_persona_text(value: Any) -> int | None:
    """Map a free-text persona description to a persona index (0..3) or None."""
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        # nested -- caller should iterate; treat first element here for fallback
        return None
    s = str(value).strip().lower()
    if not s:
        return None
    # leading "0:" / "1:" / etc.
    m = re.match(r"^\s*([0-3])\s*[:\.\-]", s)
    if m:
        return int(m.group(1))
    # token match -- longest first
    for idx, tokens in PERSONA_LOOKUP:
        for t in tokens:
            if t and t in s:
                return idx
    return None


def posterior_from_inferred(
    inferred: Any, n_agents: int
) -> tuple[list[list[float]], list[bool]]:
    """Return one posterior per agent + parseable flag.

    Posterior is a length-N_PERSONAS distribution; uniform if unparseable.
    """
    posteriors: list[list[float]] = []
    parsed_flags: list[bool] = []
    items: list[Any]
    if isinstance(inferred, list):
        items = list(inferred)
    elif isinstance(inferred, dict):
        items = [inferred.get(str(i)) or inferred.get(i) for i in range(n_agents)]
    elif inferred is None:
        items = [None] * n_agents
    else:
        # single string referring to all agents (or summary text) -- try to parse once
        items = [inferred] * n_agents
    while len(items) < n_agents:
        items.append(None)
    items = items[:n_agents]
    for it in items:
        idx = parse_persona_text(it)
        if idx is None:
            posteriors.append([1.0 / N_PERSONAS] * N_PERSONAS)
            parsed_flags.append(False)
        else:
            v = [EPS_ONE_HOT / (N_PERSONAS - 1)] * N_PERSONAS
            v[idx] = 1.0 - EPS_ONE_HOT
            posteriors.append(v)
            parsed_flags.append(True)
    return posteriors, parsed_flags


def entropy_nats(p: list[float]) -> float:
    return -sum(x * math.log(x) for x in p if x > 0)


def kl_to_point(p: list[float], theta_star: int) -> float:
    px = p[theta_star] if 0 <= theta_star < len(p) else 1e-12
    return -math.log(max(px, 1e-12))


# ---------------------------------------------------------------------------
# LLM trace ingestion
# ---------------------------------------------------------------------------

TRACE_PATTERNS = [
    ("analysis/E2_llm_baselines_{m}_c19_K20_s5_trace.json", "internal"),
    ("analysis/E2_external_llm_baselines_{m}_c19_K20_s5_trace.json", "external"),
]

MODELS_FOR_TRACE = ["DeepSeek_V3_2", "Kimi_K2_6", "Llama_4_Maverick_17B_128E_Instruct_FP8", "gpt_5_4_nano_20260317"]


def iter_llm_trace_rows() -> Iterable[dict[str, Any]]:
    """Yield per-(method, backbone, substrate, seed, episode_k, agent_idx) records."""
    substrate = "hpspgg_c19"  # all current LLM traces are calibration c19
    for model in MODELS_FOR_TRACE:
        for pat, _kind in TRACE_PATTERNS:
            path = ROOT / pat.format(m=model)
            if not path.exists():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                print(f"[warn] failed to read {path}: {exc}", file=sys.stderr)
                continue
            if not isinstance(data, list):
                continue
            for entry in data:
                algo = entry.get("algorithm")
                seed = entry.get("seed")
                trace = entry.get("trace") or []
                if seed is None or not trace:
                    continue
                n_agents = len(trace[0].get("contributions") or []) or 3
                thetas = true_types_for(int(seed), n=n_agents)
                cum = 0.0
                for round_idx, ev in enumerate(trace):
                    welfare = float(ev.get("welfare", 0.0))
                    cum += welfare
                    parsed = ev.get("parsed") or {}
                    posts, flags = posterior_from_inferred(parsed.get("inferred_personas"), n_agents)
                    yield {
                        "method": algo,
                        "backbone": norm_backbone(model),
                        "substrate": substrate,
                        "seed": int(seed),
                        "episode_k": int(ev.get("round", round_idx)) + 1,
                        "beta": None,
                        "episode_payoff": welfare,
                        "cum_payoff": cum,
                        "oracle_welfare": float(ev.get("oracle_welfare", 0.0)),
                        "contributions": list(ev.get("contributions") or []),
                        "rewards": list(ev.get("rewards") or []),
                        "per_agent": [
                            {
                                "agent_idx": i,
                                "theta_star": thetas[i],
                                "posterior": posts[i],
                                "posterior_parsed": flags[i],
                                "posterior_entropy": entropy_nats(posts[i]),
                                "kl_to_truth": kl_to_point(posts[i], thetas[i]),
                            }
                            for i in range(n_agents)
                        ],
                    }


# ---------------------------------------------------------------------------
# Numeric agent npz ingestion (for beta-ablation + overtake)
# ---------------------------------------------------------------------------

BETA_TOKEN = {"0": 0.0, "0p05": 0.05, "0p1": 0.1, "0p25": 0.25, "0p5": 0.5,
              "0p75": 0.75, "1": 1.0, "1p5": 1.5}


def iter_numeric_rows() -> Iterable[dict[str, Any]]:
    """Yield numeric-agent K=20 trajectories for each (model, profile, beta, algo, seed)."""
    pat = re.compile(r"E2_(.+?)_c(\d+)_beta(.+?)\.npz$")
    paths = sorted(glob.glob(str(ROOT / "results" / "cloudgpt" / "E2_*_c*_beta*.npz")))
    for p in paths:
        name = os.path.basename(p)
        m = pat.match(name)
        if not m:
            continue
        model, c, btok = m.group(1), int(m.group(2)), m.group(3)
        if model.startswith("8algos_"):
            continue
        if btok not in BETA_TOKEN:
            continue
        beta = BETA_TOKEN[btok]
        try:
            d = np.load(p, allow_pickle=True)
            algos = [str(a) for a in d["algorithms"]]
            welfare = d["welfare"]  # (algo, seed, K)
            K = int(d["K"].item())
            n_seeds = int(d["seeds"].item())
        except Exception as exc:
            print(f"[warn] failed npz {p}: {exc}", file=sys.stderr)
            continue
        for ai, algo in enumerate(algos):
            for s in range(n_seeds):
                cum = 0.0
                for k in range(K):
                    w = float(welfare[ai, s, k])
                    cum += w
                    yield {
                        "method": algo,
                        "backbone": norm_backbone(model),
                        "substrate": f"hpspgg_c{c}",
                        "seed": s,
                        "episode_k": k + 1,
                        "beta": beta,
                        "episode_payoff": w,
                        "cum_payoff": cum,
                        "per_agent": None,  # numeric runs don't log per-agent posteriors
                    }


# ---------------------------------------------------------------------------
# Concordia compact ingestion (single-shot -> episode_k=1)
# ---------------------------------------------------------------------------

def iter_concordia_rows() -> Iterable[dict[str, Any]]:
    paths = sorted(
        list(glob.glob(str(ROOT / "analysis" / "concordia_pub_coordination_compact_*.json")))
        + list(glob.glob(str(ROOT / "analysis" / "concordia_haggling_compact_*.json")))
        + list(glob.glob(str(ROOT / "analysis" / "concordia_haggling_multi_item_compact_*.json")))
    )
    for p in paths:
        name = os.path.basename(p)
        try:
            data = json.loads(Path(p).read_text(encoding="utf-8"))
        except Exception:
            continue
        if "episodes" not in data:
            continue
        # derive a substrate codename
        if "haggling_multi_item_compact_" in name:
            substrate = "haggling_multi_" + name.split("haggling_multi_item_compact_")[1].rsplit("_s", 1)[0].rsplit("_smoke", 1)[0]
        elif "haggling_compact_" in name:
            substrate = "haggling_" + name.split("haggling_compact_")[1].rsplit("_s", 1)[0].rsplit("_smoke", 1)[0]
        else:
            substrate = name.split("compact_")[1].rsplit("_s", 1)[0].rsplit(".json", 1)[0]
        # model
        model = data.get("model") or "mechanistic"
        backbone = norm_backbone(model) if model and model not in ("none", "offline", "mechanistic") else "mechanistic"
        for ep in data["episodes"]:
            method = ep.get("method")
            seed = ep.get("seed")
            score = ep.get("focal_score_mean")
            if seed is None or score is None:
                continue
            yield {
                "method": method,
                "backbone": backbone,
                "substrate": substrate,
                "seed": int(seed),
                "episode_k": 1,
                "beta": None,
                "episode_payoff": float(score),
                "cum_payoff": float(score),
                "per_agent": None,
                "coordination_rate": ep.get("coordination_rate"),
                "valid_action_rate": ep.get("valid_action_rate"),
            }


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def write_master_and_csvs() -> dict[str, int]:
    master_path = OUT_DIR / "master_rollouts.jsonl"
    ent_path = OUT_DIR / "posterior_entropy.csv"
    kl_path = OUT_DIR / "posterior_kl.csv"
    beta_path = OUT_DIR / "beta_ablation.csv"
    cum_path = OUT_DIR / "cum_payoff_trajectories.csv"
    counts: dict[str, int] = defaultdict(int)
    with master_path.open("w", encoding="utf-8") as fmaster, \
         ent_path.open("w", newline="", encoding="utf-8") as fent, \
         kl_path.open("w", newline="", encoding="utf-8") as fkl, \
         beta_path.open("w", newline="", encoding="utf-8") as fbeta, \
         cum_path.open("w", newline="", encoding="utf-8") as fcum:
        ent_writer = csv.DictWriter(fent, fieldnames=["backbone", "substrate", "method", "seed", "agent_idx", "episode_k", "posterior_entropy", "posterior_parsed", "theta_space_size"])
        ent_writer.writeheader()
        kl_writer = csv.DictWriter(fkl, fieldnames=["method", "backbone", "substrate", "seed", "agent_idx", "episode_k", "theta_star", "kl_to_truth", "posterior_parsed"])
        kl_writer.writeheader()
        beta_writer = csv.DictWriter(fbeta, fieldnames=["beta", "backbone", "substrate", "method", "seed", "episode_k", "episode_payoff", "cum_payoff"])
        beta_writer.writeheader()
        cum_writer = csv.DictWriter(fcum, fieldnames=["method", "backbone", "substrate", "seed", "episode_k", "episode_payoff", "cum_payoff", "beta"])
        cum_writer.writeheader()

        def dump(row: dict[str, Any]) -> None:
            fmaster.write(json.dumps(row, ensure_ascii=False) + "\n")
            counts["master"] += 1
            # entropy / KL rows
            if row.get("per_agent"):
                for pa in row["per_agent"]:
                    ent_writer.writerow({
                        "backbone": row["backbone"],
                        "substrate": row["substrate"],
                        "method": row["method"],
                        "seed": row["seed"],
                        "agent_idx": pa["agent_idx"],
                        "episode_k": row["episode_k"],
                        "posterior_entropy": f"{pa['posterior_entropy']:.6f}",
                        "posterior_parsed": int(bool(pa.get("posterior_parsed", False))),
                        "theta_space_size": N_PERSONAS,
                    })
                    counts["entropy"] += 1
                    kl_writer.writerow({
                        "method": row["method"],
                        "backbone": row["backbone"],
                        "substrate": row["substrate"],
                        "seed": row["seed"],
                        "agent_idx": pa["agent_idx"],
                        "episode_k": row["episode_k"],
                        "theta_star": pa["theta_star"],
                        "kl_to_truth": f"{pa['kl_to_truth']:.6f}",
                        "posterior_parsed": int(bool(pa.get("posterior_parsed", False))),
                    })
                    counts["kl"] += 1
            # cum payoff trajectory
            cum_writer.writerow({
                "method": row["method"],
                "backbone": row["backbone"],
                "substrate": row["substrate"],
                "seed": row["seed"],
                "episode_k": row["episode_k"],
                "episode_payoff": f"{row['episode_payoff']:.6f}",
                "cum_payoff": f"{row['cum_payoff']:.6f}",
                "beta": row.get("beta"),
            })
            counts["cum"] += 1
            # beta ablation row -- only when beta is set
            if row.get("beta") is not None:
                beta_writer.writerow({
                    "beta": row["beta"],
                    "backbone": row["backbone"],
                    "substrate": row["substrate"],
                    "method": row["method"],
                    "seed": row["seed"],
                    "episode_k": row["episode_k"],
                    "episode_payoff": f"{row['episode_payoff']:.6f}",
                    "cum_payoff": f"{row['cum_payoff']:.6f}",
                })
                counts["beta"] += 1

        for row in iter_llm_trace_rows():
            dump(row)
        for row in iter_numeric_rows():
            dump(row)
        for row in iter_concordia_rows():
            dump(row)
    return counts


def write_coverage_report(counts: dict[str, int]) -> None:
    lines = [
        "# Master rollout export — coverage report",
        "",
        f"Output directory: `{OUT_DIR.relative_to(ROOT).as_posix()}/`",
        "",
        "| file | rows | notes |",
        "|---|---|---|",
        f"| `master_rollouts.jsonl` | {counts['master']} | one row per (method, backbone, substrate, seed, episode_k) |",
        f"| `posterior_entropy.csv` | {counts['entropy']} | LLM trace methods only (numeric / Concordia rows do not log per-agent posteriors) |",
        f"| `posterior_kl.csv` | {counts['kl']} | KL to point-mass theta_star reconstructed from seed |",
        f"| `beta_ablation.csv` | {counts['beta']} | HP-SPGG numeric only — paired β ∈ {{0, 0.05, 0.1, 0.25, 0.5, 0.75, 1, 1.5}} |",
        f"| `cum_payoff_trajectories.csv` | {counts['cum']} | all sources — Concordia rows are episode_k=1 only |",
        "",
        "## Conventions",
        "",
        "- `backbone` ∈ {`DeepSeek-V3.2`, `GPT-5.4-nano`, `Kimi-K2.6`, `Llama-Maverick`} for LLM-driven runs.",
        "  Numeric/mechanistic methods use `backbone='mechanistic'`.",
        "- `method` is the algorithm name as logged (`hpsmg_plus`, `hpsmg`, `joint_psrl`, `oracle`,",
        "  `llm_greedy`, `llm_belief`, `atom_tom0/1/2`, `atom_adaptive_ftl`, `atom_adaptive_hedge`,",
        "  `econ_bne`, `hpsmg_plus_proxy`, `hpsmg_plus_joint_proxy`, `oracle_joint`, ...).",
        "- `substrate = hpspgg_c{N}` for HP-SPGG profile index N; Concordia substrates use their compact codenames",
        "  (e.g. `capetown_mechanistic_joint`, `haggling_fruitville`).",
        "- `episode_k` is 1-indexed.",
        "- `theta_star`: reconstructed via `np.random.default_rng(seed).integers(0, 4, size=n)` to match",
        "  `llm_hpgg/run_llm_baselines.py::run_episode`. Persona index order is",
        "  `[altruistic_builder, conditional_cooperator, risk_averse_balancer, free_rider]`.",
        "- `posterior` (LLM rows): empirical one-hot-with-smoothing distribution derived from the model's free-text",
        "  `inferred_personas` field. `posterior_parsed=0` rows are uniform fallbacks (entropy = log 4 ≈ 1.386 nats).",
        "  This is a *hard-label approximation* — to get true soft posteriors we would need to re-prompt the LLM",
        "  to return a distribution.",
        "- `beta`: only set for HP-SPGG numeric rows (the LLM agents don't take β as input).",
        "",
        "## Known gaps",
        "",
        "1. **LLM β-ablation is missing** — no LLM-driven β=0 vs β=0.25 paired runs. Schema 3 currently",
        "   exists only for numeric agents on `hpspgg_c{1..29}`. To extend, re-run",
        "   `llm_hpgg.run_llm_baselines` and `run_external_llm_baselines` with β=0 (currently β is implicit 0",
        "   in those wrappers — they don't expose β to the LLM, so the comparison is trivially identical).",
        "2. **Concordia compact runs are single-shot** (episode_k=1) — no within-substrate K=20 horizon and",
        "   no posterior dumps. Extending requires modifying `llm_hpgg_concordia/run_pub_coordination_compact.py`",
        "   and `run_haggling_compact.py` to (a) iterate K episodes per seed, (b) maintain a cross-episode",
        "   posterior in mechanistic methods, (c) dump it per episode.",
        "3. **Soft posteriors not available** — `inferred_personas` is free text. Hard-label approximation",
        "   in this export is best-effort: parser does longest-token match against persona keys/labels.",
        "",
    ]
    (OUT_DIR / "EXPORT_COVERAGE.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    counts = write_master_and_csvs()
    write_coverage_report(counts)
    print("Wrote to", OUT_DIR.relative_to(ROOT).as_posix())
    for k in ["master", "entropy", "kl", "beta", "cum"]:
        print(f"  {k}: {counts[k]} rows")


if __name__ == "__main__":
    main()
