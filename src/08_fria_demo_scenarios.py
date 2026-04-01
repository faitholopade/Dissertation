"""Step 08: FRIA scenario demonstration and retrieval.

Constructs Fundamental Rights Impact Assessment scenarios for welfare
and recruitment use cases, then retrieves matching risk records from
the annotated corpus to demonstrate the framework's practical utility.

Outputs:
    output/fria_scenario_results.csv
    output/fria_scenario_summary.txt
"""

import os, sys, csv, textwrap
from pathlib import Path
from collections import Counter

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
SRC  = Path(__file__).resolve().parent

CSV_CANDIDATES = [
    BASE / "output" / "master_annotation_table_final.csv",
    BASE / "output" / "master_annotation_table_llm_v2.csv",
    BASE / "data"   / "master_annotation_table_v05.csv",
    BASE / "master_annotation_table_hybrid.csv",
    BASE / "master_annotation_table_llm.csv",
    BASE / "master_annotation_table.csv",
]
OUT_CSV = BASE / "output" / "fria_scenario_results.csv"
OUT_TXT = BASE / "output" / "fria_scenario_summary.txt"
FIG_OUT = BASE / "figures" / "fig_fria_scenario_hits.png"


def load_table():
    for path in CSV_CANDIDATES:
        if path.exists():
            df = pd.read_csv(path).fillna("")
            print(f"  Loaded {len(df)} records from {path.name}")
            return df
    sys.exit("ERROR: No annotation table CSV found. Run steps 1-2 first.")


DOMAIN_COLS  = ["annex_domain", "llm_annex_domain", "llm_v2_annex_domain",
                "hybrid_annex_domain", "hybrid_v2_annex_domain"]
PATTERN_COLS = ["system_pattern", "llm_system_pattern", "llm_v2_system_pattern",
                "hybrid_system_pattern", "hybrid_v2_system_pattern"]
RIGHTS_COLS  = ["rights", "llm_rights", "llm_v2_rights"]
HARMS_COLS   = ["harms", "llm_harms", "llm_v2_harms"]


def _any_col_equals(row, col_names, target):
    for col in col_names:
        if col in row.index and str(row[col]).strip().lower() == target.lower():
            return True
    return False


def _any_col_contains(row, col_names, targets):
    if isinstance(targets, str):
        targets = [targets]
    for col in col_names:
        if col in row.index:
            val = str(row[col]).strip().lower()
            for t in targets:
                if t.lower() in val:
                    return True
    return False


def search_cases(df, annex_domain=None, pattern_contains=None,
                 right_contains=None, harm_contains=None):
    out = df.copy()

    if annex_domain:
        cols = [c for c in DOMAIN_COLS if c in out.columns]
        mask = pd.Series(False, index=out.index)
        for col in cols:
            mask |= (out[col].astype(str).str.strip().str.lower() == annex_domain.lower())
        out = out[mask]

    if pattern_contains:
        targets = pattern_contains if isinstance(pattern_contains, list) else [pattern_contains]
        cols = [c for c in PATTERN_COLS if c in out.columns]
        mask = pd.Series(False, index=out.index)
        for col in cols:
            for t in targets:
                mask |= out[col].astype(str).str.contains(t, case=False, na=False)
        out = out[mask]

    if right_contains:
        cols = [c for c in RIGHTS_COLS if c in out.columns]
        mask = pd.Series(False, index=out.index)
        for col in cols:
            mask |= out[col].astype(str).str.contains(right_contains, case=False, na=False)
        out = out[mask]

    if harm_contains:
        cols = [c for c in HARMS_COLS if c in out.columns]
        mask = pd.Series(False, index=out.index)
        for col in cols:
            mask |= out[col].astype(str).str.contains(harm_contains, case=False, na=False)
        out = out[mask]

    return out


def _best_val(row, col_names, fallback="unknown"):
    for col in col_names:
        if col in row.index:
            v = str(row[col]).strip().lower()
            if v and v not in ("", "unknown", "nan"):
                return v
    return fallback


SHOW_COLS = ["source", "source_id", "title", "annex_domain",
             "system_pattern", "rights", "harms"]

