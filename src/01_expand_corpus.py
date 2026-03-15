# Expand corpus to >=150 records by adding deduplicated AIAAIC entries.

import pandas as pd
import re, os, sys

if not os.path.exists("data/master_annotation_table_v01.csv"):
    print("⚠ master_annotation_table.csv not found!")
    sys.exit(1)

master = pd.read_csv("data/master_annotation_table_v01.csv", encoding="utf-8")
print(f"Existing master: {len(master)} rows")
print(f"  Sources: {master['source'].value_counts().to_dict()}")

used_titles = set(master["title"].astype(str).str.strip().str.lower())
print(f"  Unique titles: {len(used_titles)}")

aiaaic_path = "data/aiaaic/AIAAIC_Repository_Incidents.csv"
if not os.path.exists(aiaaic_path):
    import glob
    matches = glob.glob("*AIAAIC*Incidents*.csv")
    if matches:
        aiaaic_path = matches[0]
    else:
        print("⚠ AIAAIC incidents CSV not found!")
        sys.exit(1)

aiaaic = pd.read_csv(aiaaic_path, header=1, encoding="utf-8",
                      on_bad_lines="skip", low_memory=False)
print(f"\nAIAAIC CSV: {len(aiaaic)} rows")
print(f"  Columns: {list(aiaaic.columns[:8])}")

assert "Headline" in aiaaic.columns, f"Expected 'Headline' column, got: {list(aiaaic.columns[:5])}"

EMPLOYMENT_KW = [
    "employment", "employee", "worker", "workforce", "recruitment", "hiring",
    "applicant", "candidate", "cv", "resume", "hr ", "human resources",
    "layoff", "termination", "fired", "promotion", "gig work", "labour",
    "labor", "workplace", "shift", "task allocation", "wage", "salary",
    "job ad", "job screen", "hiring algorithm",
]
BENEFITS_KW = [
    "benefit", "welfare", "social security", "public assistance",
    "unemployment", "disability", "pension", "healthcare", "medicaid",
    "veteran", "fraud", "eligibility", "public service", "essential service",
    "housing", "food stamp", "universal credit", "subsidy", "asylum",
    "refugee", "immigration", "child protection", "debt recovery",
    "social protection", "insurance", "credit scor", "transplant",
    "flood", "emergency", "911", "triage",
]
PUBLIC_KW = [
    "government", "ministry", "department", "authority", "agency",
    "council", "police", "court", "justice", "dwp", "nhs",
    "public sector", "federal", "state ", "regulator", "municipal",
    "govt",
]

def score_row(row):
    text = " ".join([
        str(row.get("Headline", "")),
        str(row.get("Sector(s)", "")),
        str(row.get("Purpose(s)", "")),
        str(row.get("Issue(s)", "")),
        str(row.get("Technology(ies)", "")),
    ]).lower()
    s = 0
    if any(kw in text for kw in EMPLOYMENT_KW): s += 2
    if any(kw in text for kw in BENEFITS_KW): s += 2
    if any(kw in text for kw in PUBLIC_KW): s += 1
    return s

aiaaic["_score"] = aiaaic.apply(score_row, axis=1)

def is_duplicate(headline):
    if not isinstance(headline, str) or not headline.strip():
        return True
    h = headline.strip().lower()
    for et in used_titles:
        if h[:35] == et[:35]:
            return True
        if len(h) > 10 and len(et) > 10:
            if h in et or et in h:
                return True
    return False

aiaaic["_is_dup"] = aiaaic["Headline"].astype(str).apply(is_duplicate)
candidates = aiaaic[~aiaaic["_is_dup"]].copy()
candidates = candidates.sort_values("_score", ascending=False)

print(f"\n  After dedup: {len(candidates)} candidates (removed {aiaaic['_is_dup'].sum()} duplicates)")
print(f"  Score distribution of candidates:")
print(f"    Score 5: {(candidates['_score'] == 5).sum()}")
print(f"    Score 4: {(candidates['_score'] == 4).sum()}")
print(f"    Score 3: {(candidates['_score'] == 3).sum()}")
print(f"    Score 2: {(candidates['_score'] == 2).sum()}")
print(f"    Score 1: {(candidates['_score'] == 1).sum()}")

target = 40
expansion = candidates.head(target)

print(f"\n  Selected {len(expansion)} new AIAAIC records")
print(f"  Score range: {expansion['_score'].min()} – {expansion['_score'].max()}")
print(f"\n  Selected records:")
for i, (_, row) in enumerate(expansion.iterrows()):
    print(f"    [{row['_score']}] {str(row['AIAAIC ID#']):12s} {str(row['Headline'])[:70]}")

PATTERN_RULES = {
    "profiling_scoring": ["profil", "scor", "risk assess", "credit scor",
        "fraud detect", "anomaly", "predictive polic", "recidivism", "predict"],
    "surveillance_monitor": ["surveillance", "monitor", "track", "camera",
        "cctv", "facial recogn", "biometric", "body cam", "recogniti"],
    "classification_triage": ["classif", "triage", "categori", "prioriti", "screen"],
    "resource_allocation": ["resource alloc", "benefit calcul", "schedul",
        "disburs", "allocat", "automat.*assign"],
    "chatbot": ["chatbot", "virtual assistant", "conversational"],
    "summary_assistant": ["summari", "report generat", "document generat"],
}

