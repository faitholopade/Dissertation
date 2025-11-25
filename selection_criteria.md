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

