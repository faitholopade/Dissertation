#!/usr/bin/env python3
"""
08_fria_demo_scenarios.py — FRIA-Style Retrieval Demonstrations (Section 5.4)
─────────────────────────────────────────────────────────────────────────────
Queries the hybrid-annotated CSV table to surface relevant incidents for
five hypothetical deployer FRIA scenarios.  Searches across ALL domain,
pattern, rights, and harms columns (keyword, LLM v2, and hybrid) to
maximise retrieval recall.

Outputs
  output/fria_scenario_results.csv    – all matched rows with scenario tags
  output/fria_scenario_summary.txt    – full human-readable report
  figures/fig_fria_scenario_hits.png  – bar chart of hits per scenario

Usage
  python src/08_fria_demo_scenarios.py
"""

import os, sys, csv, textwrap
from pathlib import Path
from collections import Counter

import pandas as pd

# ── paths ─────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent.parent
SRC  = Path(__file__).resolve().parent

CSV_CANDIDATES = [
    BASE / "output" / "master_annotation_table_final.csv",
    BASE / "output" / "master_annotation_table_llm_v2.csv",
    BASE / "data"   / "master_annotation_table_v05.csv",
    BASE / "master_annotation_table_hybrid.csv",
    BASE / "master_annotation_table_llm.csv",
    BASE / "master_annotation_table.csv",
]
OUT_CSV = BASE / "output" / "fria_scenario_results.csv"
OUT_TXT = BASE / "output" / "fria_scenario_summary.txt"
FIG_OUT = BASE / "figures" / "fig_fria_scenario_hits.png"


# ══════════════════════════════════════════════════════════════
#  DATA LOADING
# ══════════════════════════════════════════════════════════════

def load_table():
    """Load the best available annotation table (CSV)."""
    for path in CSV_CANDIDATES:
        if path.exists():
            df = pd.read_csv(path).fillna("")
            print(f"  Loaded {len(df)} records from {path.name}")
            return df
    sys.exit("ERROR: No annotation table CSV found. Run steps 1-2 first.")


# ══════════════════════════════════════════════════════════════
#  MULTI-COLUMN SEARCH HELPERS
#  Each helper checks ALL column variants (keyword, LLM, hybrid)
#  so a record matches if ANY annotation layer tagged it.
# ══════════════════════════════════════════════════════════════

DOMAIN_COLS  = ["annex_domain", "llm_annex_domain", "llm_v2_annex_domain",
                "hybrid_annex_domain", "hybrid_v2_annex_domain"]
PATTERN_COLS = ["system_pattern", "llm_system_pattern", "llm_v2_system_pattern",
                "hybrid_system_pattern", "hybrid_v2_system_pattern"]
RIGHTS_COLS  = ["rights", "llm_rights", "llm_v2_rights"]
HARMS_COLS   = ["harms", "llm_harms", "llm_v2_harms"]


def _any_col_equals(row, col_names, target):
    """True if any of the listed columns exactly equals `target`."""
    for col in col_names:
        if col in row.index and str(row[col]).strip().lower() == target.lower():
            return True
    return False


def _any_col_contains(row, col_names, targets):
    """True if any column contains any of the target substrings."""
    if isinstance(targets, str):
        targets = [targets]
    for col in col_names:
        if col in row.index:
            val = str(row[col]).strip().lower()
            for t in targets:
                if t.lower() in val:
                    return True
    return False


def search_cases(df, annex_domain=None, pattern_contains=None,
                 right_contains=None, harm_contains=None):
    """
    Filter the DataFrame using multi-column OR logic.
    Mirrors the approach in fria_demo.py but extended to v2 columns.
    """
    out = df.copy()

    if annex_domain:
        cols = [c for c in DOMAIN_COLS if c in out.columns]
        mask = pd.Series(False, index=out.index)
        for col in cols:
            mask |= (out[col].astype(str).str.strip().str.lower() == annex_domain.lower())
        out = out[mask]

    if pattern_contains:
        targets = pattern_contains if isinstance(pattern_contains, list) else [pattern_contains]
        cols = [c for c in PATTERN_COLS if c in out.columns]
        mask = pd.Series(False, index=out.index)
        for col in cols:
            for t in targets:
                mask |= out[col].astype(str).str.contains(t, case=False, na=False)
        out = out[mask]

    if right_contains:
        cols = [c for c in RIGHTS_COLS if c in out.columns]
        mask = pd.Series(False, index=out.index)
        for col in cols:
            mask |= out[col].astype(str).str.contains(right_contains, case=False, na=False)
        out = out[mask]

    if harm_contains:
        cols = [c for c in HARMS_COLS if c in out.columns]
        mask = pd.Series(False, index=out.index)
        for col in cols:
            mask |= out[col].astype(str).str.contains(harm_contains, case=False, na=False)
        out = out[mask]

    return out


def _best_val(row, col_names, fallback="unknown"):
    """Return first non-empty, non-unknown value from a list of columns."""
    for col in col_names:
        if col in row.index:
            v = str(row[col]).strip().lower()
            if v and v not in ("", "unknown", "nan"):
                return v
    return fallback


# ══════════════════════════════════════════════════════════════
#  DISPLAY HELPERS
# ══════════════════════════════════════════════════════════════

SHOW_COLS = ["source", "source_id", "title", "annex_domain",
             "system_pattern", "rights", "harms"]

def _show(subset, report):
    """Print and log a markdown table of up to 15 hits."""
