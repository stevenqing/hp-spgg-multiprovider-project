"""
Comprehensive v3 redesign of all §10 figures.

Shared design system:
  - Inter sans-serif typography
  - Algorithm family color schemes (Bayesian blue / LLM-coord warm / Type-agnostic gray)
  - "Ours" highlighted via deepest tone + bold label
  - Background bands segment algorithm families
  - Inline value labels at bar tips
  - Minimal grid, no chartjunk
  - Subdued error indicators

Figures produced:
  fig10_hp_spgg_cross_model_v3.{pdf,png}   (already done; regenerated)
  fig10_beta_sweep_v3.{pdf,png}
  fig10_concordia_main_v3.{pdf,png}
  fig10_concordia_cross_model_v3.{pdf,png}
  figA1_hp_spgg_winner_heatmap_v3.{pdf,png}
  figA2_hp_spgg_welfare_pareto_v3.{pdf,png}
  figA3_hp_spgg_iqr_distribution_v3.{pdf,png}
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch
import matplotlib as mpl
import numpy as np
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parents[1] / "arr_paper" / "figs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# DESIGN SYSTEM
# ============================================================
plt.rcParams.update({
    "font.family": "Inter",
    "font.sans-serif": ["Inter", "Helvetica Neue", "Arial", "DejaVu Sans"],
    "font.weight": "regular",
    "font.size": 9,
    "axes.titlesize": 11,
    "axes.titleweight": "semibold",
    "axes.titlepad": 14,
    "axes.titlelocation": "left",
    "axes.titley": 1.02,
    "axes.labelsize": 9,
    "axes.labelweight": "regular",
    "axes.labelpad": 8,
    "axes.linewidth": 0.4,
    "axes.edgecolor": "#cccccc",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": False,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "xtick.color": "#444444",
    "ytick.color": "#444444",
    "xtick.major.size": 0,
    "ytick.major.size": 0,
    "xtick.major.pad": 4,
    "ytick.major.pad": 4,
    "legend.fontsize": 8,
    "legend.frameon": False,
    "legend.handletextpad": 0.4,
    "legend.columnspacing": 1.4,
    "figure.dpi": 130,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
    "mathtext.fontset": "custom",
    "mathtext.it": "Inter:italic",
    "mathtext.bf": "Inter:bold",
    "mathtext.rm": "Inter",
})

PALETTE = {
    "oracle":              "#9aa0a6",
    "hpsmg_plus":          "#1b3a6f",
    "hpsmg":               "#3d6cb3",
    "map_greedy":          "#7b9fcf",
    "joint_psrl":          "#b3c5e0",
    "llm_belief":          "#e08e45",
    "econ_bne":            "#c0463f",
    "atom_tom0":           "#d4a04a",
    "atom_tom1":           "#cc8242",
    "atom_adaptive_hedge": "#b8723d",
    "psrl_notype":         "#3d3d3d",
    "random":              "#6e6e6e",
    "iql":                 "#a8a8a8",
    # Concordia-specific
    "oracle_joint":        "#9aa0a6",
    "hpsmg_plus_joint":    "#1b3a6f",
    "hpsmg_plus_proxy":    "#3d6cb3",
    "econ_bne_mech":       "#c0463f",
    "atom_tom1_mech":      "#cc8242",
    "llm_greedy":          "#e8b06f",
}

LABEL = {
    "oracle":              "Oracle",
    "hpsmg_plus":          r"PACT$^+$ (ours)",
    "hpsmg":               "PACT (ours)",
    "map_greedy":          "MAP-Type-Greedy",
    "joint_psrl":          "Joint-PSRL",
    "llm_belief":          "llm_belief",
    "econ_bne":            "ECON-BNE",
    "atom_tom0":           "A-ToM-0",
    "atom_tom1":           "A-ToM-1",
    "atom_adaptive_hedge": "A-ToM hedge",
    "psrl_notype":         "PSRL-NoType",
    "random":              "Random",
    "iql":                 "IQL",
    "oracle_joint":        "Oracle (joint)",
    "hpsmg_plus_joint":    r"PACT$^+$ (joint proxy, ours)",
    "hpsmg_plus_proxy":    r"PACT$^+$ (proxy, ours)",
    "econ_bne_mech":       "ECON-BNE (mech)",
    "atom_tom1_mech":      "A-ToM-1 (mech)",
    "llm_greedy":          "llm_greedy",
}

FAMILY_BAND = {
    "bayesian":      "#f0f4fa",
    "llm_coord":     "#fbf3ec",
    "type_agnostic": "#f5f5f5",
    "oracle":        "#ffffff",
}
FAMILY_OF = {
    "oracle":              "oracle",
    "hpsmg_plus":          "bayesian",
    "hpsmg":               "bayesian",
    "map_greedy":          "bayesian",
    "joint_psrl":          "bayesian",
    "llm_belief":          "llm_coord",
    "econ_bne":            "llm_coord",
    "atom_tom0":           "llm_coord",
    "atom_tom1":           "llm_coord",
    "atom_adaptive_hedge": "llm_coord",
    "psrl_notype":         "type_agnostic",
    "random":              "type_agnostic",
    "iql":                 "type_agnostic",
}

INK = "#202020"
MUTED = "#555555"
LIGHTER = "#888888"
PALE = "#cccccc"


def style_axis(ax):
    """Apply consistent spine/tick styling."""
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(PALE)
    ax.tick_params(colors=MUTED, which="both")


# ============================================================
# FIG 1: HP-SPGG cross-model (regenerated for completeness)
# ============================================================
def make_fig1_cross_model():
    data = {
        "DeepSeek-V3.2":     [
            ("oracle",              0.000, 0.000),
            ("hpsmg_plus",          0.400, 0.800),
            ("hpsmg",               0.828, 0.541),
            ("map_greedy",          0.712, 0.466),
            ("joint_psrl",          0.832, 0.080),
            ("llm_belief",          3.074, 2.231),
            ("econ_bne",            3.990, 3.414),
            ("atom_tom0",           6.000, 7.457),
            ("atom_adaptive_hedge", 4.790, 4.509),
            ("psrl_notype",        13.912, 7.374),
            ("random",             28.266, 5.124),
            ("iql",                28.342, 16.914),
        ],
        "GPT-5.4-nano":      [
            ("oracle",              0.000, 0.000),
            ("hpsmg_plus",          0.912, 0.292),
            ("hpsmg",               0.644, 0.631),
            ("map_greedy",          0.854, 0.421),
            ("joint_psrl",          1.492, 0.342),
            ("llm_belief",          7.197, 3.475),
            ("econ_bne",           14.880, 2.753),
            ("atom_tom0",           4.080, 4.941),
            ("atom_adaptive_hedge", 7.653, 4.958),
            ("psrl_notype",        17.720, 1.677),
            ("random",             26.458, 1.814),
            ("iql",                24.792, 11.728),
        ],
        "Kimi-K2.6":         [
            ("oracle",              0.000, 0.000),
            ("hpsmg_plus",          0.704, 0.435),
            ("hpsmg",               0.632, 0.609),
            ("map_greedy",          0.762, 0.391),
            ("joint_psrl",          1.650, 0.404),
            ("llm_belief",         11.784, 3.334),
            ("econ_bne",           10.488, 6.032),
            ("atom_tom0",          10.672, 6.356),
            ("atom_adaptive_hedge", 7.484, 4.096),
            ("psrl_notype",        19.506, 2.610),
            ("random",             26.540, 4.514),
            ("iql",                20.118, 18.527),
        ],
        "Llama-4-Maverick":  [
            ("oracle",              0.000, 0.000),
            ("hpsmg_plus",          0.312, 0.624),
            ("hpsmg",               0.732, 0.609),
            ("map_greedy",          0.974, 0.439),
            ("joint_psrl",          1.194, 0.347),
            ("llm_belief",         10.356, 3.819),
            ("econ_bne",            3.382, 4.534),
            ("atom_tom0",           7.240, 7.789),
            ("atom_adaptive_hedge", 7.006, 4.583),
            ("psrl_notype",        10.654, 4.357),
            ("random",             24.342, 4.323),
            ("iql",                27.526, 16.339),
        ],
    }

    canonical_order = [
        "oracle", "hpsmg_plus", "hpsmg", "map_greedy", "joint_psrl",
        "llm_belief", "econ_bne", "atom_tom0", "atom_adaptive_hedge",
        "psrl_notype", "random", "iql",
    ]

    fig, axes = plt.subplots(2, 2, figsize=(9.5, 6.8), sharey=False)
    axes = axes.flatten()

    for idx, (ax, (model_name, rows)) in enumerate(zip(axes, data.items())):
        rowmap = {a: (m, s) for a, m, s in rows}
        present = [a for a in canonical_order if a in rowmap]
        ys = np.arange(len(present))
        means = np.array([rowmap[a][0] for a in present])
        stds  = np.array([rowmap[a][1] for a in present])

        # Family bands
        family_for_row = [FAMILY_OF[a] for a in present]
        run_start = 0
        for i in range(1, len(family_for_row) + 1):
            if i == len(family_for_row) or family_for_row[i] != family_for_row[i - 1]:
                fam = family_for_row[run_start]
                if fam != "oracle":
                    ax.axhspan(run_start - 0.5, i - 0.5,
                               color=FAMILY_BAND[fam], zorder=0)
                run_start = i

        # Bars
        for i, a in enumerate(present):
            ax.barh(ys[i], means[i], height=0.62, color=PALETTE[a],
                    edgecolor="none", zorder=2)
            ax.text(means[i] + 0.6, ys[i], f"{means[i]:.2f}",
                    fontsize=7.5, color=MUTED, va="center", ha="left", zorder=3)
            if stds[i] > 0:
                ax.plot([max(0, means[i] - stds[i]), means[i] + stds[i]],
                        [ys[i], ys[i]], color=LIGHTER, linewidth=0.8,
                        zorder=2.5, alpha=0.7, solid_capstyle="butt")

        ax.set_yticks(ys)
        ax.set_yticklabels([LABEL[a] for a in present], fontsize=8)
        for tick_label, a in zip(ax.get_yticklabels(), present):
            if a in ("hpsmg_plus", "hpsmg"):
                tick_label.set_fontweight("semibold")
                tick_label.set_color("#1b3a6f")

        ax.invert_yaxis()
        ax.set_title(model_name, fontsize=11, fontweight="semibold",
                     loc="left", color=INK)
        if idx >= 2:
            ax.set_xlabel(r"Cumulative Bayesian regret at $K=20$",
                          fontsize=8.5, color=MUTED)

        ax.grid(axis="x", linestyle=":", linewidth=0.5, color="#dddddd", zorder=0.5)
        ax.set_axisbelow(True)
        xmax = means.max() + max(stds.max(), 5)
        ax.set_xlim(0, xmax * 1.15)
        style_axis(ax)

    family_handles = [
        mpatches.Patch(color=FAMILY_BAND["bayesian"],      label="Bayesian type-aware"),
        mpatches.Patch(color=FAMILY_BAND["llm_coord"],     label="LLM coordination"),
        mpatches.Patch(color=FAMILY_BAND["type_agnostic"], label="Type-agnostic"),
    ]
    fig.legend(handles=family_handles, loc="lower center", ncol=3,
               bbox_to_anchor=(0.5, -0.01), frameon=False,
               fontsize=8.5, handlelength=2.0, columnspacing=2.5)

    plt.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(OUT_DIR / "fig10_hp_spgg_cross_model_v3.pdf", bbox_inches="tight")
    fig.savefig(OUT_DIR / "fig10_hp_spgg_cross_model_v3.png", bbox_inches="tight", dpi=180)
    plt.close(fig)
    print("OK: fig10_hp_spgg_cross_model_v3")


# ============================================================
# FIG 2: β-sweep regime (redesigned)
# ============================================================
def make_fig2_beta_sweep():
    """
    Two-panel β-sweep:
      Left: Simulation tier on G_trap, 8 seeds, mean ± std error band
            -- validates Theorem 8.5(i) self-decay edge
      Right: LLM tier on HP-SPGG, 4 backbones, direct labels at curve end
            -- shows backbone-dependent regimes (self-decay + burn-in jump)
    """
    # ---- Simulation tier data (G_trap, K=50, 8 seeds) ----
    sim_betas = [0, 0.3, 1, 3, 10]
    sim_data = {
        0:   [0.03824900, 0.03027404, 0.05171785, 0.06626882, 0.08495601, 0.06339015, 0.00412266, 0.03824900],
        0.3: [0.03824900, 0.03027404, 0.04742121, 0.06626882, 0.08495601, 0.06339015, 0.00412266, 0.03824900],
        1:   [0.03824900, 0.05170398, 0.04742121, 0.06626882, 0.08495601, 0.06339015, 0.00412266, 0.03824900],
        3:   [2.02867288, 1.08034076, 0.04742121, 0.06626882, 0.08495601, 0.06339015, 0.00549688, 2.02867288],
        10:  [2.06901715, 1.16484390, 0.04742121, 0.06626882, 0.08495601, 0.06339015, 4.28220043, 2.06901715],
    }
    sim_means = np.array([np.mean(sim_data[b]) for b in sim_betas])
    sim_stds  = np.array([np.std(sim_data[b], ddof=1) for b in sim_betas])
    sim_medians = np.array([np.median(sim_data[b]) for b in sim_betas])

    # ---- LLM tier data ----
    llm_betas = [0.0, 0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 1.5]
    hpsmg_plus = {
        "DeepSeek-V3.2":     [0.400, 0.400, 0.400, 0.400, 0.400, 0.400, 0.530, 0.630],
        "GPT-5.4-nano":      [0.912, 0.912, 0.912, 0.912, 0.936, 0.994, 0.898, 0.926],
        "Kimi-K2.6":         [0.744, 0.744, 0.744, 0.704, 0.728, 0.728, 0.728, 0.752],
        "Llama-4-Maverick":  [0.966, 0.966, 0.966, 0.312, 0.312, 0.312, 0.312, 0.312],
    }
    model_color = {
        "DeepSeek-V3.2":     "#1b3a6f",
        "GPT-5.4-nano":      "#c0463f",
        "Kimi-K2.6":         "#2c7a5e",
        "Llama-4-Maverick":  "#b8723d",
    }
    model_marker = {
        "DeepSeek-V3.2":     "o",
        "GPT-5.4-nano":      "s",
        "Kimi-K2.6":         "D",
        "Llama-4-Maverick":  "^",
    }
    label_y_offset = {
        "DeepSeek-V3.2":     -0.025,
        "GPT-5.4-nano":      +0.030,
        "Kimi-K2.6":         +0.040,
        "Llama-4-Maverick":  -0.005,
    }
    model_zorder = {
        "Kimi-K2.6":         2,
        "GPT-5.4-nano":      3,
        "DeepSeek-V3.2":     4,
        "Llama-4-Maverick":  5,
    }

    fig, (ax_sim, ax_llm) = plt.subplots(
        1, 2, figsize=(11.5, 4.2),
        gridspec_kw={"width_ratios": [0.85, 1.15]},
    )

    # ============ Panel A: Simulation tier ============
    SIM_COLOR = "#1b3a6f"
    x_sim_plot = np.arange(len(sim_betas))

    # Highlight the "safe regime" β ∈ [0, 1]
    ax_sim.axvspan(-0.4, 2.5, color="#f0f4fa", alpha=0.6, zorder=0.5)

    # Mean line + error band
    ax_sim.fill_between(x_sim_plot, sim_means - sim_stds, sim_means + sim_stds,
                        color=SIM_COLOR, alpha=0.18, zorder=2,
                        linewidth=0)
    ax_sim.plot(x_sim_plot, sim_means, color=SIM_COLOR, linewidth=2.0, zorder=3,
                solid_capstyle="round")
    ax_sim.plot(x_sim_plot, sim_means, "o", markerfacecolor="white",
                markeredgecolor=SIM_COLOR, markersize=7,
                markeredgewidth=1.6, zorder=4)

    # Inline value labels at each mean
    for i, (b, m) in enumerate(zip(sim_betas, sim_means)):
        offset_y = 0.18 if m < 0.5 else (-0.25 if m > 1.5 else 0.15)
        ax_sim.text(x_sim_plot[i], m + offset_y, f"{m:.2f}",
                    fontsize=7.5, color=MUTED, ha="center", va="bottom" if offset_y > 0 else "top")

    ax_sim.set_xticks(x_sim_plot)
    ax_sim.set_xticklabels([f"{b:g}" for b in sim_betas])
    ax_sim.set_xlim(-0.4, len(sim_betas) - 0.6)
    ax_sim.set_xlabel(r"Type-discrimination bonus weight $\beta$", color=MUTED)
    ax_sim.set_ylabel(r"PACT$^+$ cumulative regret at $K=50$", color=MUTED)
    ax_sim.set_ylim(-0.3, 3.2)
    ax_sim.set_yticks([0, 1, 2, 3])
    ax_sim.grid(axis="y", linestyle=":", linewidth=0.5, color="#dddddd")
    ax_sim.set_axisbelow(True)
    ax_sim.set_title("(a) Simulation tier on $\\mathcal{G}^{\\mathrm{trap}}_m$",
                     fontsize=11, fontweight="semibold", loc="left", color=INK)
    style_axis(ax_sim)

    # ============ Panel B: LLM tier ============
    x_llm = np.arange(len(llm_betas))

    # Soft band at burn-in transition zone
    ax_llm.axvspan(2.5, 3.5, color="#fdf0e6", alpha=0.5, zorder=0.5)

    for m, ys in hpsmg_plus.items():
        c = model_color[m]
        mk = model_marker[m]
        z = model_zorder[m]
        ax_llm.plot(x_llm, ys, color=c, linewidth=2.0, zorder=z,
                    solid_capstyle="round")
        ax_llm.plot(x_llm, ys, mk, markerfacecolor="white", markeredgecolor=c,
                    markersize=7, markeredgewidth=1.6, zorder=z + 0.5)

        # Direct label at end of curve (backbone name only)
        end_y = ys[-1] + label_y_offset[m]
        ax_llm.text(len(llm_betas) - 1 + 0.25, end_y,
                    m, fontsize=8.5, color=c, fontweight="semibold",
                    va="center", ha="left")

    ax_llm.set_xticks(x_llm)
    ax_llm.set_xticklabels([f"{b:g}" for b in llm_betas])
    ax_llm.set_xlim(-0.4, len(llm_betas) - 1 + 2.4)
    ax_llm.set_xlabel(r"Type-discrimination bonus weight $\beta$", color=MUTED)
    ax_llm.set_ylabel(r"PACT$^+$ cumulative regret at $K=20$", color=MUTED)
    ax_llm.set_ylim(0, 1.18)
    ax_llm.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax_llm.grid(axis="y", linestyle=":", linewidth=0.5, color="#dddddd")
    ax_llm.set_axisbelow(True)
    ax_llm.set_title("(b) LLM tier on HP-SPGG (four backbones)",
                     fontsize=11, fontweight="semibold", loc="left", color=INK)
    style_axis(ax_llm)

    plt.tight_layout()
    fig.savefig(OUT_DIR / "fig10_beta_sweep_v3.pdf", bbox_inches="tight")
    fig.savefig(OUT_DIR / "fig10_beta_sweep_v3.png", bbox_inches="tight", dpi=180)
    plt.close(fig)
    print("OK: fig10_beta_sweep_v3 (two-panel)")


# ============================================================
# FIG 3: Concordia main (Option A) — 2-panel
# ============================================================
def make_fig3_concordia_main():
    """
    Concordia results as TWO RADAR/POLYGON charts side by side.
    - Left: Pub Coordination (9 axes = 8 mech + 1 DeepSeek live)
    - Right: Haggling (9 axes)

    Each axis is a config. Each algorithm gets a polygon. Oracle = outer ring
    of the radar (when normalized, oracle scores form the unit circle reference).
    """
    # ---- Pub Coordination data ----
    pub_coord_data = [
        # (short_label, dict)
        ("capetown\n($s$=100)",        {"oracle_joint": 1.265, "hpsmg_plus_joint": 1.248, "econ_bne_mech": 1.042, "atom_tom1_mech": 0.983}),
        ("capetown\n($s$=30)",         {"oracle_joint": 1.276, "hpsmg_plus_joint": 1.247, "econ_bne_mech": 1.044, "atom_tom1_mech": 0.965}),
        ("edinburgh\n($s$=30)",        {"oracle_joint": 1.270, "hpsmg_plus_joint": 1.270, "econ_bne_mech": 1.270, "atom_tom1_mech": 1.270}),
        ("edinburgh\nclosures",        {"oracle_joint": 1.226, "hpsmg_plus_joint": 1.208, "econ_bne_mech": 1.087, "atom_tom1_mech": 1.013}),
        ("edinburgh\ntough fr.",       {"oracle_joint": 1.253, "hpsmg_plus_joint": 1.253, "econ_bne_mech": 1.253, "atom_tom1_mech": 1.253}),
        ("london\n($s$=30)",           {"oracle_joint": 1.335, "hpsmg_plus_joint": 1.317, "econ_bne_mech": 1.202, "atom_tom1_mech": 1.154}),
        ("london\nclosures",           {"oracle_joint": 1.275, "hpsmg_plus_joint": 1.267, "econ_bne_mech": 1.235, "atom_tom1_mech": 1.224}),
        ("london mini\n($s$=30)",      {"oracle_joint": 1.317, "hpsmg_plus_joint": 1.308, "econ_bne_mech": 1.076, "atom_tom1_mech": 1.064}),
        ("london mini\nDeepSeek live", {"oracle_joint": 1.300, "hpsmg_plus_joint": 1.108, "econ_bne_mech": 0.825, "atom_tom1_mech": 0.825}),
    ]
    # ---- Haggling data ----
    haggling_data = [
        ("fruitville\ngullible\n(single)",  {"oracle_joint": 7.000, "hpsmg_plus_joint": 7.400, "econ_bne_mech": 7.400, "atom_tom1_mech": 7.000}),
        ("fruitville\n(single)",            {"oracle_joint": 7.822, "hpsmg_plus_joint": 7.822, "econ_bne_mech": 7.822, "atom_tom1_mech": 7.822}),
        ("vegbrooke\n(single)",             {"oracle_joint": 1.983, "hpsmg_plus_joint": 1.983, "econ_bne_mech": 1.733, "atom_tom1_mech": 1.983}),
        ("vegbrooke\nstrange",              {"oracle_joint": 0.000, "hpsmg_plus_joint": 0.000, "econ_bne_mech": 0.000, "atom_tom1_mech": -10.000}),
        ("vegbrooke\nstubborn",             {"oracle_joint": -0.333, "hpsmg_plus_joint": 1.100, "econ_bne_mech": 0.967, "atom_tom1_mech": 0.767}),
        ("cumulative\nscore (multi)",       {"oracle_joint": 5.600, "hpsmg_plus_joint": 6.000, "econ_bne_mech": 6.000, "atom_tom1_mech": 5.600}),
        ("fruitville\ngullible (multi)",    {"oracle_joint": 6.300, "hpsmg_plus_joint": 6.767, "econ_bne_mech": 6.700, "atom_tom1_mech": 5.667}),
        ("fruitville\nmulti",               {"oracle_joint": 4.400, "hpsmg_plus_joint": 4.400, "econ_bne_mech": 4.400, "atom_tom1_mech": 3.933}),
        ("vegbrooke\n(multi)",              {"oracle_joint": 4.550, "hpsmg_plus_joint": 4.550, "econ_bne_mech": 4.550, "atom_tom1_mech": 4.100}),
    ]

    algos_order = ["oracle_joint", "hpsmg_plus_joint", "econ_bne_mech", "atom_tom1_mech"]

    def normalize_per_axis(data, algo, axis_idx):
        """
        Per-axis normalization: scale all algorithms on each axis so that
        best (max across the 4 algos) -> 1.0 and worst -> 0.15 (not 0,
        to keep all polygons visible).
        Caps at 1.25 in case PACT+ exceeds the others.
        """
        d = data[axis_idx][1]
        algos = ["oracle_joint", "hpsmg_plus_joint", "econ_bne_mech", "atom_tom1_mech"]
        all_scores = [d.get(a, 0) for a in algos]
        best = max(all_scores)
        worst = min(all_scores)
        if best == worst:
            return 1.0  # degenerate axis where all algos tie
        score = d.get(algo, 0)
        # Linear remap [worst, best] -> [0.15, 1.0]
        norm = 0.15 + 0.85 * (score - worst) / (best - worst)
        return max(0.15, min(norm, 1.25))

    def draw_radar(ax, data, title):
        n_axes = len(data)
        # Angles for each axis (start at top, go clockwise)
        angles = np.linspace(np.pi / 2, np.pi / 2 - 2 * np.pi,
                             n_axes, endpoint=False)

        # Draw axis spokes
        for ang in angles:
            ax.plot([ang, ang], [0, 1.25],
                    color="#dddddd", linewidth=0.5, zorder=0.5)

        # Draw concentric reference rings
        for r in (0.25, 0.5, 0.75, 1.0):
            circle_angles = np.linspace(0, 2 * np.pi, 100)
            ax.plot(circle_angles, [r] * 100,
                    color="#dddddd" if r < 1.0 else "#aaaaaa",
                    linewidth=0.5 if r < 1.0 else 0.8,
                    linestyle=":" if r < 1.0 else "-",
                    zorder=0.5)
        # Label the oracle ring
        ax.text(np.pi / 2 + 0.06, 1.04, "Oracle",
                fontsize=7.5, color="#7a7a7a", style="italic", ha="left")

        # Draw axis labels at the spoke tips
        for ang, (label, _) in zip(angles, data):
            r = 1.42
            x = r * np.cos(ang)
            y = r * np.sin(ang)
            # Adjust horizontal alignment based on angle
            if abs(np.cos(ang)) < 0.2:
                ha = "center"
            elif np.cos(ang) > 0:
                ha = "left"
            else:
                ha = "right"
            ax.text(ang, r, label, fontsize=7.5, color=MUTED,
                    ha=ha, va="center", linespacing=1.1)

        # Plot each algorithm's polygon
        # Draw order (bottom up): A-ToM-1, ECON-BNE, Oracle, PACT+
        # so PACT+ is the hero polygon on top
        algo_visual = [
            ("atom_tom1_mech",    {"color": PALETTE["atom_tom1_mech"], "lw": 1.5, "alpha_fill": 0.18, "alpha_line": 0.85, "z": 2}),
            ("econ_bne_mech",     {"color": PALETTE["econ_bne_mech"],  "lw": 1.5, "alpha_fill": 0.18, "alpha_line": 0.9,  "z": 3}),
            ("oracle_joint",      {"color": PALETTE["oracle_joint"],   "lw": 1.5, "alpha_fill": 0.0,  "alpha_line": 0.95, "z": 4, "linestyle": "--"}),
            ("hpsmg_plus_joint",  {"color": PALETTE["hpsmg_plus_joint"], "lw": 2.4, "alpha_fill": 0.28, "alpha_line": 1.0,  "z": 5}),
        ]

        for algo, vis in algo_visual:
            vals = [normalize_per_axis(data, algo, i) for i in range(n_axes)]
            # Close the polygon
            vals_closed = vals + [vals[0]]
            angles_closed = list(angles) + [angles[0]]
            ax.fill(angles_closed, vals_closed,
                    color=vis["color"], alpha=vis["alpha_fill"], zorder=vis["z"])
            ax.plot(angles_closed, vals_closed,
                    color=vis["color"], linewidth=vis["lw"],
                    linestyle=vis.get("linestyle", "-"),
                    alpha=vis["alpha_line"], zorder=vis["z"] + 0.5,
                    solid_capstyle="round")
            # Dots at each vertex for the PACT+ polygon to anchor reading
            if algo == "hpsmg_plus_joint":
                ax.plot(angles, vals, "o",
                        markerfacecolor=vis["color"], markeredgecolor="white",
                        markersize=5, markeredgewidth=1.2, zorder=vis["z"] + 1)

        ax.set_ylim(0, 1.32)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_title(title, fontsize=12, fontweight="semibold",
                     color=INK, pad=20)

    # Build the figure with two polar subplots
    fig = plt.figure(figsize=(11.5, 6.0))
    ax_left = fig.add_subplot(1, 2, 1, projection="polar")
    ax_right = fig.add_subplot(1, 2, 2, projection="polar")

    draw_radar(ax_left,  pub_coord_data, "Pub Coordination")
    draw_radar(ax_right, haggling_data,  "Haggling")

    # Shared legend at bottom
    legend_handles = [
        Line2D([0], [0], color=PALETTE["oracle_joint"], linestyle="--",
               linewidth=1.5, label="Oracle (joint)"),
        mpatches.Patch(facecolor=PALETTE["hpsmg_plus_joint"], alpha=0.55,
                       edgecolor=PALETTE["hpsmg_plus_joint"], linewidth=2.4,
                       label=r"PACT$^+$ (joint proxy, ours)"),
        mpatches.Patch(facecolor=PALETTE["econ_bne_mech"], alpha=0.5,
                       edgecolor=PALETTE["econ_bne_mech"], linewidth=1.5,
                       label="ECON-BNE (mech)"),
        mpatches.Patch(facecolor=PALETTE["atom_tom1_mech"], alpha=0.5,
                       edgecolor=PALETTE["atom_tom1_mech"], linewidth=1.5,
                       label="A-ToM-1 (mech)"),
    ]
    fig.legend(handles=legend_handles, loc="lower center", ncol=4,
               frameon=False, fontsize=9, bbox_to_anchor=(0.5, -0.02),
               handlelength=2.0, columnspacing=2.0)

    # Caption note
    fig.text(0.5, -0.07,
             "Each axis is one config; per-axis min–max normalization so the best algorithm reaches the outer ring and the worst reaches the inner ring",
             ha="center", fontsize=7.5, color=LIGHTER, style="italic")

    plt.tight_layout(rect=[0, 0.02, 1, 0.96])
    fig.savefig(OUT_DIR / "fig10_concordia_main_v3.pdf", bbox_inches="tight")
    fig.savefig(OUT_DIR / "fig10_concordia_main_v3.png", bbox_inches="tight", dpi=180)
    plt.close(fig)
    print("OK: fig10_concordia_main_v3 (radar)")


# ============================================================
# FIG 4: Concordia cross-model
# ============================================================
def make_fig4_concordia_cross_model():
    backbones = ["DeepSeek-V3.2", "GPT-5.4-nano", "Llama-4-Maverick"]

    data = {
        "DeepSeek-V3.2": {
            "oracle_joint":     1.300,
            "hpsmg_plus_joint": None,
            "hpsmg_plus_proxy": 1.108,
            "econ_bne":         0.825,
            "atom_tom1":        0.825,
            "llm_belief":       0.825,
            "llm_greedy":       0.825,
        },
        "GPT-5.4-nano": {
            "oracle_joint":     1.300,
            "hpsmg_plus_joint": 1.300,
            "hpsmg_plus_proxy": 1.108,
            "econ_bne":         1.125,
            "atom_tom1":        1.008,
            "llm_belief":       1.008,
            "llm_greedy":       1.050,
        },
        "Llama-4-Maverick": {
            "oracle_joint":     1.300,
            "hpsmg_plus_joint": 1.300,
            "hpsmg_plus_proxy": 1.108,
            "econ_bne":         0.825,
            "atom_tom1":        0.825,
            "llm_belief":       0.825,
            "llm_greedy":       0.825,
        },
    }
    algos_order = ["oracle_joint", "hpsmg_plus_joint", "hpsmg_plus_proxy",
                   "econ_bne", "atom_tom1", "llm_belief", "llm_greedy"]

    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    n = len(algos_order)
    bar_w = 0.105
    x = np.arange(len(backbones))

    for j, algo in enumerate(algos_order):
        ys, missing = [], []
        for k, bb in enumerate(backbones):
            v = data[bb].get(algo)
            if v is None:
                ys.append(0)
                missing.append(k)
            else:
                ys.append(v)
        off = (j - (n - 1) / 2) * bar_w
        bars = ax.bar(x + off, ys, width=bar_w,
                      color=PALETTE[algo], edgecolor="none",
                      label=LABEL[algo], zorder=2)
        # Hide missing ones
        for idx in missing:
            bars[idx].set_alpha(0.0)
            ax.text(x[idx] + off, 0.04, "n/a", fontsize=6.5,
                    color=LIGHTER, ha="center", va="bottom",
                    rotation=90, style="italic")

    # Oracle reference line
    ax.axhline(y=1.300, color=PALETTE["oracle_joint"], linewidth=0.8,
               linestyle=":", alpha=0.55, zorder=1)
    ax.text(len(backbones) - 0.5, 1.318, "Oracle = 1.30",
            fontsize=7.5, color=LIGHTER, ha="right", va="bottom",
            style="italic")

    ax.set_xticks(x)
    ax.set_xticklabels(backbones, fontsize=9)
    ax.set_ylabel("Focal score mean", color=MUTED)
    ax.set_ylim(0, 1.45)
    ax.grid(axis="y", linestyle=":", linewidth=0.5, color="#dddddd")
    ax.set_axisbelow(True)
    ax.set_title(r"Concordia Pub Coordination $\cdot$ $\mathrm{london\_mini}$ live LLM rollouts ($s=5$)",
                 fontsize=11.5, fontweight="semibold", loc="left", color=INK)
    style_axis(ax)

    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.28),
              ncol=4, frameon=False, fontsize=8, handletextpad=0.4,
              columnspacing=1.6)

    plt.tight_layout()
    fig.savefig(OUT_DIR / "fig10_concordia_cross_model_v3.pdf", bbox_inches="tight")
    fig.savefig(OUT_DIR / "fig10_concordia_cross_model_v3.png", bbox_inches="tight", dpi=180)
    plt.close(fig)
    print("OK: fig10_concordia_cross_model_v3")


# ============================================================
# FIG A1: Winner heatmap (refined)
# ============================================================
def make_figA1_winner_heatmap():
    betas = [0.0, 0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 1.5]
    models = ["DeepSeek-V3.2", "GPT-5.4-nano", "Kimi-K2.6", "Llama-4-Maverick"]

    hpsmg_plus = {
        "DeepSeek-V3.2":     [0.400, 0.400, 0.400, 0.400, 0.400, 0.400, 0.530, 0.630],
        "GPT-5.4-nano":      [0.912, 0.912, 0.912, 0.912, 0.936, 0.994, 0.898, 0.926],
        "Kimi-K2.6":         [0.744, 0.744, 0.744, 0.704, 0.728, 0.728, 0.728, 0.752],
        "Llama-4-Maverick":  [0.966, 0.966, 0.966, 0.312, 0.312, 0.312, 0.312, 0.312],
    }
    hpsmg = {"DeepSeek-V3.2": 0.828, "GPT-5.4-nano": 0.644, "Kimi-K2.6": 0.632, "Llama-4-Maverick": 0.732}
    map_greedy = {"DeepSeek-V3.2": 0.712, "GPT-5.4-nano": 0.854, "Kimi-K2.6": 0.762, "Llama-4-Maverick": 0.974}
    joint_psrl = {"DeepSeek-V3.2": 0.832, "GPT-5.4-nano": 1.492, "Kimi-K2.6": 1.650, "Llama-4-Maverick": 1.194}

    cat_color = {
        0: PALETTE["hpsmg_plus"],
        1: PALETTE["hpsmg"],
        2: PALETTE["map_greedy"],
        3: PALETTE["joint_psrl"],
    }
    cat_label = {
        0: r"PACT$^+$ wins",
        1: r"PACT ($\beta=0$) wins",
        2: "MAP-Type-Greedy wins",
        3: "Joint-PSRL wins",
    }

    winners = np.zeros((len(models), len(betas)), dtype=int)
    regrets = np.zeros((len(models), len(betas)))
    for i, m in enumerate(models):
        for j, b in enumerate(betas):
            vals = {0: hpsmg_plus[m][j], 1: hpsmg[m], 2: map_greedy[m], 3: joint_psrl[m]}
            winner = min(vals, key=lambda k: vals[k])
            winners[i, j] = winner
            regrets[i, j] = vals[winner]

    fig, ax = plt.subplots(figsize=(7.5, 3.4))

    # Color grid with thin white separators
    img = np.zeros((len(models), len(betas), 4))
    for i in range(len(models)):
        for j in range(len(betas)):
            c = cat_color[winners[i, j]]
            r, g, bl = int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)
            img[i, j] = [r / 255, g / 255, bl / 255, 1.0]
    ax.imshow(img, aspect="auto", interpolation="nearest")

    # White gridlines between cells
    for j in range(1, len(betas)):
        ax.axvline(x=j - 0.5, color="white", linewidth=2)
    for i in range(1, len(models)):
        ax.axhline(y=i - 0.5, color="white", linewidth=2)

    # Text labels: regret values
    for i in range(len(models)):
        for j in range(len(betas)):
            text_color = "white" if winners[i, j] in (0, 1, 3) and j < 8 else INK
            # PACT light blue band needs dark text; PACT+ dark navy needs light text
            if winners[i, j] == 1:  # PACT (medium-blue)
                text_color = "white"
            elif winners[i, j] == 0:  # PACT+ (deepest navy)
                text_color = "white"
            elif winners[i, j] == 2:
                text_color = INK
            elif winners[i, j] == 3:
                text_color = INK
            ax.text(j, i, f"{regrets[i,j]:.2f}",
                    fontsize=9, ha="center", va="center",
                    color=text_color, fontweight="semibold")

    ax.set_xticks(range(len(betas)))
    ax.set_xticklabels([f"{b:g}" for b in betas])
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels(models)
    # No xlabel — title already says "(backbone, β)" and tick values are clearly β
    ax.set_title(r"Winning Bayesian-family algorithm at each (backbone, $\beta$) cell",
                 fontsize=11, fontweight="semibold", loc="left", color=INK)
    ax.tick_params(colors=MUTED, length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)

    handles = [mpatches.Patch(color=c, label=cat_label[k]) for k, c in cat_color.items()]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.40),
              ncol=4, frameon=False, fontsize=8, handlelength=1.5,
              columnspacing=2.2)

    # Caption strip below legend
    ax.text(0.5, -0.55,
            r"$\beta$ values shown along x-axis. Cell text shows the winner's cumulative regret at $K=20$",
            transform=ax.transAxes, fontsize=7.5, color=LIGHTER,
            style="italic", ha="center")

    plt.tight_layout()
    fig.savefig(OUT_DIR / "figA1_hp_spgg_winner_heatmap_v3.pdf", bbox_inches="tight")
    fig.savefig(OUT_DIR / "figA1_hp_spgg_winner_heatmap_v3.png", bbox_inches="tight", dpi=180)
    plt.close(fig)
    print("OK: figA1_hp_spgg_winner_heatmap_v3")


# ============================================================
# FIG A2: Welfare vs regret Pareto scatter (refined)
# ============================================================
def make_figA2_welfare_pareto():
    points = [
        ("DeepSeek-V3.2", "hpsmg_plus",          0.400, 2.760),
        ("DeepSeek-V3.2", "hpsmg",               0.828, 2.853),
        ("DeepSeek-V3.2", "map_greedy",          0.712, 2.714),
        ("DeepSeek-V3.2", "joint_psrl",          0.832, 2.838),
        ("DeepSeek-V3.2", "llm_belief",          3.074, 2.736),
        ("DeepSeek-V3.2", "econ_bne",            3.990, 2.610),
        ("DeepSeek-V3.2", "atom_tom0",           6.000, 2.590),
        ("DeepSeek-V3.2", "atom_adaptive_hedge", 4.790, 2.660),
        ("DeepSeek-V3.2", "psrl_notype",        13.912, 2.174),
        ("DeepSeek-V3.2", "random",             28.266, 1.477),
        ("DeepSeek-V3.2", "iql",                28.342, 1.397),
        ("GPT-5.4-nano", "hpsmg_plus",           0.912, 2.560),
        ("GPT-5.4-nano", "hpsmg",                0.644, 2.820),
        ("GPT-5.4-nano", "map_greedy",           0.854, 2.637),
        ("GPT-5.4-nano", "joint_psrl",           1.492, 2.701),
        ("GPT-5.4-nano", "llm_belief",           7.197, 2.454),
        ("GPT-5.4-nano", "econ_bne",            14.880, 1.948),
        ("GPT-5.4-nano", "atom_tom0",            4.080, 2.586),
        ("GPT-5.4-nano", "atom_adaptive_hedge",  7.653, 2.441),
        ("GPT-5.4-nano", "psrl_notype",         17.720, 1.750),
        ("GPT-5.4-nano", "random",              26.458, 1.519),
        ("GPT-5.4-nano", "iql",                 24.792, 1.444),
        ("Kimi-K2.6", "hpsmg_plus",              0.704, 2.549),
        ("Kimi-K2.6", "hpsmg",                   0.632, 2.820),
        ("Kimi-K2.6", "map_greedy",              0.762, 2.550),
        ("Kimi-K2.6", "joint_psrl",              1.650, 2.694),
        ("Kimi-K2.6", "llm_belief",             11.784, 2.225),
        ("Kimi-K2.6", "econ_bne",               10.488, 2.168),
        ("Kimi-K2.6", "atom_tom0",              10.672, 2.256),
        ("Kimi-K2.6", "atom_adaptive_hedge",     7.484, 2.450),
        ("Kimi-K2.6", "psrl_notype",            19.506, 1.779),
        ("Kimi-K2.6", "random",                 26.540, 1.483),
        ("Kimi-K2.6", "iql",                    20.118, 1.666),
        ("Llama-4-Maverick", "hpsmg_plus",       0.312, 2.782),
        ("Llama-4-Maverick", "hpsmg",            0.732, 2.857),
        ("Llama-4-Maverick", "map_greedy",       0.974, 2.751),
        ("Llama-4-Maverick", "joint_psrl",       1.194, 2.754),
        ("Llama-4-Maverick", "llm_belief",      10.356, 2.352),
        ("Llama-4-Maverick", "econ_bne",         3.382, 2.603),
        ("Llama-4-Maverick", "atom_tom0",        7.240, 2.524),
        ("Llama-4-Maverick", "atom_adaptive_hedge", 7.006, 2.524),
        ("Llama-4-Maverick", "psrl_notype",     10.654, 2.311),
        ("Llama-4-Maverick", "random",          24.342, 1.653),
        ("Llama-4-Maverick", "iql",             27.526, 1.484),
    ]

    model_marker = {
        "DeepSeek-V3.2":     "o",
        "GPT-5.4-nano":      "s",
        "Kimi-K2.6":         "D",
        "Llama-4-Maverick":  "^",
    }

    fig, ax = plt.subplots(figsize=(7.5, 4.8))

    # Family-region background bands (soft)
    ax.axvspan(0, 2.5, color=FAMILY_BAND["bayesian"], zorder=0, alpha=0.5)
    ax.axvspan(2.5, 16, color=FAMILY_BAND["llm_coord"], zorder=0, alpha=0.5)
    ax.axvspan(16, 35, color=FAMILY_BAND["type_agnostic"], zorder=0, alpha=0.5)

    # Add family labels just below the ylim ceiling, anchored consistently
    ax.text(1.25, 3.05, "Bayesian", fontsize=8, color="#5a73a3",
            ha="center", va="top", fontweight="semibold", alpha=0.85)
    ax.text(9.0, 3.05, "LLM coordination", fontsize=8, color="#a06030",
            ha="center", va="top", fontweight="semibold", alpha=0.85)
    ax.text(25.0, 3.05, "Type-agnostic", fontsize=8, color="#666666",
            ha="center", va="top", fontweight="semibold", alpha=0.85)

    # Pareto frontier line
    sorted_points = sorted(points, key=lambda p: p[2])
    fx, fy = [], []
    best_w = -float("inf")
    for (_, _, x, y) in sorted_points:
        if y > best_w:
            best_w = y
            fx.append(x)
            fy.append(y)
    ax.plot(fx, fy, color=INK, linewidth=0.8, linestyle="--",
            alpha=0.35, zorder=1)

    # Points
    for (model, algo, regret, welfare) in points:
        # PACT+ rendered with white halo and large size for emphasis
        if algo == "hpsmg_plus":
            ax.scatter(regret, welfare, s=120,
                       color=PALETTE[algo],
                       marker=model_marker[model],
                       edgecolor="white", linewidth=1.5, zorder=4)
        else:
            ax.scatter(regret, welfare, s=55,
                       color=PALETTE[algo],
                       marker=model_marker[model],
                       edgecolor="white", linewidth=0.8, zorder=3,
                       alpha=0.88)

    ax.set_xlabel(r"Cumulative regret at $K=20$ (lower is better)", color=MUTED)
    ax.set_ylabel("Welfare mean (higher is better)", color=MUTED)
    ax.set_xlim(-1, 32)
    ax.set_ylim(1.3, 3.1)
    ax.grid(linestyle=":", linewidth=0.5, color="#dddddd")
    ax.set_axisbelow(True)
    ax.set_title("Welfare vs regret tradeoff on HP-SPGG",
                 fontsize=11.5, fontweight="semibold", loc="left", color=INK)
    style_axis(ax)

    # Build legends manually
    algo_groups = [
        ("Bayesian (ours)", ["hpsmg_plus", "hpsmg", "map_greedy", "joint_psrl"]),
        ("LLM coordination", ["llm_belief", "econ_bne", "atom_tom0", "atom_adaptive_hedge"]),
        ("Type-agnostic", ["psrl_notype", "random", "iql"]),
    ]
    algo_handles = []
    for group_label, algos in algo_groups:
        for algo in algos:
            algo_handles.append(
                Line2D([0], [0], marker="o", color="w",
                       markerfacecolor=PALETTE[algo], markersize=8,
                       markeredgecolor="white", markeredgewidth=0.5,
                       label=LABEL[algo], linewidth=0)
            )
    leg1 = ax.legend(handles=algo_handles, loc="upper right",
                     bbox_to_anchor=(0.99, 0.95),
                     title="Algorithm", title_fontsize=8,
                     fontsize=7, frameon=False, ncol=2, columnspacing=1.0)
    leg1.get_title().set_fontweight("semibold")
    leg1.get_title().set_color(INK)
    ax.add_artist(leg1)

    model_handles = [
        Line2D([0], [0], marker=m, color="w",
               markerfacecolor=LIGHTER, markersize=8,
               markeredgecolor="white", markeredgewidth=0.5,
               label=name, linewidth=0)
        for name, m in model_marker.items()
    ]
    model_handles.append(
        Line2D([0], [0], color=INK, linewidth=0.8, linestyle="--", alpha=0.5,
               label="Pareto frontier")
    )
    leg2 = ax.legend(handles=model_handles, loc="lower right",
                     bbox_to_anchor=(0.99, 0.03),
                     title="Backbone", title_fontsize=8,
                     fontsize=7, frameon=False)
    leg2.get_title().set_fontweight("semibold")
    leg2.get_title().set_color(INK)

    plt.tight_layout()
    fig.savefig(OUT_DIR / "figA2_hp_spgg_welfare_pareto_v3.pdf", bbox_inches="tight")
    fig.savefig(OUT_DIR / "figA2_hp_spgg_welfare_pareto_v3.png", bbox_inches="tight", dpi=180)
    plt.close(fig)
    print("OK: figA2_hp_spgg_welfare_pareto_v3")


# ============================================================
# FIG A3: IQR distribution shape (refined)
# ============================================================
def make_figA3_iqr_distribution():
    data = [
        ("hpsmg_plus", "DeepSeek-V3.2",     0.000, 0.000, 0.000),
        ("hpsmg_plus", "GPT-5.4-nano",      0.900, 0.720, 1.220),
        ("hpsmg_plus", "Kimi-K2.6",         0.460, 0.440, 0.720),
        ("hpsmg_plus", "Llama-4-Maverick",  0.000, 0.000, 0.000),
        ("hpsmg", "DeepSeek-V3.2",          1.110, 0.300, 1.210),
        ("hpsmg", "GPT-5.4-nano",           0.580, 0.160, 0.680),
        ("hpsmg", "Kimi-K2.6",              0.580, 0.160, 0.680),
        ("hpsmg", "Llama-4-Maverick",       0.770, 0.160, 1.060),
        ("map_greedy", "DeepSeek-V3.2",     0.720, 0.640, 0.730),
        ("map_greedy", "GPT-5.4-nano",      0.980, 0.450, 1.020),
        ("map_greedy", "Kimi-K2.6",         0.620, 0.450, 1.020),
        ("map_greedy", "Llama-4-Maverick",  1.120, 0.650, 1.180),
        ("joint_psrl", "DeepSeek-V3.2",     0.880, 0.780, 0.900),
        ("joint_psrl", "GPT-5.4-nano",      1.510, 1.300, 1.760),
        ("joint_psrl", "Kimi-K2.6",         1.700, 1.510, 1.960),
        ("joint_psrl", "Llama-4-Maverick",  1.160, 0.960, 1.450),
        ("llm_belief", "DeepSeek-V3.2",     1.680, 1.590, 5.240),
        ("llm_belief", "GPT-5.4-nano",      4.590, 4.320, 11.251),
        ("llm_belief", "Kimi-K2.6",        10.440, 10.030, 14.070),
        ("llm_belief", "Llama-4-Maverick", 10.140, 6.580, 12.190),
        ("econ_bne", "DeepSeek-V3.2",       3.000, 1.940, 5.010),
        ("econ_bne", "GPT-5.4-nano",       14.600, 12.400, 16.200),
        ("econ_bne", "Kimi-K2.6",           6.730, 6.690, 15.190),
        ("econ_bne", "Llama-4-Maverick",    1.000, 0.000, 3.930),
        ("atom_tom0", "DeepSeek-V3.2",      0.000, 0.000, 13.000),
        ("atom_tom0", "GPT-5.4-nano",       0.400, 0.000, 8.400),
        ("atom_tom0", "Kimi-K2.6",          8.990, 7.580, 14.390),
        ("atom_tom0", "Llama-4-Maverick",   3.000, 1.000, 11.800),
        ("atom_adaptive_hedge", "DeepSeek-V3.2",     1.800, 1.670, 9.680),
        ("atom_adaptive_hedge", "GPT-5.4-nano",      8.831, 1.871, 12.298),
        ("atom_adaptive_hedge", "Kimi-K2.6",         8.190, 3.120, 9.320),
        ("atom_adaptive_hedge", "Llama-4-Maverick",  7.910, 2.750, 10.810),
    ]

    algos = ["hpsmg_plus", "hpsmg", "map_greedy", "joint_psrl",
             "llm_belief", "econ_bne", "atom_tom0", "atom_adaptive_hedge"]
    models = ["DeepSeek-V3.2", "GPT-5.4-nano", "Kimi-K2.6", "Llama-4-Maverick"]

    fig, ax = plt.subplots(figsize=(9.0, 5.4))

    y_positions = []
    y_labels = []
    y_cursor = 0
    sep_after = []
    bayes_end_y = None

    for j, algo in enumerate(algos):
        if j > 0:
            sep_after.append(y_cursor - 0.5)
        # When switching from Bayesian to LLM-coord, remember the y for divider
        if algo == "llm_belief":
            bayes_end_y = y_cursor - 0.5

        for k, model in enumerate(models):
            row = next(r for r in data if r[0] == algo and r[1] == model)
            _, _, med, q25, q75 = row

            # IQR thick bar
            ax.plot([q25, q75], [y_cursor, y_cursor],
                    color=PALETTE[algo], linewidth=6, alpha=0.55,
                    solid_capstyle="round", zorder=2)
            # End ticks
            for v in (q25, q75):
                ax.plot([v, v], [y_cursor - 0.15, y_cursor + 0.15],
                        color=PALETTE[algo], linewidth=1.4, zorder=3)
            # Median white-filled dot
            ax.plot(med, y_cursor, "o",
                    markerfacecolor="white",
                    markeredgecolor=PALETTE[algo],
                    markersize=6, markeredgewidth=1.6, zorder=4)

            y_positions.append(y_cursor)
            short = {"DeepSeek-V3.2": "DeepSeek", "GPT-5.4-nano": "GPT",
                     "Kimi-K2.6": "Kimi", "Llama-4-Maverick": "Llama"}[model]
            if k == 0:
                y_labels.append(f"{LABEL[algo]}    {short}")
            else:
                y_labels.append(f"    {short}")
            y_cursor += 1
        y_cursor += 0.7

    # Subtle Bayesian / LLM-coord background bands
    if bayes_end_y is not None:
        ax.axhspan(-0.7, bayes_end_y, color=FAMILY_BAND["bayesian"],
                   alpha=0.5, zorder=0)
        ax.axhspan(bayes_end_y, y_cursor, color=FAMILY_BAND["llm_coord"],
                   alpha=0.5, zorder=0)

    ax.set_yticks(y_positions)
    ax.set_yticklabels(y_labels, fontsize=7.8)
    # Bold the "ours" algorithm names
    for tl, label in zip(ax.get_yticklabels(), y_labels):
        if "PACT$^+$" in label or "PACT " in label:
            tl.set_fontweight("semibold")
            tl.set_color("#1b3a6f")

    ax.invert_yaxis()
    ax.set_xlabel(r"Cumulative regret at $K=20$    (white dot = median, span = IQR)",
                  color=MUTED)
    ax.grid(axis="x", linestyle=":", linewidth=0.5, color="#dddddd")
    ax.set_axisbelow(True)
    ax.set_xlim(-0.5, 18)
    ax.set_title("Median + IQR distribution shape per (algorithm, backbone) on HP-SPGG",
                 fontsize=11.5, fontweight="semibold", loc="left", color=INK)
    style_axis(ax)

    # Light separator between algorithm groups
    for y in sep_after:
        ax.axhline(y=y + 0.25, color="white", linewidth=1.2, zorder=0.5)

    plt.tight_layout()
    fig.savefig(OUT_DIR / "figA3_hp_spgg_iqr_distribution_v3.pdf", bbox_inches="tight")
    fig.savefig(OUT_DIR / "figA3_hp_spgg_iqr_distribution_v3.png", bbox_inches="tight", dpi=180)
    plt.close(fig)
    print("OK: figA3_hp_spgg_iqr_distribution_v3")


if __name__ == "__main__":
    make_fig1_cross_model()
    make_fig2_beta_sweep()
    make_fig3_concordia_main()
    make_fig4_concordia_cross_model()
    make_figA1_winner_heatmap()
    make_figA2_welfare_pareto()
    make_figA3_iqr_distribution()
    print("\nAll v3 figures regenerated in:", OUT_DIR)
