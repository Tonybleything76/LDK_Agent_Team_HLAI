#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

def create_mock_run(base_dir: Path, run_id: str, profile: str, sevs: dict, top_qs: list):
    run_dir = base_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    audit = {
        "run_metadata": {
            "run_id": run_id,
            "governance_profile": profile,
            "open_questions_threshold": 3 if profile == 'dev' else 0,
            "weighted_severities": ["MAJOR", "CRITICAL"],
            "risk_gate_escalation_enabled": True,
            "auto_approve": True,
            "risk_auto_override_default": True
        },
        "gate_summary": {
            "phase_gates": [{"a": 1}, {"a": 2}],
            "risk_gates": [{"b": 1}] if profile == 'dev' else [{"b": 1}, {"b": 2}]
        },
        "open_questions_summary": {
            "total_count": sum(sevs.values()),
            "severity_counts": sevs,
            "top_10": top_qs
        }
    }
    
    with open(run_dir / "audit_summary.json", 'w') as f:
        json.dump(audit, f)
    return run_dir

def main():
    print("Verifying run_diff.py...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        outputs = tmp_path / "outputs"
        outputs.mkdir()
        
        # Run A
        run_a = create_mock_run(outputs, "run_a", "dev", {"major": 10}, ["Issue A", "Issue B"])
        
        # Run B
        run_b = create_mock_run(outputs, "run_b", "prod", {"major": 5, "critical": 1}, ["Issue B", "Issue C"])
        
        # Run diff
        cmd = [
            sys.executable,
            "scripts/run_diff.py",
            str(run_a),
            str(run_b)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"FAILED: Exit code {result.returncode}")
            print(result.stderr)
            sys.exit(1)
            
        out = result.stdout
        print("Output:\n", out)
        
        # Assertions
        assert "governance_profile: 'dev' -> 'prod'" in out, "Missing profile diff"
        assert "open_questions_threshold: '3' -> '0'" in out, "Missing threshold diff"
        assert "Risk Gates Count: 1 -> 2" in out, "Missing risk gate count diff"
        assert "major: 10 -> 5" in out, "Missing major sev diff"
        assert "critical: 0 -> 1" in out, "Missing critical sev diff"
        assert "[NEW]\n   + Issue C" in out, "Missing new issue"
        assert "[RESOLVED/GONE]\n   - Issue A" in out, "Missing resolved issue"
        
        print("SUCCESS: All diffs verified.")

if __name__ == "__main__":
    main()
