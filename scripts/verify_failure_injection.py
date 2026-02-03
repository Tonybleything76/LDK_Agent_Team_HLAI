#!/usr/bin/env python3
"""
Verify Failure Injection - CI Regression Harness

1. Runs the golden run pipeline (verify_golden_run.py).
2. Modifies the output to inject a CRITICAL failure.
3. Runs verify_run_diff.py against the modified run with PROD profile.
4. Asserts that verify_run_diff.py FAILS (exits 1).

This ensures our CI gate actually catches regressions.
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
VERIFY_GOLDEN_SCRIPT = PROJECT_ROOT / "scripts" / "verify_golden_run.py"
VERIFY_DIFF_SCRIPT = PROJECT_ROOT / "scripts" / "verify_run_diff.py"
BASELINE_DIR = PROJECT_ROOT / "tests" / "baselines" / "golden_run_baseline"

def fail(message):
    print(f"❌ TEST HARNESS FAILED: {message}")
    sys.exit(1)

def main():
    print("🧪 Starting Regression Injection Test Harness...")

    # 1. Run Golden Run to get a clean run
    print("\n1️⃣  Executing Golden Run...")
    result = subprocess.run(
        ["python3", str(VERIFY_GOLDEN_SCRIPT)],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )
    
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        fail(f"verify_golden_run.py failed (code {result.returncode})")
        
    # Extract RUN_ID
    run_id = None
    for line in result.stdout.splitlines():
        if line.startswith("RUN_ID="):
            run_id = line.split("=")[1].strip()
            break
            
    if not run_id:
        print(result.stdout)
        fail("Could not extract RUN_ID from verify_golden_run.py output")
        
    print(f"   Golden Run ID: {run_id}")
    run_dir = PROJECT_ROOT / "outputs" / run_id
    if not run_dir.exists():
        fail(f"Run directory not found: {run_dir}")

    # 2. Inject Failure (CRITICAL Question)
    print("\n2️⃣  Injecting Failure (Mock CRITICAL Question)...")
    audit_path = run_dir / "audit_summary.json"
    
    with open(audit_path, 'r') as f:
        audit_data = json.load(f)
        
    # Inject a critical question
    # MUST inject into open_questions_summary.top_10 because run_diff uses that for comparisons
    if "open_questions_summary" not in audit_data:
        audit_data["open_questions_summary"] = {"top_10": [], "total_count": 0, "severity_counts": {}}
        
    oq_sum = audit_data["open_questions_summary"]
    
    # Add to Top 10
    injected_q = "CRITICAL: Injected Failure Question"
    if "top_10" not in oq_sum:
        oq_sum["top_10"] = []
    
    # Prepend to ensure it's seen
    oq_sum["top_10"].insert(0, injected_q)
    
    # Update total count
    oq_sum["total_count"] = oq_sum.get("total_count", 0) + 1
    
    # Update severity counts
    if "severity_counts" not in oq_sum:
        oq_sum["severity_counts"] = {}
    
    sev = oq_sum["severity_counts"]
    sev["critical"] = sev.get("critical", 0) + 1

    with open(audit_path, 'w') as f:
        json.dump(audit_data, f, indent=2)
        
    print(f"   Injected '{injected_q}' into audit_summary.json (top_10)")

    # 3. Assert verify_run_diff FAILS in PROD mode
    print("\n3️⃣  Verifying Run Diff Fails in PROD mode...")
    
    cmd = [
        "python3", str(VERIFY_DIFF_SCRIPT),
        "--baseline_dir", str(BASELINE_DIR),
        "--candidate_run_id", run_id,
        "--profile", "prod"
    ]
    
    diff_result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )
    
    print("   Output from verify_run_diff:")
    print("-" * 20)
    print(diff_result.stdout)
    print("-" * 20)

    if diff_result.returncode == 0:
        fail("verify_run_diff.py PASSED but should have FAILED due to injected critical question.")
    else:
        print("✅ SUCCESS: verify_run_diff.py failed as expected (exit code 1).")
        print("   Regression test passed.")

if __name__ == "__main__":
    main()
