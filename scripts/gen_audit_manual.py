from orchestrator.audit import generate_audit_summary
import sys

run_id = '20260202_040559'
run_dir = 'outputs/20260202_040559'
print(f"Generating summary for {run_id}...")
path = generate_audit_summary(run_id, run_dir)
print(f"Generated at: {path}")
