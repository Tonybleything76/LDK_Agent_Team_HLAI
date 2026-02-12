import re
from typing import Dict, Any, List

def validate_scenario_density(content: str) -> Dict[str, Any]:
    """
    Validates that the content meets the scenario density requirements:
    1. >= 2 scenario anchor citations (e.g., [Scenario: X])
    2. >= 1 realistic decision/dialogue moment (heuristic check)
    
    Returns:
        Dict with keys:
            - passed (bool)
            - errors (List[str])
            - scenario_count (int)
            - has_dialogue (bool)
    """
    errors = []
    
    # Check 1: Scenario Anchor Citations
    # Pattern looks for [Scenario: <text>]
    anchor_pattern = r"\[Scenario:\s*[^\]]+\]"
    anchors = re.findall(anchor_pattern, content, re.IGNORECASE)
    scenario_count = len(anchors)
    
    if scenario_count < 2:
        errors.append(f"Insufficient scenario density. Found {scenario_count} anchors, required >= 2. (Use '[Scenario: valid_id]')")

    # Check 2: Realistic Decision/Dialogue Check
    # Heuristic: looking for dialogue markers or decision points
    # Dialogue: "Says:", quote marks with speaker attribution
    # Decision: "Decision Point:", "Option A:", "What should you do?"
    
    dialogue_indicators = [
        r'"[^"]+"',  # quoted text
        r'Says:',
        r'Ask:',
        r'Responds:',
        r'Decision Point:',
        r'What should you do\?',
        r'Option [A-C]:',
        r'Choose the best response',
        r'Scenario Update:'
    ]
    
    has_dialogue = False
    for pattern in dialogue_indicators:
        if re.search(pattern, content, re.IGNORECASE):
            has_dialogue = True
            break
            
    if not has_dialogue:
        errors.append("No realistic decision or dialogue moment found. Content must include at least one interaction (dialogue, decision point, or choice).")

    return {
        "passed": len(errors) == 0,
        "errors": errors,
        "scenario_count": scenario_count,
        "has_dialogue": has_dialogue
    }
