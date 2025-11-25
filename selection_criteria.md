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

## 2. AIAAIC Incident Repository

**File:** `AIAAIC Repository - Incidents.csv`  
**Script:** `aiaaic_incidents.py`

### 2.1 Columns searched

The following text columns are searched for keywords:

- `Headline`
- `Sector(s)`
- `Deployer(s)`
- `Purpose(s)`
- `Issue(s)`
- `External harms`
- `Internal impacts`
- `Summary/links`

### 2.2 Keyword groups

All matching is case-insensitive, using simple substring matching.

#### Employment / workers management

- recruit, recruitment, hiring, hire  
- job, applicant, cv, résumé, resume  
- hr, workforce, employee, personnel  
- performance review, gig worker  
- labour, labor (spelling variants)

#### Benefits / essential public services

- benefit, benefits, welfare  
- eligibility  
- public assistance, social security, social services  
- unemployment, disability, pension  
- healthcare, health care  
- debt recovery  

#### Public-sector / government context

- government, public sector  
- ministry, council, municipal  
- authority, agency, department  
- police, court  
- social services  

#### LLM / generative (narrow)

- llm, large language model  
- chatgpt, gpt-3, gpt-4, gpt4  
- bard, gemini, anthropic, claude  
- foundation model, generative ai, genai  
- chatbot  

### 2.3 Selection logic

1. Incident text contains **employment OR benefits** terms  
2. AND contains **public-sector** terms  
3. Narrow slice additionally requires **LLM/generative** terms  
4. Output:
   - `aiaaic_subset_broad_first10.csv`
   - `aiaaic_subset_llm_first10.csv`

### 2.4 Geography

- No geography filter currently applied  
- Later refinement may:
  - prioritise OECD/EU contexts  
  - downweight very different legal systems  
  - document any exclusions  

### 2.5 Negative filters

None yet; may add exclusions after manual review.

---

## 3. US Federal AI Use Case Inventory

**File:** `2024_consolidated_ai_inventory_raw_v2.csv`  
**Script:** `us_fed_ai.py`

### 3.1 Search columns

- `Use Case Name`  
- `"What is the intended purpose and expected benefits of the AI?"`  
- `"Describe the AI system’s outputs."`

### 3.2 Keyword groups

Employment:

- recruitment, recruiting, hiring, hire  
- hr, human resources  
- personnel, workforce, employee, staffing  

Benefits:

- benefits, welfare, eligibility  
- medicaid, medicare  
- social security, pension  
- unemployment, public assistance  
- healthcare, health care  

### 3.3 Selection logic

1. Keyword match on:
   - name  
   - purpose text  
   - output text  

2. Restrict to Annex III–aligned topic areas:
   - Education & Workforce  
   - Government Services (includes Benefits and Service Delivery)  
   - Mission-Enabling (internal agency support)  

3. Export first 10 rows as:
   - `us_federal_subset_first10.csv`

### 3.4 Geography

- US dataset used for *structural analogy* to Annex III, not for legal equivalence.

### 3.5 Negative filters

None implemented yet.

---

## 4. ECtHR Case-Law (rights backbone)

**File:** `final_for_viz.csv`  
**Script:** `echr.py`

### 4.1 Columns used

- `Document_Title`
- `Application_Number`
- `Article`
- `Conclusion`
- `Country`
- `year`

### 4.2 Target rights

The backbone focuses on:

- **Article 14** (non-discrimination)  
- **Protocol 1** (social-benefit / welfare relevance)

### 4.3 Selection logic

1. Retain rows where `Article` == "14" OR "P1"  
2. Require `Conclusion` containing `"violation"`  
3. Deduplicate by:
   - `Document_Title`
   - `Application_Number`
4. Export first 20 rows to:
   - `case_law_subset.csv`

### 4.4 Geography

- ECtHR covers Council of Europe, broader than EU  
- Rights framework sufficiently aligned for Annex III mapping  

### 4.5 Negative filters

- Excludes non-violation cases  
- Subject-matter refinement planned for manual annotation stage  

---

## 5. Reproducibility

To regenerate my subsets:

```bash
python aiaaic_incidents.py
python us_fed_ai.py
python echr.py
```

Then generate unified annotated table:

```bash
python annotate_records.py
```

Outputs:

- `aiaaic_subset_broad_first10.csv`  
- `aiaaic_subset_llm_first10.csv`  
- `us_federal_subset_first10.csv`  
- `case_law_subset.csv`  
- `master_annotation_table.csv`  

---

## 6. Planned refinements

- Add explicit synonym lists  
- Add negative filters  
- Introduce geography constraints  
- Compare keyword-based vs LLM-assisted selection  
- Build small gold-standard manual annotations  
