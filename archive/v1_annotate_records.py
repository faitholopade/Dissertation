"""
annotate_records.py — Rule-based annotation pipeline (v0.4).

Changes from v0.3:
  Fix 1: ECtHR column names (case_name, application_number) + fallback ID.
  Fix 2: Moved "unemployment" from EMPLOYMENT_KWS to BENEFIT_KWS;
         check BENEFIT_KWS first so unemployment → essential_services.
  Fix 3: Added misinformation keywords (error, wrong, faulty, flawed, unreliable).
  Fix 4: Added good_administration keywords + keyword-driven rights detection.
"""

import os
import pandas as pd
from typing import List, Tuple
from schema import (
    RiskRecord, AnnexDomain, ActorRole, SystemPattern,
    RightCategory, HarmCategory,
)

# ── Paths ─────────────────────────────────────────────────────
AIAAIC_DIR = "AIAAIC (AI, algorithmic and automation incidents and controversies)"
USFED_DIR  = "Federal AI Use Case Inventory"
ECHR_DIR   = "European Court of Human Rights"

AIAAIC_RANKED  = os.path.join(AIAAIC_DIR, "aiaaic_ranked_top50.csv")
AIAAIC_EXTRA   = os.path.join(AIAAIC_DIR, "aiaaic_manual_extra.csv")
USFED_RAW      = os.path.join(USFED_DIR, "2024_consolidated_ai_inventory_raw_v2.csv")
USFED_SUBSET   = os.path.join(USFED_DIR, "us_federal_subset_first10.csv")
ECHR_CSV       = os.path.join(ECHR_DIR, "case_law_subset.csv")
OUTPUT_CSV     = "master_annotation_table.csv"

# ── Keyword sets ──────────────────────────────────────────────

# FIX 2: Removed "unemployment" — it belongs in BENEFIT_KWS
EMPLOYMENT_KWS = [
    "employment", "employ", "employer", "employee", "employees",
    "worker", "workers", "workforce", "staff", "staffing",
    "recruit", "recruitment", "recruiting",
    "hiring", "hire", "hired",
    "applicant", "candidates",
    "cv", "résumé", "resume",
    "layoff", "lay-offs", "redundancy", "fired", "termination",
    "promotion", "performance review",
    "gig worker", "labour", "labor",
    "human resources", "hr screening", "job",
]

# FIX 2: "unemployment" lives here; also added policing, fraud, child protection
BENEFIT_KWS = [
    "benefit", "benefits", "welfare",
    "social security", "social assistance", "public assistance",
    "unemployment", "disability", "pension", "pensions",
    "child benefit", "child-benefit", "child welfare",
    "healthcare", "health care",
    "medicaid", "medicare",
    "veterans affairs", "veteran", "veterans",
    "welfare fraud", "overpayment", "advance payment",
    "public funds", "public funding", "funding",
    "grant", "grants",
    "eligibility", "means test", "means-testing", "means-tested",
    "eligibility screening",
    "public service", "government service", "citizen",
    "asylum", "immigration", "visa",
    "housing", "social housing", "council housing",
    "education", "student", "school",
    "policing", "police", "predictive policing",
    "child protection", "child abuse",
    "debt recovery", "robodebt",
    "fraud detection", "fraud",
]

LLM_KWS = [
    "llm", "large language model",
    "chatgpt", "gpt-3", "gpt-4", "gpt4", "gpt-4o",
    "bard", "gemini", "anthropic", "claude", "grok",
    "foundation model", "generative ai", "genai",
    "chatbot", "copilot",
    "openai", "llama", "mistral",
]

SCREENING_KWS = ["screening", "filter", "rank", "shortlist", "scoring", "triage"]
CHATBOT_KWS   = ["chatbot", "virtual assistant", "helpdesk", "copilot", "conversational"]
BIAS_KWS      = ["bias", "discrim", "unequal", "unfair", "racist", "sexist", "disparate"]
PRIVACY_KWS   = ["leak", "privacy", "data breach", "breached", "exposed", "surveillance"]

# FIX 3: Extended misinformation keywords
MISINFO_KWS   = [
    "incorrect", "false", "misleading", "hallucination", "fabricated", "inaccura",
    "error", "wrong", "faulty", "flawed", "unreliable", "erroneous",
]

PROC_UNFAIR_KWS = [
    "appeal", "due process", "procedural", "remedy", "redress",
    "opaque", "transparency",
]

