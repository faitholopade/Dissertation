"""Step 02: LLM-assisted annotation using Claude API.

Classifies each record by Annex III domain, system pattern, fundamental
rights, and harm categories using few-shot prompting with Claude.
Responses are cached to avoid redundant API calls on re-runs.

Inputs:
    data/master_annotation_table_v05.csv

Output:
    output/master_annotation_table_llm_v2.csv
"""

import pandas as pd
import json, os, sys, time, hashlib

try:
    from anthropic import Anthropic
    client = Anthropic()
except ImportError:
    print("⚠  anthropic package not installed. Run: pip install anthropic")
    sys.exit(1)

MODEL = "claude-sonnet-4-20250514"
CACHE_FILE = "output/llm_predictions_cache_v2.jsonl"

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
   - "privacy_data_protection": Excessive data collection, surveillance, GDPR concerns, profiling
     without consent, data breaches.
   - "access_social_protection": Barriers to benefits, welfare, healthcare, social services, or
     public assistance.
   - "good_administration": Lack of transparency, no right to explanation, opaque decision-making,
     no appeal/redress mechanism.
   - "other": Only if none of the above apply.

4. harms (MULTI-LABEL, semicolon-separated):
   - "unfair_exclusion": People wrongly denied services, benefits, or opportunities.
   - "privacy_breach": Actual data breach, leak, or unauthorised surveillance.
   - "misinformation_error": System produced incorrect/misleading information or hallucinations.
   - "procedural_unfairness": Decisions made without due process, human oversight, or explanation.
   - "other": Only if none of the above apply.

RULES:
- REDUCE "unknown" labels. Most real-world AI incidents CAN be classified.
- For system_pattern, if the system is clearly algorithmic but not generative/LLM, use
  the most specific non-LLM pattern (profiling_scoring, surveillance_monitor, etc.),
  then fall back to "not_llm" only if no specific pattern fits.
- Always provide a brief rationale.

Return ONLY valid JSON with keys:
annex_domain, system_pattern, rights, harms, confidence (0-1), rationale (2 sentences max)
"""

FEW_SHOT_EXAMPLES = [
    {
        "role": "user",
        "content": """Incident: Michigan MiDAS unemployment insurance fraud detection
Description: Michigan's automated system MiDAS wrongly accused over 40,000 people of unemployment insurance fraud, leading to wage garnishments and financial ruin for innocent claimants."""
    },
    {
        "role": "assistant",
        "content": json.dumps({
            "annex_domain": "essential_services",
            "system_pattern": "profiling_scoring",
            "rights": "access_social_protection;non_discrimination;good_administration",
            "harms": "unfair_exclusion;procedural_unfairness",
            "confidence": 0.95,
            "rationale": "System evaluated eligibility for unemployment benefits and wrongly flagged claimants as fraudulent, directly affecting access to social protection. It used algorithmic scoring/profiling without adequate human oversight."
        })
    },
    {
        "role": "user",
        "content": """Incident: Starbucks automated shift scheduling system
Description: Starbucks used an automated scheduling algorithm that assigned unpredictable shifts to workers, disrupting their personal lives, childcare, and second jobs."""
    },
    {
        "role": "assistant",
        "content": json.dumps({
            "annex_domain": "employment",
            "system_pattern": "resource_allocation",
            "rights": "non_discrimination;privacy_data_protection",
            "harms": "procedural_unfairness",
            "confidence": 0.9,
            "rationale": "System allocated work shifts to employees based on algorithmic optimisation, falling under Annex III(4) worker management. The resource allocation pattern is most specific as it assigns tasks/schedules to workers."
        })
    },
    {
        "role": "user",
        "content": """Incident: Netherlands SyRI welfare fraud detection automation
Description: The Dutch government used SyRI (System Risk Indication) to detect welfare fraud by combining and analysing large datasets of personal information from various government agencies."""
    },
    {
        "role": "assistant",
        "content": json.dumps({
            "annex_domain": "essential_services",
            "system_pattern": "profiling_scoring",
            "rights": "privacy_data_protection;non_discrimination;access_social_protection",
            "harms": "unfair_exclusion;privacy_breach",
            "confidence": 0.95,
            "rationale": "SyRI profiled citizens using government data to detect welfare fraud, directly impacting access to social protection. The system is a profiling/scoring tool that assessed risk of fraud among benefit recipients."
        })
    },
]

