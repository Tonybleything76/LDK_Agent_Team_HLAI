"""
Media Specification Utilities

Handles loading, saving, validation, and integrity checking of the Media Specification artifact.
"""

import json
import jsonschema
from pathlib import Path
from typing import Dict, Any, Union

# Define paths relative to this file
ORCHESTRATOR_DIR = Path(__file__).parent
PROJECT_ROOT = ORCHESTRATOR_DIR.parent
SCHEMAS_DIR = PROJECT_ROOT / "schemas"

def _load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a JSON schema from the schemas directory."""
    schema_path = SCHEMAS_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    
    with open(schema_path, "r") as f:
        schema = json.load(f)
        
    return schema

def load_media_spec(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a media spec JSON file.
    
    Args:
        path: Path to the JSON file.
        
    Returns:
        The loaded JSON object.
    """
    with open(path, "r") as f:
        return json.load(f)

def save_media_spec(obj: Dict[str, Any], path: Union[str, Path]) -> None:
    """
    Save a media spec object to JSON.
    
    Args:
        obj: The dictionary to save.
        path: Destination path.
    """
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)

def validate_media_spec(obj: Dict[str, Any]) -> None:
    """
    Validate a media spec object against its schema.
    
    Args:
        obj: The dictionary to validate.
        
    Raises:
        ValueError: If validation fails.
    """
    try:
        schema = _load_schema("media_spec.json")
        jsonschema.validate(instance=obj, schema=schema)
    except jsonschema.ValidationError as e:
        # Create a clean error message
        path = " -> ".join(str(p) for p in e.path) if e.path else "root"
        raise ValueError(f"Validation failed at '{path}': {e.message}")
    except Exception as e:
        raise ValueError(f"Schema validation error: {str(e)}")

def verify_integrity(media_spec: Dict[str, Any], course_architecture: Dict[str, Any]) -> bool:
    """
    Verify that the media spec matches the source course architecture.
    
    Checks:
    1. matching course_id
    2. architecture_hash matches the hash of course_architecture
    
    Args:
        media_spec: Loaded media spec object
        course_architecture: Loaded course architecture object
        
    Returns:
        True if integrity is verified.
        
    Raises:
        ValueError: If integrity check fails (for more descriptive errors than return False)
    """
    from orchestrator.course_architecture import stable_hash
    
    # Check 1: Course ID
    ms_id = media_spec.get("course_id")
    ca_id = course_architecture.get("course_id")
    
    if ms_id != ca_id:
        raise ValueError(f"Course ID mismatch: Media ({ms_id}) != Architecture ({ca_id})")
        
    # Check 2: Hash
    expected_hash = stable_hash(course_architecture)
    actual_hash = media_spec.get("architecture_hash")
    
    if actual_hash != expected_hash:
        raise ValueError(f"Integrity Error: Media Spec was built for a different architecture version.\n"
                         f"Expected Hash: {expected_hash}\n"
                         f"Actual Hash:   {actual_hash}")
                         
    return True
