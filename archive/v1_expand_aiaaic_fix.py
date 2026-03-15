# expand_aiaaic_fix.py — Diagnose and expand AIAAIC records robustly.

import pandas as pd
import os, sys, glob

candidates = [
    "AIAAIC Repository - Incidents.csv",
    "AIAAIC Repository - Incidents and Controversies.csv",
] + glob.glob("*AIAAIC*.csv") + glob.glob("*aiaaic*.csv")

candidates = list(dict.fromkeys(candidates))

found_path = None
for path in candidates:
    if os.path.exists(path) and "ranked" not in path.lower() and "manual" not in path.lower() and "expansion" not in path.lower():
        found_path = path
        break

if not found_path:
    print("⚠ Cannot find AIAAIC incidents CSV!")
    print(f"  Searched: {candidates}")
    print(f"  Files in directory: {[f for f in os.listdir('.') if 'aiaaic' in f.lower() or 'AIAAIC' in f]}")
    sys.exit(1)

print(f"Found: {found_path}")
print(f"File size: {os.path.getsize(found_path):,} bytes\n")

df = None
for enc in ["utf-8", "cp1252", "latin-1"]:
    for header_row in [0, 1]:
        try:
            df = pd.read_csv(found_path, header=header_row, encoding=enc, 
                             on_bad_lines="skip", low_memory=False)
            if len(df) > 10 and len(df.columns) > 3:
                print(f"  Read OK: encoding={enc}, header={header_row}")
                print(f"  Shape: {df.shape}")
                break
            else:
                df = None
        except Exception as e:
            df = None
    if df is not None:
        break

if df is None:
    print("⚠ Could not read the CSV with any encoding/header combo!")
    sys.exit(1)

print(f"\n  Columns ({len(df.columns)}):")
for i, c in enumerate(df.columns[:20]):
    sample = df[c].dropna().iloc[0] if len(df[c].dropna()) > 0 else "N/A"
    print(f"    [{i}] {c!r:40s}  sample: {str(sample)[:60]}")

id_col = None
title_col = None
desc_col = None
text_cols = []

for c in df.columns:
    cl = c.lower().strip()
    if df[c].dtype == object:
        text_cols.append(c)
    if ("id" in cl or "number" in cl) and id_col is None and "aiaaic" in cl:
        id_col = c
    elif "headline" in cl or "title" in cl or "incident" in cl.split():
        title_col = c
    elif "description" in cl or "summary" in cl or "details" in cl:
        desc_col = c

if id_col is None:
    for c in df.columns:
        if df[c].astype(str).str.match(r"^AIAAIC\d+").any():
            id_col = c
            break
    if id_col is None:
        id_col = df.columns[0]

if title_col is None:
    for c in text_cols[1:5]:
        if df[c].astype(str).str.len().mean() > 20:
            title_col = c
            break
    if title_col is None:
        title_col = text_cols[1] if len(text_cols) > 1 else text_cols[0]

print(f"\n  ID col:    {id_col}")
print(f"  Title col: {title_col}")
print(f"  Desc col:  {desc_col}")

used_ids = set()
for f in ["aiaaic_ranked_top50.csv", "aiaaic_manual_extra.csv"]:
    if os.path.exists(f):
        used = pd.read_csv(f, encoding="utf-8")
        for c in used.columns[:3]:
            ids = used[c].astype(str).str.strip()
            matches = ids[ids.str.match(r"^AIAAIC\d+", na=False)]
            if len(matches) > 0:
                used_ids.update(matches.tolist())
                break
            used_ids.update(ids.tolist())

if os.path.exists("master_annotation_table.csv"):
    mt = pd.read_csv("master_annotation_table.csv", encoding="utf-8")
    aiaaic_rows = mt[mt.get("source", pd.Series()) == "AIAAIC"]
    if "source_id" in aiaaic_rows.columns:
        used_ids.update(aiaaic_rows["source_id"].astype(str).str.strip().tolist())
    if "title" in aiaaic_rows.columns:
        used_ids.update(aiaaic_rows["title"].astype(str).str.strip().tolist())

print(f"\n  Already used IDs: {len(used_ids)}")

