#!/usr/bin/env bash
# =============================================================================
# Dev-Mode Pipeline Run
# =============================================================================
# Profile: dev
# Behavior:
#   - Dry-run mode (no API costs)
#   - Relaxed risk thresholds (threshold=3)
#   - Auto-approves all phase gates
#   - Risk gates auto-override enabled
#
# Use this for: Local development, rapid iteration, testing prompts
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🧪 Running Dev-mode pipeline..."
echo "   Profile: dev"
echo "   Provider: dry_run"
echo "   Auto-Approve: YES (all gates)"
echo "   Risk Threshold: 3 (relaxed)"
echo ""

cd "$PROJECT_ROOT"
python3 scripts/run_pipeline.py --dry_run --governance_profile dev --auto_approve

echo ""
echo "📋 Post-run commands:"
echo "   python3 scripts/run_report.py --latest           # View run report"
echo "   python3 scripts/bundle_export.py --latest        # Create export bundle"
