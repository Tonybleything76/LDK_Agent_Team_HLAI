#!/usr/bin/env python3
"""
Resume a previous orchestrator run from a checkpoint.

Usage:
    python3 scripts/resume_run.py --run_id <run_id>
    python3 scripts/resume_run.py --run_id <run_id> --from_step 4
    python3 scripts/resume_run.py --run_id <run_id> --force
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from orchestrator.run_artifacts import (
    read_manifest,
    read_checkpoint,
    read_latest_checkpoint,
    compute_config_hash,
    compute_inputs_hash,
)
from orchestrator.root_agent import run_pipeline


def main():
    parser = argparse.ArgumentParser(
        description="Resume a previous orchestrator run from a checkpoint",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Resume from next step after last completed
  python3 scripts/resume_run.py --run_id 20260130_155254

  # Resume from specific step
  python3 scripts/resume_run.py --run_id 20260130_155254 --from_step 4

  # Force resume despite config/input changes
  python3 scripts/resume_run.py --run_id 20260130_155254 --force
        """
    )
    
    parser.add_argument(
        "--run_id",
        required=True,
        help="Run ID to resume (e.g., 20260130_155254)"
    )
    
    parser.add_argument(
        "--from_step",
        type=int,
        help="Step number to resume from (default: next step after last completed)"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force resume even if config/inputs have changed"
    )
    
    args = parser.parse_args()
    
    # ----------------------------------------------------------------------
    # Validate Run Directory
    # ----------------------------------------------------------------------
    
    run_dir = PROJECT_ROOT / "outputs" / args.run_id
    
    if not run_dir.exists():
        print(f"❌ Error: Run directory not found: {run_dir}")
        sys.exit(1)
    
    checkpoints_dir = run_dir / "checkpoints"
    
    if not checkpoints_dir.exists():
        print(f"❌ Error: No checkpoints directory found in run: {run_dir}")
        print("This run may not support resuming (created before v0.2.1)")
        sys.exit(1)
    
    # ----------------------------------------------------------------------
    # Load Manifest
    # ----------------------------------------------------------------------
    
    try:
        manifest = read_manifest(run_dir)
    except FileNotFoundError:
        print(f"❌ Error: No run manifest found in: {run_dir}")
        print("This run may not support resuming (created before v0.2.1)")
        sys.exit(1)
    
    print(f"\n📋 Run Manifest:")
    print(f"   Run ID: {manifest['run_id']}")
    print(f"   Started: {manifest['started_at_utc']}")
    print(f"   Status: {manifest['status']}")
    print(f"   Last Completed Step: {manifest['current_step_completed']}")
    
    # ----------------------------------------------------------------------
    # Validate Config/Inputs Hashes (unless --force)
    # ----------------------------------------------------------------------
    
    if not args.force:
        config_path = PROJECT_ROOT / "config" / "run_config.json"
        business_brief_path = PROJECT_ROOT / "inputs" / "business_brief.md"
        sme_notes_path = PROJECT_ROOT / "inputs" / "sme_notes.md"
        
        current_config_hash = compute_config_hash(config_path)
        current_inputs_hash = compute_inputs_hash(business_brief_path, sme_notes_path)
        
        config_changed = current_config_hash != manifest["config_hash"]
        inputs_changed = current_inputs_hash != manifest["inputs_hash"]
        
        if config_changed or inputs_changed:
            print(f"\n⚠️  WARNING: Files have changed since this run started!")
            
            if config_changed:
                print(f"   - config/run_config.json has been modified")
                print(f"     Original hash: {manifest['config_hash'][:16]}...")
                print(f"     Current hash:  {current_config_hash[:16]}...")
            
            if inputs_changed:
                print(f"   - Input files (business_brief.md or sme_notes.md) have been modified")
                print(f"     Original hash: {manifest['inputs_hash'][:16]}...")
                print(f"     Current hash:  {current_inputs_hash[:16]}...")
            
            print(f"\n   Resuming with changed files may produce inconsistent results.")
            print(f"   Use --force to proceed anyway, or restore the original files.")
            sys.exit(1)
    
    # ----------------------------------------------------------------------
    # Determine Resume Step
    # ----------------------------------------------------------------------
    
    if args.from_step is not None:
        resume_step = args.from_step
        print(f"\n🔄 Resuming from user-specified step: {resume_step}")
    else:
        resume_step = manifest["current_step_completed"] + 1
        print(f"\n🔄 Resuming from next step after last completed: {resume_step}")
    
    # ----------------------------------------------------------------------
    # Load Checkpoint State
    # ----------------------------------------------------------------------
    
    # Load the checkpoint from the step BEFORE resume_step
    checkpoint_step = resume_step - 1
    
    if checkpoint_step == 0:
        # Starting from step 1, no checkpoint needed
        print(f"   No checkpoint needed (starting from step 1)")
        initial_state = None
    else:
        try:
            initial_state = read_checkpoint(checkpoints_dir, checkpoint_step)
            print(f"   Loaded state from checkpoint: step_{checkpoint_step:02d}_state.json")
        except FileNotFoundError:
            print(f"❌ Error: Checkpoint not found for step {checkpoint_step}")
            print(f"   Available checkpoints:")
            
            checkpoint_files = sorted(checkpoints_dir.glob("step_*_state.json"))
            if checkpoint_files:
                for cp in checkpoint_files:
                    print(f"     - {cp.name}")
            else:
                print(f"     (none)")
            
            sys.exit(1)
    
    # ----------------------------------------------------------------------
    # Resume Pipeline
    # ----------------------------------------------------------------------
    
    print(f"\n🚀 Starting resume...\n")
    
    run_pipeline(
        config_path=str(PROJECT_ROOT / "config" / "run_config.json"),
        run_dir=str(run_dir),
        start_step=resume_step,
        initial_state=initial_state,
    )


if __name__ == "__main__":
    main()
