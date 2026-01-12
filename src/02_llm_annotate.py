#!/usr/bin/env python3
"""
improved_llm_annotate.py  –  v2 LLM annotation with improved prompts.

Key improvements over v1:
  - Expanded system_pattern taxonomy with concrete definitions
  - Few-shot examples for each pattern category
  - Chain-of-thought reasoning for better domain classification
  - Improved disambiguation between employment and essential_services
  - Explicit instructions to reduce "unknown" rate

Run:
    python improved_llm_annotate.py
Inputs:
    master_annotation_table_v05.csv  (or master_annotation_table.csv)
Outputs:
    master_annotation_table_llm_v2.csv
"""

import pandas as pd
import json, os, sys, time, hashlib

try:
    from openai import OpenAI
    client = OpenAI()
except ImportError:
    print("⚠ openai package not installed. Run: pip install openai")
    sys.exit(1)

MODEL = "gpt-4o"  # or "gpt-4o-mini" for cost savings
CACHE_FILE = "output/llm_predictions_cache_v2.jsonl"

# ─── Load cache ─────────────────────────────────────────────────────
cache = {}
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        for line in f:
            entry = json.loads(line.strip())
            cache[entry["key"]] = entry["result"]
    print(f"  Loaded {len(cache)} cached predictions")


def cache_key(text):
    return hashlib.md5(text.encode()).hexdigest()


def save_cache(key, result):
    cache[key] = result
    with open(CACHE_FILE, "a") as f:
        f.write(json.dumps({"key": key, "result": result}) + "\n")


# ─── Improved system prompt ─────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert legal-technical annotator for an MSc dissertation on the EU AI Act.
Your task is to classify AI incident/use-case records against the EU AI Act Annex III framework.

CLASSIFICATION SCHEMA:

1. annex_domain (SINGLE LABEL – pick the BEST fit):
   - "employment": The AI system is used for recruitment, selection, CV screening, candidate
     evaluation, workplace monitoring, performance evaluation, task allocation, promotion/termination
     decisions, or any other worker management function (Annex III(4)).
     NOTE: Generic workforce analytics or labour market statistics without individual-level
     decisions do NOT qualify.
   - "essential_services": The AI system is used by/on behalf of public authorities to evaluate
     eligibility for public assistance/benefits/healthcare, grant/reduce/revoke/reclaim benefits,
     credit scoring, emergency dispatch triage, risk assessment for insurance, child protection
     decisions, or welfare fraud detection that affects eligibility (Annex III(5a)).
   - "unknown": Only if genuinely impossible to determine from the available text.

2. system_pattern (SINGLE LABEL – pick the BEST fit):
   - "llm_decision_support": System uses a large language model or generative AI to assist,
     inform, or automate decisions. Look for: ChatGPT, GPT, Gemini, Claude, LLM, generative AI,
     AI-powered chatbot providing substantive advice, AI-generated risk assessments.
   - "llm_assisted_screening": System uses LLM/generative AI specifically for screening,
     filtering, or ranking candidates/applications. Look for: AI screening, automated shortlisting
     with generative component.
   - "chatbot": System is a conversational agent (rule-based or AI-powered) that interacts with
     users in dialogue. Look for: virtual assistant, chatbot, conversational AI, customer service
     bot, IVR system.
   - "summary_assistant": System generates summaries, reports, or document drafts. Look for:
     summarisation, report generation, briefing automation, document drafting.
   - "surveillance_monitor": System monitors, tracks, or surveils individuals. Look for:
     surveillance, CCTV, facial recognition, biometric monitoring, location tracking,
     productivity monitoring, body cameras.
   - "profiling_scoring": System creates profiles, risk scores, or predictions about individuals.
     Look for: risk scoring, fraud detection, predictive policing, credit scoring, recidivism
     prediction, anomaly detection, algorithmic profiling.
   - "classification_triage": System classifies, categorises, or triages cases/people. Look for:
     automated classification, triage, priority assignment, categorisation.
   - "resource_allocation": System allocates resources, benefits, or services. Look for:
     resource allocation, benefit calculation, automated disbursement, scheduling.
   - "not_llm": System clearly uses traditional ML, rule-based algorithms, or statistical models
     WITHOUT any LLM/generative AI component. Look for: algorithm, decision tree, logistic
     regression, rule-based, random forest, neural network (non-LLM), statistical model.
   - "unknown": Only if genuinely impossible to determine the system type.

3. rights (MULTI-LABEL, semicolon-separated):
   - "non_discrimination": Evidence of bias, unfair treatment of protected groups, disparate
     impact, or algorithmic discrimination.
