# v0.5.1 Operator Test Plan: First Real Test Inputs

## Overview

This document provides copy-paste-ready test inputs and a structured 3-run test cycle to validate the governed agent pipeline using realistic but intentionally incomplete learning project data.

---

## Part 1: Test Input Design

### 1.1 What the Test Inputs Represent

**Scenario:** A contact center needs to train new customer service representatives quickly due to high turnover and declining satisfaction scores.

**business_brief.md** represents:
- A real business problem with measurable goals
- Time pressure (5-week deadline)
- Budget constraints (existing tools only)
- Compliance requirements (PCI, WCAG)
- A **critical risk**: CRM system replacement scheduled during/after course delivery

**sme_notes.md** represents:
- Subject matter expertise from a training manager
- Practical knowledge of common call types and failure modes
- **Intentional gaps**:
  - De-escalation framework exists but isn't documented
  - Identity verification scripts are missing
  - Knowledge base is 18 months out of date
  - SME availability is limited (5 hours/week for 4 weeks only)
- **Conflicting information**: Should we train on current CRM or wait for new system?

### 1.2 Why the Content is Shaped This Way

**Design Principles:**

1. **Realistic Complexity**: Real projects have incomplete information, conflicting priorities, and time pressure
2. **Governance Triggers**: Content is designed to trigger specific pipeline behaviors:
   - **Phase Gates (3/6/9)**: Normal checkpoints for review
   - **Risk Gate (Open Questions)**: Missing documentation and conflicting timelines will generate 8+ weighted open questions
   - **Risk Gate (QA Critical)**: System obsolescence risk should trigger QA critical findings
3. **Operator Learning**: Tests whether agents properly escalate ambiguity vs. making assumptions

### 1.3 Intentionally Risky or Ambiguous Aspects

| Aspect | Type | Expected Agent Behavior |
|--------|------|-------------------------|
| **CRM replacement in April** | CRITICAL RISK | Should flag as BLOCKER in open_questions, trigger risk gate |
| **Undocumented de-escalation framework** | MAJOR GAP | Should flag as MAJOR open question, may require SME interview |
| **5-week timeline vs. missing resources** | SCHEDULE RISK | Should identify as constraint, propose mitigation |
| **SME availability (5 hrs/week for 4 weeks)** | RESOURCE CONSTRAINT | Should calculate total SME time (20 hours) and assess feasibility |
| **30% ESL learners** | DESIGN CONSTRAINT | Should influence instructional design (simpler language, more visuals) |
| **Outdated knowledge base** | QUALITY RISK | Should flag as dependency, recommend update or workaround |
| **No identity verification scripts** | COMPLIANCE GAP | Should escalate as compliance risk (PCI/privacy requirement) |

**Expected Open Questions Count:**
- Strategy/Research phase: 6-8 questions (mostly MAJOR/CRITICAL)
- Architecture phase: 5-7 questions (design decisions)
- QA phase: 3-5 questions (including CRITICAL for CRM obsolescence)
- **Total weighted questions: 14-20** (well above threshold of 8)

---

## Part 2: Three-Run Test Cycle (Production-Safe)

### Run 1: Golden Baseline with Dev Profile

**Objective:** Verify the pipeline completes end-to-end with realistic inputs using the permissive dev profile.

**Script:** `./scripts/run_dev.sh`

**Configuration Changes:** None required (dev profile has relaxed thresholds and auto-override enabled)

**Execution:**
```bash
# Run pipeline with dev profile
./scripts/run_dev.sh
```

**Expected Behavior:**
- ✅ Pipeline completes all 9 agents
- ✅ Auto-approves phase gates at steps 3, 6, 9
- ⚠️ Generates 14-20 open questions (above threshold, but auto-override enabled in dev profile)
- ✅ Risk gates trigger but are auto-overridden (dev profile behavior)
- ✅ Produces audit summary with `end_state: run_completed`

**Artifacts to Check:**
```bash
# 1. Check exit code
echo $?  # Should be 0

# 2. Verify completion in run_report
python3 scripts/run_report.py --latest | grep "end_state"
# Expected: "end_state": "run_completed"

# 3. Check audit_summary
ls -lt outputs/ | head -2  # Get latest RUN_ID
cat outputs/<RUN_ID>/audit_summary.json | jq '.end_state'

# 4. Verify ledger shows auto-approvals
tail -20 governance/run_ledger.jsonl | grep -E "approval_granted|risk_gate"
```

