# Filters the AIAAIC incident repository to obtain public-sector and LLM-related harms relevant to Annex III.

import pandas as pd

FILE_PATH = "AIAAIC Repository - Incidents.csv"  

df = pd.read_csv(FILE_PATH, encoding="utf-8", low_memory=False, header=1)

print("Number of rows:", len(df))
print("Columns:", df.columns.tolist())

# make sure the expected columns are present
required_cols = [
    "AIAAIC ID#", "Headline", "Sector(s)", "Deployer(s)",
    "Purpose(s)", "Issue(s)", "External harms", "Internal impacts", "Summary/links"
]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    print("WARNING: Missing expected columns:", missing)

# --- 2. Define keyword groups for Annex III slice --- #

EMPLOYMENT_KWS = [
    "recruit", "recruitment", "hiring", "hire", "job", "applicant",
    "cv", "résumé", "resume", "hr", "workforce", "employee",
    "performance review", "gig worker", "labour", "labor"
]

BENEFITS_KWS = [
    "benefit", "benefits", "welfare", "eligibility", "public assistance",
    "social security", "social services", "unemployment", "disability",
    "healthcare", "health care", "pension", "debt recovery"
]

PUBLIC_SECTOR_KWS = [
    "government", "public sector", "ministry", "council", "municipal",
    "authority", "agency", "department", "police", "court", "social services"
]

LLM_KWS = [
    "llm", "large language model", "chatgpt", "gpt-3", "gpt-4", "gpt4",
    "bard", "gemini", "anthropic", "claude",
    "foundation model", "generative ai", "genai", "chatbot"
]

TEXT_COLS = [
    "Headline",
    "Sector(s)",
    "Deployer(s)",
    "Purpose(s)",
    "Issue(s)",
    "External harms",
    "Internal impacts",
    "Summary/links"
]

def match_any(text, keywords):
    if not isinstance(text, str):
        return False
    t = text.lower()
    return any(k in t for k in keywords)

def row_matches_any(row, keywords):
    return any(match_any(row[col], keywords) for col in TEXT_COLS if col in row)

# --- 3. Build masks --- #

mask_emp_or_benefit = df.apply(
    lambda r: row_matches_any(r, EMPLOYMENT_KWS + BENEFITS_KWS),
    axis=1
)

mask_public_sector = df.apply(
    lambda r: row_matches_any(r, PUBLIC_SECTOR_KWS),
    axis=1
)

mask_llm = df.apply(
    lambda r: row_matches_any(r, LLM_KWS),
    axis=1
)

# Broad slice: public-sector employment/benefit incidents (any tech)
mask_broad = mask_emp_or_benefit & mask_public_sector

# Narrow slice: same, but also explicitly mentions LLM / generative
mask_llm_narrow = mask_broad & mask_llm

subset_broad = df[mask_broad].copy()
subset_llm = df[mask_llm_narrow].copy()

print("Subset size (public-sector employment/benefits, any tech):", len(subset_broad))
print("Subset size (…and explicitly LLM / generative):", len(subset_llm))

# --- 4. Save first 10 rows of each slice for manual annotation --- #

cols_keep = [
    "AIAAIC ID#",
    "Headline",
    "Occurred",
    "Country(ies)",
    "Sector(s)",
    "Deployer(s)",
    "Developer(s)",
    "System name(s)",
    "Technology(ies)",
    "Purpose(s)",
    "Issue(s)",
    "External harms",
    "Internal impacts",
    "Summary/links"
]

# Handle missing columns 
cols_keep = [c for c in cols_keep if c in df.columns]

broad_out = "aiaaic_subset_broad_first10.csv"
llm_out = "aiaaic_subset_llm_first10.csv"

subset_broad[cols_keep].head(10).to_csv(broad_out, index=False)
subset_llm[cols_keep].head(10).to_csv(llm_out, index=False)

print(f"Saved broad slice to: {broad_out}")
print(f"Saved LLM-focused slice to: {llm_out}")
