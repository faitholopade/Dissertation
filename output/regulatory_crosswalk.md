# Regulatory Crosswalk: AI Act Annex III/4 & III/5a → Fundamental Rights

## Crosswalk Table

### Annex III/4(a) — Employment

**Obligation scope:** AI for recruitment or selection of natural persons — targeted job ads, CV filtering, candidate evaluation

| Dimension | Detail |
|-----------|--------|
| **Non-discrimination provisions** | EU Charter Art. 21 (Non-discrimination); Employment Equality Directive 2000/78/EC; Racial Equality Directive 2000/43/EC |
| **Non-discrimination risk indicators** | Demographic bias in training data; proxy discrimination via postal code, name, or language; disparate impact on protected groups (gender, age, ethnicity, disability) |
| **Privacy / data-protection provisions** | EU Charter Art. 8 (Data protection); GDPR Art. 22 (Automated individual decision-making); GDPR Art. 9 (Special categories) |
| **Privacy risk indicators** | Processing of special-category data (health, ethnicity) inferred from CV; profiling without valid legal basis; lack of transparency about automated scoring |
| **FRIA guiding question** | Does the system produce or influence decisions on hiring, shortlisting, or candidate ranking? Could outputs correlate with protected characteristics? |
| **Schema mapping** | `annex_domain=employment; system_pattern∈{profiling_scoring, llm_assisted_screening}; rights∈{NON-DISCRIMINATION, PRIVACY}` |
| **Mitigation examples** | Bias audit on training data; disparate-impact testing; human review of shortlists; DPIA; Art. 22 safeguards (right to explanation, human intervention) |

### Annex III/4(b) — Employment

**Obligation scope:** AI for decisions on work-related contractual relationships — promotion, termination, task allocation based on behaviour or personal traits

| Dimension | Detail |
|-----------|--------|
| **Non-discrimination provisions** | EU Charter Art. 21; Art. 31 (Fair working conditions); Employment Equality Directive 2000/78/EC |
| **Non-discrimination risk indicators** | Performance scoring correlated with protected attributes; task allocation reflecting historical bias; automated termination recommendations without context |
| **Privacy / data-protection provisions** | EU Charter Art. 8; GDPR Art. 5(1)(b) (Purpose limitation); GDPR Art. 6 (Lawfulness of processing) |
| **Privacy risk indicators** | Continuous behavioural monitoring exceeding stated purpose; keystroke / productivity tracking; sentiment analysis of communications |
| **FRIA guiding question** | Does the system monitor, evaluate, or score workers in ways that affect employment terms? Is monitoring proportionate to a legitimate aim? |
| **Schema mapping** | `annex_domain=employment; system_pattern∈{surveillance_monitor, profiling_scoring}; rights∈{NON-DISCRIMINATION, PRIVACY, FAIR-WORKING-CONDITIONS}` |
| **Mitigation examples** | Proportionality review of monitoring scope; worker consultation (GDPR Art. 88); algorithmic impact assessment; opt-out for non-essential tracking |

### Annex III/4(c) — Employment

**Obligation scope:** AI for monitoring and evaluating performance and behaviour of persons in work-related relationships

| Dimension | Detail |
|-----------|--------|
| **Non-discrimination provisions** | EU Charter Art. 21; Art. 31 (Fair working conditions) |
| **Non-discrimination risk indicators** | Biased performance benchmarks; emotion-recognition in evaluations; disparate discipline rates |
| **Privacy / data-protection provisions** | EU Charter Art. 7 (Private life); Art. 8; GDPR Art. 35 (DPIA); ePrivacy Directive (electronic communications monitoring) |
| **Privacy risk indicators** | Workplace surveillance scope creep; processing of biometric data; lack of data minimisation; no clear retention policy |
| **FRIA guiding question** | Is worker monitoring continuous or event-based? Are workers informed about data collected and how evaluations are derived? |
| **Schema mapping** | `annex_domain=employment; system_pattern=surveillance_monitor; rights∈{PRIVACY, NON-DISCRIMINATION}` |
| **Mitigation examples** | Data minimisation by design; time-limited retention; worker notification and DPIA; union/works-council consultation |

### Annex III/5(a)-i — Essential Services

**Obligation scope:** AI by public authorities to evaluate eligibility for essential public assistance benefits and services, including healthcare services

