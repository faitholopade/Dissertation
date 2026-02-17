# Selection Criteria for Initial Corpora

This document describes how I currently select records from each source dataset for my Annex III slice. It is intended to be **explicit and reproducible**, so that another annotator could replicate or adapt the process.

The selection logic is implemented in:

- `Federal AI Use Case Inventory/us_fed_ai.py`
- `AIAAIC (AI, algorithmic and automation incidents and controversies)/aiaaic_incidents.py`
- `European Court of Human Rights/echr.py`

and the downstream schema / annotation code is in:

- `schema.py`
- `annotate_records.py`

---

## 1. Overall scope

### Annex III application areas

I focus on two high-risk areas of Annex III of the EU AI Act:

1. **Annex III(4) – Employment, workers management and access to self-employment**

   - AI used for **recruitment / selection**, including targeted job ads, CV filtering, candidate evaluation.
   - AI used for **workplace decisions**, including promotion, termination, task allocation, monitoring and performance evaluation.

2. **Annex III(5)(a) – Access to essential public services and benefits**

   - AI used by (or on behalf of) **public authorities** to evaluate **eligibility** for essential public assistance and services (including healthcare), and to **grant, reduce, revoke, or reclaim** such benefits/services.

### Rights focus

Across all sources, the selection is intended to capture cases plausibly relevant to:

- **Non-discrimination / equal treatment**
- **Privacy / data protection**, especially in relation to eligibility, profiling, and automated decision-making
- Related rights (e.g. access to social protection) are considered later at the annotation stage via `RightCategory` in `schema.py`.

---

## 2. AIAAIC Incident Repository (Updated after Manual Annotation)

**File:** `AIAAIC Repository - Incidents.csv`  
**Script:** `aiaaic_incidents.py`

This section reflects **revisions introduced after an initial round of manual annotation**, which revealed that earlier keyword sets under-captured relevant Annex III incidents.

### 2.1 Columns searched

Keyword matching is performed over a concatenation of the following columns:

- `Headline`
- `Sector(s)`
- `Deployer(s)`
- `Purpose(s)`
- `Issue(s)`
- `External harms`
- `Internal impacts`
- `Summary/links`
- Detailed harms fields (`Unnamed: 14`, `Unnamed: 15`, `Unnamed: 17–19`)

This ensures that both high-level labels and narrative descriptions are considered.

---

### 2.2 Keyword groups (refined)

All matching is case-insensitive and based on substring matching.

#### Employment / workers management (Annex III(4))

Expanded after manual annotation to capture both recruitment and in-work management contexts:

- employ, employment, employer, employee, employees  
- worker, workers, workforce, staff, staffing  
- recruit, recruitment, recruiting, hiring, hire, hired  
- applicant, candidates, cv, résumé, resume  
- layoff, redundancy, fired, termination  
- promotion, performance review  
- gig worker  
- labour, labor (spelling variants)

These additions reflect the fact that many relevant incidents were labelled generically as “Employment” or “Workers” rather than explicitly “recruitment”.

---

#### Essential public services / benefits (Annex III(5)(a))

Expanded to better capture eligibility, recovery, and public funding cases:

- benefit, benefits, welfare, social security  
- social assistance, public assistance  
- unemployment, disability, pension, pensions  
- child benefit, child welfare  
- healthcare, health care, medicaid, medicare  
- veterans affairs, veteran, veterans  
- welfare fraud, overpayment, advance payment  
- public funds, public funding, funding, grant, grants  
- eligibility, eligibility screening  
- means test, means-testing, means-tested  

Manual annotation showed that eligibility-related incidents often use administrative or financial language rather than explicit “welfare” terms.

---

#### Public-sector / government context (refined)

Expanded after manual annotation to capture common public-sector identifiers not present in earlier keyword lists:

- government, govt, gov.  
- public sector, public service, public services  
- ministry, ministries  
- council, municipal, municipality, city council  
- authority, authorities  
- agency, agencies  
- department, dept  
- police, court, courts, justice  
- local authority, local authorities  
- social services  
- **dwp** (UK Department for Work and Pensions)  
- **nhs** (UK National Health Service)  
- veterans affairs  

Public-sector detection now combines:
- direct checks in `Sector(s)` and `Deployer(s)` (e.g. “Govt - …”), and  
- fallback keyword matching across all text fields.

---

#### LLM / generative AI (narrow slice)

Unchanged, intentionally strict:

- llm, large language model  
- chatgpt, gpt-3, gpt-4, gpt4  
- bard, gemini, claude, anthropic, grok  
- foundation model, generative ai, genai  
- chatbot  

Manual review confirmed that **explicit LLM mentions remain rare** in Annex III employment/benefits incidents.

---

### 2.3 Selection logic (current)

1. Incident text matches **employment OR essential services/benefits** keywords  
2. AND incident is classified as **public-sector / authority-related**  
3. **Broad slice** = (1 AND 2)  
4. **LLM narrow slice** = Broad slice AND explicit LLM/generative terms  
5. Outputs:
   - `aiaaic_subset_broad_first10.csv`
   - `aiaaic_subset_llm_first10.csv`
   - `aiaaic_manual_extra.csv` (15 additional broad incidents for manual annotation)

With these refinements, the broad slice currently yields ~120 incidents (≈6% of the full AIAAIC dataset), which is consistent with expectations for Annex III public-sector employment/benefits cases.

---

### 2.4 Geography

- No explicit geography filter is currently applied; incidents are global.
- During manual annotation, priority is given to:
  - EU, UK, US, and other OECD jurisdictions.
- Incidents from jurisdictions with very different legal frameworks are flagged during annotation and discussed as limitations rather than automatically excluded.

---

### 2.5 Negative filters (planned)

No hard negative filters are yet implemented in code.  
Manual annotation has identified candidates for future exclusions, such as:

- generic “employment” mentions unrelated to individual decision-making,
- healthcare logistics or analytics with no eligibility/access implications,
- funding references unrelated to public-benefit eligibility.

These will inform a later iteration of exclusion rules or secondary filters.

---

## 6. Planned refinements (updated)

- Iterative expansion/refinement of keyword lists based on manual annotation
- Introduction of negative filters for recurrent false positives
- Optional geography-aware filtering or weighting
- Comparison of:
  - keyword-based selection  
  - LLM-assisted selection  
  against the manually annotated gold-standard subset
- Formal evaluation of agreement between manual and automated labels