# FIX 4: New keyword set for good_administration rights
GOOD_ADMIN_KWS = [
    "opaque", "transparency", "explainab", "accountab",
    "due process", "right to explanation", "automated decision",
    "notice", "oversight", "audit",
]


def classify_text(text: str) -> Tuple[
    AnnexDomain, SystemPattern, List[RightCategory], List[HarmCategory]
]:
    t = (text or "").lower()

    # ── Domain ────────────────────────────────────────────────
    # FIX 2: Check BENEFIT_KWS *first* so "unemployment" → essential_services
    if any(k in t for k in BENEFIT_KWS):
        domain = AnnexDomain.ESSENTIAL_SERVICES
    elif any(k in t for k in EMPLOYMENT_KWS):
        domain = AnnexDomain.EMPLOYMENT
    else:
        domain = AnnexDomain.UNKNOWN

    # ── System pattern ────────────────────────────────────────
    if any(k in t for k in LLM_KWS):
        if any(k in t for k in SCREENING_KWS):
            pattern = SystemPattern.LLM_ASSISTED_SCREENING
        elif any(k in t for k in CHATBOT_KWS):
            pattern = SystemPattern.CHATBOT
        else:
            pattern = SystemPattern.LLM_DECISION_SUPPORT
    elif any(k in t for k in SCREENING_KWS):
        pattern = SystemPattern.LLM_ASSISTED_SCREENING
    else:
        pattern = SystemPattern.UNKNOWN

    # ── Rights (domain-driven + keyword-driven) ───────────────
    rights: List[RightCategory] = []

    if domain == AnnexDomain.EMPLOYMENT:
        rights.extend([RightCategory.NON_DISCRIMINATION,
                       RightCategory.PRIVACY_DATA_PROTECTION])
    elif domain == AnnexDomain.ESSENTIAL_SERVICES:
        rights.extend([RightCategory.ACCESS_SOCIAL_PROTECTION,
                       RightCategory.PRIVACY_DATA_PROTECTION])

    # FIX 4: Keyword-driven good_administration detection
    if any(k in t for k in GOOD_ADMIN_KWS):
        if RightCategory.GOOD_ADMINISTRATION not in rights:
            rights.append(RightCategory.GOOD_ADMINISTRATION)

    # Also detect non-discrimination from text even for non-employment domains
    if any(k in t for k in BIAS_KWS):
        if RightCategory.NON_DISCRIMINATION not in rights:
            rights.append(RightCategory.NON_DISCRIMINATION)

    # ── Harms (keyword-driven) ────────────────────────────────
    harms: List[HarmCategory] = []
    if any(k in t for k in BIAS_KWS):
        harms.append(HarmCategory.UNFAIR_EXCLUSION)
    if any(k in t for k in PRIVACY_KWS):
        harms.append(HarmCategory.PRIVACY_BREACH)
    if any(k in t for k in MISINFO_KWS):
        harms.append(HarmCategory.MISINFORMATION_ERROR)
    if any(k in t for k in PROC_UNFAIR_KWS):
        harms.append(HarmCategory.PROCEDURAL_UNFAIRNESS)

    if not harms:
        harms = [HarmCategory.OTHER]
    if not rights:
        rights = [RightCategory.OTHER]

    return domain, pattern, rights, harms


def _get(row, *candidates, default=""):
    """Try multiple column names, return first non-null hit."""
    for col in candidates:
        val = row.get(col)
        if val is not None and pd.notna(val):
            return str(val)
    return default


