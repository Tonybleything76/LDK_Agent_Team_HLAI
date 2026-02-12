import json
import os
from pathlib import Path

def test_media_producer_configuration():
    """
    Verify that the Media Producer Agent is explicitly registered in the run configuration.
    This ensures that the agent is discoverable and will be invoked by the orchestrator.
    """
    config_path = Path("config/run_config.json")
    assert config_path.exists(), "config/run_config.json must exist"

    with open(config_path, "r") as f:
        config = json.load(f)

    agents = config.get("agents", [])
    agent_names = [a["name"] for a in agents]

    assert "media_producer_agent" in agent_names, "media_producer_agent must be present in config/run_config.json"

    # Find the media producer config
    mp_config = next(a for a in agents if a["name"] == "media_producer_agent")

    # validation
    assert "prompt_path" in mp_config, "media_producer_agent must have a prompt_path"
    assert "gate" in mp_config, "media_producer_agent must have a gate setting"
    
    # Prompt file existence check
    prompt_path = Path(mp_config["prompt_path"])
    assert prompt_path.exists(), f"Media Producer prompt file missing at {prompt_path}"
