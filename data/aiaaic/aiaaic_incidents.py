# Filter AIAAIC incidents for public-sector employment/benefits cases

import pandas as pd

FILE_PATH = "AIAAIC Repository - Incidents.csv"

df = pd.read_csv(FILE_PATH, encoding="utf-8", low_memory=False, header=1)

print("Number of rows (incl. subheading row):", len(df))
print("Columns (raw):", df.columns.tolist())

df = df[df["AIAAIC ID#"].notna()].reset_index(drop=True)
print("Number of rows after dropping subheading row:", len(df))

def normalize(col: str) -> str:
    mapping = {
        "AIAAIC ID#": "AIAAIC_ID",
        "Country(ies)": "Country_ies",
        "Sector(s)": "Sector_s",
        "Deployer(s)": "Deployer_s",
        "Developer(s)": "Developer_s",
        "System name(s)": "System_name_s",
        "Technology(ies)": "Technology_ies",
        "Purpose(s)": "Purpose_s",
        "News trigger(s)": "News_triggers",
        "Issue(s)": "Issues",
        "External harms": "External_harms",
        "Internal impacts": "Internal_impacts",
        "Summary/links": "Summary_links",
    }
    return mapping.get(col, col.strip().replace(" ", "_"))

df.rename(columns={c: normalize(c) for c in df.columns}, inplace=True)

print("Columns (normalized):", df.columns.tolist())

EMPLOYMENT_KWS = [
    "employ", "employment", "employer", "employee", "employees",
    "worker", "workers", "workforce", "staff", "staffing",
    # recruitment / selection
    "recruit", "recruitment", "recruiting", "hiring", "hire", "hired",
    "applicant", "candidates", "cv", "résumé", "resume",
    # work-related decisions
    "layoff", "lay-offs", "redundancy", "fired", "termination",
    "promotion", "performance review",
    # misc
    "gig worker", "labour", "labor",
]

BENEFITS_KWS = [
    "benefit", "benefits", "welfare", "social security",
    "social assistance", "public assistance",
    "unemployment", "disability", "pension", "pensions",
    "child benefit", "child-benefit", "child welfare",
    "healthcare", "health care", "medicaid", "medicare",
    "veterans affairs", "veteran", "veterans",
    "welfare fraud", "overpayment", "advance payment",
    "public funds", "public funding", "funding", "grant", "grants",
    "eligibility", "means test", "means-testing", "means-tested",
    "eligibility screening",
]

PUBLIC_SECTOR_KWS = [
    "government", "govt", "gov.", "public sector", "public service",
    "public services",
    "ministry", "ministries",
    "council", "municipal", "municipality", "city council",
    "authority", "authorities",
    "agency", "agencies",
    "department", "dept",
    "police", "court", "courts", "justice",
    "local authority", "local authorities",
    "social services",
    "dwp", "nhs",
    "welfare",
    "veterans affairs",
]

LLM_KWS = [
    "llm", "large language model",
    "chatgpt", "gpt-3", "gpt-4", "gpt4",
    "bard", "gemini", "anthropic", "claude", "grok",
    "foundation model", "generative ai", "genai",
    "chatbot",
]

TEXT_COLS = [
    "Headline",
    "Sector_s",
    "Deployer_s",
    "Purpose_s",
    "Issues",
    "External_harms",
    "Internal_impacts",
    "Summary_links",
    "Unnamed:_14", "Unnamed:_15",
    "Unnamed:_17", "Unnamed:_18",
    "Unnamed:_19",
]

def text_from_row(row, cols=TEXT_COLS) -> str:
    parts = []
    for col in cols:
        if col in row and pd.notna(row[col]):
            parts.append(str(row[col]))
    return " ".join(parts).lower()

def contains_any(text: str, keywords) -> bool:
    return any(k in text for k in keywords)

def is_public_sector(row) -> bool:
    sector = str(row.get("Sector_s", "")).lower()
    deployer = str(row.get("Deployer_s", "")).lower()

    if "govt" in sector or "government" in sector:
        return True
    if any(kw in sector for kw in ["govt -", "govt-", "govt ", "gov."]):
        return True
    if any(kw in deployer for kw in ["department", "ministry", "council", "city", "municipal", "government", "dwp", "nhs"]):
        return True

    full_text = text_from_row(row)
    return contains_any(full_text, PUBLIC_SECTOR_KWS)

def matches_employment_or_benefits(row) -> bool:
    full_text = text_from_row(row)

    has_emp = contains_any(full_text, EMPLOYMENT_KWS)
    has_ben = contains_any(full_text, BENEFITS_KWS)

    return has_emp or has_ben

def matches_llm(row) -> bool:
    full_text = text_from_row(row)
    return contains_any(full_text, LLM_KWS)

mask_emp_or_benefit = df.apply(matches_employment_or_benefits, axis=1)
mask_public_sector = df.apply(is_public_sector, axis=1)
mask_llm = df.apply(matches_llm, axis=1)

mask_broad = mask_emp_or_benefit & mask_public_sector
mask_llm_narrow = mask_broad & mask_llm

subset_broad = df[mask_broad].copy()
subset_llm = df[mask_llm_narrow].copy()

print("Subset size (public-sector employment/benefits, any tech):", len(subset_broad))
print("Subset size (…and explicitly LLM / generative):", len(subset_llm))

subset_extra = subset_broad.head(15).copy()

cols_keep = [
    "AIAAIC_ID",
    "Headline",
    "Occurred",
    "Country_ies",
    "Sector_s",
    "Deployer_s",
    "Developer_s",
    "System_name_s",
    "Technology_ies",
    "Purpose_s",
    "Issues",
    "External_harms",
    "Internal_impacts",
    "Summary_links",
]

cols_keep = [c for c in cols_keep if c in df.columns]

broad_out = "aiaaic_subset_broad_first10.csv"
llm_out = "aiaaic_subset_llm_first10.csv"
extra_out = "aiaaic_manual_extra.csv"

subset_broad[cols_keep].head(10).to_csv(broad_out, index=False)
subset_llm[cols_keep].head(10).to_csv(llm_out, index=False)
subset_extra[cols_keep].to_csv(extra_out, index=False)

print(f"Saved broad slice to: {broad_out}")
print(f"Saved LLM-focused slice to: {llm_out}")
print(f"Saved extra manual subset to: {extra_out}")
