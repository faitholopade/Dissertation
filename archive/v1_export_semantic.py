# export_semantic.py — Export master_annotation_table.csv to JSON-LD.

import json
import pandas as pd
from schema import (
    RiskRecord, AnnexDomain, ActorRole, SystemPattern,
    RightCategory, HarmCategory, JSONLD_CONTEXT,
)


def _parse_enum(enum_cls, value: str):
    v = str(value or "").lower()
    for member in enum_cls:
        if member.value == v:
            return member
    return list(enum_cls)[-1]

def _parse_multi(enum_cls, value: str):
    parts = [p.strip() for p in str(value or "").split(";") if p.strip()]
    return [_parse_enum(enum_cls, p) for p in parts]


def export_jsonld(csv_path: str, jsonld_path: str):
    df = pd.read_csv(csv_path)
    records = []
    for _, row in df.iterrows():
        rec = RiskRecord(
            source=row.get("source", ""),
            source_id=str(row.get("source_id", "")),
            title=str(row.get("title", "")),
            description=str(row.get("description", "")),
            annex_domain=_parse_enum(AnnexDomain,   row.get("annex_domain", "unknown")),
            actor_role=_parse_enum(ActorRole,        row.get("actor_role", "deployer")),
            system_pattern=_parse_enum(SystemPattern, row.get("system_pattern", "unknown")),
            rights=_parse_multi(RightCategory,       row.get("rights", "")),
            harms=_parse_multi(HarmCategory,         row.get("harms", "")),
            notes=str(row.get("notes", "")),
        )
        records.append(rec.to_jsonld())

    doc = {
        "@context": JSONLD_CONTEXT,
        "@graph":   records,
    }
    with open(jsonld_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
    print(f"[OK] Wrote {len(records)} JSON-LD records to {jsonld_path}")


if __name__ == "__main__":
    export_jsonld("master_annotation_table.csv", "risk_records.jsonld")