| Dimension | Detail |
|-----------|--------|
| **Non-discrimination provisions** | EU Charter Art. 21 (Non-discrimination); Art. 34 (Social security / social assistance); Art. 35 (Healthcare); Racial Equality Directive 2000/43/EC Art. 3(1)(e) |
| **Non-discrimination risk indicators** | Proxy discrimination in eligibility scoring (e.g., postal code → ethnicity); under-representation of minority applicants in training data; algorithmic exclusion of vulnerable groups |
| **Privacy / data-protection provisions** | EU Charter Art. 8; GDPR Art. 9 (Health data, social-benefit data as special category); GDPR Art. 22 |
| **Privacy risk indicators** | Processing sensitive welfare/health data; automated profiling for fraud detection without human review; data linkage across agencies beyond original purpose |
| **FRIA guiding question** | Does the system determine, score, or rank individuals for eligibility for public benefits or healthcare access? Could errors lead to wrongful denial of essential services? |
| **Schema mapping** | `annex_domain=essential_services; system_pattern∈{profiling_scoring, resource_allocation, classification_triage}; rights∈{NON-DISCRIMINATION, PRIVACY, SOCIAL-PROTECTION}` |
| **Mitigation examples** | Fairness testing across demographic groups; human-in-the-loop for denial decisions; appeal/remedy mechanism; DPIA with special-category data assessment; transparent eligibility criteria |

### Annex III/5(a)-ii — Essential Services

**Obligation scope:** AI to grant, reduce, revoke, or reclaim essential public assistance benefits and services

| Dimension | Detail |
|-----------|--------|
| **Non-discrimination provisions** | EU Charter Art. 21; Art. 34; Art. 47 (Effective remedy and fair trial) |
| **Non-discrimination risk indicators** | Automated revocation disproportionately affecting ethnic minorities; 'robodebt'-style mass debt recovery; opaque scoring penalising disadvantaged postcodes |
| **Privacy / data-protection provisions** | EU Charter Art. 8; GDPR Art. 5(1)(d) (Accuracy); GDPR Art. 16 (Right to rectification) |
| **Privacy risk indicators** | Inaccurate records leading to wrongful revocation; data quality issues in linked administrative databases; no mechanism for subjects to correct errors |
| **FRIA guiding question** | Can the system revoke or reduce benefits without individual human review? Is there an accessible appeals process for affected individuals? |
| **Schema mapping** | `annex_domain=essential_services; system_pattern∈{profiling_scoring, resource_allocation}; rights∈{NON-DISCRIMINATION, PRIVACY, EFFECTIVE-REMEDY}` |
| **Mitigation examples** | Mandatory human review before revocation; accessible appeals process; data accuracy audits; redress fund; regular bias monitoring |

### Annex III/5(a)-iii — Essential Services

**Obligation scope:** AI for creditworthiness evaluation or credit scoring of natural persons (excluding fraud detection)

| Dimension | Detail |
|-----------|--------|
| **Non-discrimination provisions** | EU Charter Art. 21; Consumer Credit Directive 2008/48/EC |
| **Non-discrimination risk indicators** | Credit models embedding historical lending discrimination; use of non-financial behavioural data correlating with ethnicity or gender |
| **Privacy / data-protection provisions** | EU Charter Art. 8; GDPR Art. 22; GDPR Art. 15 (Right of access) |
| **Privacy risk indicators** | Opaque scoring models; use of social-media or location data without consent; inability to understand or contest a credit decision |
| **FRIA guiding question** | Does the credit scoring model use features that could proxy for protected characteristics? Can individuals obtain a meaningful explanation? |
| **Schema mapping** | `annex_domain=essential_services; system_pattern=profiling_scoring; rights∈{NON-DISCRIMINATION, PRIVACY}` |
| **Mitigation examples** | Feature audit for proxy variables; explainability report per Art. 22(3); alternative data opt-out; regular disparate-impact testing |

### Annex III/5(a)-iv — Essential Services

**Obligation scope:** AI for risk assessment and pricing in life and health insurance

| Dimension | Detail |
|-----------|--------|
| **Non-discrimination provisions** | EU Charter Art. 21; Art. 35 (Healthcare); Gender Goods & Services Directive 2004/113/EC (prohibits gender-based pricing) |
| **Non-discrimination risk indicators** | Pricing models penalising genetic predisposition or chronic illness; gender- or ethnicity-correlated premium differences |
| **Privacy / data-protection provisions** | EU Charter Art. 8; GDPR Art. 9(2)(h) (Health data); Solvency II data requirements |
| **Privacy risk indicators** | Inference of health status from behavioural data; use of wearable/IoT health data without explicit consent; secondary use of claims data |
| **FRIA guiding question** | Could the pricing model create access barriers to insurance for vulnerable groups? Is health data processed with explicit consent and clear purpose limitation? |
| **Schema mapping** | `annex_domain=essential_services; system_pattern=profiling_scoring; rights∈{NON-DISCRIMINATION, PRIVACY, HEALTHCARE-ACCESS}` |
| **Mitigation examples** | Actuarial fairness audit; prohibition of genetic data use; DPIA for health-data processing; purpose limitation enforcement; consumer disclosure |

