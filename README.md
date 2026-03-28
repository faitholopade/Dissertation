# A Reusable Semantic Framework Linking LLM Risks to Fundamental Rights Under the EU AI Act

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

**MSc Computer Science Dissertation — Trinity College Dublin, 2026**

| | |
|---|---|
| **Author** | Faith Olopade ([olopadef@tcd.ie](mailto:olopadef@tcd.ie)) |
| **Supervisor** | Dr David Lewis |
| **Co-supervisor** | Dr Delaram Golpayegani |
| **Affiliation** | School of Computer Science and Statistics, Trinity College Dublin |
| **Programme** | MSc Computer Science |
| **Date** | 2026 |

---

## Abstract

The EU Artificial Intelligence Act (Regulation 2024/1689) imposes strict obligations on providers and deployers of high-risk AI systems listed in Annex III. However, a systematic, machine-readable mapping between large language model (LLM) risk evidence and fundamental-rights protections remains absent from the compliance toolchain. This project addresses that gap by designing and populating a **reusable semantic framework** that connects application context, LLM usage patterns, risk and harm categories, and fundamental rights for high-risk public-sector applications under Annex III categories 4 (employment) and 5a (essential public services).

The framework is operationalised through a **reproducible 13-step annotation pipeline** that ingests 150 records from three public sources, annotates them via keyword rules, LLM-assisted classification, and hybrid merge, evaluates label quality against a manually annotated gold standard, and exports the results as a linked knowledge graph. A suite of Fundamental Rights Impact Assessment (FRIA) retrieval scenarios and a regulatory crosswalk demonstrate the practical utility of the framework for conformity assessment under the AI Act.

---

## Research Question

> How can a reusable semantic framework be designed and populated to link LLM-related risk evidence with fundamental-rights protections for high-risk public-sector applications (Annex III/4 and Annex III/5a) under the EU AI Act?

---

## Data Sources

| Source | Records | Description | URL |
|--------|---------|-------------|-----|
| AIAAIC Repository | ~100 | Real-world AI, algorithmic, and automation incidents | https://www.aiaaic.org |
| US Federal AI Use Case Inventory | 30 | Government AI use cases filtered to employment and essential public services | https://github.com/ombegov/2024-Federal-AI-Use-Case-Inventory |
| ECtHR Case Law (HUDOC) | 20 | European Court of Human Rights judgments on non-discrimination and social protection | https://hudoc.echr.coe.int |

---

## Semantic Vocabularies

| Vocabulary | Purpose | URI |
|------------|---------|-----|
| DPV | Data Privacy Vocabulary — core data-protection concepts | https://w3id.org/dpv/ |
| DPV-Risk | Risk and harm categories | https://w3id.org/dpv/risk/ |
| VAIR | Vocabulary of AI Risks | https://w3id.org/vair/ |
| EU-Rights | EU Charter of Fundamental Rights concepts | https://w3id.org/dpv/legal/eu/rights/ |

---

## Pipeline Architecture

The pipeline is organised as 13 sequential steps, each implemented as a standalone Python script in `src/`.

```
Step  Script                          Output
----  ------------------------------  ------------------------------------------
 01   01_expand_corpus.py             master_annotation_table_final.csv
 02   02_llm_annotate.py              master_annotation_table_llm_v2.csv
 03   03_compare_methods.py           method_comparison_results_v2.csv
 04   04_evaluate_gold.py             gold_evaluation_results.csv
 05   05_schema_definition.py         schema/*.ttl, *.jsonld
 06   06_export_semantic.py           risk_records_v2.jsonld
 07   07_generate_figures.py          figures/*.png
 07b  07b_alternative_figures.py      figures/*.png (alternative styles)
 08   08_fria_demo_scenarios.py       fria_scenario_results.csv
 09   09_error_analysis.py            error_analysis_*.csv, *.txt
 10   10_regulatory_crosswalk.py      regulatory_crosswalk.csv, .md
 11   11_chain_of_events.py           master_annotation_table_causal.csv
 12   12_knowledge_graph.py           knowledge_graph.ttl
 13   13_visualise_knowledge_graph.py  fig_knowledge_graph_full.html, .png
```

```
data/aiaaic/ ──┐
data/usfed/  ──┤──> 01_expand_corpus ──> 02_llm_annotate ──> 03_compare_methods
data/ecthr/  ──┘         |                                          |
                         v                                          v
                   04_evaluate_gold                          05_schema_definition
                         |                                          |
                         v                                          v
                   07_generate_figures                       06_export_semantic
                         |                                          |
                         v                                          v
                   08_fria_demo_scenarios                    09_error_analysis
                         |                                          |
                         v                                          v
                   10_regulatory_crosswalk               11_chain_of_events
                                                                    |
                                                                    v
                                                         12_knowledge_graph
                                                                    |
                                                                    v
                                                      13_visualise_knowledge_graph
```

---

## Repository Structure

