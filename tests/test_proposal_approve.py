import pytest
import os
import json
import uuid
import shutil
from datetime import datetime, timezone
from cli.commands import proposal_approve
import sys
from io import StringIO
from unittest.mock import MagicMock, patch

# Helpers
def create_mock_project(tmp_path):
    knowledge = tmp_path / "knowledge"
    knowledge.mkdir()
    (knowledge / "proposals").mkdir()
    (knowledge / "signals").mkdir()
    (knowledge / "validations").mkdir()
    (knowledge / "approvals").mkdir()
    
    governance = tmp_path / "governance"
    governance.mkdir()
    
    # Create approvers config
    config = {
        "schema_version": "1.0.0",
        "approvers": {
            "MEDIUM": ["med_user", "high_user"],
            "HIGH": ["high_user", "high_user_2"]
        }
    }
    with open(governance / "approvers.json", "w") as f:
        json.dump(config, f)
        
    return tmp_path

def create_proposal(project_root, proposal_id, risk_level="LOW"):
    proposal = {
        "governance_id": proposal_id,
        "title": f"Test Proposal {proposal_id}",
        "risk_assessment": {
            "risk_level": risk_level
        }
    }
    with open(project_root / "knowledge" / "proposals" / f"{proposal_id}.json", "w") as f:
        json.dump(proposal, f)
    return proposal

def create_validation(project_root, proposal_id, outcome="PASS", offset_seconds=0):
    evidence_id = str(uuid.uuid4())
    # Ensure distinct timestamps for sorting
    ts = datetime.now(timezone.utc).timestamp() + offset_seconds
    created_at = datetime.fromtimestamp(ts, timezone.utc).isoformat().replace('+00:00', 'Z')
    
    evidence = {
        "governance_id": evidence_id,
        "proposal_id": proposal_id,
        "validation_outcome": outcome,
        "created_at_utc": created_at
    }
    with open(project_root / "knowledge" / "validations" / f"{evidence_id}.json", "w") as f:
        json.dump(evidence, f)
    return evidence_id

@pytest.fixture
def mock_env(tmp_path):
    root = create_mock_project(tmp_path)
    # Patch get_project_root in strict sense, or pass args path?
    # CLI commands assume they are finding project root relative to __file__.
    # We must patch os.path.abspath or structured location.
    # EASIER: We patch execute's project_root resolution logic or change directory?
    # CHANGING CWD is dangerous for other tests.
    # BEST: Patch proposal_approve.execute to use our root.
    
    # Actually, proposal_approve.execute does:
    # project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    # We can mock this line? No, hard to mock local var.
    # We can mock os.path.dirname?
    # Or just mock the entire function? No we want to test logic.
    
    # Let's refactor proposal_approve to accept project_root optionally, but I can't modify it easily now without tool call.
    # I can mock os.path.abspath?
    # Or... copy the file to a temp dir structure that mimics repo? No.
    
    # Workaround: patch `proposal_approve.os.path.join`? Too complex.
    # How about I verify if `execute` allows me to inject it? No.
    
    # Wait, `proposal_approve.execute` calls `get_validations(project_root...)`
    # I can patch `sys.argv`? No.
    
    # let's try to patch `os.path.dirname` to return a path inside `tmp_path/cli/commands`.
    # And ensure we create that structure.
    
    cli_cmds = root / "cli" / "commands"
    cli_cmds.mkdir(parents=True)
    
    # We need to make sure `..` from `cli/commands` goes to `root`.
    # `root/cli/commands/../../` -> `root`.
    
    return root

def run_command(root, args_list):
    # args_list: e.g. ['--proposal', 'p1', '--actor-id', 'u1']
    
    # We need to mock sys.argv? No, execute takes args namespace.
    parser = argparse.ArgumentParser()
    parser.add_argument('--proposal', dest='proposal_id', required=True)
    parser.add_argument('--actor-id', required=True)
    parser.add_argument('--notes')
    args = parser.parse_args(args_list)
    
    # We need to trap sys.exit
    with patch('cli.commands.proposal_approve.sys.exit') as mock_exit:
        # We need to patch where check relies on __file__
        # Logic: project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        # We patch cli.commands.proposal_approve.__file__?
        # It's a module attribute.
        
        # We can set proposal_approve.__file__ = str(root / "cli/commands/proposal_approve.py")
        old_file = proposal_approve.__file__
        proposal_approve.__file__ = str(root / "cli" / "commands" / "proposal_approve.py")
        
        try:
            # We also need to patch output to not pollute console
            with patch('sys.stderr', new=StringIO()) as fake_err:
                 proposal_approve.execute(args)
                 return 0, fake_err.getvalue() # If no exit called, assume 0? But it calls sys.exit(0) at end.
        except Exception as e:
            # If sys.exit was called, we catch it? No, mock captures calls.
            # But the execution flow stops? No, unless side_effect is set.
            pass
        finally:
             proposal_approve.__file__ = old_file
             
        # Check mock calls
        if mock_exit.called:
            code = mock_exit.call_args[0][0]
            # Get stderr from capturing?
            # We need to capture print calls?
            # The code prints to sys.stderr before exit.
            return code, "" # We lost the stderr because it was inside the try block context? 
            # Re-running logic without try/except for now to debug tests.
            
    return -1, "Error"

