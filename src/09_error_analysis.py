#!/usr/bin/env python3
"""
09_error_analysis.py — Comprehensive Error Analysis (Section 5.3)
─────────────────────────────────────────────────────────────────
Merges TWO complementary analyses into one pipeline step:

  Part A: Gold-standard (manual) vs all automated methods
          — from manual_vs_llm_comparison.csv matched against
            keyword, LLM v2, and hybrid tables
          — categorises WHY each disagreement occurred

  Part B: Keyword vs LLM on the full 150-row master table
          — confusion matrices for domain + system pattern
          — per-label precision / recall / F1
          — disagreement example extraction

  Part C: Per-label rights and harms agreement
          — keyword vs LLM on rights and harms multi-label fields

  Part D: Qualitative theme summary
          — synthesises error patterns into narrative themes
            suitable for the dissertation discussion

Outputs
  output/error_analysis_disagreements.csv   – Part A rows
  output/error_analysis_report.txt          – full text report
  output/confusion_matrix_domain.csv        – Part B domain CM
  output/confusion_matrix_pattern.csv       – Part B pattern CM
  output/disagreement_examples.csv          – Part B domain disagreements
  output/error_analysis_rights.csv          – Part C rights agreement
  output/error_analysis_harms.csv           – Part C harms agreement
  figures/fig_error_categories.png          – Part A bar chart
  figures/fig_error_heatmap.png             – Part A method × error-type

Usage
  python src/09_error_analysis.py
"""

import os, sys, csv, textwrap
from pathlib import Path
from collections import Counter, defaultdict

import pandas as pd
import numpy as np

try:
    from sklearn.metrics import (
        confusion_matrix, classification_report, cohen_kappa_score,
    )
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("  ⚠  sklearn not available — Part B metrics will be limited")


# ── paths ─────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent.parent

GOLD_CSV   = BASE / "data"   / "aiaaic" / "manual_vs_llm_comparison.csv"
KW_CSV     = BASE / "data"   / "master_annotation_table_v01.csv"
LLM_CSV    = BASE / "output" / "master_annotation_table_llm_v2.csv"
HYBRID_CSV = BASE / "output" / "master_annotation_table_final.csv"

OUT_DIR = BASE / "output"
FIG_DIR = BASE / "figures"


# ══════════════════════════════════════════════════════════════
#  PART A: GOLD VS AUTOMATED — CATEGORISED DISAGREEMENTS
# ══════════════════════════════════════════════════════════════

def _flag(val):
    """Normalise a boolean-ish field to True/False."""
    return str(val).strip().upper() in ("YES", "TRUE", "1", "Y")


def _manual_domain(row):
    """Derive manual domain label from binary flags."""
    emp = _flag(row.get("manual_annex_employment", ""))
    ess = _flag(row.get("manual_annex_essential", ""))
    if emp and ess:
        return "both"
    elif emp:
        return "employment"
    elif ess:
        return "essential_services"
    return "unknown"


def _pred_domain(emp_val, ess_val):
    """Derive predicted domain from binary flags."""
    emp = _flag(emp_val)
    ess = _flag(ess_val)
    if emp and ess:
        return "both"
    elif emp:
        return "employment"
    elif ess:
        return "essential_services"
    return "unknown"


def categorise_domain_error(manual_domain, pred_domain, method):
    """Return (category, explanation) for a domain disagreement."""
    if manual_domain == pred_domain:
        return None, None

    if manual_domain == "unknown" and pred_domain != "unknown":
        return (
            f"{method}_over_classifies_{pred_domain}",
            f"{method} labelled '{pred_domain}' but manual found neither "
            f"employment nor essential services."
        )
    if pred_domain == "unknown" and manual_domain != "unknown":
        return (
            f"{method}_misses_{manual_domain}",
            f"{method} labelled 'unknown' but manual found '{manual_domain}'."
        )
    if {manual_domain, pred_domain} == {"employment", "essential_services"}:
        return (
            f"{method}_domain_swap",
            f"{method} labelled '{pred_domain}' but manual found "
            f"'{manual_domain}' — domain boundary confusion."
        )
    if manual_domain == "both":
        return (
            f"{method}_partial_match",
            f"{method} labelled '{pred_domain}' but manual marked BOTH "
            f"employment AND essential services."
        )
    return (
        f"{method}_other_mismatch",
        f"{method}='{pred_domain}' vs manual='{manual_domain}'."
    )


def _parse_rights(s):
    """Parse multi-label string into a set."""
    return set(
        t.strip().upper()
        for t in str(s).replace(";", ",").split(",")
        if t.strip() and t.strip().upper() not in ("NAN", "NONE", "")
    )


def categorise_rights_error(manual_str, pred_str, method):
    """Return (category, explanation) for a rights disagreement."""
    m = _parse_rights(manual_str)
    p = _parse_rights(pred_str)
    if m == p:
        return None, None
    extra   = p - m
    missing = m - p
    parts = []
    if extra:
        parts.append(f"over-predicted {extra}")
    if missing:
        parts.append(f"missed {missing}")
    label = f"{method}_rights_"
    if extra and missing:
        label += "over_under"
    elif extra:
        label += "over"
    else:
        label += "under"
    return label, f"{method} rights: {'; '.join(parts)}."


def _id_col(df):
    """Find the ID column in a DataFrame."""