```
.
├── README.md
├── LICENSE                           # CC BY 4.0
├── requirements.txt
├── run_all.py                        # Orchestrate steps 01-10
│
├── data/
│   ├── aiaaic/                       # AIAAIC incident data and processing
│   ├── ecthr/                        # ECtHR case law data and processing
│   ├── usfed/                        # US Federal AI inventory and processing
│   ├── master_annotation_table_v01.csv
│   └── master_annotation_table_v05.csv
│
├── src/                              # Pipeline scripts (steps 01-13)
│   ├── 01_expand_corpus.py
│   ├── ...
│   └── 13_visualise_knowledge_graph.py
│
├── schema/                           # Semantic schema definitions
│   ├── fria_risk_schema.ttl          # Turtle format
│   ├── fria_risk_schema.jsonld       # JSON-LD format
│   ├── example_risk_record.jsonld
│   ├── crosswalk_glossary.json
│   └── schema_documentation.md
│
├── output/                           # Pipeline outputs
│   ├── master_annotation_table_final.csv
│   ├── master_annotation_table_causal.csv
│   ├── knowledge_graph.ttl
│   ├── risk_records_v2.jsonld
│   ├── regulatory_crosswalk.csv
│   └── ...
│
├── figures/                          # Generated visualisations
│   ├── fig_knowledge_graph_full.html # Interactive knowledge graph
│   └── *.png
│
├── docs/                             # Supplementary documentation
│   ├── selection_criteria.md
│   └── source_selection_criteria.md
│
└── archive/                          # Superseded v1 scripts and outputs
```

---

## Key Outputs

| Output | Description |
|--------|-------------|
| `master_annotation_table_final.csv` | 150 records with keyword, LLM, and hybrid labels across domain, pattern, rights, and harms |
| `master_annotation_table_causal.csv` | Extended with root cause, mitigation status, and source type |
| `knowledge_graph.ttl` | RDF/Turtle knowledge graph (194 nodes, 963 edges, 1,351 triples) |
| `fig_knowledge_graph_full.html` | Interactive, zoomable knowledge graph visualisation |
| `fria_scenario_results.csv` | FRIA-style retrieval narratives for welfare and recruitment scenarios |
| `schema/fria_risk_schema.ttl` | Reusable semantic schema in Turtle |
| `schema/fria_risk_schema.jsonld` | Reusable semantic schema in JSON-LD |
| `regulatory_crosswalk.csv` | Mapping between fundamental rights and AI Act obligations |

---

## Evaluation Summary

| Metric | Keyword | LLM | Hybrid |
|--------|---------|-----|--------|
| Domain accuracy | ~60% | ~72% | ~78% |
| Unknown rate | high | low | low |
| Cohen's kappa (domain) | -- | ~0.55 | ~0.65 |

Detailed evaluation results are generated by `04_evaluate_gold.py` and `03_compare_methods.py`. Confusion matrices and inter-annotator agreement figures are available in `figures/` and `output/`.

---

## Reproducibility

| Aspect | Detail |
|--------|--------|
| **LLM** | Claude claude-sonnet-4-20250514 via Anthropic API |
| **Temperature** | 0 (deterministic) |
| **Prompt logs** | `output/llm_predictions_cache_v2.jsonl`, `output/causal_annotation_log.jsonl` |
| **Cache layer** | Prevents duplicate API calls across re-runs |
| **Gold standard** | Manually annotated via Label Studio (`data/aiaaic/label_studio_export.json`) |
| **Python** | 3.12+ |
| **Dependencies** | Pinned in `requirements.txt` |

---

## Setup and Execution

### 1. Create a virtual environment

```bash
cd Dissertation
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set environment variable

```bash
# Windows PowerShell
$env:ANTHROPIC_API_KEY = "sk-ant-..."

# macOS / Linux
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 4. Run the pipeline

```bash
# Steps 01-10
python run_all.py

# Steps 11-12 (causal extraction and knowledge graph)
python src/11_chain_of_events.py
python src/12_knowledge_graph.py

# Step 13 (knowledge graph visualisation)
python src/13_visualise_knowledge_graph.py
```

### 5. View the interactive knowledge graph

```bash
# Windows
start figures/fig_knowledge_graph_full.html

# macOS
open figures/fig_knowledge_graph_full.html
```

---

## License

This work is licensed under a [Creative Commons Attribution 4.0 International License](http://creativecommons.org/licenses/by/4.0/).

You are free to share and adapt this material for any purpose, provided appropriate attribution is given. See [LICENSE](LICENSE) for full terms.

---

## Acknowledgements

- **Dr David Lewis** and **Dr Delaram Golpayegani** (ADAPT Centre, Trinity College Dublin) for supervision and guidance
- **AIAAIC** for maintaining the public AI incident repository
- **W3C Data Privacy Vocabularies and Controls Community Group** for the Data Privacy Vocabulary (DPV)
- **ADAPT Centre** for the VAIR ontology and FRIA framework
- **Claude** (Anthropic) was used as an assistive tool for repository organisation and cleanup tasks
