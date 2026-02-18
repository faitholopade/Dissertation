# Reusable Semantic Framework Linking LLM Risks to Fundamental Rights

**MSc Computer Science Dissertation — Trinity College Dublin, 2026**

**Author:** Faith Olopade
**Supervisor:** Dr David Lewis
**Co-supervisor:** Dr Delaram Golpayegani

---

## Research Question

> How can a reusable semantic framework be designed and populated to link
> LLM-related risk evidence with fundamental-rights protections for high-risk
> public-sector applications (Annex III/4 and Annex III/5a) under the EU AI Act?

## Project Overview

This project builds a **machine-readable semantic schema** and **reproducible
annotation pipeline** that connects:

- **Application context** (Annex III employment & essential public services)
- **LLM usage patterns** (decision support, screening, chatbot, etc.)
- **Risk / harm categories** (bias, privacy breach, misinformation, procedural unfairness)
- **Fundamental rights** (non-discrimination, privacy/data protection, social protection, good administration)

The pipeline ingests 150 records from three public sources, annotates them via
keyword rules + LLM-assisted classification + hybrid merge, evaluates label
quality against a manual gold standard, and demonstrates the framework through
FRIA-style retrieval scenarios and a knowledge graph.

---

## Directory Layout

```
.
├── .gitignore
├── README.md
├── requirements.txt
├── run_all.py                        # Orchestrate full pipeline
├── run_all_patch.py                  # Patched runner (fixes for re-runs)
├── run_steps_11_12.py                # Orchestrate causal + KG steps
├── output.txt
├── structure.txt
│
├── .venv/                            # Python virtual environment (not committed)
│
├── AIAAIC AI, algorithmic and automation incidents and controversies/
│   ├── AIAAIC Repository - Incidents.csv
│   ├── aiaaic_ranked_top10.csv
│   ├── aiaaic_ranked_top30.csv
│   ├── aiaaic_subset_broad_first10.csv
│   ├── aiaaic_subset_llm_first10.csv
│   ├── Description.md
│   └── llm_predictions_cache.jsonl
│
├── archive/                          # V1 scripts and outputs (superseded)
│   ├── v1_annotate_records.py
│   ├── v1_compare_methods.py
│   ├── v1_error_analysis.py
│   ├── v1_evaluate_annotations.py
│   ├── v1_expand_aiaaic_fix.py
│   ├── v1_expand_corpus.py
│   ├── v1_export_semantic.py
│   ├── v1_fria_demo.py
│   ├── v1_generate_figures.py
│   ├── v1_llm_annotate.py
│   ├── v1_schema.py
│   ├── v1_run_pipeline.bat
│   └── v1_*.csv / v1_*.jsonl         # V1 outputs
│
├── data/
│   ├── master_annotation_table_v01.csv
│   ├── master_annotation_table_v05.csv
│   ├── aiaaic/
│   │   ├── AIAAIC_Repository_Incidents.csv
│   │   ├── aiaaic_expansion.csv
│   │   ├── aiaaic_incidents.py
│   │   ├── aiaaic_manual_extra.csv
│   │   ├── aiaaic_ranked_top50.csv
│   │   ├── aiaaic_ranked_top100.csv
│   │   ├── hybrid_experiment.py
│   │   ├── label_studio_export.json
│   │   └── manual_vs_llm_comparison.csv
│   ├── ecthr/
│   │   ├── case_law_subset.csv
│   │   └── echr.py
│   └── usfed/
│       ├── 2024_consolidated_ai_inventory_raw_v2.csv
│       ├── usfed_expansion.csv
│       └── usfed_ai.py
│
├── docs/
│   ├── README.md
│   ├── selection_criteria.md
│   └── source_selection_criteria.md
│
├── European Court of Human Rights/
│   ├── Description.md
│   └── final_for_viz.csv
│
├── Federal AI Use Case Inventory/
│   ├── Description.md
│   └── usfederal_subset_first10.csv
│
├── figures/
│   ├── fig_confusion_domain.png
│   ├── fig_confusion_pattern.png
│   ├── fig_domain_distribution.png
│   ├── fig_error_categories.png
│   ├── fig_error_heatmap.png
│   ├── fig_fria_scenario_hits.png
│   ├── fig_harms_agreement.png
│   ├── fig_harms_by_pattern.png
│   ├── fig_harms_distribution.png
│   ├── fig_kappa_summary.png
│   ├── fig_knowledge_graph.png
│   ├── fig_knowledge_graph_full.html
│   ├── fig_knowledge_graph_full.png
│   ├── fig_pattern_distribution.png
│   ├── fig_pipeline_flow.png
│   ├── fig_rights_agreement.png
│   ├── fig_rights_by_domain.png
│   ├── fig_rights_distribution.png
│   ├── fig_rights_harms_heatmap.png
│   ├── fig_source_breakdown.png
│   └── fig_unknown_rates.png
│
├── output/
│   ├── causal_annotation_log.jsonl
│   ├── causal_cache.json
│   ├── causal_summary.csv
│   ├── confusion_matrix_domain.csv
│   ├── confusion_matrix_pattern.csv
│   ├── disagreement_examples.csv
│   ├── error_analysis_disagreements.csv
│   ├── error_analysis_harms.csv
│   ├── error_analysis_report.txt
│   ├── error_analysis_rights.csv
│   ├── error_analysis_summary.txt
│   ├── fria_scenario_results.csv
│   ├── fria_scenario_summary.txt
│   ├── gold_confusion_matrices.txt
│   ├── gold_evaluation_results.csv
│   ├── gold_evaluation_summary.csv
│   ├── knowledge_graph.ttl
│   ├── knowledge_graph_summary.csv
│   ├── llm_predictions_cache_v2.jsonl
│   ├── master_annotation_table_causal.csv
│   ├── master_annotation_table_final.csv
│   ├── master_annotation_table_llm_v2.csv
│   ├── method_comparison_results_v2.csv
│   ├── regulatory_crosswalk.csv
│   ├── regulatory_crosswalk.md
│   └── risk_records_v2.jsonld
│
├── schema/
│   ├── crosswalk_glossary.json
│   ├── example_risk_record.jsonld
│   ├── fria_risk_schema.jsonld
│   ├── fria_risk_schema.ttl
│   └── schema_documentation.md
│
└── src/
    ├── 01_expand_corpus.py
    ├── 02_llm_annotate.py
    ├── 03_compare_methods.py
    ├── 04_evaluate_gold.py
    ├── 05_schema_definition.py
    ├── 06_export_semantic.py
    ├── 07_generate_figures.py
    ├── 07b_alternative_figures.py
    ├── 08_fria_demo_scenarios.py
    ├── 09_error_analysis.py
    ├── 10_regulatory_crosswalk.py
    ├── 11_chain_of_events.py
    ├── 12_knowledge_graph.py
    ├── 13_visualise_knowledge_graph.py
    └── run_all.py
```

