import json
import pytest
from pathlib import Path

def test_risk_gate_trigger():
    audit_path = Path("outputs/20260210_202335/audit_summary.json")
    assert audit_path.exists(), f"Audit summary not found at {audit_path}"
    
    with open(audit_path, "r") as f:
        audit_data = json.load(f)
    
    # 1. Assert critical open question exists
    critical_count = audit_data["open_questions_summary"]["severity_counts"].get("critical", 0)
    assert critical_count >= 1, f"Expected at least 1 critical severity, found {critical_count}"
    
    # 2. Assert total weighted open questions exceeds threshold (8)
    total_count = audit_data["open_questions_summary"]["total_count"]
    # implied threshold from user request is 8; in file it says "open_questions_threshold": 8
    threshold = audit_data["run_metadata"].get("open_questions_threshold", 8) 
    assert total_count > threshold, f"Expected total_count {total_count} > threshold {threshold}"
    
    # 3. Assert risk gates triggered
    risk_gates = audit_data["gate_summary"].get("risk_gates", [])
    assert len(risk_gates) > 0, "Risk gates should not be empty when critical issues exist and threshold is exceeded"
