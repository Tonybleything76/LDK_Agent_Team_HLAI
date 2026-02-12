"""
Course Architecture Utilities

Handles loading, saving, validation, and hashing of the v0.6 Course Architecture artifact.
"""

import json
import hashlib
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

def load_course_architecture(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a course architecture JSON file.
    
    Args:
        path: Path to the JSON file.
        
    Returns:
        The loaded JSON object.
    
    Raises:
        FileNotFoundError: If file misses.
        json.JSONDecodeError: If invalid JSON.
    """
    with open(path, "r") as f:
        return json.load(f)

def save_course_architecture(obj: Dict[str, Any], path: Union[str, Path]) -> None:
    """
    Save a course architecture object to JSON.
    
    Args:
        obj: The dictionary to save.
        path: Destination path.
    """
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)

def stable_hash(obj: Dict[str, Any]) -> str:
    """
    Compute a stable SHA256 hash of the JSON object.
    
    Keys are sorted to ensure determinism.
    
    Args:
        obj: JSON-serializable dictionary.
        
    Returns:
        Hex string of the SHA256 hash.
    """
    # sort_keys=True is critical for stability
    canonical_json = json.dumps(obj, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()

def validate_course_architecture(obj: Dict[str, Any]) -> None:
    """
    Validate a course architecture object against its schema.
    
    Also validates nested Learning Objects against their schema.
    
    Args:
        obj: The dictionary to validate.
        
    Raises:
        ValueError: If validation fails, with a descriptive error message.
    """
    try:
        # Load schemas
        ca_schema = _load_schema("course_architecture.json")
        lo_schema = _load_schema("learning_object.json")
        
        # Configure resolver for local references if needed, 
        # but since we are validating in python, we might need to manually handle the $ref 
        # or use a resolver. 
        # The schema uses "$ref": "learning_object.json".
        # jsonschema RefResolver needs a base URI.
        
        resolver = jsonschema.RefResolver(
            base_uri=f"file://{SCHEMAS_DIR.absolute()}/",
            referrer=ca_schema
        )
        
        # Pre-load the referenced schema into the store if needed, 
        # or just let the resolver find it on disk via the base_uri.
        # file:// usage in RefResolver can be tricky across OS.
        # A safer way allows explicit store.
        
        # Let's try explicit validation of the top level, and relying on `jsonschema` to resolve.
        # If that is flaky, we can manually check.
        # Given the constraint to use "existing repo patterns" (none exist for schema validation yet),
        # I'll implement a robust way: replace the $ref with the actual schema in memory 
        # OR use the resolver correctly.
        
        # Approach: Load both, create a store (registry in newer jsonschema, but let's stick to standard)
        # We will use RefResolver with the directory.
        
        jsonschema.validate(instance=obj, schema=ca_schema, resolver=resolver)
        
    except jsonschema.ValidationError as e:
        # Create a clean error message
        path = " -> ".join(str(p) for p in e.path) if e.path else "root"
        raise ValueError(f"Validation failed at '{path}': {e.message}")
    except Exception as e:
        raise ValueError(f"Schema validation error: {str(e)}")


def create_from_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate course_architecture.json from the system state (Pass 1).
    
    This functions maps the output from Learning Architect (curriculum.outline)
    and Assessment Designer (assessment.questions) into the V0.6 schema.
    
    Args:
        state: The full system_state dictionary.
        
    Returns:
        A dictionary matching the course_architecture.json schema.
    """
    from datetime import datetime
    
    # 1. Basic Metadata
    # In a real system, course_id might come from inputs or config.
    # We'll use a placeholder or derived ID.
    course_id = "course_" + hashlib.md5(json.dumps(state.get("inputs", {}).get("business_brief", "")).encode()).hexdigest()[:8]
    
    architecture = {
        "course_id": course_id,
        "version": "0.6.0",
        "generated_at_utc": datetime.utcnow().isoformat() + "Z",
        "scenario_anchors": state.get("curriculum", {}).get("scenario_anchors", []),
        "learning_objects": []
    }
    
    # 2. Map Curriculum Outline (Learning Architect)
    # Expected structure: state['curriculum']['outline'] -> List of modules
    # Each module: { "module": "1", "title": "...", "objectives": [...] }
    
    outline = state.get("curriculum", {}).get("outline", [])
    if not isinstance(outline, list):
        outline = []
        
    for module in outline:
        mod_id = f"module_{module.get('module', 'unknown')}"
        mod_title = module.get("title", "Untitled Module")
        objectives = module.get("objectives", [])
        
        # Create a Container/Concept LO for the module itself?
        # Or just creat LOs for the objectives? 
        # The schema is a flat list of LOs.
        # Let's create one LO per Module for now as a "Process" or "Concept"
        
        lo = {
            "id": mod_id,
            "type": "concept", # Defaulting to concept for the module container
            "metadata": {
                "taxonomy_level": "bloom_understand", # Default
                "duration_minutes": 10, # Default estimate
                "tags": ["module"]
            },
            "content": {
                "key_points": objectives if objectives else ["Content for " + mod_title],
                "misconceptions": [],
                "narrative_arc": f"Module: {mod_title}"
            }
        }
        architecture["learning_objects"].append(lo)
        
    # 3. Map Assessment Questions (Assessment Designer)
    # Expected: state['assessment']['questions'] -> List of questions
    
    questions = state.get("assessment", {}).get("questions", [])
    if not isinstance(questions, list):
        questions = []
        
    # We group questions into an "Assessment" LO or attach them to modules?
    # For Pass 1, let's create a standalone Assessment LO.
    
    if questions:
        assessment_lo = {
            "id": "assessment_final",
            "type": "process", # Assessment process
            "metadata": {
                "taxonomy_level": "bloom_evaluate",
                "duration_minutes": len(questions) * 2, # 2 min per question
                "tags": ["assessment", "exam"]
            },
            "content": {
                "key_points": ["Final Verification of Learning Objectives"],
                "misconceptions": [],
                "narrative_arc": "Final Challenge"
            },
            "assessment": {
                "knowledge_checks": []
            }
        }
        
        for q in questions:
            # q structure: { "q_id": 1, "stem": "...", "options": [...], "correct_idx": 0, "feedback": "..." }
            kc = {
                "question": q.get("stem", "Untitled Question"),
                "type": "mcq" # Default to MCQ
            }
            assessment_lo["assessment"]["knowledge_checks"].append(kc)
            
        architecture["learning_objects"].append(assessment_lo)
        
    return architecture
