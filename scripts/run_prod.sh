#!/usr/bin/env bash
# =============================================================================
# Prod-Mode Pipeline Run
# =============================================================================
# Profile: prod
# Behavior:
#   - Real provider (requires API keys unless --dry_run added)
#   - Strict risk thresholds (threshold=8)
#   - Manual approval required at ALL phase gates
#   - Risk gates require manual approval
#
# Use this for: Client deliverables, final runs, production outputs
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🏭 Running Prod-mode pipeline..."
echo "   Profile: prod"
echo "   Auto-Approve: NO (manual approval at each gate)"
echo "   Risk Threshold: 8 (strict)"
echo ""
echo "⚠️  This run requires manual approval at gates 3, 6, and 9."
echo "    Type 'APPROVE' at each gate prompt to continue."
echo ""

cd "$PROJECT_ROOT"

# Check for --dry_run flag passthrough
if [[ "${1:-}" == "--dry_run" ]]; then
    echo "   Provider: dry_run (test mode)"
    python3 scripts/run_pipeline.py --dry_run --governance_profile prod
else
    echo "   Provider: config default (may incur API costs)"
    python3 scripts/run_pipeline.py --governance_profile prod
fi

echo ""
echo "📋 Post-run commands:"
echo "   python3 scripts/run_report.py --latest           # View run report"
echo "   python3 scripts/bundle_export.py --latest        # Create export bundle"
