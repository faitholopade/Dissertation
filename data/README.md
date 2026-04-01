# Data Sources

This directory contains the raw and processed data used by the annotation pipeline.

## Subdirectories

| Directory | Source | Description |
|-----------|--------|-------------|
| `aiaaic/` | [AIAAIC Repository](https://www.aiaaic.org) | AI, algorithmic, and automation incident records (~100 selected) |
| `ecthr/` | [HUDOC](https://hudoc.echr.coe.int) | European Court of Human Rights case law (20 selected) |
| `usfed/` | [Federal AI Inventory](https://github.com/ombegov/2024-Federal-AI-Use-Case-Inventory) | US Federal AI use cases (30 selected) |

## Master Annotation Tables

| File | Records | Description |
|------|---------|-------------|
| `master_annotation_table_v01.csv` | 90 | Initial corpus (60 AIAAIC + 20 ECtHR + 10 USFED) |
| `master_annotation_table_v05.csv` | 150 | Expanded corpus used by the pipeline |

## Gold Standard

| File | Records | Description |
|------|---------|-------------|
| `aiaaic/manual_vs_llm_comparison.csv` | 69 | Manually annotated AIAAIC records for evaluation |
| `aiaaic/label_studio_export.json` | -- | Label Studio annotation export |
