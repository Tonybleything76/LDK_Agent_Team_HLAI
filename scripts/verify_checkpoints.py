#!/usr/bin/env python3
"""
Verify checkpoint structure for the most recent run.

This is a dry verification script that does NOT make any API calls.
It simply checks that the checkpoint and manifest structure is correct.
"""

import sys
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def find_most_recent_run():
    """Find the most recent run directory."""
    outputs_dir = PROJECT_ROOT / "outputs"
    
    if not outputs_dir.exists():
        return None
    
    # Find all run directories (format: YYYYMMDD_HHMMSS)
    run_dirs = [d for d in outputs_dir.iterdir() if d.is_dir() and len(d.name) == 15]
    
    if not run_dirs:
        return None
    
    # Sort by name (which is timestamp-based)
    run_dirs.sort(reverse=True)
    
    return run_dirs[0]


def verify_checkpoints(run_dir: Path) -> bool:
    """
    Verify checkpoint structure for a run.
    
    Returns:
        True if structure is valid, False otherwise
    """
    print(f"\n🔍 Verifying Run: {run_dir.name}")
    print(f"   Path: {run_dir}")
    
    errors = []
    
    # ----------------------------------------------------------------------
    # Check Manifest
    # ----------------------------------------------------------------------
    
    manifest_path = run_dir / "run_manifest.json"
    
    if not manifest_path.exists():
        errors.append("❌ Missing run_manifest.json")
        manifest = None
    else:
        try:
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
            
            print(f"\n✅ Manifest Found:")
            
            # Check required keys
            required_keys = [
                "run_id",
                "started_at_utc",
                "config_hash",
                "inputs_hash",
                "current_step_completed",
                "providers_used_by_step",
                "status"
            ]
            
            for key in required_keys:
                if key not in manifest:
                    errors.append(f"❌ Manifest missing required key: {key}")
                else:
                    value = manifest[key]
                    if key == "providers_used_by_step":
                        print(f"   {key}: {len(value)} steps tracked")
                    elif key in ["config_hash", "inputs_hash"]:
                        print(f"   {key}: {value[:16]}...")
                    else:
                        print(f"   {key}: {value}")
        
        except json.JSONDecodeError as e:
            errors.append(f"❌ Invalid JSON in manifest: {e}")
            manifest = None
    
    # ----------------------------------------------------------------------
    # Check Checkpoints Directory
    # ----------------------------------------------------------------------
    
    checkpoints_dir = run_dir / "checkpoints"
    
    if not checkpoints_dir.exists():
        errors.append("❌ Missing checkpoints directory")
    else:
        checkpoint_files = sorted(checkpoints_dir.glob("step_*_state.json"))
        
        print(f"\n✅ Checkpoints Directory Found:")
        print(f"   {len(checkpoint_files)} checkpoint(s) found")
        
        if checkpoint_files:
            print(f"\n   Checkpoint Files:")
            for cp in checkpoint_files:
                # Extract step number
                step_num = int(cp.stem.split("_")[1])
                
                # Check if it's valid JSON
                try:
                    with open(cp, "r") as f:
                        state = json.load(f)
                    print(f"     ✓ {cp.name} ({len(json.dumps(state))} bytes)")
                except json.JSONDecodeError:
                    errors.append(f"❌ Invalid JSON in checkpoint: {cp.name}")
                    print(f"     ✗ {cp.name} (INVALID JSON)")
        
        # Verify checkpoint consistency with manifest
        if manifest and checkpoint_files:
            last_checkpoint_step = int(checkpoint_files[-1].stem.split("_")[1])
            manifest_step = manifest.get("current_step_completed", 0)
            
            if last_checkpoint_step != manifest_step:
                errors.append(
                    f"❌ Mismatch: Last checkpoint is step {last_checkpoint_step}, "
                    f"but manifest says {manifest_step}"
                )
    
    # ----------------------------------------------------------------------
    # Summary
    # ----------------------------------------------------------------------
    
    print(f"\n{'='*60}")
    
    if errors:
        print(f"\n❌ VERIFICATION FAILED ({len(errors)} error(s)):\n")
        for error in errors:
            print(f"   {error}")
        return False
    else:
        print(f"\n✅ VERIFICATION PASSED")
        print(f"   All required files and structure are present and valid.")
        return True


def main():
    print("="*60)
    print("Checkpoint Structure Verification (Dry Run - No API Calls)")
    print("="*60)
    
    run_dir = find_most_recent_run()
    
    if run_dir is None:
        print("\n❌ No run directories found in outputs/")
        print("   Run the orchestrator first to create a run.")
        sys.exit(1)
    
    success = verify_checkpoints(run_dir)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