EMPLOYMENT_KW = [
    "employment", "employee", "worker", "workforce", "recruitment", "hiring",
    "applicant", "candidate", "cv", "resume", "hr", "human resources",
    "layoff", "termination", "fired", "promotion", "gig work", "labour",
    "labor", "workplace", "shift scheduling", "task allocation", "salary",
    "wage", "contract worker", "freelance", "appraisal",
]

BENEFITS_KW = [
    "benefit", "welfare", "social security", "public assistance",
    "unemployment", "disability", "pension", "healthcare", "medicaid",
    "veteran", "fraud detection", "welfare fraud", "eligibility",
    "public service", "essential service", "housing benefit", "food stamp",
    "universal credit", "subsidy", "asylum", "refugee", "immigration",
    "child protection", "debt recovery", "robodebt", "sanctions",
    "social protection",
]

PUBLIC_KW = [
    "government", "ministry", "department", "authority", "agency",
    "council", "police", "courts", "justice", "dwp", "nhs",
    "public sector", "federal", "state", "regulator",
]

def score_text(text):
    if not isinstance(text, str):
        return 0
    text = text.lower()
    s = 0
    if any(kw in text for kw in EMPLOYMENT_KW): s += 2
    if any(kw in text for kw in BENEFITS_KW): s += 2
    if any(kw in text for kw in PUBLIC_KW): s += 1
    return s

df["_fulltext"] = df[text_cols].fillna("").astype(str).agg(" ".join, axis=1)
df["_score"] = df["_fulltext"].apply(score_text)

df["_id_str"] = df[id_col].astype(str).str.strip()
df["_title_str"] = df[title_col].astype(str).str.strip() if title_col else ""

mask = ~(df["_id_str"].isin(used_ids) | df["_title_str"].isin(used_ids))
df_new = df[mask].copy()

print(f"\n  Total rows in CSV: {len(df)}")
print(f"  After removing used: {len(df_new)}")
print(f"  With score >= 2: {(df_new['_score'] >= 2).sum()}")
print(f"  With score >= 1: {(df_new['_score'] >= 1).sum()}")

df_new = df_new.sort_values("_score", ascending=False)

target = 40
if (df_new["_score"] >= 2).sum() >= target:
    expansion = df_new[df_new["_score"] >= 2].head(target)
else:
    expansion = df_new[df_new["_score"] >= 1].head(target)

print(f"\n  Selected {len(expansion)} new AIAAIC records")
if len(expansion) > 0:
    print(f"  Score range: {expansion['_score'].min()} – {expansion['_score'].max()}")
    print(f"\n  Sample titles:")
    for _, row in expansion.head(10).iterrows():
        print(f"    [{row['_score']}] {str(row[title_col])[:80]}")

out_cols = [id_col, title_col]
if desc_col:
    out_cols.append(desc_col)
out_cols = [c for c in out_cols if c in expansion.columns]
out_cols += ["_score"]

expansion[out_cols].to_csv("aiaaic_expansion.csv", index=False, encoding="utf-8")
print(f"\n[OK] Saved aiaaic_expansion.csv with {len(expansion)} rows")

print(f"\n{'='*60}")
print("Rebuilding master_annotation_table_v05.csv...")

import re

def annotate_domain(text):
    if not isinstance(text, str): return "unknown"
    text = text.lower()
    if any(kw in text for kw in EMPLOYMENT_KW): return "employment"
    if any(kw in text for kw in BENEFITS_KW): return "essential_services"
    return "unknown"

PATTERN_RULES = {
    "profiling_scoring": ["profil", "scor", "risk assess", "credit scor",
        "fraud detect", "anomaly detect", "predictive polic", "recidivism"],
    "surveillance_monitor": ["surveillance", "monitor", "track", "camera",
        "cctv", "facial recognition", "biometric", "body cam"],
    "classification_triage": ["classif", "triage", "categori", "prioriti"],
    "resource_allocation": ["resource alloc", "benefit calcul", "schedul",
        "disburs", "allocat"],
    "chatbot": ["chatbot", "virtual assistant", "conversational"],
    "summary_assistant": ["summari", "report generat", "document generat"],
}

