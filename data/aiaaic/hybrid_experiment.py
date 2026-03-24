# Hybrid keyword + LLM experiment for AIAAIC selection and ranking

import os
import json
import time
import random
from typing import Dict, Any, List, Optional

import pandas as pd
from openai import OpenAI


AIAAIC_CSV = "AIAAIC Repository - Incidents.csv"

LABEL_STUDIO_JSON = "project-2-at-2025-12-16-12-40-739060b4.json"

CACHE_PATH = "llm_predictions_cache.jsonl"
COMPARISON_OUT = "manual_vs_llm_comparison.csv"
RANKED_PREFIX = "aiaaic_ranked_top"

TOP_K_EXPORTS = [10, 30, 50, 100]
LLM_MAX_ITEMS = 40  # protect against accidental big spend

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TEMPERATURE = 0



EMPLOYMENT_KWS = [
    "employ", "employment", "employer", "employee", "employees",
    "worker", "workers", "workforce", "staff", "staffing",
    "recruit", "recruitment", "recruiting", "hiring", "hire", "hired",
    "applicant", "candidates", "cv", "résumé", "resume",
    "layoff", "lay-offs", "redundancy", "fired", "termination",
    "promotion", "performance review",
    "gig worker", "labour", "labor",
]

BENEFITS_KWS = [
    "benefit", "benefits", "welfare", "social security",
    "social assistance", "public assistance",
    "unemployment", "disability", "pension", "pensions",
    "child benefit", "child-benefit", "child welfare",
    "healthcare", "health care", "medicaid", "medicare",
    "veterans affairs", "veteran", "veterans",
    "welfare fraud", "overpayment", "advance payment",
    "public funds", "public funding", "funding", "grant", "grants",
    "eligibility", "means test", "means-testing", "means-tested",
    "eligibility screening",
]

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
    "dwp", "nhs", "welfare", "veterans affairs",
]

LLM_KWS = [
    "llm", "large language model",
    "chatgpt", "gpt-3", "gpt-4", "gpt4",
    "bard", "gemini", "anthropic", "claude", "grok",
    "foundation model", "generative ai", "genai",
    "chatbot",
]



def normalize(col: str) -> str:
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

TEXT_COLS = [
    "Headline", "Sector_s", "Deployer_s", "Purpose_s", "Issues",
    "External_harms", "Internal_impacts", "Summary_links",
    "Unnamed:_14", "Unnamed:_15", "Unnamed:_17", "Unnamed:_18", "Unnamed:_19",
]

def load_aiaaic() -> pd.DataFrame:
    df = pd.read_csv(AIAAIC_CSV, encoding="utf-8", low_memory=False, header=1)
    df = df[df["AIAAIC ID#"].notna()].reset_index(drop=True)
    df.rename(columns={c: normalize(c) for c in df.columns}, inplace=True)
    df["AIAAIC_ID"] = df["AIAAIC_ID"].astype(str).str.strip()
    df["headline_norm"] = df["Headline"].astype(str).str.lower().str.strip()
    return df

def row_text(row: pd.Series) -> str:
    parts = []
    for col in TEXT_COLS:
        if col in row and pd.notna(row[col]):
            parts.append(str(row[col]))
    return " ".join(parts).lower()

def count_hits(text: str, keywords: List[str]) -> int:
    return sum(1 for k in keywords if k in text)

def is_public_sector(row: pd.Series) -> bool:
    sector = str(row.get("Sector_s", "")).lower()
    deployer = str(row.get("Deployer_s", "")).lower()

    if "govt" in sector or "government" in sector:
        return True
    if any(x in sector for x in ["govt -", "govt-", "govt ", "gov."]):
        return True
    if any(x in deployer for x in ["department", "ministry", "council", "city", "municipal", "government", "dwp", "nhs"]):
        return True

    return count_hits(row_text(row), PUBLIC_SECTOR_KWS) > 0

def matches_emp_or_benefit(row: pd.Series) -> bool:
    t = row_text(row)
    return (count_hits(t, EMPLOYMENT_KWS) > 0) or (count_hits(t, BENEFITS_KWS) > 0)



