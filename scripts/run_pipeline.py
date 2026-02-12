#!/usr/bin/env python3
"""
One-Command Pipeline Runner - Run the orchestrator with guardrails and validation.

This script provides a user-friendly interface to run the orchestrator with:
- Input validation (ensures inputs are not empty)
- Run plan display (shows what will execute)
- Cost guardrails (prevents accidental API calls)
- Dry run mode (tests without API calls)
- Multiple provider modes (manual, openai, claude_cli, dry_run)
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from orchestrator.root_agent import run_pipeline, write_ledger, utc_now
from scripts.preflight_check import run_preflight_checks
from utils.worktree_guard import enforce_preflight, enforce_postflight

CONFIG_PATH = PROJECT_ROOT / "config" / "run_config.json"
INPUTS_DIR = PROJECT_ROOT / "inputs"
BUSINESS_BRIEF_PATH = INPUTS_DIR / "business_brief.md"
SME_NOTES_PATH = INPUTS_DIR / "sme_notes.md"

MIN_INPUT_CHARS = 50  # Minimum chars to consider input "non-empty"


def validate_inputs() -> bool:
    """
    Validate that input files exist and are non-empty.
    
    Returns:
        True if inputs are valid, False otherwise
    """
    errors = []
    
    if not BUSINESS_BRIEF_PATH.exists():
        errors.append(f"❌ Missing: {BUSINESS_BRIEF_PATH}")
    elif BUSINESS_BRIEF_PATH.stat().st_size <= MIN_INPUT_CHARS:
        errors.append(f"❌ Empty or too short: {BUSINESS_BRIEF_PATH} ({BUSINESS_BRIEF_PATH.stat().st_size} bytes)")
    
    if not SME_NOTES_PATH.exists():
        errors.append(f"❌ Missing: {SME_NOTES_PATH}")
    elif SME_NOTES_PATH.stat().st_size <= MIN_INPUT_CHARS:
        errors.append(f"❌ Empty or too short: {SME_NOTES_PATH} ({SME_NOTES_PATH.stat().st_size} bytes)")
    
    if errors:
        print("\n⚠️  INPUT VALIDATION FAILED\n")
        for error in errors:
            print(f"   {error}")
        print(f"\n💡 Tip: Run this command to create template inputs:")
        print(f"   python3 scripts/seed_inputs.py\n")
        return False
    
    return True


def load_and_validate_config() -> dict:
    """
    Load and validate run configuration.
    
    Returns:
        Config dict
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Missing config file: {CONFIG_PATH}\n"
            f"Create it before running."
        )
    
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
    
    # Validate required fields
    if "agents" not in config:
        raise ValueError("Config missing required 'agents' field")
    
    if not isinstance(config["agents"], list) or len(config["agents"]) == 0:
        raise ValueError("Config 'agents' must be a non-empty list")
    
    return config


