import os
import json
import sys
from pathlib import Path

def verify_latest_run_audit():
    # Find latest run
    outputs_dir = Path("outputs")
    if not outputs_dir.exists():
        print("No outputs directory found.")
        sys.exit(1)
        
    runs = sorted([d for d in outputs_dir.iterdir() if d.is_dir()], key=lambda d: d.name)
    if not runs:
        print("No runs found in outputs/")
        sys.exit(1)
        
    latest_run = runs[-1]
    print(f"Checking run: {latest_run}")
    
    audit_file = latest_run / "audit_summary.json"
    if not audit_file.exists():
        print(f"❌ FAIL: {audit_file} does not exist.")
        sys.exit(1)
        
    print(f"✅ Found audit_summary.json")
    
    try:
        with open(audit_file, "r") as f:
            data = json.load(f)
            
        required_keys = ["run_metadata", "gate_summary", "open_questions_summary", "end_state"]
        missing = [k for k in required_keys if k not in data]
        
        if missing:
            print(f"❌ FAIL: Missing keys: {missing}")
            sys.exit(1)
            
        print("✅ Structure valid")
        print(json.dumps(data, indent=2))
        
    except json.JSONDecodeError:
        print(f"❌ FAIL: Invalid JSON in {audit_file}")
        sys.exit(1)

if __name__ == "__main__":
    verify_latest_run_audit()
