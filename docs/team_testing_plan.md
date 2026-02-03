# Team Testing Plan - v0.5.1

This document defines the minimum test cycle for validating the system before use on a real client project.

## Test Cycle Overview

| Run | Profile | Purpose | Expected Outcome |
|-----|---------|---------|------------------|
| A | dev | Sanity check | Fast pass, relaxed governance |
| B | ci | Regression test | Matches baseline, no policy violations |
| C | prod | Production simulation | Manual approvals work correctly |

---

## Run A: Dev Profile Sanity

**Purpose**: Verify the system starts and completes without errors.

```bash
./scripts/run_dev.sh
```

**Expected Behavior**:
- Auto-approves all gates
- Completes in ~30 seconds (dry_run)
- Produces `audit_summary.json` with `end_state: run_completed`

**Success Criteria**:
- [ ] Exit code 0
- [ ] `outputs/<RUN_ID>/audit_summary.json` exists
- [ ] No parse or validation errors in output

---

## Run B: CI Profile Enforcement

**Purpose**: Verify governance policies are enforced correctly.

```bash
./scripts/run_ci.sh
```

**Expected Behavior**:
- Auto-approves phase gates at steps 3, 6, 9 only
- Risk gates trigger and require approval (simulated via stdin)
- Matches CI-mode baseline for run-diff

**Success Criteria**:
- [ ] Exit code 0
- [ ] `audit_summary.json` shows `governance_profile: ci`
- [ ] Auto-approvals only at steps 3, 6, 9 (check ledger)
- [ ] At least one risk gate triggered

**Verify with**:
```bash
python3 scripts/verify_run_diff.py \
  --baseline_dir tests/baselines/golden_run_baseline \
  --latest \
  --profile ci
```

---

## Run C: Prod Profile with Manual Approvals

**Purpose**: Verify manual approval workflow works end-to-end.

```bash
./scripts/run_prod.sh --dry_run
```

**Expected Behavior**:
- Stops at gate 3, prompts for `APPROVE`
- Stops at gate 6, prompts for `APPROVE`
- Stops at gate 9, prompts for `APPROVE`
- Risk gates also prompt

**Success Criteria**:
- [ ] Operator manually typed `APPROVE` at each prompt
- [ ] `audit_summary.json` shows `auto_approve: false`
- [ ] `gate_summary.approvals.manual >= 3`
- [ ] Pipeline completes with `end_state: run_completed`

---

## Common Failure Modes

### Pipeline Fails to Start

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Config missing` | Missing `config/run_config.json` | Check file exists |
| `Prompt not found` | Invalid prompt path in config | Fix `prompt_path` in config |
| `Deprecated config` | Old config in `orchestrator/config/` | Delete deprecated file |

### Pipeline Fails Mid-Run

| Symptom | Cause | Fix |
|---------|-------|-----|
| `PARSE_ERROR` | Agent returned invalid JSON | Check prompt, retry |
| `VALIDATION_ERROR` | Deliverable too short or has placeholders | Improve prompt |
| Approval rejected | User typed something other than `APPROVE` | Intentional or retry |

### Run-Diff Fails

| Symptom | Cause | Fix |
|---------|-------|-----|
| `New Critical/Blocker Question` | Agent flagged new high-severity issue | Review and approve or fix |
| `Risk Gates Count Increased` | More risk gates than baseline | Update baseline if intentional |
| `Governance Profile Mismatch` | Run used wrong profile | Re-run with correct `--governance_profile` |

---

## Post-Test Validation

After completing all three runs:

```bash
# 1. Run full release check
python3 scripts/release_check.py

# 2. Verify git status is clean
git status --porcelain
# Should show no tracked files in outputs/ or tmp/

# 3. Review latest run report
python3 scripts/run_report.py --latest
```

---

## Acceptance Criteria Summary

- [ ] Run A (dev): Completes with no errors
- [ ] Run B (ci): Passes run-diff, matches baseline
- [ ] Run C (prod): Manual approvals work correctly
- [ ] `release_check.py` passes
- [ ] No artifacts tracked in git
