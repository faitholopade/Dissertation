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
