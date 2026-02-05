# Production Readiness Checklist - v0.5.1

This document defines what "production-ready" means for the LD Course Factory ADK and how to validate it.

## Definition of Production-Ready

A system is production-ready when:

1. **Governance is enforced**: Auto-approvals ONLY at phase gates 3/6/9, risk gates require manual approval
2. **CI is truthful**: Step names match behavior, failures produce actionable errors
3. **Artifacts are clean**: No secrets, no generated outputs committed
4. **Validation scripts pass**: All release checks succeed

---

## Required Validation Commands

Run these from the project root before any release:

```bash
# 1. Preflight - validates config, prompts, schemas
python3 scripts/preflight_check.py

# 2. Golden run - regression test with deterministic fixtures
python3 scripts/verify_golden_run.py

# 3. CI run-diff enforcement - validates governance policy compliance
# (Automatically run in CI, can be run manually for testing)
python3 scripts/verify_run_diff.py \
  --baseline_dir tests/baselines/golden_run_baseline \
  --candidate_run_id <RUN_ID> \
  --profile ci \
  --format console

# 4. Failure injection - verifies run_diff catches regressions
python3 scripts/verify_failure_injection.py

# 5. Full release check (runs preflight + golden run + report validation)
python3 scripts/release_check.py
```

All commands must exit 0 (pass).

### CI Run-Diff Policy Enforcement

The `verify_run_diff.py` script enforces governance policy by validating:

- **No new CRITICAL/BLOCKER questions** introduced vs baseline
- **Auto-approvals only at phase gates 3, 6, 9** (verified via ledger)
- **Risk gates require manual approval** (or simulated manual in CI)
- **Governance profile matches expectations** (ci/dev/prod)

This script is automatically run in CI after the golden run to ensure policy compliance.

---

## Key Artifacts to Review

### audit_summary.json

Located in `outputs/<RUN_ID>/audit_summary.json`. Review:

| Field | Expected Value | Meaning |
|-------|----------------|---------|
| `end_state` | `run_completed` | Pipeline finished successfully |
| `gate_summary.approvals.auto` | ≥1 | Auto-approvals occurred at phase gates |
| `gate_summary.risk_gates` | Array | Risk gates that required intervention |
| `open_questions_summary.total_count` | Any | Open questions flagged by agents |

### run_manifest.json

Located in `outputs/<RUN_ID>/run_manifest.json`. Review:

| Field | Check | Why |
|-------|-------|-----|
| `governance_profile` | Matches expected (ci/dev/prod) | Confirms correct profile was used |
| `auto_approve` | true/false | Confirms approval mode matches intent |
| `risk_auto_override_default` | false for ci/prod | Risk gates NOT auto-overridable |

---

## Operator Intervention Points

### Phase Gates (Steps 3, 6, 9)

- **With auto_approve=true**: Automatically approved, logged to ledger
- **With auto_approve=false**: Prompts for `APPROVE` on stdin

### Risk Gates (Any Step)

- **Always require manual approval** (policy enforced in code)
- Triggered when:
  - Weighted open questions exceed threshold
  - QA agent flags CRITICAL/BLOCKER issues
- Prompt shows: `⚠️ RISK GATE: <reason>`

### What to Check Before Approving Risk Gates

1. Review the agent's output markdown file
2. Check `*_open_questions.json` for severity breakdown
3. If uncertain, type anything other than `APPROVE` to stop

---

## Quick Reference Commands

```bash
# View latest run report
python3 scripts/run_report.py --latest

# Compare runs (detect regressions)
python3 scripts/run_diff.py <RUN_A> <RUN_B>

# Export bundle for handoff
python3 scripts/bundle_export.py --latest
```

---

## Convenience Scripts

| Script | Profile | Auto-Approve | Use Case |
|--------|---------|--------------|----------|
| `./scripts/run_dev.sh` | dev | Yes | Local development |
| `./scripts/run_ci.sh` | ci | Phase gates only | Regression testing |
| `./scripts/run_prod.sh` | prod | No | Client deliverables |
