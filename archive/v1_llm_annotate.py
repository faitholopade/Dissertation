# LLM-assisted annotation using Claude

import json
import time
import os
from typing import Dict, Any

import anthropic
import pandas as pd
from schema import (
    AnnexDomain, SystemPattern, RightCategory, HarmCategory,
)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL_NAME = "claude-sonnet-4-20250514"
MAX_RETRIES = 3
RETRY_DELAY = 5

FEW_SHOT_EXAMPLES = """
EXAMPLE 1:
TEXT: "Sweden's social insurance agency Försäkringskassan used a prediction algorithm to flag welfare fraud. The system was found to discriminate against women and migrants, applying higher scrutiny to these groups. Privacy advocates raised concerns about surveillance of benefit recipients."
ANSWER: {"annex_domain": "essential_services", "system_pattern": "not_llm", "rights": ["non_discrimination", "privacy_data_protection", "access_social_protection"], "harms": ["unfair_exclusion", "privacy_breach"]}

EXAMPLE 2:
TEXT: "A federal agency deployed a Conversation Training and Feedback Simulator powered by GPT-4 to help staff practice policy analyst interview scenarios. The tool generates realistic dialogue and scores responses for hiring preparation."
ANSWER: {"annex_domain": "employment", "system_pattern": "llm_decision_support", "rights": ["non_discrimination", "privacy_data_protection"], "harms": ["misinformation_error"]}

EXAMPLE 3:
TEXT: "A child protection worker used ChatGPT to draft a court report. Inaccuracies were found in the generated text, including fabricated case details. The department had no policy governing AI use in such sensitive contexts."
ANSWER: {"annex_domain": "essential_services", "system_pattern": "llm_decision_support", "rights": ["privacy_data_protection", "access_social_protection", "good_administration"], "harms": ["misinformation_error", "privacy_breach"]}

EXAMPLE 4:
TEXT: "Michigan's MiDAS system automatically flagged unemployment insurance claimants for fraud and issued repayment demands without human review. Over 40,000 fraud determinations were later found to be wrong."
ANSWER: {"annex_domain": "essential_services", "system_pattern": "not_llm", "rights": ["access_social_protection", "good_administration", "non_discrimination"], "harms": ["unfair_exclusion", "procedural_unfairness", "misinformation_error"]}
""".strip()

SYSTEM_MSG = (
    "You are an expert annotator classifying AI-related incidents and public-sector "
    "AI use cases for research on the EU AI Act.\n\n"
    "LABEL DEFINITIONS:\n"
    "annex_domain:\n"
    "  - employment: AI used in hiring, recruitment, CV screening, worker management, "
    "performance evaluation, workforce planning, gig-economy management, or HR.\n"
    "  - essential_services: AI used in welfare, benefits, social security, healthcare access, "
    "education, housing, asylum/immigration, public administration, government services, "
    "law enforcement, justice, unemployment insurance, fraud detection in public services, "
    "or any system that affects access to public benefits or services.\n"
    "  - unknown: Does not clearly fit employment or essential services.\n\n"
    "IMPORTANT: Unemployment benefits systems are 'essential_services', NOT 'employment'. "
    "Only classify as 'employment' if the AI is used by employers for HR purposes "
    "(hiring, firing, managing workers).\n\n"
    "system_pattern:\n"
    "  - llm_decision_support: An LLM/foundation model helps make or inform a decision.\n"
    "  - llm_assisted_screening: An LLM filters, ranks, or shortlists candidates/applications.\n"
    "  - chatbot: An LLM-powered conversational interface for users.\n"
    "  - summary_assistant: An LLM summarises or drafts documents.\n"
    "  - not_llm: The system clearly does NOT use an LLM (e.g. traditional ML, rule-based).\n"
    "  - unknown: Cannot determine from the text.\n\n"
    "rights (select ALL that apply):\n"
    "  - privacy_data_protection: Personal data processed, surveillance, data breach risk.\n"
    "  - non_discrimination: Risk of bias against protected groups.\n"
    "  - access_social_protection: Risk to access to welfare, benefits, public services.\n"
    "  - good_administration: Risk to transparent, fair, timely decision-making; "
    "lack of explainability, accountability, oversight, or audit.\n\n"
    "harms (select ALL that apply):\n"
    "  - unfair_exclusion: Biased or discriminatory outcomes.\n"
    "  - privacy_breach: Unauthorised data access, leak, or surveillance.\n"
    "  - misinformation_error: False, inaccurate, erroneous, flawed, or hallucinated outputs.\n"
    "  - procedural_unfairness: Lack of appeal, remedy, transparency, or due process.\n\n"
    "Return ONLY valid JSON. No extra text."
)

