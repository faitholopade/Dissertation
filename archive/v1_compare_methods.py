"""
compare_methods.py — Three-way comparison: keyword vs LLM vs hybrid.

Reads master_annotation_table_llm.csv (which has both keyword and LLM columns)
and computes agreement metrics for each method against the other, plus a
hybrid (keyword wins if not unknown, else LLM) column.

Outputs: method_comparison_results.csv
"""

import os
import sys
import pandas as pd
from sklearn.metrics import cohen_kappa_score, classification_report


def agreement_stats(gold, pred, label=""):
    """Compute percent agreement and Cohen's kappa."""
    mask = gold.notna() & pred.notna() & (gold != "") & (pred != "")
    g = gold[mask].astype(str)
    p = pred[mask].astype(str)
    if len(g) < 2:
        return {"label": label, "n": len(g), "pct_agree": None, "kappa": None}
    if len(set(g)) == 1 and len(set(p)) == 1:
        pct = float((g == p).mean())
        return {"label": label, "n": int(len(g)), "pct_agree": round(pct, 4),
                "kappa": "undefined"}
    return {
        "label": label,
        "n": int(len(g)),
        "pct_agree": round(float((g == p).mean()), 4),
        "kappa": round(float(cohen_kappa_score(g, p)), 4),
    }


def main():
    csv_path = "master_annotation_table_llm.csv"
    if not os.path.exists(csv_path):
        sys.exit(f"ERROR: {csv_path} not found. Run llm_annotate.py first.")

    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} rows from {csv_path}\n")

    # ── Build hybrid column (keyword wins if not unknown, else LLM) ──
    df["hybrid_annex_domain"] = df.apply(
        lambda r: r["annex_domain"] if r["annex_domain"] != "unknown"
                  else r["llm_annex_domain"], axis=1
    )
    df["hybrid_system_pattern"] = df.apply(
        lambda r: r["system_pattern"] if r["system_pattern"] != "unknown"
                  else r["llm_system_pattern"], axis=1
    )

    results = []

    # ── Compare keyword vs LLM on annex_domain ───────────────
    print("=" * 60)
    print("ANNEX DOMAIN: Keyword vs LLM")
    print("=" * 60)
    res = agreement_stats(df["annex_domain"], df["llm_annex_domain"], "domain_kw_vs_llm")
    print(res)
    results.append(res)

    # Count how often they differ
    diff_mask = df["annex_domain"] != df["llm_annex_domain"]
    print(f"\nDisagreements: {diff_mask.sum()} / {len(df)}")
    if diff_mask.any():
        print(df.loc[diff_mask, ["title", "annex_domain", "llm_annex_domain"]].head(15).to_string())

    # ── Compare keyword vs LLM on system_pattern ──────────────
    print("\n" + "=" * 60)
    print("SYSTEM PATTERN: Keyword vs LLM")
    print("=" * 60)
    res = agreement_stats(df["system_pattern"], df["llm_system_pattern"], "pattern_kw_vs_llm")
    print(res)
    results.append(res)

    # ── Domain distribution per method ────────────────────────
    print("\n" + "=" * 60)
    print("DOMAIN DISTRIBUTION BY METHOD")
    print("=" * 60)
    for col, name in [("annex_domain", "Keyword"),
                       ("llm_annex_domain", "LLM"),
                       ("hybrid_annex_domain", "Hybrid")]:
        print(f"\n{name}:")
        print(df[col].value_counts().to_string())

    # ── Pattern distribution per method ───────────────────────
    print("\n" + "=" * 60)
    print("SYSTEM PATTERN DISTRIBUTION BY METHOD")
    print("=" * 60)
    for col, name in [("system_pattern", "Keyword"),
                       ("llm_system_pattern", "LLM"),
                       ("hybrid_system_pattern", "Hybrid")]:
        print(f"\n{name}:")
        print(df[col].value_counts().to_string())

    # ── Summary of unknown rates ──────────────────────────────
    print("\n" + "=" * 60)
    print("UNKNOWN RATES")
    print("=" * 60)
    for col, name in [("annex_domain", "Keyword domain"),
                       ("llm_annex_domain", "LLM domain"),
                       ("hybrid_annex_domain", "Hybrid domain"),
                       ("system_pattern", "Keyword pattern"),
                       ("llm_system_pattern", "LLM pattern"),
                       ("hybrid_system_pattern", "Hybrid pattern")]:
        unk = (df[col] == "unknown").sum()
        print(f"  {name}: {unk}/{len(df)} ({100*unk/len(df):.1f}%)")

    # Save comparison CSV
    out_df = pd.DataFrame(results)
    out_df.to_csv("method_comparison_results.csv", index=False)
    print(f"\n✅ Saved method_comparison_results.csv")

    # Save enriched table with hybrid columns
    df.to_csv("master_annotation_table_hybrid.csv", index=False)
    print(f"✅ Saved master_annotation_table_hybrid.csv")


if __name__ == "__main__":
    main()
