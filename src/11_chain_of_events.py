"""
11_chain_of_events.py  —  Chain-of-events + mitigation extraction (Step 11)

Adds three new columns to each record by prompting Claude:
  - root_cause       : technology_failure | context_of_use | missing_mitigation |
                        human_error | data_quality | policy_gap | unknown
  - mitigation_reported : free-text summary of any post-incident response, or "none_reported"
  - source_type       : news_article | court_case | regulator_opinion | government_inventory | unknown

Aligned with the AI Office incident-reporting template's focus on causal chains.

Usage:
    python src/11_chain_of_events.py          (from project root)
    python 11_chain_of_events.py              (from src/)
"""

import json, time, os, sys
from pathlib import Path
from typing import Dict, Any
import anthropic
import pandas as pd

# ── Auto-resolve project root ────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
# If we're inside src/, go up one level; otherwise stay put
if SCRIPT_DIR.name == "src":
    PROJECT_ROOT = SCRIPT_DIR.parent
else:
    PROJECT_ROOT = SCRIPT_DIR
os.chdir(PROJECT_ROOT)
print(f"Working directory: {PROJECT_ROOT}")

# ── Config ───────────────────────────────────────────────────────────────────
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL_NAME = "claude-sonnet-4-20250514"
MAX_RETRIES = 3
RETRY_DELAY = 5

INPUT_CSV  = PROJECT_ROOT / "output" / "master_annotation_table_final.csv"
OUTPUT_CSV = PROJECT_ROOT / "output" / "master_annotation_table_causal.csv"
LOG_JSONL  = PROJECT_ROOT / "output" / "causal_annotation_log.jsonl"
CACHE_JSON = PROJECT_ROOT / "output" / "causal_cache.json"

# ── Root-cause categories (aligned with AI Office template) ──────────────────
ROOT_CAUSE_LABELS = [
    "technology_failure",
    "context_of_use",
    "missing_mitigation",
    "human_error",
    "data_quality",
    "policy_gap",
    "unknown",
]

SOURCE_TYPE_LABELS = [
    "news_article",
    "court_case",
    "regulator_opinion",
    "government_inventory",
    "unknown",
]

# ── System prompt ────────────────────────────────────────────────────────────
SYSTEM_MSG = """You are an expert risk analyst extracting causal information from
AI incident reports and public-sector AI use-case descriptions, aligned with
the EU AI Office serious-incident reporting template.

DEFINITIONS
-----------
root_cause — the PRIMARY factor that led to the incident or risk. Pick ONE:
  • technology_failure   — bug, model error, algorithmic flaw, system malfunction
  • context_of_use       — system deployed outside intended scope, wrong population,
                           cultural / jurisdictional mismatch
  • missing_mitigation   — no safeguard, human oversight, or control was in place
  • human_error          — operator mistake, misuse, insufficient training
  • data_quality         — biased, incomplete, unrepresentative, or poisoned data
  • policy_gap           — absence of regulation, unclear rules, legal loophole
  • unknown              — text does not contain enough information to determine

mitigation_reported — a SHORT (≤30 words) summary of any corrective action,
  company response, regulatory action, or system withdrawal mentioned.
  If nothing is mentioned, return exactly "none_reported".

source_type — what kind of document is this?
  • news_article          — press / media report
  • court_case            — judicial ruling, court filing, legal challenge
  • regulator_opinion     — decision or statement by a regulator / DPA / authority
  • government_inventory  — official government AI use-case catalogue entry
  • unknown               — cannot determine

Return ONLY valid JSON with keys: root_cause, mitigation_reported, source_type.
No extra text."""

PROMPT_TEMPLATE = """Analyse the following AI incident or use-case record.

SOURCE: {source}
TITLE:  {title}
DESCRIPTION (may be truncated):
{description}

Return STRICTLY a JSON object with keys "root_cause", "mitigation_reported", "source_type"."""

# ── Few-shot examples ────────────────────────────────────────────────────────
FEW_SHOT = """Here are annotated examples:

EXAMPLE 1
SOURCE: AIAAIC
TITLE: Australia scraps robodebt welfare debt recovery
DESCRIPTION: The Australian government's automated debt recovery system incorrectly calculated welfare overpayments using income averaging, leading to hundreds of thousands of false debt notices. A Royal Commission found the scheme was unlawful. The system was scrapped and a $1.8 billion settlement was reached.
ANSWER: {"root_cause": "technology_failure", "mitigation_reported": "System scrapped; Royal Commission held; $1.8B settlement paid to affected citizens", "source_type": "news_article"}

EXAMPLE 2
SOURCE: USFED
TITLE: Policy Analyst Assistant
DESCRIPTION: The Student and Exchange Visitor Program (SEVP) uses AI to help policy analysts quickly find and summarize information across internal documents.
ANSWER: {"root_cause": "unknown", "mitigation_reported": "none_reported", "source_type": "government_inventory"}

EXAMPLE 3
SOURCE: AIAAIC
TITLE: HireVue recruitment facial analysis screening
DESCRIPTION: HireVue used facial analysis in video interviews to assess job candidates. The FTC investigated concerns about bias and deception. HireVue discontinued the facial analysis component following public backlash and regulatory scrutiny.
ANSWER: {"root_cause": "context_of_use", "mitigation_reported": "Facial analysis feature discontinued following FTC scrutiny and public backlash", "source_type": "news_article"}

Now analyse the following record:"""