LLM_KW = ["llm", "large language model", "chatgpt", "gpt-4", "gpt-3",
           "generative ai", "genai", "foundation model", "chatbot"]

def annotate_pattern(text):
    if not isinstance(text, str): return "unknown"
    text = text.lower()
    for pattern, rules in PATTERN_RULES.items():
        if any(re.search(r, text) for r in rules):
            return pattern
    if any(kw in text for kw in LLM_KW):
        return "llm_decision_support"
    non_llm = ["algorithm", "machine learning", "neural network", "random forest",
               "rule-based", "statistical model", "regression"]
    if any(kw in text for kw in non_llm) and not any(kw in text for kw in LLM_KW):
        return "not_llm"
    return "unknown"

def annotate_rights(text):
    if not isinstance(text, str): return "other"
    text = text.lower()
    rights = []
    if any(kw in text for kw in ["bias", "discriminat", "unfair", "racial", "gender", "ethnic"]):
        rights.append("non_discrimination")
    if any(kw in text for kw in ["privacy", "data protection", "surveillance", "personal data", "gdpr"]):
        rights.append("privacy_data_protection")
    if any(kw in text for kw in ["welfare", "benefit", "eligibility", "social protection", "pension"]):
        rights.append("access_social_protection")
    if any(kw in text for kw in ["transparency", "accountability", "redress", "appeal", "explainab"]):
        rights.append("good_administration")
    return ";".join(rights) if rights else "other"

def annotate_harms(text):
    if not isinstance(text, str): return "other"
    text = text.lower()
    harms = []
    if any(kw in text for kw in ["exclud", "denied", "reject", "wrongly flag", "false positive"]):
        harms.append("unfair_exclusion")
    if any(kw in text for kw in ["data breach", "data leak", "privacy breach", "hack"]):
        harms.append("privacy_breach")
    if any(kw in text for kw in ["misinformation", "hallucin", "inaccura", "error", "incorrect"]):
        harms.append("misinformation_error")
    if any(kw in text for kw in ["procedural", "no appeal", "opaque", "black box", "unexplained"]):
        harms.append("procedural_unfairness")
    return ";".join(harms) if harms else "other"


records = []

if os.path.exists("master_annotation_table.csv"):
    existing = pd.read_csv("master_annotation_table.csv", encoding="utf-8")
    for _, row in existing.iterrows():
        records.append(row.to_dict())
    print(f"  Existing: {len(existing)} rows")

for _, row in expansion.iterrows():
    full_text = str(row.get("_fulltext", ""))
    title = str(row.get(title_col, ""))[:80]
    sid = str(row.get(id_col, ""))
    records.append({
        "source": "AIAAIC",
        "source_id": sid,
        "title": title,
        "description": full_text[:500],
        "annex_domain": annotate_domain(full_text),
        "system_pattern": annotate_pattern(full_text),
        "rights": annotate_rights(full_text),
        "harms": annotate_harms(full_text),
    })

if os.path.exists("usfed_expansion.csv"):
    usfed = pd.read_csv("usfed_expansion.csv", encoding="utf-8", low_memory=False)
    existing_titles = {r.get("title", "") for r in records}
    text_cols_u = [c for c in usfed.columns if usfed[c].dtype == object]
    name_cols = [c for c in usfed.columns if "name" in c.lower()]
    name_col = name_cols[0] if name_cols else usfed.columns[0]

    added = 0
    for _, row in usfed.iterrows():
        title = str(row.get(name_col, ""))[:80]
        if title in existing_titles:
            continue
        full_text = " ".join(str(row.get(c, "")) for c in text_cols_u)
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
        added += 1
    print(f"  USFED expansion: {added} rows")

final = pd.DataFrame(records)
final.to_csv("master_annotation_table_v05.csv", index=False, encoding="utf-8")
print(f"\n[OK] Saved master_annotation_table_v05.csv with {len(final)} records")
print(f"\n-- Source distribution --")
print(final["source"].value_counts().to_string())
print(f"\n-- Domain distribution --")
print(final["annex_domain"].value_counts().to_string())