def build_ranked_candidates(df: pd.DataFrame) -> pd.DataFrame:
    broad = df[df.apply(matches_emp_or_benefit, axis=1) & df.apply(is_public_sector, axis=1)].copy()

    def score_row(r):
        t = row_text(r)
        emp = count_hits(t, EMPLOYMENT_KWS)
        ben = count_hits(t, BENEFITS_KWS)
        pub = count_hits(t, PUBLIC_SECTOR_KWS)
        llm = count_hits(t, LLM_KWS)
        return emp + ben + pub + llm

    broad["kw_score"] = broad.apply(score_row, axis=1)
    broad["kw_emp_hits"] = broad.apply(lambda r: count_hits(row_text(r), EMPLOYMENT_KWS), axis=1)
    broad["kw_ben_hits"] = broad.apply(lambda r: count_hits(row_text(r), BENEFITS_KWS), axis=1)
    broad["kw_pub_hits"] = broad.apply(lambda r: count_hits(row_text(r), PUBLIC_SECTOR_KWS), axis=1)
    broad["kw_llm_hits"] = broad.apply(lambda r: count_hits(row_text(r), LLM_KWS), axis=1)

    broad.sort_values(by=["kw_score", "kw_pub_hits", "kw_emp_hits", "kw_ben_hits"], ascending=False, inplace=True)
    return broad



def normalize_manual_choice(choice: str, which: str) -> str:
    if not isinstance(choice, str):
        return ""
    c = choice.strip().lower()
    if c.startswith("not annex"):
        return "No"
    if which == "emp" and "annex iii(4" in c:
        return "Yes"
    if which == "ess" and "annex iii(5" in c:
        return "Yes"
    return ""

def normalize_rights(rights: List[str]) -> str:
    mapped = []
    for r in rights:
        if not isinstance(r, str):
            continue
        rl = r.strip().lower()
        if "non-discrimination" in rl or "non_discrimination" in rl:
            mapped.append("NON_DISCRIMINATION")
        elif "privacy" in rl:
            mapped.append("PRIVACY")
        else:
            mapped.append("OTHER")
    return ";".join(sorted(set(mapped)))

def load_labelstudio_manual(json_path: str) -> pd.DataFrame:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = []
    for item in data:
        d = item.get("data", {})
        aiaaic_id = d.get("AIAAIC_ID") or d.get("AIAAIC ID#") or d.get("AIAAIC") or ""
        aiaaic_id = str(aiaaic_id).strip()

        manual_emp = ""
        manual_ess = ""
        rights = []

        anns = item.get("annotations", [])
        if anns:
            results = anns[0].get("result", [])
            for r in results:
                name = r.get("from_name")
                choices = (r.get("value", {}) or {}).get("choices", []) or []
                if name == "annex_employment" and choices:
                    manual_emp = normalize_manual_choice(choices[0], "emp")
                elif name == "annex_essential" and choices:
                    manual_ess = normalize_manual_choice(choices[0], "ess")
                elif name == "rights" and choices:
                    rights.extend(choices)

        rows.append({
            "AIAAIC_ID": aiaaic_id,
            "manual_annex_employment": manual_emp,
            "manual_annex_essential": manual_ess,
            "manual_rights": normalize_rights(rights),
            "manual_headline": d.get("Headline", ""),
            "manual_summary": d.get("Summary_links") or d.get("Summary/links") or "",
            "manual_issues": d.get("Issues") or d.get("Issue(s)") or "",
        })

    df = pd.DataFrame(rows)
    df["AIAAIC_ID"] = df["AIAAIC_ID"].astype(str).str.strip()
    df["manual_headline_norm"] = df["manual_headline"].astype(str).str.lower().str.strip()
    return df[df["AIAAIC_ID"].str.len() > 0].copy()



def openai_client() -> OpenAI:
    return OpenAI()

