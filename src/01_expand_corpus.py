#!/usr/bin/env python3
"""
expand_corpus_final.py  –  Definitively expand corpus to ≥150 records.

Reads AIAAIC Repository - Incidents.csv (header on ROW 1, not row 0),
deduplicates against your existing master_annotation_table.csv,
and adds ~40 new high-relevance AIAAIC records.

Run:
    python expand_corpus_final.py
"""

import pandas as pd
import re, os, sys

# ═══════════════════════════════════════════════════════════════
# 1. LOAD EXISTING MASTER TABLE
# ═══════════════════════════════════════════════════════════════
if not os.path.exists("data/master_annotation_table_v01.csv"):
    print("⚠ master_annotation_table.csv not found!")
    sys.exit(1)

master = pd.read_csv("data/master_annotation_table_v01.csv", encoding="utf-8")
print(f"Existing master: {len(master)} rows")
print(f"  Sources: {master['source'].value_counts().to_dict()}")

# Collect ALL existing titles for dedup (lowercase, stripped)
used_titles = set(master["title"].astype(str).str.strip().str.lower())
print(f"  Unique titles: {len(used_titles)}")

# ═══════════════════════════════════════════════════════════════
# 2. LOAD AIAAIC CSV (header=1 because row 0 is a merged banner)
# ═══════════════════════════════════════════════════════════════
aiaaic_path = "data/aiaaic/AIAAIC_Repository_Incidents.csv"
if not os.path.exists(aiaaic_path):
    # Try alternate name
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

# Verify we got the right header
assert "Headline" in aiaaic.columns, f"Expected 'Headline' column, got: {list(aiaaic.columns[:5])}"

# ═══════════════════════════════════════════════════════════════
# 3. KEYWORD SCORING (Annex III relevance)
# ═══════════════════════════════════════════════════════════════
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
