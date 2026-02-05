#!/usr/bin/env bash
# =============================================================================
# Local CI Validation Script
# =============================================================================
# This script runs the COMPLETE validation suite that would run in CI.
# Run this before committing changes or starting team testing.
#
# What it does (in order):
#   1. Preflight Check - Validates config, prompts, schemas
#   2. Golden Run - Regression test with deterministic fixtures
#   3. Run-Diff Enforcement - Validates governance policy compliance
#   4. Failure Injection - Verifies run_diff catches regressions
#
# Exit codes:
#   0 = All checks passed (safe to proceed)
#   1 = One or more checks failed (fix before proceeding)
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "🚀 Running Local CI Validation Suite..."
echo "   This will take ~60 seconds"
echo ""

# Track overall status
FAILED=0

# -----------------------------------------------------------------------------
# 1. Preflight Check
# -----------------------------------------------------------------------------
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1/4: Preflight Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "WHY: Validates config files, prompts, and schemas are correct"
echo "WHAT IT CHECKS:"
echo "  • config/run_config.json exists and is valid JSON"
echo "  • All agent prompts exist and contain required variables"
echo "  • No placeholder text (TODO, TBD, [Missing) in prompts"
echo "  • Schemas are valid JSON"
echo "  • Output directories are writable"
echo ""

if python3 scripts/preflight_check.py; then
    echo "✅ Preflight check passed"
else
    echo "❌ Preflight check failed"
    FAILED=1
fi
echo ""

# -----------------------------------------------------------------------------
# 2. Golden Run Verification
# -----------------------------------------------------------------------------
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2/4: Golden Run Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "WHY: Runs the pipeline with known inputs and verifies expected behavior"
echo "WHAT IT CHECKS:"
echo "  • Pipeline completes successfully with test fixtures"
echo "  • Governance profile is 'ci'"
echo "  • Auto-approvals ONLY at phase gates 3, 6, 9"
echo "  • Risk gates require manual approval (simulated in CI)"
echo "  • No unexpected errors or warnings"
echo ""

if python3 scripts/verify_golden_run.py; then
    echo "✅ Golden run verification passed"
else
    echo "❌ Golden run verification failed"
    FAILED=1
fi
echo ""

# -----------------------------------------------------------------------------
# 3. Failure Injection Test
# -----------------------------------------------------------------------------
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3/4: Failure Injection Regression Test"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "WHY: Verifies that run-diff enforcement actually catches regressions"
echo "WHAT IT DOES:"
echo "  • Runs golden run"
echo "  • Injects a CRITICAL failure into the output"
echo "  • Runs verify_run_diff.py against the modified output"
echo "  • Asserts that verify_run_diff.py FAILS (catches the regression)"
echo ""

if python3 scripts/verify_failure_injection.py; then
    echo "✅ Failure injection test passed (run_diff correctly caught regression)"
else
    echo "❌ Failure injection test failed (run_diff did not catch regression)"
    FAILED=1
fi
echo ""

# -----------------------------------------------------------------------------
# 4. Full Release Check
# -----------------------------------------------------------------------------
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4/4: Full Release Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "WHY: Final validation that all components work together"
echo "WHAT IT CHECKS:"
echo "  • Preflight check passes"
echo "  • Golden run passes"
echo "  • Run report can be generated and parsed"
echo ""

if python3 scripts/release_check.py; then
    echo "✅ Release check passed"
else
    echo "❌ Release check failed"
    FAILED=1
fi
echo ""

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $FAILED -eq 0 ]; then
    echo "✅ ALL CHECKS PASSED"
    echo ""
    echo "Your repository is ready for team testing!"
    echo ""
    echo "Next steps:"
    echo "  1. Review inputs/business_brief.md and inputs/sme_notes.md"
    echo "  2. Run: ./scripts/run_dev.sh (quick sanity check)"
    echo "  3. Run: ./scripts/run_prod.sh --dry_run (test manual approvals)"
    echo ""
    exit 0
else
    echo "❌ SOME CHECKS FAILED"
    echo ""
    echo "Please fix the failures above before proceeding."
    echo ""
    exit 1
fi
