# Architecture Blueprint: v0.6 Enterprise Scale

**Status:** Draft
**Target Version:** 0.6
**Baseline:** v0.5.2 (Production Validated)
**Author:** Lead Systems Architect (Antigravity)

---

## 1. Architectural Goals for v0.6

This blueprint defines the transition from the v0.5.2 "Pilot-Ready" system to a v0.6 "Enterprise-Scalable" production platform. The focus shifts from proving feasibility to maximizing quality, efficiency, and integration readiness.

| Goal | Metric / Outcome | v0.5.2 State | v0.6 Target State |
| :--- | :--- | :--- | :--- |
| **Output Quality Elevation** | Separation of structure vs. content | Linear generation (risk of drift) | **Two-Pass Model** (Structure First → Content Second) |
| **Cost Efficiency** | Cost per successful deployed course | Linear cost (fail late = expensive) | **Fail Fast** (Cheap Pass 1 validation prevents expensive Pass 2 waste). Target **30% reduction** in wasted spend. |
| **Deployment Readiness** | LMS / SCORM compatibility | Markdown deliverables (requires manual porting) | **Canonical Learning Object Schema** + Media Adapters (Direct export path) |
| **Governance Scaling** | Approval latency vs. Volume | Manual gates for every run | **Tiered Governance**: Risk-based gates + Executive Dashboard signals |

---

## 2. New Architectural Capabilities

### A. Two-Pass Generation Model

To solve the "drift" problem and optimize cost, the monolithic agent pipeline is split into two distinct phases with a hard governance barrier.

#### Pass 1: The Reasoning Core (Structure & Strategy)
*   **Focus:** Educational logic, curriculum architecture, learning objectives, and assessment strategy.
*   **Agents:** Strategy Lead, Learning Architect, Assessment Designer.
*   **Output:** `course_architecture.json` (A validated graph of Learning Objects).
*   **Cost:** Low (text-only, reasoning models).
*   **Governance:** **Structural Gate**. Must be approved before generating content.

#### Pass 2: The Production Factory (Content & Media)
*   **Focus:** Tone, storytelling, scriptwriting, asset generation, and formatting.
*   **Agents:** Instructional Designer, Storyboard Artist, **Media Producer (New)**, QA.
*   **Input:** Locked `course_architecture.json` (Immutable during Pass 2).
*   **Output:** Production-ready assets (Scripts, Images, Slide Decks, SCORM descriptors).
*   **Cost:** High (Creative generation, image models).

### B. Expanded Learning Object (LO) Schema

We move from loose JSON state to a strict **Canonical Data Model**.

**New Schema: `schemas/learning_object.json`**

```json
{
  "id": "lo_101_intro",
  "type": "concept | procedure | fact | principle",
  "metadata": {
    "taxonomy_level": "bloom_apply",
    "duration_minutes": 5,
    "tags": ["onboarding", "compliance"]
  },
  "content": {
    "key_points": ["..."],
    "misconceptions": ["..."],
    "narrative_arc": "Hero's Journey"
  },
  "assessment": {
    "knowledge_checks": [],
    "rubric_id": "rubric_v1"
  },
  "relationships": {
    "prerequisites": ["lo_100_safety"],
    "supports": ["lo_102_advanced"]
  }
}
```

**Reusability Strategy:**
*   LOs are stored as atomic units.
*   A "Course" is a named collection of LO citations.
*   Enables "Remixing" existing LOs into new curricula without regeneration.

### C. Media & Delivery Layer

A new abstraction layer handles the translation of "Scripts" into "Deployable Formats".

**New Agents / Services:**
1.  **Media Adapter Agent:**
    *   Reads `learning_object` + `sme_notes`.
    *   Outputs `media_spec.json` (scene-by-scene visual instructions, asset requests).
2.  **Delivery Packager (Service):**
    *   Not an LLM agent, but a Python service (`src/packager`).
    *   Translates `media_spec` + Markdown into specific formats:
        *   `target=slides` → Reveal.js / PPTX bundle
        *   `target=rise` → Rise 360 compatible structure
        *   `target=scorm` → scorm_driver packaging

---

## 3. Updated Agent Topology

The linear chain is replaced by a two-stage flow with an intermediate persistence layer.

