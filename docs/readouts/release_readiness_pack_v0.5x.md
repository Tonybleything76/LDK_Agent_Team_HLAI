# Release Readiness Pack v0.5x

**Generated:** 2026-02-12T15:53:50-06:00  
**Head Commit:** `685236b fix(governance): attribute auto-approvals to profile vs CLI`  
**System Version:** 0.5.2  
**Final Status:** ❌ **FAIL**

---

## Executive Summary

**Release Recommendation:** 🛑 **HOLD**

The repository has **3 critical blockers** preventing release:
1. **Pytest failures** (3 tests failing)
2. **API keys not visible** (operator must source .env)
3. **Ledger events missing** (preflight/postflight not found in governance runs)

---

## Repository State

### Tracked Files
✅ **CLEAN** - No tracked modifications detected

### Untracked Files
- **Count:** 52 untracked files/directories
- **Top-level:** adk/, cli/, docs/, governance/, inputs/, knowledge/, orchestrator/, prompts/, schemas/, scripts/, services/, tests/, utils/

---

## Version Identity

| Attribute | Value |
|-----------|-------|
| Head Commit | `685236b` |
| Commit Subject | fix(governance): attribute auto-approvals to profile vs CLI |
| run_config.json version | 0.5.2 |
| Default Provider | openai |

**Note:** Task naming uses "v0.5x" while system version is "0.5.2" - minor discrepancy, not a blocker.

---

## Test Results

### Pytest Summary
❌ **FAILED**

```
3 failed, 65 passed, 2 warnings, 1 error in 3.37s
```

**Failing Tests:**
1. `test_bundle_export.py::test_collect_run_files_includes_dist` - dist artifacts not included in bundle
2. `test_config_integrity.py::test_media_producer_configuration` - media_producer_agent missing from config
3. `test_offline_integration.py::test_offline_media_delivery_integration` - dist/ not in bundle arcnames

**Import Error:**
- `test_proposal_create.py` - cannot import `proposal_create` from `cli.commands`

---

## Governance Durability Evidence

### Multi-Run Proof (3 runs)

| Run ID | Profile | Status | Steps | Config Hash | Inputs Hash | Audit OK | Ledger OK |
|--------|---------|--------|-------|-------------|-------------|----------|-----------|
| 20260212_212221 | dev | completed | 3 | 073b6ca8... | be857c21... | ✅ | ❌ |
| 20260212_212233 | staging | completed | 3 | 073b6ca8... | be857c21... | ✅ | ❌ |
| 20260212_212256 | staging | completed | 4 | 073b6ca8... | be857c21... | ✅ | ❌ |

**Audit Summary Validation:**
- ✅ All runs have `run_id` populated
- ✅ All runs have `gate_manifest` with planned_phase_gates
- ✅ Phase gates encountered correctly (step 3 for all runs)
- ✅ Risk gates triggered and recorded in audit
- ✅ Approval counts accurate (auto vs manual)

**Ledger Validation:**
- ❌ **FAIL:** preflight_passed events NOT FOUND for any run
- ❌ **FAIL:** postflight_passed events NOT FOUND for any run
- ✅ **PASS:** No `cli_flag` approval_source detected (0 occurrences across all runs)

**Possible Cause:** Ledger schema change or event name mismatch. The audit summaries are complete and correct, but ledger events are missing.

---

## Risk Gate Attribution Proof

**Run ID:** 20260212_211808

**Audit Summary:**
- ✅ 2 risk gates triggered (step 1: open_questions_threshold, step 7: qa_critical)
- ✅ Both marked as `approved_mode: manual` (correct for staging profile with auto_override=false)
- ✅ Metadata shows `risk_auto_override: false` correctly

**Ledger Validation:**
- ❌ **FAIL:** No risk_gate_triggered events found in ledger
- ⚠️ **WARNING:** Ledger has 1080 total lines but no events for this run_id with event_type containing "risk_gate"