def _show(subset, report):
    cols = [c for c in SHOW_COLS if c in subset.columns]
    # Add hybrid columns if available
    for extra in ["hybrid_v2_annex_domain", "hybrid_v2_system_pattern"]:
        if extra in subset.columns:
            cols.append(extra)

    table = subset[cols].head(15).to_markdown(index=False)
    print(table)
    report.append(table)
    report.append(f"\n  -> {len(subset)} total matching records\n")
    print(f"\n  -> {len(subset)} total matching records\n")


def _show_distributions(subset, report):
    if subset.empty:
        return

    dom_col = next((c for c in reversed(DOMAIN_COLS) if c in subset.columns), None)
    pat_col = next((c for c in reversed(PATTERN_COLS) if c in subset.columns), None)

    if dom_col:
        dist = subset[dom_col].value_counts().to_dict()
        line = f"  Domain distribution:  {dist}"
        print(line); report.append(line)

    if pat_col:
        dist = subset[pat_col].value_counts().to_dict()
        line = f"  Pattern distribution: {dist}"
        print(line); report.append(line)

    if "source" in subset.columns:
        dist = subset["source"].value_counts().to_dict()
        line = f"  Source breakdown:     {dist}"
        print(line); report.append(line)


SCENARIOS = [
    {
        "id":        "A",
        "name":      "Welfare / Benefits Eligibility Deployer",
        "annex_ref": "Annex III/5(a)",
        "narrative": (
            "A public-sector body is deploying an AI system to assist in "
            "determining eligibility for social welfare benefits (Annex III/5a). "
            "Under Article 27, they must conduct a Fundamental Rights Impact "
            "Assessment.  The FRIA team queries the framework for precedent "
            "incidents where similar profiling/scoring or resource-allocation "
            "systems in essential services caused discrimination or denied access."
        ),
        "query_params": {
            "annex_domain":      "essential_services",
            "pattern_contains":  ["profiling_scoring", "resource_allocation",
                                  "classification_triage"],
        },
        "fallback_params": {
            "annex_domain": "essential_services",
        },
    },
    {
        "id":        "B",
        "name":      "Public-Sector Recruitment AI (Annex III/4)",
        "annex_ref": "Annex III/4(a)",
        "narrative": (
            "A government HR department plans to use an LLM-assisted tool for "
            "CV screening and candidate shortlisting (Annex III/4).  They need "
            "to surface past incidents of bias or unfair exclusion in "
            "employment AI to inform their risk assessment."
        ),
        "query_params": {
            "annex_domain":      "employment",
            "right_contains":    "non_discrimination",
        },
        "fallback_params": {
            "annex_domain": "employment",
        },
    },
    {
        "id":        "C",
        "name":      "Surveillance / Biometric Monitoring in Public Services",
        "annex_ref": "Annex III/1 (Biometrics) + Annex III/5(a)",
        "narrative": (
            "A city council is evaluating facial-recognition cameras for public "
            "housing security.  They need evidence of surveillance harms, "
            "privacy breaches, and disproportionate monitoring in public-sector "
            "or essential-service contexts."
        ),
        "query_params": {
            "pattern_contains": ["surveillance_monitor"],
        },
        "fallback_params": None,
    },
    {
        "id":        "D",
        "name":      "LLM Decision-Support for Case Workers",
        "annex_ref": "Annex III/5(a)",
        "narrative": (
            "A social-services agency wants to deploy an LLM chatbot to help "
            "case workers draft eligibility summaries.  The deployer needs "
            "incidents where LLM-based, chatbot, or summary-assistant systems "
            "caused errors, misinformation, or procedural unfairness."
        ),
        "query_params": {
            "pattern_contains": ["llm_decision_support", "llm_assisted_screening",
                                 "chatbot", "summary_assistant",
                                 "misinformation_error"],
        },
        "fallback_params": None,
    },
    {
        "id":        "E",
        "name":      "Profiling & Scoring — Cross-Domain Thematic Review",
        "annex_ref": "Cross-domain (Annex III/4 + III/5a)",
        "narrative": (
            "A national AI regulator is conducting a thematic review of all "
            "profiling/scoring systems across Annex III domains to identify "
            "systemic discrimination patterns and common failure modes."
        ),
        "query_params": {
            "pattern_contains": ["profiling_scoring"],
        },
        "fallback_params": None,
    },
]


