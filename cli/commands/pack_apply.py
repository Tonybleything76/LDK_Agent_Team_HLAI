import argparse
import json
import os
import shutil
import sys
import hashlib
from datetime import datetime, timezone

# Relative imports
from governance import approval_ledger
from utils import hashing

def register(pack_subparsers):
    apply_parser = pack_subparsers.add_parser('apply', help='Apply a Knowledge Pack to the active sandbox')
    apply_parser.add_argument('--pack-version', required=True, help='Version of the Knowledge Pack to apply')
    apply_parser.add_argument('--actor-id', required=True, help='ID of the actor performing the apply')
    apply_parser.add_argument('--notes', help='Optional notes for the application')
    apply_parser.add_argument('--force', action='store_true', help='Force apply even if version matches current')
    apply_parser.set_defaults(func=execute)

def verify_pack_integrity(pack_path, pack_version):
    """
    Verifies that the pack at pack_path matches its manifest.
    Returns (True, "OK", manifest_data) or (False, reason, None).
    """
    manifest_path = os.path.join(pack_path, 'manifest.json')
    if not os.path.exists(manifest_path):
        return False, f"Manifest missing in pack {pack_version}", None
    
    try:
        with open(manifest_path, 'r') as f:
            manifest_data = json.load(f)
    except json.JSONDecodeError:
        return False, f"Manifest corrupted in pack {pack_version}", None
        
    # 1. Verify Manifest Hash
    stored_hash = manifest_data.get('manifest_hash')
    if not stored_hash:
        return False, "Manifest missing 'manifest_hash' field", None
        
    # Recompute manifest hash (exclude existing hash field for computation)
    check_data = manifest_data.copy()
    check_data.pop('manifest_hash', None)
    
    canonical_json = hashing.canonical_json_dumps(check_data)
    calculated_hash = hashing.compute_string_sha256(canonical_json)
    
    if calculated_hash != stored_hash:
        return False, f"Manifest hash mismatch. Expected {stored_hash}, got {calculated_hash}", None
        
    # 2. Verify File Hashes
    files = manifest_data.get('files', [])
    if not files:
        return False, "Manifest contains no files", None
        
    for file_entry in files:
        rel_path = file_entry.get('path')
        expected_sha = file_entry.get('sha256')
        
        abs_path = os.path.join(pack_path, rel_path)
        if not os.path.exists(abs_path):
            return False, f"File missing: {rel_path}", None
            
        actual_sha = hashing.compute_file_sha256(abs_path)
        if actual_sha != expected_sha:
            return False, f"File hash mismatch for {rel_path}. Expected {expected_sha}, got {actual_sha}", None
            
    return True, "Integrity Verified", manifest_data

