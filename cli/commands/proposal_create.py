import argparse
import uuid
import json
import os
import stat
from datetime import datetime, timezone
import sys

from utils import schema_validator
from governance import approval_ledger


def register(subparsers):
    proposal_parser = subparsers.add_parser('proposal', help='Improvement Proposal commands')
    proposal_subparsers = proposal_parser.add_subparsers(dest='proposal_command', required=True)

    create_parser = proposal_subparsers.add_parser('create', help='Create a new Improvement Proposal')

    create_parser.add_argument('--signals', required=True, help='Comma-separated Signal governance IDs')
    create_parser.add_argument('--author-id', required=True, help='Author agent or human ID')
    create_parser.add_argument('--target-path', required=True, help='Fully qualified module path')
    create_parser.add_argument('--version-constraint', required=True, help='Semantic version range')
    create_parser.add_argument('--rationale', required=True, help='Rationale for the change')
    create_parser.add_argument('--proposed-modification', required=True, help='Diff or description')
    create_parser.add_argument('--risk', required=True, choices=['LOW', 'MEDIUM', 'HIGH'], help='Risk level')
    create_parser.add_argument('--parent-proposal-id', default=None, help='Parent proposal ID if updating')

    create_parser.set_defaults(func=execute)


def execute(args):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

    signal_ids = [s.strip() for s in args.signals.split(',')]

    # 1. Validate all signals exist and collect tenant context
    signals_dir = os.path.join(project_root, 'knowledge', 'signals')
    tenant_ids = set()
    for sig_id in signal_ids:
        sig_path = os.path.join(signals_dir, f"{sig_id}.json")
        if not os.path.exists(sig_path):
            print(f"Error: Signal {sig_id} not found at {sig_path}", file=sys.stderr)
            sys.exit(1)
        with open(sig_path, 'r') as f:
            sig_data = json.load(f)
        tenant_ids.add(sig_data.get('tenant_context', {}).get('tenant_id', ''))

    # 2. Enforce single-tenant constraint
    if len(tenant_ids) > 1:
        print("Error: Mixed tenant contexts detected across signals.", file=sys.stderr)
        sys.exit(1)

    tenant_id = tenant_ids.pop() if tenant_ids else ''

    # 3. Build proposal payload
    governance_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

    payload = {
        "governance_id": governance_id,
        "schema_version": "1.0.0",
        "created_at_utc": created_at,
        "author_id": args.author_id,
        "linked_signal_ids": signal_ids,
        "target_component": {
            "path": args.target_path,
            "version_constraint": args.version_constraint
        },
        "change_intent": {
            "rationale": args.rationale,
            "proposed_modification": args.proposed_modification
        },
        "risk_level": args.risk,
        "governance_state": "DRAFT"
    }

    if args.parent_proposal_id:
        payload["parent_proposal_id"] = args.parent_proposal_id

    # 4. Validate against schema
    try:
        schema_validator.validate_instance(payload, 'improvement_proposal.schema.json')
    except Exception as e:
        print(f"Schema Validation Error:\n{e}", file=sys.stderr)
        sys.exit(1)

    # 5. Write to knowledge/proposals/{governance_id}.json
    proposals_dir = os.path.join(project_root, 'knowledge', 'proposals')
    os.makedirs(proposals_dir, exist_ok=True)

    target_file = os.path.join(proposals_dir, f"{governance_id}.json")

    if os.path.exists(target_file):
        print(f"Error: Proposal file {target_file} already exists. Collision detected.", file=sys.stderr)
        sys.exit(1)

    with open(target_file, 'w') as f:
        json.dump(payload, f, indent=4)

    # 6. Enforce read-only
    os.chmod(target_file, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

    # 7. Append ledger entry
    try:
        ledger_entry = approval_ledger.append_entry(
            action="PROPOSAL_CREATED",
            actor=args.author_id,
            target_artifact_id=governance_id,
            evidence_ref=target_file,
            decision_metadata={
                "risk_level": args.risk,
                "linked_signal_count": len(signal_ids),
                "tenant_id_context": tenant_id
            }
        )
    except Exception as e:
        print(f"Ledger Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Proposal created successfully: {governance_id}")
    print(f"Ledger entry: {ledger_entry['ledger_seq']} ({ledger_entry['integrity_hash'][:8]}...)")
