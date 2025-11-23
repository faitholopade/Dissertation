# Loads all filtered datasets and applies rule-based classification to generate the unified master_annotation_table.csv.

import pandas as pd
from schema import (
    RiskRecord, AnnexDomain, ActorRole, SystemPattern,
    RightCategory, HarmCategory
)

def classify_text_basic(text: str):
    """Very rough heuristic classifier — v0.1."""
    t = text.lower()

    # Annex domain
    if any(k in t for k in ["recruit", "hiring", "job", "cv", "resume", "hr"]):
        domain = AnnexDomain.EMPLOYMENT
    elif any(k in t for k in ["benefit", "welfare", "eligibility", "healthcare", "social service"]):
        domain = AnnexDomain.ESSENTIAL_SERVICES
    else:
        domain = AnnexDomain.UNKNOWN

    # System pattern (LLM)
    if any(k in t for k in ["chatgpt", "llm", "large language model", "gpt", "chatbot"]):
        pattern = SystemPattern.LLM_DECISION_SUPPORT
    elif any(k in t for k in ["screening", "filter", "rank", "resume", "cv"]):
        pattern = SystemPattern.LLM_ASSISTED_SCREENING
    else:
        pattern = SystemPattern.UNKNOWN

    # Rights
    rights = []
    if domain == AnnexDomain.EMPLOYMENT:
        rights.append(RightCategory.NON_DISCRIMINATION)
        rights.append(RightCategory.PRIVACY_DATA_PROTECTION)
    if domain == AnnexDomain.ESSENTIAL_SERVICES:
        rights.append(RightCategory.ACCESS_SOCIAL_PROTECTION)
        rights.append(RightCategory.PRIVACY_DATA_PROTECTION)

    # Harms — placeholder logic
    harms = []
    if any(k in t for k in ["bias", "discrim", "unequal", "unfair"]):
        harms.append(HarmCategory.UNFAIR_EXCLUSION)
    if any(k in t for k in ["leak", "privacy", "data"]):
        harms.append(HarmCategory.PRIVACY_BREACH)

    if not harms:
        harms = [HarmCategory.OTHER]

    return domain, pattern, rights, harms


def build_records():
    records = []

    # --- 1. US FEDERAL AI USE CASES ---
    us = pd.read_csv("./Federal AI Use Case Inventory/us_federal_subset_first10.csv")
    for _, row in us.iterrows():
        desc = str(row.get("What is the intended purpose and expected benefits of the AI?", "")) + " " + str(
            row.get("Describe the AI system’s outputs.", "")
        )
        domain, pattern, rights, harms = classify_text_basic(desc)

        rec = RiskRecord(
            source="US_FED",
            source_id=row.get("Use Case Name"),
            title=row.get("Use Case Name", ""),
            description=desc,
            annex_domain=domain,
            actor_role=ActorRole.DEPLOYER,
            system_pattern=pattern,
            rights=rights,
            harms=harms,
            notes="Auto annotation v0.1 (rule-based)"
        )
        records.append(rec)

    # --- 2. AIAAIC BROAD + LLM INCIDENTS ---
    for fname in ["./AIAAIC (AI, algorithmic and automation incidents and controversies)/aiaaic_subset_broad_first10.csv", "./AIAAIC (AI, algorithmic and automation incidents and controversies)/aiaaic_subset_llm_first10.csv"]:
        aia = pd.read_csv(fname)
        for _, row in aia.iterrows():
            desc = str(row.get("Summary/links", "")) + " " + str(row.get("Issue(s)", ""))
            domain, pattern, rights, harms = classify_text_basic(desc)

            rec = RiskRecord(
                source="AIAAIC",
                source_id=row.get("AIAAIC ID#"),
                title=row.get("Headline", ""),
                description=desc,
                annex_domain=domain,
                actor_role=ActorRole.DEPLOYER,
                system_pattern=pattern,
                rights=rights,
                harms=harms,
                notes="Auto annotation v0.1 (rule-based)"
            )
            records.append(rec)

    # --- 3. ECtHR CASES ---
    echr = pd.read_csv("./European Court of Human Rights/case_law_subset.csv")
    for _, row in echr.iterrows():
        desc = (
            f"Articles: {row.get('articles','')} | Conclusion: {row.get('conclusion','')}"
        )
        domain = AnnexDomain.ESSENTIAL_SERVICES  # rights slice mainly about benefits/discrimination
        pattern = SystemPattern.NOT_LLM          # case-law, not a tech system
        rights = [RightCategory.NON_DISCRIMINATION, RightCategory.ACCESS_SOCIAL_PROTECTION]
        harms = [HarmCategory.PROCEDURAL_UNFAIRNESS]

        rec = RiskRecord(
            source="ECtHR",
            source_id=row.get("application_number"),
            title=row.get("case_name", ""),
            description=desc,
            annex_domain=domain,
            actor_role=ActorRole.DEPLOYER,
            system_pattern=pattern,
            rights=rights,
            harms=harms,
            notes="ECtHR rights backbone"
        )
        records.append(rec)

    return records


if __name__ == "__main__":
    records = build_records()

    # Convert dataclasses → DataFrame
    data = []
    for r in records:
        data.append({
            "source": r.source,
            "source_id": r.source_id,
            "title": r.title,
            "description": r.description,
            "annex_domain": r.annex_domain.value,
            "actor_role": r.actor_role.value,
            "system_pattern": r.system_pattern.value,
            "rights": ";".join([x.value for x in r.rights]),
            "harms": ";".join([x.value for x in r.harms]),
            "notes": r.notes
        })

    df = pd.DataFrame(data)
    df.to_csv("master_annotation_table.csv", index=False)

    print("Saved master_annotation_table.csv with", len(df), "records.")
