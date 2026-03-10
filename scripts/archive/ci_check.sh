#!/bin/bash
set -e

echo "🚀 Running Local CI Checks..."

# 1. Preflight Check
echo "---------------------------------------------------"
echo "Wrapper: Running preflight_check.py..."
python3 scripts/preflight_check.py || { echo "❌ Preflight Check Failed"; exit 1; }

# 2. Golden Run Verification
echo "---------------------------------------------------"
echo "Wrapper: Running verify_golden_run.py..."
python3 scripts/verify_golden_run.py || { echo "❌ Golden Run Failed"; exit 1; }

echo "---------------------------------------------------"
echo "✅ All CI checks passed locally."
