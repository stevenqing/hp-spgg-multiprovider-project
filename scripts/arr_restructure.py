"""Restructure arr_paper/main.tex: condense theory in body, push proofs to appendix.tex."""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAIN = ROOT / "arr_paper" / "main.tex"
APPENDIX = ROOT / "arr_paper" / "appendix.tex"

NEW_THEORY = r"""\section{Theoretical Guarantees}
\label{sec:theory}

The decoupling theorem is the structural foundation of our analysis. Combined
with the algorithmic refinement of H-PSMG\textsuperscript{+}, it yields a
regret bound that is exponentially tighter in $n$ than the generic
Bayesian-RL guarantee for the joint hypothesis class, and admits an
exponential-in-$|\Theta|^n$ burn-in improvement on a deep-trap family. We
state the three informal theorems here; all proofs, supporting lemmas, the
worked numerical illustration on the two-agent Bayesian Prisoner's Dilemma,
the counter-examples motivating the structural assumptions, and the
matching minimax lower bounds are deferred to the appendix.

\subsection{Posterior decoupling}

\begin{theorem}[Posterior Decoupling, informal]
\label{thm:decoupling}
Under Assumptions~\ref{ass:TI} (Type-Independent Transitions),
\ref{ass:RL} (Reward Locality), and \ref{ass:PF} (Prior Factorisation),
the posterior over the latent world factorises at every episode:
\begin{equation}
\label{eq:decoupling}
P(P, \boldsymbol{\theta} \mid \mathcal{H}_k)
  = \mu_{k+1}^P(P) \cdot \prod_{i \in [n]} \mu_{k+1}^{\Theta,i}(\theta_i),
  \qquad \forall k \geq 0,
\end{equation}
with marginals updated independently by Bayes' rule from their respective
likelihood factors $L_P$ and $L_{\Theta,i}$.
\end{theorem}

Two immediate consequences. \emph{Storage:} maintaining the joint posterior
costs $O(\dim(P_0^P) + n|\Theta_i|)$ rather than the naive
$O(\dim(P_0^P) \cdot |\Theta|^n)$ (Corollary~\ref{cor:storage}).
\emph{Trajectory equivalence:} under coupled randomness, H-PSMG and
Joint-PSRL produce pathwise-identical trajectories
(Proposition~\ref{prop:bit-identical}); H-PSMG is therefore a statistical
equal of Joint-PSRL at exponentially smaller memory. The two structural
assumptions TI and RL are individually necessary: violating either breaks
the likelihood factorisation, as shown by two minimal counter-examples in
the appendix.

\subsection{Bayesian regret}

\begin{theorem}[Bayesian Regret of H-PSMG, informal]
\label{thm:main-regret-informal}
Under the assumptions of Theorem~\ref{thm:decoupling} together with
Assumptions~\ref{ass:ISI}, \ref{ass:CSR}, a Dirichlet prior on $P^*$,
and a bounded type-inference information ratio
$\bar{\Gamma} = O(H^2 |\Theta_i|)$, the Bayesian regret of agent $i$
over $K$ episodes satisfies
\begin{equation}
\mathbb{E}\big[\mathrm{Reg}_i^B(K)\big]
 \leq \tilde{O}\!\Big(H^{3/2}\sqrt{S \cdot A_{\mathrm{joint}} \cdot K}\Big)
 + O\!\Big(H \sqrt{|\Theta_i| \log|\Theta_i| \cdot K}\Big)
 + K \cdot \epsilon_{\mathrm{CCE}},
\end{equation}
where $A_{\mathrm{joint}} = \prod_i |\mathcal{A}_i|$ and
$\epsilon_{\mathrm{CCE}}$ is the CCE oracle approximation error.
\end{theorem}

The bound cleanly separates transition learning from per-agent type
identification. It is tight in both directions. Without
Assumption~\ref{ass:PF}, no algorithm achieves better than
$\Omega(\sqrt{|\Theta|^n K})$, exponentially worse in $n$
(Theorem~\ref{thm:lower-no-pf}); under the full assumption set, a matching
minimax lower bound (Theorem~\ref{thm:lower-matching}) shows that our
bound is near-optimal modulo a $\sqrt{H}$ gap on the type-inference term.
Under the stronger identifiability Assumption~\ref{ass:TID}, the
type-inference cost collapses to a constant burn-in $O(H \log|\Theta_i|/\rho)$
(Corollary~\ref{cor:gap-dependent}).

\subsection{Burn-in separation for H-PSMG\texorpdfstring{\textsuperscript{+}}{+}}

\begin{theorem}[Regret of H-PSMG\textsuperscript{+}, informal]
\label{thm:hpsmg-plus}
Fix $\beta > 0$. Under the assumptions of
Theorem~\ref{thm:main-regret-informal}:

\emph{(i) Asymptotic match.} On any HT-MG, the Bayesian regret of
H-PSMG\textsuperscript{+} matches the H-PSMG bound of
Theorem~\ref{thm:main-regret-informal} up to a constant absorbed into the
leading $\tilde{O}(H\sqrt{|\Theta_i| K})$ term.

\emph{(ii) Exponential-in-$|\Theta|^n$ burn-in improvement.} On the
deep-trap family $\mathcal{G}_m^{\mathrm{trap}}$ (formal construction in
the appendix), the expected burn-in regret of H-PSMG and Joint-PSRL is
$\Theta(m^n H)$, whereas H-PSMG\textsuperscript{+} achieves $O(H)$ for any
$\beta > 0$; the separation is $\Omega(m^n)$.
\end{theorem}

A companion rate-separation result (Theorem~\ref{thm:rate-separation}) shows
that two natural type-agnostic alternatives---MAP-type-greedy and
type-uniform PSRL---both incur $\Omega(K)$ regret on an explicit
exploration-trap instance while H-PSMG remains $\tilde O(\sqrt{K})$. The
empirical counterpart of all three guarantees, on an LLM substrate, is the
subject of Section~\ref{sec:experiments-llm}.

"""

