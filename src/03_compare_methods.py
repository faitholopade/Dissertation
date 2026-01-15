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
    print("DOMAIN COMPARISONS")
    print("=" * 60)

    pairs = [
        ("annex_domain", "llm_annex_domain", "domain_kw_vs_llm_v1"),
        ("annex_domain", "llm_v2_annex_domain", "domain_kw_vs_llm_v2"),
    ]
    for c1, c2, label in pairs:
        if c1 in df.columns and c2 in df.columns:
            r = compare_single(df, c1, c2, label)
            results.append(r)
            print(f"  {label}: agree={r['pct_agree']:.3f}, κ={r['kappa']:.3f}")

    # ── Pattern comparisons ──
    print("\n" + "=" * 60)
    print("SYSTEM PATTERN COMPARISONS")
    print("=" * 60)

    pairs = [
        ("system_pattern", "llm_system_pattern", "pattern_kw_vs_llm_v1"),
        ("system_pattern", "llm_v2_system_pattern", "pattern_kw_vs_llm_v2"),
    ]
    for c1, c2, label in pairs:
        if c1 in df.columns and c2 in df.columns:
            r = compare_single(df, c1, c2, label)
            results.append(r)
            print(f"  {label}: agree={r['pct_agree']:.3f}, κ={r['kappa']:.3f}")

    # ── Distribution summaries ──
    print("\n" + "=" * 60)
    print("DISTRIBUTION SUMMARIES")
    print("=" * 60)

    for col in ["annex_domain", "llm_v2_annex_domain", "hybrid_v2_annex_domain",
                "system_pattern", "llm_v2_system_pattern", "hybrid_v2_system_pattern"]:
        if col in df.columns:
            print(f"\n{col}:")
            print(df[col].value_counts().to_string())

    # ── Unknown rate improvement ──
    print("\n" + "=" * 60)
    print("UNKNOWN RATE COMPARISON (v1 vs v2)")
    print("=" * 60)

    for dim, v1_col, v2_col in [
        ("domain", "llm_annex_domain", "llm_v2_annex_domain"),
        ("pattern", "llm_system_pattern", "llm_v2_system_pattern"),
    ]:
        rates = {}
        for label, col in [("v1", v1_col), ("v2", v2_col)]:
            if col in df.columns:
                unk = (df[col] == "unknown").sum()
                rates[label] = f"{unk}/{len(df)} ({unk/len(df):.1%})"
        if rates:
            print(f"  {dim}: " + " → ".join(f"{k}: {v}" for k, v in rates.items()))

    # Save results
    results_df = pd.DataFrame(results)
    results_df.to_csv("output/method_comparison_results_v2.csv", index=False)
    print(f"output/method_comparison_results_v2.csv")

    # Save final combined table
    df.to_csv("output/master_annotation_table_final.csv", index=False)
    print(f"✅ Saved master_annotation_table_final.csv ({len(df)} rows)")


if __name__ == "__main__":
    main()