def run_scenarios(df):
    all_hits   = []
    report     = []
    counts     = {}

    report.append("=" * 68)
    report.append("  FRIA-STYLE DEMONSTRATION SCENARIOS")
    report.append(f"  Dataset: {len(df)} records")
    report.append("=" * 68)

    for sc in SCENARIOS:
        report.append("")
        report.append("-" * 68)
        report.append(f"  Scenario {sc['id']}: {sc['name']}")
        report.append(f"  Annex Reference: {sc['annex_ref']}")
        report.append("-" * 68)

        # Wrap narrative nicely
        for line in textwrap.wrap(sc["narrative"], width=66):
            report.append(f"  {line}")
        print(f"\n{'-' * 68}")
        print(f"  Scenario {sc['id']}: {sc['name']}")
        print(f"{'-' * 68}")
        print(f"  {sc['narrative']}\n")

        # Primary query
        hits = search_cases(df, **sc["query_params"])

        # Fallback if primary returns empty
        if hits.empty and sc.get("fallback_params"):
            report.append(f"\n  (Primary query returned 0 — broadening to domain-only)")
            print(f"  (Primary query returned 0 — broadening to domain-only)")
            hits = search_cases(df, **sc["fallback_params"])

        n = len(hits)
        counts[sc["id"]] = n

        report.append(f"\n  Hits: {n} / {len(df)}")
        print(f"  Hits: {n} / {len(df)}")

        if n > 0:
            report.append("")
            _show(hits, report)
            _show_distributions(hits, report)
        else:
            report.append("  (No matching records)")
            print("  (No matching records)")

        # Tag for CSV
        hits = hits.copy()
        hits["scenario_id"]   = sc["id"]
        hits["scenario_name"] = sc["name"]
        all_hits.append(hits)

    report.append(f"\n{'=' * 68}")
    report.append("  SCENARIO HIT SUMMARY")
    report.append(f"{'=' * 68}")
    for sc in SCENARIOS:
        c = counts[sc["id"]]
        report.append(f"    Scenario {sc['id']} ({sc['name'][:42]:42s})  {c:3d} hits")

    if all_hits:
        combined = pd.concat(all_hits, ignore_index=True)
        # Deduplicate by first available ID column
        id_col = next((c for c in ("source_id", "AIAAIC_ID", "title")
                       if c in combined.columns), None)
        if id_col:
            unique_n = combined[id_col].nunique()
        else:
            unique_n = len(combined)
        report.append(f"\n  Total unique records surfaced: {unique_n} / {len(df)}")
        report.append(f"  Coverage: {unique_n / len(df) * 100:.1f}%")
    else:
        combined = pd.DataFrame()

    return combined, "\n".join(report), counts


def make_figure(counts):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  [WARN]  matplotlib not available — skipping figure")
        return

    FIG_OUT.parent.mkdir(parents=True, exist_ok=True)

    ids    = list(counts.keys())
    values = list(counts.values())
    labels = [f"Scenario {i}" for i in ids]
    names  = [sc["name"] for sc in SCENARIOS]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(labels[::-1], values[::-1], color="#4A90D9")
    ax.set_xlabel(f"Number of matching records (n = 150)")
    ax.set_title("FRIA-Style Scenario Retrieval Hits")

    # Annotate bars with scenario names
    for bar, name, val in zip(bars, names[::-1], values[::-1]):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{name[:38]}  ({val})", va="center", fontsize=8)

    plt.tight_layout()
    fig.savefig(FIG_OUT, dpi=150)
    plt.close(fig)
    print(f"  [OK] {FIG_OUT}")


def main():
    print("=" * 60)
    print("  STEP 8: FRIA-Style Demonstration Scenarios")
    print("=" * 60)

    df = load_table()
    all_hits_df, report_text, counts = run_scenarios(df)

    # Print full report
    print(report_text)

    # Save CSV
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    if not all_hits_df.empty:
        all_hits_df.to_csv(OUT_CSV, index=False)
        print(f"  [OK] {OUT_CSV}")
    else:
        print("  [WARN]  No hits to save")

    # Save text report
    OUT_TXT.write_text(report_text, encoding="utf-8")
    print(f"  [OK] {OUT_TXT}")

    # Figure
    make_figure(counts)

    print(f"\n[OK] FRIA demonstration complete.")


if __name__ == "__main__":
    main()