def print_run_plan(config: dict, provider_override: str = None):
    """
    Print a clear run plan showing what will execute.
    
    Args:
        config: Run configuration
        provider_override: Provider override (from --mode or --dry_run)
    """
    print("\n" + "=" * 60)
    print("RUN PLAN")
    print("=" * 60)
    
    # Provider configuration
    default_provider = provider_override or config.get("provider") or os.getenv("PROVIDER") or "manual"
    print(f"\n📡 Provider Configuration:")
    print(f"   Default: {default_provider}")
    if provider_override:
        print(f"   Override: {provider_override} (forced)")
    
    # Agent list with per-agent provider overrides
    print(f"\n🤖 Agents ({len(config['agents'])} steps):")
    for idx, agent in enumerate(config["agents"], start=1):
        agent_name = agent["name"]
        agent_provider = provider_override or agent.get("provider") or default_provider
        
        # Show override indicator
        override_indicator = ""
        if provider_override:
            override_indicator = " [FORCED]"
        elif agent.get("provider") and agent.get("provider") != default_provider:
            override_indicator = " [override]"
        
        print(f"   {idx:2d}. {agent_name:35s} → {agent_provider}{override_indicator}")
    
    # Gate configuration
    approval_cfg = config.get("approval", {})
    gate_strategy = approval_cfg.get("gate_strategy", "per_phase")
    
    print(f"\n🚧 Approval Gates:")
    print(f"   Strategy: {gate_strategy}")
    
    if gate_strategy == "per_phase":
        phase_gates = approval_cfg.get("phase_gates", [3, 6, 9])
        print(f"   Gate Points: {phase_gates}")
        print(f"   → Pipeline will halt at steps: {', '.join(map(str, phase_gates))}")
    elif gate_strategy == "per_agent":
        gated_agents = [
            f"{idx}:{agent['name']}" 
            for idx, agent in enumerate(config["agents"], start=1) 
            if agent.get("gate", False)
        ]
        if gated_agents:
            print(f"   Gated Agents: {', '.join(gated_agents)}")
        else:
            print(f"   No agents have gates enabled")
    
    # Validation configuration
    validation_cfg = config.get("validation", {})
    min_chars = validation_cfg.get("min_deliverable_chars", 300)
    placeholder_markers = validation_cfg.get("placeholder_markers", [])
    
    print(f"\n✅ Validation Thresholds:")
    print(f"   Min deliverable chars: {min_chars}")
    print(f"   Placeholder markers: {len(placeholder_markers)} configured")
    
    print("\n" + "=" * 60)


def cost_guardrail_check(num_steps: int, provider: str, skip_confirmation: bool) -> bool:
    """
    Check with user before making API calls (unless --yes flag is set).
    
    Args:
        num_steps: Number of steps that will make API calls
        provider: Provider name
        skip_confirmation: If True, skip the confirmation prompt
        
    Returns:
        True if user approves or skip_confirmation is True, False otherwise
    """
    # API providers that incur costs
    api_providers = ["openai", "openai_api", "perplexity", "claude_cli"]
    
    if provider not in api_providers:
        # No cost for manual or dry_run
        return True
    
    if skip_confirmation:
        print(f"\n⚡ Skipping cost guardrail (--yes flag set)")
        return True
    
    print(f"\n" + "=" * 60)
    print(f"💰 COST GUARDRAIL")
    print(f"=" * 60)
    print(f"\nThis run will make API calls for up to {num_steps} steps using provider: {provider}")
    print(f"This may incur API costs.\n")
    
    user_input = input("Type RUN to continue, anything else to abort: ").strip()
    
    if user_input.upper() != "RUN":
        print(f"\n⛔ Run aborted by user (cost guardrail)")
        
        # Log the abort
        write_ledger({
            "timestamp_utc": utc_now(),
            "event": "run_failed",
            "reason": "cost_guardrail_rejected",
            "provider": provider,
            "num_steps": num_steps,
        })
        
        return False
    
    print(f"\n✅ Cost guardrail passed - proceeding with run\n")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Run the orchestrator pipeline with guardrails and validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (no API calls, tests full pipeline)
  python3 scripts/run_pipeline.py --dry_run
  
  # Run with OpenAI (with cost confirmation)
  python3 scripts/run_pipeline.py --mode openai
  
  # Run with OpenAI (skip cost confirmation)
  python3 scripts/run_pipeline.py --mode openai --yes
  
  # Run with manual provider (copy/paste)
  python3 scripts/run_pipeline.py --mode manual
  
  # Run with Claude CLI
  python3 scripts/run_pipeline.py --mode claude_cli

Modes:
  manual      - Manual copy/paste mode (no API calls)
  openai      - OpenAI API (requires OPENAI_API_KEY)
  claude_cli  - Claude CLI (requires 'claude' command)
  perplexity  - Perplexity API (requires PERPLEXITY_API_KEY)
  dry_run     - Dry run mode (no API calls, returns stubs)

