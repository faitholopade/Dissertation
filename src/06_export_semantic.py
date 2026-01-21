#!/usr/bin/env python3
"""
export_semantic_v2.py  –  Export all records as JSON-LD using the v2 schema.

Run:
    python export_semantic_v2.py
Inputs:
    master_annotation_table_hybrid.csv  (or _v05 or _llm_v2)
    fria_risk_schema.jsonld
Outputs:
    risk_records_v2.jsonld
"""

import pandas as pd
import json, os, sys


def load_context():
    path = "schema/fria_risk_schema.jsonld"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)["@context"]
    # Fallback minimal context
    return {"fria": "https://example.org/fria-risk-schema#"}


def export():
    # Find best available table
    for path in [
        "output/master_annotation_table_llm_v2.csv",
        "output/master_annotation_table_hybrid.csv",
        "data/master_annotation_table_v05.csv",
        "data/master_annotation_table_v01.csv"
    ]:
        if os.path.exists(path):
            df = pd.read_csv(path)
            print(f"Loaded {len(df)} rows from {path}")
            break
    else:
        print("⚠ No annotation table found!")
        sys.exit(1)

    context = load_context()

    # Determine best columns for each dimension
    def best_col(df, preferences):
        for p in preferences:
            if p in df.columns:
                return p
        return None
