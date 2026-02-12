import json
import os
import jsonschema
from jsonschema import Draft202012Validator

def validate_instance(instance, schema_filename):
    """
    Validates a JSON instance against a schema file located in knowledge/schemas.
    
    Args:
        instance: The JSON object (dict) to validate.
        schema_filename: The filename of the schema (e.g., 'improvement_signal.schema.json').
        
    Raises:
        ValidationError: If the instance is invalid, with a descriptive message.
        FileNotFoundError: If the schema file does not exist.
    """
    # Locate schema directory relative to project root
    # Assumptions: this file is in utils/schema_validator.py
    # Project root is ../
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    schema_path = os.path.join(project_root, 'knowledge', 'schemas', schema_filename)
    
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found at: {schema_path}")
        
    with open(schema_path, 'r') as f:
        schema = json.load(f)
        
    validator = Draft202012Validator(schema)
    
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    
    if errors:
        error_messages = []
        for error in errors:
            path = "/" + "/".join(str(p) for p in error.path)
            error_messages.append(f"Path '{path}': {error.message}")
        
        raise jsonschema.ValidationError("\n".join(error_messages))
        
    return True