# Line numbers are 1-indexed in the file but we work 0-indexed in Python.
# Boundaries derived from the structure survey:
#   1 .. 286    keep (preamble, Intro, Related Work, Problem Setting, Algorithm)
# 287 .. 694    cut (sections: PD theorem + proofs, BPD example, counter-examples, regret roadmap)
# 695 .. 1208   keep (Empirical Study, Discussion, Conclusion, then \appendix)
#1209 .. 2235   cut (in-line appendix material)
#2236           \end{document} -- re-emit manually


def relabel(text: str) -> str:
    """Rename labels that will live in the appendix to avoid clashes with the
    new informal theorems in the main body, then patch internal refs."""
    pairs = [
        ("thm:decoupling", "thm:decoupling-app"),
        ("thm:main-regret-informal", "thm:main-regret-app"),
        ("thm:hpsmg-plus", "thm:hpsmg-plus-app"),
    ]
    for old, new in pairs:
        text = text.replace("\\label{" + old + "}", "\\label{" + new + "}")
        text = text.replace("\\ref{" + old + "}", "\\ref{" + new + "}")
    return text


def main() -> None:
    src = MAIN.read_text(encoding="utf-8").split("\n")
    pre_body = src[:286]
    cut_theory = src[286:694]
    post_body = src[694:1208]   # ends with the \appendix line
    inline_app = src[1208:2235]

    new_main = (
        pre_body
        + NEW_THEORY.rstrip("\n").split("\n")
        + post_body
        + ["", "\\input{appendix}", "", "\\end{document}", ""]
    )

    cut_theory_text = relabel("\n".join(cut_theory))
    inline_app_text = relabel("\n".join(inline_app))
    new_app_text = cut_theory_text + "\n\n" + inline_app_text + "\n"

    MAIN.write_text("\n".join(new_main), encoding="utf-8")
    APPENDIX.write_text(new_app_text, encoding="utf-8")

    print(f"main.tex: {len(new_main)} lines, {MAIN.stat().st_size} bytes")
    print(f"appendix.tex: {APPENDIX.stat().st_size} bytes")


if __name__ == "__main__":
    main()
