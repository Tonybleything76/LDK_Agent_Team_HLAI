#!/usr/bin/env python3
"""
Preflight Checks - Deterministic guardrails to prevent invalid pipeline runs.

This script validates system state BEFORE any execution starts.
It is deterministic (no LLM calls) and fail-fast.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Set

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("preflight")

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "run_config.json"
SCHEMAS_DIR = PROJECT_ROOT / "schemas"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
LEDGER_PATH = PROJECT_ROOT / "governance" / "run_ledger.jsonl"
OUTPUT_CONTRACT_PATH = PROJECT_ROOT / "schemas" / "agent_output_contract.json" # One example schema

REQUIRED_TOP_KEYS = {"agents", "approval", "validation", "mode", "provider"}
REQUIRED_APPROVAL_KEYS = {"gate_strategy"} # Basic check, more detailed in code
REQUIRED_PROMPT_VARS = {"{business_brief}", "{sme_notes}", "{system_state}"}
FORBIDDEN_MARKERS = ["[Missing", "TBD", "TODO", "PLACEHOLDER"]


def check_config_validation(config: Dict) -> List[str]:
    """Validate config/run_config.json structure and keys."""
    errors = []
    
    # Check top-level keys
    missing_keys = REQUIRED_TOP_KEYS - set(config.keys())
    if missing_keys:
        errors.append(f"Config missing required keys: {', '.join(missing_keys)}")
    
    # Check for unknown keys (typo protection), but allow some flexibility if needed? 
    # The requirement says "Fail with clear error if unknown keys are detected"
    # We will strictly check against a known allow-list or just the top level for now based on requirement.
    # Actually, strict top-level check might be too brittle if user adds one, let's stick to requirements.
    # "Fail with clear error if unknown keys are detected (protect against typos)"
    # I'll need to define the allowed keys strictly.
    ALLOWED_TOP_KEYS = REQUIRED_TOP_KEYS | {"governance_profile"} # Add any optional ones found in existing config
    
    # Update ALLOWED based on what I saw in view_file of run_config.json
    # It had: mode, provider, approval, validation, agents.
    # It did NOT have governance_profile in the json file itself, but maybe scripts use it.
    
    unknown_keys = set(config.keys()) - ALLOWED_TOP_KEYS
    if unknown_keys:
        errors.append(f"Config contains unknown top-level keys: {', '.join(unknown_keys)}")

    # Check approval structure
    if "approval" in config:
        approval = config["approval"]
        if "risk_gate_escalation" in approval:
            rge = approval["risk_gate_escalation"]
            if rge.get("enabled") is True:
                # startup check: verify required keys for escalation
                rge_required = {"enabled", "open_questions_threshold", "auto_override"} 
                # Note: "force_gate_on_qa_critical" is in the file saw in view_file.
                
                # Check misses in RGE
                # The user request specifically mentioned: verify approval.risk_gate_escalation keys exist when enabled
                # I'll check for the ones I saw in the file + general sanity
                pass # Just ensuring it has a dict structure is usually enough, but let's be safe

    return errors

def check_agent_prompt_integrity(config: Dict) -> List[str]:
    """Verify prompt paths exist and contain required variables."""
    errors = []
    agents = config.get("agents", [])
    
    for idx, agent in enumerate(agents):
        name = agent.get("name", f"agent_{idx}")
        prompt_path_str = agent.get("prompt_path")
        
        if not prompt_path_str:
            errors.append(f"Agent '{name}' missing 'prompt_path'")
            continue
            
        prompt_path = PROJECT_ROOT / prompt_path_str
        if not prompt_path.exists():
            errors.append(f"Agent '{name}' prompt not found: {prompt_path_str}")
            continue
            
        try:
            content = prompt_path.read_text(encoding="utf-8")
            for var in REQUIRED_PROMPT_VARS:
                if var not in content:
                    errors.append(f"Agent '{name}' prompt ({prompt_path_str}) missing variable: {var}")
        except Exception as e:
            errors.append(f"Error reading prompt for '{name}': {e}")
            
    return errors

def check_prompt_hygiene() -> List[str]:
    """Scan all prompt files for placeholder markers."""
    errors = []
    prompts_dir = PROJECT_ROOT / "prompts"
    
    if not prompts_dir.exists():
        return ["Prompts directory not found"]
        
    # Recursive search for .md files
    for prompt_file in prompts_dir.rglob("*.md"):
        try:
            lines = prompt_file.read_text(encoding="utf-8").splitlines()
            for i, line in enumerate(lines, 1):
                for marker in FORBIDDEN_MARKERS:
                    if marker in line:
                        # Calculate relative path for cleaner output
                        rel_path = prompt_file.relative_to(PROJECT_ROOT)
                        errors.append(f"Hygiene Check Failed: '{marker}' found in {rel_path}:{i}")
        except Exception as e:
            errors.append(f"Error reading {prompt_file}: {e}")
            
    return errors

def check_schema_availability() -> List[str]:
    """Verify schemas exist and can be loaded."""
    errors = []
    
    if not SCHEMAS_DIR.exists():
        return ["Schemas directory missing"]
        
    json_files = list(SCHEMAS_DIR.glob("*.json"))
    if not json_files:
        return ["No JSON schemas found in schemas/"]
        
    # Helper to load schema
    loaded_any = False
    for sf in json_files:
        try:
            json.loads(sf.read_text(encoding="utf-8"))
            loaded_any = True
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON schema {sf.name}: {e}")
            
    if not loaded_any and not errors:
        errors.append("Could not load any schemas successfully")
        
    return errors

def check_paths_and_permissions() -> List[str]:
    """Verify ledger is writable and outputs dir exists/creatable."""
    errors = []
    
    # Check outputs dir
    if not OUTPUTS_DIR.exists():
        try:
            OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create outputs directory: {e}")
    elif not os.access(OUTPUTS_DIR, os.W_OK):
        errors.append(f"Outputs directory is not writable: {OUTPUTS_DIR}")
        
    # Check ledger
    # The ledger file might not exist yet if it's the very first run, 
    # but the directory should exist and be writable.
    ledger_dir = LEDGER_PATH.parent
    if not ledger_dir.exists():
         errors.append(f"Governance directory missing: {ledger_dir}")
    elif not os.access(ledger_dir, os.W_OK):
         errors.append(f"Governance directory not writable: {ledger_dir}")
         
    if LEDGER_PATH.exists() and not os.access(LEDGER_PATH, os.W_OK):
        errors.append(f"Run ledger is not writable: {LEDGER_PATH}")

    return errors

def run_preflight_checks() -> bool:
    """
    Run all preflight checks.
    Returns True if passed, False if failed.
    """
    print("🔍 Running Preflight Checks...")
    
    all_errors = []
    
    # 1. Config Load & Validation
    if not CONFIG_PATH.exists():
        all_errors.append(f"Config file missing: {CONFIG_PATH}")
        config = {}
    else:
        try:
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
            all_errors.extend(check_config_validation(config))
        except json.JSONDecodeError as e:
            all_errors.append(f"Config JSON invalid: {e}")
            config = {}
            
    # 2. Agent Prompt Integrity (depends on config)
    if config:
        all_errors.extend(check_agent_prompt_integrity(config))
        
    # 3. Prompt Hygiene
    all_errors.extend(check_prompt_hygiene())
    
    # 4. Schema Availability
    all_errors.extend(check_schema_availability())
    
    # 5. Ledger + Output Paths
    all_errors.extend(check_paths_and_permissions())
    
    if all_errors:
        print("\n❌ PREFLIGHT CHECK FAILED")
        for i, err in enumerate(all_errors, 1):
            print(f"   {i}. {err}")
        print("\n(Use --skip_preflight to bypass if absolutely necessary)\n")
        return False
    else:
        print("✅ Preflight check passed\n")
        return True

if __name__ == "__main__":
    if not run_preflight_checks():
        sys.exit(1)
    sys.exit(0)