### Annex III/5(a)-v — Essential Services

**Obligation scope:** AI for evaluating and classifying emergency calls or dispatching emergency first-response services (police, firefighters, medical aid)

| Dimension | Detail |
|-----------|--------|
| **Non-discrimination provisions** | EU Charter Art. 2 (Right to life); Art. 21; Art. 35 (Healthcare) |
| **Non-discrimination risk indicators** | Deprioritisation of calls from certain neighbourhoods or languages; accent/dialect bias in speech recognition; lower triage priority for non-native speakers |
| **Privacy / data-protection provisions** | EU Charter Art. 8; ePrivacy Directive (location data); GDPR Art. 6(1)(d) (Vital interests) |
| **Privacy risk indicators** | Location tracking of callers; recording and profiling of emergency communications; retention of sensitive call content beyond operational need |
| **FRIA guiding question** | Could triage errors lead to delayed emergency response for specific demographic groups? Is caller data retained proportionately? |
| **Schema mapping** | `annex_domain=essential_services; system_pattern∈{classification_triage, resource_allocation}; rights∈{RIGHT-TO-LIFE, NON-DISCRIMINATION, PRIVACY}` |
| **Mitigation examples** | Multi-language / multi-accent testing; performance monitoring by caller demographics; minimal data retention; human escalation protocol |

## Normalised Glossary

| Term | Definition |
|------|------------|
| **Annex III/4** | AI Act high-risk category covering AI systems used in employment, workers management, and access to self-employment (Article 6(2) read with Annex III, point 4). |
| **Annex III/5a** | AI Act high-risk category covering AI systems used by public authorities or on their behalf to evaluate eligibility for essential public services and benefits, and to grant, reduce, revoke, or reclaim such services (Article 6(2) read with Annex III, point 5(a)). |
| **Automated decision-making** | A decision based solely on automated processing, including profiling, which produces legal effects or similarly significantly affects the data subject (GDPR Art. 22). |
| **DPIA** | Data Protection Impact Assessment — required under GDPR Article 35 when processing is likely to result in a high risk to the rights and freedoms of natural persons. |
| **Deployer** | Any natural or legal person, public authority, agency, or other body using an AI system under its authority (AI Act Art. 3(4)). |
| **Disparate impact** | When a facially neutral policy, practice, or algorithmic output disproportionately and negatively affects members of a protected group, even absent discriminatory intent. |
| **Essential public service** | A service provided by or on behalf of a public authority that individuals depend on for basic needs, including welfare, healthcare, social housing, and utilities access. |
| **FRIA** | Fundamental Rights Impact Assessment — mandatory under AI Act Article 27 for deployers of high-risk AI systems that are public bodies or provide essential public services. |
| **High-risk AI system** | An AI system referred to in Article 6(2) of the AI Act and listed in Annex III, subject to the requirements in Chapter III, Section 2. |
| **Human-in-the-loop** | A design pattern where a human operator reviews, validates, or can override AI system outputs before they take effect on individuals. |
| **Non-discrimination** | The right to equal treatment without distinction based on protected characteristics (sex, race, colour, ethnic or social origin, genetic features, language, religion, political opinion, disability, age, sexual orientation). EU Charter Article 21. |
| **Privacy / Data Protection** | The right to respect for private and family life (EU Charter Art. 7) and the right to the protection of personal data (EU Charter Art. 8; GDPR). |
| **Profiling** | Any form of automated processing of personal data to evaluate certain personal aspects, in particular to analyse or predict aspects concerning performance at work, economic situation, health, personal preferences, interests, reliability, behaviour, location, or movements (GDPR Art. 4(4)). |
| **Provider** | A natural or legal person, public authority, agency, or other body that develops an AI system or has an AI system developed with a view to placing it on the market or putting it into service (AI Act Art. 3(3)). |
| **Proxy discrimination** | Discrimination that occurs indirectly when a seemingly neutral variable (e.g., postal code, language) is statistically correlated with a protected characteristic (e.g., ethnicity). |
| **Special category data** | Personal data revealing racial or ethnic origin, political opinions, religious or philosophical beliefs, trade union membership, genetic data, biometric data, health data, or data concerning sex life or sexual orientation (GDPR Art. 9). |