---

## Setup

### 1. Create a virtual environment (recommended)

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

---

## How to Run

### Pipeline (Steps 01–10)

```bash
python run_all.py
```
### Pipeline (Steps 7b–10)

```bash
python run_all_patch.py
```

This runs corpus expansion → LLM annotation → method comparison → gold
evaluation → schema definition → semantic export → figures → FRIA demos →
error analysis → regulatory crosswalk.

### Extraction + knowledge graph (Steps 11–13)

```bash
python run_steps_11_12.py
python src/13_visualise_knowledge_graph.py
```

### Interactive knowledge graph

```bash
start figures/fig_knowledge_graph_full.html   # Windows
open figures/fig_knowledge_graph_full.html     # macOS
```

---

## Data Sources

| Source | Records | Type | URL |
|--------|---------|------|-----|
| AIAAIC | ~100 | AI incident reports | https://www.aiaaic.org |
| US Federal AI Inventory | 30 | Government AI use cases | https://github.com/ombegov/2024-Federal-AI-Use-Case-Inventory |
| ECtHR (via HUDOC) | 20 | Fundamental rights case law | https://hudoc.echr.coe.int |

---

## Semantic Vocabularies Used

| Vocabulary | Purpose | URI |
|------------|---------|-----|
| DPV | Data protection concepts | https://w3id.org/dpv/ |
| DPV-Risk | Risk/harm categories | https://w3id.org/dpv/risk/ |
| VAIR | AI risk vocabulary | https://w3id.org/vair/ |
| EU-Rights | EU Charter fundamental rights | https://w3id.org/dpv/legal/eu/rights/ |

