
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
        "right_1_nondiscrimination": "EU Charter Art. 21; Art. 35 (Healthcare); Gender Goods & Services Directive 2004/113/EC (prohibits gender-based pricing)",
        "risk_indicators_nondiscrimination": "Pricing models penalising genetic predisposition or chronic illness; gender- or ethnicity-correlated premium differences",
        "right_2_privacy_dp": "EU Charter Art. 8; GDPR Art. 9(2)(h) (Health data); Solvency II data requirements",
        "risk_indicators_privacy": "Inference of health status from behavioural data; use of wearable/IoT health data without explicit consent; secondary use of claims data",
        "fria_question": "Could the pricing model create access barriers to insurance for vulnerable groups? Is health data processed with explicit consent and clear purpose limitation?",
        "schema_mapping": "annex_domain=essential_services; system_pattern=profiling_scoring; rights∈{NON-DISCRIMINATION, PRIVACY, HEALTHCARE-ACCESS}",
        "mitigation_examples": "Actuarial fairness audit; prohibition of genetic data use; DPIA for health-data processing; purpose limitation enforcement; consumer disclosure",
    },
    {
        "annex_ref": "Annex III/5(a)-v",
        "annex_domain": "essential_services",
        "obligation_scope": "AI for evaluating and classifying emergency calls or dispatching emergency first-response services (police, firefighters, medical aid)",
        "right_1_nondiscrimination": "EU Charter Art. 2 (Right to life); Art. 21; Art. 35 (Healthcare)",
        "risk_indicators_nondiscrimination": "Deprioritisation of calls from certain neighbourhoods or languages; accent/dialect bias in speech recognition; lower triage priority for non-native speakers",
        "right_2_privacy_dp": "EU Charter Art. 8; ePrivacy Directive (location data); GDPR Art. 6(1)(d) (Vital interests)",
        "risk_indicators_privacy": "Location tracking of callers; recording and profiling of emergency communications; retention of sensitive call content beyond operational need",
        "fria_question": "Could triage errors lead to delayed emergency response for specific demographic groups? Is caller data retained proportionately?",
        "schema_mapping": "annex_domain=essential_services; system_pattern∈{classification_triage, resource_allocation}; rights∈{RIGHT-TO-LIFE, NON-DISCRIMINATION, PRIVACY}",
        "mitigation_examples": "Multi-language / multi-accent testing; performance monitoring by caller demographics; minimal data retention; human escalation protocol",
    },
]


# ══════════════════════════════════════════════════════════════
# GLOSSARY
# Normalised definitions for key terms used in the crosswalk
# ══════════════════════════════════════════════════════════════

