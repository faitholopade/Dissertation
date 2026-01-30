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
    for c in ("AIAAIC_ID", "AIAAIC ID#", "AIAAIC_ID#", "id",
              "record_id", "source_id"):
        if c in df.columns:
            return c
    return None


def part_a_gold_analysis(gold, kw, llm, hybrid):
    """
    Compare manual gold-standard labels against every automated method.
    Returns (list_of_disagreement_dicts, Counter_of_categories).
    """
    disagreements = []
    error_counter = Counter()

    for _, row in gold.iterrows():
        rid   = str(row.get("AIAAIC_ID", "")).strip()
        title = str(row.get("manual_headline", ""))[:80]
        m_dom = _manual_domain(row)

        # ── Gold vs LLM (from the comparison file itself) ─────
        llm_dom = _pred_domain(
            row.get("llm_annex_employment", ""),
            row.get("llm_annex_essential", ""),
        )
        cat, expl = categorise_domain_error(m_dom, llm_dom, "LLM_gold")
        if cat:
            disagreements.append({
                "record_id": rid, "title": title,
                "dimension": "domain", "method": "LLM_gold_file",
                "manual_label": m_dom, "predicted_label": llm_dom,
                "error_category": cat, "explanation": expl,
                "confidence": row.get("llm_confidence", ""),
                "rationale": str(row.get("llm_rationale_short", ""))[:200],
            })
            error_counter[cat] += 1

        # Rights check
        m_rights = row.get("manual_rights", "")
        l_rights = row.get("llm_rights", "")
        rcat, rexpl = categorise_rights_error(m_rights, l_rights, "LLM_gold")
        if rcat:
            disagreements.append({
                "record_id": rid, "title": title,
                "dimension": "rights", "method": "LLM_gold_file",
                "manual_label": str(m_rights),
                "predicted_label": str(l_rights),
                "error_category": rcat, "explanation": rexpl,
                "confidence": row.get("llm_confidence", ""),
                "rationale": str(row.get("llm_rationale_short", ""))[:200],
            })
            error_counter[rcat] += 1

        # ── Gold vs Keyword / LLM v2 / Hybrid (matched on ID) ─
        for label, ext_df, dom_col in [
            ("keyword", kw,     "annex_domain"),
            ("LLM_v2",  llm,    "llm_v2_annex_domain"),
            ("hybrid",  hybrid, "hybrid_v2_annex_domain"),
        ]:
            if ext_df.empty:
                continue
            ext_id = _id_col(ext_df)
            if not ext_id:
                continue
            match = ext_df[ext_df[ext_id].astype(str).str.strip() == rid]
            if match.empty or dom_col not in match.columns:
                continue
            pred = str(match.iloc[0].get(dom_col, "unknown")).strip().lower()
            cat, expl = categorise_domain_error(m_dom, pred, label)
            if cat:
                disagreements.append({
                    "record_id": rid, "title": title,
                    "dimension": "domain", "method": label,
                    "manual_label": m_dom, "predicted_label": pred,
                    "error_category": cat, "explanation": expl,
                    "confidence": "", "rationale": "",
                })
                error_counter[cat] += 1

    return disagreements, error_counter


# ══════════════════════════════════════════════════════════════
#  PART B: KEYWORD vs LLM — FULL-TABLE CONFUSION MATRICES
# ══════════════════════════════════════════════════════════════

def _print_confusion(gold, pred, labels, title=""):
    """Build a confusion matrix DataFrame and print it."""
    if not HAS_SKLEARN:
        return pd.DataFrame()
    cm = confusion_matrix(gold, pred, labels=labels)
    df_cm = pd.DataFrame(cm, index=labels, columns=labels)
    return df_cm


def analyse_disagreements(df, kw_col, llm_col,
                          title_col="title", desc_col="description"):
    """Return rows where keyword != LLM."""
    mask = df[kw_col].astype(str) != df[llm_col].astype(str)
    cols = [c for c in [title_col, kw_col, llm_col, desc_col]
            if c in df.columns]
    return df.loc[mask, cols].copy()


