# Phase 5 Improvement Backlog Architecture

## 1. Backlog System Purpose

The Improvement Backlog serves as the **Governance Air Gap** between live operations and system evolution. Its existance is non-negotiable before any learning loop is enabled because:

1.  **Protects Determinism:** It forces all "learning" to be converted into discrete, versioned code/data changes rather than dynamic model updates. The system never "learns" during a run; it is "taught" between versions.
2.  **Commercial Safety:** It strips tenant-specific context from feedback. A "Signal" enters the backlog, but only sanitized "Patterns" result in changes, preventing data contamination across tenants.
3.  **Audit & Reversibility:** Every change to the reasoning core is traceable to a specific proposal and approval. If a new prompt version degrades performance, the backlog provides the immediate rollback path and the "why" of the original change.

## 2. Backlog Data Model (Conceptual)

The system is built on strict, immutable entities stored as versioned artifacts.

*   **Improvement Signal**: Raw input (e.g., "Pilot Operator marked output as 'Too Generic'", or "Dry Run Score < 80"). References the specific Run ID and Node.
*   **Improvement Proposal (IP)**: The formal change request.
    *   *Source*: Links to Signals.
    *   *Mechanism*: `prompt_update` | `schema_change` | `logic_refactor`.
    *   *Target Component*: Agent Name / Module Path.
    *   *Proposed Change*: Diff or Pointer to new version.
*   **Impact Scope**:
    *   *Risk Level*: `Low` (Wording) | `Medium` (Logic) | `High` (Schema/governance).
    *   *Regression Risk*: Which existing tests might fail?
*   **Validation Evidence**:
    *   *Pre-Computation*: Dry run results of the proposed change.
    *   *Diff Analysis*: Semantic comparison of Before vs. After.
*   **Governance State**: `Draft` -> `Validating` -> `Review_Pending` -> `Approved` -> `Rejected` -> `Promoted`.

## 3. Governance Flow Through the Backlog

1.  **Ingest (Signal Capture)**: Operators or automated scorers tag a run result. The system strips PII/Tenant Data and creates an **Improvement Signal**.
2.  **Triage (Proposal Creation)**: An Architect (or future specialized agent) groups Signals into an **Improvement Proposal**. The solution is drafted (e.g., "Adjust Validator Prompt to be stricter on 'synergy'").
3.  **Validation (The Guardrail)**:
    *   The Proposal is applied in a temporary sandbox.
    *   Regression suite runs.
    *   **Deterministic Test**: Does the change fix the Signal case?
    *   **Side-Effect Test**: Does it break the Golden Set?
4.  **Gate (Human Approval)**:
    *   Reviewer sees: The Signal, The Change, The Diff, The Validation Result.
    *   Binary decision: Approve for Release or Reject.
5.  **Promotion (Version Bump)**:
    *   Approved changes are merged to `main`.
    *   System creates a specialized Git Tag / Release.
    *   Audit Log records the linkage: `Signal -> Proposal -> Commit -> Release`.

## 4. Definition of “Phase 5 Ready”

The system is ready to safely ingest pilot feedback when:

*   [ ] **Repository Standard**: A dedicated directory/store exists for `signals` and `proposals` (e.g., `knowledge/backlog`).
*   [ ] **Schema Enforced**: JSON Schemas for `ImprovementProposal` are defined and validated by CI.
*   [ ] **CLI Tooling**: A command `adk-improve propose` exists to scaffold a valid proposal from a run output.
*   [ ] **Governance Lock**: The CI pipeline fails if a change is made to `prompts/` or `schemas/` without a corresponding `Approved` Proposal ID linked in the commit message/metadata.