GLOSSARY = {
    "Annex III/4": "AI Act high-risk category covering AI systems used in employment, workers management, and access to self-employment (Article 6(2) read with Annex III, point 4).",
    "Annex III/5a": "AI Act high-risk category covering AI systems used by public authorities or on their behalf to evaluate eligibility for essential public services and benefits, and to grant, reduce, revoke, or reclaim such services (Article 6(2) read with Annex III, point 5(a)).",
    "FRIA": "Fundamental Rights Impact Assessment — mandatory under AI Act Article 27 for deployers of high-risk AI systems that are public bodies or provide essential public services.",
    "Non-discrimination": "The right to equal treatment without distinction based on protected characteristics (sex, race, colour, ethnic or social origin, genetic features, language, religion, political opinion, disability, age, sexual orientation). EU Charter Article 21.",
    "Privacy / Data Protection": "The right to respect for private and family life (EU Charter Art. 7) and the right to the protection of personal data (EU Charter Art. 8; GDPR).",
    "Profiling": "Any form of automated processing of personal data to evaluate certain personal aspects, in particular to analyse or predict aspects concerning performance at work, economic situation, health, personal preferences, interests, reliability, behaviour, location, or movements (GDPR Art. 4(4)).",
    "Automated decision-making": "A decision based solely on automated processing, including profiling, which produces legal effects or similarly significantly affects the data subject (GDPR Art. 22).",
    "Deployer": "Any natural or legal person, public authority, agency, or other body using an AI system under its authority (AI Act Art. 3(4)).",
    "Provider": "A natural or legal person, public authority, agency, or other body that develops an AI system or has an AI system developed with a view to placing it on the market or putting it into service (AI Act Art. 3(3)).",
    "High-risk AI system": "An AI system referred to in Article 6(2) of the AI Act and listed in Annex III, subject to the requirements in Chapter III, Section 2.",
    "Disparate impact": "When a facially neutral policy, practice, or algorithmic output disproportionately and negatively affects members of a protected group, even absent discriminatory intent.",
    "DPIA": "Data Protection Impact Assessment — required under GDPR Article 35 when processing is likely to result in a high risk to the rights and freedoms of natural persons.",
    "Human-in-the-loop": "A design pattern where a human operator reviews, validates, or can override AI system outputs before they take effect on individuals.",
    "Special category data": "Personal data revealing racial or ethnic origin, political opinions, religious or philosophical beliefs, trade union membership, genetic data, biometric data, health data, or data concerning sex life or sexual orientation (GDPR Art. 9).",
    "Proxy discrimination": "Discrimination that occurs indirectly when a seemingly neutral variable (e.g., postal code, language) is statistically correlated with a protected characteristic (e.g., ethnicity).",
    "Essential public service": "A service provided by or on behalf of a public authority that individuals depend on for basic needs, including welfare, healthcare, social housing, and utilities access.",
}


# ── output functions ──────────────────────────────────────────
def save_csv():
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = list(CROSSWALK[0].keys())
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(CROSSWALK)
    print(f"  [OK] {OUT_CSV}")


def save_markdown():
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append("# Regulatory Crosswalk: AI Act Annex III/4 & III/5a → Fundamental Rights\n")
    lines.append("*Auto-generated by `10_regulatory_crosswalk.py` for dissertation Appendix.*\n")

    lines.append("## Crosswalk Table\n")
    for row in CROSSWALK:
        lines.append(f"### {row['annex_ref']} — {row['annex_domain'].replace('_', ' ').title()}\n")
        lines.append(f"**Obligation scope:** {row['obligation_scope']}\n")
        lines.append(f"| Dimension | Detail |")
        lines.append(f"|-----------|--------|")
        lines.append(f"| **Non-discrimination provisions** | {row['right_1_nondiscrimination']} |")
        lines.append(f"| **Non-discrimination risk indicators** | {row['risk_indicators_nondiscrimination']} |")
        lines.append(f"| **Privacy / data-protection provisions** | {row['right_2_privacy_dp']} |")
        lines.append(f"| **Privacy risk indicators** | {row['risk_indicators_privacy']} |")
        lines.append(f"| **FRIA guiding question** | {row['fria_question']} |")
        lines.append(f"| **Schema mapping** | `{row['schema_mapping']}` |")
        lines.append(f"| **Mitigation examples** | {row['mitigation_examples']} |")
        lines.append("")

    lines.append("## Normalised Glossary\n")
    lines.append("| Term | Definition |")
    lines.append("|------|------------|")
    for term, defn in sorted(GLOSSARY.items()):
        lines.append(f"| **{term}** | {defn} |")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"  [OK] {OUT_MD}")


def save_glossary():
    OUT_GLOSS.parent.mkdir(parents=True, exist_ok=True)
    OUT_GLOSS.write_text(json.dumps(GLOSSARY, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  [OK] {OUT_GLOSS}")


def main():
    print("=" * 60)
    print("  STEP 10: Regulatory Crosswalk (Objective 1)")
    print("=" * 60)

    save_csv()
    save_markdown()
    save_glossary()

    print(f"\n  Crosswalk: {len(CROSSWALK)} rows mapping Annex III obligations → rights")
    print(f"  Glossary:  {len(GLOSSARY)} normalised terms")
    print("\n[OK] Regulatory crosswalk complete.")


if __name__ == "__main__":
    main()