---

## Pipeline Architecture

```
data/aiaaic/ ─┐
data/usfed/  ─┤─→ 01_expand_corpus ─→ master_annotation_table_final.csv
data/ecthr/  ─┘         │
                         ├─→ 02_llm_annotate ─→ master_annotation_table_llm_v2.csv
                         │
                         ├─→ 03_compare_methods ─→ method_comparison_results_v2.csv
                         │
                         ├─→ 04_evaluate_gold ─→ gold_evaluation_results.csv
                         │
                         ├─→ 05_schema_definition ──┐
                         ├─→ 06_export_semantic ─────┤─→ schema/*.ttl, *.jsonld
                         │                           │
                         ├─→ 07_generate_figures ────┤─→ figures/*.png
                         │                           │
                         ├─→ 08_fria_demo_scenarios ─┤─→ fria_scenario_*.csv
                         │                           │
                         ├─→ 09_error_analysis ──────┤─→ error_analysis_*.csv
                         │                           │
                         └─→ 10_regulatory_crosswalk ┘─→ regulatory_crosswalk.csv/.md
                                                          │
                         11_chain_of_events ──→ master_annotation_table_causal.csv
                         12_knowledge_graph ──→ knowledge_graph.ttl (1,351 triples)
                         13_visualise_kg     ──→ interactive HTML + static PNG
```

---

## Key Outputs

| Output | Description |
|--------|-------------|
| `master_annotation_table_final.csv` | 150 records with keyword + LLM + hybrid labels |
| `master_annotation_table_causal.csv` | + root_cause, mitigation_reported, source_type |
| `knowledge_graph.ttl` | RDF/Turtle graph (194 nodes, 963 edges, 1,351 triples) |
| `fig_knowledge_graph_full.html` | Interactive, zoomable knowledge graph |
| `fria_scenario_results.csv` | FRIA-style narratives for welfare & recruitment |
| `schema/fria_risk_schema.ttl` | Reusable semantic schema (Turtle) |
| `schema/fria_risk_schema.jsonld` | Reusable semantic schema (JSON-LD) |
| `regulatory_crosswalk.csv` | Rights ↔ obligations mapping |

---

## Evaluation Summary

| Metric | Keyword | LLM | Hybrid |
|--------|---------|-----|--------|
| Domain accuracy | ~60% | ~72% | ~78% |
| Unknown rate | high | low | low |
| Cohen's κ (domain) | — | ~0.55 | ~0.65 |

*(Exact figures generated by `04_evaluate_gold.py` and `03_compare_methods.py`.)*

---

## Reproducibility

- **LLM:** Claude claude-sonnet-4-20250514 via Anthropic API
- **Temperature:** 0 (deterministic)
- **All prompts** logged in `output/llm_predictions_cache_v2.jsonl` and `output/causal_annotation_log.jsonl`
- **Cache layer** prevents duplicate API calls across re-runs
- **Gold standard:** manually annotated records via Label Studio (`data/aiaaic/label_studio_export.json`)

---

## License

This project is submitted as part of an MSc dissertation at Trinity College
Dublin, School of Computer Science and Statistics. All code is provided for
academic evaluation purposes.

---

## Acknowledgements

- Dr David Lewis and Dr Delaram Golpayegani (ADAPT Centre, TCD) for supervision
- AIAAIC for the public incident database
- W3C DPV Community Group for the Data Privacy Vocabulary
- ADAPT Centre for VAIR and FRIA ontology work
