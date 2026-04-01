# Run the full dissertation pipeline from project root

import subprocess, sys, os

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

# Ensure child processes use UTF-8 encoding (avoids cp1252 failures on Windows)
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

print(f"Working directory: {ROOT}\n")

required_files = {
    "src/01_expand_corpus.py":      "Corpus expansion",
    "src/02_llm_annotate.py":       "LLM annotation",
    "src/03_compare_methods.py":    "Method comparison",
    "src/04_evaluate_gold.py":      "Gold-standard evaluation",
    "src/05_schema_definition.py":  "Schema generation",
    "src/06_export_semantic.py":    "JSON-LD export",
    "src/07_generate_figures.py":   "Figure generation",
    "src/sparql_demo.py":           "SPARQL query demo",
    "src/multi_model_comparison.py": "Multi-model comparison",
}

required_data = {
    "data/master_annotation_table_v01.csv":  "Original 90-row master table",
    "data/master_annotation_table_v05.csv":  "Expanded 150-row master table",
    "data/aiaaic/AIAAIC_Repository_Incidents.csv": "Full AIAAIC incidents",
    "data/aiaaic/manual_vs_llm_comparison.csv":    "Gold-standard annotations",
}

print("=" * 60)
print("  STEP 0: Checking required files")
print("=" * 60)

all_ok = True
for path, desc in {**required_files, **required_data}.items():
    exists = os.path.exists(path)
    status = "[OK]" if exists else "[FAIL]"
    print(f"  {status} {path:50s} {desc}")
    if not exists:
        all_ok = False

if not all_ok:
    print("\n[WARN] Some files are missing! Fix before running.")
    sys.exit(1)

if "--check" in sys.argv:
    print("\n[OK] All files present. Run without --check to execute pipeline.")
    sys.exit(0)

steps = [
    ("STEP 1: Expand corpus to 150 records",         "src/01_expand_corpus.py"),
    ("STEP 2: LLM annotation (uses cache)",         "src/02_llm_annotate.py"),
    ("STEP 3: Compare keyword vs LLM methods",      "src/03_compare_methods.py"),
    ("STEP 4: Gold-standard evaluation",            "src/04_evaluate_gold.py"),
    ("STEP 5: Generate schema artefacts",           "src/05_schema_definition.py"),
    ("STEP 6: Export JSON-LD records",              "src/06_export_semantic.py"),
    ("STEP 7: Generate dissertation figures",       "src/07_generate_figures.py"),
    ("STEP 7b: Alternative rights & harms figures", "src/07b_alternative_figures.py"),
    ("STEP 8: FRIA-style demonstration scenarios",  "src/08_fria_demo_scenarios.py"),
    ("STEP 9: Error analysis",                      "src/09_error_analysis.py"),
    ("STEP 10: Regulatory crosswalk",               "src/10_regulatory_crosswalk.py"),
    ("STEP 11: Chain-of-events + mitigation extraction", "src/11_chain_of_events.py"),
    ("STEP 12: Knowledge graph construction",        "src/12_knowledge_graph.py"),
    ("STEP 14: SPARQL query demonstrations",         "src/sparql_demo.py"),
    ("STEP 15: Multi-model LLM comparison",          "src/multi_model_comparison.py"),
]

results = []
for desc, script in steps:
    print(f"\n{'=' * 60}")
    print(f"  {desc}")
    print(f"{'=' * 60}")

    if not os.path.exists(script):
        print(f"\n[WARN] {script} not found - skipping")
        results.append((desc, False))
        continue

    result = subprocess.run(
        [sys.executable, script],
        cwd=ROOT,
    )

    success = result.returncode == 0
    results.append((desc, success))

    if not success:
        print(f"\n[WARN] {script} failed with exit code {result.returncode}")
        print("  Stopping pipeline. Fix the error above and re-run.")
        sys.exit(1)

print(f"\n{'=' * 60}")
print(f"  PIPELINE COMPLETE")
print(f"{'=' * 60}")
for desc, ok in results:
    print(f"  {'[OK]' if ok else '[FAIL]'} {desc}")

# Check output files
print(f"\n  Output files:")
outputs = [
    "output/master_annotation_table_final.csv",
    "output/master_annotation_table_llm_v2.csv",
    "output/gold_evaluation_summary.csv",
    "output/risk_records_v2.jsonld",
    "schema/fria_risk_schema.jsonld",
    "schema/fria_risk_schema.ttl",
    "output/master_annotation_table_causal.csv",
    "output/causal_summary.csv",
    "output/causal_annotation_log.jsonl",
    "output/knowledge_graph.ttl",
    "output/knowledge_graph_summary.csv",
    "output/sparql_demo_results.txt",
    "output/multi_model_comparison.csv",
    "output/multi_model_comparison_summary.txt",
]
for f in outputs:
    print(f"    {'[OK]' if os.path.exists(f) else '[FAIL]'} {f}")

fig_count = len([f for f in os.listdir("figures") if f.endswith(".png")])
print(f"    {'[OK]' if fig_count >= 13 else '[FAIL]'} figures/ ({fig_count} PNGs)")

print(f"\n[OK] All done! Your dissertation artefacts are ready.")