# ── LLM call ─────────────────────────────────────────────────────────────────
def call_llm(prompt: str) -> Dict[str, Any]:
    for attempt in range(MAX_RETRIES):
        try:
            resp = client.messages.create(
                model=MODEL_NAME,
                max_tokens=256,
                temperature=0,
                system=SYSTEM_MSG,
                messages=[{"role": "user", "content": prompt}],
            )
            text = ""
            for block in resp.content:
                if block.type == "text":
                    text = block.text
            obj = json.loads(text)
            return {
                "root_cause":          obj.get("root_cause", "unknown"),
                "mitigation_reported": obj.get("mitigation_reported", "none_reported"),
                "source_type":         obj.get("source_type", "unknown"),
            }
        except json.JSONDecodeError:
            return {"root_cause": "unknown", "mitigation_reported": "none_reported",
                    "source_type": "unknown"}
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                print(f"  Retry {attempt+1} after error: {e}")
                time.sleep(RETRY_DELAY)
            else:
                print(f"  Failed after {MAX_RETRIES} attempts: {e}")
                return {"root_cause": "unknown", "mitigation_reported": "none_reported",
                        "source_type": "unknown"}


# ── Source-type heuristic (zero LLM calls for obvious cases) ─────────────────
def heuristic_source_type(source: str) -> str:
    s = str(source).strip().upper()
    if s == "USFED":
        return "government_inventory"
    if s == "ECTHR":
        return "court_case"
    return ""


# ── Main ─────────────────────────────────────────────────────────────────────
def run_causal_extraction():
    if not INPUT_CSV.exists():
        print(f"ERROR: Cannot find {INPUT_CSV}")
        print(f"  Expected at: {INPUT_CSV.resolve()}")
        print(f"  Contents of output/:")
        out_dir = PROJECT_ROOT / "output"
        if out_dir.exists():
            for f in sorted(out_dir.glob("master_annotation*")):
                print(f"    {f.name}")
        sys.exit(1)

    df = pd.read_csv(INPUT_CSV)
    print(f"Loaded {len(df)} rows from {INPUT_CSV.name}")

    # Load cache
    cache = {}
    if CACHE_JSON.exists():
        with open(CACHE_JSON, "r") as f:
            cache = json.load(f)
        print(f"Loaded {len(cache)} cached causal annotations")

    new_rows = []
    with open(LOG_JSONL, "w", encoding="utf-8") as logf:
        for idx, row in df.iterrows():
            sid = str(row.get("source_id", row.get("sourceid", "")))
            source = str(row.get("source", ""))
            title  = str(row.get("title", ""))[:200]
            desc   = str(row.get("description", ""))[:800]

            if sid in cache:
                result = cache[sid]
            else:
                h_st = heuristic_source_type(source)

                prompt = FEW_SHOT + "\n" + PROMPT_TEMPLATE.format(
                    source=source, title=title, description=desc
                )
                result = call_llm(prompt)

                if h_st:
                    result["source_type"] = h_st

                cache[sid] = result

                log_entry = {
                    "idx": int(idx), "source_id": sid,
                    "raw_response": result,
                    "timestamp": time.time(), "model": MODEL_NAME,
                }
                logf.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

            rc = result.get("root_cause", "unknown").lower().strip()
            if rc not in ROOT_CAUSE_LABELS:
                rc = "unknown"

            st = result.get("source_type", "unknown").lower().strip()
            if st not in SOURCE_TYPE_LABELS:
                st = "unknown"

            new_rows.append({
                "root_cause":          rc,
                "mitigation_reported": result.get("mitigation_reported", "none_reported"),
                "source_type":         st,
            })
            print(f"  {idx+1}/{len(df)}  {source:<7} {title[:50]:<52} -> {rc}")

    # Save cache
    with open(CACHE_JSON, "w") as f:
        json.dump(cache, f, ensure_ascii=False, indent=1)

    causal_df = pd.DataFrame(new_rows)
    merged = pd.concat([df.reset_index(drop=True), causal_df], axis=1)
    merged.to_csv(OUTPUT_CSV, index=False)
    print(f"\nSaved {OUTPUT_CSV.name}  ({len(merged)} rows, {len(merged.columns)} cols)")

    print("\n-- Root Cause Distribution --")
    print(merged["root_cause"].value_counts().to_string())
    print("\n-- Source Type Distribution --")
    print(merged["source_type"].value_counts().to_string())
    mit = merged[merged["mitigation_reported"] != "none_reported"]
    print(f"\nRecords with mitigation reported: {len(mit)}/{len(merged)} "
          f"({100*len(mit)/len(merged):.1f}%)")

    summary = merged.groupby(["root_cause", "source_type"]).size().reset_index(name="count")
    summary.to_csv(PROJECT_ROOT / "output" / "causal_summary.csv", index=False)
    print("output/causal_summary.csv")


if __name__ == "__main__":
    run_causal_extraction()
