import json
import pytest
from orchestrator.providers.dry_run_provider import DryRunProvider

@pytest.fixture
def provider():
    return DryRunProvider()

def test_storyboard_quality_bar_fields(provider):
    """
    Test that the storyboard step output generator in the dry run provider
    correctly emits the required quality bar fields.
    """
    prompt = "# Storyboard Agent\nSome context here..."
    response = provider.run(prompt)
    data = json.loads(response)
    
    storyboards = data.get("updated_state", {}).get("storyboards", [])
    
    assert len(storyboards) == 6, f"Expected 6 storyboards, got {len(storyboards)}"
    
    for i, module in enumerate(storyboards):
        assert module["module_id"] == f"M{i+1}"
        
        # Check Transformational Dilemma
        assert "transformational_dilemma" in module
        assert module["transformational_dilemma"].startswith("Transformational Dilemma:")
        
        # Check Dialogue Prompts
        dialogue = module.get("dialogue_prompts", [])
        assert len(dialogue) == 2
        assert dialogue[0].startswith("Dialogue Prompt 1:")
        assert dialogue[1].startswith("Dialogue Prompt 2:")
        
        # Check Governance Anchor
        assert "governance_anchor" in module
        assert module["governance_anchor"].startswith("Governance Anchor:")
        
        # Check Behavior Signal
        assert "level_3_behavior_signal" in module
        assert module["level_3_behavior_signal"].startswith("Level 3 Behavior Signal:")
