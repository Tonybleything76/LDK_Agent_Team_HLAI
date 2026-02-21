"""
test_objective_count_and_storyboard_alignment.py

Verifies two structural invariants using dry_run (no API cost):
  1. objectives_count > 0 — Learning Architect emits exactly 2 per module (6×2 = 12)
  2. Storyboard module count == 6 — Storyboard does not collapse or omit modules

These guard against regression of:
  - objectives_per_run = [0,0,0] caused by missing `objectives` key in LA schema
  - QA CRITICAL "5 vs 6 modules" caused by storyboard re-deriving structure
"""

import json
import pytest
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers — import the consistency script's analyze_structure function.
# ---------------------------------------------------------------------------
import scripts.run_content_consistency as run_consistency
from orchestrator.providers.dry_run_provider import DryRunProvider


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def dry_run_la_state(tmp_path) -> dict:
    """
    Parse the DryRunProvider's learning architect stub and write it to a
    temp folder so analyze_structure() can read it as it would a real run.
    """
    provider = DryRunProvider()
    raw = provider._create_learning_architect_stub()
    state = json.loads(raw)

    run_path = tmp_path / "run_dry"
    run_path.mkdir()

    # Wrap in the format run_pipeline.py writes to disk
    disk_state = {
        "deliverable_markdown": state.get("deliverable_markdown", ""),
        "updated_state": state.get("updated_state", {}),
        "open_questions": state.get("open_questions", []),
    }
    la_file = run_path / "03_learning_architect_agent_state.json"
    la_file.write_text(json.dumps(disk_state))

    return {"path": run_path, "state": state}


@pytest.fixture
def dry_run_storyboard_state(tmp_path) -> dict:
    """
    Build a synthetic storyboard state that models a correctly aligned
    6-module storyboard as required by the updated storyboard prompt.

    This fixture represents the minimum-contract output the storyboard agent
    MUST produce after the prompt fix.
    """
    storyboards = [
        {
            "module_id": f"M{i}",
            "screen_id": i,
            "visual_layout": "Content Slide",
            "media_asset_description": f"Visual for module M{i}",
            "alt_text": f"Module M{i} slide illustration",
            "dev_notes": "Auto-generated stub",
        }
        for i in range(1, 7)  # exactly 6 entries, M1–M6
    ]

    run_path = tmp_path / "run_storyboard"
    run_path.mkdir()

    sb_file = run_path / "06_storyboard_agent_state.json"
    sb_file.write_text(json.dumps({
        "deliverable_markdown": "# Visual Storyboard\n\n(stub)",
        "updated_state": {"storyboards": storyboards},
        "open_questions": [],
    }))

    return {"path": run_path, "storyboards": storyboards}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestObjectiveCount:
    """Verify Learning Architect stub emits objectives and they are counted."""

    def test_dry_run_la_stub_has_objectives_key(self, dry_run_la_state):
        """Each module in the dry-run stub must have an 'objectives' key."""
        updated_state = dry_run_la_state["state"]["updated_state"]
        modules = updated_state["curriculum"]["modules"]
        assert len(modules) == 6, f"Expected 6 modules, got {len(modules)}"
        for mod in modules:
            assert "objectives" in mod, (
                f"Module {mod.get('module_id')} is missing 'objectives' key. "
                "Check dry_run_provider.make_module()."
            )

    def test_dry_run_la_stub_has_exactly_2_objectives_per_module(self, dry_run_la_state):
        """Each module must have exactly 2 objective strings."""
        modules = dry_run_la_state["state"]["updated_state"]["curriculum"]["modules"]
        for mod in modules:
            objs = mod.get("objectives", [])
            assert len(objs) == 2, (
                f"Module {mod.get('module_id')} has {len(objs)} objectives; expected 2."
            )
            for obj in objs:
                assert isinstance(obj, str) and len(obj) > 5, (
                    f"Objective '{obj}' in {mod.get('module_id')} is not a valid string."
                )

    def test_objectives_count_is_12_via_analyze_structure(self, dry_run_la_state):
        """
        analyze_structure() should report objectives_count == 12
        when modules have the objectives key (6 modules × 2 objectives).
        """
        run_data = {"path": dry_run_la_state["path"]}
        metrics = run_consistency.analyze_structure(run_data)

        assert metrics["objectives_count"] > 0, (
            "objectives_count is 0 — the consistency script is not reading "
            "'objectives' from modules, or the data is missing the key."
        )
        assert metrics["objectives_count"] == 12, (
            f"Expected objectives_count=12 (6×2), got {metrics['objectives_count']}."
        )
        assert metrics["modules_count"] == 6


class TestStoryboardModuleAlignment:
    """Verify storyboard preserves the 6-module structure."""

    def test_storyboard_has_6_module_entries(self, dry_run_storyboard_state):
        """Storyboard updated_state.storyboards must have exactly 6 entries."""
        storyboards = dry_run_storyboard_state["storyboards"]
        assert len(storyboards) == 6, (
            f"Storyboard has {len(storyboards)} entries; expected 6. "
            "The storyboard agent may be collapsing or re-deriving module structure."
        )

    def test_storyboard_entries_have_module_ids(self, dry_run_storyboard_state):
        """Each storyboard entry must carry a module_id field."""
        for entry in dry_run_storyboard_state["storyboards"]:
            assert "module_id" in entry, (
                f"Storyboard entry {entry.get('screen_id')} is missing 'module_id'."
            )

    def test_storyboard_module_ids_are_sequential(self, dry_run_storyboard_state):
        """Storyboard entries must reference M1–M6 in exact order."""
        ids = [e["module_id"] for e in dry_run_storyboard_state["storyboards"]]
        expected = [f"M{i}" for i in range(1, 7)]
        assert ids == expected, (
            f"Storyboard module_id sequence is {ids}; expected {expected}."
        )
