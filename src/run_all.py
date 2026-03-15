
"""
run_all.py  –  Run the complete dissertation pipeline end-to-end.

Execute this from your Dissertation directory:
    python run_all.py

Pipeline order:
  1. expand_corpus.py        → Expand to ≥150 records
  2. improved_llm_annotate.py → Re-annotate with v2 prompts (needs OpenAI key)
  3. compare_methods_v2.py   → Compare all methods
  4. evaluate_gold.py        → Gold-standard evaluation
  5. schema_definition.py    → Generate schema artefacts
  6. export_semantic_v2.py   → Export JSON-LD
  7. generate_figures_v2.py  → Generate all figures
"""

import subprocess, sys, os

SCRIPTS = [
    ("1. Expand corpus", "expand_corpus.py"),
    ("2. LLM annotation v2", "improved_llm_annotate.py"),
    ("3. Method comparison v2", "compare_methods_v2.py"),
    ("4. Gold evaluation", "evaluate_gold.py"),
    ("5. Schema definition", "schema_definition.py"),
    ("6. Semantic export v2", "export_semantic_v2.py"),
    ("7. Generate figures", "generate_figures_v2.py"),
]


def run_script(label, script):
    print(f"\n{'='*60}")
    print(f"  {label}: {script}")
    print(f"{'='*60}")

    if not os.path.exists(script):
        print(f"  ⚠ {script} not found – skipping")
        return False

    result = subprocess.run(
        [sys.executable, script],
        capture_output=True, text=True, timeout=300
    )

    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        print(f"  ⚠ {script} failed (exit code {result.returncode})")
        if result.stderr:
            print(f"  STDERR: {result.stderr[:500]}")
        return False
    return True


def main():
    print("=" * 60)
    print("  DISSERTATION PIPELINE – FULL RUN")
    print("=" * 60)

    successes = 0
    failures = 0

    for label, script in SCRIPTS:
        # Step 2 requires OpenAI key
        if "llm_annotate" in script:
            if not os.environ.get("OPENAI_API_KEY"):
                print(f"\n  ⚠ Skipping {script} – set OPENAI_API_KEY first")
                print(f"     export OPENAI_API_KEY='sk-...'")
                failures += 1
                continue

        try:
            ok = run_script(label, script)
            if ok:
                successes += 1
            else:
                failures += 1
        except Exception as e:
            print(f"  ⚠ Error running {script}: {e}")
            failures += 1

    print(f"\n{'='*60}")
    print(f"  PIPELINE COMPLETE: {successes} succeeded, {failures} failed")
    print(f"{'='*60}")

    # List outputs
    print("\n  Generated files:")
    for ext in [".csv", ".jsonld", ".ttl", ".png", ".md", ".txt"]:
        files = [f for f in os.listdir(".") if f.endswith(ext)]
        if files:
            print(f"    {ext}: {', '.join(sorted(files)[:5])}" +
                  (f" (+{len(files)-5} more)" if len(files) > 5 else ""))


if __name__ == "__main__":
    main()
