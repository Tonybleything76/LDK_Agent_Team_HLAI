#!/usr/bin/env bash
# =============================================================================
# CI-Mode Pipeline Run
# =============================================================================
# Profile: ci
# Behavior:
#   - Deterministic (dry_run mode)
#   - Auto-approves phase gates at steps 3, 6, 9
#   - Risk gates require manual approval (cannot be auto-approved by policy)
#
# Use this for: Regression testing, CI validation, baseline generation
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔬 Running CI-mode pipeline..."
echo "   Profile: ci"
echo "   Provider: dry_run"
echo "   Auto-Approve Phase Gates: YES (steps 3, 6, 9)"
echo "   Risk Gates: Manual approval required (policy enforced)"
echo ""

cd "$PROJECT_ROOT"
python3 scripts/run_pipeline.py --dry_run --governance_profile ci --auto_approve

echo ""
echo "📋 Post-run commands:"
echo "   python3 scripts/run_report.py --latest           # View run report"
echo "   python3 scripts/bundle_export.py --latest        # Create export bundle"
