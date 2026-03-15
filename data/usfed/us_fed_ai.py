# Filter US Federal AI use cases to Annex III employment/essential service domains

import pandas as pd

csv_path = "2024_consolidated_ai_inventory_raw_v2.csv"
df = pd.read_csv(csv_path, encoding="latin-1")

print("Columns:", df.columns.tolist())
print("Number of rows:", len(df))

purpose_col = [c for c in df.columns if c.startswith("What is the intended purpose")][0]
output_col  = [c for c in df.columns if c.startswith("Describe the AI system")][0]

print("Using description columns:", purpose_col, "and", output_col)

EMPLOYMENT_KEYWORDS = [
    "recruitment", "recruiting", "hiring", "hire", "hr",
    "human resources", "personnel", "workforce", "employee", "staffing"
]

BENEFIT_KEYWORDS = [
    "benefits", "welfare", "eligibility", "medicaid", "medicare",
    "social security", "pension", "unemployment", "public assistance",
    "healthcare", "health care"
]

def matches_keywords(text: str, keywords):
    if not isinstance(text, str):
        return False
    t = text.lower()
    return any(k in t for k in keywords)

name_col = "Use Case Name"

mask_employment = (
    df[name_col].apply(matches_keywords, args=(EMPLOYMENT_KEYWORDS,)) |
    df[purpose_col].apply(matches_keywords, args=(EMPLOYMENT_KEYWORDS,)) |
    df[output_col].apply(matches_keywords, args=(EMPLOYMENT_KEYWORDS,))
)

mask_benefits = (
    df[name_col].apply(matches_keywords, args=(BENEFIT_KEYWORDS,)) |
    df[purpose_col].apply(matches_keywords, args=(BENEFIT_KEYWORDS,)) |
    df[output_col].apply(matches_keywords, args=(BENEFIT_KEYWORDS,))
)

subset_keywords = df[mask_employment | mask_benefits].copy()
print("Subset size after keyword filter:", len(subset_keywords))

# Only keep topic areas relevant to Annex III
allowed_topics = [
    "Education & Workforce",
    "Government Services (includes Benefits and Service Delivery)",
    " Government Services (includes Benefits and Service Delivery)",  # leading space variant
    "Mission-Enabling (internal agency support)",
]

subset = subset_keywords[subset_keywords["Use Case Topic Area"].isin(allowed_topics)].copy()
print("Subset size after topic-area filter:", len(subset))

cols_of_interest = [
    "Agency",
    name_col,
    "Use Case Topic Area",
    purpose_col,
    output_col,
    "Is the AI use case rights-impacting, safety-impacting, both, or neither?",
    "Stage of Development",
]

subset_small = subset[cols_of_interest]

out_path = "us_federal_subset_first10.csv"
subset_small.head(10).to_csv(out_path, index=False)
print(f"Saved first 10 rows to: {out_path}")
