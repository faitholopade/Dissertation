"""
evaluate_annotations.py — Compute agreement metrics (v0.3).

Evaluates TWO datasets:
  Part A: Original AIAAIC pilot (manual_vs_llm_comparison.csv)
  Part B: Master table keyword-vs-LLM (master_annotation_table_llm.csv)

Outputs agreement stats for each, saves evaluate_results.csv.
"""

import os
import sys
import pandas as pd
from sklearn.metrics import cohen_kappa_score

AIAAIC_DIR = "AIAAIC (AI, algorithmic and automation incidents and controversies)"
COMPARISON_CSV = os.path.join(AIAAIC_DIR, "manual_vs_llm_comparison.csv")
MASTER_LLM_CSV = "master_annotation_table_llm.csv"


def agreement(gold, pred):
    """Percent agreement and Cohen's kappa on two Series."""
    mask = gold.notna() & pred.notna() & (gold != "") & (pred != "")
    g = gold[mask].astype(str)
    p = pred[mask].astype(str)
    if len(g) < 2:
        return {"n": len(g), "percent_agreement": None, "kappa": None}
    if len(set(g)) == 1 and len(set(p)) == 1:
        pct = float((g == p).mean())
        return {"n": int(len(g)), "percent_agreement": round(pct, 4),
                "kappa": "undefined (single label)"}
    return {
        "n": int(len(g)),
        "percent_agreement": round(float((g == p).mean()), 4),
        "kappa": round(float(cohen_kappa_score(g, p)), 4),
    }


def has_right(rights_str, keyword):
    if not isinstance(rights_str, str):
        return "No"
    return "Yes" if keyword.upper() in rights_str.upper() else "No"


def part_a_aiaaic_pilot():
    """Original AIAAIC manual vs LLM comparison."""
    print("=" * 60)
    print("PART A: AIAAIC Pilot (manual_vs_llm_comparison.csv)")
    print("=" * 60)

    if not os.path.exists(COMPARISON_CSV):
        print(f"  Skipping — {COMPARISON_CSV} not found.\n")
        return []

    df = pd.read_csv(COMPARISON_CSV)
    df = df.dropna(subset=["llm_annex_employment", "llm_annex_essential"])
    print(f"  Loaded {len(df)} rows\n")

    results = []

    print("  === Annex III(4) - Employment ===")
    res = agreement(df["manual_annex_employment"], df["llm_annex_employment"])
    res["dataset"] = "AIAAIC_pilot"; res["label"] = "employment"
    print(f"  {res}")
    results.append(res)

    print("\n  === Annex III(5a) - Essential services ===")
    res = agreement(df["manual_annex_essential"], df["llm_annex_essential"])
    res["dataset"] = "AIAAIC_pilot"; res["label"] = "essential_services"
    print(f"  {res}")
    results.append(res)

    print("\n  === Non-discrimination ===")
    df["manual_has_nd"] = df["manual_rights"].apply(lambda x: has_right(x, "NON-DISCRIMINATION"))
    df["llm_has_nd"]    = df["llm_rights"].apply(lambda x: has_right(x, "NON-DISCRIMINATION"))
    res = agreement(df["manual_has_nd"], df["llm_has_nd"])
    res["dataset"] = "AIAAIC_pilot"; res["label"] = "non_discrimination"
    print(f"  {res}")
    results.append(res)

    print("\n  === Privacy ===")
    df["manual_has_priv"] = df["manual_rights"].apply(lambda x: has_right(x, "PRIVACY"))
    df["llm_has_priv"]    = df["llm_rights"].apply(lambda x: has_right(x, "PRIVACY"))
    res = agreement(df["manual_has_priv"], df["llm_has_priv"])
    res["dataset"] = "AIAAIC_pilot"; res["label"] = "privacy"
    print(f"  {res}")
    results.append(res)

    return results


def part_b_master_table():
    """Master annotation table: keyword vs LLM."""
    print("\n" + "=" * 60)
    print("PART B: Master Table (keyword vs LLM)")
    print("=" * 60)

    if not os.path.exists(MASTER_LLM_CSV):
        print(f"  Skipping — {MASTER_LLM_CSV} not found.\n")
        return []

    df = pd.read_csv(MASTER_LLM_CSV).fillna("")
    print(f"  Loaded {len(df)} rows\n")

    results = []

    print("  === Annex domain ===")
    res = agreement(df["annex_domain"], df["llm_annex_domain"])
    res["dataset"] = "master_table"; res["label"] = "annex_domain"
    print(f"  {res}")
    results.append(res)

    print("\n  === System pattern ===")
    res = agreement(df["system_pattern"], df["llm_system_pattern"])
    res["dataset"] = "master_table"; res["label"] = "system_pattern"
    print(f"  {res}")
    results.append(res)

    # Per-right agreement
    for right_label in ["privacy_data_protection", "non_discrimination",
                        "access_social_protection"]:
        kw  = df["rights"].str.contains(right_label, na=False).map({True: "Yes", False: "No"})
        llm = df["llm_rights"].str.contains(right_label, na=False).map({True: "Yes", False: "No"})
        res = agreement(kw, llm)
        res["dataset"] = "master_table"; res["label"] = f"right_{right_label}"
        print(f"\n  === {right_label} ===")
        print(f"  {res}")
        results.append(res)

    # Per-harm agreement
    for harm_label in ["unfair_exclusion", "privacy_breach",
                       "misinformation_error", "procedural_unfairness"]:
        kw  = df["harms"].str.contains(harm_label, na=False).map({True: "Yes", False: "No"})
        llm = df["llm_harms"].str.contains(harm_label, na=False).map({True: "Yes", False: "No"})
        res = agreement(kw, llm)
        res["dataset"] = "master_table"; res["label"] = f"harm_{harm_label}"
        print(f"\n  === {harm_label} ===")
        print(f"  {res}")
        results.append(res)

    return results


def main():
    all_results = []
    all_results.extend(part_a_aiaaic_pilot())
    all_results.extend(part_b_master_table())

    if all_results:
        out = pd.DataFrame(all_results)
        out.to_csv("evaluate_results.csv", index=False)
        print(f"\n[OK] Saved evaluate_results.csv with {len(out)} rows")


if __name__ == "__main__":
    main()
