#!/usr/bin/env python3
"""
Director Demo Run Pack Generator

Executes a deterministic pipeline run and packages a polished proof-of-work bundle
for executive review.

Usage:
    python3 scripts/generate_director_demo_pack.py
"""

import os
import sys
import json
import shutil
import subprocess
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
EXPORTS_DIR = PROJECT_ROOT / "exports"
LEDGER_PATH = PROJECT_ROOT / "governance" / "run_ledger.jsonl"

def print_step(step: str):
    print(f"\n🔵 {step}...")

def fail(message: str):
    print(f"\n❌ FAILED: {message}")
    sys.exit(1)

def run_pipeline() -> Path:
    """Execute the pipeline and return the run directory."""
    print_step("Executing FULL pipeline run (Profile: CI)")
    
    cmd = [
        "python3", "scripts/run_pipeline.py",
        "--governance_profile", "ci",
        "--auto_approve",
        "--dry_run",
        "--yes"  # Skip cost confirmation
    ]
    
    # We use dry_run provider to be safe and deterministic, as per requirements
    # "PROVIDER=dry_run"
    env = os.environ.copy()
    env["PROVIDER"] = "dry_run"
    env["CI_SIMULATE_MANUAL_RISK_APPROVAL"] = "true"
    
    # Run with captured output to parse run_dir
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        env=env
    )
    
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        fail(f"Pipeline execution failed with code {result.returncode}")

    print("   Pipeline finished successfully.")
    
    # Extract run_dir from stdout
    # Looks for "Audit summary generated: outputs/20260201_223456/audit_summary.json"
    lines = result.stdout.splitlines()
    run_dir = None
    for line in lines:
        if "Audit summary generated" in line:
            # Parse path
            path_str = line.split("generated:")[1].strip()
            run_dir = Path(PROJECT_ROOT) / Path(path_str).parent
            break
            
    if not run_dir or not run_dir.exists():
        # Fallback: Find latest directory in outputs
        subdirs = [d for d in OUTPUTS_DIR.iterdir() if d.is_dir()]
        subdirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        if subdirs:
            run_dir = subdirs[0]
            
    if not run_dir:
        fail("Could not determine run directory from output.")
        
    print(f"   Captured RUN_ID: {run_dir.name}")
    return run_dir

def validate_invariants(run_dir: Path):
    print_step("Validating invariants")
    
    manifest_path = run_dir / "run_manifest.json"
    audit_path = run_dir / "audit_summary.json"
    
    if not manifest_path.exists(): fail("run_manifest.json missing")
    if not audit_path.exists(): fail("audit_summary.json missing")
    
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        with open(audit_path, 'r') as f:
            audit = json.load(f)
    except json.JSONDecodeError:
        fail("Failed to decode JSON artifacts")

    # 1. audit.run_id matches RUN_ID
    if audit.get("run_id") != run_dir.name:
        fail(f"Audit run_id mismatch: {audit.get('run_id')} != {run_dir.name}")
        
    # 2. gate_manifest.planned_phase_gates == [3,6,9]
    # In manifest, it's under approval_config -> phase_gates usually, 
    # but audit has 'gate_manifest' or we check manifest directly.
    # The requirement says "gate_manifest.planned_phase_gates", likely meaning inside audit or manifest.
    # We found it in audit["gate_manifest"]["planned_phase_gates"]
    phase_gates = audit.get("gate_manifest", {}).get("planned_phase_gates")
    if phase_gates != [3, 6, 9]:
        fail(f"Planned phase gates mismatch. Expected [3, 6, 9], got {phase_gates}")
        
    # 3. >= 1 phase gate encountered
    # In audit -> gate_summary -> phase_gates
    encountered = audit.get("gate_summary", {}).get("phase_gates", [])
    if len(encountered) < 1:
        fail("No phase gates encountered")

    # 4. >= 1 step_approved event in ledger (for this run_id)
    # 5. >= 1 risk_gate_forced event in ledger (for this run_id)
    step_approved_found = False
    risk_gate_forced_found = False
    
    if not LEDGER_PATH.exists():
        fail("Ledger file missing")
        
    with open(LEDGER_PATH, 'r') as f:
        for line in f:
            try:
                evt = json.loads(line)
                if evt.get("run_id") == run_dir.name:
                    if evt.get("event") == "step_approved":
                        step_approved_found = True
                    if evt.get("event") == "risk_gate_forced":
                        risk_gate_forced_found = True
            except:
                pass
                
    if not step_approved_found:
        fail("No 'step_approved' event found in ledger")
    if not risk_gate_forced_found:
        fail("No 'risk_gate_forced' event found in ledger")
        
    # 6. manifest.status == "completed"
    if manifest.get("status") != "completed":
        fail(f"Manifest status is '{manifest.get('status')}', expected 'completed'")
        
    print("   ✅ All invariants passed.")