**Success Criteria:**
- Exit code is `0`
- `run_report` shows `end_state: run_completed`
- `audit_summary.json` exists with complete data
- Ledger shows phase gate approvals at steps 3, 6, 9
- 14-20 open questions logged

---

### Run 2: CI Profile with Risk Gate Detection

**Objective:** Verify risk gates trigger correctly using the CI profile (which requires manual approval for risk gates).

**Script:** `./scripts/run_ci.sh`

**Configuration Changes:** None required (CI profile enforces manual approval for risk gates)

**Execution:**
```bash
# Run pipeline with CI profile
./scripts/run_ci.sh
```

**Expected Behavior:**
- ✅ Pipeline runs normally through early agents
- ✅ Auto-approves phase gates at steps 3, 6, 9 (CI profile allows this)
- 🛑 **STOPS at first risk gate** (likely step 3 or 4) with prompt for manual approval
- ⚠️ Risk gate triggered by: open_questions_threshold (14-20 questions > 8 threshold)

**When Prompted:**
```
🛑 RISK GATE: open_questions_threshold
Triggered by agent: learning_architect_agent at step 3
Type APPROVE to OVERRIDE and continue, anything else to stop:
```

**Action:** Type `APPROVE` and press Enter to continue

**Artifacts to Check:**
```bash
# 1. Check for risk gate events in ledger
grep "risk_gate_forced" governance/run_ledger.jsonl | tail -5

# 2. Verify manual approval was logged
grep "approval_granted" governance/run_ledger.jsonl | grep "manual" | tail -3

# 3. Confirm completion
python3 scripts/run_report.py --latest | grep "end_state"
# Expected: "end_state": "run_completed"
```

**Success Criteria:**
- Pipeline paused at risk gate and required manual approval
- Operator typed `APPROVE` to continue
- Exit code is `0` (after approval)
- Ledger shows `risk_gate_forced` event
- Ledger shows manual approval with operator source
- Pipeline completed after approval

---

### Run 3: CI Profile with Rejection (Governance Enforcement)

**Objective:** Verify strict governance enforcement when operator rejects approval at risk gate.

**Script:** `./scripts/run_ci.sh`

**Configuration Changes:** None required

**Execution:**
```bash
# Run pipeline with CI profile again
./scripts/run_ci.sh
```

**Expected Behavior:**
- ✅ Pipeline runs normally through early agents
- 🛑 **STOPS at first risk gate** (same as Run 2)

**When Prompted:**
```
🛑 RISK GATE: open_questions_threshold
Triggered by agent: learning_architect_agent at step 3
Type APPROVE to OVERRIDE and continue, anything else to stop:
```

**Action:** Press Enter WITHOUT typing APPROVE (reject the approval)

**Artifacts to Check:**
```bash
# 1. Verify non-zero exit code
echo $?  # Should be 1 or non-zero

# 2. Check ledger for rejection
grep "approval_rejected" governance/run_ledger.jsonl | tail -3

# 3. Verify partial completion
python3 scripts/run_report.py --latest | grep "current_step_completed"
# Should show step 2 or 3 (not 9)

# 4. Check manifest status
ls -lt outputs/ | head -2  # Get latest RUN_ID
cat outputs/<RUN_ID>/run_manifest.json | jq '.status'
# Expected: "aborted"
```

**Success Criteria:**
- Pipeline halted at risk gate when operator rejected
- Exit code is non-zero (failure)
- Terminal showed: `⛔ Run stopped by user approval rejection.`
- Ledger shows `approval_rejected` event
- Pipeline stopped at step 2-4 (not completed)
- Manifest status is `aborted`

---

### Pre-Test Setup (One-Time)

```bash
# Navigate to project root
cd /Users/jbleyta/Projects/ld-course-factory-adk

# Verify test inputs are in place
cat inputs/business_brief.md | head -5
cat inputs/sme_notes.md | head -5

# Verify scripts are executable
chmod +x scripts/run_dev.sh scripts/run_ci.sh scripts/run_prod.sh
```

### Run 1: Golden Baseline

```bash
# Run dev profile (auto-approves all gates including risk gates)
./scripts/run_dev.sh

# Verify success
echo "Exit code: $?"
python3 scripts/run_report.py --latest | grep "end_state"

# Save RUN_ID for baseline
ls -lt outputs/ | head -2
```

**Success Criteria:**
- Exit code is `0`
- Report shows `end_state: run_completed`
- 14-20 open questions logged

---

### Run 2: CI Profile with Manual Approval