def load_cache(path: str) -> Dict[str, Dict[str, Any]]:
    cache = {}
    if not os.path.exists(path):
        return cache
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            cache[obj["cache_key"]] = obj
    return cache

def append_cache(path: str, record: Dict[str, Any]) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def cache_key(aiaaic_id: str) -> str:
    return f"aiaaic::{aiaaic_id}"

SYSTEM_PROMPT = """You are annotating AI incident summaries for an MSc dissertation.
Return ONLY valid JSON.

Classify for EU AI Act Annex III:
- annex_iii_4_employment: Yes/No
- annex_iii_5a_essential_services: Yes/No

Rights (array):
- NON_DISCRIMINATION
- PRIVACY
- OTHER

Also include:
- confidence: number 0..1
- rationale_short: <=2 sentences
"""

USER_PROMPT_TEMPLATE = """Incident to classify:

Headline: {headline}
Issues: {issues}
Summary: {summary}

Annex III(4) Employment includes recruitment/selection (job ads, CV filtering, candidate evaluation) and workplace decisions (promotion/termination, task allocation, monitoring/performance evaluation of workers).

Annex III(5)(a) Essential public services/benefits includes eligibility decisions for public assistance/services (including healthcare), and granting/revoking/reclaiming benefits/services.

Return JSON with keys:
annex_iii_4_employment, annex_iii_5a_essential_services, rights, confidence, rationale_short.
"""

def validate_prediction(obj: Dict[str, Any]) -> Dict[str, Any]:
    def yesno(x):
        if isinstance(x, str):
            xl = x.strip().lower()
            if xl in ["yes", "y", "true"]:
                return "Yes"
            if xl in ["no", "n", "false"]:
                return "No"
        return "No"

    rights = obj.get("rights", [])
    if isinstance(rights, str):
        rights = [rights]
    if not isinstance(rights, list):
        rights = ["OTHER"]

    allowed_rights = {"NON_DISCRIMINATION", "PRIVACY", "OTHER"}
    rights = [r for r in rights if isinstance(r, str)]
    rights = [r.strip().upper() for r in rights]
    rights = [r for r in rights if r in allowed_rights]
    if not rights:
        rights = ["OTHER"]

    conf = obj.get("confidence", 0.5)
    try:
        conf = float(conf)
    except Exception:
        conf = 0.5
    conf = max(0.0, min(1.0, conf))

    rationale = obj.get("rationale_short", "")
    if not isinstance(rationale, str):
        rationale = ""

    return {
        "annex_iii_4_employment": yesno(obj.get("annex_iii_4_employment", "No")),
        "annex_iii_5a_essential_services": yesno(obj.get("annex_iii_5a_essential_services", "No")),
        "rights": rights,
        "confidence": conf,
        "rationale_short": rationale[:400],
    }

def llm_classify(client: OpenAI, headline: str, summary: str, issues: str) -> Dict[str, Any]:
    resp = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(headline=headline, issues=issues, summary=summary)},
        ],
    )
    raw = resp.choices[0].message.content
    obj = json.loads(raw)
    return validate_prediction(obj)

def safe_llm_call(client: OpenAI, aiaaic_id: str, headline: str, summary: str, issues: str,
                  cache: Dict[str, Dict[str, Any]], max_retries: int = 4) -> Dict[str, Any]:
    k = cache_key(aiaaic_id)
    if k in cache:
        return cache[k]["prediction"]

    for attempt in range(max_retries):
        try:
            pred = llm_classify(client, headline, summary, issues)
            rec = {"cache_key": k, "aiaaic_id": aiaaic_id, "prediction": pred, "model": MODEL_NAME, "ts": time.time()}
            append_cache(CACHE_PATH, rec)
            cache[k] = rec
            return pred
        except Exception as e:
            wait = (2 ** attempt) + random.random()
            print(f"[WARN] LLM call failed for {aiaaic_id} (attempt {attempt+1}/{max_retries}): {e}")
            time.sleep(wait)

    raise RuntimeError(f"LLM call failed after {max_retries} retries for {aiaaic_id}")



