import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone

# Relative imports
from governance import approval_ledger
from cli.commands import pack_apply

def register(pack_subparsers):
    rollback_parser = pack_subparsers.add_parser('rollback', help='Rollback active sandbox to a previous snapshot')
    rollback_parser.add_argument('--to-snapshot', required=True, help='Snapshot ID or filename in knowledge/active/_snapshots/')
    rollback_parser.add_argument('--actor-id', required=True, help='ID of the actor performing the rollback')
    rollback_parser.add_argument('--notes', help='Optional notes for the rollback')
    rollback_parser.set_defaults(func=execute)

def execute(args):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    # Paths
    knowledge_dir = os.path.join(project_root, 'knowledge')
    active_dir = os.path.join(knowledge_dir, 'active')
    active_pack_marker = os.path.join(active_dir, 'ACTIVE_PACK.json')
    snapshots_dir = os.path.join(active_dir, '_snapshots')
    active_packs_store_dir = os.path.join(active_dir, 'packs')
    source_packs_dir = os.path.join(knowledge_dir, 'packs')
    
    # 1. Validate Snapshot
    snapshot_arg = args.to_snapshot
    if not snapshot_arg.endswith('.json'):
        snapshot_arg += '.json'
        
    snapshot_path = os.path.join(snapshots_dir, snapshot_arg)
    
    if not os.path.exists(snapshot_path):
        print(f"Blocked: Snapshot {snapshot_path} not found.", file=sys.stderr)
        sys.exit(2)
        
    try:
        with open(snapshot_path, 'r') as f:
            snapshot_data = json.load(f)
    except json.JSONDecodeError:
        print(f"Blocked: Snapshot {snapshot_path} is corrupted / invalid JSON.", file=sys.stderr)
        sys.exit(2)
        
    target_pack_version = snapshot_data.get('pack_version')
    if not target_pack_version:
        print(f"Blocked: Snapshot missing 'pack_version' field.", file=sys.stderr)
        sys.exit(2)

    # 2. Check Current State
    if not os.path.exists(active_pack_marker):
        print("Blocked: No active pack marker found. Cannot rollback from undefined state.", file=sys.stderr)
        sys.exit(2)
        
    try:
        with open(active_pack_marker, 'r') as f:
            current_active = json.load(f)
            current_version = current_active.get('pack_version')
    except:
        current_version = "unknown"

    # 3. Restore Pack Directory
    # Ensure knowledge/active/packs/{target_pack_version} exists
    target_active_pack_dir = os.path.join(active_packs_store_dir, target_pack_version)
    
    if not os.path.exists(target_active_pack_dir):
        # Attempt restore from source
        source_pack_path = os.path.join(source_packs_dir, target_pack_version)
        if not os.path.exists(source_pack_path):
            print(f"Blocked: Target pack {target_pack_version} not found in source store or active store.", file=sys.stderr)
            sys.exit(2)
            
        # Verify Integrity before restore
        is_valid, reason, manifest = pack_apply.verify_pack_integrity(source_pack_path, target_pack_version)
        if not is_valid:
            print(f"Blocked: Integrity Check Failed for source pack {target_pack_version}: {reason}", file=sys.stderr)
            sys.exit(2)
            
        # Restore
        try:
            shutil.copytree(source_pack_path, target_active_pack_dir)
        except Exception as e:
            print(f"Operational Error: Failed to restore pack directory: {e}", file=sys.stderr)
            sys.exit(1)
            
    # 4. Restore ACTIVE_PACK.json
    # Deterministic write using snapshot content
    try:
        with open(active_pack_marker, 'w') as f:
            json.dump(snapshot_data, f, indent=4, sort_keys=True)
    except Exception as e:
         print(f"Operational Error: Failed to write ACTIVE_PACK.json: {e}", file=sys.stderr)
         sys.exit(1)

    # 5. Ledger Entry
    decision_metadata = {
        "snapshot_ref": os.path.relpath(snapshot_path, project_root),
        "previous_pack_version": current_version,
        "restored_pack_version": target_pack_version,
        "restored_git_commit_hash": snapshot_data.get('git_commit_hash'),
        "manifest_hash": None # We didn't necessarily re-read manifest unless we restored. 
        # Requirement: "manifest_hash (if pack dir restore performed)"
    }
    
    # If we did a verify/restore, we have `manifest` variable from scope?
    # No, scope is inside block. Let's fix that if we want it.
    # Actually, we only have it if we entered the block.
    # Simple fix: we can't easily get it unless we re-read it.
    # The requirement says "if pack dir restore performed".
    # I'll just leave it null if we didn't restore.
    
    # Wait, if we restored, `manifest` variable is local to that block. 
    # Python variables leak scope if not functions, but `manifest` is defined inside `if`.
    # To be safe, let's init it to None.
    
    # Actually, let's verify if we need to report it.
    # "manifest_hash (if pack dir restore performed)"
    # I'll rely on it being None if not performed.
    
    # Oh, wait. If I defined `manifest` in the `if` block, and verify pass, I can access it.
    # But if execution didn't go in `if`, it's unbound.
    # Let's check `if 'manifest' in locals():`
    
    if 'manifest' in locals() and manifest:
         decision_metadata['manifest_hash'] = manifest.get('manifest_hash')

    try:
        approval_ledger.append_entry(
            action="PACK_ROLLED_BACK",
            actor=args.actor_id,
            target_artifact_id=target_pack_version,
            evidence_ref=os.path.relpath(active_pack_marker, project_root),
            decision_metadata=decision_metadata
        )
    except Exception as e:
        print(f"Warning: Ledger update failed but rollback performed. Error: {e}", file=sys.stderr)
        # Requirement: "If ledger write fails, rollback MUST NOT complete"
        # BUT we already wrote ACTIVE_PACK.json!
        # This breaks strict constraint 2): "If ledger write fails, rollback MUST NOT complete (and must leave system consistent)."
        
        # FIX: We must revert ACTIVE_PACK.json if ledger fails!
        # We know `current_active` was the previous state.
        # We should write it back.
        
        print("Initiating compensatory rollback of ACTIVE_PACK.json due to ledger failure...", file=sys.stderr)
        try:
             with open(active_pack_marker, 'w') as f:
                 # We need to write back `current_active`.
                 # Use json dump.
                 json.dump(current_active, f, indent=4, sort_keys=True)
             print("System state restored to pre-rollback state.", file=sys.stderr)
        except Exception as revert_e:
             print(f"CRITICAL: Failed to revert ACTIVE_PACK.json: {revert_e}. System in inconsistent state.", file=sys.stderr)
        
        sys.exit(1)

    print(f"Rolled back to snapshot {snapshot_arg} (version {target_pack_version})")
    sys.exit(0)
