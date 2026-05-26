"""Generate paper-ready figures from results.npz."""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


ALGOS = ["hpsmg_plus", "hpsmg", "joint_psrl", "map_greedy", "random", "oracle"]
LABELS = {
    "hpsmg_plus":  r"PACT$^{+}$",
    "hpsmg":       r"PACT",
    "joint_psrl":  r"Joint-PSRL",
    "map_greedy":  r"MAP-Type-Greedy",
    "random":      r"Random",
    "oracle":      r"Oracle",
}
COLORS = {
    "hpsmg_plus":  "#1f77b4",
    "hpsmg":       "#ff7f0e",
    "joint_psrl":  "#2ca02c",
    "map_greedy":  "#d62728",
    "random":      "#7f7f7f",
    "oracle":      "#9467bd",
}
LINESTYLES = {
    "hpsmg_plus":  "-",
    "hpsmg":       "--",
    "joint_psrl":  "-.",
    "map_greedy":  ":",
    "random":      "-",
    "oracle":      "-",
}


def main():
    data = np.load("results.npz")
    K = len(data["hpsmg_plus_cumreg_mean"])

    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(11, 3.5))

    # Left: cumulative regret over rounds
    rounds = np.arange(1, K + 1)
    for algo in ALGOS:
        m = data[f"{algo}_cumreg_mean"]
        s = data[f"{algo}_cumreg_std"]
        n_seeds = data[f"{algo}_posterior"].shape[0]
        sem = s / np.sqrt(n_seeds)
        ax_left.plot(rounds, m, label=LABELS[algo], color=COLORS[algo],
                     linestyle=LINESTYLES[algo], linewidth=2)
        ax_left.fill_between(rounds, m - sem, m + sem,
                             color=COLORS[algo], alpha=0.15)
    ax_left.set_xlabel("Round $k$")
    ax_left.set_ylabel(r"Cumulative regret $\sum_{k'=1}^{k} \mathrm{Reg}^B(k')$")
    ax_left.set_title("Per-round Bayesian regret (HP-SPGG)")
    ax_left.legend(loc="upper left", fontsize=9, ncol=2)
    ax_left.grid(True, alpha=0.3)

    # Right: posterior concentration on true type (averaged across agents and seeds)
    # Compute mean TV distance to delta on true type over rounds, for PACT+ only
    # (other algorithms compared if interesting)
    for algo in ["hpsmg_plus", "hpsmg", "joint_psrl"]:
        post = data[f"{algo}_posterior"]  # (seeds, K, n, |Theta_i|)
        # True types per seed: argmax of final posterior? No - need to load
        # separately. Instead, plot the max posterior mass per agent over rounds.
        n_seeds, K_, n_agents, _ = post.shape
        max_mass = post.max(axis=-1)  # (seeds, K, n) - confidence in MAP type
        mean_max = max_mass.mean(axis=(0, 2))  # average over seeds and agents
        ax_right.plot(rounds, mean_max, label=LABELS[algo],
                      color=COLORS[algo], linestyle=LINESTYLES[algo], linewidth=2)
    ax_right.axhline(1.0, color='k', linestyle=':', alpha=0.4)
    ax_right.set_xlabel("Round $k$")
    ax_right.set_ylabel("Posterior mass on MAP type (mean over agents)")
    ax_right.set_title("Posterior concentration over rounds")
    ax_right.legend(loc="lower right", fontsize=9)
    ax_right.grid(True, alpha=0.3)
    ax_right.set_ylim(0.25, 1.05)

    fig.tight_layout()
    fig.savefig("hp_spgg_results.pdf", bbox_inches="tight")
    fig.savefig("hp_spgg_results.png", bbox_inches="tight", dpi=140)
    print("Saved hp_spgg_results.pdf and hp_spgg_results.png")

    # Print summary table to console (for inclusion in paper)
    print("\n=== Summary table (cumulative regret at K=K) ===")
    for algo in ALGOS:
        m = data[f"{algo}_cumreg_mean"][-1]
        s = data[f"{algo}_cumreg_std"][-1]
        n_seeds = data[f"{algo}_posterior"].shape[0]
        sem = s / np.sqrt(n_seeds)
        print(f"  {LABELS[algo]:>20}: {m:>6.2f} +/- {sem:.2f}")


if __name__ == "__main__":
    main()
