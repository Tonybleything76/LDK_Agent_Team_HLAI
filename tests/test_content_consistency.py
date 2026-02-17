
import json
import os
import shutil
import subprocess
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
INPUTS_DIR = PROJECT_ROOT / "_inputs_demo"

# Ensure script is importable
import sys
sys.path.insert(0, str(PROJECT_ROOT))

# Import the module to be tested
# We use exec/import for script files that might not be in a package
try:
    from scripts.run_content_consistency import analyze_structure, calculate_quality_rubric, calculate_stability_score
except ImportError:
    # If standard import fails (e.g. if scripts is not a package), we can use importlib or just test subprocess
    pass

@pytest.fixture
def mock_run_dir(tmp_path):
    """Creates a mock run directory with artifacts."""
    run_dir = tmp_path / "mock_run"
    run_dir.mkdir()
    
    # Create artifacts
    (run_dir / "audit_summary.json").write_text(json.dumps({"run_id": "test_run"}))
    (run_dir / "run_manifest.json").write_text(json.dumps({"status": "completed"}))
    
    # Strategy Lead
    (run_dir / "01_strategy_lead_agent_state.json").write_text(json.dumps({
        "deliverable_markdown": "# Strategy\nWe verify Belief and Behavior systems.",
        "strategy": {"goals": ["Goal 1"]}
    }))
    
    # Learning Architect
    (run_dir / "03_learning_architect_agent_state.json").write_text(json.dumps({
        "curriculum": {
            "outline": [
                {"title": "Module 1", "objectives": ["Obj 1", "Obj 2"]},
                {"title": "Copilot Module", "objectives": ["Learn Copilot"]}
            ]
        }
    }))
    
    return run_dir

def test_analyze_structure(mock_run_dir):
    """Test structural analysis logic."""
    from scripts.run_content_consistency import analyze_structure
    
    # Mock record
    record = {"path": mock_run_dir}
    metrics = analyze_structure(record)
    
    assert metrics["modules_count"] == 2
    assert metrics["objectives_count"] == 3
    assert metrics["schema_validity"]["learning_architect"] is True

def test_calculate_quality_rubric(mock_run_dir):
    """Test rubric calculation."""
    from scripts.run_content_consistency import calculate_quality_rubric
    
    scores = calculate_quality_rubric(mock_run_dir)
    
    assert scores["belief_clarity_present"] is True
    assert scores["behavior_clarity_present"] is True
    assert scores["systems_policies_present"] is True
    assert scores["alignment_score"] == 2 # Goals + Modules
    assert scores["copilot_coverage_score"] == 1 # >0 mentions

def test_calculate_stability_score():
    """Test stability score calculation."""
    from scripts.run_content_consistency import calculate_stability_score
    
    reports = [
        {"structure": {"modules_count": 5, "objectives_count": 10}},
        {"structure": {"modules_count": 5, "objectives_count": 10}},
        {"structure": {"modules_count": 5, "objectives_count": 10}}
    ]
    assert calculate_stability_score(reports) == 100
    
    # Variance in modules
    reports[2]["structure"]["modules_count"] = 4
    assert calculate_stability_score(reports) == 80  # -20 penalty
    
    # Variance in objectives
    reports = [
        {"structure": {"modules_count": 5, "objectives_count": 10}},
        {"structure": {"modules_count": 5, "objectives_count": 12}} # 20% diff
    ]
    # avg = 11. max_diff = 1. 1/11 = ~0.09. < 0.1 so no penalty?
    # Let's make it bigger
    reports[1]["structure"]["objectives_count"] = 15 # avg 12.5. diff 2.5. 2.5/12.5 = 0.2
    assert calculate_stability_score(reports) <= 90

def test_full_script_dry_run(tmp_path):
    """
    Integration test using subprocess to run the script in dry_run mode.
    This creates a real loop execution but mocks the pipeline via provider=dry_run (which creates artifacts).
    """
    # Create dummy inputs
    inputs_dir = tmp_path / "inputs"
    inputs_dir.mkdir()
    (inputs_dir / "business_brief.md").write_text("# Brief")
    (inputs_dir / "sme_notes.md").write_text("# Notes")
    
    # We need the script to actually invoke run_pipeline.py.
    # We rely on run_pipeline.py's dry_run to produce artifacts strings.
    # However, run_pipeline dry_run might NOT produce actual files in outputs/ unless mocked.
    # The real run_pipeline dry_run DOES output stubs.
    
    # Let's try running it.
    # We need to ensure PROJECT_ROOT is correct for the subprocess call within the script.
    
    # Command
    cmd = [
        "python3", "scripts/run_content_consistency.py",
        "--inputs-dir", str(inputs_dir),
        "--provider", "dry_run",
        "--runs", "1",
        "--governance_profile", "content_only"
    ]
    
    # Execute
    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        env={**os.environ, "PROJECT_ROOT": str(PROJECT_ROOT)},
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        
    assert result.returncode == 0
    
    # Check outputs
    export_json = PROJECT_ROOT / "exports" / "content_consistency_report.json"
    export_zip = PROJECT_ROOT / "exports" / "content_consistency_pack.zip"
    
    assert export_json.exists()
    assert export_zip.exists()
    
    with open(export_json) as f:
        data = json.load(f)
        assert data["overall_stability_score"] >= 0
        assert len(data["runs"]) == 1
        
    # Check zip
    with zipfile.ZipFile(export_zip, 'r') as zf:
        names = zf.namelist()
        assert "content_consistency_report.json" in names
        assert "diff_overview.md" in names
