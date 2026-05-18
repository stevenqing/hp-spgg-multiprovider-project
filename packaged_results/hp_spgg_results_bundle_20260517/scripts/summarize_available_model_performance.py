from __future__ import annotations

from pathlib import Path

import numpy as np

ROOT = Path("results/cloudgpt")

PROMPTED_MODELS = {
    "DeepSeek-V3.2": "DeepSeek_V3_2",
    "gpt-5.4-nano": "gpt_5_4_nano_20260317",
    "Kimi-K2.6": "Kimi_K2_6",
    "Llama-4-Maverick": "Llama_4_Maverick_17B_128E_Instruct_FP8",
}

EXTERNAL_ALGOS = [
    "atom_tom0",
    "atom_tom1",
    "atom_tom2",
    "atom_adaptive_ftl",
    "atom_adaptive_hedge",
    "econ_bne",
]

EXTERNAL_MODELS = {
    "gpt-5.4-nano": "gpt_5_4_nano_20260317",
    "Kimi-K2.6": "Kimi_K2_6",
    "Llama-4-Maverick": "Llama_4_Maverick_17B_128E_Instruct_FP8",
}


def rows_from_npz(path: Path) -> list[dict[str, object]]:
    data = np.load(path, allow_pickle=True)
    algorithms = [str(value) for value in data["algorithms"]]
    cumulative = data["cumulative_regret"]
    regrets = data["regrets"]
    welfare = data["welfare"]
    rows: list[dict[str, object]] = []
    for index, algorithm in enumerate(algorithms):
        final_regret = cumulative[index, :, -1]
        rows.append(
            {
                "algorithm": algorithm,
                "final_cumulative_regret_mean": float(final_regret.mean()),
                "final_cumulative_regret_std": float(final_regret.std()),
                "per_round_regret_mean": float(regrets[index].mean()),
                "welfare_mean": float(welfare[index].mean()),
                "welfare_std": float(welfare[index].std()),
            }
        )
    return rows


def print_row(model: str, family: str, row: dict[str, object], status: str = "complete") -> None:
    print(
        f"{model}\t{family}\t{row['algorithm']}\t"
        f"{row['final_cumulative_regret_mean']:.4f}\t{row['final_cumulative_regret_std']:.4f}\t"
        f"{row['per_round_regret_mean']:.4f}\t"
        f"{row['welfare_mean']:.4f}\t{row['welfare_std']:.4f}\t{status}"
    )


def main() -> None:
    print("model\tfamily\talgorithm\tfinal_cumulative_regret_mean\tfinal_cumulative_regret_std\tper_round_regret_mean\twelfare_mean\twelfare_std\tstatus")

    for model, slug in PROMPTED_MODELS.items():
        path = ROOT / f"E2_llm_baselines_{slug}_c19_K20_s5.npz"
        if path.exists():
            for row in rows_from_npz(path):
                print_row(model, "prompted", row)

    deepseek_external = ROOT / "E2_external_llm_baselines_DeepSeek_V3_2_c19_K20_s5.npz"
    if deepseek_external.exists():
        for row in rows_from_npz(deepseek_external):
            print_row("DeepSeek-V3.2", "external", row)

    for model, slug in EXTERNAL_MODELS.items():
        for algorithm in EXTERNAL_ALGOS:
            path = ROOT / "shards" / f"E2_external_{slug}_c19_K20_s5_{algorithm}.npz"
            if not path.exists():
                continue
            rows = rows_from_npz(path)
            row = next((candidate for candidate in rows if candidate["algorithm"] == algorithm), rows[0])
            print_row(model, "external", row, "complete_shard")


if __name__ == "__main__":
    main()
