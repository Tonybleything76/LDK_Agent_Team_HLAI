import json
from pathlib import Path
from typing import Any, Dict, List

# -----------------------------
# Validation / Guardrails
# Single source of truth
# -----------------------------

from dataclasses import dataclass, field

# -----------------------------
# Validation / Guardrails
# Single source of truth
# -----------------------------

@dataclass
class ValidationConfig:
    min_deliverable_chars: int = 300
    placeholder_markers: List[str] = field(default_factory=list)


def safe_json_loads(text: str) -> Dict[str, Any]:
    """Safely parse JSON, providing a helpful error if it fails."""
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {e}\nContent snippet: {text[:200]}...")


def validate_agent_output(agent_name: str, result: Dict[str, Any], vcfg: ValidationConfig) -> None:
    """Validate an agent result dict against the MVP contract + guardrails."""
    # Required keys
    for k in ["deliverable_markdown", "updated_state", "open_questions"]:
        if k not in result:
            raise ValueError(f"{agent_name} output missing required key: {k}")

    # Types
    if not isinstance(result["deliverable_markdown"], str):
        raise ValueError(f"{agent_name}: deliverable_markdown must be a string")
    if not isinstance(result["updated_state"], dict):
        raise ValueError(f"{agent_name}: updated_state must be an object/dict")
    if not isinstance(result["open_questions"], list) or not all(
        isinstance(x, str) for x in result["open_questions"]
    ):
        raise ValueError(f"{agent_name}: open_questions must be an array of strings")

    deliverable = result["deliverable_markdown"].strip()

    # Non-empty deliverable
    if not deliverable:
        raise ValueError(f"{agent_name}: deliverable_markdown is empty")

    # Placeholder detection
    lower_deliverable = deliverable.lower()
    for marker in vcfg.placeholder_markers:
        if marker.lower() in lower_deliverable:
            raise ValueError(
                f"{agent_name}: deliverable_markdown contains placeholder marker: '{marker}'"
            )

    # Length sanity check
    if len(deliverable) < vcfg.min_deliverable_chars:
        raise ValueError(
            f"{agent_name}: deliverable_markdown is too short ({len(deliverable)} chars). "
            f"Expected at least {vcfg.min_deliverable_chars}."
        )


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return safe_json_loads(path.read_text(encoding="utf-8"))


def validate_agent_output_file(agent_name: str, json_path: Path) -> Dict[str, Any]:
    """Read a JSON file, validate it, return the parsed dict."""
    result = read_json(json_path)
    # create default config for backward compatibility if needed, though this function isn't used in root_agent
    validate_agent_output(agent_name, result, ValidationConfig())
    return result


def deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Merge b into a recursively (dicts merge; lists overwrite; scalars overwrite)."""
    for k, v in b.items():
        if k in a and isinstance(a[k], dict) and isinstance(v, dict):
            deep_merge(a[k], v)
        else:
            a[k] = v
    return a
