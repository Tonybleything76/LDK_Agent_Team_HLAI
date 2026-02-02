import json
import re
from typing import Dict, Any


class ValidationError(Exception):
    """Raised when JSON parsing or validation fails."""
    pass


def extract_json_object(raw_text: str) -> str:
    """
    Extract JSON object from LLM response that may contain code fences or commentary.
    
    Handles common patterns:
    - Code fences: ```json ... ``` or ``` ... ```
    - Leading/trailing commentary
    - Bare JSON objects
    
    Args:
        raw_text: Raw text from LLM response
        
    Returns:
        Extracted JSON string
        
    Raises:
        ValidationError: If no JSON object can be extracted
    """
    if not raw_text or not raw_text.strip():
        raise ValidationError("Empty response received")
    
    text = raw_text.strip()
    
    # Pattern 1: Code fences with optional language specifier
    # Matches ```json\n{...}\n``` or ```\n{...}\n```
    fence_pattern = r'```(?:json)?\s*\n(.*?)\n```'
    fence_match = re.search(fence_pattern, text, re.DOTALL)
    
    if fence_match:
        return fence_match.group(1).strip()
    
    # Pattern 2: Find first { and last } to extract JSON object
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return text[first_brace:last_brace + 1]
    
    # No JSON found
    raise ValidationError(
        f"No JSON object found in response. "
        f"Response snippet: {text[:300]}..."
    )


def parse_json_object(raw_text: str) -> Dict[str, Any]:
    """
    Parse JSON object from LLM response with robust extraction and error handling.
    
    Args:
        raw_text: Raw text from LLM response
        
    Returns:
        Parsed JSON dictionary
        
    Raises:
        ValidationError: If extraction or parsing fails with helpful error message
    """
    try:
        # Extract JSON from potentially wrapped response
        json_str = extract_json_object(raw_text)
        
        # Parse the extracted JSON
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            # Provide helpful error with snippet
            snippet = json_str[:300] if len(json_str) > 300 else json_str
            raise ValidationError(
                f"PARSE_ERROR: Failed to parse JSON: {e}\n"
                f"Extracted content snippet:\n{snippet}\n"
                f"{'...' if len(json_str) > 300 else ''}"
            )
            
    except ValidationError:
        # Re-raise our own ValidationErrors
        raise
    except Exception as e:
        # Catch any other unexpected errors
        snippet = raw_text[:300] if len(raw_text) > 300 else raw_text
        raise ValidationError(
            f"PARSE_ERROR: Unexpected error during JSON extraction: {e}\n"
            f"Raw response snippet:\n{snippet}\n"
            f"{'...' if len(raw_text) > 300 else ''}"
        )
