#!/usr/bin/env python3
"""
run_all_patch.py
────────────────
Add this to the END of your existing run_all.py to include
the four new scripts.  Or run standalone after run_all.py.
"""

import subprocess, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
SRC  = BASE / "src"

NEW_STEPS = [
    ("STEP 7b", "07b_alternative_figures.py",  "Alternative rights & harms figures"),
    ("STEP 8",  "08_fria_demo_scenarios.py",    "FRIA-style demonstration scenarios"),
    ("STEP 9",  "09_error_analysis.py",         "Error analysis (Section 5.3)"),
    ("STEP 10", "10_regulatory_crosswalk.py",   "Regulatory crosswalk (Objective 1)"),
]

def run_step(label, script, description):
    path = SRC / script
    if not path.exists():
        print(f"\n  ⚠  {path} not found – skipping {label}")
        return False
    print(f"\n{'=' * 60}")
    print(f"  {label}: {description}")
    print(f"{'=' * 60}")
    result = subprocess.run([sys.executable, str(path)], cwd=str(BASE))
    if result.returncode != 0:
        print(f"  ❌ {label} failed (exit code {result.returncode})")
        return False
    return True

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  RUNNING ADDITIONAL PIPELINE STEPS (8–10)")
    print("=" * 60)

    results = {}
    for label, script, desc in NEW_STEPS:
        results[label] = run_step(label, script, desc)

    print("\n" + "=" * 60)
    print("  ADDITIONAL STEPS SUMMARY")
    print("=" * 60)
    for label, ok in results.items():
        print(f"  {'✅' if ok else '❌'} {label}")
    print()