**Attribution Correctness:**
- ✅ Audit summary shows correct attribution (profile-based, not cli_flag)
- ✅ No `cli_flag` approval_source in ledger for this run (0 occurrences)

---

## Environment Prerequisites

**Dotenv Usage:** NO_DOTENV detected in `scripts/run_pipeline.py`

**Operator Steps Required:**
```bash
set -a
source .env
set +a
```

**API Key Visibility (Current Session):**
- ❌ OPENAI_API_KEY: MISSING
- ❌ PERPLEXITY_API_KEY: MISSING
- ❌ ANTHROPIC_API_KEY: MISSING

**Note:** Keys must be sourced before running live provider tests.

---

## What is Proven

✅ **Repository Cleanliness:** Tracked files are clean  
✅ **Governance Attribution:** Auto-approvals correctly attributed to profile (not cli_flag)  
✅ **Audit Completeness:** All audit_summary.json files are self-contained with run_id and gate_manifest  
✅ **Multi-Run Stability:** 3 sequential runs with different profiles completed successfully  
✅ **Risk Gate Logic:** Risk gates trigger correctly based on thresholds and profile settings  
✅ **No CLI Flag Regression:** Zero `approval_source == "cli_flag"` detected across all runs  

---

## What is NOT Proven

❌ **Live Provider Cost:** No live runs with actual API calls (all dry_run)  
❌ **Live Provider Latency:** No timing data for real LLM calls  
❌ **Model Quality:** No validation of actual LLM output quality  
❌ **Production Profile Differences:** Only dev/staging profiles tested, not production  
❌ **Ledger Event Completeness:** preflight/postflight events missing from ledger  
❌ **Bundle Export:** Failing tests indicate dist/ artifacts not included  
❌ **Media Producer Integration:** Config integrity test failing  

---

## Release Blockers

### CRITICAL
1. **Pytest Failures (3 tests)**
   - `test_bundle_export` - dist artifacts not included
   - `test_config_integrity` - media_producer_agent missing
   - `test_offline_integration` - dist/ not in bundle

2. **API Keys Not Visible**
   - Operator must source .env before live runs
   - Current session has no keys loaded

3. **Ledger Events Missing**
   - preflight_passed / postflight_passed not found
   - Possible schema change or event name mismatch
   - Impacts audit trail completeness

### MINOR
4. **Version Mismatch**
   - Task naming: "v0.5x"
   - run_config.json: "0.5.2"
   - Not a blocker, just documentation inconsistency

---

## Recommendation

🛑 **DO NOT PROMOTE TO PRODUCTION**

**Required Actions Before Release:**
1. Fix 3 failing pytest tests (bundle_export, config_integrity, offline_integration)
2. Investigate and restore ledger preflight/postflight events
3. Ensure .env is sourced for live provider runs
4. Re-run full test suite and confirm 100% pass rate
5. Execute at least one live provider smoke test (step 1 only) to validate API key visibility

**After Fixes:**
- Re-run governance durability proof
- Verify ledger events are present
- Confirm pytest 100% pass
- Generate new release readiness pack

---

## Appendix: Governance Run Details

### Run 20260212_212221 (dev profile)
- auto_approve: true
- risk_auto_override: true
- open_questions_threshold: 3
- Phase gates: [3, 6, 9], encountered: [3]
- Risk gates: 2 (step 1 auto-overridden, step 1 threshold exceeded)
- Approvals: manual=0, auto=2

### Run 20260212_212233 (staging profile)
- auto_approve: true
- risk_auto_override: false
- open_questions_threshold: 5
- Phase gates: [3, 6, 9], encountered: [3]
- Risk gates: 2 (step 1 manual, step 1 threshold exceeded)
- Approvals: manual=1, auto=1

### Run 20260212_212256 (staging profile)
- auto_approve: true
- risk_auto_override: false
- open_questions_threshold: 5
- Phase gates: [3, 6, 9], encountered: [3]
- Risk gates: 2 (step 1 manual, step 1 threshold exceeded)
- Approvals: manual=1, auto=1

---

**End of Report**
