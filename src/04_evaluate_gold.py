#!/usr/bin/env python3
"""
evaluate_gold.py  –  Compare Label Studio gold annotations against
                     keyword, LLM, and hybrid automated annotations.

Expects:
  - manual_vs_llm_comparison.csv  (Label Studio pilot export with manual labels)
  - master_annotation_table_llm.csv / _llm_v2.csv  (keyword + LLM labels)
  - master_annotation_table_hybrid.csv  (hybrid labels)

Run:
    python evaluate_gold.py
Outputs:
    gold_evaluation_results.csv
    gold_evaluation_summary.csv
    gold_confusion_matrices.txt
"""

import pandas as pd
import numpy as np
import os, sys, glob, warnings
warnings.filterwarnings("ignore")

from sklearn.metrics import (
    cohen_kappa_score, classification_report,
    confusion_matrix, f1_score, precision_score, recall_score
)


def safe_kappa(y1, y2):
    try:
        if len(set(y1)) <= 1 and len(set(y2)) <= 1:
            return 1.0 if list(y1) == list(y2) else 0.0
        return cohen_kappa_score(y1, y2)
    except Exception:
        return float("nan")


def pct_agree(y1, y2):
    y1, y2 = list(y1), list(y2)
    return sum(a == b for a, b in zip(y1, y2)) / len(y1) if y1 else 0


def normalise_binary(val):
    """Convert various yes/no/1/0/True/False to 'yes'/'no'."""
    if pd.isna(val):
        return "no"
    val = str(val).strip().lower()
    if val in ["yes", "true", "1", "1.0", "y"]:
        return "yes"
    return "no"


# ─── Find gold file ────────────────────────────────────────────
def find_gold_file():
    """Search for the manual_vs_llm_comparison.csv file."""
    candidates = [
        "data/aiaaic/manual_vs_llm_comparison.csv",
        "data/aiaaic/manual_vs_llm_comparison.csv",
        "data/aiaaic/manual_vs_llm_comparison.csv",
    ]
    for pattern in candidates:
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
    # Recursive search
    for root, dirs, files in os.walk("."):
        for f in files:
            if f == "data/aiaaic/manual_vs_llm_comparison.csv":
                return os.path.join(root, f)
    return None


def main():
    print("=" * 60)
    print("GOLD-STANDARD EVALUATION: Manual vs Automated Methods")
    print("=" * 60 + "\n")

    # ── Load gold data ──
    gold_path = find_gold_file()
    if not gold_path:
        print("⚠ Could not find manual_vs_llm_comparison.csv!")
        print("  Searched current directory and subdirectories.")
        sys.exit(1)

    gold = pd.read_csv(gold_path, encoding="utf-8")
    print(f"  Gold data: {len(gold)} rows from {gold_path}")
    print(f"  Columns: {list(gold.columns)}\n")

    results = []
    report_lines = []

    # ── Identify columns explicitly ──
    # Based on actual file: manual_annex_employment, manual_annex_essential,
    #   llm_annex_employment, llm_annex_essential, manual_headline, AIAAIC_ID
    manual_emp_col = None
    manual_ess_col = None
    llm_emp_col = None
    llm_ess_col = None
    title_col = None
    id_col = None

    for c in gold.columns:
        cl = c.lower()
        # Manual columns: must start with 'manual' and NOT be headline/rights
        if cl.startswith("manual") and "employ" in cl:
            manual_emp_col = c
        elif cl.startswith("manual") and ("essential" in cl or "annex_essential" in cl):
            manual_ess_col = c
        elif cl.startswith("manual") and "headline" in cl:
            title_col = c
        # LLM columns: must start with 'llm'
        elif cl.startswith("llm") and "employ" in cl:
            llm_emp_col = c
        elif cl.startswith("llm") and ("essential" in cl or "annex_essential" in cl):
            llm_ess_col = c
        # ID column
        elif "aiaaic" in cl and "id" in cl:
            id_col = c

    print(f"  Manual employment col: {manual_emp_col}")
    print(f"  Manual essential col:  {manual_ess_col}")
    print(f"  LLM employment col:    {llm_emp_col}")
    print(f"  LLM essential col:     {llm_ess_col}")
    print(f"  Title col:             {title_col}")
    print(f"  ID col:                {id_col}\n")

    # ═══════════════════════════════════════════════════════════
    # PART A: Gold vs LLM (from the comparison file itself)
    # ═══════════════════════════════════════════════════════════
    print("=" * 60)
    print("PART A: Gold (Manual) vs LLM (from comparison file)")
    print("=" * 60)

    if manual_emp_col and llm_emp_col:
        m = gold[manual_emp_col].apply(normalise_binary)
        l = gold[llm_emp_col].apply(normalise_binary)
        mask = m.notna() & l.notna()
        m, l = m[mask], l[mask]

