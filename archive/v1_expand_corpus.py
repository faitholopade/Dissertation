#!/usr/bin/env python3
"""
expand_corpus.py  –  Expand the master annotation corpus to ≥150 records.

Sources expanded:
  1. AIAAIC: pull from aiaaic_ranked_top100.csv (rows 51–100, beyond current top50)
  2. USFED:  pull additional rows from 2024consolidatedaiinventoryrawv2.csv
  3. OECD AIM (new source): public-sector AI cases from OECD AI policy observatory

Run:
    python expand_corpus.py
Outputs:
    aiaaic_expansion.csv          – 40 additional AIAAIC rows
    usfed_expansion.csv           – 20 additional USFED rows
    master_annotation_table_v05.csv – unified ≥150-row table
"""

import pandas as pd
import re, os, sys

# ── Keyword dictionaries (v3 – expanded) ────────────────────────────
EMPLOYMENT_KW = [
    "employment", "employ", "employee", "employer", "worker", "workforce",
    "staffing", "staff", "recruitment", "recruiting", "hiring", "hire",
    "applicant", "candidate", "cv", "résumé", "resume", "hr",
    "human resources", "personnel", "layoff", "redundancy", "termination",
    "fired", "promotion", "performance review", "gig work", "gig worker",
    "labour", "labor", "shortlisting", "screening", "job", "workplace",
    "shift scheduling", "task allocation", "worker management",
    "job advertisement", "salary", "wage", "intern", "apprentice",
    "contract worker", "freelance", "temporary worker", "probation",
    "disciplinary", "appraisal", "roster", "rota",
]

BENEFITS_KW = [
    "benefit", "benefits", "welfare", "social security", "public assistance",
    "unemployment", "disability", "pension", "pensions", "child benefit",
    "child welfare", "healthcare", "health care", "medicaid", "medicare",
    "veteran", "veterans", "veterans affairs", "fraud detection",
    "welfare fraud", "overpayment", "advance payment", "eligibility",
    "means testing", "eligibility screening", "public funding", "grants",
    "social protection", "public service", "essential service",
    "housing benefit", "food stamp", "snap", "tanf", "income support",
    "universal credit", "jobseeker", "allowance", "subsidy", "stipend",
    "asylum", "refugee", "immigration", "visa", "border",
    "child protection", "safeguarding", "care system",
    "debt recovery", "robodebt", "sanctions",
]

PUBLIC_SECTOR_KW = [
    "government", "govt", "gov.", "ministry", "department", "authority",
    "agency", "council", "municipal", "city council", "police", "courts",
    "justice", "local authority", "social services", "dwp", "nhs",
    "veterans affairs", "public sector", "public body", "state",
    "federal", "national", "regional", "county", "borough",
    "parliament", "congress", "senate", "regulator", "ombudsman",
    "inspector", "commissioner", "public authority",
]

LLM_KW = [
    "llm", "large language model", "chatgpt", "gpt-3", "gpt-4", "gpt4",
    "gpt3", "bard", "gemini", "claude", "grok", "anthropic",
    "foundation model", "generative ai", "genai", "chatbot",
    "copilot", "openai", "mistral", "llama", "deepseek",
    "ai assistant", "virtual assistant", "language model",
    "transformer", "prompt", "fine-tune", "fine-tuning",
]

SYSTEM_PATTERN_RULES = {
    "llm_decision_support": [
        "decision support", "decision-support", "case management",
        "recommendation engine", "eligibility determination",
        "risk scoring", "triage", "prioriti", "predict",
        "automat.*decision", "algorithmic decision",
    ],
    "llm_assisted_screening": [
        "screening", "shortlist", "filter", "rank.*candidate",
        "cv.*scor", "resume.*scor", "applicant.*track",
        "pre-screen", "initial review",
    ],
    "chatbot": [
        "chatbot", "chat bot", "virtual assistant", "conversational",
        "customer service bot", "helpdesk", "help desk", "faq bot",
        "interactive voice", "ivr",
    ],
    "summary_assistant": [
        "summari", "summary", "report generat", "draft",
        "document generat", "text generat", "content generat",
        "briefing", "memo generat",
    ],
    "surveillance_monitor": [
        "surveillance", "monitor", "track", "camera", "cctv",
        "facial recognition", "biometric", "body cam",
        "geolocation", "gps track", "keystroke",
        "screen capture", "productivity monitor",
    ],
    "profiling_scoring": [
        "profil", "scor", "risk assess", "credit scor",
        "fraud detect", "anomaly detect", "pattern detect",
        "predictive polic", "recidivism", "threat assess",
    ],
}


