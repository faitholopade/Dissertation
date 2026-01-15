#!/usr/bin/env python3
"""
compare_methods_v2.py  –  Extended method comparison for v2 annotations.

Compares keyword vs LLM v2 vs hybrid v2, including the expanded
system_pattern taxonomy.

Run:
    python compare_methods_v2.py
Inputs:
    master_annotation_table_llm_v2.csv
Outputs:
    method_comparison_results_v2.csv
    master_annotation_table_final.csv
"""

import pandas as pd
import numpy as np
import os, sys, warnings
warnings.filterwarnings("ignore")

from sklearn.metrics import cohen_kappa_score, classification_report


def safe_kappa(y1, y2):
    try:
        if len(set(y1)) <= 1 and len(set(y2)) <= 1:
            return 1.0
        return cohen_kappa_score(y1, y2)
    except:
        return float("nan")


def compare_single(df, col1, col2, label):
    """Compare two columns and return metrics."""
    mask = df[col1].notna() & df[col2].notna()
    y1 = df.loc[mask, col1].astype(str).values
    y2 = df.loc[mask, col2].astype(str).values

    n = len(y1)
    pa = sum(a == b for a, b in zip(y1, y2)) / n if n > 0 else 0
    k = safe_kappa(y1, y2)
    unk1 = sum(1 for v in y1 if v == "unknown") / n if n > 0 else 0
    unk2 = sum(1 for v in y2 if v == "unknown") / n if n > 0 else 0

    return {
        "label": label,
        "n": n,
        "pct_agree": round(pa, 4),
        "kappa": round(k, 4),
        "unknown_rate_1": round(unk1, 4),
        "unknown_rate_2": round(unk2, 4),
    }


def main():
    for path in ["output/master_annotation_table_llm_v2.csv",
                  "output/master_annotation_table_llm.csv"]:
        if os.path.exists(path):
            df = pd.read_csv(path)
            print(f"Loaded {len(df)} rows from {path}")
            break
    else:
        print("⚠ No LLM-annotated table found!")
        sys.exit(1)

    results = []

    # ── Domain comparisons ──
    print("\n" + "=" * 60)
