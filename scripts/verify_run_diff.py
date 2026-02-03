#!/usr/bin/env python3
"""
CI Run-Diff Policy Enforcement

This script enforces governance policy by comparing a candidate run against a baseline.
It validates that:
1. No new CRITICAL or BLOCKER questions were introduced
2. No unauthorized auto-approvals occurred
3. The governance profile matches expectations

Usage:
  python3 scripts/verify_run_diff.py \\
    --baseline_dir tests/baselines/golden_run_baseline \\
    --candidate_run_id <RUN_ID> \\
    --profile <PROFILE> \\
    --format console

Exit codes:
  0: Policy compliance verified
  1: Policy violation detected
  2: Script error (missing files, invalid args, etc.)
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Constants
OUTPUTS_DIR = Path("outputs")
BLOCKER_SEVERITIES = {"CRITICAL", "BLOCKER"}

def load_audit_summary(run_dir: Path) -> Dict[str, Any]:
    """Load and parse audit_summary.json from a run directory."""
    audit_path = run_dir / "audit_summary.json"
    if not audit_path.exists():
        raise FileNotFoundError(f"Missing audit_summary.json in {run_dir}")
    
    with open(audit_path, 'r') as f:
        return json.load(f)

def load_run_ledger(run_dir: Path) -> List[Dict[str, Any]]:
    """Load and parse run_ledger.jsonl from a run directory."""
    ledger_path = run_dir / "run_ledger.jsonl"
    if not ledger_path.exists():
        return []
    
    ledger = []
    with open(ledger_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                ledger.append(json.loads(line))
    return ledger

def get_top_questions(audit: Dict[str, Any]) -> List[str]:
    """Extract top_10 questions from audit summary."""
    return audit.get("open_questions_summary", {}).get("top_10", [])

def get_severity_counts(audit: Dict[str, Any]) -> Dict[str, int]:
    """Extract severity counts from audit summary."""
    return audit.get("open_questions_summary", {}).get("severity_counts", {})

def get_governance_profile(audit: Dict[str, Any]) -> str:
    """Extract governance profile from audit summary."""
    return audit.get("run_metadata", {}).get("governance_profile", "unknown")

def check_new_blocker_questions(baseline_audit: Dict[str, Any], candidate_audit: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Check if candidate introduced new CRITICAL/BLOCKER questions.
    Returns (passed, violations)
    """
    baseline_questions = set(get_top_questions(baseline_audit))
    candidate_questions = set(get_top_questions(candidate_audit))
    
    new_questions = candidate_questions - baseline_questions
    violations = []
    
    for q in new_questions:
        # Check if it's a blocker severity
        if any(sev in q.upper() for sev in BLOCKER_SEVERITIES):
            violations.append(f"New {sev} question: {q}")
    
    # Also check severity counts
    baseline_sevs = get_severity_counts(baseline_audit)
    candidate_sevs = get_severity_counts(candidate_audit)
    
    for sev in BLOCKER_SEVERITIES:
        baseline_count = baseline_sevs.get(sev.lower(), 0)
        candidate_count = candidate_sevs.get(sev.lower(), 0)
        if candidate_count > baseline_count:
            violations.append(f"Increased {sev} count: {baseline_count} -> {candidate_count}")
    
    return len(violations) == 0, violations

def check_unauthorized_auto_approvals(ledger: List[Dict[str, Any]], expected_profile: str) -> Tuple[bool, List[str]]:
    """
    Check for unauthorized auto-approvals in the ledger.
    
    Policy:
    - Auto-approvals only allowed at phase gates 3, 6, 9
    - Risk gates must be manual (or simulated manual in CI)
    
    Returns (passed, violations)
    """
    violations = []
    
    for entry in ledger:
        if entry.get("event") == "approval":
            gate_num = entry.get("gate_number")
            gate_type = entry.get("gate_type", "").lower()
            approval_type = entry.get("approval_type", "").lower()
            
            # Check if this is an auto-approval
            if approval_type == "auto":
                # Auto-approvals only allowed at phase gates 3, 6, 9
                if gate_type == "phase" and gate_num in [3, 6, 9]:
                    continue  # This is allowed
                else:
                    violations.append(
                        f"Unauthorized auto-approval at gate {gate_num} ({gate_type})"
                    )
            
            # Risk gates should never be auto-approved (must be manual or simulated)
            if gate_type == "risk" and approval_type == "auto":
                violations.append(
                    f"Risk gate {gate_num} was auto-approved (should be manual)"
                )
    
    return len(violations) == 0, violations

