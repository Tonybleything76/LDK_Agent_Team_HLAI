#!/usr/bin/env python3
"""
Pilot Run Executor - Strict Production Configuration

Executes the pipeline in "Pilot Mode" with:
- Real Provider (OpenAI)
- Risk Gates Enabled
- Strict Governance Profile ("pilot")
- No Simulations
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
import shutil

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent

def fail(message: str):
    print(f"\n❌ PILOT ERROR: {message}")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Execute a Pilot Run with strict production configuration.")
    parser.add_argument(
        "--inputs-dir", 
        required=True,
        help="Directory containing business_brief.md and sme_notes.md"
    )
    parser.add_argument(
        "--provider",
        default="openai",
        choices=["openai", "claude_cli", "perplexity"],
        help="Real provider to use (default: openai)"
    )
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="Model to use (default: gpt-4o)"
    )
    
    args = parser.parse_args()

    # 1. Validate Environment
    if args.provider == "openai":
        if not os.environ.get("OPENAI_API_KEY"):
            fail("OPENAI_API_KEY environment variable is missing.")
    elif args.provider == "claude_cli":
        # Check for anthropic or other env vars if needed, but strict check is on OpenAI for now as primary
        pass
        
    print(f"🚀 Starting Pilot Run...")
    print(f"   Provider: {args.provider}")
    print(f"   Model: {args.model}")
    print(f"   Inputs: {args.inputs_dir}")

    # 2. Check Inputs
    inputs_path = Path(args.inputs_dir)
    if not inputs_path.exists():
        fail(f"Inputs directory not found: {inputs_path}")
    
    if not (inputs_path / "business_brief.md").exists():
        fail(f"Missing business_brief.md in {inputs_path}")
    if not (inputs_path / "sme_notes.md").exists():
        fail(f"Missing sme_notes.md in {inputs_path}")

    # 3. Construct Command
    # We call run_pipeline.py but inject strict config overrides via environment or args.
    # We use `run_pipeline.py` arguments for profile and inputs.
    # We rely on `run_pipeline.py` to respect overrides.
    
    # Wait, run_pipeline.py doesn't accept a generic JSON override arg easily via CLI without complex escaping.
    # However, we can use the `config_overrides` argument if we import and run it directly, 
    # OR we can rely on `governance_profile` logic.
    # But `run_pipeline.py` logic for profiles is deeply embedded? 
    # Actually, `orchestrator/root_agent.py` takes a `governance_profile` arg but doesn't auto-switch config based on it yet 
    # (except for the manifest logging).
    # The requirement says: "Risk gates currently fire due to simulated open questions."
    # And "Risk gates currently fire ... limit to real learning."
    # We need to ENABLE risk gates in config.
    
    # We will invoke run_pipeline.py as a subprocess to keep environment clean, 
    # but we need to pass overrides.
    # Since run_pipeline CLI doesn't support arbitrary config overrides, we might need to:
    # A) Create a temporary config file
    # B) Modify run_pipeline.py to accept overrides (No refactors allowed unless required)
    # C) Use a python script to import and run `run_pipeline` function directly.
    
    # Option C is best. It allows passing dicts.
    
    # We'll use this script as a wrapper that imports `run_pipeline`.
    # But first we need to add PROJECT_ROOT to sys.path
    sys.path.insert(0, str(PROJECT_ROOT))
    
    try:
        from scripts.run_pipeline import run_pipeline
    except ImportError:
        # Fallback if scripts is not a package
        sys.path.append(str(PROJECT_ROOT / "scripts"))
        from run_pipeline import run_pipeline

    # Constants for overrides
    PILOT_CONFIG_OVERRIDES = {
        "approval": {
            "risk_gate_escalation": {
                "enabled": True,  # FORCE ENABLE
                "open_questions_threshold": 8,
                "force_gate_on_qa_critical": True,
                "auto_override": False  # Strict mode!
            }
        }
    }

    # Set Environment Variables for the run
    os.environ["PROVIDER"] = args.provider
    if args.provider == "openai":
         os.environ["OPENAI_MODEL"] = args.model
    
    # Enforce NO simulation
    if "CI_SIMULATE_MANUAL_RISK_APPROVAL" in os.environ:
        del os.environ["CI_SIMULATE_MANUAL_RISK_APPROVAL"]

    try:
        run_pipeline(
            inputs_dir=str(inputs_path),
            governance_profile="pilot",
            config_overrides=PILOT_CONFIG_OVERRIDES,
            # We don't want auto-approve for pilot, usually? 
            # Or do we? "Governance behaving correctly" implies manual checks?
            # "No simulated governance noise."
            # "Pilot run = ... governance on"
            # So we do NOT pass auto_approve=True unless specifically requested for a non-interactive pilot?
            # Usually Pilot runs are interactive or heavily monitored.
            # But specific Requirement: "fail fast... provider routing explicit"
            # Let's assume interactive by default or just let run_pipeline defaults handle it (which is interactive).
        )
        print("\n✅ Pilot Run Completed Successfully.")
        
    except Exception as e:
        fail(f"Pipeline Execution Failed: {e}")

if __name__ == "__main__":
    main()
