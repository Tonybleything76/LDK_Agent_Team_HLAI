import pytest
from scripts.run_pilot_acceptance import evaluate_gates

def test_evaluate_gates_success():
    report = {
        "overall_stability_score": 90,
        "structure_stability_score": 90,
        "objectives_per_run": [12, 12],
        "modules_per_run": [6, 6],
        "storyboard_per_run": [6, 6],
        "structure_diffs_summary": []
    }
    passed, failures, warnings = evaluate_gates(
        report=report,
        course_slug="test-course",
        min_structure_stability=80,
        require_quality=False,
        min_objectives=12,
        expected_modules=6
    )
    assert passed is True
    assert len(failures) == 0

def test_evaluate_gates_success_with_allowed_drift():
    report = {
        "overall_stability_score": 70, # soft warn
        "structure_stability_score": 90,
        "objectives_per_run": [12, 12],
        "modules_per_run": [6, 6],
        "storyboard_per_run": [6, 6],
        "structure_diffs_summary": [
            {"field": "key_concepts_count", "module_id": "M1", "runs": [4, 5]}
        ]
    }
    passed, failures, warnings = evaluate_gates(
        report=report,
        course_slug="test-course",
        min_structure_stability=80,
        require_quality=False,
        min_objectives=12,
        expected_modules=6,
        require_empty_diffs=False
    )
    assert passed is True
    assert len(failures) == 0
    assert len(warnings) >= 2 # 1 for depth drift, 1 for overall_stability_score
    assert any("Allowed depth drift" in w for w in warnings)
    assert any("overall_stability_score 70 is below threshold 80" in w for w in warnings)

def test_evaluate_gates_fail_strict_diffs():
    report = {
        "overall_stability_score": 90,
        "structure_stability_score": 90,
        "objectives_per_run": [12, 12],
        "modules_per_run": [6, 6],
        "storyboard_per_run": [6, 6],
        "structure_diffs_summary": [
            {"field": "key_concepts_count", "module_id": "M1", "runs": [4, 5]}
        ]
    }
    passed, failures, warnings = evaluate_gates(
        report=report,
        course_slug="test-course",
        min_structure_stability=80,
        require_quality=False,
        min_objectives=12,
        expected_modules=6,
        require_empty_diffs=True
    )
    assert passed is False
    assert len(failures) > 0
    assert any("structure_diffs detected" in f for f in failures)

def test_evaluate_gates_fail_objectives():
    report = {
        "overall_stability_score": 90,
        "structure_stability_score": 90,
        "objectives_per_run": [0, 12], # FAIL
        "modules_per_run": [6, 6],
        "storyboard_per_run": [6, 6],
        "structure_diffs_summary": []
    }
    passed, failures, warnings = evaluate_gates(
        report=report,
        course_slug="test-course",
        min_structure_stability=80,
        require_quality=False,
        min_objectives=12,
        expected_modules=6
    )
    assert passed is False
    assert any("objectives_count failed" in f for f in failures)

def test_evaluate_gates_fail_modules():
    report = {
        "overall_stability_score": 90,
        "structure_stability_score": 90,
        "objectives_per_run": [12, 12],
        "modules_per_run": [6, 5], # FAIL
        "storyboard_per_run": [6, 6],
        "structure_diffs_summary": []
    }
    passed, failures, warnings = evaluate_gates(
        report=report,
        course_slug="test-course",
        min_structure_stability=80,
        require_quality=False,
        min_objectives=12,
        expected_modules=6
    )
    assert passed is False
    assert any("modules_count failed" in f for f in failures)

def test_evaluate_gates_fail_storyboard():
    report = {
        "overall_stability_score": 90,
        "structure_stability_score": 90,
        "objectives_per_run": [12, 12],
        "modules_per_run": [6, 6],
        "storyboard_per_run": [6, 5], # FAIL
        "structure_diffs_summary": []
    }
    passed, failures, warnings = evaluate_gates(
        report=report,
        course_slug="test-course",
        min_structure_stability=80,
        require_quality=False,
        min_objectives=12,
        expected_modules=6
    )
    assert passed is False
    assert any("storyboard_module_count failed" in f for f in failures)

def test_evaluate_gates_fail_missing_key():
    report = {
        "overall_stability_score": 90,
        "structure_stability_score": 90,
        "objectives_per_run": [12, 12],
        "modules_per_run": [6, 6],
        # "storyboard_per_run" missing
    }
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        evaluate_gates(
            report=report,
            course_slug="test-course",
            min_structure_stability=80,
            require_quality=False,
            min_objectives=12,
            expected_modules=6
        )
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1