def check_governance_profile(candidate_audit: Dict[str, Any], expected_profile: str) -> Tuple[bool, List[str]]:
    """
    Check if the governance profile matches expectations.
    Returns (passed, violations)
    """
    actual_profile = get_governance_profile(candidate_audit)
    
    if actual_profile != expected_profile:
        return False, [f"Profile mismatch: expected '{expected_profile}', got '{actual_profile}'"]
    
    return True, []

def main():
    parser = argparse.ArgumentParser(
        description="CI Run-Diff Policy Enforcement",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--baseline_dir",
        type=Path,
        required=True,
        help="Path to baseline run directory"
    )
    parser.add_argument(
        "--candidate_run_id",
        type=str,
        required=True,
        help="Run ID of candidate run to verify"
    )
    parser.add_argument(
        "--profile",
        type=str,
        required=True,
        help="Expected governance profile (e.g., 'ci', 'dev', 'prod')"
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["console", "json"],
        default="console",
        help="Output format"
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    baseline_dir = args.baseline_dir
    candidate_dir = OUTPUTS_DIR / args.candidate_run_id
    
    # Validate paths exist
    if not baseline_dir.exists():
        print(f"ERROR: Baseline directory not found: {baseline_dir}", file=sys.stderr)
        sys.exit(2)
    
    if not candidate_dir.exists():
        print(f"ERROR: Candidate run directory not found: {candidate_dir}", file=sys.stderr)
        sys.exit(2)
    
    try:
        # Load data
        baseline_audit = load_audit_summary(baseline_dir)
        candidate_audit = load_audit_summary(candidate_dir)
        candidate_ledger = load_run_ledger(candidate_dir)
        
        # Run policy checks
        all_violations = []
        
        # 1. Check for new blocker questions
        passed, violations = check_new_blocker_questions(baseline_audit, candidate_audit)
        if not passed:
            all_violations.extend([f"[BLOCKER_QUESTIONS] {v}" for v in violations])
        
        # 2. Check for unauthorized auto-approvals
        passed, violations = check_unauthorized_auto_approvals(candidate_ledger, args.profile)
        if not passed:
            all_violations.extend([f"[AUTO_APPROVAL] {v}" for v in violations])
        
        # 3. Check governance profile
        passed, violations = check_governance_profile(candidate_audit, args.profile)
        if not passed:
            all_violations.extend([f"[PROFILE] {v}" for v in violations])
        
        # Report results
        if args.format == "json":
            result = {
                "passed": len(all_violations) == 0,
                "violations": all_violations,
                "baseline_dir": str(baseline_dir),
                "candidate_run_id": args.candidate_run_id,
                "expected_profile": args.profile
            }
            print(json.dumps(result, indent=2))
        else:
            print(f"🔍 CI Run-Diff Policy Enforcement")
            print(f"   Baseline: {baseline_dir}")
            print(f"   Candidate: {args.candidate_run_id}")
            print(f"   Expected Profile: {args.profile}")
            print()
            
            if all_violations:
                print(f"❌ POLICY VIOLATIONS DETECTED ({len(all_violations)}):")
                for v in all_violations:
                    print(f"   • {v}")
                print()
            else:
                print("✅ POLICY COMPLIANCE VERIFIED")
                print()
        
        # Exit with appropriate code
        sys.exit(0 if len(all_violations) == 0 else 1)
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(2)

if __name__ == "__main__":
    main()