def annotate_record(title, description, source=""):
    user_msg = f"""Incident: {title}
Source: {source}
Description: {description[:1500]}"""

    key = cache_key(user_msg)
    if key in cache:
        return cache[key]

    messages = FEW_SHOT_EXAMPLES + [
        {"role": "user", "content": user_msg}
    ]

    try:
        response = client.messages.create(
            model=MODEL,
            system=SYSTEM_PROMPT,
            messages=messages,
            temperature=0,
            max_tokens=500,
        )
        result = json.loads(response.content[0].text)
        save_cache(key, result)
        return result

    except Exception as e:
        print(f"  ⚠ API error: {e}")
        time.sleep(2)
        return {
            "annex_domain": "unknown", "system_pattern": "unknown",
            "rights": "other", "harms": "other",
            "confidence": 0, "rationale": f"API error: {str(e)[:100]}"
        }

def main():
    for path in ["data/master_annotation_table_v05.csv", "data/master_annotation_table_v01.csv"]:
        if os.path.exists(path):
            df = pd.read_csv(path)
            print(f"Loaded {len(df)} rows from {path}")
            break
    else:
        print("⚠  No master annotation table found!")
        sys.exit(1)

    title_col = "title" if "title" in df.columns else df.columns[0]
    desc_cols = [c for c in df.columns if c.lower() in
                 ["description", "desc", "summary", "text", "summary/links"]]
    if not desc_cols:
        desc_cols = [c for c in df.columns if df[c].dtype == object and c != title_col][:1]

    source_col = "source" if "source" in df.columns else None

    llm_results = []
    for i, row in df.iterrows():
        title = str(row.get(title_col, ""))
        desc = " ".join(str(row.get(c, "")) for c in desc_cols)
        source = str(row.get(source_col, "")) if source_col else ""

        result = annotate_record(title, desc, source)
        llm_results.append(result)

        domain = result.get("annex_domain", "unknown")
        pattern = result.get("system_pattern", "unknown")
        print(f"  [{i+1}/{len(df)}] {source} / {title[:50]} -> {domain} | {pattern}")

        if cache_key(f"Incident: {title}\nSource: {source}\nDescription: {desc[:1500]}") not in cache:
            time.sleep(0.5)

    df["llm_v2_annex_domain"] = [r.get("annex_domain", "unknown") for r in llm_results]
    df["llm_v2_system_pattern"] = [r.get("system_pattern", "unknown") for r in llm_results]
    df["llm_v2_rights"] = [r.get("rights", "other") for r in llm_results]
    df["llm_v2_harms"] = [r.get("harms", "other") for r in llm_results]
    df["llm_v2_confidence"] = [r.get("confidence", 0) for r in llm_results]
    df["llm_v2_rationale"] = [r.get("rationale", "") for r in llm_results]

    # Hybrid columns: prefer LLM label unless it says unknown
    df["hybrid_v2_annex_domain"] = df.apply(
        lambda r: r["llm_v2_annex_domain"]
        if r.get("annex_domain") == "unknown" or r.get("annex_domain") == r["llm_v2_annex_domain"]
        else (r.get("annex_domain") if r["llm_v2_annex_domain"] == "unknown"
              else r["llm_v2_annex_domain"]),
        axis=1
    )
    df["hybrid_v2_system_pattern"] = df.apply(
        lambda r: r["llm_v2_system_pattern"]
        if r.get("system_pattern") == "unknown" or r.get("system_pattern") == r["llm_v2_system_pattern"]
        else (r.get("system_pattern") if r["llm_v2_system_pattern"] == "unknown"
              else r["llm_v2_system_pattern"]),
        axis=1
    )

    out_path = "output/master_annotation_table_llm_v2.csv"
    df.to_csv(out_path, index=False)
    print(f"\n[OK] Saved {out_path}")

    print(f"\n-- LLM v2 Domain Distribution --")
    print(df["llm_v2_annex_domain"].value_counts().to_string())
    print(f"\n-- LLM v2 System Pattern Distribution --")
    print(df["llm_v2_system_pattern"].value_counts().to_string())
    print(f"\n-- Hybrid v2 Domain Distribution --")
    print(df["hybrid_v2_annex_domain"].value_counts().to_string())
    print(f"\n-- Hybrid v2 System Pattern Distribution --")
    print(df["hybrid_v2_system_pattern"].value_counts().to_string())

    print(f"\n-- Unknown Rates --")
    for col_label, col_name in [
        ("Keyword domain", "annex_domain"),
        ("LLM v2 domain", "llm_v2_annex_domain"),
        ("Hybrid v2 domain", "hybrid_v2_annex_domain"),
        ("Keyword pattern", "system_pattern"),
        ("LLM v2 pattern", "llm_v2_system_pattern"),
        ("Hybrid v2 pattern", "hybrid_v2_system_pattern"),
    ]:
        if col_name in df.columns:
            unk = (df[col_name] == "unknown").sum()
            print(f"  {col_label}: {unk}/{len(df)} ({unk/len(df):.1%})")

if __name__ == "__main__":
    main()
