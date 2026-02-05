# v0.5.1 Test Inputs & Operator Test Plan - Summary

## What Was Created

### 1. Realistic Test Inputs (Copy-Paste Ready)

**Location:** `/Users/jbleyta/Projects/ld-course-factory-adk/inputs/`

#### `business_brief.md` (55 lines)
A realistic learning project brief for customer service training with:
- **Business problem:** High turnover (45%), declining CSAT (71%)
- **Time pressure:** 5-week deadline
- **Constraints:** Budget limits, compliance requirements (PCI, WCAG)
- **Critical risk:** CRM system replacement scheduled for April 2026

#### `sme_notes.md` (102 lines)
Subject matter expert notes with intentional gaps:
- **Undocumented framework:** LEAP de-escalation method exists but not formalized
- **Missing resources:** No identity verification scripts (compliance gap)
- **Conflicting priorities:** Train on current CRM or wait for new system?
- **Limited availability:** SME has only 20 total hours (5 hrs/week × 4 weeks)

### 2. Comprehensive Operator Test Plan

**Location:** `/Users/jbleyta/.gemini/antigravity/brain/825c3bf6-f6bc-41a9-99ed-4fb75a573a31/operator_test_plan.md`

**Contents:**
- Part 1: Test Input Design (what, why, intentional risks)
- Part 2: Three-Run Test Cycle (baseline, risk trigger, strict enforcement)
- Part 3: Exact Operator Commands (copy-paste ready)
- Part 4: Completion Criteria (7 observable conditions)
- Appendix: Understanding governance triggers

### 3. Quick Reference Guide

**Location:** `/Users/jbleyta/.gemini/antigravity/brain/825c3bf6-f6bc-41a9-99ed-4fb75a573a31/quick_reference.md`

**Contents:**
- One-page summary of three test runs
- Essential commands only
- Troubleshooting tips

---

## Why These Inputs Trigger Governance

### Expected Open Questions: 14-20 (Threshold: 8)

**CRITICAL/BLOCKER Questions (6-8):**
- CRM replacement in April → course obsolete in 60 days
- Missing identity verification scripts → compliance risk
- Undocumented de-escalation framework → can't standardize training

**MAJOR Questions (5-7):**
- SME availability (20 hours total) → feasibility concern
- Outdated knowledge base (18 months) → quality risk
- 30% ESL learners → design constraint
- No practice simulation tool → interactivity limitation

**MINOR Questions (3-5):**
- Limited computer literacy → prerequisite concern
- Duplicate prompt directories → minor inconsistency

### Risk Gate Triggers

1. **Open Questions Threshold:** 14-20 weighted questions >> 8 threshold
2. **QA Critical:** QA agent will flag CRM obsolescence as CRITICAL/BLOCKER
3. **Compliance Gap:** Missing identity verification scripts (PCI/privacy requirement)

---

## Three-Run Test Cycle

### Run 1: Baseline Success
- **Config:** Risk gates disabled
- **Expected:** ✅ Completes with 14-20 open questions
- **Validates:** Pipeline works end-to-end with realistic inputs

### Run 2: Risk Gates with Auto-Override
- **Config:** Risk gates enabled, `auto_override: true`
- **Expected:** ✅ Triggers risk gates but completes
- **Validates:** Risk detection works, auto-override policy respected

### Run 3: Strict Enforcement
- **Config:** Risk gates enabled, `auto_override: false`
- **Expected:** ❌ Halts at risk gate when operator rejects
- **Validates:** Manual approval enforcement, governance prevents unsafe auto-approval

---

## Completion Criteria (Non-Technical)

**v0.5.1 Team Testing Is Successful When:**

1. ✅ Pipeline processes realistic, incomplete inputs without crashing
2. ✅ System correctly identifies 14-20 risks/questions (not zero, not 100)
3. ✅ Governance gates trigger at correct thresholds (8+ questions, QA critical)
4. ✅ Permissive mode allows work to continue (dev profile)
5. ✅ Strict mode enforces manual approval (prod profile)
6. ✅ Audit trail captures all decisions (who approved, when, why)
7. ✅ Operators can run tests without developer assistance

---

## Key Design Decisions

### Why Customer Service Training?

- **Familiar domain:** Most people understand customer service
- **Realistic complexity:** Real projects have gaps, conflicts, time pressure
- **Clear risks:** CRM obsolescence, missing documentation, compliance gaps
- **Measurable outcomes:** Can count open questions, verify risk triggers

### Why Intentionally Incomplete?

Real learning projects are messy:
- Stakeholders know what they want but haven't documented processes
- External dependencies change (system upgrades, policy changes)
- Resources are constrained (time, budget, SME availability)
- Compliance requirements exist but aren't fully defined

**The test validates that agents:**
- Identify risks rather than make assumptions
- Escalate appropriately via open questions
- Respect governance by enforcing approvals
- Produce audit trails for accountability

### Why Three Runs?

1. **Run 1 (baseline):** Proves the system works
2. **Run 2 (risk detection):** Proves governance triggers correctly
3. **Run 3 (enforcement):** Proves governance can't be bypassed

---

## Next Steps for Operators

1. **Review test inputs:**
   ```bash
   cat inputs/business_brief.md
   cat inputs/sme_notes.md
   ```

2. **Read operator test plan:**
   - Open: `/Users/jbleyta/.gemini/antigravity/brain/825c3bf6-f6bc-41a9-99ed-4fb75a573a31/operator_test_plan.md`
   - Focus on Part 3 (Exact Operator Commands)

3. **Run tests in order:**
   - Run 1: Baseline (should pass)
   - Run 2: Risk gates (should pass with warnings)
   - Run 3: Strict enforcement (should fail at risk gate)

4. **Verify completion criteria:**
   - Check exit codes
   - Review audit summaries
   - Inspect governance ledger

---

## Files Modified/Created

**Modified:**
- `/Users/jbleyta/Projects/ld-course-factory-adk/inputs/business_brief.md` (replaced template with realistic content)
- `/Users/jbleyta/Projects/ld-course-factory-adk/inputs/sme_notes.md` (replaced template with realistic content)

**Created:**
- `/Users/jbleyta/.gemini/antigravity/brain/825c3bf6-f6bc-41a9-99ed-4fb75a573a31/operator_test_plan.md` (comprehensive test plan)
- `/Users/jbleyta/.gemini/antigravity/brain/825c3bf6-f6bc-41a9-99ed-4fb75a573a31/quick_reference.md` (one-page quick reference)
- `/Users/jbleyta/.gemini/antigravity/brain/825c3bf6-f6bc-41a9-99ed-4fb75a573a31/test_inputs_summary.md` (this document)

---

**Version:** 1.0  
**Created:** 2026-02-04  
**Purpose:** Enable first real operator testing of v0.5.1 governed agent pipeline
