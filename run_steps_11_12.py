"""
run_steps_11_12.py  —  Run chain-of-events extraction + knowledge graph build.

Can be run from anywhere — scripts auto-resolve the project root.

Usage:
    python run_steps_11_12.py                 (from src/)
    python src/run_steps_11_12.py             (from project root)
"""

import subprocess, sys, os
from pathlib import Path

# Auto-resolve project root
SCRIPT_DIR = Path(__file__).resolve().parent
if SCRIPT_DIR.name == "src":
    PROJECT_ROOT = SCRIPT_DIR.parent
    SRC_DIR = SCRIPT_DIR
else:
    PROJECT_ROOT = SCRIPT_DIR
    SRC_DIR = SCRIPT_DIR / "src"

os.chdir(PROJECT_ROOT)
print(f"Project root: {PROJECT_ROOT}")

def run(label, script_name):
    # Try src/ first, then current dir
    script = SRC_DIR / script_name
    if not script.exists():
        script = PROJECT_ROOT / script_name
    if not script.exists():
        print(f"  ERROR: Cannot find {script_name}")
        print(f"    Tried: {SRC_DIR / script_name}")
        print(f"    Tried: {PROJECT_ROOT / script_name}")
        return 1

    print(f"\n{'='*70}")
    print(f"  {label}")
    print(f"  Script: {script}")
    print(f"{'='*70}")
    result = subprocess.run([sys.executable, str(script)],
                            capture_output=False, text=True,
                            cwd=str(PROJECT_ROOT))
    if result.returncode != 0:
        print(f"  {script_name} exited with code {result.returncode}")
    return result.returncode


def main():
    rc1 = run("STEP 11  Chain-of-events + mitigation extraction",
              "11_chain_of_events.py")

    rc2 = run("STEP 12  Knowledge graph construction",
              "12_knowledge_graph.py")

    print(f"\n{'='*70}")
    print(f"  DONE")
    print(f"  Step 11: {'OK' if rc1 == 0 else 'check errors'}")
    print(f"  Step 12: {'OK' if rc2 == 0 else 'check errors'}")
    print(f"{'='*70}")

    print(f"\nNew output files:")
    for f in [
        "output/master_annotation_table_causal.csv",
        "output/causal_summary.csv",
        "output/causal_annotation_log.jsonl",
        "output/knowledge_graph.ttl",
        "output/knowledge_graph_summary.csv",
        "figures/fig_knowledge_graph.png",
    ]:
        p = PROJECT_ROOT / f
        tag = "OK" if p.exists() else "--"
        print(f"  {tag}  {f}")


if __name__ == "__main__":
    main()