```mermaid
graph TD
    subgraph "Pass 1: Reasoning Core"
        SL[Strategy Lead] --> CA[Curriculum Architect]
        CA --> AD[Assessment Designer]
        AD --> |Output| LOG[Learning Object Graph]
    end

    G1{Governance Gate 1\nAuthorize Production}

    subgraph "Pass 2: Production Factory"
        LOG --> ID[Instructional Designer]
        ID --> SA[Storyboard Artist]
        ID --> MP[Media Producer (New)]
        SA --> QA[QA Agent]
        MP --> QA
    end

    QA --> |Verified Assets| DP[Delivery Packager]
    DP --> Output[Deployable Bundle]

    LOG --> G1
    G1 --> ID
```

**Key Data Flow:**
*   Pass 1 agents R/W to `system_state.curriculum`.
*   **Gate 1** freezes `system_state.curriculum`.
*   Pass 2 agents Read-Only `system_state.curriculum`, Write to `system_state.assets`.

---

## 4. Governance Evolution

Governance in v0.6 scales from "checking text" to "verifying structure".

| Governance Layer | v0.5.2 Implementation | v0.6 Evolution |
| :--- | :--- | :--- |
| **Deterministic Audit** | `audit_summary.json` (Run level) | **LO Graph Hash**: Cryptographic proof that Pass 2 did not deviate from Pass 1 instructions. |
| **Regression Prevention** | `verify_run_diff.py` (Text diff) | **Semantic Diff**: "Did the Learning Objectives change?" vs "Did the phrasing change?". |
| **Executive Signal** | Manual CLI Output | **Risk Dashboard**: Aggregated view of "Open Questions per Course". |

**New Gate Rule:**
*   **Pass 1 Gate:** Manual Approval Mandatory. (High leverage decision).
*   **Pass 2 Gates:** Automated checks for JSON schema validity & Asset completeness. Risk gate only on content policy violation.

---

## 5. Cost and Performance Model

**Cost Analysis (Est. per 60 min Course):**

| Phase | v0.5.2 Cost | v0.6 Cost | Rationale |
| :--- | :--- | :--- | :--- |
| **Strategy & Outline** | $0.50 | $0.80 | More deeper reasoning models (O1/Claude 3.5 Sonnet) used in Pass 1. |
| **Scripting & Content** | $4.00 | $2.50 | Pass 2 uses faster, constrained models (GPT-4o/Flash) strictly following LO graph. |
| **Rework / Waste** | 20% (entire run rerun) | 5% (Pass 2 rerun only) | if Strategy matches, we only re-run production, not reasoning. |
| **Total** | **~$5.40** | **~$3.45** | **~36% Cost Reduction** via caching Pass 1. |

**Latency:**
*   **v0.5.2:** 15 mins end-to-end (Sequential).
*   **v0.6:**
    *   Pass 1: 3 mins (Interactive speed).
    *   Review: (User time).
    *   Pass 2: 12 mins (Can run parallel branches per LO).

---

## 6. Migration Plan (v0.5.2 → v0.6)

This migration uses a "Strangler Fig" pattern: We build the new specific capabilities while keeping the v0.5 orchestrator running until replacement.

### Phase 1: Architecture Scaffolding (Wk 1)
*   [ ] Create `schemas/learning_object.json`.
*   [ ] Implement `TwoPassOrchestrator` (extends `RootAgent`).
*   [ ] **Validation:** Unit tests for Schema compliance.

### Phase 2: Agent Upgrades (Pass 1) (Wk 2)
*   [ ] Refactor `Strategy Lead` and `Curriculum Architect` to output strictly to new LO schema.
*   [ ] Implement **Gate 1** (Intermediate Save/Load).
*   [ ] **Validation:** Verify `course_architecture.json` generation.

### Phase 3: Production Factory (Wk 3)
*   [ ] Update `Instructional Designer` to ingest LO Graph (Read-Only).
*   [ ] Create `Media Producer` Agent (Script → Media Spec).
*   [ ] **Validation:** End-to-end run (Pass 1 + Pass 2).

### Phase 4: Delivery & Scale (Wk 4)
*   [ ] Implement `Delivery Packager` stub (Markdown export).
*   [ ] Integrate `verify_semantic_diff.py`.
*   [ ] **Exit Criteria:** 3 Successful Golden Runs with new Architecture.

---
