"""Step 06: Export annotated records as semantic JSON-LD.

Converts the final annotation table into a collection of JSON-LD risk
records conforming to the FRIA risk schema.

Inputs:
    output/master_annotation_table_llm_v2.csv

Output:
    output/risk_records_v2.jsonld
"""

import pandas as pd
import json, os, sys


def load_context():
    path = "schema/fria_risk_schema.jsonld"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)["@context"]
    return {"fria": "https://example.org/fria-risk-schema#"}


def export():
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

    def best_col(df, preferences):
        for p in preferences:
            if p in df.columns:
                return p
        return None

    domain_col = best_col(df, ["hybrid_v2_annex_domain", "hybrid_annex_domain", "annex_domain"])
    pattern_col = best_col(df, ["hybrid_v2_system_pattern", "hybrid_system_pattern", "system_pattern"])
    rights_col = best_col(df, ["llm_v2_rights", "rights"])
    harms_col = best_col(df, ["llm_v2_harms", "harms"])

    records = []
    for _, row in df.iterrows():
        source = str(row.get("source", ""))
        sid = str(row.get("source_id", ""))

        rights_str = str(row.get(rights_col, "other")) if rights_col else "other"
        harms_str = str(row.get(harms_col, "other")) if harms_col else "other"
        rights_list = [r.strip() for r in rights_str.split(";") if r.strip()]
        harms_list = [h.strip() for h in harms_str.split(";") if h.strip()]

        record = {
            "@type": "RiskRecord",
            "@id": f"fria:record/{source}-{sid}".replace(" ", "_"),
            "source": source,
            "sourceId": sid,
            "title": str(row.get("title", "")),
            "annexDomain": str(row.get(domain_col, "unknown")) if domain_col else "unknown",
            "systemPattern": str(row.get(pattern_col, "unknown")) if pattern_col else "unknown",
            "rightsImpacted": rights_list,
            "harmsIdentified": harms_list,
            "annotationMethod": "hybrid",
        }

        if "llm_v2_confidence" in row.index:
            record["confidence"] = float(row.get("llm_v2_confidence", 0))

        records.append(record)

    output = {
        "@context": context,
        "@graph": records
    }

    out_path = "output/risk_records_v2.jsonld"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"[OK] Wrote {len(records)} JSON-LD records to {out_path}")


if __name__ == "__main__":
    export()