# Improved run_helper
from governance import approval_ledger

def invoke_approve(root, proposal_id, actor_id, notes=None):
    import argparse
    args = argparse.Namespace(proposal_id=proposal_id, actor_id=actor_id, notes=notes)
    
    # Redirect stderr
    capture_err = StringIO()
    capture_out = StringIO() # It prints to stdout for success
    
    # Patch __file__
    old_file = proposal_approve.__file__
    old_ledger_file = approval_ledger.__file__
    
    proposal_approve.__file__ = str(root / "cli" / "commands" / "proposal_approve.py")
    approval_ledger.__file__ = str(root / "governance" / "approval_ledger.py")
    
    
    def side_effect(code=0):
        raise SystemExit(code)
        
    try:
        with patch('sys.stderr', capture_err), patch('sys.stdout', capture_out), patch('sys.exit') as mock_exit:
            mock_exit.side_effect = side_effect
            try:
                proposal_approve.execute(args)
            except SystemExit as e:
                exit_code = e.code
                if exit_code is None:
                    exit_code = 0
    finally:
        proposal_approve.__file__ = old_file
        approval_ledger.__file__ = old_ledger_file
        
    return exit_code, capture_err.getvalue() + capture_out.getvalue()



def test_low_risk_pass_validation(mock_env):
    create_proposal(mock_env, "p_low", "LOW")
    create_validation(mock_env, "p_low", "PASS")
    
    code, output = invoke_approve(mock_env, "p_low", "any_actor")
    assert code == 0, f"Output: {output}"
    assert "Proposal Approved" in output, f"Output: {output}"
    assert "1/1 approvals" in output

def test_medium_risk_invalid_actor(mock_env):
    create_proposal(mock_env, "p_med", "MEDIUM")
    create_validation(mock_env, "p_med", "PASS")
    
    code, output = invoke_approve(mock_env, "p_med", "random_guy")
    assert code == 2, f"Output: {output}"
    assert "not authorized" in output

def test_medium_risk_valid_actor(mock_env):
    create_proposal(mock_env, "p_med", "MEDIUM")
    create_validation(mock_env, "p_med", "PASS")
    
    code, output = invoke_approve(mock_env, "p_med", "med_user")
    assert code == 0, f"Output: {output}"
    assert "Proposal Approved" in output

def test_high_risk_two_man_rule(mock_env):
    create_proposal(mock_env, "p_high", "HIGH")
    create_validation(mock_env, "p_high", "PASS")
    
    # 1st Approval
    code, output = invoke_approve(mock_env, "p_high", "high_user")
    assert code == 0, f"Output: {output}"
    assert "1/2 approvals" in output, f"Output: {output}"
    assert "Fully Approved: False" in output
    
    # Same actor tries again
    code, output = invoke_approve(mock_env, "p_high", "high_user")
    assert code == 2, f"Output: {output}"
    assert "already approved" in output
    
    # 2nd Distinct Approval
    code, output = invoke_approve(mock_env, "p_high", "high_user_2")
    assert code == 0, f"Output: {output}"
    assert "2/2 approvals" in output
    assert "Fully Approved: True" in output

def test_validation_failure_blocks(mock_env):
    create_proposal(mock_env, "p_fail", "LOW")
    # Old PASS
    create_validation(mock_env, "p_fail", "PASS", offset_seconds=-100)
    # New FAIL
    create_validation(mock_env, "p_fail", "FAIL", offset_seconds=0)
    
    code, output = invoke_approve(mock_env, "p_fail", "any_actor")
    assert code == 2, f"Output: {output}"
    assert "Most recent validation is FAIL" in output or "Most recent validation is FAIL" in output # Check exact string later

def test_ledger_integrity(mock_env):
    create_proposal(mock_env, "p_ledger", "LOW")
    create_validation(mock_env, "p_ledger", "PASS")
    
    invoke_approve(mock_env, "p_ledger", "actor_1")
    
    # Read ledger
    ledger_path = mock_env / "governance" / "approval_ledger.jsonl"
    assert ledger_path.exists(), "Ledger should exist"
    
    with open(ledger_path) as f:
        lines = f.readlines()
        last = json.loads(lines[-1])
        assert last['action'] == "PROPOSAL_APPROVED"
        assert last['decision_metadata']['latest_validation_status_internal'] == "PASS"

import argparse # Re-import needed for invoke helper if inside func, but here global is fine.
