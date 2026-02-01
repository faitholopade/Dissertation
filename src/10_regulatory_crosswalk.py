#!/usr/bin/env python3
"""
10_regulatory_crosswalk.py
──────────────────────────
Generates a structured regulatory crosswalk table mapping
AI Act Annex III/4 and III/5a obligations to fundamental rights
protections (privacy / data protection and non-discrimination).

Outputs:
  output/regulatory_crosswalk.csv     – machine-readable crosswalk
  output/regulatory_crosswalk.md      – Markdown for dissertation appendix
  schema/crosswalk_glossary.json      – normalised glossary of key terms

Supports Research Plan Objective 1.
"""

import json, csv, os
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT_CSV  = BASE / "output" / "regulatory_crosswalk.csv"
OUT_MD   = BASE / "output" / "regulatory_crosswalk.md"
OUT_GLOSS = BASE / "schema" / "crosswalk_glossary.json"


# ══════════════════════════════════════════════════════════════
# CROSSWALK DATA
# Each row links an Annex III obligation to applicable rights,
# relevant legal provisions, risk indicators, and schema mapping.
# ══════════════════════════════════════════════════════════════

CROSSWALK = [
    # ── Annex III/4: Employment, Workers Management ───────────
    {
        "annex_ref": "Annex III/4(a)",
        "annex_domain": "employment",
        "obligation_scope": "AI for recruitment or selection of natural persons — targeted job ads, CV filtering, candidate evaluation",
        "right_1_nondiscrimination": "EU Charter Art. 21 (Non-discrimination); Employment Equality Directive 2000/78/EC; Racial Equality Directive 2000/43/EC",
        "risk_indicators_nondiscrimination": "Demographic bias in training data; proxy discrimination via postal code, name, or language; disparate impact on protected groups (gender, age, ethnicity, disability)",
        "right_2_privacy_dp": "EU Charter Art. 8 (Data protection); GDPR Art. 22 (Automated individual decision-making); GDPR Art. 9 (Special categories)",
        "risk_indicators_privacy": "Processing of special-category data (health, ethnicity) inferred from CV; profiling without valid legal basis; lack of transparency about automated scoring",
        "fria_question": "Does the system produce or influence decisions on hiring, shortlisting, or candidate ranking? Could outputs correlate with protected characteristics?",
        "schema_mapping": "annex_domain=employment; system_pattern∈{profiling_scoring, llm_assisted_screening}; rights∈{NON-DISCRIMINATION, PRIVACY}",
        "mitigation_examples": "Bias audit on training data; disparate-impact testing; human review of shortlists; DPIA; Art. 22 safeguards (right to explanation, human intervention)",
    },
    {
        "annex_ref": "Annex III/4(b)",
        "annex_domain": "employment",
        "obligation_scope": "AI for decisions on work-related contractual relationships — promotion, termination, task allocation based on behaviour or personal traits",
        "right_1_nondiscrimination": "EU Charter Art. 21; Art. 31 (Fair working conditions); Employment Equality Directive 2000/78/EC",
        "risk_indicators_nondiscrimination": "Performance scoring correlated with protected attributes; task allocation reflecting historical bias; automated termination recommendations without context",
        "right_2_privacy_dp": "EU Charter Art. 8; GDPR Art. 5(1)(b) (Purpose limitation); GDPR Art. 6 (Lawfulness of processing)",
        "risk_indicators_privacy": "Continuous behavioural monitoring exceeding stated purpose; keystroke / productivity tracking; sentiment analysis of communications",
        "fria_question": "Does the system monitor, evaluate, or score workers in ways that affect employment terms? Is monitoring proportionate to a legitimate aim?",
        "schema_mapping": "annex_domain=employment; system_pattern∈{surveillance_monitor, profiling_scoring}; rights∈{NON-DISCRIMINATION, PRIVACY, FAIR-WORKING-CONDITIONS}",
        "mitigation_examples": "Proportionality review of monitoring scope; worker consultation (GDPR Art. 88); algorithmic impact assessment; opt-out for non-essential tracking",
    },
    {
        "annex_ref": "Annex III/4(c)",
        "annex_domain": "employment",
        "obligation_scope": "AI for monitoring and evaluating performance and behaviour of persons in work-related relationships",
        "right_1_nondiscrimination": "EU Charter Art. 21; Art. 31 (Fair working conditions)",
        "risk_indicators_nondiscrimination": "Biased performance benchmarks; emotion-recognition in evaluations; disparate discipline rates",
        "right_2_privacy_dp": "EU Charter Art. 7 (Private life); Art. 8; GDPR Art. 35 (DPIA); ePrivacy Directive (electronic communications monitoring)",
        "risk_indicators_privacy": "Workplace surveillance scope creep; processing of biometric data; lack of data minimisation; no clear retention policy",
        "fria_question": "Is worker monitoring continuous or event-based? Are workers informed about data collected and how evaluations are derived?",
        "schema_mapping": "annex_domain=employment; system_pattern=surveillance_monitor; rights∈{PRIVACY, NON-DISCRIMINATION}",
        "mitigation_examples": "Data minimisation by design; time-limited retention; worker notification and DPIA; union/works-council consultation",
    },
    # ── Annex III/5a: Essential Public Services & Benefits ────
    {
        "annex_ref": "Annex III/5(a)-i",
        "annex_domain": "essential_services",
        "obligation_scope": "AI by public authorities to evaluate eligibility for essential public assistance benefits and services, including healthcare services",
        "right_1_nondiscrimination": "EU Charter Art. 21 (Non-discrimination); Art. 34 (Social security / social assistance); Art. 35 (Healthcare); Racial Equality Directive 2000/43/EC Art. 3(1)(e)",
        "risk_indicators_nondiscrimination": "Proxy discrimination in eligibility scoring (e.g., postal code → ethnicity); under-representation of minority applicants in training data; algorithmic exclusion of vulnerable groups",
        "right_2_privacy_dp": "EU Charter Art. 8; GDPR Art. 9 (Health data, social-benefit data as special category); GDPR Art. 22",
        "risk_indicators_privacy": "Processing sensitive welfare/health data; automated profiling for fraud detection without human review; data linkage across agencies beyond original purpose",
        "fria_question": "Does the system determine, score, or rank individuals for eligibility for public benefits or healthcare access? Could errors lead to wrongful denial of essential services?",
        "schema_mapping": "annex_domain=essential_services; system_pattern∈{profiling_scoring, resource_allocation, classification_triage}; rights∈{NON-DISCRIMINATION, PRIVACY, SOCIAL-PROTECTION}",
        "mitigation_examples": "Fairness testing across demographic groups; human-in-the-loop for denial decisions; appeal/remedy mechanism; DPIA with special-category data assessment; transparent eligibility criteria",
    },
    {
        "annex_ref": "Annex III/5(a)-ii",
        "annex_domain": "essential_services",
        "obligation_scope": "AI to grant, reduce, revoke, or reclaim essential public assistance benefits and services",
        "right_1_nondiscrimination": "EU Charter Art. 21; Art. 34; Art. 47 (Effective remedy and fair trial)",
        "risk_indicators_nondiscrimination": "Automated revocation disproportionately affecting ethnic minorities; 'robodebt'-style mass debt recovery; opaque scoring penalising disadvantaged postcodes",
        "right_2_privacy_dp": "EU Charter Art. 8; GDPR Art. 5(1)(d) (Accuracy); GDPR Art. 16 (Right to rectification)",
        "risk_indicators_privacy": "Inaccurate records leading to wrongful revocation; data quality issues in linked administrative databases; no mechanism for subjects to correct errors",
        "fria_question": "Can the system revoke or reduce benefits without individual human review? Is there an accessible appeals process for affected individuals?",
        "schema_mapping": "annex_domain=essential_services; system_pattern∈{profiling_scoring, resource_allocation}; rights∈{NON-DISCRIMINATION, PRIVACY, EFFECTIVE-REMEDY}",
        "mitigation_examples": "Mandatory human review before revocation; accessible appeals process; data accuracy audits; redress fund; regular bias monitoring",
    },
    {
        "annex_ref": "Annex III/5(a)-iii",
        "annex_domain": "essential_services",
        "obligation_scope": "AI for creditworthiness evaluation or credit scoring of natural persons (excluding fraud detection)",
        "right_1_nondiscrimination": "EU Charter Art. 21; Consumer Credit Directive 2008/48/EC",
        "risk_indicators_nondiscrimination": "Credit models embedding historical lending discrimination; use of non-financial behavioural data correlating with ethnicity or gender",
        "right_2_privacy_dp": "EU Charter Art. 8; GDPR Art. 22; GDPR Art. 15 (Right of access)",
        "risk_indicators_privacy": "Opaque scoring models; use of social-media or location data without consent; inability to understand or contest a credit decision",
        "fria_question": "Does the credit scoring model use features that could proxy for protected characteristics? Can individuals obtain a meaningful explanation?",
        "schema_mapping": "annex_domain=essential_services; system_pattern=profiling_scoring; rights∈{NON-DISCRIMINATION, PRIVACY}",
        "mitigation_examples": "Feature audit for proxy variables; explainability report per Art. 22(3); alternative data opt-out; regular disparate-impact testing",
    },
    {
        "annex_ref": "Annex III/5(a)-iv",
        "annex_domain": "essential_services",
        "obligation_scope": "AI for risk assessment and pricing in life and health insurance",