def build_records() -> list[RiskRecord]:
    records: list[RiskRecord] = []

    # ── 1. US Federal AI use cases ────────────────────────────
    if os.path.exists(USFED_SUBSET):
        us = pd.read_csv(USFED_SUBSET)
        purpose_col = [c for c in us.columns if c.startswith("What is the intended purpose")]
        output_col  = [c for c in us.columns if c.startswith("Describe the AI system")]
        pcol = purpose_col[0] if purpose_col else ""
        ocol = output_col[0]  if output_col  else ""

        for _, row in us.iterrows():
            desc = f"{_get(row, pcol)} {_get(row, ocol)}"
            domain, pattern, rights, harms = classify_text(desc)
            records.append(RiskRecord(
                source="USFED",
                source_id=_get(row, "Use Case Name"),
                title=_get(row, "Use Case Name"),
                description=desc.strip(),
                annex_domain=domain,
                actor_role=ActorRole.DEPLOYER,
                system_pattern=pattern,
                rights=rights,
                harms=harms,
                notes="Auto annotation v0.4 rule-based",
            ))
        print(f"  USFED: {len(us)} rows loaded")
    else:
        print(f"  Warning: {USFED_SUBSET} not found, skipping US Federal")

    # ── 2. AIAAIC ranked top-50 + manual extras ───────────────
    aiaaic_files = [AIAAIC_RANKED, AIAAIC_EXTRA]
    for fname in aiaaic_files:
        if not os.path.exists(fname):
            print(f"  Warning: {fname} not found, skipping")
            continue
        aia = pd.read_csv(fname)
        for _, row in aia.iterrows():
            desc = " ".join([
                _get(row, "Summary_links", "Summary/links", "Summarylinks"),
                _get(row, "Issues", "Ethicalissues", "Ethical issues"),
                _get(row, "External_harms", "External harms", "Externalharms"),
                _get(row, "Headline"),
            ])
            domain, pattern, rights, harms = classify_text(desc)
            records.append(RiskRecord(
                source="AIAAIC",
                source_id=_get(row, "AIAAIC_ID", "AIAAICID", "AIAAIC ID"),
                title=_get(row, "Headline"),
                description=desc.strip(),
                annex_domain=domain,
                actor_role=ActorRole.DEPLOYER,
                system_pattern=pattern,
                rights=rights,
                harms=harms,
                notes="Auto annotation v0.4 rule-based",
            ))
        print(f"  AIAAIC: {len(aia)} rows from {os.path.basename(fname)}")

    # ── 3. ECtHR case-law backbone ────────────────────────────
    # FIX 1: Actual CSV columns are case_name and application_number
    #         (not casename / applicationnumber). Also use row index
    #         as fallback ID to prevent dedup from collapsing rows.
    if os.path.exists(ECHR_CSV):
        echr = pd.read_csv(ECHR_CSV)
        for idx, row in echr.iterrows():
            # Try both naming conventions
            app_no = _get(row, "application_number", "applicationnumber", "appno")
            case_nm = _get(row, "case_name", "casename")

            # Fallback: use row index if application_number is empty
            if not app_no or app_no == "nan":
                app_no = f"echr_row_{idx}"

            desc = (
                f"Case: {case_nm}; "
                f"Articles: {_get(row, 'articles')}; "
                f"Conclusion: {_get(row, 'conclusion')}; "
                f"Keywords: {_get(row, 'keywords')}"
            )
            records.append(RiskRecord(
                source="ECtHR",
                source_id=app_no,
                title=case_nm,
                description=desc,
                annex_domain=AnnexDomain.ESSENTIAL_SERVICES,
                actor_role=ActorRole.DEPLOYER,
                system_pattern=SystemPattern.NOT_LLM,
                rights=[RightCategory.NON_DISCRIMINATION,
                        RightCategory.ACCESS_SOCIAL_PROTECTION],
                harms=[HarmCategory.PROCEDURAL_UNFAIRNESS],
                notes="ECtHR rights backbone",
            ))
        print(f"  ECtHR: {len(echr)} rows loaded")
    else:
        print(f"  Warning: {ECHR_CSV} not found, skipping ECtHR")

    return records


if __name__ == "__main__":
    print("Building master annotation table (v0.4)...")
    records = build_records()

    df = pd.DataFrame([r.to_row() for r in records])
    df = df.fillna("")

    # Dedup: prefer non-empty source_id, then first occurrence
    df = df.drop_duplicates(subset=["source_id", "source"], keep="first")
    # Also dedup by title+source for rows that had empty source_id
    mask_empty_id = (df["source_id"] == "") | (df["source_id"] == "nan")
    df_with_id  = df[~mask_empty_id]
    df_no_id    = df[mask_empty_id].drop_duplicates(subset=["title", "source"], keep="first")
    df = pd.concat([df_with_id, df_no_id], ignore_index=True)

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nSaved {OUTPUT_CSV} with {len(df)} records.")
    print("\n-- Domain distribution --")
    print(df["annex_domain"].value_counts().to_string())
    print("\n-- System pattern distribution --")
    print(df["system_pattern"].value_counts().to_string())
    print("\n-- Source distribution --")
    print(df["source"].value_counts().to_string())
