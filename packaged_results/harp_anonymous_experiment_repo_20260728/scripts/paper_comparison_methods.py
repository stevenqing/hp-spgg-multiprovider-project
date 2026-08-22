"""Shared core method colors used across the HARP paper figures."""

from __future__ import annotations


METHOD_ORDER = ("pact_family", "llm_psrl", "atom_tom1", "econ_bne")
METHOD_LABELS = {
    "pact_family": "HARP family (ours)",
    "llm_psrl": "LLM-PSRL",
    "atom_tom1": "A-ToM-1",
    "econ_bne": "ECON-BNE",
}
METHOD_COLORS = {
    "pact_family": "#12345D",
    "llm_psrl": "#2F7D5B",
    "atom_tom1": "#D4A04A",
    "econ_bne": "#B64B45",
}
METHOD_MARKERS = {
    "pact_family": "o",
    "llm_psrl": "D",
    "atom_tom1": "^",
    "econ_bne": "s",
}
ORACLE_LABEL = "Oracle reference"
ORACLE_COLOR = "#303030"
ORACLE_LINESTYLE = (0, (4, 2.4))