The --dry_run flag is a shortcut for --mode dry_run.
        """
    )
    
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Run in dry mode (no API calls, returns stubs)"
    )
    
    parser.add_argument(
        "--mode",
        choices=["manual", "openai", "claude_cli", "perplexity"],
        help="Provider mode to use"
    )
    
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip cost confirmation prompt (auto-approve costs only)"
    )
    
    parser.add_argument(
        "--auto_approve",
        action="store_true",
        help="Auto-approve all gates (approvals logged but skipped)"
    )

    parser.add_argument(
        "--skip_preflight",
        action="store_true",
        help="Skip preflight checks (use with caution)"
    )

    parser.add_argument(
        "--governance_profile",
        choices=["dev", "staging", "prod", "ci"],
        help="Governance profile (overrides config defaults: dev=relaxed, prod=strict, ci=strict+non-interactive)"
    )

    parser.add_argument(
        "--allow-dirty-worktree",
        action="store_true",
        help="Allow running with dirty worktree (dev profile only)"
    )

    parser.add_argument(
        "--max-step",
        type=int,
        help="Stop execution after completing this step number (inclusive)"
    )
    
    args = parser.parse_args()

    # Validate max-step
    if args.max_step is not None and args.max_step < 1:
        print("\n❌ Error: --max-step must be >= 1")
        sys.exit(1)
    
    # Determine provider
    if args.dry_run:
        provider = "dry_run"
    elif args.mode:
        provider = args.mode
    else:
        provider = None  # Will use config default
    
    print("=" * 60)
    print("ORCHESTRATOR PIPELINE RUNNER")
    print("=" * 60)

    # --------------------------------------------------------------------------
    # Governance Profile Logic
    # --------------------------------------------------------------------------
    
    # 1. Resolve Profile (CLI > Env Var)
    governance_profile = args.governance_profile or os.getenv("GOVERNANCE_PROFILE")
    
    # 2. Define Profiles (Additive overrides)
    GOVERNANCE_PROFILES = {
        "dev": {
            "auto_approve": True,
            "risk_gate_escalation": {
                "enabled": True,
                "open_questions_threshold": 3,
                "auto_override": True,
                "weighted_severities": ["CRITICAL", "BLOCKER", "MAJOR", "UNPREFIXED"]
            }
        },
        "staging": {
            "auto_approve": True,
            "risk_gate_escalation": {
                "enabled": True,
                "open_questions_threshold": 5,
                "auto_override": False,
                "weighted_severities": ["CRITICAL", "BLOCKER", "MAJOR"]
            }
        },
        "prod": {
            "auto_approve": False,
            "risk_gate_escalation": {
                "enabled": True,
                "open_questions_threshold": 8,
                "auto_override": False,
                "weighted_severities": ["CRITICAL", "BLOCKER"]
            }
        },
        "ci": {
            "auto_approve": True,
            "risk_gate_escalation": {
                "enabled": True,
                "open_questions_threshold": 8,
                "auto_override": False,
                "force_gate_on_qa_critical": True,
                "weighted_severities": ["CRITICAL", "BLOCKER"]
            }
        }
    }
    
    config_overrides = {}
    
    if governance_profile:
        if governance_profile not in GOVERNANCE_PROFILES:
            print(f"\n❌ Invalid governance profile: {governance_profile}")
            print(f"   Choices: {list(GOVERNANCE_PROFILES.keys())}")
            sys.exit(1)
            
        print(f"\n🛡️  GOVERNANCE PROFILE: {governance_profile.upper()}")
        profile_settings = GOVERNANCE_PROFILES[governance_profile]
        
        # Apply Auto-Approve from Profile
        # Note: CLI --auto_approve flag takes precedence if set, but profile sets the baseline
        auto_approve_from_profile = False
        if profile_settings.get("auto_approve"):
            if not args.auto_approve:
                # If profile says yes, enable it (unless explicitly disabled? we don't have --no-auto-approve yet)
                # We assume profile sets the floor.
                args.auto_approve = True
                auto_approve_from_profile = True
                print(f"   → Auto-Approve: ENABLED (by profile)")
        
        # Track auto-approval source for audit attribution
        if auto_approve_from_profile:
            os.environ["AUTO_APPROVE_SOURCE"] = "profile"
            os.environ["AUTO_APPROVE_PROFILE"] = governance_profile
        
        # Build Config Overrides
        overrides = {
            "approval": {
                "risk_gate_escalation": profile_settings.get("risk_gate_escalation", {})
            }
        }
        config_overrides = overrides
        
        # Show overrides
        print(f"   → Risk Gates: ENABLED")
        print(f"   → Threshold: {profile_settings['risk_gate_escalation']['open_questions_threshold']}")
        print(f"   → Auto-Override: {profile_settings['risk_gate_escalation']['auto_override']}")
        print()

    # Handle Auto-Approve Flag
    if args.auto_approve:
        os.environ["AUTO_APPROVE"] = "1"
        # Track source if not already set by profile
        if "AUTO_APPROVE_SOURCE" not in os.environ:
            os.environ["AUTO_APPROVE_SOURCE"] = "cli_flag"
        print("\n" + "!" * 60)
        print("⚠️  WARNING: AUTO-APPROVAL ENABLED")
        print("!" * 60)
        print("All approval gates will be automatically approved.")
        print("This action will be logged in the ledger.")
        print("!" * 60 + "\n")
    
    # Step 0: Preflight Checks
    if not args.skip_preflight:
        if not run_preflight_checks():
            sys.exit(1)
    else:
        print("\n⚠️  SKIPPING PREFLIGHT CHECKS (--skip_preflight set)\n")

    # Step 1: Validate inputs
    print("\n📋 Step 1: Validating inputs...")
    if not validate_inputs():
        sys.exit(1)
    print("   ✅ Inputs validated")
    
    # Step 2: Load and validate config
    print("\n⚙️  Step 2: Loading configuration...")
    try:
        config = load_and_validate_config()
        print(f"   ✅ Config loaded ({len(config['agents'])} agents)")
    except Exception as e:
        print(f"\n❌ Config validation failed: {e}\n")
        sys.exit(1)
    
    # Step 3: Print run plan
    print_run_plan(config, provider)
    
    # Step 4: Cost guardrail check
    num_steps = len(config["agents"])
    # Adjust num_steps for cost guardrail if max_step is set
    if args.max_step:
        num_steps = min(num_steps, args.max_step)
        print(f"\n⚡ Run limited to first {args.max_step} steps (--max-step)")

    effective_provider = provider or config.get("provider") or os.getenv("PROVIDER") or "manual"
    
    if not cost_guardrail_check(num_steps, effective_provider, args.yes):
        sys.exit(1)
    
    # Step 5: Set provider environment variable if needed
    if provider:
        os.environ["PROVIDER"] = provider
        print(f"🔧 Set PROVIDER={provider}\n")
    
    # Step 6: Run the pipeline
    print("=" * 60)
    print("STARTING PIPELINE EXECUTION")
    print("=" * 60)
    print()
    
    # Generate Run ID and Directory explicitly to support preflight checks
    run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_dir = PROJECT_ROOT / "outputs" / run_id

    # Define a ledger writer that injects timestamps
    def guarded_ledger_writer(event):
        if "timestamp_utc" not in event:
            event["timestamp_utc"] = utc_now()
        write_ledger(event)

    try:
        # Enforce Preflight Guard
        enforce_preflight(
            allow_dirty=args.allow_dirty_worktree,
            profile=governance_profile, # Pass actual profile (None if unset)
            ledger_writer=guarded_ledger_writer,
            run_id=run_id
        )
        
        run_pipeline(
            config_path=str(CONFIG_PATH),
            run_dir=str(run_dir),  # Pass explicit run_dir to use the same ID
            start_step=1,
            initial_state=None,
            config_overrides=config_overrides,
            governance_profile=governance_profile,
            max_step=args.max_step,
        )

        # Enforce Postflight Guard
        # Only run if pipeline completed successfully (did not raise exception)
        enforce_postflight(
            allow_dirty=args.allow_dirty_worktree,
            profile=governance_profile,
            ledger_writer=guarded_ledger_writer,
            run_id=run_id
        )
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user (Ctrl+C)")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
