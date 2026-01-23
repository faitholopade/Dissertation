#!/usr/bin/env python3
"""
07b_alternative_figures.py
──────────────────────────
Generates alternative visualisations for the two figures that
07_generate_figures.py could not produce due to insufficient data:
  - fig_rights_agreement.png  →  fig_rights_distribution.png
  - fig_harms_agreement.png   →  fig_harms_distribution.png

Instead of agreement charts (which require paired annotations),
these show the *distribution* of rights and harms labels across
the corpus, which is still informative for Sections 5.2 / 5.3.

Also generates:
  - fig_rights_by_domain.png  – stacked bar: rights × domain
  - fig_harms_by_pattern.png  – heatmap: harms × system pattern

Outputs to figures/.
"""

import os, sys, re
from pathlib import Path
from collections import Counter

import pandas as pd
import numpy as np

BASE     = Path(__file__).resolve().parent.parent
LLM_CSV  = BASE / "output" / "master_annotation_table_llm_v2.csv"
GOLD_CSV = BASE / "data" / "aiaaic" / "manual_vs_llm_comparison.csv"
FIG_DIR  = BASE / "figures"

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns
except ImportError:
    sys.exit("matplotlib / seaborn required")


def load():
    df = pd.read_csv(LLM_CSV) if LLM_CSV.exists() else pd.DataFrame()
    gold = pd.read_csv(GOLD_CSV) if GOLD_CSV.exists() else pd.DataFrame()
    print(f"  Loaded {len(df)} annotated records, {len(gold)} gold rows")
    return df, gold


def _explode_multi(series, sep=","):
    """Split multi-label strings and return a flat Counter."""
    c = Counter()
    for val in series.dropna():
        for part in str(val).split(sep):
            part = part.strip().upper()
            if part and part not in ("NAN", "NONE", "UNKNOWN", ""):
                c[part] += 1
    return c


# ── Figure A: Rights distribution across corpus ──────────────
def fig_rights_distribution(df, gold):
    """
    Combine rights labels from gold file and from the LLM v2 table
    (if a rights column exists) into a single distribution bar chart.
    """
    rights_counts = Counter()

    # Gold file has manual_rights and llm_rights
    if "manual_rights" in gold.columns:
        rights_counts.update(_explode_multi(gold["manual_rights"]))
    if "llm_rights" in gold.columns:
        rights_counts.update(_explode_multi(gold["llm_rights"]))

    # LLM v2 table may have a rights column
    for col in ("rights", "rights_categories", "llm_v2_rights"):
        if col in df.columns:
            rights_counts.update(_explode_multi(df[col]))
            break

    if not rights_counts:
        # Synthesise from gold-file binary flags
        if "manual_annex_employment" in gold.columns:
            emp_yes = gold[gold["manual_annex_employment"].astype(str).str.upper().isin(["YES","TRUE","1","Y"])]
            ess_yes = gold[gold["manual_annex_essential"].astype(str).str.upper().isin(["YES","TRUE","1","Y"])]
            rights_counts["NON-DISCRIMINATION (employment-linked)"] = len(emp_yes)
            rights_counts["PRIVACY / DATA-PROTECTION (services-linked)"] = len(ess_yes)
            # Infer from keyword hits
            if "kw_emp_hits" in gold.columns:
                rights_counts["NON-DISCRIMINATION (kw-inferred)"] = int((gold["kw_emp_hits"].fillna(0) > 0).sum())
            if "kw_ben_hits" in gold.columns:
                rights_counts["SOCIAL PROTECTION (kw-inferred)"] = int((gold["kw_ben_hits"].fillna(0) > 0).sum())

    if not rights_counts:
        print("  ⚠  No rights data found – cannot generate rights distribution")
        return

    labels, values = zip(*rights_counts.most_common())
    short = [l[:35] for l in labels]

    fig, ax = plt.subplots(figsize=(9, max(4, len(labels) * 0.5)))
    ax.barh(short[::-1], values[::-1], color="#5B9BD5")
    ax.set_xlabel("Frequency (across gold + LLM annotations)")
    ax.set_title("Rights Label Distribution Across Annotated Records")
    plt.tight_layout()
    out = FIG_DIR / "fig_rights_distribution.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  ✅ {out}")


# ── Figure B: Harms distribution ─────────────────────────────
def fig_harms_distribution(df, gold):
    """
    Show distribution of harm categories.  If explicit harms columns
    are empty, derive harms from system_pattern / domain combinations.
    """
    harms_counts = Counter()

    # Try explicit harms columns
    for col in ("harms", "harm_categories", "llm_v2_harms"):
        if col in df.columns:
            harms_counts.update(_explode_multi(df[col]))
            break

    # If nothing found, derive proxy harms from domain × pattern
    if not harms_counts:
        # Map system patterns to likely harm categories
        pattern_to_harm = {
            "profiling_scoring":      "Unfair exclusion / Discriminatory profiling",
            "surveillance_monitor":   "Privacy breach / Disproportionate surveillance",
            "resource_allocation":    "Unjust resource denial",
            "classification_triage":  "Misclassification / Erroneous triage",
            "llm_decision_support":   "Hallucination / Misleading output",
            "llm_assisted_screening": "Biased screening / Over-reliance on AI",
            "chatbot":                "Misinformation / Procedural unfairness",
