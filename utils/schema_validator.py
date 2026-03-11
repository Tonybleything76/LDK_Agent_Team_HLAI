import json
import os
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema import Draft202012Validator


def _get_schema_dir() -> Path:
    """Return the knowledge/schemas directory, resolved from this file's location."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return Path(project_root) / "knowledge" / "schemas"


def validate_instance(instance: Any, schema_filename: str) -> bool:
    """
    Validate a JSON-serialisable object against a schema file in ``knowledge/schemas/``.

    Args:
        instance:        The dict/list to validate.
        schema_filename: Filename of the schema (e.g. ``improvement_signal.schema.json``).

    Returns:
        ``True`` when validation passes.

    Raises:
        FileNotFoundError:           If the schema file does not exist.
        jsonschema.ValidationError:  If the instance is invalid, with a
                                     descriptive path-qualified message.
    """
    schema_path = _get_schema_dir() / schema_filename
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)

    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    if errors:
        messages = [
            f"Path '/{'/'.join(str(p) for p in e.path)}': {e.message}"
            for e in errors
        ]
        raise jsonschema.ValidationError("\n".join(messages))

    return True