def annotate_domain(text):
    text = text.lower()
    emp = any(kw in text for kw in EMPLOYMENT_KW)
    ben = any(kw in text for kw in BENEFITS_KW)
    if emp and not ben: return "employment"
    if ben: return "essential_services"
    if emp: return "employment"
    return "unknown"

def annotate_pattern(text):
    text = text.lower()
    for pattern, rules in PATTERN_RULES.items():
        if any(re.search(r, text) for r in rules): return pattern
    llm_kw = ["llm", "large language", "chatgpt", "gpt", "generative ai", "genai"]
    if any(kw in text for kw in llm_kw): return "llm_decision_support"
    nonllm = ["algorithm", "machine learning", "neural network", "automat"]
    if any(kw in text for kw in nonllm): return "not_llm"
    return "unknown"

def annotate_rights(text):
    text = text.lower()
    r = []
    if any(kw in text for kw in ["bias", "discriminat", "unfair", "racial", "gender", "ethnic"]): r.append("non_discrimination")
    if any(kw in text for kw in ["privacy", "data protection", "surveillance", "gdpr", "personal data"]): r.append("privacy_data_protection")
    if any(kw in text for kw in ["welfare", "benefit", "eligibility", "pension", "social protection"]): r.append("access_social_protection")
    if any(kw in text for kw in ["transparency", "accountability", "redress", "appeal", "opaque"]): r.append("good_administration")
    return ";".join(r) if r else "other"

def annotate_harms(text):
    text = text.lower()
    h = []
    if any(kw in text for kw in ["exclud", "denied", "reject", "wrongly flag", "false positive"]): h.append("unfair_exclusion")
    if any(kw in text for kw in ["data breach", "leak", "hack"]): h.append("privacy_breach")
    if any(kw in text for kw in ["misinformation", "hallucin", "inaccura", "error", "incorrect"]): h.append("misinformation_error")
    if any(kw in text for kw in ["procedural", "no appeal", "opaque", "black box"]): h.append("procedural_unfairness")
    return ";".join(h) if h else "other"

new_rows = []
for _, row in expansion.iterrows():
    full_text = " ".join([
        str(row.get("Headline", "")),
        str(row.get("Sector(s)", "")),
        str(row.get("Purpose(s)", "")),
        str(row.get("Issue(s)", "")),
        str(row.get("Technology(ies)", "")),
    ])
    summary = str(row.get("Summary/links", ""))
    desc = full_text
    if summary and summary != "nan":
        desc = summary[:200] + " | " + full_text

    new_rows.append({
        "source": "AIAAIC",
        "source_id": str(row.get("AIAAIC ID#", "")),
        "title": str(row.get("Headline", ""))[:120],
        "description": desc[:500],
        "annex_domain": annotate_domain(full_text),
        "system_pattern": annotate_pattern(full_text),
        "rights": annotate_rights(full_text),
        "harms": annotate_harms(full_text),
        "actor_role": "deployer",
        "notes": "rule-based annotation",
    })

all_rows = list(master.to_dict("records"))

all_rows.extend(new_rows)
print(f"\n  Added {len(new_rows)} new AIAAIC records")

# Add USFED expansion if available
if os.path.exists("data/usfed/usfed_expansion.csv"):
    usfed = pd.read_csv("data/usfed/usfed_expansion.csv", encoding="utf-8", low_memory=False)
    existing_titles_now = {r["title"].strip().lower() for r in all_rows if "title" in r}

    name_cols = [c for c in usfed.columns if "name" in c.lower()]
    name_col = name_cols[0] if name_cols else usfed.columns[0]
    text_cols = [c for c in usfed.columns if usfed[c].dtype == object]

    added_usfed = 0
    for _, row in usfed.iterrows():
        title = str(row.get(name_col, ""))[:80]
        if title.strip().lower() not in existing_titles_now:
            full_text = " ".join(str(row.get(c, "")) for c in text_cols)
            all_rows.append({
                "source": "USFED", "source_id": title, "title": title,
                "description": full_text[:500],
                "annex_domain": annotate_domain(full_text),
                "system_pattern": annotate_pattern(full_text),
                "rights": annotate_rights(full_text),
                "harms": annotate_harms(full_text),
                "actor_role": "deployer",
                "notes": "rule-based annotation",
            })
            added_usfed += 1
    print(f"  Added {added_usfed} new USFED records")

final = pd.DataFrame(all_rows)
final.to_csv("data/master_annotation_table_v05.csv", index=False, encoding="utf-8")
print(f"\n{'='*60}")
print(f"[OK] Saved master_annotation_table_v05.csv with {len(final)} records")
print(f"{'='*60}")

print(f"\n-- Source distribution --")
print(final["source"].value_counts().to_string())
print(f"\n-- Domain distribution --")
print(final["annex_domain"].value_counts().to_string())
print(f"\n-- System pattern distribution --")
print(final["system_pattern"].value_counts().to_string())
