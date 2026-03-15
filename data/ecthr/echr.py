# Extract ECtHR cases on discrimination + social-benefit rights

import pandas as pd

csv_path = "final_for_viz.csv"
df = pd.read_csv(csv_path, encoding="utf-8", low_memory=False)

print("Columns:", df.columns.tolist())
print("Number of rows:", len(df))

# Article 14 = discrimination, P1 = protection of property (social benefits)
TARGET_ARTICLES = ["14", "P1"]

def article_matches(x):
    if not isinstance(x, str):
        return False
    t = x.upper()
    return any(a == t for a in TARGET_ARTICLES)

mask_articles = df["Article"].astype(str).apply(article_matches)

def is_violation(c):
    if not isinstance(c, str):
        return False
    return "violation" in c.lower()

mask_conclusion = df["Conclusion"].astype(str).apply(is_violation)

subset = df[mask_articles & mask_conclusion].copy()
print("Subset size (target articles + violation):", len(subset))

subset["Application_Number"] = subset["Application_Number"].astype(str)

subset_unique = subset.drop_duplicates(
    subset=["Document_Title", "Application_Number"]
).copy()

print("Unique cases after deduplication:", len(subset_unique))

case_law = pd.DataFrame({
    "case_name": subset_unique["Document_Title"],
    "application_number": subset_unique["Application_Number"],
    "year": subset_unique["year"],
    "country": subset_unique["Country"],
    "articles": subset_unique["Article"],
    "conclusion": subset_unique["Conclusion"],
})

case_law["keywords"] = "discrimination; social benefits"
case_law["url"] = ""

case_law_sample = case_law.head(20).copy()

out_path = "case_law_subset.csv"
case_law_sample.to_csv(out_path, index=False)
print(f"Saved case-law subset to: {out_path}")
print(case_law_sample.head())
