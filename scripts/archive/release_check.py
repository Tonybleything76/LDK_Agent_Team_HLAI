#!/usr/bin/env python3
"""
Release Readiness Checker

Deterministic "release check" command that validates the repo is safe to operate by running:
1) Preflight checks
2) Golden run regression
3) Run report sanity (latest run report JSON is parseable and contains required keys)

Usage:
  python3 scripts/release_check.py [--skip_golden] [--skip_report]
"""

import sys
import subprocess
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
COMMANDS = {
    "preflight": ["python3", "scripts/preflight_check.py"],
    "golden": ["python3", "scripts/verify_golden_run.py"],
    "report": ["python3", "scripts/run_report.py", "--latest", "--format", "json"]
}

REQUIRED_REPORT_KEYS = {
    "header.run_id": ["header", "run_id"],
    "header.end_state": ["header", "end_state"],
    "gates.approvals.manual": ["gates", "approvals", "manual"],
    "gates.approvals.auto": ["gates", "approvals", "auto"],
}

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_result(name: str, passed: bool, error_msg: str = None):
    if passed:
        print(f"{GREEN}✅ {name} passed{RESET}")
    else:
        print(f"{RED}❌ {name} failed{RESET}")
        if error_msg:
             print(f"   {error_msg}")

def run_command(name: str, cmd: List[str]) -> Tuple[bool, str, str]:
    """
    Run a subprocess command and return (success, stdout, stderr).
    """
    print(f"{BOLD}Running {name}...{RESET}")
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def validate_json_keys(data: Dict[str, Any]) -> str:
    """
    Validate presence of required keys in nested dictionary.
    Returns error message string if failed, None if success.
    """
    for key_name, path in REQUIRED_REPORT_KEYS.items():
        current = data
        for part in path:
            if not isinstance(current, dict) or part not in current:
                return f"Missing key: {key_name}"
            current = current[part]
    return None

def main():
    parser = argparse.ArgumentParser(description="Release Readiness Checker")
    parser.add_argument("--skip_golden", action="store_true", help="Skip golden run regression test")
    parser.add_argument("--skip_report", action="store_true", help="Skip run report sanity check")
    args = parser.parse_args()

    checklist: List[Tuple[str, bool]] = []
    failure_details = []

    # 1. Preflight Check
    success, out, err = run_command("Preflight Check", COMMANDS["preflight"])
    checklist.append(("Preflight", success))
    if not success:
        failure_details.append(("Preflight Check", out, err))
        # Fail fast? Requirement says "If any subprocess fails, stop immediately"
        # But we also need to "Identify which step failed".
        # Let's print the checklist and then exit.
    
    if success:
        # 2. Golden Run
        if not args.skip_golden:
            success, out, err = run_command("Golden Run", COMMANDS["golden"])
            checklist.append(("Golden Run", success))
            if not success:
                failure_details.append(("Golden Run", out, err))
        else:
            print(f"{BOLD}Skipping Golden Run{RESET}")
            
    if success and not failure_details:
        # 3. Run Report
        if not args.skip_report:
            success, out, err = run_command("Run Report", COMMANDS["report"])
            
            if not success:
                 checklist.append(("Run Report JSON", False))
                 failure_details.append(("Run Report Script", out, err))
            else:
                # Parse and Validate
                try:
                    data = json.loads(out)
                    validation_error = validate_json_keys(data)
                    if validation_error:
                         checklist.append(("Run Report JSON", False))
                         failure_details.append(("JSON Validation", out, validation_error))
                         success = False
                    else:
                         checklist.append(("Run Report JSON", True))
                except json.JSONDecodeError as e:
                    checklist.append(("Run Report JSON", False))
                    failure_details.append(("JSON Parse", out, str(e)))
                    success = False
        else:
             print(f"{BOLD}Skipping Run Report{RESET}")

    # --- Summary ---
    print(f"\n{BOLD}=== Release Checklist ==={RESET}")
    any_failed = False
    for name, passed in checklist:
        print_result(name, passed)
        if not passed:
            any_failed = True

    if any_failed:
        print(f"\n{RED}{BOLD}FAILED{RESET}")
        for name, out, err in failure_details:
            print(f"\n{BOLD}--- Failure Message ({name}) ---{RESET}")
            # Print last ~40 lines of stderr/stdout if reasonable
            combined = ""
            if out: combined += f"[STDOUT]\n{out}\n"
            if err: combined += f"[STDERR]\n{err}\n"
            
            lines = combined.splitlines()
            if len(lines) > 40:
                print("... (truncated) ...")
                print("\n".join(lines[-40:]))
            else:
                print(combined)
        sys.exit(1)
    else:
        print(f"\n{GREEN}{BOLD}RELEASE CHECK PASSED{RESET}")
        sys.exit(0)

if __name__ == "__main__":
    main()
