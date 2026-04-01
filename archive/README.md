# Archive

This directory contains **superseded v1 scripts and outputs** from the initial
prototype phase of the project. They are retained for reference and
provenance but are **not used by the current pipeline**.

All v1 functionality has been replaced by the modular scripts in `src/`
(Steps 01-13).

## Naming Convention

All files are prefixed with `v1_` to distinguish them from the current
pipeline outputs.

## Contents

- `v1_annotate_records.py` — original monolithic annotation script
- `v1_expand_corpus.py`, `v1_expand_aiaaic_fix.py` — corpus expansion prototypes
- `v1_llm_annotate.py` — initial LLM annotation approach
- `v1_evaluate_annotations.py` — early evaluation logic
- `v1_compare_methods.py` — method comparison prototype
- `v1_error_analysis.py` — error analysis prototype
- `v1_export_semantic.py` — semantic export prototype
- `v1_fria_demo.py` — FRIA scenario prototype
- `v1_generate_figures.py` — figure generation prototype
- `v1_schema.py` — original schema definition
- `v1_run_pipeline.bat` — Windows batch runner
- `v1_*.csv`, `v1_*.jsonl`, `v1_*.jsonld`, `v1_*.txt` — v1 output data
- `v0_aiaaic/` — original AIAAIC data directory (now in `data/aiaaic/`)
- `v0_ecthr/` — original ECtHR data directory (now in `data/ecthr/`)
- `v0_usfed/` — original US Federal data directory (now in `data/usfed/`)
