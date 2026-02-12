import re
from typing import Dict, Any, List

def validate_human_ai_framing(content: str) -> Dict[str, Any]:
    """
    Validates that the content explicitly frames Human vs AI roles.
    
    checks for:
    - "Human Decision Boundary"
    - "AI Capability Boundary" or "What AI Cannot Do"
    - "Failure Mode" or "When AI is Wrong"
    
    Returns:
        Dict with keys:
            - passed (bool)
            - errors (List[str])
    """
    errors = []
    
    # Define required semantic concepts and their flexible string variations
    required_concepts = {
        "Human Decision Boundary": [
            r"Human Decision Boundary",
            r"Human Application",
            r"Role of the Human",
            r"Where the Human Steps In",
            r"Human Judgment",
            r"Human in the loop"
        ],
        "AI Capability Boundary": [
            r"AI Capability Boundary",
            r"AI Limitations",
            r"What AI Cannot Do",
            r"System Limitations",
            r"AI Boundary"
        ],
        "Failure Mode / Risk": [
            r"Failure Mode",
            r"When AI is Wrong",
            r"Risk of Hallucination",
            r"Reference Check",
            r"Verification needed",
            r"Common Pitfalls"
        ]
    }
    
    passed_concepts = []
    
    for concept_name, patterns in required_concepts.items():
        found = False
        for p in patterns:
            if re.search(p, content, re.IGNORECASE):
                found = True
                break
        
        if found:
            passed_concepts.append(concept_name)
        else:
            errors.append(f"Missing '{concept_name}' or equivalent framing.")
            
    return {
        "passed": len(errors) == 0,
        "errors": errors,
        "found_concepts": passed_concepts
    }
