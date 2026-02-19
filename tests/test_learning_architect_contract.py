
import pytest
from orchestrator.validation import validate_agent_output, ValidationConfig

# Reusable valid state fixture
@pytest.fixture
def valid_learning_architect_output():
    return {
        "deliverable_markdown": "# Valid Course\n" + "Content " * 50 + "\n" + "More content " * 30, # > 300 chars
        "updated_state": {
            "course_title": "Test Course",
            "course_summary": "A summary.",
            "target_audience": "Learners",
            "business_goal_alignment": ["Goal 1"],
            "belief_behavior_systems": {
                "belief": "B",
                "behaviors": ["B1"],
                "systems_policies_enablers": ["S1"]
            },
            "curriculum": {
                "modules": [
                    {
                        "module_id": f"M{i}",
                        "title": f"Module {i}",
                        "outcome": "Outcome",
                        "key_concepts": ["K1", "K2", "K3", "K4"],
                        "activities": ["A1", "A2"],
                        "checks": [
                            {"type": "mcq", "prompt": "Q?", "success_criteria": ["A"]},
                            {"type": "short_answer", "prompt": "Q?", "success_criteria": ["A"]}
                        ]
                    }
                    for i in range(1, 7) # 6 modules
                ]
            },
            "constraints": {},
            "assumptions": []
        },
        "open_questions": []
    }

def test_valid_schema(valid_learning_architect_output):
    """Test that a fully compliant output passes validation."""
    validate_agent_output("learning_architect_agent", valid_learning_architect_output, ValidationConfig())

def test_missing_required_keys(valid_learning_architect_output):
    """Test failure when required keys are missing from updated_state."""
    del valid_learning_architect_output["updated_state"]["curriculum"]
    with pytest.raises(ValueError, match="missing required key"):
        validate_agent_output("learning_architect_agent", valid_learning_architect_output, ValidationConfig())

def test_module_count_enforcement(valid_learning_architect_output):
    """Test failure when module count is not 6 and no justification provided."""
    modules = valid_learning_architect_output["updated_state"]["curriculum"]["modules"]
    modules.pop() # Now 5
    with pytest.raises(ValueError, match="module count is 5"):
        validate_agent_output("learning_architect_agent", valid_learning_architect_output, ValidationConfig())

def test_valid_module_count_with_justification(valid_learning_architect_output):
    """Test pass when module count != 6 BUT justification is present."""
    modules = valid_learning_architect_output["updated_state"]["curriculum"]["modules"]
    modules.pop() # Now 5
    valid_learning_architect_output["updated_state"]["assumptions"].append("JUSTIFICATION: module_count=5 because reasons")
    validate_agent_output("learning_architect_agent", valid_learning_architect_output, ValidationConfig())

def test_module_structure_fields(valid_learning_architect_output):
    """Test failure when a module is missing required fields."""
    del valid_learning_architect_output["updated_state"]["curriculum"]["modules"][0]["outcome"]
    with pytest.raises(ValueError, match="missing field 'outcome'"):
        validate_agent_output("learning_architect_agent", valid_learning_architect_output, ValidationConfig())

def test_module_id_sequence(valid_learning_architect_output):
    """Test failure when module IDs are not sequential M1..M6."""
    valid_learning_architect_output["updated_state"]["curriculum"]["modules"][1]["module_id"] = "M99"
    with pytest.raises(ValueError, match="expected 'M2'"):
        validate_agent_output("learning_architect_agent", valid_learning_architect_output, ValidationConfig())

def test_check_types(valid_learning_architect_output):
    """Test failure when check type is invalid."""
    valid_learning_architect_output["updated_state"]["curriculum"]["modules"][0]["checks"][0]["type"] = "invalid_type"
    with pytest.raises(ValueError, match="invalid type"):
        validate_agent_output("learning_architect_agent", valid_learning_architect_output, ValidationConfig())

def test_array_bounds(valid_learning_architect_output):
    """Test failure when array lengths are out of bounds."""
    # Key concepts < 4
    valid_learning_architect_output["updated_state"]["curriculum"]["modules"][0]["key_concepts"] = ["K1"]
    with pytest.raises(ValueError, match="out of bounds"):
        validate_agent_output("learning_architect_agent", valid_learning_architect_output, ValidationConfig())
