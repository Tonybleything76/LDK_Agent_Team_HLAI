# Phase 5: Improvement Backlog Schema Specification

## 1. Required Schema Files

The following four schema definitions constitute the minimum complete set required to instantiate the Improvement Backlog logic. They must exist before any ingestion tooling is built.

### 1. `schemas/backlog/improvement_signal.json`
*   **Ownership Scope:** External (Pilot/Operator/Automated Scorer) -> Backlog Ingest.
*   **Why it must exist first:** Defines the contract for *what* is allowed to trigger a change. Without this, we cannot build ingesters that safely strip PII or tenant context. It acts as the firewall between "Operation" and "Evolution".
*   **Core Responsibility:** Captures the "Complaint" or "Observation" without prescribing the solution.

### 2. `schemas/backlog/improvement_proposal.json`
*   **Ownership Scope:** Internal (Architect Agent / Human Engineer).
*   **Why it must exist first:** This is the unit of work for the system. It binds a specific solution to a set of Signals. It is the "Pull Request" of the governance model.
*   **Core Responsibility:** Defines the *Intent* of the change (what logic/prompts will trigger) and the *Rationale* (why this fixes the linked signals).

### 3. `schemas/backlog/validation_evidence.json`
*   **Ownership Scope:** System (Validation Runner / CI).
*   **Why it must exist first:** Governance requires proof before approval. This schema structures the "Test Results"—dry runs, regression checks, and diff analyses—so that the Gatekeeper (Human) has a standardized view of risk.
*   **Core Responsibility:** Immutable record of *what happened* when the Proposal was applied in a sandbox.

### 4. `schemas/backlog/governance_audit.json` (The Promotion Record)
*   **Ownership Scope:** System (Governance Engine).
*   **Why it must exist first:** Enforces the "Chain of Custody". It links `Signal` -> `Proposal` -> `Evidence` -> `Approval Decision` -> `Git Commit`.
*   **Core Responsibility:** Ensures no code change enters `main` without a cryptographically verifiable path back to a business justification (Signal).

---

## 2. Canonical Field Definitions (Conceptual)

These semantic definitions must be enforced across all backlog schemas to ensure referential integrity and governance.

### Identity & Linkage
*   **`governance_id`**: A globally unique, immutable identifier for any Backlog Artifact (Signal, Proposal, etc.). Must be collision-resistant (e.g., UUIDv4 or SHA-256 content hash).
*   **`run_linkage`**: A composite key (`run_id` + `node_path`) identifying exactly *where* in a previous execution an issue occurred. Must resolve to a specific artifact in the Audit Log.
*   **`proposal_fingerprint`**: A hash of the proposal's *intent* (target component + semantic change). Used to detect and reject duplicate concurrent proposals.

### Architecture Targeting
*   **`target_component`**: A strict, fully qualified path to the system component being modified (e.g., `agents.learning_architect.prompts.outline_creation`). Must align with the codebase structure.
*   **`semantic_version_target`**: The specific version of the component that the proposal intends to modify (prevents "merge conflicts" in logic).

### Governance Classification
*   **`risk_level`**: An enumerated classification (`LOW`, `MEDIUM`, `HIGH`) derived from the *type* of change (e.g., Prompt tweak vs. Schema Refactor). Determines the required approval authority.
*   **`validation_status`**: A strictly controlled state enum (`PENDING`, `PASS`, `FAIL`, `REGRESSION`). Only the Validation Runner can write this field.
*   **`approval_signature`**: Cryptographic or Authenticated proof of the human who authorized the transition from `Review` to `Promoted`.

---

## 3. Determinism & Governance Constraints on Schemas

The schema layer is the primary enforcement mechanism for the "Governance Air Gap". It must implement the following controls:

### Append-Only History
The schemas must be designed such that updates are effectively new records. An `ImprovementProposal` is never "edited"; a new version is created pointing to the previous one (`parent_id`). The Governance Audit log is a linear, append-only ledger.

### Prohibition of Silent Mutation
Every schema must reject "orphan" changes.
*   A **Proposal** is invalid if it does not link to at least one **Signal**.
*   A **Promotion** is invalid if it does not link to a passing **Validation Evidence** record.
*   **Constraint**: The schematized data structure must *require* these foreign keys, making "admin bypass" syntactically invalid.

### Explicit Approval Lineage
The `governance_audit` structure must structurally enforce the "Why". It is not enough to say "Approved by Admin". The record must serialize:
`{ Signal(s) } + { Proposal } + { Validation } + { Human_Decision } = { Release_Tag }`.
This equation must be verifiable by traversing the links in the schema objects.

### Tenant Boundary Protection
The `ImprovementSignal` schema must strictly validate input fields to ensure no "free text" dumps from the runtime are accepted unless explicitly sanitized.
*   **Constraint**: Schema fields for "Pilot Feedback" must be structured (e.g., Enums, specific selected text ranges) rather than open blobs, or tagged with a `pii_scrubbed: boolean` assertion that the ingress tool must verify.

---

## 4. Definition of “Schema Layer Complete”

The Backlog Schema Layer is considered complete and ready for tooling construction ONLY when the following binary conditions are met in the repository:

### 1. Schema Files Present
*   [ ] `schemas/backlog/improvement_signal.json` exists and is valid JSON.
*   [ ] `schemas/backlog/improvement_proposal.json` exists and is valid JSON.
*   [ ] `schemas/backlog/validation_evidence.json` exists and is valid JSON.
*   [ ] `schemas/backlog/governance_audit.json` exists and is valid JSON.

### 2. Cross-Reference Validation
*   [ ] A test script `tests/governance/test_schema_integrity.py` passes.
*   [ ] The test generates a mock chain: `Signal` -> `Proposal` -> `Evidence` -> `Audit`.
*   [ ] The test confirms that `jsonschema` validation strictly enforces the presence of linkage IDs (e.g., a Proposal implies a Signal ID).

### 3. CI Integration
*   [ ] The `scripts/validate_schemas.py` (or equivalent) preflight check includes the new `schemas/backlog/` directory.
*   [ ] Changing a field in `improvement_proposal.json` without updating the version/tests fails the build.

### 4. Pilot Readiness
*   [ ] A `mock_signal.json` matching the schema can be successfully loaded and validated by the `course_architecture` schema loader (proving system compatibility).