```bash
# Run CI profile (requires manual approval for risk gates)
./scripts/run_ci.sh

# When prompted at risk gate, type: APPROVE
# Then press Enter

# Verify completion
echo "Exit code: $?"
grep "risk_gate_forced" governance/run_ledger.jsonl | tail -5
grep "approval_granted" governance/run_ledger.jsonl | grep "manual" | tail -3
```

**Success Criteria:**
- Pipeline paused at risk gate
- Operator typed `APPROVE` to continue
- Exit code is `0`
- Ledger shows manual approval

---

### Run 3: CI Profile with Rejection

```bash
# Run CI profile again
./scripts/run_ci.sh

# When prompted at risk gate, press Enter WITHOUT typing APPROVE

# Verify rejection
echo "Exit code: $?"  # Should be non-zero
grep "approval_rejected" governance/run_ledger.jsonl | tail -3
python3 scripts/run_report.py --latest | grep "current_step_completed"
```

**Success Criteria:**
- Pipeline halted at risk gate
- Exit code is non-zero
- Ledger shows `approval_rejected`
- Pipeline stopped at step 2-4

---

## Part 4: Completion Criteria

### v0.5.1 Team Testing Is Successful When:

1. ✅ **Run 1 completes successfully** with realistic inputs, generating 14-20 open questions and producing a complete audit trail

2. ✅ **Risk gates trigger correctly** when open questions exceed threshold (8+) or QA finds critical issues, with events logged to governance ledger

3. ✅ **Auto-override policy works** in permissive mode (dev profile with `auto_override: true`), allowing pipeline to complete despite risk gates

4. ✅ **Strict governance enforcement works** when `auto_override: false`, forcing manual approval at risk gates and halting pipeline when approval is rejected

5. ✅ **Audit trail is complete** for all three runs, with ledger events showing:
   - Phase gate approvals (steps 3, 6, 9)
   - Risk gate triggers (with metadata: threshold, count, reason)
   - Approval mode (auto vs. manual)
   - Run outcomes (completed, aborted, failed)

6. ✅ **Agents properly escalate ambiguity** by generating open questions for missing documentation, conflicting timelines, and compliance gaps (observable in run reports)

7. ✅ **No false positives or negatives** in governance enforcement:
   - Phase gates don't trigger risk escalation
   - Risk gates don't trigger on low-severity issues
   - Auto-override respects policy configuration

---

## Appendix: Understanding the Test Inputs

### Why This Scenario Triggers Governance

**Open Questions Expected:**

From **strategy_lead_agent** (step 1):
- CRITICAL: "CRM system replacement scheduled for April 2026 - should we delay course or train on current system?"
- MAJOR: "De-escalation framework (LEAP) exists but is not formally documented - how do we standardize training?"
- MAJOR: "SME availability limited to 20 total hours - is this sufficient for course development?"

From **learner_research_agent** (step 2):
- MAJOR: "30% of learners are ESL - what language complexity level should we target?"
- MINOR: "Limited computer literacy for some learners - should we include basic computer skills module?"

From **learning_architect_agent** (step 3):
- CRITICAL: "Identity verification scripts missing - compliance requirement for PCI/privacy, need formal documentation"
- MAJOR: "Knowledge base 18 months out of date - should we update before referencing in course?"
- MAJOR: "Practice simulation tool needed but not budgeted - can Rise provide adequate interactivity?"

From **qa_agent** (step 7):
- CRITICAL: "Course will be obsolete within 60 days due to CRM replacement - recommend delaying until new system is available"
- BLOCKER: "Missing compliance documentation (identity verification) creates legal risk"

**Total: 14-16 weighted questions** (threshold is 8)

### Why This Scenario Reflects Reality

Real learning projects often have:
- **Incomplete requirements**: Stakeholders know what they want but haven't documented processes
- **Conflicting priorities**: Speed vs. quality, current vs. future state
- **Resource constraints**: Limited SME time, budget restrictions
- **External dependencies**: System upgrades, policy changes, compliance requirements
- **Ambiguity**: "We need training" without clear success criteria or scope

This test scenario validates that the agent pipeline:
1. **Identifies risks** rather than making assumptions
2. **Escalates appropriately** via open questions and risk gates
3. **Respects governance** by enforcing approval requirements
4. **Produces audit trails** for decision accountability

---

**Document Version:** 1.0  
**Created:** 2026-02-04  
**Purpose:** Enable first real operator testing of v0.5.1 governed agent pipeline