def main():
    df = load_aiaaic()
    ranked = build_ranked_candidates(df)

    print(f"[INFO] Ranked broad slice size: {len(ranked)}")

    keep_cols = [
        "AIAAIC_ID", "Headline", "Occurred", "Country_ies", "Sector_s", "Deployer_s",
        "Technology_ies", "Purpose_s", "Issues", "External_harms", "Internal_impacts",
        "Summary_links", "kw_score", "kw_emp_hits", "kw_ben_hits", "kw_pub_hits", "kw_llm_hits",
    ]
    keep_cols = [c for c in keep_cols if c in ranked.columns]

    for k in TOP_K_EXPORTS:
        out = f"{RANKED_PREFIX}{k}.csv"
        ranked[keep_cols].head(k).to_csv(out, index=False)
        print(f"[INFO] Saved {out}")

    manual = load_labelstudio_manual(LABEL_STUDIO_JSON)
    print(f"[INFO] Loaded manual annotations: {len(manual)} rows")

    merged = manual.merge(ranked, how="left", on="AIAAIC_ID", suffixes=("_manual", ""))

    # Try headline matching if ID merge missed rows
    missing = merged["Headline"].isna()
    if missing.any():
        lookup = ranked.set_index("headline_norm")
        for idx in merged[missing].index:
            hn = merged.at[idx, "manual_headline_norm"]
            if hn in lookup.index:
                rrow = lookup.loc[hn]
                if isinstance(rrow, pd.DataFrame):
                    rrow = rrow.iloc[0]
                for col in ranked.columns:
                    merged.at[idx, col] = rrow[col]

    client = openai_client()
    cache = load_cache(CACHE_PATH)

    todo = merged.head(LLM_MAX_ITEMS).copy()

    llm_rows = []
    for _, r in todo.iterrows():
        aiaaic_id = str(r.get("AIAAIC_ID", "")).strip()
        headline = str(r.get("Headline", r.get("manual_headline", "")) or "")
        summary = str(r.get("Summary_links", r.get("manual_summary", "")) or "")
        issues = str(r.get("Issues", r.get("manual_issues", "")) or "")

        if not (headline or summary or issues):
            continue

        pred = safe_llm_call(client, aiaaic_id, headline, summary, issues, cache)

        llm_rows.append({
            "AIAAIC_ID": aiaaic_id,
            "llm_annex_employment": pred["annex_iii_4_employment"],
            "llm_annex_essential": pred["annex_iii_5a_essential_services"],
            "llm_rights": ";".join(pred["rights"]),
            "llm_confidence": pred["confidence"],
            "llm_rationale_short": pred["rationale_short"],
        })

    llm_df = pd.DataFrame(llm_rows)
    comp = merged.merge(llm_df, how="left", on="AIAAIC_ID")

    out_cols = [
        "AIAAIC_ID",
        "manual_headline",
        "manual_annex_employment",
        "manual_annex_essential",
        "manual_rights",
        "kw_score", "kw_emp_hits", "kw_ben_hits", "kw_pub_hits", "kw_llm_hits",
        "llm_annex_employment", "llm_annex_essential", "llm_rights",
        "llm_confidence", "llm_rationale_short",
        "Summary_links",
    ]
    out_cols = [c for c in out_cols if c in comp.columns]
    comp[out_cols].to_csv(COMPARISON_OUT, index=False)
    print(f"[INFO] Saved comparison table: {COMPARISON_OUT}")

    valid = comp["llm_annex_employment"].notna()
    if valid.any():
        emp_agree = (comp.loc[valid, "manual_annex_employment"] == comp.loc[valid, "llm_annex_employment"]).mean()
        ess_agree = (comp.loc[valid, "manual_annex_essential"] == comp.loc[valid, "llm_annex_essential"]).mean()
        print(f"[INFO] Manual vs LLM agreement: Annex III(4) = {emp_agree:.2%}, Annex III(5)(a) = {ess_agree:.2%}")

    print("[DONE] Hybrid keyword + LLM experiment complete.")


if __name__ == "__main__":
    main()