def generate_summary(run_dir: Path) -> Dict[str, Any]:
    print_step("Generating Director Summary")
    
    with open(run_dir / "audit_summary.json", 'r') as f:
        audit = json.load(f)
    
    # Extract data for summary
    run_id = audit.get("run_id")
    # Governance profile from audit or we know it's "ci"
    # The requirement says "governance_profile": "ci"
    status = audit.get("end_state", "").replace("run_", "") # "run_completed" -> "completed"
    
    # If end_state is just "completed" or something else, handle it. 
    # Manifest has "status": "completed". Let's use that if available to match req exactly.
    with open(run_dir / "run_manifest.json", 'r') as f:
        manifest = json.load(f)
    if manifest.get("status") == "completed":
        status = "completed"
    
    phase_gates = audit.get("gate_summary", {}).get("phase_gates", [])
    
    # risk_gates count
    risk_gates = len(audit.get("gate_summary", {}).get("risk_gates", []))
    
    # approvals
    approvals = audit.get("gate_summary", {}).get("approvals", {"manual": 0, "auto": 0})
    
    summary = {
        "run_id": run_id,
        "governance_profile": "ci",
        "status": status,
        "phase_gates": phase_gates,
        "risk_gates": risk_gates,
        "approvals": approvals,
        "ledger_events_verified": True,
        "artifacts": {
            "manifest": f"{run_dir.name}/run_manifest.json",
            "audit": f"{run_dir.name}/audit_summary.json"
        }
    }
    
    # Ensure exports dir exists
    EXPORTS_DIR.mkdir(exist_ok=True)
    
    summary_path = EXPORTS_DIR / "director_demo_run_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
        
    print(f"   Generated: {summary_path}")
    return summary

def create_zip_bundle(run_dir: Path):
    print_step("Creating ZIP Bundle")
    
    zip_path = EXPORTS_DIR / "director_demo_run_pack.zip"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add run_manifest.json
        zf.write(run_dir / "run_manifest.json", arcname="run_manifest.json")
        
        # Add audit_summary.json
        zf.write(run_dir / "audit_summary.json", arcname="audit_summary.json")
        
        # Add director_demo_run_summary.json
        zf.write(EXPORTS_DIR / "director_demo_run_summary.json", arcname="director_demo_run_summary.json")
        
        # Add filtered ledger events
        ledger_content = []
        with open(LEDGER_PATH, 'r') as f:
            for line in f:
                try:
                    evt = json.loads(line)
                    if evt.get("run_id") == run_dir.name:
                        ledger_content.append(evt)
                except:
                    pass
        
        # We need to write this to a temp string or file then add to zip
        # Let's write to a temp file in exports first
        temp_ledger_path = EXPORTS_DIR / "run_ledger_filtered.jsonl"
        with open(temp_ledger_path, 'w') as f:
            for evt in ledger_content:
                f.write(json.dumps(evt) + "\n")
        
        zf.write(temp_ledger_path, arcname="run_ledger_filtered.jsonl")
        
        # Clean up temp file
        os.remove(temp_ledger_path)
        
    print(f"   Bundle created: {zip_path}")

def main():
    try:
        run_dir = run_pipeline()
        validate_invariants(run_dir)
        generate_summary(run_dir)
        create_zip_bundle(run_dir)
        
        print("\n" + "="*60)
        print(f"DIRECTOR DEMO PACK READY: exports/director_demo_run_pack.zip")
        print("="*60 + "\n")
        
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(130)
    except Exception as e:
        fail(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
