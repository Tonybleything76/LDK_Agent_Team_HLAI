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
        
        # Check Transformational Trigger
        trigger = module.get("transformational_trigger", {})
        assert "assumption_to_challenge" in trigger
        assert "disorienting_prompt" in trigger
        assert "reframed_belief" in trigger
        
        # Check Dialogue Density
        dialogue = module.get("dialogue_prompts", {})
        # Note: exactly 2 prompts required
        assert len(dialogue.keys()) == 2
        assert "reflection_prompt" in dialogue
        assert "peer_or_manager_prompt" in dialogue
        
        # Check Governance Anchor
        anchor = module.get("governance_anchor", {})
        assert "verification_step" in anchor
        assert "policy_boundary_callout" in anchor
        assert "human_accountability_line" in anchor
        assert anchor["human_accountability_line"] == "You are the publisher/owner"
        
        # Check Behavior Signal
        assert "on_the_job_behavior" in module
        assert "manager_observable_signal" in module
