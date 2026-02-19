import os
import shutil
import tempfile
import pytest
import sys
from pathlib import Path
import subprocess

from scripts.validate_inputs_quality import validate_quality

@pytest.fixture
def temp_inputs_dir():
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def create_valid_inputs(inputs_dir: Path):
    brief_content = """# Business Context
Acme Corp needs a Copilot roll-out. Copilot.

# Organizational Goals
- Goal 1 is important
- Goal 2 is relevant
- Goal 3 is critical

# Target Audience
Everyone.

# Learning Objectives
- Learn X
- Learn Y
- Learn Z
- Learn W

# Success Metrics
- Increase adoption by 20%
- Save 5 hours weekly
- Complete setup in 1 month

# Delivery Modality
Online

# Strategic Framing
Strategy.
"""
    notes_content = """# Core Instructional Philosophy
Philosophy.

# Essential Concept Coverage
Concepts.

# Gotchas
Gotchas.

# Responsible AI Behavior Model
Behavior. Belief.

# Systems & Policy Alignment
Policies.

# Tone & Human Experience
Tone.

# Non-Negotiable Learning Outcomes
Outcomes.
"""
    (inputs_dir / "business_brief.md").write_text(brief_content)
    (inputs_dir / "sme_notes.md").write_text(notes_content)

def test_valid_fixture_passes(temp_inputs_dir):
    create_valid_inputs(temp_inputs_dir)
    is_valid, errors = validate_quality(temp_inputs_dir, "Copilot")
    assert is_valid is True
    assert len(errors) == 0

def test_missing_section_fails(temp_inputs_dir):
    create_valid_inputs(temp_inputs_dir)
    # Remove 'Success Metrics' section
    brief_path = temp_inputs_dir / "business_brief.md"
    content = brief_path.read_text()
    content = content.replace("# Success Metrics", "# Some Other Section")
    brief_path.write_text(content)
    
    is_valid, errors = validate_quality(temp_inputs_dir, "Copilot")
    assert is_valid is False
    assert any("missing headers" in e and "Success Metrics" in e for e in errors)

def test_belief_behavior_systems_fails(temp_inputs_dir):
    create_valid_inputs(temp_inputs_dir)
    # Remove 'Belief' and 'Behavior'
    notes_path = temp_inputs_dir / "sme_notes.md"
    content = notes_path.read_text()
    content = content.replace("Behavior. Belief.", "")
    content = content.replace("Responsible AI Behavior Model", "Responsible AI X Model")
    notes_path.write_text(content)

    is_valid, errors = validate_quality(temp_inputs_dir, "Copilot")
    assert is_valid is False
    assert any("must include 'Belief'" in e for e in errors)
    assert any("must include 'Behavior'" in e for e in errors)

def test_new_course_inputs_script(temp_inputs_dir):
    # Call new_course_inputs.py logic via subprocess or import
    project_root = Path(__file__).parent.parent
    script_path = project_root / "scripts" / "new_course_inputs.py"
    
    slug = "test_script_slug"
    target_dir = project_root / f"_inputs_{slug}"
    
    try:
        if target_dir.exists():
            shutil.rmtree(target_dir)

        # Run command
        res = subprocess.run([sys.executable, str(script_path), slug], capture_output=True, text=True)
        assert res.returncode == 0
        assert target_dir.exists()
        assert (target_dir / "business_brief.md").exists()
        assert (target_dir / "sme_notes.md").exists()
        
        # Idempotency: run again without force should fail
        res_fail = subprocess.run([sys.executable, str(script_path), slug], capture_output=True, text=True)
        assert res_fail.returncode == 1
        assert "already exists" in res_fail.stdout or "already exists" in res_fail.stderr

        # With force should pass
        res_force = subprocess.run([sys.executable, str(script_path), slug, "--force"], capture_output=True, text=True)
        assert res_force.returncode == 0

    finally:
        if target_dir.exists():
            shutil.rmtree(target_dir)
