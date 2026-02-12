# Phase 5 Implementation Handoff

## 1. Repository Directory Diff

```text
knowledge/
├── signal/
├── proposal/
├── validation/
├── promotion/
├── schemas/
│   ├── improvement_signal.schema.json
│   ├── improvement_proposal.schema.json
│   ├── validation_evidence.schema.json
│   └── promotion_record.schema.json
├── cli/
└── tests/
    └── test_schemas.py
```

## 2. JSON Schema Files (FULL CONTENT)

### `knowledge/schemas/improvement_signal.schema.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://ld-course-factory.adk/schemas/backlog/improvement_signal.schema.json",
  "title": "Improvement Signal",
  "description": "A discrete unit of feedback, observation, or error from the runtime environment.",
  "type": "object",
  "required": [
    "governance_id",
    "schema_version",
    "created_at_utc",
    "source",
    "signal_type",
    "content",
    "tenant_context",
    "pii_scrubbed"
  ],
  "properties": {
    "governance_id": {
      "type": "string",
      "description": "Immutable UUIDv4 or Content Hash identifying this signal.",
      "pattern": "^[0-9a-fA-F-]{36}$"
    },
    "schema_version": {
      "type": "string",
      "const": "1.0.0"
    },
    "created_at_utc": {
      "type": "string",
      "format": "date-time",
      "description": "creation timestamp in UTC ISO-8601."
    },
    "source": {
      "type": "object",
      "required": ["type", "origin_id"],
      "properties": {
        "type": {
          "type": "string",
          "enum": ["pilot_feedback", "operator_observation", "automated_scorer", "system_error"]
        },
        "origin_id": {
          "type": "string",
          "description": "ID of the user, agent, or run that generated the signal."
        }
      },
      "additionalProperties": false
    },
    "signal_type": {
      "type": "string",
      "enum": ["complaint", "observation", "feature_request", "bug_report"]
    },
    "content": {
      "type": "object",
      "required": ["summary", "details"],
      "properties": {
        "summary": { "type": "string", "maxLength": 200 },
        "details": { "type": "string" },
        "affected_artifacts": {
          "type": "array",
          "items": { "type": "string" }
        }
      },
      "additionalProperties": false
    },
    "tenant_context": {
      "type": "object",
      "required": ["tenant_id"],
      "properties": {
        "tenant_id": { "type": "string" },
        "course_id": { "type": "string" }
      },
      "additionalProperties": false
    },
    "pii_scrubbed": {
      "type": "boolean",
      "const": true,
      "description": "Must be true to be accepted into the backlog."
    }
  },
  "additionalProperties": false
}
```

### `knowledge/schemas/improvement_proposal.schema.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://ld-course-factory.adk/schemas/backlog/improvement_proposal.schema.json",
  "title": "Improvement Proposal",
  "description": "A proposed change to the system logic or content, linking signals to a solution.",
  "type": "object",
  "required": [
    "governance_id",
    "schema_version",
    "created_at_utc",
    "author_id",
    "linked_signal_ids",
    "target_component",
    "change_intent",
    "risk_level",
    "governance_state"
  ],
  "properties": {
    "governance_id": {
      "type": "string",
      "pattern": "^[0-9a-fA-F-]{36}$"
    },
    "schema_version": {
      "type": "string",
      "const": "1.0.0"
    },
    "created_at_utc": {
      "type": "string",
      "format": "date-time"
    },
    "author_id": {
      "type": "string",
      "description": "Agent or Human ID proposing the change."
    },
    "linked_signal_ids": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "string",
        "pattern": "^[0-9a-fA-F-]{36}$"
      },
      "description": "Must link to at least one valid Signal ID."
    },
    "target_component": {
      "type": "object",
      "required": ["path", "version_constraint"],
      "properties": {
        "path": { 
          "type": "string",
          "description": "Fully qualified module path (e.g. agents.librarian.prompts)."
        },
        "version_constraint": {
          "type": "string",
          "description": "Semantic version range this proposal applies to."
        }
      },
      "additionalProperties": false
    },
    "change_intent": {
      "type": "object",
      "required": ["rationale", "proposed_modification"],
      "properties": {
        "rationale": { "type": "string" },
        "proposed_modification": { 
          "type": "string",
          "description": "Description or diff of the intended change."
        }
      },
      "additionalProperties": false
    },
    "risk_level": {
      "type": "string",
      "enum": ["LOW", "MEDIUM", "HIGH"]
    },
    "governance_state": {
      "type": "string",
      "enum": ["DRAFT", "REVIEW", "APPROVED", "REJECTED", "SUPERSEDED", "IMPLEMENTED"]
    },
    "parent_proposal_id": {
      "type": "string",
      "pattern": "^[0-9a-fA-F-]{36}$",
      "description": "If this updates a previous proposal, link it here."
    }
  },
  "additionalProperties": false
}
```

### `knowledge/schemas/validation_evidence.schema.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://ld-course-factory.adk/schemas/backlog/validation_evidence.schema.json",
  "title": "Validation Evidence",
  "description": "Immutable record of verification for a specific Proposal.",
  "type": "object",
  "required": [
    "governance_id",
    "schema_version",
    "created_at_utc",
    "proposal_id",
    "validator_context",
    "validation_outcome",
    "evidence_artifacts"
  ],
  "properties": {
    "governance_id": {
      "type": "string",
      "pattern": "^[0-9a-fA-F-]{36}$"
    },
    "schema_version": {
      "type": "string",
      "const": "1.0.0"
    },
    "created_at_utc": {
      "type": "string",
      "format": "date-time"
    },
    "proposal_id": {
      "type": "string",
      "pattern": "^[0-9a-fA-F-]{36}$"
    },
    "validator_context": {
      "type": "object",
      "required": ["runner_id", "environment"],
      "properties": {
        "runner_id": { "type": "string" },
        "environment": { "type": "string", "enum": ["ci", "sandbox", "dry_run"] }
      },
      "additionalProperties": false
    },
    "validation_outcome": {
      "type": "string",
      "enum": ["PASS", "FAIL", "REGRESSION", "ERROR"]
    },
    "evidence_artifacts": {
      "type": "object",
      "required": ["run_id", "summary"],
      "properties": {
        "run_id": { "type": "string" },
        "summary": { "type": "string" },
        "logs_uri": { "type": "string" },
        "metrics": {
          "type": "object",
          "additionalProperties": { "type": "number" }
        }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

### `knowledge/schemas/promotion_record.schema.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://ld-course-factory.adk/schemas/backlog/promotion_record.schema.json",
  "title": "Promotion Record",
  "description": "The final seal of approval linking a Proposal to a specific commit/release.",
  "type": "object",
  "required": [
    "governance_id",
    "schema_version",
    "created_at_utc",
    "proposal_id",
    "evidence_id",
    "approval_authority",
    "target_git_ref",
    "promotion_status"
  ],
  "properties": {
    "governance_id": {
      "type": "string",
      "pattern": "^[0-9a-fA-F-]{36}$"
    },
    "schema_version": {
      "type": "string",
      "const": "1.0.0"
    },
    "created_at_utc": {
      "type": "string",
      "format": "date-time"
    },
    "proposal_id": {
      "type": "string",
      "pattern": "^[0-9a-fA-F-]{36}$"
    },
    "evidence_id": {
      "type": "string",
      "pattern": "^[0-9a-fA-F-]{36}$",
      "description": "The PASSing validation evidence ID."
    },
    "approval_authority": {
      "type": "object",
      "required": ["approver_id", "signature", "role"],
      "properties": {
        "approver_id": { "type": "string" },
        "role": { "type": "string" },
        "signature": { 
          "type": "string",
          "description": "Cryptographic signature or authenticated token hash."
        }
      },
      "additionalProperties": false
    },
    "target_git_ref": {
      "type": "string",
      "description": "The git commit hash or tag that implements this proposal."
    },
    "promotion_status": {
      "type": "string",
      "enum": ["PROMOTED", "ROLLED_BACK"],
      "description": "State transition direction."
    }
  },
  "additionalProperties": false
}
```

## 3. Deterministic Storage Rules

1.  **Filename Format**: All backlog artifacts must be stored as `{governance_id}.json` within their respective specific subdirectories (`knowledge/signals/`, `knowledge/proposals/`, etc.).
2.  **ID Generation**: `governance_id` must be a v4 UUID or SHA-256 Content Hash. It must be generated at creation time and never modified.
3.  **Append-Only Enforcement**: The filesystem layer must `chmod 444` (read-only) any artifact after writing. The ingestion CLI must strictly fail if the target file already exists (no overwrites).
4.  **Prohibition of Overwrite**: Updates to a proposal must result in a **new** file with a new `governance_id` that references the `parent_proposal_id` of the previous version. The original file remains untouched.
5.  **Promotion Version Tagging**: When a `promotion_record` is created, the system must create a git tag `backlog-{proposal_id}` pointing to the commit referenced in `target_git_ref`.

## 4. CI Enforcement Specification

The following checks must run in the CI pipeline (e.g., `scripts/validate_schemas.py` called from GitHub Actions):

-   [ ] **Schema Validation**: All `*.json` files in `knowledge/` must validate against their respective schemas in `knowledge/schemas/`.
-   [ ] **Immutable History**: The CI must fail if any commit modifies an existing `.json` file in `knowledge/` (except for specific 'draft' folders if they existed, but here all are immutable).
-   [ ] **Linkage Integrity**: 
    -   Every `improvement_proposal` must contain `linked_signal_ids` that exist in `knowledge/signals/`.
    -   Every `validation_evidence` must link to a valid `improvement_proposal` in `knowledge/proposals/`.
    -   Every `promotion_record` must link to a `validation_evidence` that has `validation_outcome: "PASS"`.
-   [ ] **No Orphans**: Any `improvement_proposal` committed to `knowledge/proposals/` without at least one `improvement_signal` in the same commit or existing history must trigger a failure.