def kw_match(text, keywords):
    """Case-insensitive substring match against keyword list."""
    if not isinstance(text, str):
        return False
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


def regex_match(text, patterns):
    """Case-insensitive regex match."""
    if not isinstance(text, str):
        return False
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in patterns)


def concat_text_cols(row, cols):
    """Concatenate multiple columns into one searchable string."""
    parts = []
    for c in cols:
        if c in row.index and isinstance(row[c], str):
            parts.append(row[c])
    return " ".join(parts)


# ─── AIAAIC expansion ───────────────────────────────────────────────
def expand_aiaaic():
    """
    Load the full AIAAIC incidents CSV and select rows 51-100 from the
    ranked list (already have top 50) plus any new high-relevance rows.
    Falls back to re-ranking from the full CSV if ranked file unavailable.
    """
    # Try ranked file first
    ranked_path = "aiaaic_ranked_top100.csv"
    full_path = "./AIAAIC (AI, algorithmic and automation incidents and controversies)/AIAAIC Repository - Incidents.csv"

    if os.path.exists(ranked_path):
        df = pd.read_csv(ranked_path)
        # Take rows beyond the first 50 (already in corpus)
        existing_ids_path = "aiaaic_ranked_top50.csv"
        if os.path.exists(existing_ids_path):
            existing = pd.read_csv(existing_ids_path)
            existing_ids = set(existing.iloc[:, 0].astype(str))
            df = df[~df.iloc[:, 0].astype(str).isin(existing_ids)]
        expansion = df.head(40)

    elif os.path.exists(full_path):
        df = pd.read_csv(full_path, header=1)
        df = df[df.iloc[:, 0].notna()].copy()
        # Rename columns for consistency
        col_map = {}
        for c in df.columns:
            if "aiaaic" in c.lower() and "id" in c.lower():
                col_map[c] = "AIAAIC_ID"
            elif "headline" in c.lower():
                col_map[c] = "Headline"
        df.rename(columns=col_map, inplace=True)

        text_cols = [c for c in df.columns if df[c].dtype == object]

        def score_row(row):
            txt = concat_text_cols(row, text_cols)
            s = 0
            if kw_match(txt, EMPLOYMENT_KW): s += 2
            if kw_match(txt, BENEFITS_KW): s += 2
            if kw_match(txt, PUBLIC_SECTOR_KW): s += 1
            if kw_match(txt, LLM_KW): s += 3
            return s

        df["_score"] = df.apply(score_row, axis=1)
        df = df[df["_score"] >= 2].sort_values("_score", ascending=False)

        # Remove already-used IDs
        for f in ["aiaaic_ranked_top50.csv", "aiaaic_manual_extra.csv"]:
            if os.path.exists(f):
                used = pd.read_csv(f)
                id_col = used.columns[0]
                used_ids = set(used[id_col].astype(str))
                if "AIAAIC_ID" in df.columns:
                    df = df[~df["AIAAIC_ID"].astype(str).isin(used_ids)]

        expansion = df.head(40)
    else:
        print("⚠ No AIAAIC source file found – creating placeholder.")
        expansion = pd.DataFrame()

    if len(expansion) > 0:
        expansion.to_csv("aiaaic_expansion.csv", index=False)
        print(f"  AIAAIC expansion: {len(expansion)} new rows → aiaaic_expansion.csv")
    return expansion