def part_b_full_table(df, report):
    """
    Keyword vs LLM confusion matrices + classification reports
    on the full 150-row master table.
    """
    def log(msg):
        print(msg)
        report.append(msg)

    log(f"\n{'=' * 68}")
    log("  PART B: KEYWORD vs LLM — FULL-TABLE ANALYSIS (150 rows)")
    log(f"{'=' * 68}")

    # Determine which LLM columns exist
    llm_dom_col = next((c for c in ("llm_v2_annex_domain", "llm_annex_domain")
                        if c in df.columns), None)
    llm_pat_col = next((c for c in ("llm_v2_system_pattern", "llm_system_pattern")
                        if c in df.columns), None)

    cm_domain  = pd.DataFrame()
    cm_pattern = pd.DataFrame()
    disag      = pd.DataFrame()

    # ── Domain confusion matrix ───────────────────────────────
    if llm_dom_col and "annex_domain" in df.columns and HAS_SKLEARN:
        domain_labels = ["employment", "essential_services", "unknown"]
        cm_domain = _print_confusion(
            df["annex_domain"], df[llm_dom_col],
            labels=domain_labels, title="Annex Domain",
        )
        log(f"\n  CONFUSION MATRIX: Annex Domain (rows=keyword, cols=LLM)")
        log(f"  {'─' * 50}")
        log(cm_domain.to_string())

        cr = classification_report(
            df["annex_domain"], df[llm_dom_col],
            labels=domain_labels, zero_division=0,
        )
        log(f"\n  Classification report (keyword=reference, LLM=prediction):")
        log(cr)

        kappa = cohen_kappa_score(df["annex_domain"], df[llm_dom_col])
        log(f"  Cohen's κ (domain): {kappa:.3f}")

        # Domain disagreements
        disag = analyse_disagreements(df, "annex_domain", llm_dom_col)
        log(f"\n  Domain disagreements: {len(disag)} / {len(df)}")
        if not disag.empty:
            for _, row in disag.head(10).iterrows():
                log(f"    Title:   {str(row.get('title', ''))[:80]}")
                log(f"    Keyword: {row['annex_domain']}  |  LLM: {row[llm_dom_col]}")
                desc = str(row.get("description", ""))[:120]
                if desc:
                    log(f"    Desc:    {desc}...")
                log("")

    # ── Pattern confusion matrix ──────────────────────────────
    if llm_pat_col and "system_pattern" in df.columns and HAS_SKLEARN:
        pattern_labels = sorted(set(
            df["system_pattern"].tolist() + df[llm_pat_col].tolist()
        ))
        cm_pattern = _print_confusion(
            df["system_pattern"], df[llm_pat_col],
            labels=pattern_labels, title="System Pattern",
        )
        log(f"\n  CONFUSION MATRIX: System Pattern (rows=keyword, cols=LLM)")
        log(f"  {'─' * 50}")
        log(cm_pattern.to_string())

        cr2 = classification_report(
            df["system_pattern"], df[llm_pat_col],
            labels=pattern_labels, zero_division=0,
        )
        log(f"\n  Classification report (system pattern):")
        log(cr2)

        kappa2 = cohen_kappa_score(df["system_pattern"], df[llm_pat_col])
        log(f"  Cohen's κ (pattern): {kappa2:.3f}")

    return cm_domain, cm_pattern, disag


# ══════════════════════════════════════════════════════════════
#  PART C: PER-LABEL RIGHTS & HARMS AGREEMENT
# ══════════════════════════════════════════════════════════════

def rights_harms_analysis(df, kw_col, llm_col, all_labels, name, report):
    """Per-label agreement for multi-label fields (comma/semicolon separated)."""
    if kw_col not in df.columns or llm_col not in df.columns:
        report.append(f"\n  ⚠  Skipping {name} — columns not found")
        return pd.DataFrame()

    def log(msg):
        print(msg)
        report.append(msg)

    log(f"\n{'=' * 68}")
    log(f"  PER-LABEL AGREEMENT: {name}")
    log(f"{'=' * 68}")

    results = []
    for label in all_labels:
        kw_has  = df[kw_col].astype(str).str.contains(label, na=False).astype(int)
        llm_has = df[llm_col].astype(str).str.contains(label, na=False).astype(int)

        agree    = (kw_has == llm_has).mean()
        both     = ((kw_has == 1) & (llm_has == 1)).sum()
        kw_only  = ((kw_has == 1) & (llm_has == 0)).sum()
        llm_only = ((kw_has == 0) & (llm_has == 1)).sum()
        neither  = ((kw_has == 0) & (llm_has == 0)).sum()

        results.append({
            "label": label, "agree": round(agree, 3),
            "both": int(both), "kw_only": int(kw_only),
            "llm_only": int(llm_only), "neither": int(neither),
        })
        log(f"  {label:30s}  agree={agree:.3f}  both={both}  "
            f"kw_only={kw_only}  llm_only={llm_only}")

    return pd.DataFrame(results)


# ══════════════════════════════════════════════════════════════
#  PART D: QUALITATIVE THEME SYNTHESIS
# ══════════════════════════════════════════════════════════════

