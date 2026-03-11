#!/usr/bin/env python3
"""
Golden Run Gate — smoke test for the full 10-agent pipeline using the dry_run provider.

Verifies that:
  1. The pipeline completes all 10 steps without error
  2. Each step produces a non-empty deliverable_markdown
  3. The audit summary is generated

Run with:
  PROVIDER=dry_run AUTO_APPROVE=1 python3 scripts/verify_golden_run.py

Used by CI to catch regressions before merge.
"""

import os
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Force dry_run + auto-approve for golden gate
os.environ.setdefault("PROVIDER", "dry_run")
os.environ.setdefault("AUTO_APPROVE", "1")

from orchestrator.root_agent import run_pipeline  # noqa: E402


def _find_latest_run_dir() -> "Path | None":
    outputs = PROJECT_ROOT / "outputs"
    if not outputs.exists():
        return None
    dirs = sorted(
        (d for d in outputs.iterdir() if d.is_dir()),
        key=lambda d: d.name,
        reverse=True,
    )
    return dirs[0] if dirs else None


def main() -> None:
    print("=" * 60)
    print("GOLDEN RUN GATE — dry_run smoke test")
    print("=" * 60)

    run_pipeline(
        config_overrides={
            "approval": {
                "risk_gate_escalation": {
                    "enabled": False,
                    "auto_override": True,
                }
            }
        }
    )

    # ── Assertions ────────────────────────────────────────────────────────────
    run_dir = _find_latest_run_dir()
    assert run_dir is not None, "No run directory found in outputs/"

    # Manifest must exist and show completed
    manifest_path = run_dir / "run_manifest.json"
    assert manifest_path.exists(), f"run_manifest.json missing in {run_dir}"
    manifest = json.loads(manifest_path.read_text())
    assert manifest.get("status") == "completed", (
        f"Expected status=completed, got {manifest.get('status')}"
    )

    # All 10 agent deliverables must exist and be non-empty
    agent_names = [
        "strategy_lead_agent",
        "learner_research_agent",
        "learning_architect_agent",
        "instructional_designer_agent",
        "assessment_designer_agent",
        "storyboard_agent",
        "media_producer_agent",
        "qa_agent",
        "change_management_agent",
        "operations_librarian_agent",
    ]
    for step, name in enumerate(agent_names, start=1):
        md_path = run_dir / f"{step:02d}_{name}.md"
        assert md_path.exists(), f"Missing deliverable: {md_path}"
        content = md_path.read_text().strip()
        assert len(content) >= 50, f"Deliverable too short ({len(content)} chars): {md_path}"

    # Audit summary must be generated
    audit_path = run_dir / "audit_summary.json"
    assert audit_path.exists(), f"audit_summary.json missing in {run_dir}"

    print("\n✅ GOLDEN RUN GATE PASSED")
    print(f"   Run dir: {run_dir}")


if __name__ == "__main__":
    main()
