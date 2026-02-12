import pytest
import os
import json
from pathlib import Path
from orchestrator.quality.scenario_validator import validate_scenario_density
from orchestrator.quality.human_ai_validator import validate_human_ai_framing
from orchestrator.quality.quality_score import calculate_quality_score

def test_validate_scenario_density_success():
    content = """
    Here is a lesson.
    [Scenario: scenario_1]
    The user says: "Help me!"
    [Scenario: scenario_2]
    Decision Point: What do you do?
    """
    result = validate_scenario_density(content)
    assert result["passed"] is True
    assert result["scenario_count"] == 2
    assert result["has_dialogue"] is True

def test_validate_scenario_density_failure_count():
    content = """
    Here is a lesson.
    [Scenario: scenario_1]
    Decision Point: What do you do?
    """
    result = validate_scenario_density(content)
    assert result["passed"] is False
    assert "Insufficient scenario density" in result["errors"][0]

def test_validate_scenario_density_failure_dialogue():
    content = """
    Here is a lesson.
    [Scenario: scenario_1]
    [Scenario: scenario_2]
    Just boring text.
    """
    result = validate_scenario_density(content)
    assert result["passed"] is False
    assert "No realistic decision" in result["errors"][0]

def test_validate_human_ai_framing_success():
    content = """
    Human Decision Boundary: The human must decide X.
    AI Capability Boundary: The AI cannot do Y.
    Failure Mode: If the AI hallucinates, verify manually.
    """
    result = validate_human_ai_framing(content)
    assert result["passed"] is True

def test_validate_human_ai_framing_failure():
    content = """
    The AI is great. Use it for everything.
    """
    result = validate_human_ai_framing(content)
    assert result["passed"] is False
    assert len(result["errors"]) >= 1

def test_calculate_quality_score(tmp_path):
    # Setup dummy run dir
    run_dir = tmp_path / "run_test"
    run_dir.mkdir()
    
    # Create artifacts
    (run_dir / "04_instructional_designer_agent.md").write_text("""
    # Learning Objectives
    [Scenario: sc1]
    [Scenario: sc2]
    Says: "Hello"
    Human Decision Boundary: Yes.
    """)
    (run_dir / "05_assessment_designer_agent.md").write_text("""
    # Assessment
    # Practice
    """)
    
    # Mock Course Architecture
    ca = {
        "learning_objects": [
            {"sme_nuances": ["Never trust the bot", "Real world"]}
        ]
    }
    (run_dir / "course_architecture.json").write_text(json.dumps(ca))
    
    result = calculate_quality_score(str(run_dir))
    
    # Assertions
    # Density: 2 anchors * 2 = 4 (capped 30)
    # Nuance: "Never trust the bot" no match? "Real world" no.
    # Structure: Objectives + Assessment + Practice = 3/6? * 20 = 10
    # Anti-generic: 20
    
    assert result["total_score"] > 0
    assert "breakdown" in result
