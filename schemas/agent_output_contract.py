"""
Agent output contract schema shim.
Loads the JSON schema and exposes required keys.
"""
import json
from pathlib import Path
from typing import Dict, Any, List

_SCHEMA_PATH = Path(__file__).parent / "agent_output_contract.json"


def load_schema() -> Dict[str, Any]:
    """Load the agent_output_contract.json schema."""
    with open(_SCHEMA_PATH, "r") as f:
        return json.load(f)


# Expose REQUIRED_KEYS for backward compatibility
_schema = load_schema()
REQUIRED_KEYS: List[str] = _schema.get("required_keys", [])
