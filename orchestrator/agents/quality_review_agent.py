import json
import os
from pathlib import Path
from typing import Dict, Any

from orchestrator.providers import get_provider
from orchestrator.json_tools import parse_json_object

PROMPT_PATH = Path("prompts/quality_review/prompt.md")

class QualityReviewError(Exception):
    pass

def run_quality_review(
    storyboard_state: Dict[str, Any],
    la_state: Dict[str, Any],
    provider_name: str = "openai",
    model: str = None
) -> Dict[str, Any]:
    """
    Runs the Quality Review Agent.
    
    Args:
        storyboard_state: Parsed JSON of the storyboard output
        la_state: Parsed JSON of the learning architect state
        provider_name: AI provider to use
        model: Model name parameter (if the provider handles it via env vars, we might set it)
        
    Returns:
        A dictionary containing the quality review report
    """
    if not PROMPT_PATH.exists():
        raise QualityReviewError(f"Missing prompt: {PROMPT_PATH}")

    with open(PROMPT_PATH, "r") as f:
        prompt_template = f.read()

    # We append the states to the prompt
    # In this pipeline pattern, we can just replace {system_state} if the prompt had it,
    # but since we wrote a prompt that just expects the JSON appended, we do that.
    
    input_data = (
        f"\n\n# Input Data\n\n## Final Storyboard Output\n```json\n"
        f"{json.dumps(storyboard_state, indent=2)}\n```\n\n"
        f"## Learning Architect State\n```json\n"
        f"{json.dumps(la_state, indent=2)}\n```\n"
    )
    
    prompt = prompt_template + input_data

    # Use the provider module
    provider = get_provider(provider_name)
    
    # If model is specified, for OpenAI it is typically read from the OPENAI_MODEL env var
    # we can set it temporarily if needed, though usually the orchestrator handles it.
    if model:
        os.environ["OPENAI_MODEL"] = model

    print(f"Running Quality Review Agent using provider '{provider_name}'...")
    response = provider.run(prompt)
    
    try:
        parsed = parse_json_object(response)
        return parsed
    except Exception as e:
        raise QualityReviewError(f"Failed to parse quality review output: {e}\nRaw response:\n{response}")
