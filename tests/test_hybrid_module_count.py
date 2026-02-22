import json
import pytest
from orchestrator.providers.dry_run_provider import DryRunProvider
from scripts.run_pilot_acceptance import evaluate_gates

def test_default_no_target_is_6_modules():
    provider = DryRunProvider()
    raw = provider._create_learning_architect_stub("Standard Prompt")
    state = json.loads(raw)
    modules = state["updated_state"]["curriculum"]["modules"]
    
    assert len(modules) == 6, "Expected 6 modules by default"
    assert modules[0]["module_id"] == "M1"
    assert modules[-1]["module_id"] == "M6"

def test_target_3_produces_3_modules():
    provider = DryRunProvider()
    prompt = "Some instructions\nMODULE_COUNT_TARGET: 3\nMore instructions"
    raw = provider._create_learning_architect_stub(prompt)
    state = json.loads(raw)
    modules = state["updated_state"]["curriculum"]["modules"]
    
    assert len(modules) == 3, "Expected exactly 3 modules"
    assert modules[0]["module_id"] == "M1"
    assert modules[-1]["module_id"] == "M3"

def test_storyboard_preserves_dynamic_count():
    """Verify that pilot acceptance gates pass with dynamic 3 module counts"""
    report = {
        "overall_stability_score": 90,
        "structure_stability_score": 90,
        "objectives_per_run": [6, 6],    # exactly 2 objectives per module * 3 modules
        "modules_per_run": [3, 3],
        "storyboard_per_run": [3, 3],
        "structure_diffs_summary": []
    }
    
    passed, failures, warnings = evaluate_gates(
        report=report,
        course_slug="test-hybrid",
        min_structure_stability=80,
        require_quality=False,
        min_objectives=6,              # 3 modules * 2 objectives
        expected_modules=3             # Expected is 3 instead of 6
    )
    
    assert passed is True, f"Gates failed unexpectedly: {failures}"
    assert len(failures) == 0
