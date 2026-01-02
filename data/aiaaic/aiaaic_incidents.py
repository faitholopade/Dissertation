"""
Filters the AIAAIC incident repository to obtain public-sector incidents
that plausibly fall under Annex III(4) (employment / worker management)
or Annex III(5)(a) (essential public services / benefits), with an optional
narrow slice for explicit LLM / generative AI.

Outputs:
- aiaaic_subset_broad_first10.csv  (broad slice, first 10 for inspection)
- aiaaic_subset_llm_first10.csv    (broad + explicit LLM/generative, first 10)
- aiaaic_manual_extra.csv          (extra 15 from broad slice for manual labelling)
"""

import pandas as pd

FILE_PATH = "AIAAIC Repository - Incidents.csv"

# ----------------------------------------------------------------------
# 1. Load CSV and drop subheading row
# ----------------------------------------------------------------------

# header=1 -> second row is header; first row (index 0) is a subheading row
df = pd.read_csv(FILE_PATH, encoding="utf-8", low_memory=False, header=1)

print("Number of rows (incl. subheading row):", len(df))
print("Columns (raw):", df.columns.tolist())

# Drop the subheading row: it has NaN in "AIAAIC ID#"
df = df[df["AIAAIC ID#"].notna()].reset_index(drop=True)
print("Number of rows after dropping subheading row:", len(df))

# ----------------------------------------------------------------------
# 2. Normalise column names
# ----------------------------------------------------------------------

def normalize(col: str) -> str:
    """Map original AIAAIC column names to safe, predictable ones."""
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

# The harms details live in Unnamed: 14,15,17,18,19 → now Unnamed:_14 etc.
# We'll include them in TEXT_COLS.

# ----------------------------------------------------------------------
# 3. Keyword groups (expanded using manual annotation patterns)
# ----------------------------------------------------------------------

# Employment / worker management
EMPLOYMENT_KWS = [
    # stems
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
    # some incidents label issues as "Employment"
    "employment",
]

# Essential public services / benefits
BENEFITS_KWS = [
    # direct welfare / benefits language
    "benefit", "benefits", "welfare", "social security",
    "social assistance", "public assistance",
    "unemployment", "disability", "pension", "pensions",
    "child benefit", "child-benefit", "child welfare",
    # health-related services
    "healthcare", "health care", "medicaid", "medicare",
    # typical public-benefit contexts
    "veterans affairs", "veteran", "veterans",
    "welfare fraud", "overpayment", "advance payment",
    # funding / grants in public contexts
    "public funds", "public funding", "funding", "grant", "grants",
    # eligibility / screening language
    "eligibility", "means test", "means-testing", "means-tested",
    "eligibility screening",
]

# Public-sector / authority context
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
    "dwp",  # UK Department for Work and Pensions
    "nhs",  # UK National Health Service
    "welfare",
    "veterans affairs",
]

# LLM / generative AI (for narrow slice)
LLM_KWS = [
    "llm", "large language model",
    "chatgpt", "gpt-3", "gpt-4", "gpt4",
    "bard", "gemini", "anthropic", "claude", "grok",
    "foundation model", "generative ai", "genai",
    "chatbot",
]

# Text fields used for keyword matching
TEXT_COLS = [
    "Headline",
    "Sector_s",
    "Deployer_s",
    "Purpose_s",
    "Issues",
    "External_harms",
    "Internal_impacts",
    "Summary_links",
    "Unnamed:_14",  # harms details (external)
    "Unnamed:_15",
    "Unnamed:_17",  # internal impacts details
    "Unnamed:_18",
    "Unnamed:_19",
]

def text_from_row(row, cols=TEXT_COLS) -> str:
    """Concatenate selected columns into one lowercased string."""
    parts = []
    for col in cols:
        if col in row and pd.notna(row[col]):
            parts.append(str(row[col]))
    return " ".join(parts).lower()

def contains_any(text: str, keywords) -> bool:
    return any(k in text for k in keywords)

# ----------------------------------------------------------------------
# 4. Helper functions for masks
# ----------------------------------------------------------------------

def is_public_sector(row) -> bool:
    """
    Determine if an incident is in a public-sector / authority context.
    Uses Sector_s, Deployer_s, and generic PUBLIC_SECTOR_KWS.
    """
    sector = str(row.get("Sector_s", "")).lower()
    deployer = str(row.get("Deployer_s", "")).lower()

    # Quick checks on sector & deployer
    if "govt" in sector or "government" in sector:
        return True
    if any(kw in sector for kw in ["govt -", "govt-", "govt ", "gov."]):
        return True
    if any(kw in deployer for kw in ["department", "ministry", "council", "city", "municipal", "government", "dwp", "nhs"]):
        return True

    # Fallback: generic public-sector keywords across selected text fields
    full_text = text_from_row(row)
    return contains_any(full_text, PUBLIC_SECTOR_KWS)

def matches_employment_or_benefits(row) -> bool:
    """
    Determine if an incident plausibly fits employment (Annex III(4))
    or essential public services/benefits (Annex III(5)(a)).
    """
    full_text = text_from_row(row)

    has_emp = contains_any(full_text, EMPLOYMENT_KWS)
    has_ben = contains_any(full_text, BENEFITS_KWS)

    return has_emp or has_ben

def matches_llm(row) -> bool:
    full_text = text_from_row(row)
    return contains_any(full_text, LLM_KWS)

# ----------------------------------------------------------------------
# 5. Build masks
# ----------------------------------------------------------------------

mask_emp_or_benefit = df.apply(matches_employment_or_benefits, axis=1)
mask_public_sector = df.apply(is_public_sector, axis=1)
mask_llm = df.apply(matches_llm, axis=1)

# Broad slice: public-sector + employment/benefit context
mask_broad = mask_emp_or_benefit & mask_public_sector

# Narrow slice: subset of broad where explicit LLM / generative mentioned
mask_llm_narrow = mask_broad & mask_llm

subset_broad = df[mask_broad].copy()
subset_llm = df[mask_llm_narrow].copy()

print("Subset size (public-sector employment/benefits, any tech):", len(subset_broad))
print("Subset size (…and explicitly LLM / generative):", len(subset_llm))

# Extra slice for manual annotation (first 15 from broad)
subset_extra = subset_broad.head(15).copy()

# ----------------------------------------------------------------------
# 6. Save CSV slices for inspection / manual labelling
# ----------------------------------------------------------------------

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
