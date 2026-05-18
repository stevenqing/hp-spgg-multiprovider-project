"""Create headline HP-SPGG tables and regret curves."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


@dataclass(frozen=True)
class ResultSource:
    path: Path
    label: str
    group: str


PREFERRED_ORDER = [
    "oracle",
    "hpsmg_plus",
    "map_greedy",
    "hpsmg",
    "joint_psrl",
    "atom_adaptive_hedge",
    "econ_bne",
    "llm_belief",
    "atom_tom0",
    "llm_greedy",
    "atom_tom2",
    "atom_adaptive_ftl",
    "atom_tom1",
    "psrl_notype",
    "random",
    "iql",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", required=True, help="Native .npz result file.")
    parser.add_argument("--llm", help="Prompted LLM baseline .npz result file.")
    parser.add_argument("--external", help="External A-ToM/ECON .npz result file.")
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-tex", required=True)
    parser.add_argument("--out-fig", required=True)
    parser.add_argument("--bootstrap", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260517)
    args = parser.parse_args()

    sources = [ResultSource(Path(args.native), "Native", "native")]
    if args.external:
        sources.append(ResultSource(Path(args.external), "External LLM", "external"))
    if args.llm:
        sources.append(ResultSource(Path(args.llm), "Prompted LLM", "prompted"))

    rows = []
    curves = []
    rng = np.random.default_rng(args.seed)
    for source in sources:
        source_rows, source_curves = summarize_source(source, args.bootstrap, rng)
        rows.extend(source_rows)
        curves.extend(source_curves)

    rows.sort(key=lambda row: (row["mean"], preferred_rank(row["algorithm"])))
    write_markdown(Path(args.out_md), rows, sources)
    write_latex(Path(args.out_tex), rows)
    write_figure(Path(args.out_fig), curves)
    print(f"summary_md={args.out_md}")
    print(f"table_tex={args.out_tex}")
    print(f"figure={args.out_fig}")


def summarize_source(source: ResultSource, bootstrap_count: int, rng: np.random.Generator) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    data = np.load(source.path, allow_pickle=True)
    algorithms = [str(value) for value in data["algorithms"]]
    cumulative = np.asarray(data["cumulative_regret"], dtype=float)
    regrets = np.asarray(data["regrets"], dtype=float)
    welfare = np.asarray(data["welfare"], dtype=float)
    rows = []
    curves = []
    for index, algorithm in enumerate(algorithms):
        if not include_algorithm(algorithm):
            continue
        final = cumulative[index, :, -1]
        lower, upper = bootstrap_ci(final, bootstrap_count, rng)
        q25, q75 = np.percentile(final, [25, 75])
        rows.append(
            {
                "group": source.label,
                "algorithm": algorithm,
                "K": int(data["K"]),
                "seeds": int(data["seeds"]),
                "mean": float(final.mean()),
                "std": float(final.std(ddof=0)),
                "median": float(np.median(final)),
                "q25": float(q25),
                "q75": float(q75),
                "ci_low": lower,
                "ci_high": upper,
                "per_round": float(regrets[index].mean()),
                "welfare": float(welfare[index].mean()),
                "source": source.path.as_posix(),
            }
        )
        curves.append(
            {
                "label": display_algorithm(algorithm),
                "algorithm": algorithm,
                "group": source.group,
                "mean": cumulative[index].mean(axis=0),
                "std": cumulative[index].std(axis=0, ddof=0),
                "seeds": int(data["seeds"]),
            }
        )
    return rows, curves


def include_algorithm(algorithm: str) -> bool:
    return algorithm in set(PREFERRED_ORDER)


def bootstrap_ci(values: np.ndarray, bootstrap_count: int, rng: np.random.Generator) -> tuple[float, float]:
    if values.size == 0:
        return float("nan"), float("nan")
    samples = rng.choice(values, size=(bootstrap_count, values.size), replace=True).mean(axis=1)
    lower, upper = np.percentile(samples, [2.5, 97.5])
    return float(lower), float(upper)


def preferred_rank(algorithm: str) -> int:
    try:
        return PREFERRED_ORDER.index(algorithm)
    except ValueError:
        return len(PREFERRED_ORDER)


def display_algorithm(algorithm: str) -> str:
    return algorithm.replace("_", "-")


def write_markdown(path: Path, rows: list[dict[str, object]], sources: list[ResultSource]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# HP-SPGG Headline Statistics", ""]
    lines.append("Sources:")
    for source in sources:
        lines.append(f"- {source.label}: `{source.path.as_posix()}`")
    lines.extend(
        [
            "",
            "| Rank | Group | Algorithm | K | Seeds | Mean | Std | Median | IQR | Bootstrap 95% CI | Per-round | Welfare |",
            "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: |",
        ]
    )
    for rank, row in enumerate(rows, start=1):
        lines.append(
            f"| {rank} | {row['group']} | `{row['algorithm']}` | {row['K']} | {row['seeds']} | "
            f"{row['mean']:.4f} | {row['std']:.4f} | {row['median']:.4f} | "
            f"[{row['q25']:.4f}, {row['q75']:.4f}] | "
            f"[{row['ci_low']:.4f}, {row['ci_high']:.4f}] | {row['per_round']:.4f} | {row['welfare']:.4f} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_latex(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row_end = r"\\"
    lines = [
        r"\begin{tabular}{llrrrrr}",
        r"\toprule",
        f"Group & Method & Seeds & Mean & Median & IQR & 95\\% CI {row_end}",
        r"\midrule",
    ]
    for row in rows:
        method = str(row["algorithm"]).replace("_", "\\_")
        lines.append(
            f"{row['group']} & {method} & {row['seeds']} & {row['mean']:.3f} & "
            f"{row['median']:.3f} & [{row['q25']:.3f}, {row['q75']:.3f}] & "
            f"[{row['ci_low']:.3f}, {row['ci_high']:.3f}] {row_end}"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_figure(path: Path, curves: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    selected = [curve for curve in curves if curve["algorithm"] in {"oracle", "hpsmg_plus", "map_greedy", "joint_psrl", "atom_adaptive_hedge", "econ_bne", "llm_belief", "random"}]
    selected.sort(key=lambda curve: preferred_rank(str(curve["algorithm"])))
    plt.figure(figsize=(7.2, 4.4))
    for curve in selected:
        mean = np.asarray(curve["mean"], dtype=float)
        std = np.asarray(curve["std"], dtype=float)
        x_values = np.arange(1, mean.size + 1)
        stderr = std / max(1, int(curve["seeds"])) ** 0.5
        plt.plot(x_values, mean, label=str(curve["label"]), linewidth=2.0)
        plt.fill_between(x_values, mean - stderr, mean + stderr, alpha=0.12)
    plt.xlabel("Round")
    plt.ylabel("Cumulative regret")
    plt.legend(frameon=False, fontsize=8)
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


if __name__ == "__main__":
    main()