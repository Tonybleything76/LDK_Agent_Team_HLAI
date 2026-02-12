#!/usr/bin/env python3
"""
Test: Auto-Approval Attribution Correctness

Verifies that ledger events correctly attribute auto-approval to either:
1. Governance profile (when enabled via --governance_profile)
2. CLI flag (when enabled via --auto_approve)

This test ensures audit compliance by verifying that the approval_source
field accurately reflects the actual source of auto-approval.
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

LEDGER_PATH = PROJECT_ROOT / "governance" / "run_ledger.jsonl"


def read_ledger_events(run_id: str) -> list:
    """Read all ledger events for a specific run_id."""
    events = []
    if not LEDGER_PATH.exists():
        return events
    
    with open(LEDGER_PATH, "r") as f:
        for line in f:
            if line.strip():
                event = json.loads(line)
                if event.get("run_id") == run_id:
                    events.append(event)
    return events


def test_profile_auto_approval_attribution():
    """
    Test Case 1: Dev profile auto-approval
    
    Command: python3 scripts/run_pipeline.py --governance_profile dev --max-step 3
    
    Expected: ledger step_approved entries contain:
        "approval_source": "profile"
        "approval_reason": "Auto-approval enabled by governance profile: dev"
    """
    print("\\n" + "=" * 70)
    print("TEST CASE 1: Profile-Based Auto-Approval Attribution")
    print("=" * 70)
    
    # Run pipeline with dev profile (auto-approve enabled by profile)
    cmd = [
        "python3", "scripts/run_pipeline.py",
        "--governance_profile", "dev",
        "--max-step", "3",
        "--dry_run",  # Use dry_run to avoid API calls
        "--yes",  # Skip cost confirmation
        "--allow-dirty-worktree"  # Allow testing with modified files
    ]
    
    print(f"\\nExecuting: {' '.join(cmd)}")
    
    # No input needed with --yes flag
    input_data = ""
    
    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        input=input_data,
        capture_output=True,
        text=True
    )
    
    print(f"\\nReturn code: {result.returncode}")
    
    if result.returncode != 0:
        print(f"STDERR:\\n{result.stderr}")
        print(f"STDOUT:\\n{result.stdout}")
        raise AssertionError(f"Pipeline failed with return code {result.returncode}")
    
    # Extract run_id from output
    run_id = None
    for line in result.stdout.split("\\n"):
        if "run_id" in line.lower() or "20" in line:
            # Look for timestamp pattern YYYYMMDD_HHMMSS
            import re
            match = re.search(r'(\\d{8}_\\d{6})', line)
            if match:
                run_id = match.group(1)
                break
    
    # Alternative: find latest run directory
    if not run_id:
        outputs_dir = PROJECT_ROOT / "outputs"
        if outputs_dir.exists():
            runs = sorted([d.name for d in outputs_dir.iterdir() if d.is_dir() and d.name.startswith("20")])
            if runs:
                run_id = runs[-1]
    
    if not run_id:
        raise AssertionError("Could not determine run_id from pipeline output")
    
    print(f"\\nRun ID: {run_id}")
    
    # Read ledger events for this run
    events = read_ledger_events(run_id)
    
    # Filter step_approved events
    approved_events = [e for e in events if e.get("event") == "step_approved"]
    
    print(f"\\nFound {len(approved_events)} step_approved events")
    
    if len(approved_events) == 0:
        raise AssertionError("No step_approved events found in ledger")
    
    # Verify each approval has correct attribution
    failures = []
    for event in approved_events:
        approval_source = event.get("approval_source")
        approval_reason = event.get("approval_reason")
        step_idx = event.get("step_idx")
        
        print(f"\\nStep {step_idx}:")
        print(f"  approval_source: {approval_source}")
        print(f"  approval_reason: {approval_reason}")
        
        # Expected values for profile-based auto-approval
        if approval_source != "profile":
            failures.append(
                f"Step {step_idx}: Expected approval_source='profile', got '{approval_source}'"
            )
        
        # For risk gates, the approval_reason is different
        expected_reason = "Auto-approval enabled by governance profile: dev"
        expected_risk_reason = "Auto-approve override after risk gate"
        
        if approval_reason not in [expected_reason, expected_risk_reason]:
            failures.append(
                f"Step {step_idx}: Expected approval_reason='{expected_reason}' or '{expected_risk_reason}', got '{approval_reason}'"
            )
    
    if failures:
        print("\\n❌ TEST FAILED:")
        for failure in failures:
            print(f"  - {failure}")
        raise AssertionError(f"{len(failures)} attribution errors found")
    
    print("\\n✅ TEST PASSED: All approvals correctly attributed to profile")
    return True


def test_cli_flag_auto_approval_attribution():
    """
    Test Case 2: CLI flag auto-approval
    
    Command: python3 scripts/run_pipeline.py --auto_approve --max-step 3
    
    Expected: ledger step_approved entries contain:
        "approval_source": "cli_flag"
        "approval_reason": "Auto-approval enabled via CLI flag"
    """
    print("\\n" + "=" * 70)
    print("TEST CASE 2: CLI Flag Auto-Approval Attribution")
    print("=" * 70)
    
    # Sleep for 2 seconds to ensure different run_id
    print("\\nWaiting 2 seconds to ensure unique run_id...")
    time.sleep(2)
    
    # Run pipeline with explicit --auto_approve flag (no governance profile)
    cmd = [
        "python3", "scripts/run_pipeline.py",
        "--auto_approve",
        "--max-step", "3",
        "--dry_run",  # Use dry_run to avoid API calls
        "--yes",  # Skip cost confirmation
        "--skip_preflight",  # Skip preflight to bypass worktree check
        "--allow-dirty-worktree"  # Allow testing with modified files
    ]
    
    print(f"\\nExecuting: {' '.join(cmd)}")
    
    # No input needed with --yes flag
    input_data = ""
    
    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        input=input_data,
        capture_output=True,
        text=True
    )
    
    print(f"\\nReturn code: {result.returncode}")
    
    if result.returncode != 0:
        print(f"STDERR:\\n{result.stderr}")
        print(f"STDOUT:\\n{result.stdout}")
        raise AssertionError(f"Pipeline failed with return code {result.returncode}")
    
    # Extract run_id from output
    run_id = None
    import re
    for line in result.stdout.split("\\n"):
        match = re.search(r'(\\d{8}_\\d{6})', line)
        if match:
            run_id = match.group(1)
            break
    
    # Alternative: find latest run directory
    if not run_id:
        outputs_dir = PROJECT_ROOT / "outputs"
        if outputs_dir.exists():
            runs = sorted([d.name for d in outputs_dir.iterdir() if d.is_dir() and d.name.startswith("20")])
            if runs:
                run_id = runs[-1]
    
    if not run_id:
        raise AssertionError("Could not determine run_id from pipeline output")
    
    print(f"\\nRun ID: {run_id}")
    
    # Read ledger events for this run
    events = read_ledger_events(run_id)
    
    # Filter step_approved events
    approved_events = [e for e in events if e.get("event") == "step_approved"]
    
    print(f"\\nFound {len(approved_events)} step_approved events")
    
    if len(approved_events) == 0:
        raise AssertionError("No step_approved events found in ledger")
    
    # Verify each approval has correct attribution
    failures = []
    for event in approved_events:
        approval_source = event.get("approval_source")
        approval_reason = event.get("approval_reason")
        step_idx = event.get("step_idx")
        
        print(f"\\nStep {step_idx}:")
        print(f"  approval_source: {approval_source}")
        print(f"  approval_reason: {approval_reason}")
        
        # Expected values for CLI flag auto-approval
        if approval_source != "cli_flag":
            failures.append(
                f"Step {step_idx}: Expected approval_source='cli_flag', got '{approval_source}'"
            )
        
        # For risk gates, the approval_reason is different
        expected_reason = "Auto-approval enabled via CLI flag"
        expected_risk_reason = "Auto-approve override after risk gate"
        
        if approval_reason not in [expected_reason, expected_risk_reason]:
            failures.append(
                f"Step {step_idx}: Expected approval_reason='{expected_reason}' or '{expected_risk_reason}', got '{approval_reason}'"
            )
    
    if failures:
        print("\\n❌ TEST FAILED:")
        for failure in failures:
            print(f"  - {failure}")
        raise AssertionError(f"{len(failures)} attribution errors found")
    
    print("\\n✅ TEST PASSED: All approvals correctly attributed to CLI flag")
    return True


if __name__ == "__main__":
    try:
        # Test 1: Profile-based auto-approval
        test_profile_auto_approval_attribution()
        
        # Test 2: CLI flag auto-approval
        test_cli_flag_auto_approval_attribution()
        
        print("\\n" + "=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        sys.exit(0)
        
    except Exception as e:
        print(f"\\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
