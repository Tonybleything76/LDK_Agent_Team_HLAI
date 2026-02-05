#!/usr/bin/env bash
# =============================================================================
# Team Test Cycle - v0.5.1 Operator Testing
# =============================================================================
# Runs a complete 3-step test sequence:
#   1. Preflight checks
#   2. Golden run (dev profile - captures baseline)
#   3. Failure injection (verifies error handling)
#
# Exit codes:
#   0 = All tests passed
#   1 = Preflight failed
#   2 = Golden run failed
#   3 = Failure injection failed
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track overall status
OVERALL_STATUS=0

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 v0.5.1 Team Test Cycle"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd "$PROJECT_ROOT"

# =============================================================================
# Step 1: Preflight Checks
# =============================================================================
echo -e "${BLUE}[1/3] Running preflight checks...${NC}"
if python3 scripts/preflight_check.py; then
    echo -e "${GREEN}✅ Preflight checks passed${NC}"
else
    echo -e "${RED}❌ Preflight checks failed${NC}"
    exit 1
fi
echo ""

# =============================================================================
# Step 2: Golden Run (Baseline)
# =============================================================================
echo -e "${BLUE}[2/3] Running golden baseline (dev profile)...${NC}"
if python3 scripts/verify_golden_run.py; then
    echo -e "${GREEN}✅ Golden run completed successfully${NC}"
    
    # Extract RUN_ID from verify_golden_run output
    # The script should emit "RUN_ID=<run_id>" to stdout
    GOLDEN_RUN_OUTPUT=$(python3 scripts/verify_golden_run.py 2>&1 || true)
    GOLDEN_RUN_ID=$(echo "$GOLDEN_RUN_OUTPUT" | grep "RUN_ID=" | cut -d'=' -f2 | tr -d ' ')
    
    if [ -n "$GOLDEN_RUN_ID" ]; then
        echo -e "${GREEN}   Baseline RUN_ID: $GOLDEN_RUN_ID${NC}"
    else
        echo -e "${YELLOW}   ⚠️  Could not extract RUN_ID (non-fatal)${NC}"
    fi
else
    echo -e "${RED}❌ Golden run failed${NC}"
    exit 2
fi
echo ""

# =============================================================================
# Step 3: Failure Injection
# =============================================================================
echo -e "${BLUE}[3/3] Running failure injection tests...${NC}"
if python3 scripts/verify_failure_injection.py; then
    echo -e "${GREEN}✅ Failure injection tests passed${NC}"
else
    echo -e "${RED}❌ Failure injection tests failed${NC}"
    exit 3
fi
echo ""

# =============================================================================
# Summary
# =============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "  1. Review test outputs in outputs/ directory"
echo "  2. Check governance ledger: governance/run_ledger.jsonl"
echo "  3. Generate report: python3 scripts/run_report.py --latest"
echo ""

exit 0
