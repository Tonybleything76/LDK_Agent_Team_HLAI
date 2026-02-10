import os
import json
import pytest
from orchestrator.audit import generate_audit_summary

def test_audit_summary_completeness():
    """
    Regression test to ensure audit_summary.json always contains:
    - run_id (string)
    - gate_manifest (dict, non-null) with keys: phase_gates, risk_gates, approvals
    
    This test uses an existing run output directory if available, 
    otherwise mocking is required (but instructions prefer using the existing 20260210_213017).
    """
    run_id = "20260210_213017"
    run_dir = f"outputs/{run_id}"
    
    # Check if the target run directory exists
    if not os.path.isdir(run_dir):
        pytest.skip(f"Run directory {run_dir} not found. Skipping regression test.")

    # Regenerate audit summary cleanly (suppress ledger events to avoid polluting ledger)
    output_path = generate_audit_summary(run_id, run_dir, suppress_ledger_events=True)
    
    assert output_path is not None, "Audit summary generation failed"
    assert os.path.exists(output_path), "Audit summary file not written"
    
    with open(output_path, "r") as f:
        summary = json.load(f)
        
    # 1. Verify run_id
    assert "run_id" in summary, "run_id missing from audit summary"
    assert summary["run_id"] == run_id, f"run_id mismatch: expected {run_id}, got {summary.get('run_id')}"
    
    # 2. Verify gate_manifest
    assert "gate_manifest" in summary, "gate_manifest missing from audit summary"
    assert isinstance(summary["gate_manifest"], dict), "gate_manifest must be a dictionary"
    
    manifest = summary["gate_manifest"]
    required_keys = ["phase_gates", "risk_gates", "approvals"]
    for key in required_keys:
        assert key in manifest, f"Key '{key}' missing from gate_manifest"
        
    # Optional: Verify risk_gates logic if known to be present in this run
    # (The instructions mention this run should have risk gates, but we stick to schema completeness mostly)
    # assert isinstance(manifest["risk_gates"], list)