PROMPT_TEMPLATE = """
Here are some annotated examples to guide your classification:

{examples}

Now classify the following text. Return STRICTLY a JSON object with keys
"annex_domain", "system_pattern", "rights" (array), and "harms" (array).

TEXT:
\"\"\"{text}\"\"\"
""".strip()


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
                "annex_domain":   obj.get("annex_domain", "unknown"),
                "system_pattern": obj.get("system_pattern", "unknown"),
                "rights":         obj.get("rights", []) or [],
                "harms":          obj.get("harms", []) or [],
            }
        except json.JSONDecodeError:
            return {"annex_domain": "unknown", "system_pattern": "unknown",
                    "rights": [], "harms": []}
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                print(f"    Retry {attempt+1} after error: {e}")
                time.sleep(RETRY_DELAY)
            else:
                print(f"    Failed after {MAX_RETRIES} attempts: {e}")
                return {"annex_domain": "unknown", "system_pattern": "unknown",
                        "rights": [], "harms": []}


def _norm_domain(v):
    v = (v or "").lower()
    if v.startswith("employment"): return AnnexDomain.EMPLOYMENT
    if v.startswith("essential"):  return AnnexDomain.ESSENTIAL_SERVICES
    return AnnexDomain.UNKNOWN

def _norm_pattern(v):
    v = (v or "").lower()
    for sp in SystemPattern:
        if v == sp.value: return sp
    return SystemPattern.UNKNOWN

def _norm_rights(vals):
    out = []
    for v in (vals or []):
        for rc in RightCategory:
            if str(v).lower() == rc.value:
                out.append(rc); break
    return out or [RightCategory.OTHER]

def _norm_harms(vals):
    out = []
    for v in (vals or []):
        for hc in HarmCategory:
            if str(v).lower() == hc.value:
                out.append(hc); break
    return out or [HarmCategory.OTHER]


def annotate_with_llm(input_csv: str, output_csv: str, log_jsonl: str):
    df = pd.read_csv(input_csv)
    ann_rows = []

    with open(log_jsonl, "w", encoding="utf-8") as log_f:
        for idx, row in df.iterrows():
            text = str(row.get("description", ""))
            prompt = PROMPT_TEMPLATE.format(
                examples=FEW_SHOT_EXAMPLES,
                text=text,
            )
            raw = call_llm(prompt)

            log_entry = {
                "idx": int(idx),
                "source": row.get("source", ""),
                "source_id": str(row.get("source_id", "")),
                "prompt": prompt,
                "raw_response": raw,
                "timestamp": time.time(),
                "model": MODEL_NAME,
            }
            log_f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

            domain  = _norm_domain(raw.get("annex_domain", "unknown"))
            pattern = _norm_pattern(raw.get("system_pattern", "unknown"))
            rights  = _norm_rights(raw.get("rights", []))
            harms   = _norm_harms(raw.get("harms", []))

            ann_rows.append({
                "llm_annex_domain":   domain.value,
                "llm_system_pattern": pattern.value,
                "llm_rights":         ";".join(r.value for r in rights),
                "llm_harms":          ";".join(h.value for h in harms),
            })
            print(f"  [{idx+1}/{len(df)}] {row.get('source','')} / "
                  f"{str(row.get('title',''))[:40]} -> {domain.value}")

    ann_df = pd.DataFrame(ann_rows)
    merged = pd.concat([df.reset_index(drop=True), ann_df], axis=1)
    merged.to_csv(output_csv, index=False)
    print(f"\nSaved LLM-annotated table to {output_csv}")


if __name__ == "__main__":
    annotate_with_llm(
        input_csv="master_annotation_table.csv",
        output_csv="master_annotation_table_llm.csv",
        log_jsonl="llm_annotation_log.jsonl",
    )