# ─── USFED expansion ────────────────────────────────────────────────
def expand_usfed():
    """
    Pull additional rows from the 2024 Federal AI Use Case Inventory.
    Focus on rights-impacting / safety-impacting cases.
    """
    path = "./Federal AI Use Case Inventory/2024_consolidated_ai_inventory_raw_v2.csv"
    if not os.path.exists(path):
        # Try alternate name
        for alt in ["2024consolidatedaiinventoryraw.csv",
                     "2024-Federal-AI-Use-Case-Inventory.csv"]:
            if os.path.exists(alt):
                path = alt
                break

    if not os.path.exists(path):
        print("⚠ No USFED source file found – creating placeholder.")
        return pd.DataFrame()

    for enc in ["utf-8", "cp1252", "latin-1"]:
        try:
            df = pd.read_csv(path, low_memory=False, encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        print(f"⚠ Could not read {path} with any encoding")
        return pd.DataFrame()

    # Identify text columns
    name_col = [c for c in df.columns if "use case name" in c.lower()]
    purpose_col = [c for c in df.columns if "purpose" in c.lower() or "intended" in c.lower()]
    output_col = [c for c in df.columns if "output" in c.lower()]
    impact_col = [c for c in df.columns if "rights" in c.lower() or "impact" in c.lower() or "safety" in c.lower()]

    search_cols = name_col + purpose_col + output_col + impact_col
    if not search_cols:
        search_cols = [c for c in df.columns if df[c].dtype == object][:5]

    def score_row(row):
        txt = concat_text_cols(row, search_cols)
        s = 0
        if kw_match(txt, EMPLOYMENT_KW): s += 2
        if kw_match(txt, BENEFITS_KW): s += 2
        if kw_match(txt, LLM_KW): s += 3
        # Boost rights/safety-impacting
        for c in impact_col:
            if isinstance(row.get(c), str) and "yes" in row[c].lower():
                s += 2
        return s

    df["_score"] = df.apply(score_row, axis=1)
    df = df[df["_score"] >= 2].sort_values("_score", ascending=False)

    # Remove already-used (first 10)
    if os.path.exists("usfederal_subset_first10.csv"):
        used = pd.read_csv("usfederal_subset_first10.csv")
        if len(used) > 0:
            id_col = used.columns[0]
            used_ids = set(used[id_col].astype(str))
            match_col = df.columns[0]
            df = df[~df[match_col].astype(str).isin(used_ids)]

    expansion = df.head(20)
    if len(expansion) > 0:
        expansion.to_csv("usfed_expansion.csv", index=False)
        print(f"  USFED expansion: {len(expansion)} new rows → usfed_expansion.csv")
    return expansion


# ─── Annotate new rows (keyword-based) ──────────────────────────────
def annotate_domain(text):
    if kw_match(text, EMPLOYMENT_KW):
        return "employment"
    elif kw_match(text, BENEFITS_KW):
        return "essential_services"
    return "unknown"


def annotate_pattern(text):
    for pattern, rules in SYSTEM_PATTERN_RULES.items():
        if regex_match(text, rules):
            return pattern
    if kw_match(text, LLM_KW):
        return "llm_decision_support"
    # Check for clear non-LLM signals
    non_llm_signals = ["algorithm", "machine learning", "neural network",
                       "random forest", "logistic regression", "rule-based",
                       "statistical model", "regression"]
    if kw_match(text, non_llm_signals) and not kw_match(text, LLM_KW):
        return "not_llm"
    return "unknown"


def annotate_rights(text):
    rights = []
    disc_kw = ["bias", "discriminat", "unfair", "racial", "gender", "ethnic",
               "protected group", "disparate", "inequality", "prejudice",
               "stereotyp", "marginal", "vulnerable group"]
    priv_kw = ["privacy", "data protection", "surveillance", "personal data",
               "gdpr", "profiling", "data breach", "data leak", "pii",
               "consent", "tracking", "biometric"]
    social_kw = ["welfare", "benefit", "eligibility", "social protection",
                 "public service", "entitlement", "pension", "assistance",
                 "healthcare access", "social security"]
    admin_kw = ["transparency", "due process", "accountability", "redress",
                "appeal", "oversight", "explainab", "right to explanation",
                "procedural", "good administration"]

    if regex_match(text, disc_kw):
        rights.append("non_discrimination")
    if regex_match(text, priv_kw):
        rights.append("privacy_data_protection")
    if regex_match(text, social_kw):
        rights.append("access_social_protection")
    if regex_match(text, admin_kw):
        rights.append("good_administration")
    if not rights:
        rights.append("other")
    return ";".join(rights)


def annotate_harms(text):
    harms = []
    excl_kw = ["exclud", "denied", "reject", "revok", "cut off",
               "wrongly flag", "false positive", "misclassif",
               "unfair exclusion", "wrongly denied"]
    priv_kw = ["data breach", "data leak", "privacy breach", "surveillance",
               "exposed personal", "leaked", "hack", "unauthori"]
    misinfo_kw = ["misinformation", "hallucin", "inaccura", "error",
                  "incorrect", "false information", "wrong advice",
                  "misleading"]
    proc_kw = ["procedural", "due process", "no appeal", "no redress",
               "lack of transparency", "opaque", "black box",
               "unexplained", "automated.*without.*review"]

    if regex_match(text, excl_kw):
        harms.append("unfair_exclusion")
    if regex_match(text, priv_kw):
        harms.append("privacy_breach")
    if regex_match(text, misinfo_kw):
        harms.append("misinformation_error")
    if regex_match(text, proc_kw):
        harms.append("procedural_unfairness")
    if not harms:
        harms.append("other")
    return ";".join(harms)


def build_expanded_table():
    """Combine existing 90-row table with new expansion rows."""
    print("Building expanded master annotation table (v0.5)...\n")

    records = []

    # ── Load existing 90 records ──
    existing_path = "master_annotation_table.csv"
    if os.path.exists(existing_path):
        existing = pd.read_csv(existing_path)
        print(f"  Existing: {len(existing)} rows loaded from {existing_path}")
        for _, row in existing.iterrows():
            records.append(row.to_dict())
    else:
        print("  ⚠ No existing master table found – building from scratch")

    # ── AIAAIC expansion ──
    aiaaic_exp = expand_aiaaic()
    if len(aiaaic_exp) > 0:
        title_col = "Headline" if "Headline" in aiaaic_exp.columns else aiaaic_exp.columns[1] if len(aiaaic_exp.columns) > 1 else aiaaic_exp.columns[0]
        id_col = "AIAAIC_ID" if "AIAAIC_ID" in aiaaic_exp.columns else aiaaic_exp.columns[0]
        text_cols = [c for c in aiaaic_exp.columns if aiaaic_exp[c].dtype == object]

        for _, row in aiaaic_exp.iterrows():
            full_text = concat_text_cols(row, text_cols)
            title = str(row.get(title_col, ""))[:80]
            records.append({
                "source": "AIAAIC",
                "source_id": str(row.get(id_col, "")),
                "title": title,
                "description": full_text[:500],
                "annex_domain": annotate_domain(full_text),
                "system_pattern": annotate_pattern(full_text),
                "rights": annotate_rights(full_text),
                "harms": annotate_harms(full_text),
            })

    # ── USFED expansion ──
    usfed_exp = expand_usfed()
    if len(usfed_exp) > 0:
        name_cols = [c for c in usfed_exp.columns if "name" in c.lower()]
        name_col = name_cols[0] if name_cols else usfed_exp.columns[0]
        text_cols = [c for c in usfed_exp.columns if usfed_exp[c].dtype == object]

        for _, row in usfed_exp.iterrows():
            full_text = concat_text_cols(row, text_cols)
            title = str(row.get(name_col, ""))[:80]
            records.append({
                "source": "USFED",
                "source_id": title,
                "title": title,
                "description": full_text[:500],
                "annex_domain": annotate_domain(full_text),
                "system_pattern": annotate_pattern(full_text),
                "rights": annotate_rights(full_text),
                "harms": annotate_harms(full_text),
            })

    # ── Build final table ──
    df = pd.DataFrame(records)
    out_path = "master_annotation_table_v05.csv"
    df.to_csv(out_path, index=False)
    print(f"\n✅ Saved {out_path} with {len(df)} records.")
    print(f"\n-- Domain distribution --")
    print(df["annex_domain"].value_counts().to_string())
    print(f"\n-- Source distribution --")
    print(df["source"].value_counts().to_string())
    print(f"\n-- System pattern distribution --")
    print(df["system_pattern"].value_counts().to_string())

    return df


if __name__ == "__main__":
    build_expanded_table()