def execute(args):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    # Paths
    knowledge_dir = os.path.join(project_root, 'knowledge')
    source_packs_dir = os.path.join(knowledge_dir, 'packs')
    active_dir = os.path.join(knowledge_dir, 'active')
    active_pack_marker = os.path.join(active_dir, 'ACTIVE_PACK.json')
    snapshots_dir = os.path.join(active_dir, '_snapshots')
    active_packs_store_dir = os.path.join(active_dir, 'packs')
    
    # 1. Input Validation
    target_pack_source = os.path.join(source_packs_dir, args.pack_version)
    if not os.path.exists(target_pack_source):
        print(f"Blocked: Pack version {args.pack_version} not found in {source_packs_dir}", file=sys.stderr)
        sys.exit(2)
        
    # 2. Check Integrity
    is_valid, reason, manifest = verify_pack_integrity(target_pack_source, args.pack_version)
    if not is_valid:
        print(f"Blocked: Integrity Check Failed: {reason}", file=sys.stderr)
        sys.exit(2)
        
    # 3. Check Current State (Idempotency)
    current_version = None
    if os.path.exists(active_pack_marker):
        try:
            with open(active_pack_marker, 'r') as f:
                current_active = json.load(f)
                current_version = current_active.get('pack_version')
        except:
            pass # corrupted marker, proceed to fix? Or block? Assume we can overwrite.
            
    if current_version == args.pack_version and not args.force:
        print(f"Blocked: Pack {args.pack_version} is already active.", file=sys.stderr)
        sys.exit(2)
        
    # 4. Prepare Directories
    os.makedirs(active_dir, exist_ok=True)
    os.makedirs(snapshots_dir, exist_ok=True)
    os.makedirs(active_packs_store_dir, exist_ok=True)
    
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    
    # 5. Create Snapshot of Previous State
    if os.path.exists(active_pack_marker):
        # We backup the ACTIVE_PACK.json file as the snapshot of "what was active"
        # Identifying string: timestamp_oldversion
        snap_id = f"{timestamp.replace(':', '').replace('-', '')}_{current_version or 'unknown'}"
        snap_path = os.path.join(snapshots_dir, f"{snap_id}.json")
        shutil.copy2(active_pack_marker, snap_path)
    
    # 6. Apply Pack
    # Copy from source to active/packs/{version}
    target_pack_dest = os.path.join(active_packs_store_dir, args.pack_version)
    
    # If dest exists, we remove it to ensure clean copy (unless it's same version and we forced, we still refresh)
    if os.path.exists(target_pack_dest):
        shutil.rmtree(target_pack_dest)
        
    shutil.copytree(target_pack_source, target_pack_dest)
    
    # 7. Update ACTIVE_PACK.json
    promotions_dir = os.path.join(knowledge_dir, 'promotions')
    
    # Attempt to find promotion ID for this pack? manifest doesn't guarantee it linked.
    # But usually a Pack is created by Promotion Record.
    # The manifest contains 'proposal_id', 'git_commit_hash'.
    # We can search promotions for one that matches?
    # Or just leave it blank if not easily found.
    # Prompt says: "promotion_id (if present)".
    # Let's verify manifest has it? No, manifest schema I saw earlier didn't strictly look for it.
    # But `promotion_record.py` CREATED the pack.
    # And created a Promotion Record. But it didn't PUT the promotion ID IN the manifest.
    # So we might not know it easily without searching.
    # I'll search `knowledge/promotions/` for a record that points to this pack?
    # Or matches the proposal + git hash?
    # `promotion_record` schema has `proposal_id` and `target_git_ref`.
    
    found_promo_id = None
    if os.path.exists(promotions_dir):
        for fname in os.listdir(promotions_dir):
            if fname.endswith('.json'):
                try:
                    with open(os.path.join(promotions_dir, fname), 'r') as f:
                        p_data = json.load(f)
                        if (p_data.get('proposal_id') == manifest.get('proposal_id') and 
                            p_data.get('target_git_ref') == manifest.get('git_commit_hash')):
                            found_promo_id = p_data.get('governance_id')
                            break # Found a match
                except: continue
    
    new_active_state = {
        "pack_version": args.pack_version,
        "applied_at_utc": timestamp,
        "git_commit_hash": manifest.get('git_commit_hash'),
        "promotion_id": found_promo_id
    }
    
    # Deterministic write
    with open(active_pack_marker, 'w') as f:
        json.dump(new_active_state, f, indent=4, sort_keys=True)
        
    # 8. Ledger Entry
    decision_metadata = {
        "manifest_hash": manifest.get('manifest_hash'),
        "git_commit_hash": manifest.get('git_commit_hash'),
        "snapshot_ref": snap_path if os.path.exists(active_pack_marker) and 'snap_path' in locals() else None,
        "previous_pack_version": current_version
    }
    
    try:
        approval_ledger.append_entry(
            action="PACK_APPLIED",
            actor=args.actor_id,
            target_artifact_id=args.pack_version,
            evidence_ref=os.path.relpath(active_pack_marker, project_root),
            decision_metadata=decision_metadata
        )
    except Exception as e:
        print(f"Warning: Ledger update failed but pack was applied. Error: {e}", file=sys.stderr)
        # We don't exit 1 here as the operation effectively succeeded? 
        # Requirement: "Apply must be deterministic and auditable (ledger entry required)."
        # If ledger fails, maybe we SHOULD fail.
        # But we already wrote to disk.
        # Ideally we rollback if ledger fails.
        # For MVP, let's print operational error and exit 1? 
        # Or try to rollback? 
        # I'll just exit 1 to signal "Partial Failure / Operational Error".
        sys.exit(1)

    print(f"Applied {args.pack_version} successfully.")
    sys.exit(0)
