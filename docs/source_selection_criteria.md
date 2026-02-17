# Source Selection Criteria and Background

This document summarises the **curation practices, taxonomies, and reporting structures** of the external sources used in this dissertation. The goal is **not** to exhaustively ingest or reproduce these sources, but to understand how incidents and risks are selected, structured, and categorised, and to identify elements that can be reused or adapted when mapping incidents to **EU AI Act Annex III** application areas and **fundamental-rights risks**.

---

## 1. AIAAIC – AI, Algorithmic, and Automation Incidents and Controversies

### What it is
The AIAAIC repository is an **open, publicly accessible collection of AI-, algorithmic-, and automation-related incidents**, primarily curated from **news reporting** and other public sources. Each entry represents a real-world incident where automated or AI-driven systems have caused, contributed to, or been associated with harm.

### How incidents are curated
- Incidents are **selected and summarised by volunteers** associated with the AIAAIC project.
- Each incident is linked to **one or more external news articles** or public reports.
- Incidents are described using:
  - short textual summaries,
  - issue descriptions,
  - harm categories,
  - and contextual metadata (sector, deployer, technology, etc.).
- The repository evolves over time, with changes in tagging and categorisation practices as the project matures.

### Strengths
- **Open access** and transparent: the full dataset is publicly available.
- **Broad coverage** across sectors, geographies, and types of AI systems.
- Direct linkage to **journalistic sources**, which provides traceability and context.
- Widely referenced in the academic literature on AI incidents and harms.

### Limitations
- The taxonomy is **not designed specifically for EU AI Act Annex III** categories or for formal fundamental-rights analysis.
- As a **volunteer-curated resource**, categorisation practices may vary over time and across contributors.
- Harm labels and issue descriptions are often high-level and not aligned to legal concepts such as *non-discrimination* or *data protection* as defined in EU law.

### How this dissertation uses AIAAIC
AIAAIC is used as a **primary incident corpus** from which a filtered subset is extracted. The incidents are then:
- mapped to **Annex III(4) Employment** and **Annex III(5)(a) Essential public services/benefits** where plausible,
- re-annotated using a custom schema aligned with **fundamental rights**,
- and compared across **keyword-based**, **manual**, and **LLM-assisted** selection approaches.

---

## 2. OECD AI Incidents Monitor (AIM)

### What it is
The OECD AI Incidents Monitor (AIM) is an initiative developed by the **OECD.AI expert group** to systematically identify and document AI-related incidents and hazards.

### How incidents are identified
- AIM detects potential AI incidents and hazards by monitoring **reputable news outlets** through the **Event Registry** platform.
- Event Registry processes **over 150,000 news articles per day**, from which relevant AI-related events are identified.
- The OECD explicitly frames AIM as an **evidence base**, acknowledging that it represents a **subset** of all AI-related harms rather than a complete census.

### Reporting structure and taxonomy
- AIM is aligned with a **common reporting framework** for AI incidents.
- This framework includes **29 criteria**, some mandatory, covering aspects such as:
  - system context,
  - type of harm,
  - affected stakeholders,
  - and severity.
- The OECD distinguishes between:
  - **AI incidents** (realised harms),
  - and **AI hazards** (potential risks).
- The documentation notes **court rulings** as a future or complementary source of evidence.

### Strengths
- Strong **methodological transparency** and institutional credibility.
- Explicit definitions of “AI incident” and “AI hazard”.
- Structured reporting framework that can inform downstream schema design.

### Limitations
- AIM is **not fully open access** in the same way as AIAAIC.
- The framework is not tailored to **EU AI Act Annex III application areas** or to detailed fundamental-rights mapping.

### Relevance to this dissertation
OECD AIM informs:
- the **structure** of incident descriptions,
- the distinction between realised harms and potential risks,
- and the idea of a **standardised reporting template**, which influences the design of the dissertation’s semantic schema.

---

## 3. AI Incident Database (AIID) – Partnership on AI

### What it is
The AI Incident Database (AIID), hosted by the **Partnership on AI**, is a **centralised, crowdsourced repository** documenting incidents where AI systems have caused real-world problems.

### How incidents are curated
- Incidents are **submitted by contributors** and reviewed by the AIID team.
- Each incident is documented with:
  - narrative descriptions,
  - metadata fields,
  - and a **taxonomy of failure causes and impacts**.
- The project explicitly aims to help **anticipate and prevent future harms** by learning from past incidents.

### Scale and scope
- The AIID reports **more than 1,200 incident reports** (figure subject to growth).
- Coverage spans multiple sectors and types of AI systems.

### Strengths
- Clear focus on **incident analysis** and **failure causes**.
- Well-developed **taxonomic structure** for describing AI failures.
- Strong emphasis on learning and prevention.

### Limitations
- Like AIAAIC, AIID is **not designed specifically for Annex III or fundamental-rights compliance**.
- Crowdsourced submissions may vary in depth and consistency.

### Relevance to this dissertation
AIID provides:
- examples of **incident taxonomies**,
- approaches to **failure cause analysis**,
- and inspiration for structuring incident-level annotations, even though the dataset itself is not directly used.

---

## 4. MIT AI Risk Repository

### What it is
The MIT AI Risk Repository is a **taxonomy-focused resource**, rather than an incident database. It aggregates and structures AI risks identified across the literature.

### Structure and taxonomy
- The repository contains **over 1,600 AI risks**, organised by:
  - **risk domain**,
  - and **cause**.
- It is built from a **systematic review** of existing AI risk frameworks and publications.

### Strengths
- Provides a **comprehensive, structured risk taxonomy**.
- Useful for harmonising and comparing different risk frameworks.
- Widely cited as a reference point for AI risk categorisation.

### Limitations
- Does **not document concrete incidents**.
- Does not directly address **legal compliance**, Annex III categories, or fundamental-rights assessments.

### Relevance to this dissertation
The MIT AI Risk Repository is used as:
- a reference for **risk and harm categories**,
- a comparative taxonomy to align with incident-level harms,
- and a conceptual bridge between high-level risk frameworks and concrete incidents.

---

## 5. Summary

Across these sources:

- **AIAAIC** and **AIID** provide rich, open, incident-level data but lack legal alignment.
- **OECD AIM** provides methodological rigor and structured reporting concepts.
- **MIT AI Risk Repository** offers a broad, systematic taxonomy of AI risks.

This dissertation draws selectively from each:
- using AIAAIC as the main incident corpus,
- borrowing structural ideas from OECD AIM,
- referencing AIID for incident taxonomy practices,
- and aligning harms with MIT-style risk categories,
to support a **reusable semantic framework** for mapping AI incidents to **EU AI Act Annex III** application areas and **fundamental-rights protections**.
