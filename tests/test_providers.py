"""
Unit tests for orchestrator/providers/

Tests cover (no real API calls made):
- DryRunProvider returns contract-compliant JSON for generic and specialised agents
- DryRunProvider._extract_agent_name() parses agent names correctly
- OpenAIProvider raises ValueError when OPENAI_API_KEY is not set
- get_provider() factory returns correct types and raises on unknown names
"""

import json
import os
import pytest

from orchestrator.providers import get_provider, DryRunProvider, OpenAIProvider


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

GENERIC_PROMPT = "You are the Strategy Lead Agent. Please produce a course strategy."
LEARNING_ARCHITECT_PROMPT = "# Learning Architect Agent\nDesign the curriculum."
QA_PROMPT = "You are the Quality Assurance Specialist. Review this content."


def _parse_and_assert_contract(raw_json: str) -> dict:
    """Assert raw_json is valid JSON with the three required contract keys."""
    data = json.loads(raw_json)
    assert "deliverable_markdown" in data, "Missing deliverable_markdown"
    assert "updated_state" in data, "Missing updated_state"
    assert "open_questions" in data, "Missing open_questions"
    assert isinstance(data["deliverable_markdown"], str)
    assert isinstance(data["updated_state"], dict)
    assert isinstance(data["open_questions"], list)
    return data


# ---------------------------------------------------------------------------
# DryRunProvider — contract compliance
# ---------------------------------------------------------------------------

def test_dry_run_generic_prompt_returns_valid_contract():
    provider = DryRunProvider()
    result = provider.run(GENERIC_PROMPT)
    _parse_and_assert_contract(result)


def test_dry_run_deliverable_meets_minimum_length():
    provider = DryRunProvider()
    result = provider.run(GENERIC_PROMPT)
    data = json.loads(result)
    assert len(data["deliverable_markdown"].strip()) >= 300


def test_dry_run_learning_architect_returns_valid_contract():
    provider = DryRunProvider()
    result = provider.run(LEARNING_ARCHITECT_PROMPT)
    data = _parse_and_assert_contract(result)
    # Must include curriculum with 6 modules
    updated_state = data["updated_state"]
    assert "curriculum" in updated_state
    modules = updated_state["curriculum"]["modules"]
    assert len(modules) == 6


def test_dry_run_learning_architect_module_ids_sequential():
    provider = DryRunProvider()
    result = provider.run(LEARNING_ARCHITECT_PROMPT)
    data = json.loads(result)
    modules = data["updated_state"]["curriculum"]["modules"]
    for i, m in enumerate(modules, start=1):
        assert m["module_id"] == f"M{i}", f"Expected M{i}, got {m['module_id']}"


def test_dry_run_learning_architect_required_state_keys():
    provider = DryRunProvider()
    result = provider.run(LEARNING_ARCHITECT_PROMPT)
    data = json.loads(result)
    required = [
        "course_title", "course_summary", "target_audience",
        "business_goal_alignment", "belief_behavior_systems",
        "curriculum", "constraints", "assumptions",
    ]
    for key in required:
        assert key in data["updated_state"], f"Missing key in updated_state: {key}"


def test_dry_run_strategy_lead_simulates_risk_gate_open_questions():
    """strategy_lead stub generates >8 MAJOR questions to exercise risk gate testing."""
    provider = DryRunProvider()
    # The stub fires when agent name matches 'strategy lead'
    prompt = "# Role: Strategy Lead\nCreate a strategy."
    result = provider.run(prompt)
    data = json.loads(result)
    major_questions = [q for q in data["open_questions"] if q.upper().startswith("MAJOR:")]
    assert len(major_questions) >= 8


def test_dry_run_qa_simulates_critical_open_question():
    """Quality Assurance specialist stub generates a CRITICAL open question."""
    provider = DryRunProvider()
    result = provider.run(QA_PROMPT)
    data = json.loads(result)
    critical = [q for q in data["open_questions"] if q.upper().startswith("CRITICAL:")]
    assert len(critical) >= 1


# ---------------------------------------------------------------------------
# DryRunProvider — agent name extraction
# ---------------------------------------------------------------------------

def test_extract_agent_name_from_role_line():
    provider = DryRunProvider()
    prompt = "# Role: Strategy Lead Agent\nDo something."
    assert provider._extract_agent_name(prompt) == "Strategy Lead Agent"


def test_extract_agent_name_from_you_are_line():
    provider = DryRunProvider()
    prompt = "You are the Quality Assurance Specialist. Review this."
    assert provider._extract_agent_name(prompt) == "Quality Assurance Specialist"


def test_extract_agent_name_fallback():
    provider = DryRunProvider()
    assert provider._extract_agent_name("No role information here.") == "Unknown Agent"


# ---------------------------------------------------------------------------
# get_provider() factory
# ---------------------------------------------------------------------------

def test_get_provider_dry_run():
    provider = get_provider("dry_run")
    assert isinstance(provider, DryRunProvider)


def test_get_provider_case_insensitive():
    provider = get_provider("DRY_RUN")
    assert isinstance(provider, DryRunProvider)


def test_get_provider_unknown_raises():
    with pytest.raises(ValueError, match="Unknown provider"):
        get_provider("nonexistent_provider")


def test_get_provider_empty_string_raises():
    with pytest.raises(ValueError, match="Unknown provider"):
        get_provider("")


def test_get_provider_none_without_env_raises(monkeypatch):
    monkeypatch.delenv("PROVIDER", raising=False)
    with pytest.raises(ValueError):
        get_provider(None)


def test_get_provider_reads_env_var(monkeypatch):
    monkeypatch.setenv("PROVIDER", "dry_run")
    provider = get_provider(None)
    assert isinstance(provider, DryRunProvider)


# ---------------------------------------------------------------------------
# OpenAIProvider — init guard (no API call needed)
# ---------------------------------------------------------------------------

def test_openai_provider_raises_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        OpenAIProvider()


def test_openai_provider_reads_model_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o")
    provider = OpenAIProvider()
    assert provider.model == "gpt-4o"


def test_openai_provider_default_model(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake-key")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    provider = OpenAIProvider()
    assert provider.model == "gpt-4o-mini"


def test_openai_provider_temperature_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake-key")
    monkeypatch.setenv("OPENAI_TEMPERATURE", "0.7")
    provider = OpenAIProvider()
    assert provider.temperature == pytest.approx(0.7)


def test_openai_provider_invalid_temperature_falls_back(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake-key")
    monkeypatch.setenv("OPENAI_TEMPERATURE", "not-a-float")
    provider = OpenAIProvider()
    assert provider.temperature == pytest.approx(0.2)
