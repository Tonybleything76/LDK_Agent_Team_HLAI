import json
import os
import pytest
from jsonschema import validate, ValidationError

SCHEMA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../schemas"))

def load_schema(name):
    with open(os.path.join(SCHEMA_DIR, name), "r") as f:
        return json.load(f)

def test_improvement_signal_schema():
    schema = load_schema("improvement_signal.schema.json")
    valid_data = {
        "governance_id": "550e8400-e29b-41d4-a716-446655440000",
        "schema_version": "1.0.0",
        "created_at_utc": "2023-10-27T10:00:00Z",
        "source": {
            "type": "pilot_feedback",
            "origin_id": "user_123"
        },
        "signal_type": "complaint",
        "content": {
            "summary": "It broke",
            "details": "The thing broke when I clicked it."
        },
        "tenant_context":{
             "tenant_id": "tenant_1",
             "course_id": "course_A"
        },
        "pii_scrubbed": True
    }
    validate(instance=valid_data, schema=schema)

    with pytest.raises(ValidationError):
        invalid = valid_data.copy()
        invalid["pii_scrubbed"] = False
        validate(instance=invalid, schema=schema)

def test_improvement_proposal_schema():
    schema = load_schema("improvement_proposal.schema.json")
    valid_data = {
        "governance_id": "550e8400-e29b-41d4-a716-446655440000",
        "schema_version": "1.0.0",
        "created_at_utc": "2023-10-27T10:00:00Z",
        "author_id": "agent_architect",
        "linked_signal_ids": ["550e8400-e29b-41d4-a716-446655440000"],
        "target_component": {
            "path": "agents.librarian",
            "version_constraint": "v1.0"
        },
        "change_intent": {
            "rationale": "Fix bug",
            "proposed_modification": "Change line 10"
        },
        "risk_level": "LOW",
        "governance_state": "DRAFT"
    }
    validate(instance=valid_data, schema=schema)

def test_validation_evidence_schema():
    schema = load_schema("validation_evidence.schema.json")
    valid_data = {
        "governance_id": "550e8400-e29b-41d4-a716-446655440000",
        "schema_version": "1.0.0",
        "created_at_utc": "2023-10-27T10:00:00Z",
        "proposal_id": "550e8400-e29b-41d4-a716-446655440000",
        "validator_context": {
            "runner_id": "ci_runner",
            "environment": "ci"
        },
        "validation_outcome": "PASS",
        "evidence_artifacts": {
            "run_id": "run_123",
            "summary": "All passed"
        }
    }
    validate(instance=valid_data, schema=schema)

def test_promotion_record_schema():
    schema = load_schema("promotion_record.schema.json")
    valid_data = {
        "governance_id": "550e8400-e29b-41d4-a716-446655440000",
        "schema_version": "1.0.0",
        "created_at_utc": "2023-10-27T10:00:00Z",
        "proposal_id": "550e8400-e29b-41d4-a716-446655440000",
        "evidence_id": "550e8400-e29b-41d4-a716-446655440000",
        "approval_authority": {
            "approver_id": "admin",
            "role": "admin",
            "signature": "sha256:signature"
        },
        "target_git_ref": "deadbeef",
        "promotion_status": "PROMOTED" # wait, did I add this? Check schema.
    }
    # I did not add promotion_status in my memory list but I should check the file I wrote.
    # Ah, I added it in the write_to_file call: "promotion_status": enum [PROMOTED, ROLLED_BACK]
    # But wait, looking at my write_to_file call for promotion_record...
    # "required": [..., "promotion_status"]? No, checking properties...
    # I need to be careful. I'll read the file to be sure.
    validate(instance=valid_data, schema=schema)

if __name__ == "__main__":
    # verification script to run manually if pytest not avail
    try:
        test_improvement_signal_schema()
        test_improvement_proposal_schema()
        test_validation_evidence_schema()
        test_promotion_record_schema()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"TEST FAILED: {e}")
        exit(1)
