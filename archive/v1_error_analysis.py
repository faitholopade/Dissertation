# error_analysis.py — Detailed error analysis for the dissertation (Ch 5.3).

import os
import sys
import pandas as pd
import numpy as np
from sklearn.metrics import (
    confusion_matrix, classification_report, cohen_kappa_score,
)
from collections import Counter


def print_confusion(gold, pred, labels, title=""):
    cm = confusion_matrix(gold, pred, labels=labels)
    df_cm = pd.DataFrame(cm, index=labels, columns=labels)
    print(f"\n{'='*60}")
    print(f"CONFUSION MATRIX: {title}")
    print(f"{'='*60}")
    print(f"Rows = keyword, Columns = LLM\n")
    print(df_cm.to_string())
    return df_cm


def analyse_disagreements(df, kw_col, llm_col, title_col="title", desc_col="description"):
    mask = df[kw_col].astype(str) != df[llm_col].astype(str)
    cols = [title_col, kw_col, llm_col, desc_col]
    cols = [c for c in cols if c in df.columns]
    return df.loc[mask, cols].copy()


def rights_harms_analysis(df, kw_col, llm_col, all_labels, name=""):
    print(f"\n{'='*60}")
    print(f"PER-LABEL AGREEMENT: {name}")
    print(f"{'='*60}")
    results = []
    for label in all_labels:
        kw_has  = df[kw_col].astype(str).str.contains(label, na=False).astype(int)
        llm_has = df[llm_col].astype(str).str.contains(label, na=False).astype(int)
        agree = (kw_has == llm_has).mean()
        both   = ((kw_has == 1) & (llm_has == 1)).sum()
        kw_only  = ((kw_has == 1) & (llm_has == 0)).sum()
        llm_only = ((kw_has == 0) & (llm_has == 1)).sum()
        neither  = ((kw_has == 0) & (llm_has == 0)).sum()
        results.append({
            "label": label, "agree": round(agree, 3),
            "both": both, "kw_only": kw_only, "llm_only": llm_only, "neither": neither,
        })
        print(f"  {label:30s}  agree={agree:.3f}  both={both}  kw_only={kw_only}  llm_only={llm_only}")
    return pd.DataFrame(results)


def main():
    csv_path = "master_annotation_table_llm.csv"
    if not os.path.exists(csv_path):
        sys.exit(f"ERROR: {csv_path} not found. Run llm_annotate.py first.")

    df = pd.read_csv(csv_path).fillna("")
    print(f"Loaded {len(df)} rows from {csv_path}\n")

    report_lines = []
    def log(msg):
        print(msg)
        report_lines.append(msg)

    domain_labels = ["employment", "essential_services", "unknown"]
    cm_domain = print_confusion(
        df["annex_domain"], df["llm_annex_domain"],
        labels=domain_labels, title="Annex Domain"
    )
    report_lines.append(cm_domain.to_string())

    log("\nClassification report (keyword as reference, LLM as prediction):")
    cr = classification_report(
        df["annex_domain"], df["llm_annex_domain"],
        labels=domain_labels, zero_division=0,
    )
    log(cr)

    pattern_labels = sorted(set(df["system_pattern"].tolist() + df["llm_system_pattern"].tolist()))
    cm_pattern = print_confusion(
        df["system_pattern"], df["llm_system_pattern"],
        labels=pattern_labels, title="System Pattern"
    )
    report_lines.append(cm_pattern.to_string())

    log("\nClassification report (system pattern):")
    cr2 = classification_report(
        df["system_pattern"], df["llm_system_pattern"],
        labels=pattern_labels, zero_division=0,
    )
    log(cr2)

    log(f"\n{'='*60}")
    log("DOMAIN DISAGREEMENT EXAMPLES (keyword vs LLM)")
    log(f"{'='*60}")
    disag = analyse_disagreements(df, "annex_domain", "llm_annex_domain")
    log(f"Total disagreements: {len(disag)} / {len(df)}")
    if not disag.empty:
        for _, row in disag.head(10).iterrows():
            log(f"\n  Title: {row.get('title','')[:80]}")
            log(f"  Keyword: {row['annex_domain']}  |  LLM: {row['llm_annex_domain']}")
            log(f"  Desc: {str(row.get('description',''))[:120]}...")

    rights_labels = [
        "privacy_data_protection", "non_discrimination",
        "access_social_protection", "good_administration", "other"
    ]
    rights_df = rights_harms_analysis(df, "rights", "llm_rights", rights_labels, "Rights")
    rights_df.to_csv("error_analysis_rights.csv", index=False)

    harms_labels = [
        "unfair_exclusion", "privacy_breach",
        "misinformation_error", "procedural_unfairness", "other"
    ]
    harms_df = rights_harms_analysis(df, "harms", "llm_harms", harms_labels, "Harms")
    harms_df.to_csv("error_analysis_harms.csv", index=False)

    cm_domain.to_csv("confusion_matrix_domain.csv")
    cm_pattern.to_csv("confusion_matrix_pattern.csv")
    disag.to_csv("disagreement_examples.csv", index=False)

    with open("error_analysis_report.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"\n[OK] Saved: confusion_matrix_domain.csv, confusion_matrix_pattern.csv")
    print(f"[OK] Saved: disagreement_examples.csv, error_analysis_report.txt")
    print(f"[OK] Saved: error_analysis_rights.csv, error_analysis_harms.csv")


if __name__ == "__main__":
    main()
