
# Evaluate automated annotations against Label Studio gold standard

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
    if pd.isna(val):
        return "no"
    val = str(val).strip().lower()
    if val in ["yes", "true", "1", "1.0", "y"]:
        return "yes"
    return "no"


def find_gold_file():
    candidates = [
        "data/aiaaic/manual_vs_llm_comparison.csv",
        "data/aiaaic/manual_vs_llm_comparison.csv",
        "data/aiaaic/manual_vs_llm_comparison.csv",
    ]
    for pattern in candidates:
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
    for root, dirs, files in os.walk("."):
        for f in files:
            if f == "data/aiaaic/manual_vs_llm_comparison.csv":
                return os.path.join(root, f)
    return None


def main():
    print("=" * 60)
    print("GOLD-STANDARD EVALUATION: Manual vs Automated Methods")
    print("=" * 60 + "\n")

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

    manual_emp_col = None
    manual_ess_col = None
    llm_emp_col = None
    llm_ess_col = None
    title_col = None
    id_col = None

    for c in gold.columns:
        cl = c.lower()
        if cl.startswith("manual") and "employ" in cl:
            manual_emp_col = c
        elif cl.startswith("manual") and ("essential" in cl or "annex_essential" in cl):
            manual_ess_col = c
        elif cl.startswith("manual") and "headline" in cl:
            title_col = c
        elif cl.startswith("llm") and "employ" in cl:
            llm_emp_col = c
        elif cl.startswith("llm") and ("essential" in cl or "annex_essential" in cl):
            llm_ess_col = c
        elif "aiaaic" in cl and "id" in cl:
            id_col = c

    print(f"  Manual employment col: {manual_emp_col}")
    print(f"  Manual essential col:  {manual_ess_col}")
    print(f"  LLM employment col:    {llm_emp_col}")
    print(f"  LLM essential col:     {llm_ess_col}")
    print(f"  Title col:             {title_col}")
    print(f"  ID col:                {id_col}\n")

    print("=" * 60)
    print("PART A: Gold (Manual) vs LLM (from comparison file)")
    print("=" * 60)

    if manual_emp_col and llm_emp_col:
        m = gold[manual_emp_col].apply(normalise_binary)
        l = gold[llm_emp_col].apply(normalise_binary)
        mask = m.notna() & l.notna()
        m, l = m[mask], l[mask]

        pa = pct_agree(m, l)
        k = safe_kappa(m, l)
        p = precision_score(m, l, pos_label="yes", zero_division=0)
        r = recall_score(m, l, pos_label="yes", zero_division=0)
        f = f1_score(m, l, pos_label="yes", zero_division=0)

        results.append({
            "comparison": "manual_vs_llm", "dimension": "employment",
            "n": len(m), "pct_agree": round(pa, 4), "kappa": round(k, 4),
            "precision": round(p, 4), "recall": round(r, 4), "f1": round(f, 4),
        })
        print(f"\n  Employment: n={len(m)}, agree={pa:.3f}, κ={k:.3f}, F1={f:.3f}")
        report_lines.append(f"Employment (manual vs LLM): agree={pa:.3f}, κ={k:.3f}, F1={f:.3f}")

    if manual_ess_col and llm_ess_col:
        m = gold[manual_ess_col].apply(normalise_binary)
        l = gold[llm_ess_col].apply(normalise_binary)
        mask = m.notna() & l.notna()
        m, l = m[mask], l[mask]

        pa = pct_agree(m, l)
        k = safe_kappa(m, l)
        p = precision_score(m, l, pos_label="yes", zero_division=0)
        r = recall_score(m, l, pos_label="yes", zero_division=0)
        f = f1_score(m, l, pos_label="yes", zero_division=0)

        results.append({
            "comparison": "manual_vs_llm", "dimension": "essential_services",
            "n": len(m), "pct_agree": round(pa, 4), "kappa": round(k, 4),
            "precision": round(p, 4), "recall": round(r, 4), "f1": round(f, 4),
        })
        print(f"  Essential:  n={len(m)}, agree={pa:.3f}, κ={k:.3f}, F1={f:.3f}")
        report_lines.append(f"Essential (manual vs LLM): agree={pa:.3f}, κ={k:.3f}, F1={f:.3f}")

    print("\n" + "=" * 60)
    print("PART B: Gold (Manual) vs Keyword (matched on AIAAIC_ID)")
    print("=" * 60)

    auto_tables = {}
    for name, candidates in [
        ("keyword", ["data/master_annotation_table_v01.csv"]),
        ("hybrid", ["output/master_annotation_table_hybrid.csv", "output/master_annotation_table_final.csv"]),
        ("llm_v2", ["output/master_annotation_table_llm_v2.csv"]),
    ]:
        for path in candidates:
            if os.path.exists(path):
                auto_tables[name] = pd.read_csv(path, encoding="utf-8")
                print(f"  Loaded {name}: {len(auto_tables[name])} rows from {path}")
                break

    def match_and_compare(gold_df, auto_df, auto_name, gold_id_col, auto_id_col,
                          manual_emp, manual_ess, auto_domain_col):
        if gold_id_col is None or auto_domain_col not in auto_df.columns:
            print(f"  ⚠ Cannot match: missing columns")
            return []

        auto_id = None
        for c in auto_df.columns:
            if "source_id" in c.lower() or "aiaaic_id" in c.lower():
                auto_id = c
                break
        if auto_id is None and "source_id" in auto_df.columns:
            auto_id = "source_id"
        if auto_id is None:
            return match_by_title(gold_df, auto_df, auto_name, manual_emp, manual_ess, auto_domain_col)

        gold_ids = gold_df[gold_id_col].astype(str).str.strip()
        auto_ids = auto_df[auto_id].astype(str).str.strip()

        matched_results = []
        gold_domains = []
        auto_domains = []

        for gi, gid in gold_ids.items():
            auto_match = auto_df[auto_ids == gid]
            if auto_match.empty:
                auto_match = auto_df[auto_ids.str.contains(gid, na=False)]
            if auto_match.empty:
                continue

            auto_row = auto_match.iloc[0]

            emp = normalise_binary(gold_df.loc[gi, manual_emp]) if manual_emp else "no"
            ess = normalise_binary(gold_df.loc[gi, manual_ess]) if manual_ess else "no"

            if emp == "yes":
                gold_domain = "employment"
            elif ess == "yes":
                gold_domain = "essential_services"
            else:
                gold_domain = "unknown"

            auto_domain = str(auto_row.get(auto_domain_col, "unknown"))

            gold_domains.append(gold_domain)
            auto_domains.append(auto_domain)

        if len(gold_domains) < 3:
            print(f"  ⚠ Only {len(gold_domains)} matches found for {auto_name}")
            return []

        pa = pct_agree(gold_domains, auto_domains)
        k = safe_kappa(gold_domains, auto_domains)

        result = {
            "comparison": f"manual_vs_{auto_name}", "dimension": "annex_domain",
            "n": len(gold_domains), "pct_agree": round(pa, 4), "kappa": round(k, 4),
        }
        print(f"  {auto_name} domain: n={len(gold_domains)}, agree={pa:.3f}, κ={k:.3f}")

        labels = sorted(set(gold_domains + auto_domains))
        cm = confusion_matrix(gold_domains, auto_domains, labels=labels)
        print(f"  Confusion matrix (rows=manual, cols={auto_name}):")
        cm_df = pd.DataFrame(cm, index=labels, columns=labels)
        print(cm_df.to_string())
        print()

        return [result]

    def match_by_title(gold_df, auto_df, auto_name, manual_emp, manual_ess, auto_domain_col):
        if title_col is None:
            return []
        auto_title_col = "title" if "title" in auto_df.columns else None
        if auto_title_col is None:
            return []

        gold_titles = gold_df[title_col].astype(str).str.lower().str.strip()
        auto_titles = auto_df[auto_title_col].astype(str).str.lower().str.strip()

        gold_domains = []
        auto_domains = []

        for gi, gt in gold_titles.items():
            gt_short = gt[:40]
            for ai, at in auto_titles.items():
                if gt_short in at or at[:40] in gt:
                    emp = normalise_binary(gold_df.loc[gi, manual_emp]) if manual_emp else "no"
                    ess = normalise_binary(gold_df.loc[gi, manual_ess]) if manual_ess else "no"

                    if emp == "yes":
                        gold_domain = "employment"
                    elif ess == "yes":
                        gold_domain = "essential_services"
                    else:
                        gold_domain = "unknown"

                    gold_domains.append(gold_domain)
                    auto_domains.append(str(auto_df.loc[ai, auto_domain_col]))
                    break

        if len(gold_domains) < 3:
            return []

        pa = pct_agree(gold_domains, auto_domains)
        k = safe_kappa(gold_domains, auto_domains)
        result = {
            "comparison": f"manual_vs_{auto_name}", "dimension": "annex_domain",
            "n": len(gold_domains), "pct_agree": round(pa, 4), "kappa": round(k, 4),
        }
        print(f"  {auto_name} domain (title-matched): n={len(gold_domains)}, agree={pa:.3f}, κ={k:.3f}")
        return [result]

    for auto_name, domain_col_options in [
        ("keyword", ["annex_domain"]),
        ("hybrid", ["hybrid_annex_domain", "annex_domain"]),
        ("llm_v2", ["llm_v2_annex_domain", "llm_annex_domain"]),
    ]:
        if auto_name not in auto_tables:
            continue
        adf = auto_tables[auto_name]
        dcol = None
        for dc in domain_col_options:
            if dc in adf.columns:
                dcol = dc
                break
        if dcol is None:
            continue

        r = match_and_compare(gold, adf, auto_name, id_col, None,
                              manual_emp_col, manual_ess_col, dcol)
        results.extend(r)

    print("=" * 60)
    print("PART C: Gold (Manual) vs Keyword Hits (from comparison file)")
    print("=" * 60)

    if "kw_emp_hits" in gold.columns and manual_emp_col:
        kw_emp = (gold["kw_emp_hits"] > 0).map({True: "yes", False: "no"})
        m_emp = gold[manual_emp_col].apply(normalise_binary)

        pa = pct_agree(m_emp, kw_emp)
        k = safe_kappa(m_emp, kw_emp)
        results.append({
            "comparison": "manual_vs_keyword_hits", "dimension": "employment",
            "n": len(m_emp), "pct_agree": round(pa, 4), "kappa": round(k, 4),
        })
        print(f"  Employment (kw_hits>0): n={len(m_emp)}, agree={pa:.3f}, κ={k:.3f}")

    if "kw_ben_hits" in gold.columns and manual_ess_col:
        kw_ess = (gold["kw_ben_hits"] > 0).map({True: "yes", False: "no"})
        m_ess = gold[manual_ess_col].apply(normalise_binary)

        pa = pct_agree(m_ess, kw_ess)
        k = safe_kappa(m_ess, kw_ess)
        results.append({
            "comparison": "manual_vs_keyword_hits", "dimension": "essential_services",
            "n": len(m_ess), "pct_agree": round(pa, 4), "kappa": round(k, 4),
        })
        print(f"  Essential (kw_hits>0):  n={len(m_ess)}, agree={pa:.3f}, κ={k:.3f}")

    print("\n" + "=" * 60)
    print("SUMMARY: All Methods vs Gold Standard")
    print("=" * 60)

    results_df = pd.DataFrame(results)
    if len(results_df) > 0:
        print(results_df.to_string(index=False))
        results_df.to_csv("output/gold_evaluation_results.csv", index=False, encoding="utf-8")
        print("output/gold_evaluation_results.csv")

        summary_df = results_df.copy()
        summary_df["pct_agree"] = summary_df["pct_agree"].apply(lambda x: f"{x:.1%}")
        summary_df["kappa"] = summary_df["kappa"].apply(lambda x: f"{x:.3f}")
        for col in ["precision", "recall", "f1"]:
            if col in summary_df.columns:
                summary_df[col] = summary_df[col].apply(
                    lambda x: f"{x:.3f}" if pd.notna(x) else "–")

        summary_df.to_csv("output/gold_evaluation_summary.csv", index=False, encoding="utf-8")
        print("output/gold_evaluation_summary.csv")
    else:
        print("⚠ No evaluation results produced!")
        print("  Check that gold file columns match expected format.")

    with open("output/gold_confusion_matrices.txt", "w", encoding="utf-8") as f:
        f.write("GOLD-STANDARD EVALUATION REPORT\n")
        f.write("=" * 60 + "\n\n")
        for line in report_lines:
            f.write(line + "\n")
        f.write("\nFull results:\n")
        if len(results_df) > 0:
            f.write(results_df.to_string(index=False))
    print("output/gold_confusion_matrices.txt")


if __name__ == "__main__":
    main()
