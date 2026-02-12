import pytest
import sys
import os
import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Add scripts to path to import the module
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import enforce_promotion_guard
from governance import approval_ledger

class ExitException(Exception):
    def __init__(self, code):
        self.code = code

@pytest.fixture
def mock_sys_exit(monkeypatch):
    mock = MagicMock()
    def side_effect(code):
        raise ExitException(code)
    
    mock.side_effect = side_effect
    monkeypatch.setattr(sys, "exit", mock)
    return mock

@pytest.fixture
def mock_subprocess(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr(subprocess, "check_output", mock)
    return mock

@pytest.fixture
def mock_verify_ledger(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr(approval_ledger, "verify_ledger", mock)
    return mock

@pytest.fixture
def mock_path_exists(monkeypatch):
    # Mock Path.exists globally for usage in script
    mock = MagicMock(return_value=False)
    monkeypatch.setattr(Path, "exists", mock)
    return mock

def run_main_expecting_code(code, mock_sys_exit):
    try:
        enforce_promotion_guard.main()
    except ExitException as e:
        assert e.code == code
        mock_sys_exit.assert_called_with(code)
    except SystemExit as e:
        assert e.code == code
    else:
        pytest.fail(f"main() did not exit, expected {code}")

def test_no_governed_changes(mock_subprocess, mock_sys_exit):
    mock_subprocess.return_value = b"README.md\n"
    run_main_expecting_code(0, mock_sys_exit)

def test_governed_changes_no_promo_id(mock_subprocess, mock_sys_exit, monkeypatch):
    def side_effect(cmd, **kwargs):
        cmd_str = " ".join(cmd)
        if "git diff" in cmd_str:
            return b"prompts/test_prompt.md\n"
        if "git log" in cmd_str:
            return b"Update prompt\n" 
        return b""
        
    mock_subprocess.side_effect = side_effect
    monkeypatch.delenv("ADK_PROMOTION_ID", raising=False)
    
    run_main_expecting_code(3, mock_sys_exit)

def test_governed_changes_valid_id_in_commit_msg(mock_subprocess, mock_sys_exit, mock_verify_ledger, mock_path_exists):
    promo_id = "test-uuid-1234"
    
    def side_effect(cmd, **kwargs):
        cmd_str = " ".join(cmd)
        if "git diff" in cmd_str:
            return b"schemas/test_schema.json\n"
        if "git log" in cmd_str:
            return f"Update schema\nPROMOTION_ID={promo_id}\n".encode()
        if "git rev-parse" in cmd_str:
            return b"target_hash_123\n"
        return b""
    mock_subprocess.side_effect = side_effect
    
    # Mock Path.exists to return True
    mock_path_exists.return_value = True
    
    promo_content = json.dumps({
        "id": promo_id,
        "target_commit_hash": "target_hash_123"
    })
    
    with patch("builtins.open", mock_open(read_data=promo_content)):
         run_main_expecting_code(0, mock_sys_exit)
    
    mock_verify_ledger.assert_called_once()

def test_governed_changes_valid_id_in_env_var(mock_subprocess, mock_sys_exit, mock_verify_ledger, monkeypatch, mock_path_exists):
    promo_id = "test-uuid-env"
    
    def side_effect(cmd, **kwargs):
        cmd_str = " ".join(cmd)
        if "git diff" in cmd_str:
            return b"orchestrator/root_agent.py\n" 
        if "git log" in cmd_str:
            return b"Update agent\n" 
        if "git rev-parse" in cmd_str:
            return b"target_hash_env\n"
        return b""
    mock_subprocess.side_effect = side_effect
    
    monkeypatch.setenv("ADK_PROMOTION_ID", promo_id)
    mock_path_exists.return_value = True
    
    promo_content = json.dumps({
        "id": promo_id,
        "target_commit_hash": "target_hash_env"
    })
    
    with patch("builtins.open", mock_open(read_data=promo_content)):
         run_main_expecting_code(0, mock_sys_exit)

def test_promotion_hash_mismatch(mock_subprocess, mock_sys_exit, mock_verify_ledger, monkeypatch, mock_path_exists):
    promo_id = "test-uuid-mismatch"
    
    def side_effect(cmd, **kwargs):
        cmd_str = " ".join(cmd)
        if "git diff" in cmd_str:
            return b"prompts/foo.md\n"
        if "git log" in cmd_str:
            return b"msg"
        if "git rev-parse" in cmd_str:
            return b"current_hash_actual\n"
        return b""
        
    mock_subprocess.side_effect = side_effect
    monkeypatch.setenv("ADK_PROMOTION_ID", promo_id)
    mock_path_exists.return_value = True
    
    promo_content = json.dumps({
        "id": promo_id,
        "target_commit_hash": "target_hash_expected" 
    })
    
    with patch("builtins.open", mock_open(read_data=promo_content)):
         run_main_expecting_code(4, mock_sys_exit)

def test_promotion_file_missing(mock_subprocess, mock_sys_exit, monkeypatch, mock_path_exists):
    promo_id = "missing-promo"
    
    def side_effect(cmd, **kwargs):
        if "git diff" in " ".join(cmd):
            return b"prompts/foo.md\n"
        return b""
        
    mock_subprocess.side_effect = side_effect
    monkeypatch.setenv("ADK_PROMOTION_ID", promo_id)
    
    # Path.exists returns False by default from fixture setup? 
    # Must ensure it returns False for this test
    mock_path_exists.return_value = False
    
    run_main_expecting_code(3, mock_sys_exit)

def test_ledger_lookup_for_hash(mock_subprocess, mock_sys_exit, mock_verify_ledger, monkeypatch, mock_path_exists):
    promo_id = "ledger-lookup-uuid"
    expected_hash = "hash_from_ledger"
    
    def side_effect(cmd, **kwargs):
        cmd_str = " ".join(cmd)
        if "git diff" in cmd_str:
             return b"schemas/foo.json\n"
        if "git rev-parse" in cmd_str:
             return f"{expected_hash}\n".encode()
        return b""
        
    mock_subprocess.side_effect = side_effect
    monkeypatch.setenv("ADK_PROMOTION_ID", promo_id)
    
    mock_path_exists.return_value = True
    
    promo_content = json.dumps({
        "id": promo_id
    })
    
    ledger_entry = json.dumps({
        "action": "PROMOTION_RECORDED",
        "target_artifact_id": promo_id,
        "decision_metadata": {
            "git_commit_hash": expected_hash
        }
    })
    other_entry = json.dumps({
        "action": "OTHER", 
        "target_artifact_id": "other"
    })
    
    def open_side_effect(file, mode='r', **kwargs):
        path_str = str(file)
        if "promotions" in path_str and promo_id in path_str:
             return mock_open(read_data=promo_content).return_value
        if "approval_ledger.jsonl" in path_str:
             return mock_open(read_data=f"{other_entry}\n{ledger_entry}\n").return_value
        return mock_open(read_data="").return_value

    with patch("builtins.open", side_effect=open_side_effect):
        run_main_expecting_code(0, mock_sys_exit)

def test_ledger_integrity_failure(mock_subprocess, mock_sys_exit, mock_verify_ledger, monkeypatch, mock_path_exists):
    def side_effect(cmd, **kwargs):
        cmd_str = " ".join(cmd)
        if "git diff" in cmd_str:
            return b"prompts/foo.md\n"
        if "git rev-parse" in cmd_str:
            return b"hash\n"
        return b""
    mock_subprocess.side_effect = side_effect
    
    monkeypatch.setenv("ADK_PROMOTION_ID", "p1")
    mock_path_exists.return_value = True
    mock_verify_ledger.side_effect = Exception("Integrity Error")
    
    promo_content = json.dumps({"id": "p1", "target_commit_hash": "hash"})
    
    with patch("builtins.open", mock_open(read_data=promo_content)):
         run_main_expecting_code(3, mock_sys_exit)

def test_skip_guard(mock_subprocess, mock_sys_exit, monkeypatch):
    monkeypatch.setenv("ADK_SKIP_PROMOTION_GUARD", "1")
    monkeypatch.delenv("CI", raising=False)
    
    run_main_expecting_code(0, mock_sys_exit)
    # Ensure subprocess was NOT called (changes not detected)
    mock_subprocess.assert_not_called()

def test_skip_guard_ignored_in_ci(mock_subprocess, mock_sys_exit, monkeypatch):
    monkeypatch.setenv("ADK_SKIP_PROMOTION_GUARD", "1")
    monkeypatch.setenv("CI", "true")
    
    mock_subprocess.return_value = b"" 
    
    run_main_expecting_code(0, mock_sys_exit)
    # Ensure check ran (subprocess called)
    mock_subprocess.assert_called()
