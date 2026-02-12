import argparse
import uuid
import json
import os
import stat
from datetime import datetime, timezone
import sys

# Relative imports to avoid sys.path issues usually, but adk.py sets up path
from utils import schema_validator
from governance import approval_ledger

def register(subparsers):
    signal_parser = subparsers.add_parser('signal', help='Improvement Signal commands')
    signal_subparsers = signal_parser.add_subparsers(dest='signal_command', required=True)
    
    create_parser = signal_subparsers.add_parser('create', help='Create a new Improvement Signal')
    
    # Arguments mapping to schema fields
    create_parser.add_argument('--source-type', required=True, 
                              choices=['pilot_feedback', 'operator_observation', 'automated_scorer', 'system_error'],
                              help='Type of the source generating the signal')
    create_parser.add_argument('--origin-id', required=True, help='ID of the user, agent, or run')
    
    create_parser.add_argument('--signal-type', required=True,
                              choices=['complaint', 'observation', 'feature_request', 'bug_report'],
                              help='Classification of the signal')
                              
    create_parser.add_argument('--summary', required=True, help='Short summary (max 200 chars)')
    create_parser.add_argument('--details', required=True, help='Full details of the signal')
    create_parser.add_argument('--affected-artifacts', nargs='*', help='List of affected artifact IDs')
    
    create_parser.add_argument('--tenant-id', required=True, help='Tenant ID context')
    create_parser.add_argument('--course-id', help='Course ID context (optional)')
    
    create_parser.set_defaults(func=execute)

def execute(args):
    # 1. Generate Governance/Content ID
    governance_id = str(uuid.uuid4())
    
    # 2. Construct Payload
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    
    payload = {
        "governance_id": governance_id,
        "schema_version": "1.0.0",
        "created_at_utc": created_at,
        "source": {
            "type": args.source_type,
            "origin_id": args.origin_id
        },
        "signal_type": args.signal_type,
        "content": {
            "summary": args.summary,
            "details": args.details
        },
        "tenant_context": {
            "tenant_id": args.tenant_id
        },
        "pii_scrubbed": True
    }
    
    if args.affected_artifacts:
        payload["content"]["affected_artifacts"] = args.affected_artifacts
        
    if args.course_id:
        payload["tenant_context"]["course_id"] = args.course_id
        
    # 3. Validate Payload
    try:
        schema_validator.validate_instance(payload, 'improvement_signal.schema.json')
    except Exception as e:
        print(f"Schema Validation Error:\n{e}", file=sys.stderr)
        sys.exit(1)
        
    # 4. Deterministic Write to knowledge/signals/{governance_id}.json
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    signals_dir = os.path.join(project_root, 'knowledge', 'signals')
    os.makedirs(signals_dir, exist_ok=True)
    
    target_file = os.path.join(signals_dir, f"{governance_id}.json")
    
    if os.path.exists(target_file):
        print(f"Error: Signal file {target_file} already exists. Collision detected.", file=sys.stderr)
        sys.exit(1)
        
    with open(target_file, 'w') as f:
        json.dump(payload, f, indent=4)
        
    # 5. Enforce Append-Only / Read-Only
    os.chmod(target_file, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH) # 0444
    
    # 6. Append Ledger Entry
    try:
        ledger_entry = approval_ledger.append_entry(
            action="SIGNAL_CREATED",
            actor=args.origin_id, # Using origin_id as actor for signal creation
            target_artifact_id=governance_id,
            evidence_ref=target_file,
            decision_metadata={
                "signal_type": args.signal_type,
                "source_type": args.source_type
            }
        )
    except Exception as e:
        print(f"Ledger Error: {e}", file=sys.stderr)
        # Rollback (delete file) if ledger fails? 
        # Requirement says "Deterministic write to knowledge/signals", then "Append ledger".
        # If ledger fails, we have an orphan signal. For strict transaction, removal might be best.
        # But given strict append-only constraints, maybe we shouldn't delete. 
        # Proceeding with error report.
        sys.exit(1)

    print(f"Signal created successfully: {governance_id}")
    print(f"Ledger entry: {ledger_entry['ledger_seq']} ({ledger_entry['integrity_hash'][:8]}...)")
