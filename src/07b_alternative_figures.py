"""Step 07b: Generate alternative figure styles.

Produces supplementary distribution figures for rights and harms using
alternative visual encodings for comparison.

Outputs:
    figures/fig_*.png  (alternative styles)
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
    c = Counter()
    for val in series.dropna():
        for part in str(val).split(sep):
            part = part.strip().upper()
            if part and part not in ("NAN", "NONE", "UNKNOWN", ""):
                c[part] += 1
    return c


def fig_rights_distribution(df, gold):
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
    print(f"  [OK] {out}")


def fig_harms_distribution(df, gold):
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
            "summary_assistant":      "Factual error / Omission in summary",
            "misinformation_error":   "Misinformation / Deception",
            "not_llm":                "Non-LLM system failure",
        }
        # Use best available pattern column
        pat_col = None
        for c in ("hybrid_v2_system_pattern", "llm_v2_system_pattern", "system_pattern"):
            if c in df.columns:
                pat_col = c
                break
        if pat_col:
            for val in df[pat_col].dropna():
                harm = pattern_to_harm.get(str(val).strip(), None)
                if harm:
                    harms_counts[harm] += 1

    if not harms_counts:
        print("  ⚠  No harms data found – cannot generate harms distribution")
        return

    labels, values = zip(*harms_counts.most_common())
    short = [l[:45] for l in labels]

    fig, ax = plt.subplots(figsize=(10, max(4, len(labels) * 0.5)))
    ax.barh(short[::-1], values[::-1], color="#E07B54")
    ax.set_xlabel("Frequency (derived from system-pattern labels)")
    ax.set_title("Inferred Harm Categories Across 150 Records")
    plt.tight_layout()
    out = FIG_DIR / "fig_harms_distribution.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  [OK] {out}")


def fig_rights_by_domain(gold):
    if not {"manual_annex_employment", "manual_annex_essential", "manual_rights"}.issubset(gold.columns):
        print("  ⚠  Skipping rights × domain (missing columns)")
        return

    rows = []
    for _, r in gold.iterrows():
        m_emp = str(r["manual_annex_employment"]).strip().upper() in ("YES","TRUE","1","Y")
        m_ess = str(r["manual_annex_essential"]).strip().upper() in ("YES","TRUE","1","Y")
        domain = "Employment" if m_emp else ("Essential Services" if m_ess else "Neither")
        rights_raw = str(r.get("manual_rights", ""))
        for right in rights_raw.replace(";", ",").split(","):
            right = right.strip().upper()
            if right and right not in ("NAN", "NONE", ""):
                rows.append({"domain": domain, "right": right[:30]})

    if not rows:
        print("  ⚠  No rights × domain pairs found")
        return

    rdf = pd.DataFrame(rows)
    ct = pd.crosstab(rdf["right"], rdf["domain"])

    fig, ax = plt.subplots(figsize=(9, 5))
    ct.plot.barh(stacked=True, ax=ax, colormap="Set2")
    ax.set_xlabel("Count")
    ax.set_title("Rights Labels by Annex III Domain (Gold Standard)")
    ax.legend(title="Domain", loc="lower right")
    plt.tight_layout()
    out = FIG_DIR / "fig_rights_by_domain.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  [OK] {out}")


def fig_harms_by_pattern(df):
    dom_col = None
    pat_col = None
    for c in ("hybrid_v2_annex_domain", "llm_v2_annex_domain", "annex_domain"):
        if c in df.columns:
            dom_col = c
            break
    for c in ("hybrid_v2_system_pattern", "llm_v2_system_pattern", "system_pattern"):
        if c in df.columns:
            pat_col = c
            break

    if not dom_col or not pat_col:
        print("  ⚠  Skipping harms × pattern heatmap (missing columns)")
        return

    ct = pd.crosstab(df[pat_col], df[dom_col])
    # Drop 'unknown' rows/cols if they dominate
    if "unknown" in ct.index and len(ct.index) > 2:
        ct = ct.drop("unknown", axis=0, errors="ignore")

    if ct.empty:
        return

    fig, ax = plt.subplots(figsize=(8, max(4, len(ct.index) * 0.45)))
    sns.heatmap(ct, annot=True, fmt="d", cmap="YlOrRd", ax=ax, linewidths=0.5)
    ax.set_title("System Pattern × Domain (Hybrid Labels)")
    ax.set_ylabel("System Pattern")
    ax.set_xlabel("Annex Domain")
    plt.tight_layout()
    out = FIG_DIR / "fig_harms_by_pattern.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  [OK] {out}")


def main():
    print("=" * 60)
    print("  STEP 7b: Alternative Rights & Harms Figures")
    print("=" * 60)

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    df, gold = load()

    fig_rights_distribution(df, gold)
    fig_harms_distribution(df, gold)
    fig_rights_by_domain(gold)
    fig_harms_by_pattern(df)

    print("\n[OK] Alternative figures complete.")


if __name__ == "__main__":
    main()
