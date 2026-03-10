"""
Unit tests for orchestrator/validation.py

Tests cover:
- validate_agent_output() contract enforcement
- check_open_questions_format() severity prefix warnings
"""

import pytest
from orchestrator.validation import (
    ValidationConfig,
    validate_agent_output,
    check_open_questions_format,
    SEVERITY_PREFIXES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _valid_output(**overrides):
    """Return a minimal valid agent output dict."""
    base = {
        "deliverable_markdown": "A" * 350,  # above default 300-char minimum
        "updated_state": {"some_key": "some_value"},
        "open_questions": [],
    }
    base.update(overrides)
    return base


DEFAULT_CFG = ValidationConfig()


# ---------------------------------------------------------------------------
# validate_agent_output — happy path
# ---------------------------------------------------------------------------

def test_validate_passes_valid_output():
    validate_agent_output("test_agent", _valid_output(), DEFAULT_CFG)


def test_validate_passes_with_prefixed_open_questions(capsys):
    output = _valid_output(open_questions=["CRITICAL: Something broke", "MINOR: Typo found"])
    validate_agent_output("test_agent", output, DEFAULT_CFG)
    captured = capsys.readouterr()
    assert "missing severity prefix" not in captured.out


# ---------------------------------------------------------------------------
# validate_agent_output — missing / wrong-type keys
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("missing_key", ["deliverable_markdown", "updated_state", "open_questions"])
def test_validate_fails_missing_required_key(missing_key):
    output = _valid_output()
    del output[missing_key]
    with pytest.raises(ValueError, match=missing_key):
        validate_agent_output("test_agent", output, DEFAULT_CFG)


def test_validate_fails_deliverable_not_string():
    with pytest.raises(ValueError, match="deliverable_markdown must be a string"):
        validate_agent_output("test_agent", _valid_output(deliverable_markdown=42), DEFAULT_CFG)


def test_validate_fails_updated_state_not_dict():
    with pytest.raises(ValueError, match="updated_state must be an object"):
        validate_agent_output("test_agent", _valid_output(updated_state=["list"]), DEFAULT_CFG)


def test_validate_fails_open_questions_not_list():
    with pytest.raises(ValueError, match="open_questions must be an array"):
        validate_agent_output("test_agent", _valid_output(open_questions="not a list"), DEFAULT_CFG)


def test_validate_fails_open_questions_contains_non_string():
    with pytest.raises(ValueError, match="open_questions must be an array"):
        validate_agent_output("test_agent", _valid_output(open_questions=[1, 2, 3]), DEFAULT_CFG)


# ---------------------------------------------------------------------------
# validate_agent_output — deliverable content checks
# ---------------------------------------------------------------------------

def test_validate_fails_empty_deliverable():
    with pytest.raises(ValueError, match="deliverable_markdown is empty"):
        validate_agent_output("test_agent", _valid_output(deliverable_markdown="   "), DEFAULT_CFG)


def test_validate_fails_short_deliverable():
    cfg = ValidationConfig(min_deliverable_chars=500)
    with pytest.raises(ValueError, match="too short"):
        validate_agent_output("test_agent", _valid_output(deliverable_markdown="x" * 100), cfg)


def test_validate_fails_placeholder_marker():
    cfg = ValidationConfig(placeholder_markers=["TODO", "TBD"])
    output = _valid_output(deliverable_markdown="A" * 300 + " TODO: fill this in")
    with pytest.raises(ValueError, match="placeholder marker"):
        validate_agent_output("test_agent", output, cfg)


def test_validate_placeholder_check_is_case_insensitive():
    cfg = ValidationConfig(placeholder_markers=["TODO"])
    output = _valid_output(deliverable_markdown="A" * 300 + " todo: fill this in")
    with pytest.raises(ValueError, match="placeholder marker"):
        validate_agent_output("test_agent", output, cfg)


# ---------------------------------------------------------------------------
# check_open_questions_format — severity prefix warnings
# ---------------------------------------------------------------------------

def test_no_warnings_when_all_prefixed():
    questions = [
        "CRITICAL: The login form is broken",
        "BLOCKER: Missing dependency",
        "MAJOR: Performance issue",
        "MINOR: Typo in label",
    ]
    warnings = check_open_questions_format("test_agent", questions)
    assert warnings == []


def test_warning_for_unprefixed_question():
    questions = ["This question has no severity prefix"]
    warnings = check_open_questions_format("test_agent", questions)
    assert len(warnings) == 1
    assert "missing severity prefix" in warnings[0]
    assert "open_questions[0]" in warnings[0]


def test_warning_only_for_unprefixed_in_mixed_list():
    questions = [
        "CRITICAL: A real problem",
        "no prefix here",
        "MINOR: Small thing",
        "also no prefix",
    ]
    warnings = check_open_questions_format("test_agent", questions)
    assert len(warnings) == 2
    assert "open_questions[1]" in warnings[0]
    assert "open_questions[3]" in warnings[1]


def test_empty_questions_produce_no_warnings():
    assert check_open_questions_format("test_agent", []) == []


def test_empty_string_question_skipped():
    # Blank strings don't trigger a warning (nothing to prefix)
    assert check_open_questions_format("test_agent", ["", "   "]) == []


def test_prefix_check_is_case_insensitive():
    # 'critical:' lowercase should still be recognised as prefixed
    questions = ["critical: Something broke"]
    warnings = check_open_questions_format("test_agent", questions)
    assert warnings == []


def test_severity_prefixes_constant_has_expected_values():
    assert "CRITICAL:" in SEVERITY_PREFIXES
    assert "BLOCKER:" in SEVERITY_PREFIXES
    assert "MAJOR:" in SEVERITY_PREFIXES
    assert "MINOR:" in SEVERITY_PREFIXES


# ---------------------------------------------------------------------------
# validate_agent_output — unprefixed questions print warning but don't raise
# ---------------------------------------------------------------------------

def test_unprefixed_questions_print_warning_not_raise(capsys):
    output = _valid_output(open_questions=["This has no prefix"])
    # Should not raise
    validate_agent_output("test_agent", output, DEFAULT_CFG)
    captured = capsys.readouterr()
    assert "missing severity prefix" in captured.out
