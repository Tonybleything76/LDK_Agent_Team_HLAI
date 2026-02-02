"""
System state schema shim.
Loads the JSON schema and provides helper functions.
"""
import json
from pathlib import Path
from typing import Dict, Any

_SCHEMA_PATH = Path(__file__).parent / "system_state.json"


def load_schema() -> Dict[str, Any]:
    """Load the system_state.json schema."""
    with open(_SCHEMA_PATH, "r") as f:
        return json.load(f)


def get_initial_state() -> Dict[str, Any]:
    """Return a fresh copy of the initial system state."""
    return load_schema()