def part_d_themes(error_counter, report):
    """Build qualitative narrative from error category counts."""
    def log(msg):
        print(msg)
        report.append(msg)

    log(f"\n{'=' * 68}")
    log("  QUALITATIVE ERROR THEMES (for Section 5.3 discussion)")
    log(f"{'=' * 68}")

    over  = sum(v for k, v in error_counter.items() if "over_classif" in k)
    miss  = sum(v for k, v in error_counter.items() if "misses_" in k)
    swap  = sum(v for k, v in error_counter.items() if "swap" in k)
    part  = sum(v for k, v in error_counter.items() if "partial" in k)
    rover = sum(v for k, v in error_counter.items() if "rights_over" in k)
    rund  = sum(v for k, v in error_counter.items() if "rights_under" in k
                or "rights_over_under" in k)

    if over:
        log(f"\n  1. Over-classification ({over} instances)")
        log("     The LLM assigned a specific Annex III domain when the manual")
        log("     annotator found no relevance.  Typical cause: keyword presence")
        log("     (e.g. 'employment') treated as sufficient evidence without")
        log("     checking for individual-level decision-making, which the")
        log("     Annex III definitions require.")

    if miss:
        log(f"\n  2. Under-classification / Missed domains ({miss} instances)")
        log("     The automated method labelled 'unknown' when the manual")
        log("     annotator identified a clear Annex III domain.  Common causes:")
        log("     sparse incident descriptions and implicit rather than explicit")
        log("     domain language (e.g. 'public assistance' not 'welfare').")

    if swap:
        log(f"\n  3. Domain boundary confusion ({swap} instances)")
        log("     Employment ↔ essential services swaps.  Reflects genuine")
        log("     ambiguity at the Annex III boundary — e.g. a government HR")
        log("     tool could fall under Annex III/4 or Annex III/5a.")

    if part:
        log(f"\n  4. Partial match — dual-domain records ({part} instances)")
        log("     Manual annotator marked BOTH employment AND essential services")
        log("     but automated method only predicted one.  Suggests the LLM")
        log("     defaults to a single-label framing.")

    if rover or rund:
        log(f"\n  5. Rights label disagreements ({rover + rund} instances)")
        log("     Most common pattern: LLM predicts 'OTHER' where manual found")
        log("     specific rights (NON-DISCRIMINATION, PRIVACY), or LLM adds")
        log("     extra rights categories the manual annotator did not flag.")


# ══════════════════════════════════════════════════════════════
#  FIGURES
# ══════════════════════════════════════════════════════════════

def make_figures(error_counter, disagreements):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  ⚠  matplotlib not available — skipping figures")
        return

    FIG_DIR.mkdir(parents=True, exist_ok=True)

    # ── Figure 1: Error category bar chart ────────────────────
    cats = error_counter.most_common(15)
    if cats:
        labels, values = zip(*cats)
        short = [l.replace("_", " ")[:42] for l in labels]

        fig, ax = plt.subplots(figsize=(10, max(4, len(cats) * 0.45)))
        ax.barh(short[::-1], values[::-1], color="#E07B54")
        ax.set_xlabel("Count")
        ax.set_title("Error Categories: Manual vs Automated Disagreements")
        plt.tight_layout()
        out = FIG_DIR / "fig_error_categories.png"
        fig.savefig(out, dpi=150)
        plt.close(fig)
        print(f"  ✅ {out}")

    # ── Figure 2: Method × error-type heatmap ─────────────────
    if disagreements:
        df = pd.DataFrame(disagreements)
        if "method" in df.columns and "error_category" in df.columns:
            def simplify(cat):
                if "over_classif" in cat:   return "Over-classification"
                if "misses_" in cat:        return "Under-classification"
                if "swap" in cat:           return "Domain swap"
                if "partial" in cat:        return "Partial match"
                if "rights" in cat:         return "Rights mismatch"
                return "Other"

            df["error_type"] = df["error_category"].apply(simplify)
            ct = pd.crosstab(df["method"], df["error_type"])

            fig, ax = plt.subplots(figsize=(9, max(3, len(ct.index) * 0.6)))
            im = ax.imshow(ct.values, cmap="YlOrRd", aspect="auto")
            ax.set_xticks(range(len(ct.columns)))
            ax.set_xticklabels(ct.columns, rotation=30, ha="right")
            ax.set_yticks(range(len(ct.index)))
            ax.set_yticklabels(ct.index)
            for i in range(ct.shape[0]):
                for j in range(ct.shape[1]):
                    ax.text(j, i, str(ct.values[i, j]), ha="center",
                            va="center", fontsize=10,
                            color="white" if ct.values[i, j] > ct.values.max()/2
                            else "black")
