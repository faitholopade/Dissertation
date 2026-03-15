# Dissertation
## Overview

This repository contains a prototype data extraction, classification,
and annotation pipeline for my MSc Dissertation:

**Mapping LLM-related risks to fundamental-rights protections in Annex
III high-risk public-sector applications under the EU AI Act.**

The purpose of this pipeline is to:

1.  Collect representative samples from three key data sources\
2.  Define a reusable semantic schema (Annex domains, system patterns,
    rights, harms)\
3.  Automatically generate first‑pass annotations\
4.  Produce a unified `master_annotation_table.csv` to support further
    manual refinement and later LLM-assisted classification

------------------------------------------------------------------------

##  Repository Structure

    DISSERTATION/
    │
    ├── Federal AI Use Case Inventory/
    │   ├── 2024_consolidated_ai_inventory_raw_v2.csv
    │   ├── us_fed_ai.py
    │   ├── us_federal_subset_first10.csv
    │   ├── Description.md
    │
    ├── AIAAIC (AI, algorithmic and automation incidents and controversies)/
    │   ├── AIAAIC Repository - Incidents.csv
    │   ├── aiaaic_incidents.py
    │   ├── aiaaic_subset_broad_first10.csv
    │   ├── aiaaic_subset_llm_first10.csv
    │   ├── Description.md
    │
    ├── European Court of Human Rights/
    │   ├── final_for_viz.csv
    │   ├── echr.py
    │   ├── case_law_subset.csv
    │   ├── Description.md
    │
    ├── schema.py
    ├── annotate_records.py
    ├── master_annotation_table.csv
    └── README.md

Each subdirectory includes the **raw dataset**, a **filtering script**,
and a **10‑row representative subset**.

------------------------------------------------------------------------

## Data Sources

### 1. US Federal AI Use Case Inventory

-   Raw dataset: 2,133 federal AI use cases\
-   Filtered to match **employment** and **essential public services**
    aligned with Annex III(4)/(5)(a)\
-   Output: `us_federal_subset_first10.csv`

### 2. AIAAIC Incident Repository

-   2,121 real‑world AI/algorithmic incidents\
-   Two slices extracted:
    -   **Broad**: public-sector employment & benefit harms\
    -   **LLM‑specific**: incidents explicitly involving LLMs\
-   Outputs:
    -   `aiaaic_subset_broad_first10.csv`
    -   `aiaaic_subset_llm_first10.csv`

### 3. ECtHR Case Law (HUDOC-derived)

-   54k‑row dataset of ECtHR case-law metadata\
-   Filtered for:
    -   **Article 14 (non‑discrimination)**\
    -   **Protocol 1 (welfare/social‑benefit relevance)**\
    -   **Violation findings**\
-   Output: `case_law_subset.csv`

This slice provides the **rights backbone** for linking AI harms to
fundamental-rights obligations.

------------------------------------------------------------------------

## Schema (Ontology v0.1)

Implemented in `schema.py`:

-   **AnnexDomain** --- Employment, Essential Services\
-   **ActorRole** --- Provider, Deployer\
-   **SystemPattern** --- LLM screening, chatbot, decision‑support,
    summarisation\
-   **RightCategory** --- privacy/data protection, non-discrimination,
    access to social protection\
-   **HarmCategory** --- unfair exclusion, privacy breach,
    misinformation/error, procedural unfairness\
-   **RiskRecord dataclass** --- unified machine‑readable record
    structure

This schema will evolve into a richer semantic representation later.

------------------------------------------------------------------------

## Annotation Pipeline

Implemented in `annotate_records.py`.

The script:

1.  Loads the filtered subsets (US_FED, AIAAIC, ECtHR)\
2.  Applies lightweight rule‑based annotation\
3.  Assigns:
    -   Annex domain\
    -   Actor role\
    -   LLM usage pattern\
    -   Fundamental‑rights categories\
    -   Harm categories\
4.  Wraps each item in a `RiskRecord` dataclass\
5.  Produces a combined file: **`master_annotation_table.csv`**

------------------------------------------------------------------------

## Output

### `master_annotation_table.csv`

A unified table containing:

-   Source dataset\
-   Title and description\
-   Annex domain\
-   Actor role\
-   System pattern\
-   Rights implicated\
-   Harms identified\
-   Notes for manual refinement

This will support FRIA‑style case analysis, schema refinement, and
future LLM‑assisted classification.

------------------------------------------------------------------------

## Running the Pipeline

### Install dependencies

``` bash
pip install pandas
```

### Generate dataset slices

``` bash
python us_fed_ai.py
python aiaaic_incidents.py
python echr.py
```

### Build unified annotation table

``` bash
python annotate_records.py
```

------------------------------------------------------------------------

## Next Steps (Roadmap)

-   Refine schema and align with Annex III definitions\
-   Add LLM-assisted classification for improved accuracy\
-   Manual annotation of \~20--40 representative samples\
-   Build semantic mapping / ontology export (e.g., RDF/DPV)\
-   Evaluate framework using FRIA-style case studies

------------------------------------------------------------------------

## Author

**Faith Olopade**\
MSc Computer Science\
Trinity College Dublin\
olopadef@tcd.ie
